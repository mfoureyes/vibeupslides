# -*- coding: utf-8 -*-
"""What a brand's decks have in common: shared slides and facts.

A brand keeps them in its library, in one place:

    library/<brand>/shared/slides/<name>.json    one slide as it would stand in a deck ({"master": "team", ...})
    library/<brand>/shared/facts.json            values many decks name: {"address": "...", "team": {"size": 42}, ...}

A deck uses them instead of copying them:

    {"shared": "team"}                           the slide, as it is in the library today
    {"shared": "team", "title": "Our team"}      the same slide with one field of its own
    "Visit us: {{fact.address}}"                 a fact inside any text; {{fact.team.size}} reaches into a group

A fact may differ by language ({"de": "...", "en": "..."}); the text that names it then differs by language too.
When a shared slide or a fact changes, `vs.py refresh` builds every deck that uses it again.
"""
import copy, json, os, re

FACT = re.compile(r"\{\{\s*fact\.([\w.-]+)\s*\}\}")
NAME = re.compile(r"^[a-z0-9][a-z0-9_-]*$")


def folder(brand_dir):
    return os.path.join(brand_dir, "shared")

def slides(brand_dir):
    """{name: slide} of the brand's shared slides. A file that is not valid JSON is left out and named in errors()."""
    out, d = {}, os.path.join(folder(brand_dir), "slides")
    for fn in sorted(os.listdir(d)) if os.path.isdir(d) else []:
        if fn.endswith(".json"):
            try:
                s = json.load(open(os.path.join(d, fn), encoding="utf-8"))
                if isinstance(s, dict): out[fn[:-5]] = s
            except (OSError, ValueError):
                pass
    return out

def facts(brand_dir):
    try:
        f = json.load(open(os.path.join(folder(brand_dir), "facts.json"), encoding="utf-8"))
        return f if isinstance(f, dict) else {}
    except (OSError, ValueError):
        return {}

def errors(brand_dir):
    """Files in shared/ that cannot be read, as lines for a report."""
    out, d = [], folder(brand_dir)
    for rel in ["facts.json"] + [os.path.join("slides", f) for f in (sorted(os.listdir(os.path.join(d, "slides"))) if os.path.isdir(os.path.join(d, "slides")) else []) if f.endswith(".json")]:
        p = os.path.join(d, rel)
        if os.path.exists(p):
            try: json.load(open(p, encoding="utf-8"))
            except ValueError as e: out.append(f"shared/{rel} is not valid JSON: {e}")
    return out

def _fact(all_facts, key, lang, langs):
    """The value of fact.a.b for a language, None if there is no such fact."""
    v = all_facts
    for part in key.split("."):
        if not isinstance(v, dict) or part not in v: return None
        v = v[part]
    if isinstance(v, dict) and v and set(v) <= set(langs) | {"*"}:
        v = v.get(lang, v.get("*", next(iter(v.values()))))
    return None if isinstance(v, (dict, list)) else str(v)

def _by_lang(all_facts, text, langs):
    """True if a text names a fact that differs by language."""
    for m in FACT.finditer(text):
        v = all_facts
        for part in m.group(1).split("."):
            v = v.get(part) if isinstance(v, dict) else None
        if isinstance(v, dict) and v and set(v) <= set(langs) | {"*"}: return True
    return False

def _fill(node, all_facts, langs, lang, used, missing):
    if isinstance(node, str):
        if "{{" not in node or not FACT.search(node): return node
        def one(l):
            def sub(m):
                v = _fact(all_facts, m.group(1), l, langs)
                if v is None: missing.add(m.group(1)); return m.group(0)
                used.add(m.group(1)); return v
            return FACT.sub(sub, node)
        if lang is None and len(langs) > 1 and _by_lang(all_facts, node, langs):
            return {l: one(l) for l in langs}
        return one(lang or langs[0])
    if isinstance(node, list):
        return [_fill(x, all_facts, langs, lang, used, missing) for x in node]
    if isinstance(node, dict):
        per_lang = bool(node) and set(node) <= set(langs) | {"*"} and lang is None
        return {k: _fill(v, all_facts, langs, (k if per_lang and k != "*" else lang), used, missing) for k, v in node.items()}
    return node

def resolve(deck, brand_dir):
    """The deck with its shared slides and facts filled in. Returns (deck, report); report has `slides` and `facts`
    (names the deck uses) and `problems` (lines). The deck given is not changed. Resolving a resolved deck changes
    nothing, so it is safe to do it wherever a deck is about to be rendered or checked."""
    lib, all_facts = slides(brand_dir), facts(brand_dir)
    langs = deck.get("langs") or [deck.get("lang") or "en"]
    out = dict(deck); used_slides, used, missing, problems = [], set(), set(), list(errors(brand_dir))
    new = []
    for i, s in enumerate(deck.get("slides") or [], 1):
        if isinstance(s, dict) and s.get("shared"):
            name = str(s["shared"])
            if name in lib:
                merged = copy.deepcopy(lib[name]); merged.update({k: v for k, v in s.items()})
                s = merged
                if name not in used_slides: used_slides.append(name)
            else:
                problems.append(f"slide {i} names the shared slide '{name}', which the brand does not have (shared/slides/{name}.json)")
        new.append(_fill(s, all_facts, langs, None, used, missing) if isinstance(s, dict) else s)
    out["slides"] = new
    for k in ("title", "footer_left", "footer_right"):
        if isinstance(out.get(k), str): out[k] = _fill(out[k], all_facts, langs, langs[0], used, missing)
    for m in sorted(missing):
        problems.append(f"the fact '{m}' is named in the deck and not in the brand's shared/facts.json")
    return out, {"slides": used_slides, "facts": sorted(used), "problems": problems}

def uses(deck):
    """What a deck file names without resolving it: (shared slide names, fact keys)."""
    names = [str(s["shared"]) for s in deck.get("slides") or [] if isinstance(s, dict) and s.get("shared")]
    return sorted(set(names)), sorted(set(FACT.findall(json.dumps(deck, ensure_ascii=False))))

def put_slide(brand_dir, name, slide):
    if not NAME.match(name): raise ValueError("a shared slide's name is lower case letters, digits, - and _")
    d = os.path.join(folder(brand_dir), "slides"); os.makedirs(d, exist_ok=True)
    clean = {k: v for k, v in slide.items() if k not in ("shared", "edited", "for_all")}
    json.dump(clean, open(os.path.join(d, name + ".json"), "w", encoding="utf-8"), indent=2, ensure_ascii=False)
    return os.path.join(d, name + ".json")

def set_fact(brand_dir, key, value):
    """Write one fact; a.b writes into a group. value: text, or {"de": ..., "en": ...}."""
    f = facts(brand_dir); node = f; parts = key.split(".")
    for p in parts[:-1]:
        if not isinstance(node.get(p), dict): node[p] = {}
        node = node[p]
    node[parts[-1]] = value
    os.makedirs(folder(brand_dir), exist_ok=True)
    json.dump(f, open(os.path.join(folder(brand_dir), "facts.json"), "w", encoding="utf-8"), indent=2, ensure_ascii=False)
