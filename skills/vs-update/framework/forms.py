# -*- coding: utf-8 -*-
"""Forms a brand's decks come to share over time.

A slide written freely for one deck (master `free`, its own HTML body) is a one-off. When the same form turns
up again, in the same deck or in another deck of the brand, it has become part of how this company presents,
and it belongs into the brand's library as a master: then every deck uses the same one, and a change to it
reaches all of them (`vs.py refresh`).

The brand remembers what it has seen in `library/<brand>/forms.json`:

    {"seen": {"<mark of a form>": {"first": "2026-10-13", "uses": [{"deck": "kickoff", "slide": 4, "title": "..."}]}},
     "own":  {"<master>": {"made": "2026-10-13", "from": "kickoff, slide 4", "decks": ["kickoff", "pitch"]}}}

A form is told by its markup alone: the tags and classes of the body in their order, without the words.

Parts are the same one level down: a block that recurs inside slides of different forms (a band with the
conclusion under several slides, a row of logos, a contact box). Such a block becomes a part of the brand,
`library/<brand>/parts/<name>.html` (a header like a master's, then the markup with slots), and is used from
then on

    on any slide:          "parts": [{"part": "takeaway", "t1": "..."}]   placed where the free body has
                           <vs-part n="1"></vs-part>, otherwise at the end of the slide
    inside a master:       {{>part takeaway}}                              with the slots of the slide

forms.json remembers them under "parts" (where a block was seen) and "own_parts" (the brand's parts and the
decks that use them). Blocks that several of the brand's own masters hold word for word are found as well.
"""
import hashlib, json, os, re, time

_TAG = re.compile(r"<(/?)([a-zA-Z][\w-]*)\b([^>]*)>")
_INLINE = {"em", "strong", "b", "i", "u", "sup", "sub", "br", "mark", "small", "span", "a"}
_RAW = re.compile(r"<(style|script|svg)\b.*?</\1\s*>", re.S | re.I)

def mark(body, least=3):
    """The mark of a free slide's form: its block tags and their classes in order. None for a body with fewer
    than `least` elements (a single paragraph is not a form)."""
    b = _RAW.sub(lambda m: f"<{m.group(1).lower()}/>", str(body or ""))
    parts = []
    for m in _TAG.finditer(b):
        name = m.group(2).lower()
        if m.group(1) or name in _INLINE: continue
        cls = re.search(r'\bclass="([^"]*)"', m.group(3))
        parts.append(name + ("." + ".".join(sorted(cls.group(1).split())) if cls else ""))
    if len(parts) < least: return None
    return hashlib.sha1(" ".join(parts).encode()).hexdigest()[:12]

_VOID = {"area", "base", "br", "col", "embed", "hr", "img", "input", "link", "meta", "param", "source", "track", "wbr"}

def blocks(html):
    """The top-level elements of a piece of HTML as [(start, end)], in order (text between them is left out)."""
    raw = [(m.start(), m.end()) for m in _RAW.finditer(html)]
    out, depth, start = [], 0, None
    for m in _TAG.finditer(html):
        if any(a < m.start() < b for a, b in raw): continue
        name = m.group(2).lower(); close = bool(m.group(1)); selfclose = m.group(3).rstrip().endswith("/")
        if name in ("style", "script", "svg") and not close:
            end = next((b for a, b in raw if a == m.start()), m.end())
            if depth == 0: out.append((m.start(), end))
            continue
        if close:
            depth -= 1
            if depth == 0 and start is not None: out.append((start, m.end())); start = None
            depth = max(depth, 0)
        elif name in _VOID or selfclose:
            if depth == 0: out.append((m.start(), m.end()))
        else:
            if depth == 0: start = m.start()
            depth += 1
    return out

def part_mark(html):
    """The mark of a block: two elements at least, and a class that names it (a bare <div><p> is no part)."""
    return mark(html, 2) if re.match(r"<[a-zA-Z][\w-]*\b[^>]*\bclass=", html.strip()) else None

def parts_of(body):
    """[(block number from 1, mark, html)] of the blocks of a free body that are a form of their own."""
    out = []
    for i, (a, b) in enumerate(blocks(str(body or "")), 1):
        k = part_mark(body[a:b])
        if k: out.append((i, k, body[a:b]))
    return out

def master_blocks(body):
    """[(block number, html)] of the blocks inside the <section> of a master's template."""
    m = re.search(r"<section\b[^>]*>(.*)</section>", body, re.S)
    inner = m.group(1) if m else body
    return [(i, inner[a:b]) for i, (a, b) in enumerate(blocks(inner), 1)]

def _norm(html):
    return re.sub(r"\s+", " ", html).strip()

def shared_in_masters(brand_dir):
    """Blocks that two or more of the brand's own masters hold word for word: [(html, [(master, block), …])]."""
    def read(folder):
        for fn in sorted(os.listdir(folder)) if os.path.isdir(folder) else []:
            if not fn.endswith(".html"): continue
            try: yield fn[:-5], re.sub(r"^\s*<!--vs.*?-->", "", open(os.path.join(folder, fn), encoding="utf-8").read(), count=1, flags=re.S)
            except OSError: continue
    own = {_norm(h) for _, body in read(os.path.join(os.path.dirname(os.path.abspath(__file__)), "masters")) for _, h in master_blocks(body)}
    seen = {}
    for name, body in read(os.path.join(brand_dir, "masters")):          # blocks the framework's masters share are its own design, not the brand's
        for i, h in master_blocks(body):
            if "{{>part " in h or not part_mark(h) or _norm(h) in own: continue
            seen.setdefault(_norm(h), []).append((name, i))
    return [(h, w) for h, w in seen.items() if len({m for m, _ in w}) > 1]

def path(brand_dir):
    return os.path.join(brand_dir, "forms.json")

def load(brand_dir):
    try:
        d = json.load(open(path(brand_dir), encoding="utf-8"))
        if isinstance(d, dict):
            for k in ("seen", "own", "parts", "own_parts"): d.setdefault(k, {})
            d.setdefault("told", [])
            return d
    except (OSError, ValueError): pass
    return {"seen": {}, "own": {}, "parts": {}, "own_parts": {}, "told": []}

def _title(slide, langs):
    t = slide.get("title")
    if isinstance(t, dict): t = t.get(langs[0], next(iter(t.values()), ""))
    return re.sub(r"<[^>]+>", "", str(t or ""))[:60]

def _bodies(slide, langs):
    b = slide.get("body")
    return [x for x in (b.values() if isinstance(b, dict) and set(b) <= set(langs) | {"*"} else [b]) if isinstance(x, str)]

def note(brand_dir, deck_name, deck, defaults=()):
    """Remember the free forms and the brand's own masters this deck uses. Returns the lines to print: one for
    every free slide whose form the brand has seen before. defaults: names of the framework's masters."""
    mem = load(brand_dir); langs = deck.get("langs") or [deck.get("lang") or "en"]; lines = []; today = time.strftime("%Y-%m-%d")
    for rec in mem["seen"].values():                         # what this deck showed last time is told anew
        rec["uses"] = [u for u in rec.get("uses") or [] if u.get("deck") != deck_name]
    for rec in mem["own"].values():
        rec["decks"] = [x for x in rec.get("decks") or [] if x != deck_name]
    for rec in mem["parts"].values():
        rec["uses"] = [u for u in rec.get("uses") or [] if u.get("deck") != deck_name]
    for rec in mem["own_parts"].values():
        rec["decks"] = [x for x in rec.get("decks") or [] if x != deck_name]
    mine, blocks_here = {}, {}
    for i, s in enumerate(deck.get("slides") or [], 1):
        if not isinstance(s, dict): continue
        m = s.get("master")
        if m == "free":
            for body in _bodies(s, langs)[:1]:
                k = mark(body)
                if not k: continue
                rec = mem["seen"].setdefault(k, {"first": today, "uses": []})
                rec["uses"].append({"deck": deck_name, "slide": i, "title": _title(s, langs)}); mine.setdefault(k, []).append(i)
                for j, pk, _ in parts_of(body):                # the blocks of the slide, each a form of its own
                    prec = mem["parts"].setdefault(pk, {"first": today, "uses": []})
                    prec["uses"].append({"deck": deck_name, "slide": i, "block": j, "form": k}); blocks_here.setdefault(pk, []).append((i, j))
        elif m and m not in defaults and os.path.exists(os.path.join(brand_dir, "masters", f"{m}.html")):
            rec = mem["own"].setdefault(m, {"made": today, "decks": []})
            if deck_name not in rec["decks"]: rec["decks"].append(deck_name)
        ps = s.get("parts")
        for e in (ps if isinstance(ps, list) else [ps] if isinstance(ps, dict) else []):
            if isinstance(e, dict) and e.get("part"):
                rec = mem["own_parts"].setdefault(str(e["part"]), {"made": today, "decks": []})
                if deck_name not in rec["decks"]: rec["decks"].append(deck_name)
    for k, slides in mine.items():
        uses = mem["seen"][k]["uses"]; others = [u for u in uses if u["deck"] != deck_name]
        if len(uses) < 2: continue
        where = ", ".join(f"slide {u['slide']} of {u['deck']}" for u in others[:4]) or f"slides {', '.join(map(str, slides))} of this deck"
        lines.append(f"FORMS: slide {slides[0]} is written freely in a form the brand has used before ({where}; first seen {mem['seen'][k]['first']}). It has become part of how "
                     f"this company presents: make it a master of the brand, so that every deck uses the same one and a change reaches all of them: "
                     f"vs.py forms <brand> --promote {deck_name} --slide {slides[0]} --name <name>")
    for pk, here in blocks_here.items():                    # a block that recurs in slides of another form: a part
        uses = mem["parts"][pk]["uses"]
        if len(uses) < 2 or len({u["form"] for u in uses}) < 2: continue
        i, j = here[0]; others = [u for u in uses if (u["deck"], u["slide"]) != (deck_name, i)]
        where = ", ".join(f"slide {u['slide']} of {u['deck']}" for u in others[:4])
        lines.append(f"FORMS: block {j} of slide {i} recurs inside other slides ({where}; first seen {mem['parts'][pk]['first']}). It is a part of how this "
                     f"company presents: make it a part of the brand, so that every slide uses the same one and a change reaches all of them: "
                     f"vs.py forms <brand> --part <name> --from {deck_name} --slide {i} --block {j}")
    for h, where in shared_in_masters(brand_dir):           # the brand's own masters holding the same block word for word, told once
        key = hashlib.sha1(h.encode()).hexdigest()[:12]
        if key in mem["told"]: continue
        mem["told"].append(key); m0, b0 = where[0]
        lines.append(f"FORMS: the masters {', '.join(sorted({m for m, _ in where}))} hold the same block ({re.sub(r'<[^>]+>', ' ', h)[:60].strip() or h[:60]} …). Make it one "
                     f"part, so that a change reaches all of them: vs.py forms <brand> --part <name> --from-master {m0} --block {b0}")
    mem["seen"] = {k: v for k, v in mem["seen"].items() if v.get("uses")}
    mem["parts"] = {k: v for k, v in mem["parts"].items() if v.get("uses")}
    try: json.dump(mem, open(path(brand_dir), "w", encoding="utf-8"), indent=1, ensure_ascii=False)
    except OSError: pass
    return lines

def to_part(name, html):
    """A block as a part: its markup stays, every run of words becomes a slot (t1, t2, …). Returns (text of the
    part file, {slot: words})."""
    tmpl, sample, n = [], {}, 0
    for kind, text in _split(html):
        if kind == "t" and re.sub(r"<[^>]+>", "", text).strip():
            n += 1; lead = text[:len(text) - len(text.lstrip())]; tail = text[len(text.rstrip()):]
            tmpl.append(f"{lead}{{{{t{n}}}}}{tail}"); sample[f"t{n}"] = text.strip()
        else: tmpl.append(text)
    meta = {"name": name, "use": "A part of this brand's own, a block that came up in several slides. Say here what it is for.",
            "slots": {k: "text; in the sample: " + re.sub(r"<[^>]+>", "", v)[:50] for k, v in sample.items()}, "sample": sample}
    return "<!--vs " + json.dumps(meta, ensure_ascii=False) + " -->\n" + "".join(tmpl).strip() + "\n", sample

def words(html):
    """The runs of words of a block, in order, as to_part numbers them."""
    return [t.strip() for k, t in _split(html) if k == "t" and re.sub(r"<[^>]+>", "", t).strip()]

def _split(body):
    """[(kind, text)]: 'm' markup that stays, 't' a run of words with its inline tags."""
    out, cur, raw = [], 0, [(m.start(), m.end()) for m in _RAW.finditer(body)]
    def push(kind, text):
        if not text: return
        if out and out[-1][0] == kind: out[-1] = (kind, out[-1][1] + text)
        else: out.append((kind, text))
    toks = [m for m in re.finditer(r"<[^>]+>", body) if not any(a <= m.start() < b for a, b in raw)]
    i = 0
    while i <= len(toks):
        end = toks[i].start() if i < len(toks) else len(body)
        seg = body[cur:end]
        in_raw = next(((a, b) for a, b in raw if a <= cur < b), None)
        if in_raw: push("m", body[cur:in_raw[1]]); cur = in_raw[1]; continue
        nxt = next((a for a, b in raw if cur <= a < end), None)
        if nxt is not None: seg = body[cur:nxt]; end = nxt
        push("t" if seg.strip() else "m", seg)
        if nxt is not None: cur = end; continue
        if i == len(toks): break
        tag = toks[i].group(0); nm = re.match(r"</?([a-zA-Z][\w-]*)", tag)
        inline = bool(nm) and nm.group(1).lower() in _INLINE and not re.search(r"\bclass=", tag)
        push("t" if inline else "m", tag)
        cur = toks[i].end(); i += 1
    return _balance(out)

def _balance(parts):
    """Inline tags at the edge of a run of words whose partner lies outside it go back to the markup, so that
    every run is whole: "<b>Fazit</b>" stays together, a lone "</b>" does not end a slot."""
    out = []
    def add(kind, text):
        if not text: return
        if out and out[-1][0] == kind: out[-1] = (kind, out[-1][1] + text)
        else: out.append((kind, text))
    for kind, text in parts:
        if kind != "t": add(kind, text); continue
        toks = re.split(r"(<[^>]+>)", text); stack, pair = [], {}
        for j, tk in enumerate(toks):
            m = re.match(r"<(/?)([a-zA-Z][\w-]*)", tk or "")
            if not m or (tk.rstrip().endswith("/>")) or m.group(2).lower() == "br": continue
            if not m.group(1): stack.append((m.group(2).lower(), j))
            else:
                k = next((x for x in range(len(stack) - 1, -1, -1) if stack[x][0] == m.group(2).lower()), None)
                if k is not None: pair[stack[k][1]] = j; pair[j] = stack[k][1]; del stack[k]
        lone = {j for j, tk in enumerate(toks) if tk.startswith("<") and j not in pair and not re.match(r"<br\b", tk, re.I)}
        a, b = 0, len(toks)
        while a < b and (not toks[a].strip() or a in lone): a += 1
        while b > a and (not toks[b - 1].strip() or (b - 1) in lone): b -= 1
        mid = "".join(toks[a:b])
        if not re.sub(r"<[^>]+>", "", mid).strip(): add("m", text); continue
        add("m", "".join(toks[:a])); add("t", mid); add("m", "".join(toks[b:]))
    return out

def to_master(name, slide, langs):
    """A free slide as a master: its body stays as it is, every run of words becomes a slot (t1, t2, …) with
    the slide's words as the sample. Returns (text of the master file, the slide as it stands in a deck from
    now on, the slot names)."""
    bodies = slide.get("body"); per_lang = isinstance(bodies, dict) and set(bodies) <= set(langs) | {"*"}
    first = (bodies.get(langs[0]) or next(iter(bodies.values()))) if per_lang else str(bodies or "")
    split = _split
    parts = split(first); tmpl, sample, n = [], {}, 0
    for kind, text in parts:
        if kind == "t" and re.sub(r"<[^>]+>", "", text).strip():
            n += 1; lead = text[:len(text) - len(text.lstrip())]; tail = text[len(text.rstrip()):]
            tmpl.append(f"{lead}{{{{t{n}}}}}{tail}"); sample[f"t{n}"] = text.strip()
        else: tmpl.append(text)
    slots = {"kicker": "small label above the title (optional)", "title": "the title as a full sentence, <em> marks the one accent word", "lead": "one sentence (optional)"}
    slots.update({k: "text; in the sample: " + re.sub(r"<[^>]+>", "", v)[:50] for k, v in sample.items()})
    new = {k: v for k, v in slide.items() if k not in ("master", "body", "class")}; new["master"] = name
    if per_lang:                                             # the words of every language, slot by slot
        per = {l: [t.strip() for k, t in split(b) if k == "t" and re.sub(r"<[^>]+>", "", t).strip()] for l, b in bodies.items()}
        for j in range(n):
            vals = {l: v[j] for l, v in per.items() if j < len(v)}
            new[f"t{j + 1}"] = vals if len(set(vals.values())) > 1 else sample[f"t{j + 1}"]
    else: new.update(sample)
    smp = dict(sample); smp.update({k: (v.get(langs[0], next(iter(v.values()))) if isinstance(v, dict) else v) for k, v in slide.items() if k in ("kicker", "title", "lead")})
    meta = {"name": name, "order": 75, "use": "A form of this brand's own, taken from a slide that was written freely and came up again. Say here what it is for.", "slots": slots, "sample": smp}
    cls = re.sub(r"[^\w -]", "", str(slide.get("class") or "")).strip()
    text = ("<!--vs " + json.dumps(meta, ensure_ascii=False) + " -->\n"
            f'<section class="slide{" " + cls if cls else ""}" {{{{attrs}}}}>\n  {{{{#kicker}}}}<div class="kicker">{{{{kicker}}}}</div>{{{{/kicker}}}}\n  <h2>{{{{title}}}}</h2>\n'
            "  {{#lead}}<p class=\"lead\">{{lead}}</p>{{/lead}}\n  " + "".join(tmpl).strip() + "\n  {{notes}}\n</section>\n")
    return text, new, list(sample)
