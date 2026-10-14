# -*- coding: utf-8 -*-
"""Motion for VibeUpSlides decks: hooks, motion sets, tokens, intensity, film strips.

Motion belongs to the brand. The framework only names the places where something may move (the hooks) and
when (the choreography); HOW it moves comes from a motion set chosen for the brand, is tuned by the brand's
motion tokens, and may be finished off by the brand's own motion.css.

    hooks        classes in the masters and in the engine, listed below
    motion set   motion/<name>.css: one idea of movement applied to every hook, as @keyframes m-<role>
    tokens       brand.json "motion": ease, duration, stagger, travel, change -> --m-ease, --m-dur, --m-stagger,
                 --m-travel, --m-change-x, --m-change-dur (written by build.tokens_css through tokens_css() here)
    motion.css   optional file in the brand's library folder, loaded after the set: the brand's signature move
    intensity    the deck's "motion" field: off, calm, standard, expressive; scales how much moves

The resting state is always the finished slide: start values stand in the `from` keyframe only and the
animations fill backwards, so once an animation is over the element is simply itself again, and PDF export,
print, overviews and previews are right without special handling.
The R key replays the animation of the current slide. With "reduce motion" set in the system nothing moves.

Use from a generator:
    import motion
    ... slides with class mslide and the classes below ...
    add(motion.assets(brand, "standard"))      # once at the end; MOTION_ASSETS is the same for the default set

Hooks on the section (always together with mslide):
    mcover      cover slide: accent shape, big logo, then the title
    mchap       chapter slide with <div class="wedge mwipe"></div>: the accent shape makes its large move
    mcount      chapter slide with chapter_number(nr): the chapter numeral
    mstatement  statement slide
    mquote      quote slide: the quotation mark, the quote, who said it
    mphoto      full bleed: the photo is revealed
    mkpi        slide with bars(...): numbers count up, bars grow along
    mlt         full bleed with lower_third(...) for videos
    (no class)  line_chart(...): the lines draw from left to right; chevron_fill(stages): a stage fills per click
    msting      logo intro, see logo_intro()
On headings: class mtext (h1 or h2) splits the heading into words, the <em> word is the accent word.
Hooks in the engine (master.html): anim (staggered entrance), f (click step), h1 and chapter titles, kicker,
the accent shape, the big logo, large numerals, the slide change.

Roles a set defines as keyframes (a brand's motion.css may redefine single ones):
    m-item m-title m-label m-word m-accent m-shape m-wipe m-logo m-numeral m-roll m-figure m-drift
    m-bar m-mark m-photo m-rule m-panel m-sting
"""
import json, os, re

HERE = os.path.dirname(os.path.abspath(__file__))
SETS_DIR = os.path.join(HERE, "motion")

DEFAULT_SET = "rise"
TOKENS = {"ease": "cubic-bezier(.22,.61,.36,1)", "duration": 0.7, "stagger": 0.1, "travel": 28, "change": "slide"}
LEVELS = ("off", "calm", "standard", "expressive")
ROLES = ("m-item", "m-title", "m-label", "m-word", "m-accent", "m-shape", "m-wipe", "m-logo", "m-numeral", "m-roll",
         "m-figure", "m-drift", "m-bar", "m-mark", "m-photo", "m-rule", "m-panel", "m-sting")

_EASE = re.compile(r"^(linear|ease|ease-in|ease-out|ease-in-out|step-start|step-end|cubic-bezier\(\s*-?[\d.]+(\s*,\s*-?[\d.]+){3}\s*\)"
                   r"|steps\(\s*\d+(\s*,\s*[a-z-]+)?\s*\)|linear\([\d.,%\s-]+\))$")
_HEAD = re.compile(r"\A\s*/\*vs\s*(\{.*?\})\s*\*/", re.S)


# ---------------------------------------------------------------- sets, profile, tokens

def _dir_of(brand):
    return brand.get("_dir") if isinstance(brand, dict) else None

def sets(brand_dir=None):
    """All motion sets: {name: {name, title, character, fits, tokens, css}}, in catalogue order. The framework's own,
    and with brand_dir the sets in the brand's library (motion/<name>.css), such as `site`, the one copied from
    its website; a brand's set of the same name goes before the framework's."""
    out = {}
    for folder in (SETS_DIR, os.path.join(brand_dir, "motion") if brand_dir else None):
        if not folder or not os.path.isdir(folder):
            continue
        for fn in sorted(os.listdir(folder)):
            if not fn.endswith(".css"):
                continue
            text = open(os.path.join(folder, fn), encoding="utf-8").read()
            m = _HEAD.match(text)
            if not m:
                continue
            try: meta = json.loads(m.group(1))
            except ValueError: continue
            meta.setdefault("name", fn[:-4]); meta["own"] = folder != SETS_DIR
            meta["css"] = re.sub(r"/\*.*?\*/", "", text[m.end():], flags=re.S).strip()
            out[meta["name"]] = meta
    return dict(sorted(out.items(), key=lambda kv: (kv[1].get("order", 500), kv[0])))

def catalog(current=None, brand_dir=None):
    """Text list of the sets with their character, the brand's current one marked with *."""
    lines = []
    for name, s in sets(brand_dir).items():
        lines.append(f"{'*' if name == current else ' '} {name:8s} {s.get('character', '')}")
        lines.append(f"           fits: {s.get('fits', '')}")
    return "\n".join(lines)

def _number(v, lo, hi, default):
    try: return min(hi, max(lo, float(v)))
    except (TypeError, ValueError): return default

def profile(brand=None):
    """The motion profile of a brand, filled up: engine defaults, then the set's own tokens, then what brand.json says.
    brand: the brand dict (as from build.load_brand), a bare "motion" dict, or None."""
    given = brand or {}; brand_dir = _dir_of(given)
    if "motion" in given or "colors" in given or "_dir" in given:
        given = given.get("motion") or {}
    if isinstance(given, str):
        given = {"set": given}
    all_sets = sets(brand_dir)
    name = given.get("set") if given.get("set") in all_sets else DEFAULT_SET
    p = dict(TOKENS, **(all_sets.get(name, {}).get("tokens") or {}))
    p.update({k: v for k, v in given.items() if k in TOKENS and v is not None})
    ease = str(p["ease"]).strip()
    return {"set": name, "ease": ease if _EASE.match(ease) else TOKENS["ease"],
            "duration": _number(p["duration"], .1, 2.5, TOKENS["duration"]), "stagger": _number(p["stagger"], 0, .5, TOKENS["stagger"]),
            "travel": _number(p["travel"], 0, 200, TOKENS["travel"]), "change": p["change"] if p["change"] in ("slide", "fade", "none") else "slide"}

def tokens_css(brand=None):
    """The motion tokens of a brand as CSS declarations for :root (called by build.tokens_css)."""
    p = profile(brand)
    x, dur = {"slide": ("60px", ".55s"), "fade": ("0px", ".45s"), "none": ("0px", "0s")}[p["change"]]
    return (f"--m-ease:{p['ease']};--m-dur:{p['duration']:g}s;--m-stagger:{p['stagger']:g}s;--m-travel:{p['travel']:g}px;"
            f"--m-change-x:{x};--m-change-dur:{dur};")

def intensity(value):
    """The deck's "motion" field as one of off, calm, standard, expressive. true is standard, false is off."""
    if value is None or value is True:
        return "standard"
    if value is False:
        return "off"
    v = str(value).strip().lower()
    return {"true": "standard", "on": "standard", "false": "off", "none": "off", "0": "off", "1": "standard"}.get(v, v if v in LEVELS else "standard")

_KF_PROPS = ("opacity", "transform", "translate", "scale", "rotate", "filter", "clip-path", "animation-timing-function")

def _px(v, k):
    """A length of the website scaled for the slide (measured at 1440 px, a slide is 1920 wide) and by k; percentages
    of the element stay, held to a third of it, pixels to 90."""
    m = re.fullmatch(r"(-?[\d.]+)(px|%|em|rem)?", v.strip())
    if not m: return None
    n, u = float(m.group(1)), m.group(2) or "px"
    if n == 0: return "0"
    if u == "%": n = max(-33.0, min(33.0, n)) * k; return f"{round(n, 1):g}%"
    if u in ("em", "rem"): n = n * 16
    n = max(-90.0, min(90.0, n * 1.33 * k)); return f"{round(n):g}px"

def _transform(v, k):
    """transform: translate…() scale…() rotate…() as the separate properties the sets use ({translate, scale,
    rotate}), scaled by k. None for what cannot be taken over (matrix, skew, 3D rotation)."""
    out, tx, ty, sx, sy = {}, "0", "0", None, None
    for fn, args in re.findall(r"([a-zA-Z0-9]+)\(([^)]*)\)", v):
        a = [x.strip() for x in args.split(",")]; f = fn.lower()
        if f in ("translate", "translate3d"):
            tx = _px(a[0], k); ty = _px(a[1], k) if len(a) > 1 else "0"
        elif f == "translatex": tx = _px(a[0], k)
        elif f == "translatey": ty = _px(a[0], k)
        elif f in ("translatez", "perspective"): pass      # depth tricks for the graphics card, nothing that shows
        elif f in ("scale", "scale3d"):
            sx = float(a[0]); sy = float(a[1]) if len(a) > 1 else sx
        elif f == "scalex": sx = float(a[0]); sy = sy if sy is not None else 1.0
        elif f == "scaley": sy = float(a[0]); sx = sx if sx is not None else 1.0
        elif f in ("rotate", "rotatez"):
            m = re.fullmatch(r"(-?[\d.]+)deg", a[0])
            if not m: return None
            out["rotate"] = f"{max(-12.0, min(12.0, float(m.group(1)) * k)):g}deg"
        else: return None
        if tx is None or ty is None: return None
    if tx != "0" or ty != "0": out["translate"] = f"{tx} {ty}"
    if sx is not None:
        s = lambda x: f"{max(.5, 1 + (x - 1) * k):.3g}"
        out["scale"] = s(sx) if sy == sx else f"{s(sx)} {s(sy)}"
    return out

def frames_css(frames, k=1.0):
    """The keyframes of a website's entrance (frames: {property: ["0% value", "60% value", …]}, as the analysis
    reads them) as the body of a set's @keyframes rule: every step before the end with what the element is then;
    the end is the finished slide. k makes the way longer or shorter (titles travel further, labels less).
    None when nothing of it can be taken over."""
    steps = {}
    for prop, vals in (frames or {}).items():
        prop = prop.strip().lower()
        if prop not in _KF_PROPS and not prop.startswith("-webkit-transform"): continue
        prop = "transform" if prop.startswith("-webkit-transform") else prop
        for kv in vals:
            m = re.match(r"\s*([\w%.,\s]+?)\s+(\S.*)$", kv)
            if not m: continue
            for key in m.group(1).split(","):
                key = key.strip().lower(); off = {"from": 0.0, "to": 100.0}.get(key)
                if off is None:
                    try: off = float(key.rstrip("%"))
                    except ValueError: continue
                steps.setdefault(off, {})[prop] = m.group(2).strip().rstrip(";")
    rules = []
    for off in sorted(steps):
        if off >= 100: continue
        decl = []
        for prop, v in steps[off].items():
            if prop == "opacity":
                try: decl.append(f"opacity:{max(0.0, min(1.0, float(v))):g}")
                except ValueError: pass
            elif prop == "transform":
                if v in ("none", "initial"): continue
                tr = _transform(v, k)
                if tr is None: return None
                decl += [f"{p}:{x}" for p, x in tr.items()]
            elif prop in ("translate", "scale", "rotate"):
                tr = _transform(f"{prop}({','.join(v.split())})", k)
                if tr is None: return None
                decl += [f"{p}:{x}" for p, x in tr.items()]
            elif prop == "filter":
                b = re.search(r"blur\(\s*([\d.]+)px\s*\)", v)
                if b: decl.append(f"filter:blur({min(24.0, float(b.group(1)) * k):g}px)")
            elif prop == "clip-path" and re.fullmatch(r"inset\([\d.%\s]+\)", v): decl.append(f"clip-path:{v}")
            elif prop == "animation-timing-function" and _EASE.match(v): decl.append(f"animation-timing-function:{v}")
        if decl: rules.append(f"{off:g}%{{{';'.join(decl)}}}")
    return "".join(rules) or None

def _entrance(facts):
    """The website's entrance animation that most of its elements play, with its keyframes; None without one."""
    ent = [a for a in (facts.get("animations") or {}).get("in_use", []) if a.get("kind") == "entrance" and a.get("frames")]
    return max(ent, key=lambda a: a.get("count") or 0) if ent else None

def site_set(facts, url=""):
    """A motion set copied from what was measured on the brand's website (raw/motion.json): the way its elements
    arrive while scrolling becomes the way a slide's elements arrive. Returns the text of the set file, or None when
    the site shows no entrance that could be copied."""
    rv = facts.get("scroll_reveal") or {}
    rows = [r for r in rv.get("samples") or [] if r.get("kinds")] if rv.get("found") else []
    kinds, n, watched = {}, 0, bool(rows)
    def med(vals):
        vals = sorted(vals); return vals[len(vals) // 2] if vals else 0
    if rows:
        n = len(rows)
        for r in rows:
            for k in r["kinds"]: kinds[k] = kinds.get(k, 0) + 1
        num = lambda r, k: float(r.get("before", {}).get(k) or 0) if isinstance(r.get("before", {}).get(k), (int, float)) else 0.0
        ty = med([num(r, "ty") for r in rows if abs(num(r, "ty")) > 3]); tx = med([num(r, "tx") for r in rows if abs(num(r, "tx")) > 3])
        sc = med([num(r, "scale") for r in rows if abs(num(r, "scale") - 1) > .015 and num(r, "scale") > 0]) or 1
        bl = med([num(r, "blur") for r in rows if num(r, "blur") > 0]) or (8 if kinds.get("blur") else 0)
    else:                                                   # no scroll reveal: entrances the site plays as keyframe animations
        ent = [a for a in (facts.get("animations") or {}).get("in_use", []) if a.get("kind") == "entrance"]
        for a in ent:
            n += 1
            for d in a.get("does") or []: kinds[{"rise or drop": "rise"}.get(d, d)] = kinds.get({"rise or drop": "rise"}.get(d, d), 0) + 1
        if not ent or not set(kinds) & {"fade", "rise", "slide", "scale", "mask", "blur"}: return None
        ty, tx, sc, bl = (24 if kinds.get("rise") else 0), (24 if kinds.get("slide") else 0), (.95 if kinds.get("scale") else 1), (8 if kinds.get("blur") else 0)
    share = lambda k: kinds.get(k, 0) >= max(1, n * .25)
    mask, fade = share("mask"), share("fade") or not (share("rise") or share("drop") or share("slide") or share("scale") or share("mask"))
    rise, drop, slide, scale, blur = share("rise"), share("drop"), share("slide"), share("scale") and sc != 1, share("blur") and bl > 0
    def frm(k=1.0, extra=""):
        p = []
        if fade: p.append("opacity:0")
        if mask: p.append("clip-path:inset(0 0 100% 0)")
        x = f"calc(var(--mt)*{(1 if tx >= 0 else -1) * k:g})" if slide else "0"
        y = f"calc(var(--mt)*{(-1 if drop and not rise else 1) * k:g})" if (rise or drop or mask) else "0"
        if x != "0" or y != "0": p.append(f"translate:{x} {y}")
        if scale: p.append(f"scale:{1 + (sc - 1) * k:.3g}")
        if blur: p.append(f"filter:blur({bl * k:g}px)")
        if extra: p.append(extra)
        return "from{" + ";".join(p) + "}" if p else ""
    sug = (facts.get("suggestion") or {}).get("tokens") or {}
    ease = rv.get("easing") if rv.get("easing") and _EASE.match(str(rv.get("easing"))) and rv.get("easing") not in ("ease", "linear") else sug.get("ease", TOKENS["ease"])
    dur = rv.get("duration_s") or sug.get("duration") or TOKENS["duration"]
    dist = rv.get("distance_px") or max(abs(ty), abs(tx)) or 24
    tokens = {"ease": ease if _EASE.match(str(ease)) else TOKENS["ease"], "duration": round(min(1.4, max(.3, float(dur))), 2),
              "stagger": round(min(.25, max(.04, float(rv.get("stagger_s") or sug.get("stagger") or TOKENS["stagger"]))), 3),
              "travel": int(min(90, max(6, float(dist) * 1.33))) if (rise or drop or slide or mask) else 0, "change": "fade"}   # measured at 1440 px, a slide is 1920 wide
    real = _entrance(facts)                                 # the keyframes of the site's entrance: used when the reveal is played by it, or when there is no reveal
    if real and not frames_css(real["frames"]): real = None
    if real and rows and (rv.get("driven_by") or {}).get("css animation", 0) * 2 < sum((rv.get("driven_by") or {}).values() or [0]): real = None
    if real:
        if not rv.get("duration_s") and real.get("duration"): tokens["duration"] = round(min(1.4, max(.3, float(real["duration"]))), 2)
        if (not rv.get("easing") or rv.get("easing") in ("ease", "linear")) and _EASE.match(str(real.get("easing") or "")) and real["easing"] not in ("ease", "linear"): tokens["ease"] = real["easing"]
        tokens["travel"] = 0                                 # the ways are in the keyframes themselves
    said = [w for w, on in (("fade in", fade), (f"rise by about {abs(ty):g} px" if watched else "rise", rise), ("come down from above", drop and not rise), (f"slide in from the {'right' if tx >= 0 else 'left'}", slide),
                            (f"grow from {sc:.2g} of their size" if watched else "grow a little", scale), ("come into focus", blur), ("are uncovered by a mask", mask)) if on]
    if real: said = [f"enter the way its animation \u201c{real['name']}\u201d does it, with its own keyframes ({frames_css(real['frames'])})"]
    character = (f"Copied from the website: its elements {', '.join(said)}, over {tokens['duration']:g} s"
                 + (f", one after the other every {tokens['stagger']:g} s" if rv.get("stagger_s") else "") + (f" ({n} element(s) watched while scrolling)." if watched else f" (read from {n} entrance animation(s) of the site; how far they travel was not measured, the distances are the framework's)."))
    head = {"name": "site", "order": 1, "title": "Like the website", "character": character,
            "fits": "this brand, if the deck should move the way its website does" + (f" ({url})" if url else ""), "tokens": tokens}
    if real:                                                # the site's own keyframes, with their real ways and steps
        frm = lambda k=1.0, extra="": frames_css(real["frames"], k) or ""
    kf = [("m-item", frm()), ("m-title", frm(1.2)), ("m-label", frm(.6)), ("m-word", frm(.5) if not mask else "from{opacity:0;translate:0 .4em}"), ("m-accent", ""),
          ("m-shape", "from{opacity:0;translate:3% 0}"), ("m-wipe", "from{opacity:0;translate:6% 0}"), ("m-logo", frm()), ("m-numeral", frm(1.4)), ("m-roll", ""),
          ("m-figure", frm()), ("m-drift", "from{scale:1.05}"), ("m-bar", "from{width:0}"), ("m-mark", frm()),
          ("m-photo", "from{opacity:0;scale:1.03" + (f";filter:blur({bl * 2:g}px)" if blur else "") + "}"), ("m-rule", "from{opacity:0}"), ("m-panel", frm()), ("m-sting", frm(1.2))]
    return ("/*vs " + json.dumps(head, ensure_ascii=False) + " */\n.mslide{--mseq:.4}\n"
            + "\n".join(f"@keyframes {name}{{{body}}}" for name, body in kf) + "\n")

def write_site_set(brand_dir, facts, url=""):
    """Write the set copied from the website into the brand's library (motion/site.css). Returns its path, or None
    when there is nothing to copy; an older one is removed then."""
    css = site_set(facts, url); path = os.path.join(brand_dir, "motion", "site.css")
    if not css:
        if os.path.exists(path): os.remove(path)
        return None
    os.makedirs(os.path.dirname(path), exist_ok=True)
    open(path, "w", encoding="utf-8").write(css)
    return path

def brand_css(brand):
    """The brand's own motion.css (signature moves), comments removed."""
    d = (brand or {}).get("_dir") if isinstance(brand, dict) else None
    p = os.path.join(d, "motion.css") if d else None
    if not p or not os.path.exists(p):
        return ""
    return re.sub(r"/\*.*?\*/", "", open(p, encoding="utf-8").read(), flags=re.S).strip()

def assets(brand=None, level="standard", set_name=None):
    """The block a deck needs once, after its slides: hook styles, the brand's set, its motion.css, the script.
    level off loads the set that does nothing and cuts from slide to slide."""
    level = intensity(level)
    all_sets = sets(_dir_of(brand))
    name = "none" if level == "off" else (set_name if set_name in all_sets else profile(brand)["set"])
    css = all_sets.get(name, {}).get("css", "")
    own = "" if level == "off" else brand_css(brand)
    return ("\n<style id=\"motion-hooks\">" + HOOKS_CSS + "</style>\n"
            f"<style id=\"motion-set\" data-set=\"{name}\">\n{css}\n</style>\n"
            + (f"<style id=\"motion-brand\">\n{own}\n</style>\n" if own else "")
            + "<script>document.documentElement.setAttribute('data-motion-set','" + name + "');"
              "document.documentElement.setAttribute('data-motion','" + level + "');</script>\n"
            + "<script>" + HOOKS_JS + "</script>\n")


HOOKS_CSS = r'''
/* ---------- Motion hooks: where and when. How things move is in the motion set that follows (@keyframes m-...). ---------- */
.mslide{--d:.15s;--wg:calc(var(--ms)*.65);--mseq:1}

/* Headings split into words (mtext); the <em> word is the accent word and comes last */
.mtext .mw{display:inline-block;vertical-align:bottom}
.mtext .mw>span,.mtext .maccent em{display:inline-block}
.active.mslide .mtext{animation:none}
.active.mslide h1:not(.mtext),.active.mslide h2:not(.mtext){animation:m-title calc(var(--md)*1.15) var(--me) var(--d) backwards}
.active .mtext .mw>span{animation:m-word calc(var(--md)*1.05) var(--me) backwards;animation-delay:calc(var(--d) + var(--i,0)*var(--wg))}
.active .mtext .maccent em{animation:m-accent var(--md) var(--mw-ease,var(--me)) backwards;animation-delay:calc(var(--d) + var(--n,1)*var(--wg) + var(--md)*.75)}
.active.mslide .kicker{animation-delay:max(0s,calc(var(--d) - var(--md)*.2))}
.active.mslide .lead{animation:m-label var(--md) var(--me) backwards;animation-delay:calc(var(--d) + var(--md)*1.2)}
.active.mslide .who{animation:m-label var(--md) var(--me) backwards;animation-delay:calc(var(--d) + var(--md)*1.6)}

/* Cover (mcover): shape, logo, then the title */
.mcover{--d:calc(var(--md)*1.25*var(--mseq))}
.active.mcover .biglogo{animation-delay:calc(var(--md)*.7*var(--mseq))}

/* Chapter (mchap, shape with mwipe): the large move of the accent shape, then the title */
.active .wedge.mwipe{animation:m-wipe calc(var(--md)*2.1) var(--mw-ease,var(--me)) backwards}
.mchap{--d:calc(var(--md)*1.15*var(--mseq))}
.active.mchap .ghost{animation-delay:var(--d)}

/* Chapter numeral (mcount, chapter_number()): one reel per digit */
.mnumber{line-height:1}
.mnumber .mcol{display:inline-block;height:1em;overflow:hidden;vertical-align:top}
.mnumber .mreel{display:block;line-height:1;transform:translateY(calc(var(--digit)*-1em))}
.active .mnumber .mreel{animation:m-roll calc(var(--md)*2.3) var(--m-roll-ease,cubic-bezier(.2,.7,.2,1)) backwards;animation-delay:calc(var(--md)*.35 + var(--c,0)*var(--m-roll-gap,0s))}
.mcount{--d:calc(var(--md)*.45)}
.active.mcount .ghost{animation-delay:calc(var(--md)*.2)}

/* Statement, quote, photo */
.mstatement{--d:calc(var(--md)*.35)}
.mquote .mark{transform-origin:left bottom}
.active.mquote .mark{animation:m-mark calc(var(--md)*.6) var(--me) .1s backwards}
.mquote{--d:calc(var(--md)*.8)}
.active.mphoto .image{animation:m-photo calc(var(--md)*1.85) var(--mw-ease,var(--me)) backwards}
.mphoto{--d:calc(var(--md)*1.3*var(--mseq))}

/* Process chevrons fill up on a click (chevron_fill()) */
.mchev .c.f{opacity:1;transform:none;background-image:linear-gradient(90deg,var(--accent) 0 50%,transparent 50% 100%);
  background-size:200% 100%;background-position:100% 0;transition:background-position var(--md) var(--mw-ease,var(--me))}
.mchev .c.f h3,.mchev .c.f p,.mchev .c.f .m{transition:color calc(var(--md)*.4) calc(var(--md)*.5)}
.mchev .c.f.on{background-position:0 0}
.mchev .c.f.on h3,.mchev .c.f.on p{color:var(--on-accent)}.mchev .c.f.on .m{color:color-mix(in srgb,var(--on-accent) 85%,transparent)}

/* Key figures with bars (bars(), slide mkpi) */
.mbars{margin-top:70px;display:grid;gap:34px;max-width:1600px}
.mrow{display:grid;grid-template-columns:340px 1fr 180px;align-items:center;gap:36px}
.mrow .ml{font-size:30px;font-weight:500}
.mrow .mbar{height:26px;background:var(--soft)}
.mrow .mbar i{display:block;height:100%;width:var(--w);background:var(--ink);transform-origin:left center}
.mrow:first-child .mbar i{background:var(--accent)}
.mrow .mvalue{font-weight:var(--w-display);font-size:76px;line-height:1;text-align:right;font-variant-numeric:tabular-nums}
.mrow:first-child .mvalue{color:var(--accent-text)}
.active .mrow{animation:m-item var(--md) var(--me) backwards;animation-delay:calc(var(--md)*.4 + var(--i)*var(--ms)*1.5)}
.active .mrow .mbar i{animation:m-bar calc(var(--md)*2) var(--m-bar-ease,cubic-bezier(.2,.7,.2,1)) backwards;animation-delay:calc(var(--md)*.7 + var(--i)*var(--ms)*1.5)}

/* Column chart (columns()): the columns come up one after the other from left to right, each number follows its
   column, the ring on the marked column closes the build */
.mcols{position:relative;display:grid;grid-auto-flow:column;grid-auto-columns:1fr;gap:min(44px,3%);width:100%;height:100%;line-height:1.2}
.mcols::after{content:"";position:absolute;left:0;right:0;bottom:52px;height:3px;background:var(--muted)}
.mcol{display:grid;grid-template-rows:1fr 52px;min-width:0;min-height:0}
.mcol .mc{display:flex;flex-direction:column;justify-content:flex-end;align-items:center;min-height:0}
.mcol b{position:relative;flex:none;height:52px;line-height:52px;font-size:30px;font-weight:500;color:var(--muted);font-variant-numeric:tabular-nums;white-space:nowrap}
.mcol i{display:block;flex:none;width:100%;height:calc((100% - 108px)*var(--h));background:color-mix(in srgb,var(--ink) 32%,var(--paper));transform-origin:center bottom}
.mcol>span{align-self:end;text-align:center;font-size:24px;line-height:36px;color:var(--muted);white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.mcol.mk i{background:var(--accent)}
.mcol.mk b{color:var(--ink);font-weight:700;margin-bottom:30px}
/* the ring is drawn around the number itself and centred on it by translate, whatever the number's width */
.mcol.mk b::after{content:"";box-sizing:border-box;position:absolute;left:50%;top:50%;width:max(96px,calc(100% + 64px));height:96px;translate:-50% -50%;border:6px solid var(--accent);border-radius:50%}      /* as wide as the number needs: the ring never runs through a digit */
.active .mcol i{animation:m-col calc(var(--md)*1.5) var(--m-bar-ease,cubic-bezier(.2,.7,.2,1)) backwards;animation-delay:calc(var(--md)*.5 + var(--i)*var(--ms)*2.2)}
.active .mcol b{animation:m-item var(--md) var(--me) backwards;animation-delay:calc(var(--md)*1.3 + var(--i)*var(--ms)*2.2)}
.active .mcol.mk b::after{animation:m-pop calc(var(--md)*.9) var(--me) backwards;animation-delay:calc(var(--md)*2 + var(--n)*var(--ms)*2.2)}
/* with "step": true every column is a click step of its own */
.mcol.f{transform:none;transition:none}
.active .mcol.f i,.active .mcol.f b,.active .mcol.f.mk b::after{animation:none}
.active .mcol.f.on i{animation:m-col calc(var(--md)*1.5) var(--m-bar-ease,cubic-bezier(.2,.7,.2,1)) backwards}
.active .mcol.f.on b{animation:m-item var(--md) var(--me) calc(var(--md)*.8) backwards}
.active .mcol.f.on.mk b::after{animation:m-pop calc(var(--md)*.9) var(--me) calc(var(--md)*1.4) backwards}
/* what is said about the chart (the callout beside it) comes when the chart stands */
.active .mcols~* .anim{animation-delay:calc(var(--md)*2.2 + var(--ms)*14)}
@keyframes m-col{from{scale:1 0}}
@keyframes m-pop{from{opacity:0;scale:.5}}
/* Bars that grow along a time axis (Gantt): --s is the period a bar starts in, --p how many it covers; the bars are
   uncovered at an even pace from left to right, so the build reads like time passing */
/* (the ring of a marked column stands clear above its column: 108px are kept free above the tallest one) */
.mgantt{--mg:calc(var(--md)*.3)}
.active .mgantt .mgbar:not(.f){animation:m-grow calc(var(--mg)*var(--p,1)) linear backwards;animation-delay:calc(var(--md)*.6 + var(--mg)*(var(--s,1) - 1))}
.active .mgantt .mgpoint:not(.f){animation:m-pop calc(var(--md)*.8) var(--me) backwards;animation-delay:calc(var(--md)*.6 + var(--mg)*var(--s,1))}
/* as click steps (the default of the timeline master): one bar per click, drawn from its start to its end, then the milestones from left to right */
.mgantt .f{transform:none;transition:none}
.mgantt .mgbar.f.on{animation:m-grow calc(var(--md)*.5 + var(--mg)*var(--p,1)) var(--me) backwards}
.mgantt .mgpoint.f.on{animation:m-pop calc(var(--md)*.8) var(--me) backwards;animation-delay:calc(var(--mg)*var(--s,1)*.5)}
@keyframes m-grow{from{clip-path:inset(0 100% 0 0)}}

/* Line chart (line_chart()) */
.mcurve .mline{stroke-dasharray:1 1;stroke-dashoffset:0}
.mcurve line{stroke:color-mix(in srgb,var(--line) 45%,var(--paper))}
.mcurve text{fill:var(--muted)}.mcurve circle{stroke:var(--paper)}
.active .mcurve .mline{animation:m-draw var(--mc-dur,1.4s) linear var(--mc-start,.15s) backwards}
.active .mcurve .mpoint{animation:m-point .35s ease-out backwards;animation-delay:calc(var(--mc-start,.15s) + var(--i)*var(--mc-step,.2s))}
@keyframes m-draw{from{stroke-dashoffset:1}}
@keyframes m-point{from{opacity:0}}

/* Lower third (lower_third(), slide mlt) */
.mlower{position:absolute;left:var(--pad);bottom:190px;display:flex;align-items:stretch;z-index:4}
.mltaccent{width:18px;background:var(--accent);transform-origin:bottom}
.mltfield{background:var(--deep);padding:26px 44px 26px 32px;color:var(--on-deep);display:flex;flex-direction:column;gap:8px}
.mltfield b{color:var(--on-deep);font-weight:700;font-size:44px;line-height:1.1;display:block;overflow:hidden}
.mltfield small{font-size:24px;letter-spacing:.04em;color:color-mix(in srgb,var(--on-deep) 75%,transparent);display:block;overflow:hidden}
.mltfield b span,.mltfield small span{display:inline-block}
.active .mltaccent{animation:m-rule calc(var(--md)*.65) var(--mw-ease,var(--me)) calc(var(--md)*.4) backwards}
.active .mltfield{animation:m-panel calc(var(--md)*.85) var(--mw-ease,var(--me)) calc(var(--md)*.9) backwards}
.active .mltfield b span{animation:m-word calc(var(--md)*.85) var(--me) calc(var(--md)*1.5) backwards}
.active .mltfield small span{animation:m-word calc(var(--md)*.85) var(--me) calc(var(--md)*1.7) backwards}

/* Logo intro (logo_intro()) */
.msting{background:var(--deep)}
.msting .wedge{--wt:84%;--wb:72%}
html[data-motif="block"] .msting .wedge{--wt:80%;--wb:80%}
.active .wedge.mwipe2{animation:m-wipe calc(var(--md)*2.3) var(--mw-ease,var(--me)) backwards}
.mslogo{position:absolute;left:50%;top:50%;width:620px;transform:translate(-50%,-50%);z-index:2}
.active .mslogo{animation:m-sting calc(var(--md)*1.4) var(--mw-ease,var(--me)) calc(var(--md)*1.35) backwards}
.mspartner{position:absolute;left:var(--pad);bottom:70px;height:64px;z-index:2}
.active .mspartner{animation:mfade .8s calc(var(--md)*2.7) var(--me) backwards}
@keyframes mfade{from{opacity:0}}
.mskick{position:absolute;left:var(--pad);top:70px;color:color-mix(in srgb,var(--on-deep) 55%,transparent);z-index:2}
.active .mskick{animation:mfade .6s calc(var(--md)*3.3) var(--me) backwards}

/* ---------- Intensity of the deck ("motion" in deck.json): how much moves, whatever the set ---------- */
/* calm: titles and elements enter over a short way, the large pieces simply stand there */
html[data-motion="calm"] .slide{--m-k:.6}
html[data-motion="calm"] .mslide{--mseq:0}
html[data-motion="calm"] .slide.active .wedge,html[data-motion="calm"] .slide.active .biglogo,html[data-motion="calm"] .slide.active .ghost,
html[data-motion="calm"] .slide.active .mnumber .mreel,html[data-motion="calm"] .slide.active.mphoto .image,
html[data-motion="calm"] .slide.active.fullbleed .image img,html[data-motion="calm"] .slide.active.mquote .mark{animation:none}
/* expressive: longer ways, a wider stagger, and the titles of content slides move too */
html[data-motion="expressive"] .slide{--m-k:1.6;--md:calc(var(--m-dur)*1.15)}
html[data-motion="expressive"] .slide.active:not(.mslide) h2{animation:m-title calc(var(--md)*1.15) var(--me) .05s backwards}
html[data-motion="expressive"] .slide.active:not(.mslide) .lead{animation:m-label var(--md) var(--me) calc(var(--md)*.5) backwards}
/* off: nothing moves, slides and click steps cut */
html[data-motion="off"] .slide,html[data-motion-set="none"] .slide{transition:none}
/* one slide may move less or more than its deck ("move" on the slide) */
html .slide[data-move="calm"]{--m-k:.6;--md:var(--m-dur)}
html .slide[data-move="expressive"]{--m-k:1.6;--md:calc(var(--m-dur)*1.15)}
html #deck .slide[data-move="off"] *,html #deck .slide[data-move="off"] *::before,html #deck .slide[data-move="off"] *::after{animation:none!important;transition:none!important}
'''

HOOKS_JS = r'''
(function(){
  var root=document.documentElement;
  function still(){ return root.classList.contains('export')||root.getAttribute('data-motion')==='off'||root.getAttribute('data-motion-set')==='none'||/[?&]export=1/.test(location.search)||
    (window.matchMedia&&window.matchMedia('(prefers-reduced-motion: reduce)').matches); }
  /* Split headings into words so that a set can move every word on its own; elements such as <em> stay whole */
  function word(node,i){ var outer=document.createElement('span'), inner=document.createElement('span');
    outer.className='mw'+(node.nodeName==='EM'?' maccent':''); outer.style.setProperty('--i',i);
    if(typeof node==='string') inner.textContent=node; else inner.appendChild(node.cloneNode(true));
    outer.appendChild(inner); return outer; }
  function split(el){
    if(el.querySelector('[data-s]')) return;                /* a text marked inside the heading stays as the deck file has it */
    if(el.hasAttribute('data-s')) el.vsRaw=el.innerHTML;    /* an editable heading: the editing puts this back while it is open */
    var parts=[], i=0;
    Array.prototype.slice.call(el.childNodes).forEach(function(n){
      if(n.nodeType===3){ n.textContent.split(/(\s+)/).forEach(function(t){ if(!t) return;
        if(/^\s+$/.test(t)) parts.push(document.createTextNode(' ')); else parts.push(word(t,i++)); }); }
      else if(n.nodeName==='BR') parts.push(n.cloneNode());
      else if(n.nodeType===1) parts.push(word(n,i++));
    });
    el.innerHTML=''; parts.forEach(function(t){ el.appendChild(t); }); el.style.setProperty('--n',i);
  }
  document.querySelectorAll('.mtext').forEach(split);
  window.vsSplit=function(el){ if(el.vsRaw===undefined||!el.classList.contains('mtext')) return; el.innerHTML=el.vsRaw; split(el); };
  window.vsUnsplit=function(el){ if(el.vsRaw!==undefined&&el.querySelector('.mw')) el.innerHTML=el.vsRaw; };
  /* Format a number in the language of the slide, English if the language tag is not usable */
  function format(x,slide){
    try{ return Number(x).toLocaleString((slide&&slide.getAttribute('lang'))||'en'); }
    catch(err){ return Number(x).toLocaleString('en'); }
  }
  /* Numbers next to bars follow their bar: the number shown is the share of the bar that has grown so far.
     At rest (export, overview, reduced motion, sets without movement) that is the full number. */
  function sync(s){
    (s||document).querySelectorAll('.mrow').forEach(function(row){
      var v=row.querySelector('.mvalue'), bar=row.querySelector('.mbar i'); if(!v) return;
      var target=parseFloat(v.getAttribute('data-target'))||0, ratio=1, slide=row.closest('.slide');
      if(bar&&slide&&slide.classList.contains('active')&&!still()){
        var share=(parseFloat(bar.style.getPropertyValue('--w'))||0)/100, full=bar.parentNode.getBoundingClientRect().width*share;
        if(full>0) ratio=Math.max(0,Math.min(1,bar.getBoundingClientRect().width/full));
        if(ratio>.995) ratio=1;
      }
      var text=format(Math.round(target*ratio),slide); if(v.textContent!==text) v.textContent=text;
    });
  }
  var running=false;
  function loop(){ var s=document.querySelector('.slide.active'); if(!s||!s.querySelector('.mvalue')||still()){ running=false; sync(); return; }
    sync(s); requestAnimationFrame(loop); }
  function watch(){ if(!running){ running=true; requestAnimationFrame(loop); } }
  document.querySelectorAll('.mslide').forEach(function(s){
    if(!s.querySelector('.mvalue')) return;
    new MutationObserver(function(){ if(s.classList.contains('active')) watch(); }).observe(s,{attributes:true,attributeFilter:['class']});
  });
  sync(); watch();
  /* A figure that counts up (.mcountup): whole numbers run from 0 to their value when the slide appears, fast and
     never longer than three seconds; anything that is not a plain whole number simply stands. */
  function countParse(el){
    var raw=el.textContent.trim(), m=raw.match(/^(\d{1,3})(([.,'   ])\d{3})+$/)||raw.match(/^\d+$/);
    if(!m) return;
    var sep=m[3]||'', n=parseInt(raw.replace(/\D/g,''),10), digits=String(n).length;
    if(!n) return;
    el.vsCount={n:n,sep:sep,text:raw,ms:Math.min(3000,n<99?900:1200+350*(digits-2))};
    el.style.fontVariantNumeric='tabular-nums';
  }
  function countText(c,v){ var s=String(v); return c.sep?s.replace(/\B(?=(\d{3})+(?!\d))/g,c.sep):s; }
  function countRun(s){
    s.querySelectorAll('.mcountup').forEach(function(el){
      var c=el.vsCount; if(!c) return;
      cancelAnimationFrame(el.vsRaf||0); if(el.vsAnim){ try{ el.vsAnim.cancel(); }catch(e){} el.vsAnim=null; }
      if(still()||!el.animate){ el.textContent=c.text; return; }
      /* the count is tied to an animation of the element, so pausing, finishing or cancelling animations holds for it too */
      var a=el.vsAnim=el.animate([{opacity:1},{opacity:1}],{duration:c.ms,easing:'cubic-bezier(.2,.7,.2,1)'});
      function done(){ if(el.vsAnim===a){ el.vsAnim=null; cancelAnimationFrame(el.vsRaf||0); el.textContent=c.text; } }
      a.onfinish=done; a.oncancel=done;
      function step(){
        if(el.vsAnim!==a) return;
        if(still()||!s.classList.contains('active')){ try{ a.cancel(); }catch(e){ done(); } return; }
        var p=a.effect.getComputedTiming().progress;
        if(p!==null) el.textContent=countText(c,Math.round(c.n*p));
        el.vsRaf=requestAnimationFrame(step);
      }
      el.textContent=countText(c,0); el.vsRaf=requestAnimationFrame(step);
    });
  }
  function countRest(){ document.querySelectorAll('.mcountup').forEach(function(el){ if(!el.vsCount) return; if(el.vsAnim){ try{ el.vsAnim.cancel(); }catch(e){} } cancelAnimationFrame(el.vsRaf||0); el.textContent=el.vsCount.text; }); }
  document.querySelectorAll('.mcountup').forEach(countParse);
  document.querySelectorAll('.slide').forEach(function(s){
    if(!s.querySelector('.mcountup')) return;
    var was=s.classList.contains('active');
    new MutationObserver(function(){ var is=s.classList.contains('active'); if(is&&!was) countRun(s); was=is; }).observe(s,{attributes:true,attributeFilter:['class']});
    if(was) countRun(s);
  });
  new MutationObserver(function(){ if(still()) countRest(); }).observe(root,{attributes:true,attributeFilter:['class','data-motion']});
  window.vsMotionSync=function(){ sync(); };      /* for tools that step through the animations frame by frame */
  /* R key: replay the animation of the current slide */
  function replay(){
    var s=document.querySelector('.slide.active'); if(!s) return;
    s.classList.remove('active'); s.querySelectorAll('.f').forEach(function(f){f.classList.remove('on');});
    void s.offsetWidth; s.classList.add('active'); countRun(s);
  }
  window.vsReplay=replay;
  document.addEventListener('keydown',function(e){
    if((e.key==='r'||e.key==='R')&&!e.metaKey&&!e.ctrlKey) replay();
  });
  /* the comparison page of the motion sets shows decks in frames and asks them to play a slide again */
  window.addEventListener('message',function(e){
    if(!e.data||e.data.vs!=='replay') return;
    if(e.data.slide&&window.vsGo&&window.vsGo(e.data.slide)) return;
    replay();
  });
})();
'''

# the block for the default set at standard intensity, for generators that do not know the brand
MOTION_ASSETS = assets()


# ---------------------------------------------------------------- film strip

STRIP_TIMES = (0.1, 0.3, 0.6, 1.0, 1.6, 3.0)

def film_strip(html, out, labels=None, times=STRIP_TIMES, title="", lang=None, thumb=(384, 216)):
    """Draw the motion of a built deck as one picture: one row per slide, one frame per time in `times` (seconds
    after the slide became current). The animations are paused and set to each time through the Web Animations
    API, so the frames are exact and the same on every run. Returns the path of the PNG."""
    import io
    from playwright.sync_api import sync_playwright
    from PIL import Image, ImageDraw
    rows = []
    with sync_playwright() as p:
        br = p.chromium.launch(); pg = br.new_page(viewport={"width": 1280, "height": 720})
        pg.goto("file://" + os.path.abspath(html) + (f"?lang={lang}" if lang else "")); pg.wait_for_timeout(900)
        n = pg.evaluate("document.querySelectorAll('.slide:not(.off)').length")
        pg.add_style_tag(content="#ui,#hint,#toast{display:none!important}")
        for i in range(1, n + 1):
            pg.evaluate(f"location.hash='#/{i}'"); pg.wait_for_timeout(700)
            pg.evaluate("""()=>{const s=document.querySelector('.slide.active'); s.classList.remove('active'); void s.offsetWidth; s.classList.add('active');
                window.__m=s.getAnimations({subtree:true}).filter(a=>!(a.transitionProperty)); __m.forEach(a=>a.pause());}""")
            frames = []
            for t in times:
                pg.evaluate(f"__m.forEach(a=>a.currentTime={t * 1000}); window.vsMotionSync&&vsMotionSync()")
                frames.append(Image.open(io.BytesIO(pg.screenshot())).convert("RGB").resize(thumb, Image.LANCZOS))
            rows.append(frames)
        br.close()
    tw, th = thumb; gap, left, top = 6, 96, 44
    sheet = Image.new("RGB", (left + len(times) * (tw + gap), top + len(rows) * (th + gap)), "#2b2b2d")
    d = ImageDraw.Draw(sheet)
    d.text((8, 8), title, fill="#ffffff")
    for k, t in enumerate(times):
        d.text((left + k * (tw + gap) + 4, 26), f"{t:g} s", fill="#bbbbbb")
    for r, frames in enumerate(rows):
        d.text((8, top + r * (th + gap) + 6), (labels[r] if labels and r < len(labels) else f"slide {r + 1}")[:14], fill="#ffffff")
        for k, im in enumerate(frames):
            sheet.paste(im, (left + k * (tw + gap), top + r * (th + gap)))
    os.makedirs(os.path.dirname(os.path.abspath(out)), exist_ok=True)
    sheet.save(out)
    return out


# ---------------------------------------------------------------- helpers for slides

def chapter_number(nr):
    """Big chapter numeral, one reel per digit (slide with classes chapter mslide mcount). nr: 1 to 99."""
    digits = f"{int(nr):02d}"
    columns = []
    for c, digit in enumerate(digits):
        d = int(digit)
        columns.append(f'<span class="mcol" style="--c:{c}"><span class="mreel" style="--digit:{d}">' + "<br>".join(str(k) for k in range(d + 1)) + '</span></span>')
    return f'<div class="ghost mnumber">{"".join(columns)}</div>'


def chevron_fill(stages):
    """stages: list of (marker, title, sentence). Every stage fills with the accent colour on one click."""
    cs = "".join(f'<div class="c f"><div class="m">{m}</div><h3>{h}</h3><p>{p}</p></div>' for m, h, p in stages)
    return f'<div class="chevron mchev">{cs}</div>'


def bars(rows, lang="en"):
    """rows: list of (label, number, share in percent of the bar width). The first row is in the accent colour.
    The slide needs the classes mslide mkpi. Numbers get a thousands separator: a dot for German (lang="de"),
    the English comma for every other language. The script then formats with the slide language and lets the
    number follow its bar while it grows."""
    def fmt(v):
        s = f"{v:,}"
        return s.replace(",", ".") if lang == "de" else s
    row_html = "".join(
        f'<div class="mrow" style="--i:{i}"><div class="ml">{l}</div><div class="mbar"><i style="--w:{w}%"></i></div>'
        f'<div class="mvalue" data-target="{v}">{fmt(v)}</div></div>' for i, (l, v, w) in enumerate(rows))
    return f'<div class="mbars">{row_html}</div>'


def columns(rows, mark=None, lang="en", step=False):
    """rows: list of (label, number). Columns from left to right, heights in proportion to the largest number.
    mark: number of the column that carries the point (1 is the first): accent colour and a ring on its number."""
    def fmt(v):
        try:
            s = f"{v:,}" if isinstance(v, (int, float)) else str(v)
        except (TypeError, ValueError):
            s = str(v)
        return s.replace(",", "\u2009").replace(".", ",").replace("\u2009", ".") if lang == "de" else s
    def num(v):
        try: return max(float(str(v).replace(",", ".")), 0.0)
        except (TypeError, ValueError): return 0.0
    rows = [(l, v) for l, v in rows]
    top = max([num(v) for _, v in rows] or [1.0]) or 1.0
    try: mark = int(mark)
    except (TypeError, ValueError): mark = 0
    cols = "".join(
        f'<div class="mcol{" mk" if i + 1 == mark else ""}{" f" if step else ""}" style="--i:{i};--h:{num(v) / top:.4f}"><div class="mc"><b>{fmt(v)}</b><i></i></div><span>{l}</span></div>'
        for i, (l, v) in enumerate(rows))
    return f'<div class="mcols" style="--n:{len(rows)}">{cols}</div>'


def lower_third(name, role):
    """Name and role as a lower third at the bottom left (slide with classes fullbleed mslide mlt)."""
    return (f'<div class="mlower"><div class="mltaccent"></div><div class="mltfield"><b><span>{name}</span></b>'
            f'<small><span>{role}</span></small></div></div>')


def logo_intro(lang, title="Logo intro", kicker="", partner=False):
    """Logo intro for videos: the accent shape makes its large move, then the inverse brand logo appears.
    partner=True adds a second logo that fades in at the bottom left.
    Needs images=dict(LOGO_INV=<inverse logo>) when building, plus PARTNER_INV=<inverse partner logo> with partner=True."""
    k = f'<div class="kicker mskick">{kicker}</div>' if kicker else ""
    p = '  <img class="mspartner" src="{{IMG_PARTNER_INV}}" alt="">\n' if partner else ""
    return (f'<section class="slide dark mslide msting no-header no-footer" lang="{lang}" data-title="{title}">\n'
            '  <div class="wedge mwipe2"></div>\n'
            '  <img class="mslogo" src="{{IMG_LOGO_INV}}" alt="">\n'
            f'{p}'
            f'  {k}\n</section>')


def line_chart(axis, series, ymax, width=1080, height=500, duration=1.4, start=0.15, step=None):
    """Line chart as inline SVG that builds up when the slide becomes current.
    axis: list of labels on the x axis (years, for example). series: list of (values, colour, numbers_above);
    colour is any CSS colour, also var(--accent). ymax: top value of the y axis, step: distance between the grid
    lines (default ymax/5).
    All lines draw at the same time from left to right (stroke-dashoffset), points and numbers appear as soon as
    the line reaches them, the last value is bigger. The resting state is the finished picture.
    duration: time for the whole line in seconds, start: delay after the slide change."""
    L, R, T, B = 70, 20, 30, 56
    n = len(axis)
    step = step or ymax / 5
    def x(i): return L + 40 + i * (width - L - 40 - R) / max(n - 1, 1)
    def y(v): return T + (height - T - B) * (1 - v / ymax)
    g = []
    v = 0
    while v <= ymax + 1e-9:
        g.append(f'<line x1="{L}" x2="{width - R}" y1="{y(v):.1f}" y2="{y(v):.1f}" stroke-width="1.5"/>'
                 f'<text x="{L - 14}" y="{y(v) + 7:.1f}" text-anchor="end" font-size="20">{v:g}</text>')
        v += step
    for i, a in enumerate(axis):
        g.append(f'<text x="{x(i):.1f}" y="{height - B + 36}" text-anchor="middle" font-size="20">{a}</text>')
    for values, color, above in series:
        pts = " ".join(f"{x(i):.1f},{y(w):.1f}" for i, w in enumerate(values))
        g.append(f'<polyline class="mline" pathLength="1" points="{pts}" fill="none" style="stroke:{color}" stroke-width="5" '
                 'stroke-linejoin="round" stroke-linecap="round"/>')
        for i, w in enumerate(values):
            last = i == len(values) - 1
            g.append(f'<circle class="mpoint" style="--i:{i};fill:{color}" cx="{x(i):.1f}" cy="{y(w):.1f}" r="{9 if last else 6}" stroke-width="2.5"/>')
            g.append(f'<text class="mpoint" style="--i:{i};fill:{color};font-weight:{"var(--w-display)" if last else 700}" x="{x(i):.1f}" '
                     f'y="{y(w) + (-18 if above else 34):.1f}" text-anchor="middle" font-size="{24 if last else 19}">{w:g}</text>')
    return (f'<svg class="mcurve" viewBox="0 0 {width} {height}" width="{width}" height="{height}" '
            f'style="display:block;font-family:inherit;overflow:visible;--mc-dur:{duration}s;--mc-start:{start}s;--mc-step:{duration / max(n - 1, 1):.3f}s">'
            + "".join(g) + '</svg>')
