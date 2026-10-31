#!/usr/bin/env python3
"""Checks home pages against docs/landing-pattern.md: the required section ids in their relative order, a Stories link in the header and the stories region.

    python3 scripts/check_landing_pattern.py ../cancho-stats/docs/index.html ../cancho-table/docs/index.html ../cancho-ml/docs/index.html
"""
import re
import sys

REQUIRED = ["stories", "how", "results", "try", "docs"]


def check(path):
    s = open(path, encoding="utf-8").read()
    errs = []
    ids = re.findall(r'<section[^>]*\sid="([^"]+)"', s)
    for need in REQUIRED:
        if need not in ids:
            errs.append("no section with id %r" % need)
    present = [i for i in ids if i in REQUIRED]
    if [i for i in REQUIRED if i in present] != present:
        errs.append("the required sections are in the order %s, want %s" % (present, [i for i in REQUIRED if i in present]))
    header = re.search(r"<header.*?</header>", s, re.S)
    links = re.findall(r"<a[^>]*>([^<]*)</a>", header.group(0)) if header else []
    if "Stories" not in links:
        errs.append("the header has no Stories link (links: %s)" % links)
    if len(links) > 10:
        errs.append("the header has %d links (the brand and nine)" % len(links))
    if "<!--stories-->" not in s and not re.search(r'<section[^>]*id="stories"', s):
        errs.append("no stories region")
    return errs


def main(argv):
    bad = 0
    for p in argv:
        errs = check(p)
        print("%s: %s" % (p, "ok" if not errs else ""))
        for e in errs:
            print("  " + e)
        bad += bool(errs)
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]) if len(sys.argv) > 1 else 2)
