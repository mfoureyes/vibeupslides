"""The brand's voice: measure how a company writes, and check slide text against its rules.

A voice profile has two parts in the brand library:

    voice.md                 the description a writer works from: address, tone, sentences, words, fixed terms,
                             real sentences, before and after. Written by the vs-build skill from what is measured here.
    brand.json  "voice"      the rules a build can check: {"sentence_max": 22, "exclamation": false,
                             "terms": ["Example Forum"], "avoid": ["leverage => use"],
                             "de": {"address": "Sie", "gender": ":innen", "avoid": [...]}}
                             Rules under a language code apply to that language only and win over the common ones.

What is measured comes from texts the company wrote itself: the website (raw/copy.md), documents that were
read in (sources/<document>/text.md, slides.md) and sample texts the user named (voice/samples/). The numbers
go to raw/voice.json. Used through vs.py: `voice <brand> [files...]`, and by every build.
"""
import json, os, re, shutil, time

TEXT_FILES = (".txt", ".md", ".markdown", ".text")

STOP = {
    "de": "der die das und ist nicht ein eine einer eines einem einen mit für auf von zu im in den dem des auch sich wir sie es als an bei wie oder aber dass sind wird werden "
          "hat haben kann können nach aus um über unter vor noch nur mehr sehr so zum zur ihr ihre ihren unser unsere unseren uns was wer wo wenn dann durch bis diese dieser "
          "dieses diesem man hier dort alle allen damit sowie ob war waren sein seine ich du er ja nein kein keine schon immer wieder beim vom ins am".split(),
    "en": "the and is are of to in a an for on with that this it as at by from or be we you our your their they not but have has was were will can more about all which "
          "what who how when where if than then so into out up its also been these those there here do does did no yes us i he she his her them may should would could "
          "just only very over under such each any some most other one two".split(),
    "fr": "le la les de des du et est un une pour dans que qui sur avec nous vous ne pas plus par au aux en ce cette ces son sa ses notre nos votre vos leur leurs il elle "
          "ils elles on ou mais comme sont être avoir a ont tout tous toute très se si y d l".split(),
    "es": "el la los las de del y es un una para en que con por nos no más su sus nuestro nuestra nuestros se lo al como son ser este esta estos usted tu o pero muy todo todos".split(),
    "it": "il lo la i gli le di del della e è un una per in che con non più su noi voi nostro nostra il suo sono essere questo questa come ma o molto tutti tutto si al dei".split(),
    "nl": "de het een en is van in op met voor dat die niet te zijn wij we u je jij ons onze uw aan bij als ook maar of om naar door over nog meer zeer alle dit deze er".split(),
}
STOP = {k: set(v) for k, v in STOP.items()}

_WORD = re.compile(r"[^\W\d_]+(?:[-'’:*][^\W\d_]+)*", re.U)
_SENT = re.compile(r"(?<=[.!?…])[\"”“’')\]]*\s+(?=[\"„“‚'(\[]?[A-ZÄÖÜÀ-Þ0-9])")
_ABBR = re.compile(r"\b(z\.\s?B|d\.\s?h|u\.\s?a|o\.\s?ä|bzw|ca|inkl|ggf|evtl|Nr|Dr|Prof|Mr|Mrs|Ms|vs|etc|e\.\s?g|i\.\s?e|No|St|approx|Inc|Ltd|Co|e\.\s?V|GmbH\s&\sCo)\.", re.I)

# words that show how readers are addressed, per language: informal, formal
_ADDRESS = {
    "de": {"du": re.compile(r"\b(du|dich|dir|dein\w*|euch|euer|eure\w*)\b", re.I),
           "Sie": re.compile(r"\bIhnen\b|(?<![.!?:]\s)(?<!^)\b(Sie|Ihr|Ihre[mnrs]?)\b", re.M)},
    "fr": {"tu": re.compile(r"\b(tu|toi|ton|ta|tes)\b", re.I), "vous": re.compile(r"\b(vous|votre|vos)\b", re.I)},
    "es": {"tú": re.compile(r"\b(tú|tu|tus|ti|contigo)\b", re.I), "usted": re.compile(r"\b(usted|ustedes)\b", re.I)},
    "it": {"tu": re.compile(r"\b(tu|tuo|tua|tuoi|tue)\b", re.I), "Lei": re.compile(r"(?<![.!?:]\s)(?<!^)\b(Lei|Suo|Sua)\b", re.M)},
    "nl": {"je": re.compile(r"\b(je|jij|jou|jouw)\b", re.I), "u": re.compile(r"\b(u|uw)\b", re.I)},
}
_WE = {"de": r"\b(wir|uns|unser\w*)\b", "en": r"\b(we|our|ours|us)\b", "fr": r"\b(nous|notre|nos)\b", "es": r"\b(nosotros|nuestr\w+)\b",
       "it": r"\b(noi|nostr\w+)\b", "nl": r"\b(wij|we|ons|onze)\b"}
_YOU = {"en": r"\b(you|your|yours)\b"}
# ways of writing gender-inclusive forms in German
_GENDER = {":innen": re.compile(r"\w:in(nen)?\b"), "*innen": re.compile(r"\w\*in(nen)?\b"), "_innen": re.compile(r"\w_in(nen)?\b"),
           "Innen": re.compile(r"[a-zäöü]In(nen)?\b"), "/innen": re.compile(r"\w/-?in(nen)?\b")}
_EMOJI = re.compile("[\U0001F300-\U0001FAFF\u2600-\u27BF]")


_NOT_PROSE = re.compile(r"\b\d{5}\s+[A-ZÄÖÜ]|\bc/o\b|©|\bcookies?\b|\b(HRB|USt|VAT)\b", re.I)      # postal addresses, legal lines, cookie notices

def plain(v):
    return re.sub(r"\s+", " ", re.sub(r"<[^>]+>", "", str(v or ""))).strip()

def words(text):
    return _WORD.findall(text)

def sentences(text):
    """Split running text into sentences. A text without a full stop is one sentence."""
    t = _ABBR.sub(lambda m: m.group(0).replace(".", "\u2024"), plain(text))        # abbreviations do not end a sentence
    t = re.sub(r"(\d)\.(\s?\d)", "\\1\u2024\\2", t)
    return [s.replace("\u2024", ".").strip() for s in _SENT.split(t) if s.strip()]

def language(text, among=None):
    """The language a text is written in, by its small words. among: the codes to choose from."""
    ws = [w.lower() for w in words(text)]
    if not ws: return None
    score = {k: sum(w in v for w in ws) for k, v in STOP.items() if not among or k in among}
    best = max(score, key=score.get) if score else None
    return best if best and score[best] >= max(1, len(ws) // 12) else None


# ---------------------------------------------------------------- sources

def _copy_md(path):
    """raw/copy.md of the website: headlines and paragraphs. Navigation and button labels are not sentences."""
    heads, paras, key = [], [], None
    for line in open(path, encoding="utf-8"):
        line = line.rstrip("\n")
        if line.startswith("## "): key = line[3:].strip(); continue
        if line.startswith("# "): key = None; continue
        if line.startswith("- ") and key in ("h1", "h2", "h3"): heads.append(line[2:].strip())
        elif line.startswith("- ") and key == "paragraphs" and not _NOT_PROSE.search(line): paras.append(line[2:].strip())
    return heads, paras

def _text_md(path):
    """A text file: headings and short lines without a full stop are headlines, the rest is running text."""
    heads, paras = [], []
    for block in re.split(r"\n\s*\n", open(path, encoding="utf-8", errors="replace").read()):
        for line in block.split("\n"):
            raw = line.strip()
            if not raw or raw.startswith(("|", "```", "<!--", "---", "![")) or re.match(r"^(page|seite|slide|folie)\s*\d+\s*$", raw, re.I): continue
            is_head = raw.startswith("#")
            t = plain(re.sub(r"^(#+|[-*•·]|\d+[.)])\s*", "", raw)).strip("*_ ")
            if len(words(t)) < 2: continue
            (heads if is_head or (len(words(t)) <= 9 and not re.search(r"[.!?]$", t)) else paras).append(t)
    return heads, paras

def sources(brand_dir):
    """Every text the company wrote that the library holds: [(label, kind, headlines, paragraphs)]. kind: sample, document, website."""
    out = []
    sd = os.path.join(brand_dir, "voice", "samples")
    for f in sorted(os.listdir(sd)) if os.path.isdir(sd) else []:
        if f.lower().endswith(TEXT_FILES): out.append(("voice/samples/" + f, "sample") + _text_md(os.path.join(sd, f)))
    src = os.path.join(brand_dir, "sources")
    for doc in sorted(os.listdir(src)) if os.path.isdir(src) else []:
        for f in ("text.md", "slides.md"):
            p = os.path.join(src, doc, f)
            if os.path.exists(p): out.append((f"sources/{doc}/{f}", "document") + _text_md(p))
    p = os.path.join(brand_dir, "raw", "copy.md")
    if os.path.exists(p): out.append(("raw/copy.md", "website") + _copy_md(p))
    return out


# ---------------------------------------------------------------- measuring

def _pct(n, of):
    return round(100 * n / of) if of else 0

def _quantile(v, q):
    v = sorted(v)
    return v[min(len(v) - 1, int(q * len(v)))] if v else 0

def _terms(texts, min_count=2):
    """Names written with capitals more than once: candidates for fixed terms."""
    seen = {}
    for t in texts:
        for m in re.finditer(r"\b[A-ZÄÖÜ][\w&.]*(?:[ -](?:[A-ZÄÖÜ0-9][\w&.]*|of|and|für|und|de|der))*[ -][A-ZÄÖÜ0-9][\w&.]*", t):
            k = re.sub(r"^(The|Der|Die|Das|Den|Dem|Our|Unser\w*|Le|La|Les) ", "", re.sub(r"[ -](19|20)\d\d$", "", m.group(0).strip(" .")))
            if len(k) > 5 and " " in k.replace("-", " ") and not re.search(r"\d{4,}", k): seen[k] = seen.get(k, 0) + 1
    keep = [k for k, n in sorted(seen.items(), key=lambda x: (-x[1], -len(x[0]))) if n >= min_count]
    return [k for k in keep if not any(k != o and k in o and seen[o] >= seen[k] for o in keep)][:14]

def measure(brand_dir, langs=None):
    """How the brand writes, per language: {"sources": [...], "langs": {code: {...}}}."""
    src = sources(brand_dir)
    per, listing = {}, []
    for label, kind, heads, paras in src:
        n = 0
        for group, items in (("heads", heads), ("paras", paras)):
            for t in items:
                lang = language(t, langs) or language(" ".join(paras[:40]), langs) or (langs or ["en"])[0]
                per.setdefault(lang, {"heads": [], "paras": [], "by": {}})[group].append(t)
                per[lang]["by"][kind] = per[lang]["by"].get(kind, 0) + len(words(t)); n += len(words(t))
        listing.append({"file": label, "kind": kind, "words": n})
    out = {"measured": time.strftime("%Y-%m-%d"), "sources": listing, "langs": {}}
    for lang, d in per.items():
        sents = [s for p in d["paras"] for s in sentences(p)]
        lens = [len(words(s)) for s in sents if len(words(s)) > 2]
        text = " ".join(d["heads"] + d["paras"])
        ws = [w.lower() for w in words(text)]
        stop = STOP.get(lang, set())
        content = [w for w in ws if len(w) > 3 and w not in stop]
        freq = {}
        for w in content: freq[w] = freq.get(w, 0) + 1
        pairs = {}
        for a, b in zip(ws, ws[1:]):
            if a not in stop and b not in stop and len(a) > 2 and len(b) > 2: pairs[a + " " + b] = pairs.get(a + " " + b, 0) + 1
        addr = {k: len(rx.findall(text)) for k, rx in _ADDRESS.get(lang, {}).items()}
        if lang in _YOU: addr["you"] = len(re.findall(_YOU[lang], text, re.I))
        gender = {k: len(rx.findall(text)) for k, rx in _GENDER.items()} if lang == "de" else {}
        m = {"words": len(ws), "words_by_source": d["by"], "sentences": len(lens), "headlines": len(d["heads"]),
             "sentence_words": {"median": _quantile(lens, .5), "nine_in_ten_under": _quantile(lens, .9), "longest": max(lens or [0])},
             "headline_words": {"median": _quantile([len(words(h)) for h in d["heads"]], .5), "longest": max([len(words(h)) for h in d["heads"]] or [0])},
             "address": addr, "we_sentences_pct": _pct(sum(bool(re.search(_WE.get(lang, r"$^"), s, re.I)) for s in sents), len(sents)),
             "questions_pct": _pct(sum(s.rstrip("\"”’)").endswith("?") for s in sents + d["heads"]), len(sents) + len(d["heads"])),
             "exclamations_pct": _pct(sum("!" in s for s in sents + d["heads"]), len(sents) + len(d["heads"])),
             "headlines_with_full_stop_pct": _pct(sum(h.endswith(".") for h in d["heads"]), len(d["heads"])),
             "emoji": len(_EMOJI.findall(text)), "gender_forms": {k: v for k, v in gender.items() if v},
             "frequent_words": [w for w, n in sorted(freq.items(), key=lambda x: -x[1]) if n > 1][:30],
             "frequent_pairs": [w for w, n in sorted(pairs.items(), key=lambda x: -x[1]) if n > 1][:12],
             "term_candidates": _terms(d["heads"] + d["paras"]),
             "longest_sentences": sorted(sents, key=lambda s: -len(words(s)))[:3]}
        m["thin"] = m["words"] < 250                        # too little text to trust the numbers
        out["langs"][lang] = m
    return out

def suggest(measured):
    """Rules drafted from the measurement. A draft: the user and the profile decide."""
    rules, terms = {}, []
    all_lens = [m["sentence_words"]["nine_in_ten_under"] for m in measured["langs"].values() if m["sentences"] >= 5]
    med = [m["sentence_words"]["median"] for m in measured["langs"].values() if m["sentences"] >= 5]
    rules["sentence_max"] = min(24, max(14, round((max(med) + max(all_lens)) / 2))) if all_lens else 20       # between the usual and the long sentence of the brand's own texts
    rules["exclamation"] = any(m["exclamations_pct"] >= 8 for m in measured["langs"].values())
    for lang, m in measured["langs"].items():
        own = {}
        formal_informal = {k: v for k, v in m["address"].items() if k != "you" and v}
        if formal_informal:
            top = max(formal_informal, key=formal_informal.get)
            if formal_informal[top] >= 2 and formal_informal[top] >= 3 * sum(v for k, v in formal_informal.items() if k != top): own["address"] = top
        if m.get("gender_forms"):
            top = max(m["gender_forms"], key=m["gender_forms"].get)
            if m["gender_forms"][top] >= 2: own["gender"] = top
        if own: rules[lang] = own
        terms += [t for t in m["term_candidates"] if t not in terms]
    rules["terms"] = terms[:12]
    rules["avoid"] = []
    return rules


# ---------------------------------------------------------------- checking

def rules_for(voice, lang):
    """The rules that apply to one language: the common ones, overridden and extended by those under the language code."""
    if not isinstance(voice, dict): return {}
    codes = set(STOP) | {k for k, v in voice.items() if isinstance(v, dict) and len(k) in (2, 5)}
    r = {k: v for k, v in voice.items() if k not in codes}
    own = voice.get(lang) or voice.get((lang or "")[:2]) or {}
    for k, v in (own if isinstance(own, dict) else {}).items():
        r[k] = (list(r.get(k) or []) + list(v)) if k in ("avoid", "terms") and isinstance(v, list) else v
    return r

def count_rules(r):
    return sum(1 for k in ("sentence_max", "address", "gender") if r.get(k)) + (1 if r.get("exclamation") is False else 0) + len(r.get("avoid") or []) + len(r.get("terms") or [])

def _short(s, n=9):
    w = s.split()
    return " ".join(w[:n]) + (" …" if len(w) > n else "")

_MSG = {
    "en": {"long": 'sentence of {n} words (limit {limit}): "{s}"', "avoid": '"{bad}" is a word this brand avoids', "use": ', it says "{use}"',
           "term": 'written "{got}", the fixed term is "{term}"', "address": 'addresses the reader with "{got}", this brand says "{want}"',
           "gender": 'gender form "{got}", this brand writes "{want}"', "excl": "exclamation mark, this brand does not use them"},
    "de": {"long": 'Satz mit {n} Wörtern (Grenze {limit}): „{s}“', "avoid": '„{bad}“ vermeidet diese Marke', "use": ', sie sagt „{use}“',
           "term": 'geschrieben „{got}“, der feste Begriff heißt „{term}“', "address": 'Anrede „{got}“, diese Marke sagt „{want}“',
           "gender": 'Genderform „{got}“, diese Marke schreibt „{want}“', "excl": "Ausrufezeichen, diese Marke verwendet keine"},
}

def check_text(text, rules, lang, reader=False, ui="en"):
    """Findings for one piece of text: a list of sentences that say what is wrong and what the rule is.
    ui: the language the findings are written in (en for the build report, de or en on the edit page)."""
    t = plain(text)
    if not t or not rules: return []
    M = _MSG.get(ui, _MSG["en"]); out = []
    limit = rules.get("sentence_max_read") if reader else rules.get("sentence_max")
    if limit:
        for s in sentences(t):
            n = len(words(s))
            if n > limit: out.append(M["long"].format(n=n, limit=limit, s=_short(s)))
    for entry in rules.get("avoid") or []:
        bad, _, use = [x.strip() for x in str(entry).partition("=>")]
        if bad and re.search(r"(?<!\w)" + re.escape(bad) + r"(?!\w)", t, re.I):
            out.append(M["avoid"].format(bad=bad) + (M["use"].format(use=use) if use else ""))
    for term in rules.get("terms") or []:
        parts = [re.escape(p) for p in re.split(r"[\s-]+", str(term)) if p]
        if not parts: continue
        for m in re.finditer(r"(?<!\w)" + r"[\s-]*".join(parts) + r"(?!\w)", t, re.I):
            if m.group(0) != term and m.group(0) not in (rules.get("terms") or []) and not m.group(0).isupper():
                out.append(M["term"].format(got=m.group(0), term=term)); break
    want = rules.get("address")
    for form, rx in _ADDRESS.get((lang or "")[:2], {}).items():
        if want and form != want:
            m = rx.search(t)
            if m: out.append(M["address"].format(got=m.group(0), want=want))
    want = rules.get("gender")
    if want and (lang or "")[:2] == "de":
        for form, rx in _GENDER.items():
            m = rx.search(t)
            if form != want and m: out.append(M["gender"].format(got=t[max(0, m.start() - 12):m.end()].split()[-1], want=want)); break
    if rules.get("exclamation") is False and "!" in t:
        out.append(M["excl"])
    return out

# slots that hold no text of the brand: files, settings, other people's words, sources
_NO_TEXT = {"master", "only", "lang", "name", "photo", "image", "images", "src", "video", "poster", "scene", "config", "icon", "logo", "logos", "file", "url", "href", "embed",
            "ratio", "step", "mark", "motion", "scheme", "fit", "handout", "source", "notes", "read", "quote", "voice", "edited", "chapter", "number", "value", "unit",
            "correct", "minutes", "share", "density", "brief", "align", "variant", "surface"}
_FILE = re.compile(r"^(https?:|data:|brand:|images/|assets/|@\w+$)|\.(jpe?g|png|svg|webp|gif|mp4|webm|mov|pdf)$", re.I)

def slots(slide):
    """The texts of a slide with the path of their slot: [("bullets.2", "text"), ...]. Language is resolved before."""
    out = []
    def walk(v, path, key):
        if isinstance(v, dict):
            for k, x in v.items():
                if k not in _NO_TEXT: walk(x, path + [k], k)
        elif isinstance(v, list):
            for i, x in enumerate(v, 1): walk(x, path + [str(i)], key)
        elif isinstance(v, str) and plain(v) and not _FILE.search(v.strip()):
            out.append((".".join(path), v))
    walk(slide, [], None)
    return out

def check_deck(deck, voice, lang, resolve, mode="live"):
    """Findings for every slide of a deck in one language: [(number in the deck file, master, slot, finding)].
    resolve: render._resolve_lang. A slide with "voice": false is not checked (text taken over word for word)."""
    rules = rules_for(voice, lang)
    if not count_rules(rules): return []
    langs = deck.get("langs") or [lang]
    out = []
    for i, slide in enumerate(deck.get("slides", []), 1):
        if slide.get("voice") is False or (slide.get("lang") and slide["lang"] != lang): continue
        if slide.get("only") in ("live", "reading") and slide["only"] != mode: continue
        s = resolve(slide, lang, langs)
        for path, text in slots(s):
            for f in check_text(text, rules, lang): out.append((i, slide.get("master", "?"), path, f))
        if mode == "reading" and s.get("read"):
            read = "\n".join(str(x) for x in s["read"]) if isinstance(s["read"], list) else str(s["read"])
            for f in check_text(read, rules, lang, reader=True): out.append((i, slide.get("master", "?"), "read", f))
    return out

def report(findings, rules, sample=False):
    """One report block for the build: clean, or one line per finding."""
    n = count_rules(rules)
    if not n: return "voice: no rules for this language"
    if not findings: return f"voice: clean ({n} rules)"
    where = (lambda f: f"master {f[1]}, {f[2]}") if sample else (lambda f: f"slide {f[0]} ({f[1]}), {f[2]}")
    return f"voice: {len(findings)} finding(s) against {n} rules" + "".join(f"\n    VOICE {where(f)}: {f[3]}" for f in findings)


# ---------------------------------------------------------------- the profile in the library

PROFILE_SKELETON = """# Voice profile: {name}

Measured on {date} from the company's own texts ({sources}). The numbers are in raw/voice.json, the rules a
build checks are in brand.json under "voice". This file is what a writer works from: every title, bullet,
label and reader text of a deck is written so that it could stand on the company's own website.
Lines marked TODO are judgements the measurement cannot make. Nothing is invented: what the texts do not
show is recorded as "not defined".

## In one paragraph
TODO: who speaks to whom, in which manner. Four sentences a new colleague could write from.

## Address and perspective
{address}
TODO: how the reader is addressed (formal, first name, not at all), who "we" is, how customers, members or
partners are named, how the company refers to itself (full name, short name, "we").

## Tone
TODO: three or four adjectives, each with a phrase from the texts as evidence, and for each the nearest
thing the company is not (confident, not loud).

## Sentences
{sentence_facts}
TODO: rhythm (one long sentence or short ones in a row), verbs or nouns, active or passive, questions,
imperatives, how a paragraph opens and how it ends.

## Words
{word_facts}
TODO the brand's words: for itself, for its customers, for its offer, for what it promises.
TODO words it avoids, each with what it says instead. Put them into brand.json as "avoid": ["word => instead"].

## Fixed terms
Candidates from the texts (names written with capitals more than once): {terms}
TODO: product, programme, event and role names exactly as written, with the forms that are wrong.
The confirmed ones go into brand.json as "terms".

## Ten real sentences
TODO: ten sentences word for word, each with its source, chosen so that together they show the range:
a claim, a description of the offer, an invitation, a number in a sentence, a sentence about people.

## Headlines
{headline_facts}
TODO: eight real headlines word for word, and what they have in common (statement or label, with or
without a verb, case, full stop).

## Before and after
TODO: five pairs. On the left a sentence as a generic deck would put it, on the right the same content in
this voice. Take the content from what the company really offers.

## On slides
TODO: the rules that follow for slide text, each one concrete: titles, labels above titles, bullets,
numbers and units, calls to action, reader text of a reading version.

{per_language}## Open points
TODO: what the texts do not answer and the user has to decide.
"""

def _facts(lang, m):
    a = m["address"]; sw = m["sentence_words"]; hw = m["headline_words"]
    addr = ", ".join(f"\"{k}\" {v}x" for k, v in a.items() if v) or "no direct address found"
    return {
        "address": f"Measured ({lang}): {addr}; \"we\" in {m['we_sentences_pct']} % of the sentences."
                   + (f" Gender forms: {', '.join(f'{k} {v}x' for k, v in m['gender_forms'].items())}." if m.get("gender_forms") else ""),
        "sentence_facts": f"Measured ({lang}): {m['sentences']} sentences, median {sw['median']} words, nine in ten under {sw['nine_in_ten_under']}, longest {sw['longest']}. "
                          f"Questions {m['questions_pct']} %, exclamation marks {m['exclamations_pct']} %, emojis {m['emoji']}."
                          + (" Little text: treat the numbers as a hint." if m["thin"] else ""),
        "word_facts": f"Frequent ({lang}): {', '.join(m['frequent_words'][:24]) or 'too little text'}.\nFrequent pairs: {', '.join(m['frequent_pairs']) or 'none'}.",
        "headline_facts": f"Measured ({lang}): {m['headlines']} headlines, median {hw['median']} words, longest {hw['longest']}, {m['headlines_with_full_stop_pct']} % end with a full stop.",
        "terms": ", ".join(m["term_candidates"]) or "none found"}

def draft(brand_dir, name="", langs=None, force=False):
    """Measure, write raw/voice.json, and give a brand without a profile its drafts: rules in brand.json, voice.md.
    Returns (measurement, rules written or None, voice.md written or not)."""
    m = measure(brand_dir, langs)
    os.makedirs(os.path.join(brand_dir, "raw"), exist_ok=True)
    json.dump(m, open(os.path.join(brand_dir, "raw", "voice.json"), "w", encoding="utf-8"), indent=1, ensure_ascii=False)
    bj = os.path.join(brand_dir, "brand.json"); wrote_rules = None
    data = json.load(open(bj, encoding="utf-8")) if os.path.exists(bj) else {}
    if os.path.exists(bj) and m["langs"] and (force or not isinstance(data.get("voice"), dict)):
        data["voice"] = wrote_rules = suggest(m)
        json.dump(data, open(bj, "w", encoding="utf-8"), indent=2, ensure_ascii=False)
    vp = os.path.join(brand_dir, "voice.md"); wrote_md = False
    if not os.path.exists(vp):
        order = sorted(m["langs"], key=lambda l: -m["langs"][l]["words"])      # the language with the most text leads
        first = _facts(order[0], m["langs"][order[0]]) if order else {k: "Nothing measured yet: no texts in the library." for k in ("address", "sentence_facts", "word_facts", "headline_facts")} | {"terms": "none"}
        rest = ""
        for l in order[1:]:
            f = _facts(l, m["langs"][l])
            rest += (f"## In {l}\n{f['address']}\n{f['sentence_facts']}\n{f['word_facts']}\n{f['headline_facts']}\nTerm candidates: {f['terms']}\n"
                     f"TODO: what differs from {order[0]} in this language (address, tone, terms that stay untranslated), with three real sentences.\n\n")
        open(vp, "w", encoding="utf-8").write(PROFILE_SKELETON.format(
            name=name or data.get("name") or os.path.basename(brand_dir), date=m["measured"],
            sources=", ".join(f"{s['file']} {s['words']} words" for s in m["sources"]) or "no texts yet", per_language=rest, **first))
        wrote_md = True
    return m, wrote_rules, wrote_md

def add_samples(brand_dir, files):
    """Copy texts the user named as typical into voice/samples/. Returns (added, refused)."""
    sd = os.path.join(brand_dir, "voice", "samples"); os.makedirs(sd, exist_ok=True)
    added, refused = [], []
    for f in files:
        if os.path.isfile(f) and f.lower().endswith(TEXT_FILES):
            shutil.copy(f, os.path.join(sd, os.path.basename(f))); added.append(os.path.basename(f))
        else:
            refused.append(f)
    return added, refused

def summary(m):
    L = []
    for s in m["sources"]: L.append(f"  source {s['file']}: {s['words']} words ({s['kind']})")
    if not m["sources"]: L.append("  no texts in the library yet: read the website (analyze), documents (ingest) or add sample texts (voice <brand> <files>)")
    for lang, x in m["langs"].items():
        f = _facts(lang, x)
        L += [f"\n[{lang}] {x['words']} words" + (" (little text, the numbers are a hint)" if x["thin"] else ""), "  " + f["address"], "  " + f["sentence_facts"],
              "  " + f["headline_facts"], "  " + f["word_facts"].replace("\n", "\n  "), "  Term candidates: " + f["terms"]]
    return "\n".join(L)
