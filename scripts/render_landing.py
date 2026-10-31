#!/usr/bin/env python3
"""Renders the landing page of a package from its `landing.json`, in the layout of docs/landing-pattern.md (cancho-www): the same sections with the same ids in the same order, one header, one footer, the tool's own accent colour.

    python3 scripts/render_landing.py PATH/landing.json [-o PATH/docs/index.html] [--check]

`--check` fails when the page on disk is not what the manifest renders. The page is self-contained (its styles are inside), so a package pins the kit by commit and nothing is fetched when the page is shown. The format of `landing.json` is in docs/landing.md. Standard library only."""
import argparse
import html
import json
import pathlib
import re
import sys

HERE = pathlib.Path(__file__).resolve().parent
CSS = (HERE.parent / "landing" / "landing.css").read_text()
SECTIONS = ("why", "stories", "how", "watch", "status", "results", "try", "agent", "docs")   # the order of the pattern
REQUIRED = ("name", "tagline", "kind", "tier", "stage", "accent", "accent_dark", "repo")
STAGES = ("design", "built", "measured")


class Refuse(Exception):
    """a refusal with its rule tag"""

    def __init__(self, rule, message):
        super().__init__(message)
        self.rule = rule


def e(s):
    return html.escape(str(s), quote=True)


def need(d, key, where):
    if key not in d or d[key] in ("", None):
        raise Refuse("kit.landing-field-missing", "%s has no %r" % (where, key))
    return d[key]


def linked(items):
    return '<div class="cards">%s</div>' % "".join('<div class="card"><h3><a href="%s">%s</a></h3><p>%s</p></div>' % (e(c["href"]), e(c["title"]), e(c["text"])) for c in items)


def cards(items):
    return '<div class="cards">%s</div>' % "".join('<div class="card"><h3>%s</h3><p>%s</p></div>' % (e(c["title"]), e(c["text"])) for c in items)


def section(sid, title, lead, body, alt):
    return '<section%s id="%s"><div class="wrap">\n  <h2>%s</h2>\n%s%s\n</div></section>\n' % (' class="alt"' if alt else "", sid, e(title), ('  <p class="lead">%s</p>\n' % e(lead)) if lead else "", body)


def render(m):
    for k in REQUIRED:
        need(m, k, "the manifest")
    if m["stage"] not in STAGES:
        raise Refuse("kit.landing-stage", "the stage %r is not one of %s" % (m["stage"], ", ".join(STAGES)))
    name, repo = m["name"], m["repo"]
    sec = m.get("sections", {})
    for k in sec:
        if k not in SECTIONS:
            raise Refuse("kit.landing-section-unknown", "%r is not a section of the pattern (%s)" % (k, ", ".join(SECTIONS)))
    for k in ("stories", "how", "results", "try", "docs"):
        if k not in sec:
            raise Refuse("kit.landing-section-required", "the pattern requires the section %r" % k)
    out, alt = [], True
    nav = [("How it works", "#how", True), ("Stories", "#stories", False)]
    if "results" in sec:
        nav.append(("Results", "#results", True))
    nav += [("Try it", "#try", False), ("Docs", "#docs", True), ("GitHub", repo, False)]
    nav = sorted(nav, key=lambda n: ["#how", "#stories", "#results", "#try", "#docs", repo].index(n[1]))
    header = '<header class="top"><div class="wrap">\n  <a class="brand" href=".">%s</a>\n  <nav>%s</nav>\n</div></header>' % (e(name), "".join('<a%s href="%s">%s</a>' % (' class="opt"' if o else "", e(h), e(t)) for t, h, o in nav))
    hero_cta = '<a class="btn primary" href="#try">Try it</a><a class="btn" href="#how">See how it works</a>'
    hero = '<div class="wrap hero">\n  <p class="fine" style="margin:0 auto .6rem;text-align:center"><code>%s</code> &middot; tier %s &middot; %s</p>\n  <h1>%s</h1>\n  <p class="sub">%s</p>\n  <div class="cta">%s</div>\n</div>\n' % (e(m["kind"]), e(m["tier"]), e(m["stage"]), e(m["tagline"]), e(m.get("sub", "")), hero_cta)
    if "image" in m:
        hero += '<figure class="shot"><img src="%s" alt="%s"><figcaption>%s</figcaption></figure>\n' % (e(m["image"]["src"]), e(need(m["image"], "alt", "image")), e(m["image"].get("caption", "")))
    out.append(hero)
    for sid in SECTIONS:
        if sid not in sec:
            continue
        s = sec[sid]
        title, lead = need(s, "title", sid), s.get("lead", "")
        body = ""
        if sid in ("why", "docs"):
            body = cards(s["cards"]) if sid == "why" else linked(s["cards"])
        elif sid == "stories":
            body = linked(s["cards"])
        elif sid == "how":
            body = "".join("<p class=\"lead\">%s</p>" % e(p) for p in s.get("paragraphs", [])) + (cards(s["cards"]) if "cards" in s else "")
        elif sid == "watch":
            body = '<div class="term"><div class="bar"><i></i><i></i><i></i> a real run</div><pre>%s</pre></div>' % e(need(s, "run", "watch"))
            if s.get("caption"):
                body += '<p class="caption">%s</p>' % e(s["caption"])
        elif sid == "status":
            body = '<div class="cols"><div class="card"><h3>Built</h3><p>%s</p></div><div class="card"><h3>Not yet</h3><p>%s</p></div></div>' % (e(need(s, "built", "status")), e(need(s, "not_yet", "status")))
        elif sid == "results":
            body = '<div class="nums">%s</div>' % "".join('<div class="num"><b>%s</b><span>%s</span></div>' % (e(n["value"]), e(n["label"])) for n in s.get("numbers", []))
            if s.get("fine"):
                body += '<p class="fine">%s</p>' % e(s["fine"])
            elif not s.get("numbers"):
                body = '<p class="lead">No speed or accuracy figure is claimed yet.</p>'
        elif sid == "try":
            body = '<pre class="code">%s</pre>' % e(need(s, "code", "try")) + ('<p class="fine">%s</p>' % e(s["fine"]) if s.get("fine") else "")
        elif sid == "agent":
            body = '<pre class="code">%s</pre>' % e(need(s, "code", "agent")) + ('<p class="fine">%s</p>' % e(s["fine"]) if s.get("fine") else "")
        out.append(section(sid, title, lead, body, alt))
        alt = not alt
    foot = '<footer><div class="wrap">%s &middot; EUPL-1.2 &middot; written in <a href="https://github.com/alpibrusl/cancho">cancho</a>%s</div></footer>' % (e(name), "".join(' &middot; <a href="%s">%s</a>' % (e(h), e(t)) for t, h in m.get("siblings", [])))
    style = CSS.replace("@ACCENT@", m["accent"]).replace("@ACCENT_DARK@", m["accent_dark"])
    return ('<!doctype html>\n<html lang="en">\n<head>\n<meta charset="utf-8">\n<meta name="viewport" content="width=device-width, initial-scale=1">\n<title>%s: %s</title>\n<meta name="description" content="%s">\n<meta name="color-scheme" content="light dark">\n<style>\n%s</style>\n</head>\n<body>\n%s\n%s%s\n</body>\n</html>\n'
            % (e(name), e(m["tagline"].rstrip(".")), e(m.get("sub", m["tagline"])), style, header, "".join(out), foot))


def main(argv):
    ap = argparse.ArgumentParser()
    ap.add_argument("manifest")
    ap.add_argument("-o", "--out")
    ap.add_argument("--check", action="store_true")
    a = ap.parse_args(argv)
    path = pathlib.Path(a.manifest)
    try:
        m = json.loads(path.read_text())
    except (OSError, ValueError) as ex:
        print("render_landing: kit.landing-unreadable: %s" % ex)
        return 2
    out = pathlib.Path(a.out) if a.out else path.parent / "docs" / "index.html"
    try:
        page = render(m)
    except Refuse as ex:
        print("render_landing: %s: %s" % (ex.rule, ex))
        return 2
    except (KeyError, TypeError, AttributeError) as ex:
        print("render_landing: kit.landing-shape: the manifest does not have the shape of docs/landing.md (%s: %s)" % (type(ex).__name__, ex))
        return 2
    if a.check:
        if not out.exists() or out.read_text() != page:
            print("render_landing: %s is not what %s renders" % (out, path))
            return 1
        print("render_landing: up to date")
        return 0
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(page)
    print("render_landing: wrote %s" % out)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
