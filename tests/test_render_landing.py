"""The landing renderer: a manifest renders a page in the layout of the pattern, a bad manifest is refused with its rule tag, `--check` sees drift, and text is escaped."""
import copy
import json
import pathlib
import subprocess
import sys
import tempfile
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import check_landing_pattern as pattern  # noqa: E402
import render_landing as landing  # noqa: E402

MANIFEST = json.loads((ROOT / "tests" / "fixtures" / "landing.json").read_text())


def run(*args):
    return subprocess.run([sys.executable, str(ROOT / "scripts" / "render_landing.py"), *args], capture_output=True, text=True)


def manifest_file(m):
    d = pathlib.Path(tempfile.mkdtemp())
    (d / "landing.json").write_text(json.dumps(m))
    return d / "landing.json"


class Render(unittest.TestCase):
    def test_the_page_follows_the_pattern(self):
        d = pathlib.Path(tempfile.mkdtemp())
        page = d / "index.html"
        page.write_text(landing.render(MANIFEST))
        self.assertEqual(pattern.check(str(page)), [])

    def test_the_sections_come_in_the_order_of_the_pattern(self):
        page = landing.render(MANIFEST)
        ids = [page.index('id="%s"' % s) for s in ("why", "stories", "how", "watch", "status", "results", "try", "docs")]
        self.assertEqual(ids, sorted(ids))

    def test_the_accent_is_the_packages_own_and_the_page_is_self_contained(self):
        page = landing.render(MANIFEST)
        self.assertIn("--accent: #0b7a75", page)
        self.assertIn("--accent: #4fd1c5", page)
        self.assertNotIn("@ACCENT", page)
        self.assertNotIn("<link", page)
        self.assertNotIn("<script", page)

    def test_text_is_escaped(self):
        m = copy.deepcopy(MANIFEST)
        m["sections"]["watch"]["run"] = "<script>alert(1)</script>"
        m["tagline"] = 'A "quoted" <b>title</b>'
        page = landing.render(m)
        self.assertNotIn("<script>", page)
        self.assertNotIn("<b>title</b>", page)

    def test_every_required_field_is_required(self):
        for key in landing.REQUIRED:
            with self.subTest(key=key):
                m = copy.deepcopy(MANIFEST)
                del m[key]
                r = run(str(manifest_file(m)))
                self.assertEqual(r.returncode, 2)
                self.assertIn("kit.landing-field-missing", r.stdout)

    def test_every_required_section_is_required(self):
        for key in ("stories", "how", "results", "try", "docs"):
            with self.subTest(key=key):
                m = copy.deepcopy(MANIFEST)
                del m["sections"][key]
                self.assertIn("kit.landing-section-required", run(str(manifest_file(m))).stdout)

    def test_an_unknown_section_and_stage_are_refused(self):
        m = copy.deepcopy(MANIFEST)
        m["sections"]["pricing"] = {"title": "x"}
        self.assertIn("kit.landing-section-unknown", run(str(manifest_file(m))).stdout)
        m = copy.deepcopy(MANIFEST)
        m["stage"] = "shipped"
        self.assertIn("kit.landing-stage", run(str(manifest_file(m))).stdout)

    def test_a_manifest_of_the_wrong_shape_is_refused_not_a_traceback(self):
        m = copy.deepcopy(MANIFEST)
        m["sections"]["why"]["cards"] = [{"title": "no text"}]
        r = run(str(manifest_file(m)))
        self.assertEqual(r.returncode, 2)
        self.assertIn("kit.landing-shape", r.stdout)
        self.assertNotIn("Traceback", r.stderr)
        self.assertEqual(run("/nonexistent/landing.json").returncode, 2)
        bad = pathlib.Path(tempfile.mkdtemp()) / "landing.json"
        bad.write_text("{not json")
        self.assertEqual(run(str(bad)).returncode, 2)

    def test_check_sees_drift(self):
        path = manifest_file(MANIFEST)
        self.assertEqual(run(str(path)).returncode, 0)
        self.assertEqual(run(str(path), "--check").returncode, 0)
        out = path.parent / "docs" / "index.html"
        out.write_text(out.read_text() + "<!-- edited by hand -->")
        self.assertEqual(run(str(path), "--check").returncode, 1)


if __name__ == "__main__":
    unittest.main()
