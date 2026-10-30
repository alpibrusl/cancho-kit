# CLAUDE.md -- cancho-kit

The kit that gives the cancho packages one structure: templates per kind, the checker, and (later) the shared generators. The standard it implements is `docs/package-structure.md` in cancho-www; this repository is the mechanism.

- **Design before code.** A new rule of the checker or a new template starts as a change to the standard in cancho-www, with each claim marked measured, choice or open.
- **Gates are written before the code they judge and must be able to fail.** Every rule of `scripts/check_package_kit.py` has a test that breaks the rule once and sees it refused; a mutant of the checker that turns a rule off must fail a test.
- **Pinned, never copied.** A package takes the kit by commit; nothing in the kit is copied into a package. The one exception to date is `storylib.py`, which is still copied four times and is to be replaced by this.
- **Every refusal has a rule tag** (`kit.<name>`) and the checker never reaches a traceback.
- **Standard library only**, no network, no clock in a result.
- **Measured claims only.** A claim found false is corrected in place, in the document that made it.
- Licence EUPL-1.2, copyright Alpibru S.L. Commit trailer `Co-Authored-By: Claude Sonnet 5.5 <noreply@anthropic.com>`; PRs stay draft until the maintainer says merge; no force-push to main.
