"""Editing a deck in the browser: every change goes back into deck.json, never into the built HTML.

    vs.py edit <deck> [--port N] [--no-open]

The edit build of a deck marks where the text of every slot stands (data-s="items.2.text", see render.py).
The page (edit.js, edit.css) lets the user type into those places, reorder list items and slides, duplicate
and delete them. Each change is sent to the local server, which writes it into deck.json through the
functions below, keeps the version before it in <deck>/.history/ (undo, redo) and builds the deck again.
Because the deck file stays the one source, both languages, the reading version and the PDF follow, and
the agent and the user work on the same file.
"""
import copy, json, os, re, shutil, threading, time

HERE = os.path.dirname(os.path.abspath(__file__))
EDIT_HTML = "_edit.html"                 # the edit build in the deck folder; files that start with _ are not presented or packed
KEEP = 200                               # versions kept for undo
_INLINE = ("em", "strong", "b", "i", "u", "sup", "sub", "br", "mark", "small")


def assets():
    css = open(os.path.join(HERE, "edit.css"), encoding="utf-8").read()
    js = open(os.path.join(HERE, "edit.js"), encoding="utf-8").read()
    return f"<style>\n{css}\n</style>\n<script>\n{js}\n</script>"

def sanitize(html):
    """What a browser hands back from an edited place -> the text of a slot: inline emphasis and line breaks stay,
    every other tag and all attributes go."""
    t = str(html or "").replace(" ", " ").replace("&nbsp;", " ")
    t = re.sub(r"<(script|style)\b.*?</\1\s*>", "", t, flags=re.S | re.I)
    t = re.sub(r"</(div|p)\s*>\s*<(div|p)\b[^>]*>", "<br>", t, flags=re.I)
    def tag(m):
        name, attrs = m.group(2).lower(), m.group(3) or ""
        if name in _INLINE: return f"<{m.group(1)}{name}>"
        if name in ("a", "span"):                           # a link keeps its address, a span its class
            if m.group(1): return f"</{name}>"
            keep = re.search(r'\bhref="((?:https?:|mailto:|#)[^"<>]*)"', attrs) if name == "a" else re.search(r'\bclass="([\w -]+)"', attrs)
            return f'<{name} {"href" if name == "a" else "class"}="{keep.group(1)}">' if keep else f"<{name}>"
        return ""
    t = re.sub(r"<(/?)([a-zA-Z][\w-]*)\b([^>]*)>", tag, t)
    t = re.sub(r"<!--.*?-->", "", t, flags=re.S).replace("\r", "")
    t = re.sub(r"\s*\n\s*", "<br>", t.strip())
    t = re.sub(r"(<br>\s*)+$", "", re.sub(r"[ \t]+", " ", t))
    return re.sub(r"<(em|strong|b|i|u|mark|small|span|a)>\s*</\1>", "", t).strip()


# ---------------------------------------------------------------- the deck file

def _is_langs(v, langs):
    return isinstance(v, dict) and bool(v) and set(v) <= set(langs) | {"*"}

def _slide(deck, n):
    slides = deck.get("slides") or []
    if not isinstance(n, int) or n < 1 or n > len(slides): raise ValueError(f"the deck has no slide {n}")
    return slides[n - 1]

def _step(node, key):
    if isinstance(node, list):
        if not key.isdigit() or not 1 <= int(key) <= len(node): raise ValueError("this place is not in the deck file")
        return int(key) - 1
    if isinstance(node, dict) and key in node: return key
    raise ValueError("this place is not in the deck file")

def _own(deck, n, path):
    """A slide the deck takes from the brand's shared slides ({"shared": "team"}): before a change goes into one of
    its fields, the deck gets that field as the library has it. The change is then this deck's own, in the
    language it was made in, and the other languages keep the shared text."""
    slide = _slide(deck, n); name = slide.get("shared"); key = next((p for p in str(path).split(".") if p), "")
    if not name or not key or key in slide: return
    try:
        import build as B, shared
        lib = shared.slides(B.brand_dir(deck.get("brand")))
    except Exception: return
    if key in (lib.get(str(name)) or {}): slide[key] = copy.deepcopy(lib[str(name)][key])

def set_text(deck, n, path, lang, text):
    """Write the text of one slot. A text that is the same in every language becomes one per language when it is
    changed in a deck with several languages: the user changed the language they were looking at."""
    langs = deck.get("langs") or [deck.get("lang") or "en"]
    _own(deck, n, path)
    slide = _slide(deck, n); parts = [p for p in str(path).split(".") if p]
    if not parts: raise ValueError("no slot named")
    node, in_lang = slide, False                        # in_lang: already inside one language's part of the file
    for i, key in enumerate(parts):
        last = i == len(parts) - 1
        if i == 0 and key not in node:                      # a default of the master that the deck did not set yet
            if not last: raise ValueError("this text comes from the master's defaults and cannot be changed here")
            node[key] = {lang: text} if len(langs) > 1 else text; return
        k = _step(node, key); child = node[k]
        if _is_langs(child, langs):                         # {"en": ..., "de": ...}: go on in the language that is shown
            if lang not in child:
                child[lang] = copy.deepcopy(child.get("*", next(iter(child.values()))))
            if last: child[lang] = text; return
            node, k = child, lang; child = node[k]; in_lang = True
            if isinstance(child, str): raise ValueError("this place is not in the deck file")
            node = child; continue
        if last:
            if isinstance(child, (dict, list)): raise ValueError("this slot holds more than one text")
            if len(langs) > 1 and not in_lang and isinstance(child, str) and child != text:
                node[k] = {l: (text if l == lang else child) for l in langs}
            else:
                node[k] = text
            return
        node = child

def carry(deck, n, path, lang, text, keep=False):
    """Note on the slide that the user changed a text: "edited": [{"path", "from", "to": [...], "text"}]. After the
    editing the agent corrects its spelling in the language it was written in (from) and translates it into the
    deck's other languages (to), which keep what they had until then. Returns the languages that wait for the
    translation. A figure is not noted."""
    langs = deck.get("langs") or [deck.get("lang") or "en"]
    others = [l for l in langs if l != lang]
    slide = _slide(deck, n)
    marks = [m for m in slide.get("edited") or [] if isinstance(m, dict) and m.get("path") != path]
    worded = bool(text and re.search(r"[^\W\d_]", re.sub(r"<[^>]+>", "", text)))
    if worded and keep and others: marks.append({"path": path, "from": lang, "to": others, "text": text, "keep": True})      # the user wants it exactly so: translate only
    elif worded and not keep: marks.append({"path": path, "from": lang, "to": others, "text": text})
    if marks: slide["edited"] = marks
    else: slide.pop("edited", None)
    return others if worded else []

def waiting(deck):
    """Texts the user changed that are not corrected and translated yet: [(slide number, note)]."""
    return [(i, m) for i, s in enumerate(deck.get("slides") or [], 1) for m in (s.get("edited") or []) if isinstance(m, dict) and m.get("path")]

def todo(deck):
    """The lines a command prints for the agent after the user edited: what to correct and translate where."""
    return [f"REVIEW slide {i}, {m.get('path')}: written in {m.get('from')} by the user"
            + ("; they want it exactly as it stands, do not correct it" if m.get("keep") else "; correct spelling, grammar and punctuation there without rewording it")
            + (f", translate it into {', '.join(m['to'])}" if m.get("to") else "") + ", then remove the entry from the slide's \"edited\""
            + (f". Slide {i} is the brand's shared slide '{deck['slides'][i - 1]['shared']}': the change is this deck's own so far; ask the user whether it should hold for every deck, and if so write it into the shared slide and take the field out of this deck"
               if isinstance(deck["slides"][i - 1], dict) and deck["slides"][i - 1].get("shared") else "") for i, m in waiting(deck)]

def _lists(slide, path, langs):
    """Every list a path leads to: one, or one per language where the deck keeps a list per language."""
    nodes = [slide]
    for key in [p for p in str(path).split(".") if p]:
        nxt = []
        for node in nodes:
            child = node[_step(node, key)]
            nxt += list(child.values()) if _is_langs(child, langs) and not isinstance(next(iter(child.values())), str) else [child]
        nodes = nxt
    out = []
    for x in nodes:
        if not isinstance(x, list): raise ValueError("this is not a list")
        if not any(x is y for y in out): out.append(x)
    return out

def _item(path):
    """"items.2.text" -> ("items", 2): the innermost list item a place belongs to."""
    parts = [p for p in str(path).split(".") if p]
    for i in range(len(parts) - 1, 0, -1):
        if parts[i].isdigit(): return ".".join(parts[:i]), int(parts[i])
    raise ValueError("this text is not part of a list")

def item_op(deck, n, path, op):
    """Move a list item up or down, duplicate or delete it, in every language's list. Returns the item's new number."""
    langs = deck.get("langs") or [deck.get("lang") or "en"]
    base, i = _item(path); new = i
    _own(deck, n, base)
    for lst in _lists(_slide(deck, n), base, langs):
        if not 1 <= i <= len(lst): continue
        if op == "up" and i > 1: lst[i - 2], lst[i - 1] = lst[i - 1], lst[i - 2]; new = i - 1
        elif op == "down" and i < len(lst): lst[i - 1], lst[i] = lst[i], lst[i - 1]; new = i + 1
        elif op == "duplicate": lst.insert(i, copy.deepcopy(lst[i - 1])); new = i + 1
        elif op == "delete":
            if len(lst) < 2: raise ValueError("the last item of a list stays; delete the slide or change the master")
            del lst[i - 1]; new = min(i, len(lst))
    _remark(_slide(deck, n), base, i, op)
    return new

def _remark(slide, base, i, op):
    """Keep the notes of what waits for translation on the items they belong to when a list changes."""
    keep = []
    for m in slide.get("edited") or []:
        path = str(m.get("path") or "")
        if path.startswith(base + "."):
            rest = path[len(base) + 1:].split("."); k = int(rest[0]) if rest[0].isdigit() else 0
            if op == "up" and i > 1: k = i - 1 if k == i else (i if k == i - 1 else k)
            elif op == "down": k = i + 1 if k == i else (i if k == i + 1 else k)
            elif op == "duplicate" and k > i: k += 1
            elif op == "delete":
                if k == i: continue
                if k > i: k -= 1
            m = dict(m, path=".".join([base, str(k)] + rest[1:]))
        keep.append(m)
    if keep: slide["edited"] = keep
    else: slide.pop("edited", None)

def slide_op(deck, n, op):
    """Move a slide earlier or later, duplicate or delete it. Returns the number of the slide to show afterwards."""
    slides = deck.get("slides") or []; _slide(deck, n)
    if op == "earlier" and n > 1: slides[n - 2], slides[n - 1] = slides[n - 1], slides[n - 2]; return n - 1
    if op == "later" and n < len(slides): slides[n - 1], slides[n] = slides[n], slides[n - 1]; return n + 1
    if op == "duplicate": slides.insert(n, copy.deepcopy(slides[n - 1])); return n + 1
    if op == "delete":
        if len(slides) < 2: raise ValueError("a deck keeps at least one slide")
        del slides[n - 1]; return min(n, len(slides))
    return n


def set_anim(deck, n, key, value):
    """How one slide moves: "step" (builds up on click, true or false; None: as its master does it), "move"
    (calm, expressive, off; anything else: as the deck) and "order" (its click steps in an order of its own, see
    render._order; empty: as the slide has them)."""
    slide = _slide(deck, n)
    if key == "step":
        if isinstance(value, bool): slide["step"] = value
        else: slide.pop("step", None)
    elif key == "move":
        if value in ("calm", "expressive", "off"): slide["move"] = value
        else: slide.pop("move", None)
    elif key == "all":                                      # a shared slide whose change should hold for every presentation (see vs.py shared <brand> push)
        if value and slide.get("shared"): slide["for_all"] = True
        else: slide.pop("for_all", None)
    elif key == "order":                                    # the click steps in an order of the user's own: "3,1+2"
        from render import _order
        o = _order(value)
        if o: slide["order"] = [int(e) if "+" not in e else [int(x) for x in e.split("+")] for e in o.split(",")]
        else: slide.pop("order", None)
    else: raise ValueError("unknown setting")

def get_text(deck, n, path, lang):
    """The text that stands at a slot's path for a language, None if there is none."""
    try:
        langs = deck.get("langs") or [deck.get("lang") or "en"]
        node = _slide(deck, n)
        if path in ("notes", "read"):
            node = node.get(path)
            if isinstance(node, list): node = "\n\n".join(str(x) for x in node)
        else:
            for key in [p for p in str(path).split(".") if p]:
                if _is_langs(node, langs): node = node.get(lang, node.get("*"))
                node = node[_step(node, key)]
        if _is_langs(node, langs): node = node.get(lang, node.get("*"))
        return node if isinstance(node, str) else None
    except (ValueError, KeyError, IndexError, TypeError, AttributeError):
        return None

REVIEW = "review.json"                   # in the deck folder: what the user typed the last time their changes were applied

def report(deck_dir, deck):
    """What became of the texts the user typed, for the page to show them: [{slide, typed, now, changed, langs, pending}].
    changed: the text was corrected since; langs: the other languages that have a text there; pending: not looked at yet."""
    try: items = json.load(open(os.path.join(deck_dir, REVIEW), encoding="utf-8")).get("items") or []
    except (OSError, ValueError): return []
    plain = lambda t: re.sub(r"\s+", " ", re.sub(r"<[^>]+>", "", t or "")).strip()
    langs = deck.get("langs") or [deck.get("lang") or "en"]; out = []
    for it in items:
        now = get_text(deck, it.get("n"), it.get("path"), it.get("lang"))
        if now is None: continue
        try: marks = [m.get("path") for m in _slide(deck, it["n"]).get("edited") or [] if isinstance(m, dict)]
        except ValueError: marks = []
        others = [l for l in langs if l != it.get("lang") and get_text(deck, it["n"], it["path"], l) not in (None, now)]
        out.append({"slide": it["n"], "path": it["path"], "lang": it.get("lang"), "typed": plain(it.get("typed")), "now": plain(now),
                    "changed": plain(now) != plain(it.get("typed")), "langs": others, "pending": it["path"] in marks})
    return out

def base_of(deck_dir):
    """A mark of the deck file an editing page was built from."""
    import hashlib
    with open(os.path.join(deck_dir, "deck.json"), "rb") as f: return hashlib.sha1(f.read()).hexdigest()[:12]

def apply_edits(deck_dir, data, library=None):
    """Bring the changes a user made in a deck opened as a file into deck.json. data: what the page saved
    ({"ops": [...]}); slide numbers in it are those of the deck the page was built from, so they are followed
    through the moves, copies and deletions among the changes. library(): (masters of the brand, render.fit_langs),
    for slides the user added. Returns (number applied, list of notes)."""
    deck = load(deck_dir); ops = data.get("ops") or []; notes = []; done = 0; typed = {}
    order = list(range(1, len(deck.get("slides") or []) + 1))          # which slide of before stands where now
    if data.get("base") and data["base"] != base_of(deck_dir):
        notes.append("deck.json was changed after the editing page was built: the changes were applied to the deck as it is now, check the slides they name")
    for o in ops:
        try:
            if o.get("n") is None or o.get("n") not in order:
                notes.append(f"slide {o.get('n')} of the edited page was deleted by the user: a change to it was dropped"); continue
            n = order.index(o["n"]) + 1; a = o.get("a")
            if a == "text":
                text = sanitize(o.get("html"))
                if not text: continue
                set_text(deck, n, o.get("path"), str(o.get("lang") or ""), text); carry(deck, n, o.get("path"), str(o.get("lang") or ""), text, keep=bool(o.get("ok")))
                typed[(o["n"], o.get("path"), str(o.get("lang") or ""))] = text
            elif a in ("notes", "read"):
                text = sanitize(o.get("html")); set_whole(deck, n, a, str(o.get("lang") or ""), text); carry(deck, n, a, str(o.get("lang") or ""), text, keep=bool(o.get("ok")))
                typed[(o["n"], a, str(o.get("lang") or ""))] = text
            elif a == "slide":
                op = o.get("op"); slide_op(deck, n, op); i = n - 1
                if op == "earlier" and i > 0: order[i - 1], order[i] = order[i], order[i - 1]
                elif op == "later" and i < len(order) - 1: order[i], order[i + 1] = order[i + 1], order[i]
                elif op == "duplicate": order.insert(n, o.get("id"))      # the page gave the copy a number of its own: changes to it follow
                elif op == "delete": del order[i]
            elif a == "item":
                item_op(deck, n, o.get("path"), o.get("op"))
            elif a == "anim":
                set_anim(deck, n, o.get("key"), o.get("value"))
            elif a == "fill":
                if not library: raise ValueError("a new field needs the brand's masters")
                masters, fit = library(); langs = deck.get("langs") or [deck.get("lang") or "en"]
                f = next((f for f in open_fields(_slide(deck, n), masters, fit, langs) if f["slot"] == o.get("slot")), None)
                if not f: raise ValueError("this field cannot be added here")
                _slide(deck, n)[f["slot"]] = f["text"]
            elif a == "add":
                if not library: raise ValueError("new slides need the brand's masters")
                masters, fit = library(); add_slide(deck, n, str(o.get("master")), masters, fit); order.insert(n, o.get("id"))
            else:
                notes.append(f"unknown change '{a}' left out"); continue
            done += 1
        except (ValueError, KeyError, IndexError, TypeError) as e:
            notes.append(f"slide {o.get('n')}, {o.get('path') or o.get('op') or o.get('a')}: not applied ({e})")
    if done:
        save(deck_dir, deck)
        items = [{"n": order.index(n) + 1, "path": p, "lang": l, "typed": t} for (n, p, l), t in typed.items() if n in order]
        json.dump({"applied": time.strftime("%Y-%m-%d %H:%M"), "items": items}, open(os.path.join(deck_dir, REVIEW), "w", encoding="utf-8"), indent=1, ensure_ascii=False)
    return done, notes


# ---------------------------------------------------------------- history

def _hist(deck_dir, kind):
    d = os.path.join(deck_dir, ".history", kind); os.makedirs(d, exist_ok=True); return d

def _stamp():
    return f"{time.strftime('%Y%m%d-%H%M%S')}-{int(time.time() * 1000) % 1000:03d}-{time.perf_counter_ns() % 100000:05d}.json"

def _push(deck_dir, kind):
    d = _hist(deck_dir, kind)
    shutil.copy(os.path.join(deck_dir, "deck.json"), os.path.join(d, _stamp()))
    for old in sorted(os.listdir(d))[:-KEEP]: os.remove(os.path.join(d, old))

def _pop(deck_dir, kind):
    d = _hist(deck_dir, kind); files = sorted(os.listdir(d))
    if not files: return False
    shutil.move(os.path.join(d, files[-1]), os.path.join(deck_dir, "deck.json")); return True

def load(deck_dir):
    return json.load(open(os.path.join(deck_dir, "deck.json"), encoding="utf-8"))

def save(deck_dir, deck, history=True):
    """Write deck.json; the version before it goes to .history/undo, and what could be redone is gone.
    history False: a change that belongs to the step before it (a translation that arrives later)."""
    if history:
        _push(deck_dir, "undo")
        shutil.rmtree(_hist(deck_dir, "redo"), ignore_errors=True)
    tmp = os.path.join(deck_dir, "deck.json.tmp")
    json.dump(deck, open(tmp, "w", encoding="utf-8"), indent=2, ensure_ascii=False)
    os.replace(tmp, os.path.join(deck_dir, "deck.json"))

def undo(deck_dir):
    if not os.listdir(_hist(deck_dir, "undo")): return False
    _push(deck_dir, "redo"); return _pop(deck_dir, "undo")

def redo(deck_dir):
    if not os.listdir(_hist(deck_dir, "redo")): return False
    _push(deck_dir, "undo"); return _pop(deck_dir, "redo")

def depth(deck_dir):
    return len(os.listdir(_hist(deck_dir, "undo"))), len(os.listdir(_hist(deck_dir, "redo")))


# ---------------------------------------------------------------- the server's side

def set_whole(deck, n, key, lang, text):
    """Write a text that belongs to the slide as a whole (notes, reader text) for one language."""
    langs = deck.get("langs") or [deck.get("lang") or "en"]
    _own(deck, n, key)
    slide = _slide(deck, n); old = slide.get(key)
    if isinstance(old, list): old = "\n\n".join(str(x) for x in old)
    if _is_langs(old, langs): old[lang] = text; slide[key] = old
    elif len(langs) > 1 and old and old != text: slide[key] = {l: (text if l == lang else old) for l in langs}
    elif len(langs) > 1 and not old: slide[key] = {lang: text}
    else: slide[key] = text

_FILEISH = re.compile(r"^(https?:|data:|brand:|images/|assets/|@)|\.(jpe?g|png|svg|webp|gif|mp4|webm|mov|pdf)$", re.I)

def _clean_sample(v):
    """A master's sample as the start of a new slide: without the stand-in pictures of the preview."""
    if isinstance(v, dict): return {k: x for k, x in ((k, _clean_sample(x)) for k, x in v.items()) if x is not None}
    if isinstance(v, list): return [x for x in (_clean_sample(x) for x in v) if x is not None]
    return None if isinstance(v, str) and v.strip().startswith("@") else v

def _has_standin(v):
    if isinstance(v, dict): return any(_has_standin(x) for x in v.values())
    if isinstance(v, list): return any(_has_standin(x) for x in v)
    return isinstance(v, str) and v.strip().startswith("@")

def new_slides(masters):
    """The masters a new slide can be made from on the page: those whose sample needs no picture or film.
    masters: render.load_masters(...). Returns [{"name", "title", "use"}]."""
    out = []
    for name, m in sorted(masters.items(), key=lambda kv: (kv[1]["meta"].get("order", 500), kv[0])):
        meta = m["meta"]
        if meta.get("sample") is None or meta.get("hidden") or meta.get("preview_only") or name in ("raw", "logo_intro") or _has_standin(meta["sample"]): continue
        out.append({"name": name, "title": meta.get("title") or name.replace("_", " ").capitalize(), "use": str(meta.get("use") or "")[:140]})
    return out

def add_slide(deck, n, name, masters, fit):
    """Insert a new slide after slide n, filled with the master's sample texts. fit: render.fit_langs. Returns its number."""
    if name not in {x["name"] for x in new_slides(masters)}: raise ValueError("this master cannot be added here")
    langs = deck.get("langs") or [deck.get("lang") or "en"]
    slide = dict(_clean_sample(fit(copy.deepcopy(masters[name]["meta"]["sample"]), langs)), master=name)
    slides = deck.setdefault("slides", []); n = max(0, min(int(n or 0), len(slides)))
    slides.insert(n, slide); return n + 1

def templates(deck, masters, env):
    """New slides for a deck that is edited as a file: every master a slide can be made from on the page, rendered
    once per language with its sample texts, for the page to insert without a server. env: the one the deck was just
    rendered with. A master that needs a picture, a film, a scene or scripts the deck does not carry is left out.
    Returns [{"name", "title", "use", "html": {lang: section}}]."""
    import render
    langs = deck.get("langs") or [deck.get("lang") or "en"]; out = []
    fresh = lambda: {k: (v.copy() if isinstance(v, (dict, list, set)) and k != "brand" else v) for k, v in env.items()}
    watch = ("images", "assets", "media", "scenes", "scene_fonts", "need_logo_inv", "warnings")
    for m in new_slides(masters):
        slide = dict(_clean_sample(render.fit_langs(copy.deepcopy(masters[m["name"]]["meta"]["sample"]), langs)), master=m["name"])
        e = fresh(); e.update(only=None, slide_no=0); was = {k: copy.copy(e.get(k)) for k in watch}
        try: html = {l: render._finish(render.render_slide(slide, l, masters, e), 0, e) for l in langs}
        except Exception: continue
        if any(e.get(k) != was[k] for k in watch) or any("{{" in h or "<script" in h for h in html.values()): continue
        out.append(dict(m, html=html))
    return out

def field_variants(deck, masters, env):
    """Text fields a slide could still take, for a deck that is edited as a file: every slide rendered once more
    with one such field filled with the master's sample, per language, for the page to put in its place.
    Slides that carry pictures are left out (their variant would carry the pictures again).
    Returns {slide number: [{"slot", "about", "html": {lang: section}}]}."""
    import render
    langs = deck.get("langs") or [deck.get("lang") or "en"]; out = {}
    for i, slide in enumerate(deck.get("slides") or [], 1):
        if not isinstance(slide, dict) or slide.get("lang"): continue
        for f in open_fields(slide, masters, render.fit_langs, langs):
            e = {k: (v.copy() if isinstance(v, (dict, list, set)) and k != "brand" else v) for k, v in env.items()}
            e.update(only=slide.get("only") if slide.get("only") in ("live", "reading") else None, slide_no=i)
            try: html = {l: render._finish(render.render_slide(dict(slide, **{f["slot"]: f["text"]}), l, masters, e), i, e) for l in langs}
            except Exception: continue
            if any("{{" in h or "<script" in h for h in html.values()): continue
            out.setdefault(str(i), []).append({"slot": f["slot"], "about": f["about"], "html": html})
    return out

def open_fields(slide, masters, fit, langs):
    """Text fields the slide's master offers that this slide does not use yet: [{"slot", "text", "about"}]."""
    m = masters.get(slide.get("master")); out = []
    if not m: return out
    sample = fit(copy.deepcopy(m["meta"].get("sample") or {}), langs)
    for slot, about in (m["meta"].get("slots") or {}).items():
        if slide.get(slot) not in (None, "", [], {}): continue
        v = sample.get(slot); about = str(about)
        is_text = (isinstance(v, str) and not _FILEISH.search(v.strip())) or (isinstance(v, dict) and v and all(isinstance(x, str) for x in v.values()) and set(v) <= set(langs) | {"*"})
        if v is None: is_text = "optional" in about and not re.search(r"\b(list|true|false|file|photo|image|picture|video|logo|number|url)\b", about, re.I)
        if is_text and slot not in ("notes", "read", "source", "name", "chapter"):
            out.append({"slot": slot, "text": v if v is not None else "Text", "about": about[:120]})
    return out

def make_api(deck_dir, rebuild, voice_rules=None, only=None, finish=None, library=None):
    """The function the local server calls for every request of the deck's page. rebuild(): builds the page again
    from deck.json. voice_rules(lang): the brand's rules for a language, to say at once what a new text breaks.
    only: the actions that are allowed (a presented deck takes notes and nothing else).
    finish(): called when the user is done and nothing waits for the agent: brings the deck's own HTML up to date.
    library(): (masters of the deck's brand, render.fit_langs), for new slides and for fields a slide does not use yet."""
    lock = threading.Lock()
    boot = str(time.time_ns())                              # tells a page that waited whether this is a new run of the server
    def changed(deck, out, n, path, lang, text, ui):
        out["waiting"] = carry(deck, n, path, lang, text); save(deck_dir, deck); rebuild()
        out.update(n=n, path=path, text=text, review=any(m.get("path") == path for i, m in waiting(deck) if i == n))
        if voice_rules and path not in ("notes", "read"):
            import voice
            out["voice"] = voice.check_text(text, voice_rules(lang), lang, ui=ui)
    def api(action, q):
        with lock:
            n = q.get("n"); lang = str(q.get("lang") or ""); ui = "de" if q.get("ui") == "de" else "en"; out = {"ok": True}
            if only and action not in only: raise ValueError("not available here")
            if action == "state":
                out["actions"] = sorted(only) if only else ["all"]
            elif action == "text":
                deck = load(deck_dir); text = sanitize(q.get("html"))
                if not text: raise ValueError("Ein leerer Text würde das Element entfernen: den Punkt oder die Folie löschen." if ui == "de" else
                                              "an empty text would remove the element; delete the item or the slide instead")
                set_text(deck, n, q.get("path"), lang, text); changed(deck, out, n, q.get("path"), lang, text, ui)
            elif action in ("notes", "read"):               # texts of the slide as a whole: speaker notes, reader text
                deck = load(deck_dir); text = sanitize(re.sub(r"\n\s*\n", "<br><br>", str(q.get("text") or "").strip()))
                set_whole(deck, n, action, lang, text); changed(deck, out, n, action, lang, text, ui)
            elif action == "library" and library:           # what the page can offer for this slide
                deck = load(deck_dir); masters, fit = library(); langs = deck.get("langs") or [deck.get("lang") or "en"]
                out["masters"] = new_slides(masters)
                out["fields"] = [dict(f, text=None) for f in open_fields(_slide(deck, n), masters, fit, langs)]
            elif action == "add" and library:
                deck = load(deck_dir); masters, fit = library()
                out["reload"] = add_slide(deck, n, str(q.get("master")), masters, fit); save(deck_dir, deck); rebuild()
            elif action == "fill" and library:
                deck = load(deck_dir); masters, fit = library(); langs = deck.get("langs") or [deck.get("lang") or "en"]
                f = next((f for f in open_fields(_slide(deck, n), masters, fit, langs) if f["slot"] == q.get("slot")), None)
                if not f: raise ValueError("this field cannot be added here")
                _slide(deck, n)[f["slot"]] = f["text"]; save(deck_dir, deck); rebuild(); out["reload"] = n
            elif action == "anim":                          # click steps and strength of movement of one slide
                deck = load(deck_dir); set_anim(deck, n, q.get("key"), q.get("value")); save(deck_dir, deck); rebuild(); out["reload"] = n
            elif action == "item":
                deck = load(deck_dir); out["item"] = item_op(deck, n, q.get("path"), q.get("op")); save(deck_dir, deck); rebuild(); out["reload"] = n
            elif action == "slide":
                deck = load(deck_dir); out["reload"] = slide_op(deck, n, q.get("op")); save(deck_dir, deck); rebuild()
            elif action in ("undo", "redo"):
                if not (undo if action == "undo" else redo)(deck_dir): raise ValueError("nothing to " + action)
                rebuild(); out["reload"] = n
            elif action == "done":                          # the user is finished
                if waiting(load(deck_dir)): out["stop"] = True      # texts wait for the agent: the server stops, the command goes on
                elif finish: finish()                       # nothing waits: the page simply goes back to the deck, the server stays
            else:
                raise ValueError("unknown request")
            out["undo"], out["redo"] = depth(deck_dir); out["boot"] = boot
            out["open"] = len(waiting(load(deck_dir)))
            return out
    return api
