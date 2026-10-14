"""Render a deck from a content file and the master slides of a brand library.

A deck is a JSON file: which brand, which languages, and a list of slides. Every slide names a
master and fills its slots. Masters are HTML templates in <library>/<brand>/masters/ (the brand's
own) or in the framework's masters/ folder (the defaults). Nothing is written by hand per deck
unless a deck needs a look no master has yet.

Master file format:

    <!--vs {"name": "cards", "title": "Cards", "use": "...", "slots": {"title": "..."}, "sample": {...}} -->
    <section class="slide center" {{attrs}}>
      {{#kicker}}<div class="kicker">{{kicker}}</div>{{/kicker}}
      <h2>{{title}}</h2>
      {{#items}}<div class="card {{style}}">{{title}}</div>{{/items}}
      {{notes}}
    </section>

Template tags (a small subset of Mustache, values are inserted as HTML):
    {{name}}  {{a.b}}        value of a slot, empty if missing
    {{#name}}...{{/name}}    shown if the slot is set; repeated for every item of a list
    {{^name}}...{{/name}}    shown if the slot is missing or empty
    {{.}}                    the current list item, {{@i}} its number (1, 2, ...), {{@ii}} two digits (01)
    {{>helper arg ...}}      output of a helper: chapter_number, bars, columns, chevron_fill, line_chart, verdict, bgvideo,
                             lower_third, el (inline an SVG from the brand's elements/ folder), icon,
                             video, embed, scene (the media box of the slide, see media.py)
    {{attrs}}                lang, data-title, data-chapter, data-source of the slide
    {{notes}}                the speaker notes as <aside class="notes">
    {{IMG_NAME}}             left untouched, filled by the build step
"""
import hashlib, json, os, re

HERE = os.path.dirname(os.path.abspath(__file__))

_IMAGE = re.compile(r"^[^\n<>{}]+\.(jpe?g|png|webp|gif|svg|avif)$", re.I)
_TAG = re.compile(r"\{\{\s*([#^/>]?)\s*([^{}]*?)\s*\}\}")
_HEAD = re.compile(r"\A\s*<!--vs\s*(\{.*?\})\s*-->\s*", re.S)


# ---------------------------------------------------------------- masters

def parse_master(text, path=""):
    m = _HEAD.match(text)
    if not m:
        raise ValueError(f"{path}: a master starts with <!--vs {{...}} -->")
    try:
        meta = json.loads(m.group(1))
    except ValueError as e:
        raise ValueError(f"{path}: the header is not valid JSON ({e})")
    return meta, text[m.end():]

def load_masters(brand_dir=None):
    """All masters available to a brand: framework defaults, overridden by the brand's own files."""
    out = {}
    for origin, folder in (("framework", os.path.join(HERE, "masters")), ("brand", os.path.join(brand_dir or "", "masters"))):
        if not brand_dir and origin == "brand" or not os.path.isdir(folder):
            continue
        for fn in sorted(os.listdir(folder)):
            if fn.endswith(".html"):
                p = os.path.join(folder, fn)
                meta, body = parse_master(open(p, encoding="utf-8").read(), p)
                name = meta.get("name") or fn[:-5]
                out[name] = {"meta": meta, "body": body, "path": p, "origin": origin}
    for name, meta in FUNCTION_MASTERS.items():
        out[name] = {"meta": dict(meta, name=name), "body": None, "path": "(built in)", "origin": "framework"}
    return out

def catalog(brand_dir=None, full=False):
    """Text list of the masters with their slots, for choosing masters while writing a deck."""
    ms = load_masters(brand_dir)
    lines = []
    for name, m in sorted(ms.items(), key=lambda kv: (kv[1]["meta"].get("order", 500), kv[0])):
        meta = m["meta"]
        if (meta.get("preview_only") or meta.get("hidden")) and not full:      # hidden: the engine can show it, nothing offers it
            continue
        lines.append(f"{name}  [{m['origin']}]  {meta.get('use', '')}")
        for slot, desc in (meta.get("slots") or {}).items():
            lines.append(f"    {slot}: {desc}")
        if full and meta.get("sample") is not None:
            lines.append("    sample: " + json.dumps(meta["sample"], ensure_ascii=False))
    parts = load_parts(brand_dir)
    if parts:                                               # blocks of the brand's own that any slide can carry
        lines.append("\nparts of the brand: on a slide \"parts\": [{\"part\": <name>, <slots>}] (at the end of the slide, or where a free body holds <vs-part n=\"1\"></vs-part>)")
        for name, p in parts.items():
            if p["meta"].get("in_masters"):
                lines.append(f"{name}  [part, in masters as {{{{>part {name}}}}}]  {p['meta'].get('use', '')}"); continue
            lines.append(f"{name}  [part]  {p['meta'].get('use', '')}")
            for slot, desc in (p["meta"].get("slots") or {}).items():
                lines.append(f"    {slot}: {desc}")
    return "\n".join(lines)


# ---------------------------------------------------------------- template engine

def _lookup(stack, name):
    if name == ".":
        return stack[-1].get(".", stack[-1]) if isinstance(stack[-1], dict) else stack[-1]
    parts = name.split(".")
    for ctx in reversed(stack):
        if isinstance(ctx, dict) and parts[0] in ctx:
            v = ctx
            for p in parts:
                if isinstance(v, dict):
                    v = v.get(p)
                elif isinstance(v, list) and p.isdigit():
                    v = v[int(p)] if int(p) < len(v) else None
                else:
                    v = None
                if v is None:
                    break
            return v
    return None

def _parse(body):
    """Template text -> nested list of ('text', s) | ('var', name) | ('helper', args) | ('sec'|'inv', name, children)."""
    root, stack, pos = [], [], 0
    cur = root
    masked = _TAG.sub(lambda m: "\x00" * len(m.group(0)), body)      # the markup without the tags, same positions
    for m in _TAG.finditer(body):
        kind, name = m.group(1), m.group(2)
        if kind == "" and re.fullmatch(r"IMG_[A-Z0-9_]+", name):
            continue                                   # image placeholder, stays for the build step
        if m.start() > pos:
            cur.append(("text", body[pos:m.start()]))
        pos = m.end()
        if kind in "#^" and kind:
            node = ("sec" if kind == "#" else "inv", name, [])
            cur.append(node); stack.append(cur); cur = node[2]
        elif kind == "/":
            if not stack:
                raise ValueError(f"closing tag {{{{/{name}}}}} without an opening one")
            cur = stack.pop()
        elif kind == ">":
            cur.append(("helper", name.split()))
        else:
            cur.append(("var", name, _place(masked, m.start(), m.end())))
    if stack:
        raise ValueError("a {{#section}} is not closed")
    cur.append(("text", body[pos:]))
    return root

def _place(masked, start, end):
    """Where a value lands in the markup: "attr" (inside a tag, a style or a script: not text), "sole" (the only
    content of its element, so the element itself can carry the slot's name), "text" (text among other content)."""
    before = masked[:start]
    if before.rfind("<") > before.rfind(">"):
        return "attr"
    low = before.lower()
    for tag in ("style", "script", "svg", "title"):
        if low.rfind("<" + tag) > low.rfind("</" + tag):
            return "attr"
    m = re.search(r"<([a-zA-Z][\w-]*)[^<>]*>\s*$", before)
    if m and re.match(r"\s*</" + re.escape(m.group(1)) + r"\s*>", masked[end:]):
        return "sole"
    return "text"

# values of the render context that are not slots of the deck file
_NOT_SLOT = {"attrs", "notes", "motion", "lang", "brand", "b", "layout", "master", "only", "step", "read", "name", "chapter", "focus"}
_BLOCK = re.compile(r"<(p|div|ul|ol|li|table|section|h\d|img|svg|video|iframe|script|style)\b", re.I)
_NOT_TEXT = re.compile(r"^(https?:|data:|brand:|images/|assets/|@\w+$|\{\{IMG_)|\.(jpe?g|png|svg|webp|gif|mp4|webm|mov|pdf)$", re.I)

def _where(stack, paths, name):
    """The path of a value in the slide of the deck file ("items.2.text", list items counted from 1), or None."""
    if name == ".":
        return paths[-1] or None
    first = name.split(".")[0]
    if first.startswith("_"):                               # worked out by the build (prepare), not written in the deck
        return None
    for k in range(len(stack) - 1, -1, -1):
        if isinstance(stack[k], dict) and first in stack[k]:
            if paths[k] is None or first.startswith("@") or (paths[k] == "" and (first in _NOT_SLOT or first.startswith("is_"))):
                return None
            return (paths[k] + "." if paths[k] else "") + name
    return None

def _editable(out, value, path, place):
    """Edit build: mark the place where a slot's text stands with data-s="<path>", on its element when the text is
    the element's only content, on a span around it otherwise."""
    if place == "sole" and out and out[-1].rstrip().endswith(">") and not out[-1].rstrip().endswith("/>"):
        k = out[-1].rindex(">")
        out[-1] = out[-1][:k] + f' data-s="{path}"' + out[-1][k:]
        out.append(value)
    else:
        out.append(f'<span class="vs-e" data-s="{path}">{value}</span>')

def _truthy(v):
    return not (v is None or v is False or v == "" or v == [] or v == {})

def _render(nodes, stack, env, paths=None):
    out = []
    paths = paths or [""] * len(stack)                      # for every context of the stack: where it sits in the slide of the deck file
    edit = env.get("edit")
    for node in nodes:
        kind = node[0]
        if kind == "text":
            out.append(node[1])
        elif kind == "var":
            v = _lookup(stack, node[1])
            if edit and isinstance(v, str) and v.strip() and node[2] != "attr" and not _BLOCK.search(v) and not _NOT_TEXT.search(v.strip()):
                path = _where(stack, paths, node[1])
                if path:
                    _editable(out, v, path, node[2]); continue
            out.append("" if v is None or v is False else (str(v) if not isinstance(v, (dict, list)) else ""))
        elif kind == "helper":
            name, args = node[1][0], node[1][1:]
            if name not in HELPERS:
                raise ValueError(f"unknown helper {{{{>{name}}}}}")
            vals = list(args) if name == "part" else [(_lookup(stack, a) if _lookup(stack, a) is not None else a) for a in args]      # a part is named by itself, never by a slot
            out.append(HELPERS[name](env, *vals))
        else:
            v = _lookup(stack, node[1])
            if kind == "inv":
                if not _truthy(v):
                    out.append(_render(node[2], stack, env, paths))
            elif isinstance(v, list):
                base = _where(stack, paths, node[1]) if edit else None
                for i, item in enumerate(v):
                    ctx = dict(item) if isinstance(item, dict) else {".": item}
                    ctx.update({"@i": i + 1, "@ii": f"{i + 1:02d}", "@first": i == 0, "@last": i == len(v) - 1})
                    out.append(_render(node[2], stack + [ctx], env, paths + [f"{base}.{i + 1}" if base else None]))
            elif _truthy(v):
                if isinstance(v, dict):
                    out.append(_render(node[2], stack + [v], env, paths + [_where(stack, paths, node[1]) if edit else None]))
                else:
                    out.append(_render(node[2], stack, env, paths))
    return "".join(out)

def render_template(body, slots, env=None):
    return _render(_parse(body), [slots], env or {})


# ---------------------------------------------------------------- helpers and built-in masters

def _rows(v, keys):
    """Accept list items as dicts or as plain lists, return tuples in the order of keys."""
    out = []
    for item in v or []:
        out.append(tuple(item.get(k) for k in keys) if isinstance(item, dict) else tuple(item))
    return out

def _h_chapter_number(env, n):
    from motion import chapter_number
    return chapter_number(int(n))

def _h_bars(env, rows):
    from motion import bars
    return bars(_rows(rows, ("label", "value", "share")), env.get("lang", "en"))

def _h_columns(env, rows):
    from motion import columns
    s = env.get("slide") or {}
    return columns(_rows(rows, ("label", "value")), s.get("mark"), env.get("lang", "en"), step=s.get("step") is True)

def _h_bgvideo(env):
    import media
    return media.background_video(env)

def _h_chevron_fill(env, stages):
    from motion import chevron_fill
    return chevron_fill(_rows(stages, ("tag", "title", "text")))

def _h_line_chart(env, axis, series, ymax):
    from motion import line_chart
    ser = [(s.get("values"), s.get("color", "var(--accent)"), bool(s.get("labels", True))) if isinstance(s, dict) else tuple(s) for s in series]
    return line_chart(axis, ser, float(ymax))

def _h_verdict(env, columns):
    import blocks
    colours = {"accent": blocks.ACCENT, "deep": blocks.DEEP, "muted": blocks.MUTED}
    return blocks.verdict_columns([(c["title"], colours.get(c.get("color", "accent"), c.get("color")), c.get("bullets", [])) for c in columns])

def _h_lower_third(env, name, role):
    from motion import lower_third
    return lower_third(name, role)

def _h_el(env, rel):
    """Inline an SVG from the brand's elements/ folder, e.g. {{>el arrows/arrow.svg}}."""
    p = os.path.join(env.get("brand_dir") or "", "elements", str(rel))
    if not os.path.exists(p):
        env.setdefault("warnings", []).append(f"element not found: elements/{rel}")
        return ""
    svg = open(p, encoding="utf-8").read()
    svg = re.sub(r"<\?xml[^>]*\?>|<!DOCTYPE[^>]*>", "", svg).strip()
    return re.sub(r"<svg\b", '<svg class="el" aria-hidden="true"', svg, 1)

def element_names(brand_dir, kind="icons"):
    """The files of one kind in the brand's elements/ folder by the names a deck can use: the file name without
    .svg, and the part after the running number (icon_03_energy.svg is "icon_03_energy" and "energy")."""
    out, folder = {}, os.path.join(brand_dir or "", "elements", kind)
    for f in sorted(os.listdir(folder)) if os.path.isdir(folder) else []:
        if not f.lower().endswith(".svg"): continue
        stem = f[:-4]; out.setdefault(stem.lower(), f)
        short = re.sub(r"^(icon|arrow|shape)_\d+_?", "", stem)
        if short: out.setdefault(short.lower(), f)
    return out

def _h_icon(env, name):
    name = str(name).strip()
    f = element_names(env.get("brand_dir"), "icons").get(re.sub(r"\.svg$", "", name, flags=re.I).lower())
    if not f:
        env.setdefault("warnings", []).append(f"icon not found in the brand's library: {name} (vs.py elements <brand> lists them)")
        return ""
    return _h_el(env, "icons/" + f)

def _h_video(env):
    import media
    return media.video_box(env)

def _h_embed(env):
    import media
    return media.embed_box(env)

def _h_scene(env):
    import media
    return media.scene_box(env)

def load_parts(brand_dir):
    """The brand's parts (library/<brand>/parts/<name>.html, see forms.py): {name: {"meta", "body", "path"}}."""
    out, folder = {}, os.path.join(brand_dir or "", "parts")
    if brand_dir and os.path.isdir(folder):
        for fn in sorted(os.listdir(folder)):
            if fn.endswith(".html"):
                p = os.path.join(folder, fn); meta, body = parse_master(open(p, encoding="utf-8").read(), p)
                out[meta.get("name") or fn[:-5]] = {"meta": meta, "body": body, "path": p}
    return out

def _part(env, name):
    parts = env.get("_parts")
    if parts is None: parts = env["_parts"] = load_parts(env.get("brand_dir"))
    if name not in parts:
        env.setdefault("warnings", []).append(f"unknown part '{name}'. The brand has: {', '.join(sorted(parts)) or 'none'}")
        return None
    return parts[name]

def _h_part(env, name):
    """{{>part takeaway}} inside a master: the brand's part, filled from the slots of the slide."""
    p = _part(env, str(name))
    return _render(_parse(p["body"]), [env.get("slide") or {}], env) if p else ""

def _place_parts(html, s, env):
    """The parts a slide names ("parts": [{"part": "takeaway", "t1": "..."}]) go where its body holds
    <vs-part n="1"></vs-part>, the others at the end of the slide, before its notes."""
    ps = s.get("parts")
    many = isinstance(ps, list); ps = ps if many else [ps] if isinstance(ps, dict) else []
    rest = []
    for i, e in enumerate(ps, 1):
        if not isinstance(e, dict) or not e.get("part"): continue
        p = _part(env, str(e["part"]))
        if not p: continue
        base = {"b": env.get("brand_info") or {}, "lang": env.get("lang"), "brand": env.get("brand_name", "")}
        out = _render(_parse(p["body"]), [base, e], env, [None, f"parts.{i}" if many else "parts"])
        mark = re.compile(rf'<vs-part\s+n="{i}"\s*>\s*</vs-part>|<vs-part\s+n="{i}"\s*/>')
        if mark.search(html): html = mark.sub(lambda _m: out, html, count=1)
        else: rest.append(out)
    html = re.sub(r'<vs-part\b[^>]*>\s*(</vs-part>)?', "", html)
    if rest:
        k = html.find('<aside class="notes">')
        if k < 0: k = html.rfind("</section>")
        if k < 0: k = len(html)
        html = html[:k] + "\n".join(rest) + "\n" + html[k:]
    return html

def _num(v, lang):
    """A number as it is written in the language: 12,400 in English, 12.400 in German; decimals likewise."""
    s = f"{v:,.0f}" if float(v).is_integer() else f"{v:,.1f}"
    return s.translate(str.maketrans(",.", ".,")) if (lang or "en")[:2] in ("de", "fr", "es", "it", "nl") else s

def _prep_waterfall(slots, env):
    """Bars of a bridge: totals from the ground, steps from where the one before ended (_b bottom, _h height in
    percent of the chart, _kind total/up/down, _v the amount as text)."""
    items = [i for i in slots.get("items") or [] if isinstance(i, dict)]
    run, spans = 0.0, []
    for it in items:
        try: a = float(str(it.get("amount", 0)).replace(",", "."))
        except ValueError: a = 0.0
        if it.get("total"): spans.append((0.0, a)); run = a
        else: spans.append((run, run + a)); run += a
    lo = min([0.0] + [min(s) for s in spans]); hi = max([0.0] + [max(s) for s in spans]); span = (hi - lo) or 1.0
    unit = slots.get("unit") or ""; lang = env.get("lang")
    for it, (a, b) in zip(items, spans):
        it["_b"] = round((min(a, b) - lo) / span * 82, 2)          # the top 18 % stay free for the figures above the bars
        it["_h"] = round(abs(b - a) / span * 82, 2)
        kind = "total" if it.get("total") else ("down" if b < a else "up")
        it["_kind"] = kind + (" low" if kind == "down" and it["_b"] < 12 else "")
        amt = b - a if not it.get("total") else b
        it["_v"] = (("+" if amt > 0 and not it.get("total") else "−" if amt < 0 else "") + _num(abs(amt), lang) + (" " + unit if unit else ""))

PALETTE = ["var(--accent)", "var(--ink)", "var(--muted)", "var(--line)", "color-mix(in srgb,var(--accent) 40%,var(--paper))"]

def _prep_share(slots, env):
    """Parts of a ring: _a and _z where each part starts and ends in percent, _c its colour."""
    items = [i for i in slots.get("items") or [] if isinstance(i, dict)]
    vals = []
    for it in items:
        try: vals.append(max(0.0, float(str(it.get("value", 0)).replace(",", "."))))
        except ValueError: vals.append(0.0)
    total = sum(vals) or 1.0; k = 100 / total if total > 100 else 1.0; at = 0.0
    for i, (it, v) in enumerate(zip(items, vals)):
        it["_a"] = round(at, 2); at += v * k; it["_z"] = round(at, 2); it["_c"] = PALETTE[i % len(PALETTE)]
    if items:
        slots["_center"] = f"{items[0].get('value')}%"; slots["_center_label"] = items[0].get("label", "")

PREPARE = {"waterfall": _prep_waterfall, "share": _prep_share}

HELPERS = {"chapter_number": _h_chapter_number, "bars": _h_bars, "columns": _h_columns, "bgvideo": _h_bgvideo, "chevron_fill": _h_chevron_fill, "line_chart": _h_line_chart,
           "verdict": _h_verdict, "lower_third": _h_lower_third, "el": _h_el, "icon": _h_icon,
           "video": _h_video, "embed": _h_embed, "scene": _h_scene, "part": _h_part}

def _order(v):
    """ "order" of a slide as the engine reads it: [3, [1, 2]] or "3, 1+2" gives "3,1+2"; a 0 in an entry puts its
    steps on the slide from the start. Anything else gives ""."""
    if isinstance(v, str): v = [[p for p in e.split("+")] for e in v.split(",")]
    if not isinstance(v, list): return ""
    out = []
    for e in v:
        m = e if isinstance(e, list) else [e]
        try: m = [int(x) for x in m]
        except (TypeError, ValueError): continue
        m = [x for x in m if x >= 0]
        if m: out.append("+".join(str(x) for x in m))
    return ",".join(out)

def _attrs(s, lang):
    a = [f'lang="{lang}"']
    for key, attr in (("name", "data-title"), ("chapter", "data-chapter"), ("source", "data-source"), ("about", "data-about")):
        if s.get(key):
            a.append(f'{attr}="{str(s[key]).replace(chr(34), "&quot;")}"')
    if isinstance(s.get("step"), bool):                     # the deck says whether this slide builds up on click, whatever its master does
        a.append(f'data-step="{1 if s["step"] else 0}"')
    order = _order(s.get("order"))
    if order:                                               # the click steps in an order of the deck's own (see master.html, reorder)
        a.append(f'data-order="{order}"')
    if s.get("fit") is False:                               # this slide keeps its sizes: the engine does not enlarge its body to fill the slide
        a.append('data-fit="0"')
    if s.get("move") in ("calm", "expressive", "off"):       # how much moves on this one slide
        a.append(f'data-move="{s["move"]}"')
    focus = str(s.get("focus") or "").strip().lower()       # which part of the photo stays in view: "right", "left top", "30% 20%"
    if focus and re.fullmatch(r"(left|right|center|top|bottom|\d{1,3}%)( (left|right|center|top|bottom|\d{1,3}%))?", focus):
        a.append(f'style="--focus:{focus}"')
    return " ".join(a)

def _m_timer(s, env):
    from timer import timer_slide
    env["assets"].add("timer")
    return timer_slide(env["lang"], s.get("name", "Timer"), s.get("kicker", ""), int(s.get("minutes", 10)), s.get("heading", "{duration}"),
                       _rows(s.get("steps"), ("n", "title", "text")), _rows(s.get("facts"), ("label", "value")))

def _quiz_common(s, env):
    env["assets"].add("quiz")
    return dict(explanation=s.get("explanation", ""), kicker=s.get("kicker"), note=s.get("notes", ""), source=s.get("source", ""),
                revealed=bool(s.get("revealed") or env.get("handout")), advance=bool(s.get("advance")))

def _m_quiz_choice(s, env):
    from quiz import quiz_choice
    return quiz_choice(env["lang"], s.get("name", "Quiz"), s["question"], s["answers"], s.get("correct"), **_quiz_common(s, env))

def _m_quiz_true_false(s, env):
    from quiz import quiz_true_false
    return quiz_true_false(env["lang"], s.get("name", "Quiz"), s["statement"], bool(s["is_true"]), **_quiz_common(s, env))

def _m_quiz_estimate(s, env):
    from quiz import quiz_estimate
    return quiz_estimate(env["lang"], s.get("name", "Quiz"), s["question"], s["number"], s.get("unit", ""),
                         decimals=int(s.get("decimals", 0)), **_quiz_common(s, env))

def _m_logo_intro(s, env):
    from motion import logo_intro
    env["assets"].add("motion"); env["need_logo_inv"] = True
    return logo_intro(env["lang"], s.get("name", "Logo intro"), s.get("kicker", ""))

def _m_raw(s, env):
    html = s.get("html", "")
    if "<section" not in html:
        html = f'<section class="slide {s.get("class", "")}" {_attrs(s, env["lang"])}>\n{html}\n{env["notes_html"]}\n</section>'
    return html

FUNCTION_MASTERS = {
    "timer": {"order": 700, "use": "Countdown for an exercise or a break, stands after the slide that explains the task. Left out of handouts and reading versions.",
              "handout": False, "reading": False,
              "slots": {"kicker": "small label", "minutes": "1 to 60", "heading": "use {duration} for the running time, e.g. \"{duration} for the <em>interviews</em>\"",
                        "steps": "list of {n, title, text}; empty for a break (clock alone)", "facts": "list of {label, value}, value may be {duration}"},
              "sample": {"kicker": "Exercise", "minutes": 20, "heading": "{duration} for the <em>task</em>",
                         "steps": [{"n": "1", "title": "Collect", "text": "Everyone writes down three observations."}, {"n": "2", "title": "Sort", "text": "Group them on the wall."}],
                         "facts": [{"label": "Duration", "value": "{duration}"}, {"label": "Format", "value": "In pairs"}]}},
    "quiz_choice": {"order": 710, "use": "Question to the audience with two to four answers, reveal with confetti.",
                    "slots": {"question": "full sentence with question mark", "answers": "list of 2 to 4 short texts", "correct": "index of the right one, 0 = A; null for a poll",
                              "explanation": "one sentence shown after the reveal", "source": "source of the fact", "advance": "true: the next forward click reveals"},
                    "sample": {"question": "How much of a slide should the accent colour cover at most?", "answers": ["Half", "One third", "One fifth", "All of it"], "correct": 2,
                               "explanation": "The accent colour is an accent. The quiet base carries the slide."}},
    "quiz_true_false": {"order": 711, "use": "One statement, the audience says true or false.",
                        "slots": {"statement": "the statement", "is_true": "true or false", "explanation": "one sentence"},
                        "sample": {"statement": "Slides carry their own logos.", "is_true": False, "explanation": "The framework places the logos."}},
    "quiz_estimate": {"order": 712, "use": "The audience guesses a number, it counts up on reveal. Needs a real number with a source.",
                      "slots": {"question": "the question", "number": "the correct number", "unit": "short unit", "decimals": "0 by default", "explanation": "one sentence"},
                      "sample": {"question": "How many pixels wide is a slide?", "number": 1920, "unit": "pixels", "explanation": "Every slide is 1920 by 1080 pixels."}},
    "logo_intro": {"order": 800, "use": "Logo sting for the start or end of a video: wipe, then the logo.", "slots": {"kicker": "optional small line"}, "sample": {}},
    "raw": {"order": 900, "use": "Escape hatch for one slide no master covers: your own HTML. If the look will be needed again, make it a master instead.",
            "slots": {"html": "inner HTML of the slide, or a complete <section>", "class": "extra classes on the section (dark, accent, center)"},
            "sample": {"html": "<h2>A slide written by hand</h2><p class=\"lead\">Only for one-offs.</p>"}},
}
_FUNCTIONS = {"timer": _m_timer, "quiz_choice": _m_quiz_choice, "quiz_true_false": _m_quiz_true_false, "quiz_estimate": _m_quiz_estimate,
              "logo_intro": _m_logo_intro, "raw": _m_raw}


# ---------------------------------------------------------------- deck

def _resolve_lang(v, lang, langs):
    """{"en": "...", "de": "..."} -> the text for lang. Works through lists and dicts."""
    if isinstance(v, dict):
        if v and set(v) <= set(langs) | {"*"}:
            return v.get(lang, v.get("*", next(iter(v.values()))))
        return {k: _resolve_lang(x, lang, langs) for k, x in v.items()}
    if isinstance(v, list):
        return [_resolve_lang(x, lang, langs) for x in v]
    return v

def _image_name(path, full):
    return ("FULL_" if full else "I_") + hashlib.md5(path.encode()).hexdigest()[:10].upper()

def _resolve_images(v, env, full=False):
    """Replace image paths in slot values by {{IMG_NAME}} placeholders and remember the files."""
    if isinstance(v, dict):
        return {k: _resolve_images(x, env, full) for k, x in v.items()}
    if isinstance(v, list):
        return [_resolve_images(x, env, full) for x in v]
    if not isinstance(v, str):
        return v
    if v.startswith("@"):                                  # stand-ins used by the samples: @photo, @tall, @wide, @portrait, @logo, @logo_inv
        path = (env.get("standins") or {}).get(v[1:])
        if path is None:
            return v
    elif _IMAGE.match(v.strip()) and not re.match(r"(https?:|data:)", v):
        rel = v.strip()
        path = os.path.join(env.get("brand_dir") or "", rel[6:]) if rel.startswith("brand:") else os.path.join(env.get("deck_dir") or "", rel)
        if not os.path.exists(path):
            env.setdefault("warnings", []).append(f"image not found: {rel}")
            return ""
    else:
        return v
    if not path:
        return ""
    name = _image_name(path, full)
    env["images"][name] = path
    return "{{IMG_" + name + "}}"

def _plain(v):
    return re.sub(r"\s+", " ", re.sub(r"<[^>]+>", "", str(v or ""))).strip()

def _prose(v):
    """Reader text or notes as paragraphs: a list gives one paragraph per item, a blank line starts a new one."""
    if isinstance(v, list):
        v = "\n\n".join(str(x) for x in v if x)
    v = str(v or "").strip()
    if not v:
        return ""
    if re.search(r"<(p|ul|ol|div|h\d)\b", v):
        return v
    return "".join(f"<p>{p.strip()}</p>" for p in re.split(r"\n\s*\n", v) if p.strip())

def _finish(html, n, env):
    """Mark the section with the slide's number in the deck file and the version it belongs to, and add the
    reader text. Both versions of a deck are in one file; the engine shows the slides of the version it runs."""
    only = env.get("only")
    html = re.sub(r"<section\b", f'<section data-n="{n}"' + (f' data-only="{only}"' if only else ""), html, 1)
    read = env.get("read_html")
    if read and "</section>" in html:
        k = html.rindex("</section>")
        html = html[:k] + read + "\n" + html[k:]
    return html

_CONTENTS = {"en": "Contents", "de": "Inhalt", "fr": "Sommaire", "es": "Contenido", "it": "Indice", "nl": "Inhoud"}

def _contents(lang, chapters, kicker=""):
    """The contents page of a reading version: the chapters with the page each one starts on."""
    title = _CONTENTS.get(lang[:2].lower(), _CONTENTS["en"])
    rows = "".join(f'<li><a href="#/{page}"><i>{i:02d}</i><span>{name}</span><b>{page}</b></a></li>' for i, (name, page) in enumerate(chapters, 1))
    cls = "rtoc" + (" many" if len(chapters) > 7 else "") + (" cols" if len(chapters) > 11 else "")
    return (f'<section class="slide rcontents" data-only="reading" lang="{lang}" data-title="{title}">\n'
            + (f'  <div class="kicker">{kicker}</div>\n' if kicker else "") + f'  <h2>{title}</h2>\n  <ol class="{cls}">{rows}</ol>\n</section>')

def in_mode(slide, mode, masters=None):
    """Does this slide belong to the version that is built? "only" names the one version a slide is for."""
    if slide.get("only") in ("live", "reading") and slide["only"] != mode:
        return False
    return not (mode == "reading" and ((masters or {}).get(slide.get("master")) or {}).get("meta", {}).get("reading") is False)

def titles(deck):
    """The titles of a deck in a row, per language: [(number in the deck file, master, only, title or None)].
    Read like this before any slide is designed, the titles alone must give the argument."""
    langs = deck.get("langs") or [deck.get("lang") or "en"]
    out = {}
    for lang in langs:
        rows = []
        for i, slide in enumerate(deck.get("slides", []), 1):
            if slide.get("lang") and slide["lang"] != lang:
                continue
            s = _resolve_lang(slide, lang, langs)
            t = next((_plain(s.get(k)) for k in ("title", "question", "statement") if _plain(s.get(k))), None)
            rows.append((i, slide.get("master", "?"), slide.get("only") if slide.get("only") in ("live", "reading") else None, t))
        out[lang] = rows
    return out

def render_slide(slide, lang, masters, env):
    name = slide.get("master")
    if name not in masters:
        raise ValueError(f"unknown master '{name}'. Available: {', '.join(sorted(masters))}")
    m = masters[name]
    s = _resolve_images(_resolve_lang(slide, lang, env["langs"]), env, full=bool(m["meta"].get("full_images")))
    env["lang"] = lang
    read, env["read_html"] = _prose(s.get("read")), ""
    origin = "read" if read else ("notes" if _prose(s.get("notes")) else "none")
    if env.get("mode") == "reading":                       # what the build reports for a deck whose main version is the reading one
        env.setdefault("read_origin", {}).setdefault(origin, set()).add(env.get("slide_no", 0))
    text = read or _prose(s.get("notes"))                  # reading version: the text for readers goes onto the page, the notes when there is none
    if text and env.get("only") != "live":
        env["read_html"] = f'<aside class="read"{"" if origin == "read" else " data-from=" + chr(34) + "notes" + chr(34)}>{text}</aside>'
    if read and not s.get("notes"):                        # live version: the reader text serves the speaker where there are no notes
        s["notes"] = read
    notes = s.get("notes")
    env["notes_html"] = f'<aside class="notes">{notes}</aside>' if notes else ""
    if name in _FUNCTIONS:
        return _FUNCTIONS[name](s, env)
    slots = dict(_resolve_lang(fit_langs(m["meta"].get("defaults") or {}, env["langs"]), lang, env["langs"]))
    slots.update(s)
    if m["meta"].get("is_chapter") and not s.get("chapter"):
        s["chapter"] = re.sub(r"<[^>]+>", "", str(s.get("title", ""))).strip()
    if m["meta"].get("title_as_name") and not s.get("name") and s.get("title"):      # slides that do not print their title still appear in the outline
        s["name"] = re.sub(r"<[^>]+>", "", str(s["title"])).strip()
    slots.update(s)
    if slots.get("layout"):                                # {{#is_boxed}} ... {{/is_boxed}} for masters with a layout choice
        slots["is_" + re.sub(r"\W+", "_", str(slots["layout"]))] = True
    if m["meta"].get("prepare") in PREPARE:                # figures the template cannot work out: bar heights, parts of a ring
        PREPARE[m["meta"]["prepare"]](slots, env)
    env["slide"] = slots                                   # for helpers that work on the whole slide (video, embed, scene)
    slots.update({"b": env.get("brand_info") or {}, "attrs": _attrs(s, lang), "notes": env["notes_html"], "motion": env.get("motion", True), "lang": lang,
                  "brand": env.get("brand_name", "")})
    html = render_template(m["body"], slots, env)
    if s.get("parts") or "<vs-part" in html:
        html = _place_parts(html, s, env)
    if "mslide" in html or "mchev" in html or "mcurve" in html:
        env["assets"].add("motion")
    return html

CREDIT = {"de": ("Erstellt von {a}, mit ein bisschen Hilfe von VibeUpSlides von vibeup.berlin", "Erstellt mit ein bisschen Hilfe von VibeUpSlides von vibeup.berlin"),
          "en": ("Made by {a}, with a little help from VibeUpSlides by vibeup.berlin", "Made with a little help from VibeUpSlides by vibeup.berlin"),
          "fr": ("Créé par {a}, avec un peu d'aide de VibeUpSlides par vibeup.berlin", "Créé avec un peu d'aide de VibeUpSlides par vibeup.berlin"),
          "es": ("Creado por {a}, con un poco de ayuda de VibeUpSlides de vibeup.berlin", "Creado con un poco de ayuda de VibeUpSlides de vibeup.berlin"),
          "it": ("Creato da {a}, con un piccolo aiuto di VibeUpSlides di vibeup.berlin", "Creato con un piccolo aiuto di VibeUpSlides di vibeup.berlin"),
          "nl": ("Gemaakt door {a}, met een beetje hulp van VibeUpSlides van vibeup.berlin", "Gemaakt met een beetje hulp van VibeUpSlides van vibeup.berlin")}

def credit_line(author, lang):
    """The line on a deck's last slide: the person who made it, with a little help from VibeUpSlides."""
    import html as _h
    with_a, without = CREDIT.get((lang or "en")[:2], CREDIT["en"])
    a = _plain(str(author or "")).strip()
    return with_a.format(a=_h.escape(a)) if a else without

def render_deck(deck, masters, env):
    """deck: dict with langs and slides. Returns the slide file content. env collects images, assets, warnings."""
    from timer import TIMER_ASSETS
    from quiz import QUIZ_ASSETS
    import motion
    mode = env["mode"] = env.get("mode") or deck.get("mode") or "live"       # "live" or "reading", see reading.css
    chapters, pages, rpages, cover = {}, {}, {}, 0         # reading version: chapter starts and page counts per language, for the contents page
    langs = deck.get("langs") or [deck.get("lang") or "en"]
    level = motion.intensity(deck.get("motion", True))      # off, calm, standard, expressive
    env.update(langs=langs, motion=level != "off", motion_level=level, handout=bool(deck.get("handout")), sample=bool(deck.get("sample")))
    env.setdefault("images", {}); env.setdefault("assets", set()); env.setdefault("warnings", [])
    out = []; last = {}
    for i, slide in enumerate(deck.get("slides", []), 1):
        if deck.get("fit") is False and isinstance(slide, dict) and "fit" not in slide: slide = dict(slide, fit=False)
        if env["handout"] and (slide.get("handout") is False or masters.get(slide.get("master"), {}).get("meta", {}).get("handout") is False):
            continue
        meta = (masters.get(slide.get("master")) or {}).get("meta", {})
        only = slide.get("only") if slide.get("only") in ("live", "reading") else ("live" if meta.get("reading") is False else None)
        env["slide_no"], env["only"] = i, only
        for lang in ([slide["lang"]] if slide.get("lang") else langs):
            try:
                out.append(_finish(render_slide(slide, lang, masters, env), i, env)); last[lang] = len(out) - 1
                if env.get("edit") and slide.get("shared"):  # the editing says that a change to this slide stays in this deck
                    out[-1] = re.sub(r"<section\b", '<section data-shared="' + re.sub(r"[^\w-]", "", str(slide["shared"])) + '"' + (' data-forall="1"' if slide.get("for_all") else ""), out[-1], 1)
            except Exception as e:
                raise ValueError(f"slide {i} ({slide.get('master')}): {e}")
            pages[lang] = pages.get(lang, 0) + 1
            if only != "live":
                rpages[lang] = rpages.get(lang, 0) + 1
            name = _plain(_resolve_lang(slide.get("chapter") or (slide.get("title") if meta.get("is_chapter") else ""), lang, langs))
            if name and name not in [c[0] for c in chapters.setdefault(lang, [])]:
                chapters[lang].append((name, rpages.get(lang, 0) + (1 if only == "live" else 0)))
        if len(out) == sum(pages.values()) == len(pages) and str(slide.get("master", "")).startswith("cover"):
            cover = len(out)                                # the contents page follows the cover
    env["only"] = None
    if deck.get("credit") is not False and not env["sample"]:      # who made the deck, on its last slide
        for lang, k in last.items():
            j = out[k].rfind("</section>")
            if j >= 0: out[k] = out[k][:j] + f'<div class="vs-credit">{credit_line(deck.get("author"), lang)}</div>\n' + out[k][j:]
    if deck.get("contents", True) and not env["handout"] and any(len(c) > 1 for c in chapters.values()):
        first = 1 if cover else 0
        out[cover:cover] = [_contents(lang, [(n, p + 1 if p > first else p) for n, p in chapters[lang]], _plain(_resolve_lang(deck.get("title"), lang, langs)))
                            for lang in langs if len(chapters.get(lang, [])) > 1]
    for key, block in (("timer", TIMER_ASSETS), ("quiz", QUIZ_ASSETS)):
        if key in env["assets"]:
            out.append(block)
    if env.get("edit"):                                     # the editing mode: its styles and script travel with the edit build only
        import edit
        out.append(edit.assets())
    out.append(motion.assets(env.get("brand"), level))      # always: the brand's motion set also drives the engine's own entrances
    return "\n\n".join(out)

_LANG_KEY = re.compile(r"^(\*|[a-z]{2,3}(-[A-Za-z]{2,4})?)$")

def fit_langs(v, langs):
    """Sample texts may be written per language ({"de": "...", "en": "..."}). For a deck in other languages the
    nearest text is taken: the first language that is there, English, or whatever comes first."""
    if isinstance(v, dict):
        if v and all(isinstance(k, str) and _LANG_KEY.match(k) for k in v) and all(not isinstance(x, (dict, list)) for x in v.values()) and (len(v) > 1 or set(v) & set(langs)):
            if set(v) <= set(langs) | {"*"}:
                return v
            keep = {k: x for k, x in v.items() if k in langs or k == "*"}
            keep.setdefault("*", v.get("*", v.get("en", next(iter(v.values())))))
            return keep
        return {k: fit_langs(x, langs) for k, x in v.items()}
    if isinstance(v, list):
        return [fit_langs(x, langs) for x in v]
    return v

def sample_deck(masters, lang="en"):
    """A deck that shows every master once with its sample content: the brand's master slides.
    lang: one language or a list; with several the preview can be switched like any deck."""
    langs = [lang] if isinstance(lang, str) else list(lang)
    slides = []
    for name, m in sorted(masters.items(), key=lambda kv: (kv[1]["meta"].get("order", 500), kv[0])):
        meta = m["meta"]
        if meta.get("sample") is None or meta.get("hidden"):
            continue
        s = dict(fit_langs(meta["sample"], langs)); s["master"] = name
        s.setdefault("name", meta.get("title") or name.replace("_", " ").capitalize())
        slides.append(s)
    return {"langs": langs, "slides": slides, "sample": True}
