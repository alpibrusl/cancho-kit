# `landing.json`: the manifest of a landing page

`scripts/render_landing.py landing.json` renders `docs/index.html` in the layout of the landing pattern (cancho-www, `docs/landing-pattern.md`): the same sections with the same ids in the same order, one header, one footer, the package's own accent. The page is self-contained: its styles are inside it, so a package pins the kit by commit and nothing is fetched when the page is shown. `--check` fails when the page on disk is not what the manifest renders. A refusal has a rule tag (`kit.landing-*`) and exit status 2.

```json
{
  "name": "cancho-log",
  "tagline": "One sentence: the promise a reader can check.",
  "sub": "One sentence under it: what it does and for whom.",
  "kind": "library", "tier": 2, "stage": "built",
  "accent": "#0b7a75", "accent_dark": "#4fd1c5",
  "repo": "https://github.com/alpibrusl/cancho-log",
  "image": {"src": "docs/figures/x.svg", "alt": "what it shows", "caption": "optional"},
  "siblings": [["cancho-table", "https://alpibrusl.github.io/cancho-table/"]],
  "sections": { "...": "..." }
}
```

**Required fields:** `name`, `tagline`, `kind`, `tier`, `stage` (`design`, `built`, `measured`), `accent`, `accent_dark`, `repo`. `image` and `siblings` are optional.

**Sections**, in the order the page shows them. The five marked * are required by the pattern; the others are left out when the package has nothing true to put there.

| id | fields | shows |
|---|---|---|
| `why` | `title`, `lead`, `cards: [{title, text}]` | the promise as cards, with what it does not cover |
| `stories` * | `title`, `lead`, `cards: [{title, text, href}]` | the examples or the stories, linked |
| `how` * | `title`, `paragraphs`, optional `cards` | how it works |
| `watch` | `title`, `run`, `caption` | one real run, as printed by the binary (generate it, never type it) |
| `status` | `title`, `built`, `not_yet` | what exists and what does not |
| `results` * | `title`, `numbers: [{value, label}]`, `fine` | the numbers with their conditions; with none, the page says no figure is claimed |
| `try` * | `title`, `code`, `fine` | install and first command |
| `agent` | `title`, `code`, `fine` | the session of an agent |
| `docs` * | `title`, `cards: [{title, text, href}]` | where to go deeper |

Every string is HTML-escaped; there is no markup in a manifest. A figure or recording is the `image` of the page or a link in a card.

## What it is for

The tier-1 packages (`cancho-stats`, `-table`, `-ml`) keep the hand-written pages they have, which pass the pattern checker. The packages that have no landing page, or one that does not follow the pattern, get theirs from a manifest: to change the look of all of them, change `landing/landing.css` here and re-render; to change one, change its manifest.
