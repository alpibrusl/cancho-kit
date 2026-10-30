"""The checker of the package kit, and the proof that it can fail: a conforming package passes, and each rule is broken once and refused."""
import pathlib
import subprocess
import sys
import tempfile
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import check_package_kit as kit  # noqa: E402

TIER2 = """# demo

One sentence.

> **Kind:** library · **Tier:** 2 · **Stage:** built

## A complete program

```
code
```

## What is special

Things. [the doc](docs/design.md)

## Quick start

## Examples

## What exists, what cannot yet

## Learn more

## Licence
"""


def package(readme=TIER2, files=("LICENSE", "NOTICE", "AGENTS.md", "docs/design.md")):
    d = pathlib.Path(tempfile.mkdtemp())
    (d / "README.md").write_text(readme)
    for f in files:
        (d / f).parent.mkdir(parents=True, exist_ok=True)
        (d / f).write_text("x\n")
    return d


def rules(d, **kw):
    return sorted({p["rule"] for p in kit.check(d, **kw)})


class Checker(unittest.TestCase):
    def test_a_conforming_package_passes(self):
        self.assertEqual(rules(package()), [])

    def test_an_empty_readme_is_refused(self):
        self.assertEqual(rules(package("")), ["kit.readme-empty"])

    def test_no_readme_is_refused(self):
        d = package()
        (d / "README.md").unlink()
        self.assertEqual(rules(d), ["kit.readme-missing"])

    def test_a_missing_kind_line_is_refused(self):
        self.assertIn("kit.kind-line-missing", rules(package(TIER2.replace("> **Kind:** library · **Tier:** 2 · **Stage:** built", ""))))

    def test_the_kind_and_tier_can_be_given_instead(self):
        d = package(TIER2.replace("> **Kind:** library · **Tier:** 2 · **Stage:** built", ""))
        self.assertEqual(rules(d, kind="library", tier=2), [])

    def test_an_unknown_kind_and_stage_are_refused(self):
        self.assertEqual(rules(package(TIER2.replace("library", "gadget"))), ["kit.kind-unknown"])
        self.assertEqual(rules(package(TIER2.replace("built", "shipped"))), ["kit.stage-unknown"])

    def test_every_required_section_is_required(self):
        for heading in ("A complete program", "What is special", "Quick start", "Examples", "What exists, what cannot yet", "Learn more", "Licence"):
            with self.subTest(heading=heading):
                self.assertIn("kit.section-missing", rules(package(TIER2.replace("## " + heading, "## Other"))))

    def test_the_order_of_sections_is_checked(self):
        swapped = TIER2.replace("## What is special", "## @@").replace("## Quick start", "## What is special").replace("## @@", "## Quick start")
        self.assertIn("kit.section-order", rules(package(swapped)))

    def test_a_heading_inside_a_code_fence_is_not_a_section(self):
        fenced = TIER2.replace("## Examples\n", "```\n## Examples\n```\n")
        self.assertIn("kit.section-missing", rules(package(fenced)))

    def test_the_files_of_the_tier_are_required(self):
        for missing in ("LICENSE", "NOTICE", "AGENTS.md"):
            with self.subTest(missing=missing):
                files = tuple(f for f in ("LICENSE", "NOTICE", "AGENTS.md", "docs/design.md") if f != missing)
                self.assertIn("kit.file-missing", rules(package(files=files)))

    def test_docs_agents_satisfies_the_agent_file(self):
        self.assertEqual(rules(package(files=("LICENSE", "NOTICE", "docs/agents.md", "docs/design.md"))), [])

    def test_a_broken_relative_link_is_refused_and_external_links_are_not_followed(self):
        self.assertIn("kit.link-broken", rules(package(TIER2.replace("docs/design.md", "docs/nope.md"))))
        self.assertEqual(rules(package(TIER2 + "\n[x](https://example.org/a) [y](#here) ![i](nothing.png)\n")), [])

    def test_tier_one_wants_more_and_tier_three_less(self):
        self.assertIn("kit.section-missing", rules(package(), tier=1))
        three = "# d\n\n> **Kind:** cli · **Tier:** 3 · **Stage:** design\n\n## What is special\n\n## Status\n\n## More\n\n## Licence\n"
        self.assertEqual(rules(package(three, files=("LICENSE",))), [])

    def test_the_command_line(self):
        run = lambda *a: subprocess.run([sys.executable, str(ROOT / "scripts" / "check_package_kit.py"), *a], capture_output=True, text=True)
        self.assertEqual(run(str(package())).returncode, 0)
        self.assertEqual(run(str(package(""))).returncode, 1)
        self.assertEqual(run().returncode, 2)
        self.assertEqual(run(str(package()), "--kind", "gadget").returncode, 2)


class Kit(unittest.TestCase):
    def test_the_templates_have_the_sections_of_their_tier_in_order(self):
        for kind, tier in (("cli", 1), ("library", 2)):
            with self.subTest(kind=kind):
                text = (ROOT / "templates" / kind / "README.md").read_text()
                found = kit.sections_found(text)
                want = kit.REQUIRED_SECTIONS[tier]
                self.assertEqual([s for s in want if s not in found], [])
                self.assertEqual(sorted(want, key=lambda s: found[s]), [s for s in kit.ORDER if s in want])
                m = kit.KIND_LINE.search(text)
                self.assertEqual((m.group(1), int(m.group(2))), (kind, tier))

    def test_this_repository_conforms_to_its_own_kit(self):
        self.assertEqual(kit.check(ROOT), [])


if __name__ == "__main__":
    unittest.main()
