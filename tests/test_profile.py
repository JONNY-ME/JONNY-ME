import json
import sys
import tempfile
import unittest
import xml.etree.ElementTree as ET
from pathlib import Path
from unittest.mock import patch
from urllib.error import HTTPError

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import art
import build
import update_activity


REPO = "JONNY-ME/zindi-cli"
COMMIT = {"sha": "a" * 40, "commit": {"message": "A useful change\n\nDetails", "committer": {"date": "2026-07-30T09:33:38Z"}}}


def fake_fetch(path):
    return [COMMIT] if "/commits?" in path else {"private": False, "size": 2}


class ActivityTests(unittest.TestCase):
    def test_records_only_public_commit_metadata(self):
        result = update_activity.collect([REPO], fake_fetch)
        self.assertEqual(result["entries"][0]["title"], "A useful change")
        self.assertEqual(set(result["entries"][0]), {"repository", "sha", "date", "title"})

    def test_private_repository_rejected(self):
        with self.assertRaisesRegex(ValueError, "must be public"):
            update_activity.collect([REPO], lambda _: {"private": True})

    def test_repository_path_injection_rejected(self):
        with self.assertRaises(ValueError):
            update_activity.collect(["JONNY-ME/../../private"], fake_fetch)

    def test_empty_repository(self):
        def empty(path):
            if "/commits?" in path:
                raise HTTPError(path, 409, "Git Repository is empty", {}, None)
            return {"private": False, "size": 0}
        self.assertEqual(update_activity.collect([REPO], empty), {"entries": []})
        self.assertIn("first successful refresh", build.activity_markdown({"entries": []}, [REPO]))

    def test_conflict_on_nonempty_repository_is_not_swallowed(self):
        def conflict(path):
            if "/commits?" in path:
                raise HTTPError(path, 409, "Conflict", {}, None)
            return {"private": False, "size": 42}
        with self.assertRaises(HTTPError):
            update_activity.collect([REPO], conflict)

    def test_remote_titles_cannot_inject_markdown_or_html(self):
        result = update_activity.collect([REPO], fake_fetch)
        result["entries"][0]["title"] = '<img src=x> [click](javascript:alert(1))\n# header | `code`'
        rendered = build.activity_markdown(result, [REPO])
        self.assertNotIn("<img", rendered)
        self.assertIn("&lt;img", rendered)
        self.assertIn(r"\[click\]", rendered)
        self.assertIn(r"\# header \| \`code\`", rendered)
        self.assertNotIn("\n", rendered)

    def test_invalid_commit_sha_rejected(self):
        result = update_activity.collect([REPO], fake_fetch)
        result["entries"][0]["sha"] = "../../something"
        with self.assertRaises(ValueError):
            build.activity_markdown(result, [REPO])

    def test_failed_refresh_preserves_snapshot_and_noop_preserves_mtime(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            (root / "profile.json").write_text(json.dumps({"activity_repositories": [REPO]}))
            self.assertTrue(update_activity.refresh(root, fake_fetch))
            path = root / "data/activity.json"
            old, mtime = path.read_bytes(), path.stat().st_mtime_ns
            self.assertFalse(update_activity.refresh(root, fake_fetch))
            self.assertEqual(path.stat().st_mtime_ns, mtime)
            def unavailable(_):
                raise HTTPError("https://api.github.com", 403, "rate limited", {}, None)
            with self.assertRaises(HTTPError):
                update_activity.refresh(root, unavailable)
            self.assertEqual(path.read_bytes(), old)
            self.assertFalse(path.with_suffix(".tmp").exists())

    def test_second_repository_failure_does_not_publish_partial_snapshot(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            (root / "data").mkdir()
            (root / "data/activity.json").write_text('{"entries": []}\n')
            (root / "profile.json").write_text(json.dumps({"activity_repositories": [REPO, "JONNY-ME/multilingual-health-qa"]}))
            def fetch(path):
                if "multilingual" in path:
                    raise TimeoutError("network timeout")
                return fake_fetch(path)
            with self.assertRaises(TimeoutError):
                update_activity.refresh(root, fetch)
            self.assertEqual((root / "data/activity.json").read_text(), '{"entries": []}\n')


class RenderingTests(unittest.TestCase):
    def test_assets_are_self_contained_valid_svg_and_within_budget(self):
        for name, svg in art.assets().items():
            with self.subTest(name=name):
                root = ET.fromstring(svg)
                self.assertEqual(root.tag, "{http://www.w3.org/2000/svg}svg")
                if "@keyframes" in svg:
                    self.assertIn("prefers-reduced-motion", svg)
                if "static" in name:
                    self.assertNotIn("@keyframes", svg)
                for node in root.iter():
                    self.assertNotIn(node.tag.split("}")[-1], {"script", "foreignObject", "image"})
                    self.assertFalse(any(key.startswith("on") for key in node.attrib))
        for theme in ["dark", "light"]:
            total = sum(len(value.encode()) for name, value in art.assets().items() if f"-{theme}" in name)
            self.assertLess(total, 300_000)

    def test_generation_is_deterministic_and_all_referenced_assets_exist(self):
        first, second = build.outputs(), build.outputs()
        self.assertEqual(first, second)
        readme = first[build.ROOT / "README.md"]
        import re
        for name in re.findall(r'(?:src|srcset)="(assets/[^"]+)"', readme):
            self.assertIn(build.ROOT / name, first)
        self.assertIn("#01--selected-systems", readme)
        self.assertEqual(readme.count("<!-- activity:start -->"), 1)
        self.assertEqual(readme.count("<!-- activity:end -->"), 1)
        self.assertLess(readme.index('srcset="assets/hero-static-dark-compact.svg"'), readme.index('srcset="assets/hero-dark-compact.svg"'))

    def test_check_does_not_write_missing_or_stale_outputs(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            path = root / "README.md"
            with patch.object(build, "outputs", return_value={path: "new"}):
                with self.assertRaises(SystemExit):
                    build.build(check=True, root=root)
                self.assertFalse(path.exists())
                path.write_text("old")
                with self.assertRaises(SystemExit):
                    build.build(check=True, root=root)
                self.assertEqual(path.read_text(), "old")

    def test_unsafe_links_rejected(self):
        for value in ["javascript:alert(1)", "https://", "https://foo\nbar", 'https://foo/"bad']:
            with self.subTest(value=value), self.assertRaises(ValueError):
                build.safe_url(value)


if __name__ == "__main__":
    unittest.main()
