# -*- coding: utf-8 -*-
"""A look from nothing: for people who have no brand and need a good presentation soon.

The framework carries a handful of styles (framework/styles/<name>/): each one is the start of a brand library,
with its colours, an open pair of typefaces, its shape, a motion set and a stylesheet. The user is shown three
of them side by side on the same slides, chooses, and the choice becomes a library of their own
(library/<name>/), which every other part of VibeUpSlides treats like a brand read from a website. From there it
grows with what the user corrects and shows: the decisions are kept in the library's design.md.

    style.json   {"name", "order", "title": {en, de}, "character": {en, de}, "fits": {en, de},
                  "fonts": ["Inter"] (open typefaces to fetch, the first is the body unless brand.fonts says otherwise),
                  "brand": {colors, fonts, shape, motion}}       as in brand.json
    theme.css    what makes the style more than colours and type
"""
import json, os, re, shutil, time

HERE = os.path.dirname(os.path.abspath(__file__))
UA = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 Chrome/126.0 Safari/537.36"

def styles():
    """{name: {"meta": style.json, "dir": folder}}, in the order they are offered."""
    out, root = {}, os.path.join(HERE, "styles")
    for n in sorted(os.listdir(root)) if os.path.isdir(root) else []:
        try: meta = json.load(open(os.path.join(root, n, "style.json"), encoding="utf-8"))
        except (OSError, ValueError): continue
        out[meta.get("name") or n] = {"meta": meta, "dir": os.path.join(root, n)}
    return dict(sorted(out.items(), key=lambda kv: (kv[1]["meta"].get("order", 500), kv[0])))

def _t(v, lang):
    return v.get(lang[:2], v.get("en", next(iter(v.values()), ""))) if isinstance(v, dict) else str(v or "")

def catalog(lang="en"):
    return "\n".join(f"{n}: {_t(s['meta'].get('title'), lang)}. {_t(s['meta'].get('character'), lang)}\n    fits: {_t(s['meta'].get('fits'), lang)}" for n, s in styles().items())

def _lum(h):
    h = h.strip().lstrip("#"); h = "".join(c * 2 for c in h) if len(h) == 3 else h
    r, g, b = (int(h[i:i + 2], 16) / 255 for i in (0, 2, 4)); lin = lambda c: c / 12.92 if c <= .03928 else ((c + .055) / 1.055) ** 2.4
    return .2126 * lin(r) + .7152 * lin(g) + .0722 * lin(b)

def fetch_font(family, cache):
    """An open typeface from Google Fonts, kept in the workspace's cache. Returns [{"weight", "style", "file" (path), "unicode_range"}],
    empty without a network or when the family is not there."""
    import urllib.request, urllib.parse
    d = os.path.join(cache, re.sub(r"[^a-z0-9]+", "-", family.lower())); idx = os.path.join(d, "index.json")
    if os.path.exists(idx):
        try: return json.load(open(idx, encoding="utf-8"))
        except ValueError: pass
    q = urllib.parse.quote_plus(family); css = None
    for spec in (f"{q}:ital,wght@0,100..900;1,100..900", f"{q}:wght@100..900", f"{q}:ital,wght@0,400;0,500;0,600;0,700;0,800;1,400;1,600", f"{q}:wght@300;400;500;600;700;800;900", f"{q}:wght@400;700", q):
        try:
            css = urllib.request.urlopen(urllib.request.Request(f"https://fonts.googleapis.com/css2?family={spec}&display=block", headers={"User-Agent": UA}), timeout=15).read().decode(); break
        except Exception: continue
    if not css: return []
    blocks = re.findall(r"/\*\s*([\w-]+)\s*\*/\s*@font-face\s*\{([^}]*)\}", css)
    keep = [(s, blk) for s, blk in blocks if s in ("latin", "latin-ext")] or blocks
    os.makedirs(d, exist_ok=True); out = []
    try:
        for subset, blk in keep:
            u = re.search(r"url\(([^)]+)\)", blk).group(1); w = re.search(r"font-weight:\s*([^;]+)", blk).group(1).strip(); st = re.search(r"font-style:\s*([^;]+)", blk).group(1).strip()
            fn = f"{re.sub(r'[^a-z0-9]+', '-', family.lower())}-{w.replace(' ', '-')}-{st}-{subset}.woff2"
            open(os.path.join(d, fn), "wb").write(urllib.request.urlopen(u, timeout=30).read())
            rng = re.search(r"unicode-range:\s*([^;]+)", blk)
            out.append({"weight": w, "style": st, "file": fn, **({"unicode_range": rng.group(1).strip()} if rng else {})})
    except Exception:
        shutil.rmtree(d, ignore_errors=True); return []
    json.dump(out, open(idx, "w", encoding="utf-8")); return out

def make(brand_dir, style, cache, name=None, accent=None, langs=None, author=None, fonts=True, own=None):
    """Write a brand library's start: brand.json, theme.css, the typefaces. From a style as it is, or, with `own`,
    as a look of its own that only leans on a style for what it does not say itself. own: {"ground", "ink", "accent",
    "deep", "head", "body", "radius", "motif", "motion", "head_case", "head_weight", "display_weight"}, any of them.
    Returns the notes to print (typefaces that could not be fetched stand in with the system's)."""
    s = styles()[style]; meta = json.loads(json.dumps(s["meta"])); notes = []; own = {k: v for k, v in (own or {}).items() if v not in (None, "")}
    data = meta["brand"]; data["name"] = name or _t(meta.get("title"), "en"); data["style"] = style; data["confirmed"] = False
    data["source"] = "design"
    if own:
        data["derived"] = True
        if own.get("ground") or own.get("ink") or own.get("deep"):
            data["colors"] = derive_colors(own.get("ground") or data["colors"]["paper"], own.get("ink"), own.get("accent") or (accent or data["colors"]["accent"]), own.get("deep"))
            accent = None if own.get("accent") else accent
        elif own.get("accent"): accent = own["accent"]
        f0 = data.setdefault("fonts", {}); fams = []
        for role in ("body", "head"):
            if own.get(role): f0[role] = {"family": own[role], "fallback": (f0.get(role) or {}).get("fallback") or "Helvetica Neue, Arial, sans-serif"}
            if (f0.get(role) or {}).get("family") and f0[role]["family"] not in fams: fams.append(f0[role]["family"])
        meta["fonts"] = fams
        for k in ("head_weight", "display_weight"):
            if own.get(k): f0[k] = int(own[k])
        sh = data.setdefault("shape", {})
        if own.get("radius") is not None: sh["radius"] = int(own["radius"])
        for k in ("motif", "head_case"):
            if own.get(k): sh[k] = own[k]
        if own.get("motion"): data["motion"] = {"set": own["motion"]}
    if langs: data["langs"] = list(langs); data["lang"] = langs[0]
    if author: data["author"] = author
    if accent:
        if not re.fullmatch(r"#?[0-9a-fA-F]{3}([0-9a-fA-F]{3})?", accent.strip()): raise ValueError("the accent colour is a hex value such as #E5352B")
        a = "#" + accent.strip().lstrip("#").upper(); c = data["colors"]; c["accent"] = a
        c["on_accent"] = "#FFFFFF" if _lum(a) < .32 else (c.get("ink") if _lum(c.get("ink", "#111111")) < .2 else "#111111")
        for k in ("accent_text", "accent_on_deep"): c.pop(k, None)      # worked out again from the new colour
    os.makedirs(os.path.join(brand_dir, "fonts"), exist_ok=True)
    f = data.setdefault("fonts", {}); f["files"] = []; f["families"] = []
    for fam in meta.get("fonts") or []:
        roles = [r for r in ("body", "head") if (f.get(r) or {}).get("family") == fam]
        got = fetch_font(fam, cache) if fonts else []
        for g in got:
            shutil.copy(os.path.join(cache, re.sub(r"[^a-z0-9]+", "-", fam.lower()), g["file"]), os.path.join(brand_dir, "fonts", g["file"]))
            f["files"].append({"family": fam, "weight": g["weight"], "style": g["style"], "file": "fonts/" + g["file"], **({"unicode_range": g["unicode_range"]} if g.get("unicode_range") else {})})
        f["families"].append({"family": fam, "roles": roles, "source": "google", "licence": "open", "status": "embedded" if got else "missing", "files": len(got), "weights": [],
                              "note": "open typeface from Google Fonts" if got else "could not be fetched (no network?): the system's typeface stands in; `vs.py fonts google <brand> \"" + fam + "\"` fetches it later"})
        if not got: notes.append(f"typeface {fam} could not be fetched: a system typeface stands in until `vs.py fonts google {os.path.basename(brand_dir)} \"{fam}\" --role {roles[0] if roles else 'body'}` has run")
    json.dump(data, open(os.path.join(brand_dir, "brand.json"), "w", encoding="utf-8"), indent=2, ensure_ascii=False)
    shutil.copy(os.path.join(s["dir"], "theme.css"), os.path.join(brand_dir, "theme.css"))
    return notes

def _rgb(h):
    h = h.strip().lstrip("#"); h = "".join(c * 2 for c in h) if len(h) == 3 else h
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))

def _hex(rgb):
    return "#%02X%02X%02X" % tuple(max(0, min(255, int(round(x)))) for x in rgb)

def _mix(a, b, t):
    A, B = _rgb(a), _rgb(b); return _hex(tuple(A[i] + (B[i] - A[i]) * t for i in range(3)))

def _contrast(a, b):
    la, lb = _lum(a), _lum(b); return (max(la, lb) + .05) / (min(la, lb) + .05)

def _sat(h):
    r, g, b = (x / 255 for x in _rgb(h)); mx, mn = max(r, g, b), min(r, g, b)
    return 0 if mx == 0 else (mx - mn) / mx

def derive_colors(ground, ink=None, accent=None, deep=None):
    """A whole set of colours from the two or three a look is made of: the ground of the slides, the colour of
    the type, the one colour that marks. Everything between them (quiet text, rules, soft areas) is mixed, and
    checked so that it can be read."""
    ground = _hex(_rgb(ground)); dark = _lum(ground) < .18
    ink = _hex(_rgb(ink)) if ink else ("#F1F2F4" if dark else "#161616")
    if _contrast(ink, ground) < 7: ink = "#F4F5F7" if dark else "#141414"      # type has to read from the back of a room
    accent = _hex(_rgb(accent)) if accent else ("#5EEAD4" if dark else "#2F5BEA")
    soft, ghost, line = _mix(ground, ink, .06), _mix(ground, ink, .10), _mix(ground, ink, .22)
    t = .6; muted = _mix(ground, ink, t)
    while _contrast(muted, soft) < 4.7 and t < .95: t += .03; muted = _mix(ground, ink, t)
    deep = _hex(_rgb(deep)) if deep else (_mix(ground, "#000000", .5) if dark else (ink if _lum(ink) < .06 else _mix(ink, "#000000", .25)))
    out = {"accent": accent, "on_accent": "#FFFFFF" if _contrast("#FFFFFF", accent) >= _contrast("#111111", accent) else "#111111", "ink": ink, "deep": deep,
           "on_deep": "#FFFFFF" if _lum(deep) < .3 else "#111111", "muted": muted, "line": line, "soft": soft, "ghost": ghost, "paper": ground}
    a = accent; k = 0                                        # the accent as small text on the ground: darkened or lightened until it reads
    while _contrast(a, ground) < 4.6 and k < 20: a = _mix(a, ink, .08); k += 1
    if a != accent: out["accent_text"] = a
    a = accent; k = 0
    while _contrast(a, deep) < 4.5 and k < 20: a = _mix(a, out["on_deep"], .1); k += 1
    if a != accent: out["accent_on_deep"] = a
    return out

def palette(image_path, n=8):
    """The colours of one picture by area: [(hex, share)], largest first."""
    from PIL import Image
    im = Image.open(image_path).convert("RGB"); im.thumbnail((320, 320))
    q = im.quantize(n, method=Image.Quantize.MEDIANCUT) if hasattr(Image, "Quantize") else im.quantize(n)
    pal = q.getpalette(); total = im.width * im.height
    return sorted(((_hex(pal[i * 3:i * 3 + 3]), c / total) for c, i in q.getcolors()), key=lambda x: -x[1])

def read_colors(colours):
    """From colours by area to the three a look is made of. colours: [(hex, share)]. Returns {"ground", "ink", "accent", "dark"};
    accent is None where nothing coloured takes any room."""
    merged = []
    for h, s in sorted(colours, key=lambda x: -x[1]):       # shades that are nearly the same count as one
        for m in merged:
            if sum(abs(a - b) for a, b in zip(_rgb(h), _rgb(m[0]))) < 42: m[1] += s; break
        else: merged.append([h, s])
    merged.sort(key=lambda x: -x[1]); total = sum(s for _, s in merged) or 1
    ground = merged[0][0]
    inks = [(h, s) for h, s in merged[1:] if _contrast(h, ground) >= 4.5 and _sat(h) < .35 and s / total > .004]
    ink = max(inks, key=lambda x: x[1])[0] if inks else None
    acc = [(h, s) for h, s in merged if _sat(h) >= .38 and s / total > .003 and h != ground and .04 < _lum(h) < .9]
    accent = max(acc, key=lambda x: _sat(x[0]) * (x[1] / total) ** .35)[0] if acc else None
    if accent is None and _sat(ground) >= .38: accent = ground      # a ground in full colour is itself the colour that marks
    return {"ground": ground, "ink": ink, "accent": accent, "dark": _lum(ground) < .18}

def examine(sources, out_dir):
    """Look at examples the user likes (slides as PDF, PowerPoint or HTML, pictures, addresses of web pages): photograph
    them where needed, and read from every one the ground, the colour of the type and the colour that marks. What a
    measurement cannot tell (the kind of typeface, the shapes, how full a slide is) is left to the eye: the function
    returns the pictures to look at. Returns [{"name", "kind", "pages", "ground", "ink", "accent", "dark", "look_at": [files], "note"}]."""
    import ingest
    os.makedirs(out_dir, exist_ok=True); found = []
    for i, src in enumerate(sources, 1):
        web = bool(re.match(r"https?://", src)); ext = os.path.splitext(src)[1].lower()
        name = re.sub(r"[^a-z0-9]+", "-", (re.sub(r"https?://(www\.)?", "", src) if web else os.path.splitext(os.path.basename(src))[0]).lower()).strip("-")[:40] or f"example-{i}"
        rec = {"name": name, "source": src, "kind": "web page" if web else ext.lstrip(".") or "file", "pages": 1, "look_at": [], "note": ""}
        try:
            if not web and not os.path.exists(src): raise RuntimeError("file not found")
            if not web and ext in (".png", ".jpg", ".jpeg", ".webp", ".gif"):
                dst = os.path.join(out_dir, name + ext); shutil.copy(src, dst); rec["look_at"] = [dst]; cols = palette(dst)
            elif web or ext in (".pdf", ".html", ".htm") or ext in ingest.PPT_EXT:
                d = os.path.join(out_dir, name); shutil.rmtree(d, ignore_errors=True); os.makedirs(d)
                f = ingest.ingest_html(src, d, name) if (web or ext in (".html", ".htm")) else (ingest.ingest_pdf(src, d, name) if ext == ".pdf" else ingest.ingest_pptx(src, d, None))
                rec["pages"] = f.get("pages") or f.get("slides") or 1; rec["look_at"] = [os.path.join(d, s) for s in (f.get("sheets") or [])[:3]]
                pages = sorted(os.path.join(d, "pages", x) for x in os.listdir(os.path.join(d, "pages"))) if os.path.isdir(os.path.join(d, "pages")) else []
                cols = [(h, s / max(1, len(pages[:24]))) for p in pages[:24] for h, s in palette(p)] if pages else [(c["hex"], c.get("share", 0) * c.get("page_count", 1)) for c in f.get("colours_flat") or []]
                if not cols: raise RuntimeError("no page pictures came out of this file")
            else: raise RuntimeError("this kind of file is not read: use PDF, PowerPoint, HTML, a picture or the address of a web page")
            rec.update(read_colors(cols))
        except Exception as e:
            rec["note"] = f"could not be read: {e}"
        found.append(rec)
    json.dump(found, open(os.path.join(out_dir, "findings.json"), "w", encoding="utf-8"), indent=1, ensure_ascii=False)
    return found

def journal(brand_dir, line, head=None):
    """design.md: how this look came about. Every decision of the user is a line with its date, so that nothing
    has to be said twice and a later session knows why the library looks the way it does."""
    p = os.path.join(brand_dir, "design.md")
    if not os.path.exists(p):
        open(p, "w", encoding="utf-8").write((head or "# How this look came about\n") + "\nDecisions, newest last. Each line: date, what was decided, and what it came from (a word of the user, an example they showed).\n\n")
    open(p, "a", encoding="utf-8").write(f"- {time.strftime('%Y-%m-%d')}: {line.strip()}\n")

def sample(name, lang="en", topic=None):
    """The same six slides for every style: what a deck is made of, so that styles can be told apart at a glance."""
    de = lang[:2] == "de"; n = name or ("Dein Name" if de else "Your name")
    T = (lambda a, b: b) if de else (lambda a, b: a)
    return [
        {"master": "cover", "kicker": n, "title": topic or T("A title that says what this is <em>about</em>", "Ein Titel, der sagt, worum es <em>geht</em>"), "lead": T("One sentence the audience takes home.", "Ein Satz, den das Publikum mitnimmt.")},
        {"master": "statement", "text": T("Sometimes a <em>single</em> sentence is enough.", "Manchmal reicht ein <em>einziger</em> Satz.")},
        {"master": "bullets", "kicker": T("The point", "Die Aussage"), "title": T("The key message stands here as a <em>full sentence</em>", "Hier steht die Kernaussage als <em>ganzer Satz</em>"),
         "bullets": [T("Every point is a full sentence.", "Jeder Punkt ist ein ganzer Satz."), T("Three to five are enough.", "Drei bis fünf reichen."), T("The source of a number goes into the footer.", "Die Quelle einer Zahl steht in der Fußzeile.")], "step": False},
        {"master": "kpis", "kicker": T("Figures", "Zahlen"), "title": T("The most important numbers at a <em>glance</em>", "Die wichtigsten Zahlen auf einen <em>Blick</em>"),
         "items": [{"value": "33", "label": T("teams this year", "Teams in diesem Jahr")}, {"value": "82", "label": T("people in the programmes", "Menschen in den Programmen")}, {"value": "60", "unit": "%", "label": T("go on after the first test", "machen nach dem ersten Test weiter")}]},
        {"master": "flow", "kicker": T("How it hangs together", "Wie es zusammenhängt"), "title": T("Three parts that <em>depend</em> on each other", "Drei Teile, die <em>aufeinander</em> angewiesen sind"),
         "items": [{"tag": T("First", "Zuerst"), "title": T("The idea", "Die Idee"), "text": T("Where it comes from.", "Woher sie kommt.")}, {"tag": T("Then", "Dann"), "title": T("The test", "Der Test"), "text": T("What turns it into something real.", "Was aus ihr etwas Echtes macht."), "style": "accent"}, {"tag": T("At last", "Am Ende"), "title": T("The market", "Der Markt"), "text": T("Who takes it up.", "Wer sie aufnimmt.")}]},
        {"master": "cards", "kicker": T("Offers", "Angebote"), "title": T("Three things <em>compared</em>", "Drei Dinge im <em>Vergleich</em>"), "cols": 3,
         "items": [{"n": "01", "title": T("The first", "Das Erste"), "text": T("Two sentences that explain the point.", "Zwei Sätze, die den Punkt erklären.")}, {"n": "02", "title": T("The second", "Das Zweite"), "text": T("Two sentences that explain the point.", "Zwei Sätze, die den Punkt erklären.")}, {"n": "03", "title": T("The third", "Das Dritte"), "text": T("The one that stands out.", "Das, was heraussticht."), "style": "accent"}]},
    ]
