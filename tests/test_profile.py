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
import instrument
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

    def test_section_markers_are_decorative_and_precede_each_heading(self):
        readme = build.outputs()[build.ROOT / "README.md"]
        for n in range(1, 6):
            marker = readme.index(f'srcset="assets/marker-{n}-dark.svg"')
            heading = readme.index(f"## 0{n} / ")
            self.assertLess(marker, heading)
            self.assertNotIn("## 0", readme[marker:heading])
        self.assertEqual(readme.count('alt=""'), 5)


class InstrumentTests(unittest.TestCase):
    """The artwork's claims are checked: the waveform really encodes the name, the vote is a majority."""

    def test_uart_waveform_decodes_to_name(self):
        bits = instrument.uart_bits(art.NAME)
        decoded = ""
        for start in range(0, len(bits), 10):
            frame = bits[start:start + 10]
            self.assertEqual((frame[0], frame[9]), (0, 1), "8N1 start and stop bits")
            decoded += chr(sum(bit << i for i, bit in enumerate(frame[1:9])))
        self.assertEqual(decoded, "YOHANNES")
        for theme in instrument.PALETTES:
            hero = art.hero(theme)
            for char in art.NAME:
                self.assertIn(f"0x{ord(char):02X}", hero)
            self.assertIn(f"{len(bits) / art.BAUD * 1000:.2f} ms", hero)

    def test_vote_lane_is_the_majority_of_three_models(self):
        for lanes in art.FPGA_CYCLES:
            self.assertEqual(len(lanes), 3)
            vote, agree = art.majority(list(lanes))
            self.assertGreaterEqual(agree, 2, "every illustrated cycle must have a 2-of-3 majority")
            self.assertEqual(sum(value == vote for value in lanes), agree)
        self.assertTrue(any(art.majority(list(lanes))[1] == 2 for lanes in art.FPGA_CYCLES))

    def test_cli_session_matches_the_zindi_cli_exit_code_contract(self):
        exit_codes = {"API_ERROR": 1, "RATE_LIMITED": 1, "USAGE": 2, "NO_CHALLENGE": 2, "VALIDATION": 2,
                      "AUTH_REQUIRED": 3, "AUTH_EXPIRED": 3, "NOT_FOUND": 4, "ENDPOINT_UNSUPPORTED": 4, "NETWORK": 5}
        for entry in art.CLI_SESSION:
            self.assertTrue(entry["command"].startswith("zindi "))
            if entry["exit"] == 0:
                self.assertEqual(entry["stream"], "stdout")
                self.assertTrue(entry["output"].startswith('{"ok": true'))
            else:
                self.assertEqual(entry["stream"], "stderr")
                code = entry["output"].split('"code": "')[1].split('"')[0]
                self.assertEqual(exit_codes[code], entry["exit"])

    def test_palette_contrast(self):
        for theme, palette in instrument.PALETTES.items():
            for surface in instrument.SURFACES:
                for color in instrument.TEXT_COLORS:
                    with self.subTest(theme=theme, surface=surface, color=color):
                        self.assertGreaterEqual(instrument.contrast(palette[color], palette[surface]), 4.5)
            for flag in ["ch0", "ch1", "ch2", "ch3"]:
                with self.subTest(theme=theme, flag=flag):
                    self.assertGreaterEqual(instrument.contrast(palette["screen"], palette[flag]), 4.5)
            page = "#0D1117" if theme == "dark" else "#FFFFFF"
            for trace in ["ch0", "ch1", "ch2", "ch3"]:
                with self.subTest(theme=theme, page=page, trace=trace):
                    self.assertGreaterEqual(instrument.contrast(palette[trace], page), 3)

    def test_motion_runs_once_and_settles_quickly(self):
        self.assertLessEqual(art.MOTION_END, 5)
        for name, svg in art.assets().items():
            with self.subTest(name=name):
                self.assertNotIn("infinite", svg)
                if name.startswith("hero-") and "static" not in name:
                    self.assertIn('class="shutter"', svg)
                else:
                    self.assertNotIn("class=", svg)

    def test_unsafe_links_rejected(self):
        for value in ["javascript:alert(1)", "https://", "https://foo\nbar", 'https://foo/"bad']:
            with self.subTest(value=value), self.assertRaises(ValueError):
                build.safe_url(value)


if __name__ == "__main__":
    unittest.main()
