# cancho-kit

The package kit of the cancho ecosystem: one structure for the READMEs, agent surface, examples, comparisons and numbers of every package, with a template per kind and a checker that can fail.

> **Kind:** kit · **Tier:** 3 · **Stage:** design

The standard is written in cancho-www (`docs/package-structure.md`, `docs/landing-pattern.md`); this repository holds what a package pins: the templates and the checker.

## Use it

The output below is a real run at the time of writing.

```console
$ python3 scripts/check_package_kit.py ../cancho-table --kind cli --tier 1
cancho-table: kit.section-missing: no section for 'audience' (tier 1, kind cli)
cancho-table: kit.section-missing: no section for 'compare' (tier 1, kind cli)
cancho-table: kit.file-missing: no AGENTS.md or docs/agents.md
cancho-table: kit.file-missing: no llms.txt or docs/llms.txt
```

The kind and the tier are one line of the package's README, `> **Kind:** cli · **Tier:** 1 · **Stage:** built`; given there, the options are not needed. Exit status 0 conforms, 1 does not, 2 a bad invocation.

## What is special

A checker that can fail: each rule has a test that breaks it once, and turning a rule off in the checker fails a test. It is the mechanism of a standard that asks every package to say what is measured and what is not, so it is held to the same rule.

## What is here

| path | what |
|---|---|
| `scripts/check_package_kit.py` | the checker: the files of the tier, the README sections of the kit in order, the kind line, the relative links |
| `tests/` | the proof that each rule can fail |
| `scripts/render_landing.py`, `landing/landing.css`, [docs/landing.md](docs/landing.md) | the landing page of a package, rendered from its `landing.json` in the layout of the landing pattern |
| `scripts/check_landing_pattern.py` | checks a home page against the pattern (copied from cancho-www, which is to drop its copy) |
| `templates/cli/`, `templates/library/` | the README skeleton of those kinds |


## What exists, what cannot yet

Built: the checker and its tests, the `cli` and `library` templates, the landing renderer. Not built: templates for `service`, `platform`, `language` and `site`; the generators now copied as `storylib.py` into four repositories; the check of the numbers a README quotes against the recorded benchmark output; the agent-transcript driver.

The checker tests that the structure is there, not that what is written is true. The measured-claims rule of the standard is enforced by the packages' own gates and by review, not by this script.

## Learn more

The standard: cancho-www, `docs/package-structure.md`. The landing-page pattern: `docs/landing-pattern.md` there.

## Licence

EUPL-1.2, copyright Alpibru S.L.
