"""The photos of a brand and what is known about them: images/index.json in the brand library.

Each photo is measured once by the machine (size, format, faces, where its subject stands, colours, light or dark)
and described once by Claude from a numbered contact sheet (what and who it shows, the mood, which slides it fits).
After that nobody needs to look at the photo again: a deck chooses its photos from the index, and the build takes
the crop from the faces in it."""
import hashlib, json, os, re, shutil, time, urllib.parse, urllib.request

EXT = (".jpg", ".jpeg", ".png", ".webp", ".avif")
FITS = ("cover", "chapter", "closing", "split", "background", "statement", "profile", "gallery")   # the places a photo can take
WORDS = ("what", "who", "mood", "fits", "people", "avoid")                                        # what Claude writes

_CASCADE = None


def index_path(bd):
    return os.path.join(bd, "images", "index.json")


def load(bd):
    try: d = json.load(open(index_path(bd), encoding="utf-8"))
    except (OSError, ValueError): d = {}
    d.setdefault("photos", {}); return d


def save(bd, d):
    os.makedirs(os.path.join(bd, "images"), exist_ok=True)
    d["photos"] = dict(sorted(d["photos"].items()))
    json.dump(d, open(index_path(bd), "w", encoding="utf-8"), indent=1, ensure_ascii=False)


def faces(im):
    """Faces in a picture: [(x0, y0, x1, y1)] in pixels. None when no detector is installed."""
    global _CASCADE
    try:
        import cv2, numpy as np
    except Exception:
        return None
    try:
        if _CASCADE is None:
            _CASCADE = [cv2.CascadeClassifier(os.path.join(cv2.data.haarcascades, n)) for n in ("haarcascade_frontalface_default.xml", "haarcascade_frontalface_alt2.xml")]
        g = cv2.cvtColor(np.array(im.convert("RGB")), cv2.COLOR_RGB2GRAY)
        g = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8, 8)).apply(g)      # photos behind text are darkened: bring the faces back out
        hits = [[tuple(int(v) for v in f) for f in c.detectMultiScale(g, scaleFactor=1.08, minNeighbors=6, minSize=(26, 26))] for c in _CASCADE]
        both = []                                           # a face counts when both detectors see it: one alone sees faces in textures
        for (x, y, w, h) in hits[0]:
            if any(min(x + w, a + c) - max(x, a) > .5 * min(w, c) and min(y + h, b + d) - max(y, b) > .5 * min(h, d) for (a, b, c, d) in hits[1]):
                both.append((x, y, x + w, y + h))
        return both
    except Exception:
        return None


def _sig(path):
    st = os.stat(path); return f"{st.st_size}:{int(st.st_mtime)}"


def measure(path):
    """What the machine sees in a photo: size, format, faces (0 to 1 of width and height), the point the crop keeps in
    view, three colours and whether it is light or dark."""
    from PIL import Image
    im = Image.open(path); im.load(); w, h = im.size
    small = im.convert("RGB"); small.thumbnail((1200, 1200)); sw, sh = small.size
    found = faces(small)
    if found:                                               # a face has skin in it: grey façades and flags have faces only for the detector
        ycc = small.convert("YCbCr")
        def skin(b):
            px = list(ycc.crop(b).resize((24, 24)).getdata())
            return sum(1 for (_, cb, cr) in px if 77 <= cb <= 127 and 133 <= cr <= 173) / len(px)
        found = [b for b in found if skin(b) > .25]
        found = [b for b in found if not any(o != b and (o[2] - o[0]) * (o[3] - o[1]) >= (b[2] - b[0]) * (b[3] - b[1])
                                             and o[0] <= (b[0] + b[2]) / 2 <= o[2] and o[1] <= (b[1] + b[3]) / 2 <= o[3] for o in found)]   # one head, one box
    fs = [[round(x0 / sw, 3), round(y0 / sh, 3), round(x1 / sw, 3), round(y1 / sh, 3)] for (x0, y0, x1, y1) in found or []]
    fs = [f for f in fs if (f[2] - f[0]) * (f[3] - f[1]) > .0004]           # specks in a crowd are no subject
    r = w / h
    out = {"w": w, "h": h, "format": "wide" if r > 1.9 else "landscape" if r > 1.15 else "square" if r > .87 else "portrait"}
    if found is not None: out["faces"] = fs
    if fs:                                                  # the middle of the faces, the heads a little above them
        big = max((f[2] - f[0]) * (f[3] - f[1]) for f in fs); main = [f for f in fs if (f[2] - f[0]) * (f[3] - f[1]) > .25 * big]
        cx = sum((f[0] + f[2]) / 2 for f in main) / len(main); cy = sum((f[1] + f[3]) / 2 for f in main) / len(main)
        out["focus"] = f"{round(cx * 100)}% {round(max(0, cy - .05) * 100)}%"
    q = small.resize((64, 64)).quantize(colors=5, method=Image.Quantize.MEDIANCUT)
    pal = q.getpalette(); counts = sorted(q.getcolors(), reverse=True)
    out["colors"] = ["#%02x%02x%02x" % tuple(pal[i * 3:i * 3 + 3]) for _, i in counts[:3]]
    g = small.convert("L").resize((32, 32)); mean = sum(g.getdata()) / 1024
    out["tone"] = "light" if mean > 150 else "dark" if mean < 95 else "mid"
    return out


def photo_files(bd):
    folder = os.path.join(bd, "images")
    if not os.path.isdir(folder): return []
    return sorted(f for f in os.listdir(folder) if f.lower().endswith(EXT) and not f.startswith(("sheet", ".")))


def update(bd):
    """Bring the index up to date with the folder: new or changed photos are measured, gone ones leave the index.
    Returns the index and the files nobody has described yet."""
    d = load(bd); ph = d["photos"]; files = photo_files(bd)
    sources = {}
    try:
        for p in json.load(open(os.path.join(bd, "brand.json"), encoding="utf-8")).get("images") or []:
            sources[os.path.basename(p.get("file", ""))] = p.get("source")
    except (OSError, ValueError): pass
    for f in list(ph):
        if f not in files: del ph[f]
    for f in files:
        path = os.path.join(bd, "images", f); e = ph.setdefault(f, {})
        if e.get("sig") != _sig(path):
            try: e.update(measure(path)); e["sig"] = _sig(path)
            except Exception as x: e["error"] = str(x)[:120]; continue
        if not e.get("source") and sources.get(f): e["source"] = sources[f]
    save(bd, d)
    return d, [f for f in files if not ph.get(f, {}).get("what")]


def sheet(bd, files, out=None):
    """A contact sheet of the given photos, numbered, with their file names, to be looked at once. Returns the paths
    of the sheets (twelve photos each)."""
    from PIL import Image, ImageDraw, ImageFont
    paths = []
    try: font = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", 22)
    except Exception: font = ImageFont.load_default()
    for k in range(0, len(files), 12):
        part = files[k:k + 12]; cols = 4; rows = (len(part) + cols - 1) // cols; cw, ch = 420, 300
        S = Image.new("RGB", (cols * cw, rows * (ch + 40)), "white"); dr = ImageDraw.Draw(S)
        for i, f in enumerate(part):
            x, y = (i % cols) * cw, (i // cols) * (ch + 40)
            try:
                im = Image.open(os.path.join(bd, "images", f)).convert("RGB"); im.thumbnail((cw - 16, ch - 16))
                S.paste(im, (x + (cw - im.width) // 2, y + (ch - im.height) // 2))
            except Exception: dr.text((x + 20, y + 20), "unreadable", fill="red", font=font)
            dr.text((x + 10, y + ch + 6), f"{k + i + 1}  {f}", fill="black", font=font)
        os.makedirs(os.path.join(bd, "raw"), exist_ok=True)
        p = out or os.path.join(bd, "raw", f"photos_{k // 12 + 1}.png")
        if len(files) > 12 and out: p = out.replace(".png", f"_{k // 12 + 1}.png")
        S.save(p); paths.append(p)
    return paths


def describe(bd, data):
    """Take Claude's words about photos into the index: {file: {what, who, mood, fits, people, avoid}}. Returns the
    files taken and notes about what was not."""
    d = load(bd); ph = d["photos"]; taken, notes = [], []
    for f, words in (data or {}).items():
        f = os.path.basename(f)
        if f not in ph: notes.append(f"{f}: not in the index (run vs.py photos <brand> first)"); continue
        if not isinstance(words, dict): notes.append(f"{f}: give an object of words"); continue
        for k, v in words.items():
            if k not in WORDS: notes.append(f"{f}: '{k}' is not a field ({', '.join(WORDS)})"); continue
            if k == "fits":
                v = [x for x in (v if isinstance(v, list) else re.split(r"[,\s]+", str(v))) if x]
                bad = [x for x in v if x not in FITS]
                if bad: notes.append(f"{f}: fits takes {', '.join(FITS)}, not {', '.join(bad)}")
                v = [x for x in v if x in FITS]
            ph[f][k] = v
        ph[f]["described"] = time.strftime("%Y-%m-%d"); taken.append(f)
    save(bd, d)
    return taken, notes


def _next_name(bd, ext):
    used = [int(m.group(1)) for f in os.listdir(os.path.join(bd, "images")) if (m := re.match(r"photo_(\d+)", f))]
    return f"photo_{max(used + [0]) + 1:02d}{ext}"


def _known(bd, folder="images"):
    out, d = {}, os.path.join(bd, folder)
    for f in (sorted(os.listdir(d)) if os.path.isdir(d) else []):
        if f.lower().endswith(EXT): out[hashlib.sha1(open(os.path.join(d, f), "rb").read()).hexdigest()] = f
    return out


def add(bd, src, source=None, again=True):
    """A photo from outside into the brand: a file or an address. Returns (file name in images/, note). The same
    photo twice is noted, not copied; one the user took out before comes back only when asked for (again)."""
    os.makedirs(os.path.join(bd, "images"), exist_ok=True)
    if re.match(r"https?://", src):
        req = urllib.request.Request(src, headers={"User-Agent": "Mozilla/5.0 VibeUpSlides"})
        data = urllib.request.urlopen(req, timeout=30).read(); ext = os.path.splitext(urllib.parse.urlsplit(src).path)[1].lower()
        source = source or src
    else:
        p = os.path.expanduser(src)
        if not os.path.isfile(p): raise ValueError(f"no such file: {src}")
        data = open(p, "rb").read(); ext = os.path.splitext(p)[1].lower(); source = source or os.path.basename(p)
    h = hashlib.sha1(data).hexdigest(); known = _known(bd)
    if h in known: return known[h], "the brand has this photo already"
    if not again and h in _known(bd, os.path.join("images", "removed")): return "", "taken out of the brand before"
    if ext not in EXT: ext = ".jpg"
    name = _next_name(bd, ext); path = os.path.join(bd, "images", name); open(path, "wb").write(data)
    if ext in (".webp", ".avif", ".png"):                   # one format the build and every viewer reads; png stays when it is see-through
        try:
            from PIL import Image
            im = Image.open(path)
            if ext != ".png" or im.mode not in ("RGBA", "LA", "P"):
                jpg = path[:-len(ext)] + ".jpg"; im.convert("RGB").save(jpg, quality=88); os.remove(path); name = os.path.basename(jpg)
        except Exception: pass
    d = load(bd); d["photos"].setdefault(name, {})["source"] = source; save(bd, d)
    _brand_list(bd, name, source)
    return name, ""


def _brand_list(bd, name, source, remove=False):
    p = os.path.join(bd, "brand.json")
    try: b = json.load(open(p, encoding="utf-8"))
    except (OSError, ValueError): return
    lst = [x for x in b.get("images") or [] if os.path.basename(x.get("file", "")) != name]
    if not remove: lst.append({"file": "images/" + name, "source": source})
    b["images"] = lst; json.dump(b, open(p, "w", encoding="utf-8"), indent=1, ensure_ascii=False)


def remove(bd, name):
    """Take a photo out of the brand: it moves to images/removed/, nothing is deleted."""
    name = os.path.basename(name); p = os.path.join(bd, "images", name)
    if not os.path.isfile(p): raise ValueError(f"the brand has no photo {name}")
    os.makedirs(os.path.join(bd, "images", "removed"), exist_ok=True); shutil.move(p, os.path.join(bd, "images", "removed", name))
    d = load(bd); d["photos"].pop(name, None); save(bd, d); _brand_list(bd, name, None, remove=True)


def lines(d):
    """The index as one line per photo, for choosing photos without looking at them."""
    out = []
    for f, e in d["photos"].items():
        bits = [e.get("format", "?"), e.get("tone", "")]
        if "faces" in e: bits.append(f"{len(e['faces'])} face(s)" if e["faces"] else "no faces")
        if e.get("fits"): bits.append("fits " + "/".join(e["fits"]))
        what = e.get("what") or "NOT DESCRIBED"
        out.append(f"{f}: {what}" + (f" | who: {e['who']}" if e.get("who") else "") + (f" | mood: {e['mood']}" if e.get("mood") else "")
                   + f" | {', '.join(b for b in bits if b)}" + (f" | avoid: {e['avoid']}" if e.get("avoid") else ""))
    return out


_FOCUS = {}


def focus_of(path):
    """The crop for a photo of a brand library from its index: "x% y%" or ""."""
    bd = os.path.dirname(os.path.dirname(os.path.abspath(path)))
    try: t = os.stat(index_path(bd)).st_mtime
    except OSError: return ""
    if _FOCUS.get(bd, (None,))[0] != t:                    # read again when the index changed (the editor runs for hours)
        _FOCUS[bd] = (t, {f: e.get("focus", "") for f, e in load(bd)["photos"].items()})
    return _FOCUS[bd][1].get(os.path.basename(path), "")


PLACES = {"cover": "cover", "cover_photo": "cover", "chapter": "chapter", "closing": "closing"}   # masters that open, divide and end a deck


def _used(v, out):
    if isinstance(v, str):
        t = v.strip()
        if re.match(r"(brand:)?images/[^\s]+\.(jpe?g|png|webp|avif)$", t, re.I): out.add(t)
    elif isinstance(v, dict):
        for x in v.values(): _used(x, out)
    elif isinstance(v, list):
        for x in v: _used(x, out)
    return out


def note(bd, deck, masters):
    """What the build says about the photos of a deck: a photo used twice, photos of the brand nobody has described,
    an opening, chapter or closing slide without a photo while the brand has one for that place."""
    lines, where = [], {}
    for i, s in enumerate(deck.get("slides") or [], 1):
        if isinstance(s, dict):
            for p in _used(s, set()): where.setdefault(p, []).append(i)
    for p, ns in where.items():
        if len(ns) > 1:
            lines.append(f"PHOTOS: {p} stands on slides {', '.join(map(str, ns))}. A photo appears once in a deck: take another one for "
                         f"slide {ns[-1]} from `vs.py photos <brand>` (a photo the slide's content calls for).")
    files = photo_files(bd)
    if not files: return lines
    d = load(bd); todo = [f for f in files if not d["photos"].get(f, {}).get("what")]
    if todo:
        lines.append(f"PHOTOS: {len(todo)} photo(s) of the brand are not described yet ({', '.join(todo[:4])}{' …' if len(todo) > 4 else ''}): "
                     "run `vs.py photos <brand>`, look at the contact sheet once and describe them, then choose photos from the index.")
    used = {os.path.basename(p) for p in where}; slotless = []
    for i, s in enumerate(deck.get("slides") or [], 1):
        if not isinstance(s, dict): continue
        place = PLACES.get(s.get("master")); m = masters.get(s.get("master")) or {}
        if place and m and "photo" not in ((m.get("meta") or {}).get("slots") or {}) and place != "cover" and s["master"] not in slotless:
            if any(place in (e.get("fits") or []) for e in d["photos"].values()):     # a copy of the brand from before chapter and closing took a photo
                slotless.append(s["master"])
                lines.append(f"PHOTOS: the brand's own master {s['master']} has no slot photo, and the brand has photos for this place. Give it one as the "
                             f"framework's {s['master']} has it (slot \"photo\" in the header, <div class=\"bgphoto\"><img src=\"{{{{photo}}}}\" alt=\"\"></div> "
                             "first in the section), keeping the brand's look, then set the photos.")
        if not place or "photo" not in ((m.get("meta") or {}).get("slots") or {}) or s.get("photo") or s.get("video") or s.get("photo") is False: continue
        free = [f for f, e in d["photos"].items() if place in (e.get("fits") or []) and f not in used]
        if free:
            lines.append(f"PHOTOS: slide {i} ({s.get('master')}) has no photo, and the brand has {len(free)} for this place ({', '.join(free[:3])}). "
                         "Set the one whose words fit the slide (\"photo\": \"brand:images/<file>\"), or \"photo\": false if the slide stays without.")
    return lines
