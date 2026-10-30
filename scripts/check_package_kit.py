#!/usr/bin/env python3
"""Checks a cancho package against the package kit (docs/package-structure.md in cancho-www): the files of its tier, the README sections of its kind in order, the kind and tier line, and that every relative link of the README resolves.

    python3 scripts/check_package_kit.py PATH-TO-PACKAGE [--kind cli|library|service|platform|language|site|kit] [--tier 1|2|3] [--json]

The kind and the tier are read from the README line `> **Kind:** cli · **Tier:** 1 · **Stage:** built` unless given. The exit status is 0 when nothing is wrong, 1 when the package does not conform, 2 on a bad invocation. Standard library only, no network."""
import json
import pathlib
import re
import sys

KINDS = ("cli", "library", "service", "platform", "language", "site", "kit")
STAGES = ("design", "built", "measured")

# the sections of a README, in the order of the kit; each is the list of headings (regular expressions on the heading text) that count as it
SECTIONS = [
    ("flow", r"one complete flow|a complete flow|a complete program|an example|ten-line program|try it"),
    ("special", r"what is special|why\b.*"),
    ("audience", r"for humans(,| and) for agents|for humans|for agents"),
    ("quickstart", r"(two-minute )?quick ?start|getting started"),
    ("examples", r"examples|worked examples|what you can do( now)?|what you get"),
    ("agent", r"use it with an ai agent|with an ai agent|built to be read by an agent|as an mcp server"),
    ("compare", r"compared with|how it compares|comparison"),
    ("status", r"what exists.*|what (it|\w+) cannot do( yet)?|status|limitations|what it is not"),
    ("fast", r"how fast|performance|benchmarks"),
    ("more", r"learn more|documentation|more"),
    ("licence", r"licen[cs]e"),
]
ORDER = [s for s, _ in SECTIONS]
PATTERN = {s: re.compile(r"^(%s)\W*$" % p, re.I) for s, p in SECTIONS}

REQUIRED_SECTIONS = {
    1: ["flow", "special", "audience", "quickstart", "examples", "agent", "compare", "status", "fast", "more", "licence"],
    2: ["flow", "special", "quickstart", "examples", "status", "more", "licence"],
    3: ["special", "status", "more", "licence"],
}
# a file is satisfied by any of its alternatives
REQUIRED_FILES = {
    1: [("README.md",), ("LICENSE",), ("NOTICE",), ("AGENTS.md", "docs/agents.md"), ("llms.txt", "docs/llms.txt"), ("docs/index.html",)],
    2: [("README.md",), ("LICENSE",), ("NOTICE",), ("AGENTS.md", "docs/agents.md")],
    3: [("README.md",), ("LICENSE",)],
}
KIND_LINE = re.compile(r"\*\*Kind:\*\*\s*([a-z]+)\s*[·|,]\s*\*\*Tier:\*\*\s*([123])(?:\s*[·|,]\s*\*\*Stage:\*\*\s*([a-z]+))?", re.I)
LINK = re.compile(r"(?<!!)\[[^\]]*\]\(([^)\s#][^)\s]*)(?:\s+\"[^\"]*\")?\)")
HEADING = re.compile(r"^(#{2,3})\s+(.*?)\s*#*\s*$")


def headings(text):
    """the headings of level two and three outside code fences, with their line numbers"""
    out, fence = [], False
    for n, line in enumerate(text.split("\n"), 1):
        if line.lstrip().startswith("```"):
            fence = not fence
            continue
        m = None if fence else HEADING.match(line)
        if m:
            out.append((n, re.sub(r"[`*_]", "", m.group(2)).strip()))
    return out


def sections_found(text):
    """{section: line} of the first heading that matches each section"""
    found = {}
    for n, h in headings(text):
        for s in ORDER:
            if s not in found and PATTERN[s].match(h):
                found[s] = n
                break
    return found


def check(root, kind=None, tier=None):
    root = pathlib.Path(root)
    problems = []

    def bad(rule, message):
        problems.append({"rule": rule, "message": message})
    readme = root / "README.md"
    if not readme.is_file():
        bad("kit.readme-missing", "no README.md")
        return problems
    text = readme.read_text(encoding="utf-8", errors="replace")
    if not text.strip():
        bad("kit.readme-empty", "README.md is empty")
        return problems
    m = KIND_LINE.search(text)
    if m:
        k, t, stage = m.group(1).lower(), int(m.group(2)), (m.group(3) or "").lower()
        kind = kind or k
        tier = tier or t
        if k not in KINDS:
            bad("kit.kind-unknown", "the kind %r is not one of %s" % (k, ", ".join(KINDS)))
        if stage and stage not in STAGES:
            bad("kit.stage-unknown", "the stage %r is not one of %s" % (stage, ", ".join(STAGES)))
    elif kind is None or tier is None:
        bad("kit.kind-line-missing", "README.md has no line `> **Kind:** cli · **Tier:** 1 · **Stage:** built`")
    if tier not in REQUIRED_SECTIONS:
        if tier is not None:
            bad("kit.tier-unknown", "the tier %r is not 1, 2 or 3" % (tier,))
        return problems
    found = sections_found(text)
    for s in REQUIRED_SECTIONS[tier]:
        if s not in found:
            bad("kit.section-missing", "no section for %r (tier %d, kind %s)" % (s, tier, kind))
    present = [s for s in ORDER if s in found and s in REQUIRED_SECTIONS[tier]]
    in_file = sorted(present, key=lambda s: found[s])
    if present != in_file:
        bad("kit.section-order", "the sections are in the order %s, want %s" % (in_file, present))
    for alternatives in REQUIRED_FILES[tier]:
        if not any((root / a).exists() for a in alternatives):
            bad("kit.file-missing", "no %s" % " or ".join(alternatives))
    for target in LINK.findall(text):
        if re.match(r"[a-z][a-z0-9+.-]*:", target, re.I) or target.startswith("#"):
            continue
        if not (root / target.split("#")[0]).exists():
            bad("kit.link-broken", "the link %r names no file" % target)
    return problems


def main(argv):
    args = [a for a in argv if not a.startswith("--")]
    opts = {}
    it = iter(argv)
    for a in it:
        if a in ("--kind", "--tier"):
            opts[a[2:]] = next(it, None)
    path = [a for a in args if a not in opts.values()]
    if len(path) != 1 or (opts.get("kind") and opts["kind"] not in KINDS) or (opts.get("tier") and opts["tier"] not in ("1", "2", "3")):
        print(__doc__)
        return 2
    problems = check(path[0], opts.get("kind"), int(opts["tier"]) if opts.get("tier") else None)
    if "--json" in argv:
        print(json.dumps({"ok": not problems, "problems": problems}, indent=1))
    else:
        for p in problems:
            print("%s: %s: %s" % (path[0], p["rule"], p["message"]))
        if not problems:
            print("%s: conforms" % path[0])
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
