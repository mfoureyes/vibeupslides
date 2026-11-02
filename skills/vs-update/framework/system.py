"""A slide system the brand already has: its styles and its approved slides, taken over as they are.

Some brands come with slides of their own that people have already approved: an HTML slide system with a master
stylesheet and decks built with it. Rebuilding those slides from the engine's masters loses what made them good.
This module takes them over instead:

- system_css(source, engine) keeps the rules of the system's stylesheet that the engine does not have (its own
  class names, their @media and @keyframes, its custom properties), so that its slides render as they did. The
  brand keeps them in library/<brand>/system.css; build.theme_css puts them under the brand's theme.
- slides(source, ...) cuts slides out of a built deck of that system, one per language, as "raw" slides with their
  classes, inner HTML (images stay embedded), title and source line, ready to be a shared slide of the brand.

The system stays the source: when it changes, run `vs.py system <brand> --from <file>` again.
"""
import html as H
import re

_CLASS = re.compile(r"\.(-?[_a-zA-Z][\w-]*)")


def _blocks(css):
    """Top-level blocks of a stylesheet: (prelude, body) with balanced braces; comments removed."""
    css = re.sub(r"/\*.*?\*/", "", css, flags=re.S)
    out, i, n = [], 0, len(css)
    while i < n:
        j = css.find("{", i)
        if j < 0: break
        depth, k = 1, j + 1
        while k < n and depth:
            if css[k] == "{": depth += 1
            elif css[k] == "}": depth -= 1
            k += 1
        out.append((css[i:j].strip(), css[j + 1:k - 1]))
        i = k
    return out


def _styles(text):
    """All stylesheet text of an HTML page (its <style> elements), or the text itself when it is a stylesheet."""
    found = re.findall(r"<style[^>]*>(.*?)</style>", text, flags=re.S | re.I)
    return "\n".join(found) if found else text


def known_classes(engine_css):
    return set(_CLASS.findall(re.sub(r"url\([^)]*\)", "", engine_css)))


def known_vars(engine_css):
    return set(re.findall(r"(--[\w-]+)\s*:", engine_css))


def system_css(source_text, engine_text):
    """The rules of a slide system the engine lacks. Returns (css, classes taken, custom properties taken)."""
    engine_css = _styles(engine_text)
    known, kvars = known_classes(engine_css), known_vars(engine_css)
    taken, props, frames, used_frames, keep = set(), {}, {}, set(), []

    def own(sel):
        cls = set(_CLASS.findall(sel))
        return cls - known

    def rule(prelude, body):
        parts = [p.strip() for p in prelude.split(",") if p.strip()]
        mine = [p for p in parts if own(p)]
        if not mine: return None
        for p in mine: taken.update(own(p))
        used_frames.update(re.findall(r"animation(?:-name)?\s*:\s*([\w-]+)", body))
        used_frames.update(re.findall(r"animation\s*:[^;]*?\b([a-z][\w-]*)\b\s+[\d.]+m?s", body))
        return ",".join(mine) + "{" + body.strip() + "}"

    for prelude, body in _blocks(_styles(source_text)):
        if prelude.startswith("@keyframes"):
            frames[prelude.split()[1]] = "@keyframes " + prelude.split()[1] + "{" + body.strip() + "}"
        elif prelude.startswith("@media") or prelude.startswith("@supports"):
            inner = [r for r in (rule(p, b) for p, b in _blocks(body)) if r]
            if inner: keep.append(prelude + "{" + "".join(inner) + "}")
        elif prelude.startswith("@"):
            continue
        elif prelude.strip() in (":root", "html", ":root,html"):
            for k, v in re.findall(r"(--[\w-]+)\s*:\s*([^;]+)", body):
                if k not in kvars: props[k] = v.strip()
        else:
            r = rule(prelude, body)
            if r: keep.append(r)
    names = "\n".join(keep)
    for f in sorted(used_frames):
        if f in frames: keep.append(frames[f])
    head = (":root{" + ";".join(f"{k}:{v}" for k, v in props.items()) + "}\n") if props else ""
    return head + "\n".join(keep) + "\n", sorted(taken), sorted(props)


_SECTION = re.compile(r"<section\b([^>]*)>(.*?)</section>", re.S)


def _attr(attrs, name):
    m = re.search(name + r'="([^"]*)"', attrs)
    return H.unescape(m.group(1)) if m else ""


def list_slides(source_text):
    """[(number per language, lang, title, id, classes)] of the slides in a built deck."""
    out, count = [], {}
    for m in _SECTION.finditer(source_text):
        a = m.group(1)
        cls = _attr(a, "class").split()
        if "slide" not in cls: continue
        lang = _attr(a, "lang") or "-"
        count[lang] = count.get(lang, 0) + 1
        out.append((count[lang], lang, _attr(a, "data-titel") or _attr(a, "data-title") or _plain(m.group(2))[:50],
                    _attr(a, "data-id"), " ".join(c for c in cls if c != "slide")))
    return out


def _plain(html):
    m = re.search(r"<h[12][^>]*>(.*?)</h[12]>", html, re.S)
    return re.sub(r"\s+", " ", re.sub(r"<[^>]+>", "", m.group(1) if m else "")).strip()


def _keep_classes(html, keep):
    """Leave only the classes that something styles: the engine, the system's stylesheet, or a <style> of the slide
    itself. Movement classes of another engine (its own script is not there) would otherwise hide or freeze text."""
    own = set(_CLASS.findall(" ".join(re.findall(r"<style[^>]*>(.*?)</style>", html, flags=re.S))))
    ok = keep | own
    def fix(m):
        cls = [c for c in m.group(1).split() if c in ok]
        return f'class="{" ".join(cls)}"' if cls else ""
    return re.sub(r'class="([^"]*)"', fix, html), ok


def slide(source_text, langs, title=None, sid=None, number=None, strip=("kicker",), keep=None):
    """One slide of a built deck as a raw slide of the engine, every language in one: {"master": "raw", "class",
    "html": {lang: inner HTML}, "name", "source"}. The slide is found by its title (data-titel / data-title),
    its data-id, or its number in the first language. Speaker notes stay behind: a deck writes its own.
    strip: classes of elements to leave out, e.g. the kicker when the brand has none.
    keep: the class names that are styled where the slide will live (engine and system.css); others are dropped."""
    found = {}
    for m in _SECTION.finditer(source_text):
        a, inner = m.group(1), m.group(2)
        if "slide" not in _attr(a, "class").split(): continue
        lang = _attr(a, "lang")
        if lang not in langs or lang in found: continue
        t = _attr(a, "data-titel") or _attr(a, "data-title")
        if title and t != title: continue
        if sid and _attr(a, "data-id") != sid: continue
        found[lang] = (a, inner)
    if number:
        found, per = {}, {}
        for m in _SECTION.finditer(source_text):
            a = m.group(1)
            if "slide" not in _attr(a, "class").split(): continue
            lang = _attr(a, "lang"); per[lang] = per.get(lang, 0) + 1
            if lang in langs and per[lang] == number: found[lang] = (a, m.group(2))
    if not found:
        raise ValueError("no slide with " + (f'title "{title}"' if title else f'id "{sid}"' if sid else f"number {number}") + " in the languages " + ", ".join(langs))
    out = {"master": "raw", "html": {}, "name": {}, "source": {}}
    for lang, (a, inner) in found.items():
        inner = re.sub(r"\s*<aside class=\"(notes|read|cues)\"[^>]*>.*?</aside>", "", inner, flags=re.S)
        for c in strip or ():
            inner = re.sub(r'\s*<div class="' + re.escape(c) + r'">.*?</div>', "", inner, flags=re.S)
        if keep is not None:
            inner, ok = _keep_classes(inner, keep)
        out["html"][lang] = inner.strip()
        out["name"][lang] = _attr(a, "data-titel") or _attr(a, "data-title") or _plain(inner)
        src = _attr(a, "data-quelle") or _attr(a, "data-source")
        if src: out["source"][lang] = src
        out["class"] = " ".join(c for c in _attr(a, "class").split() if c != "slide" and (keep is None or c in ok))
    for k in ("name", "source"):
        if not out[k]: del out[k]
    out["approved"] = True                       # taken over as it is: its sizes and words stay, the checks name them as hints
    out["fixed"] = True                          # its colours are its own: it does not turn dark with the scheme (key D)
    return out
