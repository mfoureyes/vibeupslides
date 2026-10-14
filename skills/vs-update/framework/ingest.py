#!/usr/bin/env python3
"""Read the documents a brand already has (style guide as PDF, slide master as PowerPoint, logos,
fonts) into its library, prepared so that an agent with vision can study them without the originals.

    python3 ingest.py <brand_dir> <file or folder> [...]        ingest documents
    python3 ingest.py pages <brand_dir> <document> 3,7,12       render further single pages of a PDF source

    library/<brand>/sources/
        SOURCES.md                 index over all documents: what each is, where to look, what was found
        <document>/findings.md     what could be measured (findings.json: the same as data)
        <document>/sheets/         contact sheets of the pages or slides, in order
        <document>/pages/          single pages, large enough for small print
        <document>/text.md, text/  the text per page (PDF)
        <document>/slides.md       slides in order: layout, title, body, notes (PowerPoint)
        <document>/layouts/        one drawing per slide layout, from the placeholder geometry (PowerPoint)
        <document>/images/ media/  embedded pictures (PDF) / the media files of the deck (PowerPoint)
        images/                    loose images the user passed in (screenshots, scans)
    library/<brand>/logos/         loose logo files      library/<brand>/fonts/inbox/   loose font files

PowerPoint files are read with the standard library alone (a .pptx is a zip of XML); the drawings
need Pillow. PDF needs `pypdfium2` and `pypdf`. Slides are rendered through LibreOffice (`soffice`)
when it is installed; without it every slide is drawn schematically from its shapes instead.
Everything written here stays in the user's library: sources are study material, never deck content.
"""
import colorsys, hashlib, io, json, os, posixpath, re, shutil, statistics, subprocess, sys, tempfile, time, zipfile
import xml.etree.ElementTree as ET
from collections import Counter

PDF_PIP = "pip install pypdfium2 pypdf"
IMG_EXT = {".png", ".jpg", ".jpeg", ".svg", ".webp", ".gif"}
FONT_EXT = {".woff2", ".woff", ".ttf", ".otf"}
PPT_EXT = {".pptx", ".potx", ".ppsx", ".pptm", ".potm"}
OFFICE_EXT = {".ppt", ".pot", ".pps", ".odp", ".otp", ".doc", ".docx", ".odt"}    # readable only through LibreOffice
BIG_MEDIA = 20 * 1024 * 1024       # audio and video above this size are listed, not copied
ALL_PAGES_UP_TO = 40               # PDFs up to this length get every page as a single image
PAGE_LONG_SIDE = 2000              # pixels, single pages
KEY_PAGES = re.compile(r"logo|signet|wordmark|bildmarke|wortmarke|schutzzone|clear ?space|colou?r|farb|palette|typo|schrift|font|typeface|"
                       r"layout|grid|raster|gestaltungsraster|icon|piktogramm|pictogram|imagery|bildsprache|bildwelt|photo|foto|illustration|"
                       r"tone of voice|tonalit|sprache|wording|chart|diagram|infografik|infographic|tabelle|table|powerpoint|pr[aä]sentation|slide|folie", re.I)

def slug(name):
    return re.sub(r"[^a-z0-9]+", "-", os.path.splitext(os.path.basename(name))[0].lower()).strip("-") or "document"

def find_soffice():
    for c in ("soffice", "libreoffice"):
        p = shutil.which(c)
        if p: return p
    for p in ("/Applications/LibreOffice.app/Contents/MacOS/soffice", r"C:\Program Files\LibreOffice\program\soffice.exe",
              r"C:\Program Files (x86)\LibreOffice\program\soffice.exe", "/usr/lib/libreoffice/program/soffice", "/opt/libreoffice/program/soffice"):
        if os.path.exists(p): return p
    return None

def _pil():
    try:
        from PIL import Image, ImageDraw, ImageFont
        return Image, ImageDraw, ImageFont
    except ImportError:
        return None

_FONTS = {}
def _font(size):
    size = max(8, int(size))
    if size not in _FONTS:
        _, _, ImageFont = _pil(); f = None
        for p in ("/System/Library/Fonts/Helvetica.ttc", "/System/Library/Fonts/Supplemental/Arial.ttf", "C:\\Windows\\Fonts\\arial.ttf",
                  "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf", "DejaVuSans.ttf"):
            try: f = ImageFont.truetype(p, size); break
            except Exception: pass
        if f is None:
            try: f = ImageFont.load_default(size)
            except Exception: f = ImageFont.load_default()
        _FONTS[size] = f
    return _FONTS[size]

def _write(path, text):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    open(path, "w", encoding="utf-8").write(text)

def _rel(path, base):
    return os.path.relpath(path, base).replace(os.sep, "/")

def contact_sheets(thumb, n, labels, out_dir, landscape=True, prefix="sheet"):
    """thumb(i, w) -> PIL image of item i at about width w. Nine landscape or eight portrait items per sheet."""
    Image, ImageDraw, _ = _pil()
    cols, rows, cw = (3, 3, 640) if landscape else (4, 2, 480)
    per, pad, lab, out = cols * rows, 12, 26, []
    os.makedirs(out_dir, exist_ok=True)
    for s in range(0, n, per):
        cells = [thumb(i, cw) for i in range(s, min(n, s + per))]
        ch = max(c.height for c in cells)
        sheet = Image.new("RGB", (cols * (cw + pad) + pad, ((len(cells) - 1) // cols + 1) * (ch + lab + pad) + pad), "#e9e9ec")
        d = ImageDraw.Draw(sheet)
        for k, c in enumerate(cells):
            x, y = pad + (k % cols) * (cw + pad), pad + (k // cols) * (ch + lab + pad)
            d.text((x + 2, y + 3), str(labels[s + k])[:70], fill="#222", font=_font(17))
            sheet.paste(c.convert("RGB"), (x, y + lab)); d.rectangle([x - 1, y + lab - 1, x + c.width, y + lab + c.height], outline="#b5b5bb")
        p = os.path.join(out_dir, f"{prefix}_{s + 1:03d}-{min(n, s + per):03d}.jpg")
        sheet.save(p, quality=86); out.append(p)
    return out

# ================================================================ colours and fonts named in text

_N = r"(\d{1,3})\s*%?"
_SEP = r"\s*[,/|;·\s]\s*"
COLOUR_PATTERNS = [
    ("hex", re.compile(r"(?<![\w#&])#([0-9a-fA-F]{6}|[0-9a-fA-F]{3})\b")),
    ("hex", re.compile(r"\bHEX(?:ADECIMAL)?\s*[:#]?\s*#?([0-9a-fA-F]{6})\b", re.I)),
    ("rgb", re.compile(r"\bRGB\s*[:(]?\s*" + _N + _SEP + _N + _SEP + _N, re.I)),
    ("rgb", re.compile(r"\bR\s*[:=]?\s*(\d{1,3})" + _SEP + r"G\s*[:=]?\s*(\d{1,3})" + _SEP + r"B\s*[:=]?\s*(\d{1,3})\b")),
    ("cmyk", re.compile(r"\bCMYK\s*[:(]?\s*" + _N + _SEP + _N + _SEP + _N + _SEP + _N, re.I)),
    ("cmyk", re.compile(r"\bC\s*[:=]?\s*" + _N + _SEP + r"M\s*[:=]?\s*" + _N + _SEP + r"Y\s*[:=]?\s*" + _N + _SEP + r"K\s*[:=]?\s*" + _N)),
    ("pantone", re.compile(r"\b(?:PANTONE|Pantone|PMS)\s*[®™:]?\s*((?:\d{2,4}(?:-\d{1,4})?(?:\s?(?:CP|UP|TCX|TPX|TPG|C|U|M)\b)?)|(?:(?:Process |Cool |Warm |Reflex |Rubine |Rhodamine |Bright |Dark |Medium )?"
                           r"(?:Black|Blue|Red|Green|Yellow|Orange|Purple|Violet|Gray|Grey|Cyan|Magenta|Pink)(?:\s\d{1,4})?(?:\s?(?:C|U|M)\b)?))")),
    ("ral", re.compile(r"\bRAL\s?(\d{4}|\d{3}\s\d{2}\s\d{2})\b")),
    ("hks", re.compile(r"\bHKS\s?(\d{1,2}(?:\s?[KNEZ]\b)?)")),
    ("ncs", re.compile(r"\bNCS\s?(S\s?\d{4}-[A-Z]\d{0,2}[A-Z]?)\b")),
]
_KEYWORD_ONLY = re.compile(r"^(hex(adecimal)?|rgb|cmyk|pantone|pms|ral|hks|ncs|web|screen|print|druck|spot|[\W\d_]+)*$", re.I)

def colours_in_text(text, page=None):
    """Colour values named in running text, grouped into swatches: values that follow each other
    without other words in between belong together, the label is the line of text before them."""
    hits = []
    for kind, rx in COLOUR_PATTERNS:
        for m in rx.finditer(text):
            if kind == "hex":
                h = m.group(1).lower(); v = "#" + (h if len(h) == 6 else "".join(c * 2 for c in h))
            elif kind in ("rgb", "cmyk"):
                nums = [int(x) for x in m.groups()]
                if max(nums) > (255 if kind == "rgb" else 100): continue
                v = "/".join(map(str, nums))
            else:
                v = re.sub(r"\s+", " ", m.group(1)).strip()
            hits.append((m.start(), m.end(), kind, v))
    hits.sort(); kept = []
    for h in hits:                                                 # drop matches nested in an earlier one
        if not kept or h[0] >= kept[-1][1]: kept.append(h)
    out, cur, last_end = [], None, 0
    for start, end, kind, v in kept:
        between = text[last_end:start] if last_end else text[max(0, start - 160):start]
        lines = [re.sub(r"\s+", " ", l).strip(" :·|-–—\t") for l in between.splitlines()]
        lines = [re.sub(r"[\s:,(]*\b(hex(adecimal)?|rgb|cmyk|pantone|pms)$", "", l, flags=re.I).strip(" :·|-–—") for l in lines]
        cand = [l for l in lines if len(re.findall(r"[^\W\d_]", l)) >= 3 and not _KEYWORD_ONLY.match(l) and len(l) <= 80]
        label = re.sub(r"^(?:[\s,;.:·|/-]+|(?:and|und|or|oder|sowie|&)\s+)+", "", cand[-1], flags=re.I) if cand else None
        if cur is None or label or kind in cur:
            cur = {"label": label or "", "page": page}; out.append(cur)
            a, b = max(0, start - 70), min(len(text), end + 70)
            cur["context"] = re.sub(r"\s+", " ", text[a:b]).strip()
        cur[kind] = v; last_end = end
    for c in out:
        if "hex" not in c and "rgb" in c:
            c["hex_from_rgb"] = "#%02x%02x%02x" % tuple(int(x) for x in c["rgb"].split("/"))
    return out

KNOWN_FONTS = ("Inter|Roboto|Roboto Slab|Roboto Condensed|Roboto Mono|Open Sans|Lato|Montserrat|Poppins|Source Sans(?: Pro| 3)?|Source Serif(?: Pro| 4)?|Noto Sans|Noto Serif|"
    "Helvetica(?: Neue| Now)?|Arial(?: Narrow| Black)?|Calibri|Cambria|Verdana|Tahoma|Georgia|Times New Roman|Segoe UI|Aptos|Futura|Avenir(?: Next)?|Gotham|Proxima Nova|"
    "Univers|Frutiger|Akzidenz[- ]Grotesk|DIN(?: Pro| Next| 2014| Condensed)?|FF DIN|FF Meta|Meta(?: Pro)?|TheSans|TheSerif|TheMix|Fira Sans|Fira Code|IBM Plex(?: Sans| Serif| Mono)?|"
    "Work Sans|Nunito(?: Sans)?|Raleway|Oswald|Merriweather|Playfair Display|PT Sans|PT Serif|Ubuntu|Barlow(?: Condensed)?|Manrope|DM Sans|DM Serif(?: Display| Text)?|Space Grotesk|"
    "Rubik|Karla|Mulish|Outfit|Sora|Lexend|Plus Jakarta Sans|Libre Franklin|Franklin Gothic|Garamond|Adobe Garamond|EB Garamond|Minion(?: Pro)?|Myriad(?: Pro)?|Gill Sans|Optima|"
    "Rockwell|Bodoni|Didot|Baskerville|Libre Baskerville|Caslon|Sabon|Palatino|Century Gothic|Trebuchet MS|Circular|Graphik|GT America|GT Walsheim|S[oö]hne|Neue Haas Grotesk|"
    "Neue Haas Unica|Suisse(?: Int'l)?|Aeonik|Apercu|Brandon Grotesque|Museo(?: Sans| Slab)?|Klavika|Interstate|Trade Gothic|News Gothic|Bebas Neue|Anton|Archivo|Cabin|Dosis|"
    "Exo(?: 2)?|Hind|Josefin Sans|Kanit|Quicksand|Titillium(?: Web)?|Varela Round|Zilla Slab|Bitter|Crimson(?: Text| Pro)?|Cormorant(?: Garamond)?|Lora|Spectral|Tiempos|Canela|"
    "Recoleta|Clan(?: Pro)?|Corporate [ASE]|Thesis|Rotis|Syntax|Stone Sans|Officina(?: Sans| Serif)?|Lucida(?: Sans| Grande)?|Consolas|Courier(?: New)?|JetBrains Mono|Space Mono|"
    "SF Pro(?: Display| Text)?|San Francisco|Segoe|Corbel|Candara|Constantia|Century Schoolbook|Bahnschrift|Selawik|Atkinson Hyperlegible|Public Sans|Red Hat(?: Display| Text)?|"
    "Be Vietnam(?: Pro)?|Figtree|Geist|Onest|Instrument Sans|Bricolage Grotesque|Schibsted Grotesk|Hanken Grotesk|Albert Sans|Urbanist|Epilogue|Syne|Unbounded")
_WEIGHT = r"(?:Thin|Hairline|Extra ?Light|Ultra ?Light|Light|Regular|Roman|Book|Medium|Semi ?[Bb]old|Demi(?: ?[Bb]old)?|Bold|Extra ?[Bb]old|Ultra ?[Bb]old|Black|Heavy|Italic|Oblique|Condensed|Kursiv|Fett|Mager|Normal)"
RX_KNOWN_FONT = re.compile(r"(?<![\w-])(" + KNOWN_FONTS + r")(?![\w-])")
RX_FONT_WEIGHT = re.compile(r"\b((?:[A-Z][A-Za-z0-9]+|[A-Z]{2,})(?: (?:[A-Z][A-Za-z0-9]+|[A-Z]{2,})){0,2}) " + _WEIGHT + r"\b")
_NOT_A_FONT = re.compile(r"^(The|A|In|For|And|Headline|Headlines|Subline|Text|Body|Copy|Font|Fonts|Schrift|Schriftart|Schriften|Typeface|Title|Titel|Flie[sß]+text|"
                         r"Use|Weight|Weights|Schnitt|Schnitte|Style|Styles|Our|Unsere|Die|Der|Das|Is|Set|Always|Never|Display|Web|Print|Size)\b", re.I)

def fonts_in_text(text):
    c = Counter()
    for m in RX_KNOWN_FONT.finditer(text): c[(m.group(1), "known family")] += 1
    for m in RX_FONT_WEIGHT.finditer(text):
        fam = m.group(1)
        if not _NOT_A_FONT.match(fam) and not RX_KNOWN_FONT.fullmatch(fam): c[(fam, "followed by a weight name, verify")] += 1
    return [{"family": f, "mentions": n, "why": why} for (f, why), n in c.most_common(30)]

# ================================================================ PDF

def _pdf_libs():
    try:
        import pypdfium2, pypdf
        return pypdfium2, pypdf
    except ImportError as e:
        raise RuntimeError(f"PDF reading needs two packages ({e.name} is missing). Install them into the VibeUpSlides Python:  {sys.executable} -m {PDF_PIP}")

def _pdf_page_text(page):
    tp = page.get_textpage()
    try: return (tp.get_text_bounded() if hasattr(tp, "get_text_bounded") else tp.get_text_range()).replace("\r\n", "\n").replace("\r", "\n").replace("\ufffe", "").replace("\x02", "")
    finally: tp.close()

def _flat_colours(img, floor=0.015):
    """Colours that cover a flat share of a page: swatches, backgrounds, bars (photos fall below the floor)."""
    Image = _pil()[0]
    s = img.convert("RGB").resize((160, max(1, round(160 * img.height / img.width))), Image.NEAREST)
    total = s.width * s.height
    return {"#%02x%02x%02x" % c: n / total for n, c in (s.getcolors(total) or []) if n / total >= floor}

def render_pdf(pdf_path, out, single=None, labels=None, sheets=True):
    """Contact sheets of all pages and single pages (`single`: 1-based numbers, None for all) of a PDF.
    Returns (sheet paths, {page: path}, flat colours seen, page sizes in points)."""
    pdfium, _ = _pdf_libs()
    pdf = pdfium.PdfDocument(pdf_path); n = len(pdf)
    sizes = [pdf[i].get_size() for i in range(n)]
    labels = labels or [f"p{i + 1}" for i in range(n)]
    pages, seen, cache = {}, {}, {}
    def thumb(i, w):
        page = pdf[i]; pw, ph = sizes[i]
        if single is None or i + 1 in single:
            big = page.render(scale=PAGE_LONG_SIDE / max(pw, ph)).to_pil().convert("RGB")
            p = os.path.join(out, "pages", f"p{i + 1:03d}.jpg"); os.makedirs(os.path.dirname(p), exist_ok=True)
            big.save(p, quality=88); pages[i + 1] = p
            Image = _pil()[0]; img = big.resize((w, max(1, round(w * ph / pw))), Image.LANCZOS)
        else:
            img = page.render(scale=w / pw).to_pil().convert("RGB")
        for c, share in _flat_colours(img).items():
            e = seen.setdefault(c, {"pages": [], "share": 0}); e["pages"].append(i + 1); e["share"] = max(e["share"], round(share, 3))
        return img
    landscape = statistics.median(w / h for w, h in sizes) > 1.05
    if sheets: sheet_paths = contact_sheets(thumb, n, labels, os.path.join(out, "sheets"), landscape)
    else:
        sheet_paths = []
        for i in range(n):
            if single is None or i + 1 in single: thumb(i, 480)
    pdf.close()
    return sheet_paths, pages, seen, sizes

def _pdf_fonts_and_runs(pdf_path, notes):
    """pypdf side: fonts with embedding state, text runs with font size (for headings), outline, metadata, images."""
    _, pypdf = _pdf_libs()
    r = pypdf.PdfReader(pdf_path)
    if r.is_encrypted:
        try: r.decrypt("")
        except Exception: notes.append("the PDF is encrypted; fonts and embedded images could not be read")
    fonts, runs = {}, []
    def note_font(fd):
        try:
            base = str(fd.get("/BaseFont", "")).lstrip("/")
            if not base: return None
            name = re.sub(r"^[A-Z]{6}\+", "", base)
            if name not in fonts:
                desc = fd.get("/FontDescriptor")
                if desc is None and fd.get("/DescendantFonts"): desc = fd["/DescendantFonts"][0].get_object().get("/FontDescriptor")
                desc = desc.get_object() if desc is not None else {}
                fam = re.split(r"[-,]", name)[0]; fam = re.sub(r"(?<=[a-z])(?=[A-Z])", " ", fam).replace("MT", "").strip() if " " not in fam else fam
                fonts[name] = {"name": name, "family": fam, "type": str(fd.get("/Subtype", "")).lstrip("/"), "subset": base != name,
                               "embedded": any(k in desc for k in ("/FontFile", "/FontFile2", "/FontFile3")), "chars": 0}
            return name
        except Exception:
            return None
    for i, page in enumerate(r.pages):
        try:
            res = page.get("/Resources") or {}
            for f in (res.get_object().get("/Font") or {}).values(): note_font(f.get_object())
        except Exception: pass
        def visit(text, cm, tm, fd, size, i=i):
            if not text or not text.strip(): return
            try: eff = abs(size) * (abs(tm[0] * tm[3] - tm[1] * tm[2]) ** 0.5) * (abs(cm[0] * cm[3] - cm[1] * cm[2]) ** 0.5)
            except Exception: eff = abs(size or 0)
            name = note_font(fd) if fd else None
            if name: fonts[name]["chars"] += len(text.strip())
            runs.append((i + 1, round(eff * 2) / 2, name, text))
        try: page.extract_text(visitor_text=visit)
        except Exception as e: notes.append(f"page {i + 1}: font sizes could not be read ({type(e).__name__})")
    outline = []
    def walk(items, depth=0):
        for it in items:
            if isinstance(it, list): walk(it, depth + 1)
            else:
                try: outline.append({"level": depth + 1, "title": str(it.title), "page": r.get_destination_page_number(it) + 1})
                except Exception: pass
    try: walk(r.outline)
    except Exception: pass
    meta = {}
    try: meta = {k.lstrip("/"): str(v) for k, v in (r.metadata or {}).items() if str(v).strip()}
    except Exception: pass
    return r, fonts, runs, outline, meta

def _headings(runs):
    """Lines set clearly larger than the body size. Returns (headings, body size, sizes by share of text)."""
    by_size = Counter()
    for _, size, _, text in runs: by_size[size] += len(text.strip())
    if not by_size: return [], None, []
    body = by_size.most_common(1)[0][0]; total = sum(by_size.values())
    segs = []
    for page, size, font, text in runs:
        if segs and segs[-1][0] == page and segs[-1][1] == size and not segs[-1][3].endswith("\n"): segs[-1][3] += text
        else: segs.append([page, size, font, text])
    heads = []
    for page, size, font, text in segs:
        for line in text.splitlines():
            line = re.sub(r"\s+", " ", line).strip()
            if size >= body * 1.2 and 2 < len(line) <= 140 and re.search(r"[^\W\d_]{2}", line):
                if heads and heads[-1]["page"] == page and heads[-1]["size_pt"] == size and len(heads[-1]["text"]) + len(line) < 140 and heads[-1].pop("_open", False):
                    heads[-1]["text"] += " " + line
                else: heads.append({"page": page, "text": line, "size_pt": size, "font": font})
    sizes = sorted({h["size_pt"] for h in heads}, reverse=True)
    for h in heads: h["level"] = min(sizes.index(h["size_pt"]) + 1, 4); h.pop("_open", None)
    return heads, body, [{"size_pt": s, "share": round(n / total, 3)} for s, n in by_size.most_common(8)]

def _pdf_images(reader, out, notes, min_side=80, limit=150):
    """Embedded raster images that are pictures or logos. Vector artwork is not an image in a PDF and stays on the page render."""
    Image = _pil()[0]; saved, seen, skipped = [], set(), 0
    folder = os.path.join(out, "images")
    for i, page in enumerate(reader.pages):
        try: imgs = list(page.images)
        except Exception as e:
            notes.append(f"page {i + 1}: embedded images could not be read ({type(e).__name__})"); continue
        for im in imgs:
            try:
                data = im.data; h = hashlib.md5(data).hexdigest()
                if h in seen: continue
                seen.add(h)
                pil = im.image if getattr(im, "image", None) is not None else Image.open(io.BytesIO(data))
                w, hh = pil.size
                if min(w, hh) < min_side or w * hh < 160 * 160: skipped += 1; continue
                if len(saved) >= limit: skipped += 1; continue
                ext = os.path.splitext(im.name)[1].lower() or ".png"
                if ext not in (".png", ".jpg", ".jpeg"): ext = ".png"; buf = io.BytesIO(); pil.convert("RGBA" if pil.mode in ("RGBA", "LA", "P") else "RGB").save(buf, "PNG"); data = buf.getvalue()
                os.makedirs(folder, exist_ok=True)
                p = os.path.join(folder, f"p{i + 1:03d}_{len(saved) + 1:02d}{ext}"); open(p, "wb").write(data)
                saved.append({"file": _rel(p, out), "page": i + 1, "width": w, "height": hh, "alpha": pil.mode in ("RGBA", "LA")})
            except Exception:
                skipped += 1
    if saved and Image:
        def thumb(k, w):
            try: im = Image.open(os.path.join(out, saved[k]["file"])).convert("RGBA")
            except Exception: return Image.new("RGB", (w, 120), "#ccc")
            im.thumbnail((w, 360)); bg = Image.new("RGB", (w, max(im.height, 60)), "#f6f6f6" if not _mostly_light(im) else "#555")
            bg.paste(im, ((w - im.width) // 2, 0), im); return bg
        contact_sheets(thumb, len(saved), [f"{s['file'].split('/')[-1]}  {s['width']}x{s['height']}" for s in saved], folder, True, "sheet")
    return saved, skipped

def _mostly_light(im):
    """True for artwork that is light on transparent (a white logo), so the sheet shows it on a dark cell."""
    try:
        s = im.convert("RGBA").resize((40, 40)); px = [p for p in s.getdata() if p[3] > 60]
        return bool(px) and len(px) < 1500 and sum(1 for p in px if min(p[:3]) > 215) / len(px) > 0.8
    except Exception: return False

def ingest_pdf(path, out, name=None):
    notes = []
    pdfium, _ = _pdf_libs()
    pdf = pdfium.PdfDocument(path); n = len(pdf)
    texts = [_pdf_page_text(pdf[i]) for i in range(n)]
    pdf.close()
    reader, fonts, runs, outline, meta = _pdf_fonts_and_runs(path, notes)
    heads, body_size, size_shares = _headings(runs)
    head_set = {}
    for h in heads: head_set.setdefault((h["page"], re.sub(r"\s+", " ", h["text"]).strip()), h["level"])
    colours, per_page = [], []
    for i, t in enumerate(texts):
        cs = colours_in_text(t, i + 1); colours += cs
        first = next((h["text"] for h in heads if h["page"] == i + 1), None) or next((l.strip() for l in t.splitlines() if len(l.strip()) > 2), "")
        per_page.append({"page": i + 1, "title": first[:90], "chars": len(t.strip()), "colour_values": len(cs),
                         "key": bool(cs) or bool(KEY_PAGES.search(first)) or any(KEY_PAGES.search(h["text"]) for h in heads if h["page"] == i + 1)})
    if n <= ALL_PAGES_UP_TO: single = None
    else:
        single = {p["page"] for p in per_page if p["key"]} | {1}
        if len(single) > ALL_PAGES_UP_TO: single = set(sorted(single)[:ALL_PAGES_UP_TO])
        notes.append(f"{n} pages: only the {len(single)} pages that name colours or carry a design heading were saved as single images; "
                     f"render others with `ingest.py pages <brand_dir> {name or slug(path)} <numbers>`")
    sheets, pages, seen, sizes = render_pdf(path, out, single)
    md = [f"# {os.path.basename(path)}: text per page\n"]
    for i, t in enumerate(texts):
        lines = []
        for line in t.splitlines():
            s = re.sub(r"\s+", " ", line).strip(); lvl = head_set.get((i + 1, s))
            lines.append(("#" * (lvl + 1) + " " + s) if lvl else line.rstrip())
        body = re.sub(r"\n{3,}", "\n\n", "\n".join(lines)).strip() or "_(no text on this page: read the page image)_"
        _write(os.path.join(out, "text", f"p{i + 1:03d}.md"), f"# Page {i + 1}\n\n{body}\n")
        md.append(f"\n## Page {i + 1}\n\n{body}\n")
    _write(os.path.join(out, "text.md"), "".join(md))
    if sum(len(t.strip()) for t in texts) < 40 * n:
        notes.append("little or no text layer (scanned or outlined type): colours, fonts and headings below are incomplete, read the page images")
    images, skipped = _pdf_images(reader, out, notes)
    if not images: notes.append("no raster pictures embedded: logos and graphics in this PDF are vector artwork, crop them from the page images or ask for the logo files")
    size_count = Counter((round(w), round(h)) for w, h in sizes).most_common()
    def fmt(w, h):
        mm = (round(w / 72 * 25.4), round(h / 72 * 25.4))
        known = {(210, 297): "A4 portrait", (297, 210): "A4 landscape", (216, 279): "US Letter portrait", (279, 216): "US Letter landscape", (420, 297): "A3 landscape", (297, 420): "A3 portrait"}
        ratio = w / h
        kind = known.get(mm) or ("16:9" if abs(ratio - 16 / 9) < .02 else "4:3" if abs(ratio - 4 / 3) < .02 else "16:10" if abs(ratio - 1.6) < .02 else f"ratio {ratio:.2f}")
        return {"width_pt": w, "height_pt": h, "width_mm": mm[0], "height_mm": mm[1], "format": kind}
    flat = sorted(({"hex": c, **v, "pages": v["pages"][:12], "page_count": len(v["pages"])} for c, v in seen.items()),
                  key=lambda x: -(x["page_count"] * x["share"]))[:24]
    all_text = "\n".join(texts)
    f = {"kind": "pdf", "file": os.path.basename(path), "source": os.path.abspath(path), "pages": n, "metadata": meta,
         "page_sizes": [dict(fmt(w, h), pages=c) for (w, h), c in size_count],
         "colours_named": colours, "colours_flat": flat,
         "fonts_embedded": sorted(fonts.values(), key=lambda x: -x["chars"]), "fonts_mentioned": fonts_in_text(all_text),
         "type_sizes": {"body_pt": body_size, "by_share": size_shares},
         "headings": heads[:400], "outline": outline[:200], "page_index": per_page, "images": images, "images_skipped_small": skipped,
         "sheets": [_rel(p, out) for p in sheets], "single_pages": sorted(pages), "notes": notes}
    json.dump(f, open(os.path.join(out, "findings.json"), "w", encoding="utf-8"), indent=1, ensure_ascii=False)
    _write(os.path.join(out, "findings.md"), _pdf_findings_md(f))
    return f

def _pdf_findings_md(f):
    L = [f"# Findings: {f['file']}\n", f"PDF, {f['pages']} pages, " + "; ".join(f"{s['format']} {s['width_mm']} x {s['height_mm']} mm ({s['pages']} p.)" for s in f["page_sizes"][:3]) + ".",
         "Measured by a script: values are exact, labels and groupings are guesses. Check every colour against the page image before using it.\n"]
    for n in f["notes"]: L.append(f"- NOTE: {n}")
    L.append("\n## Colours named in the text\n")
    if f["colours_named"]:
        L.append("| Page | Label (line before the value) | HEX | RGB | CMYK | Pantone | RAL / HKS |\n|---|---|---|---|---|---|---|")
        for c in f["colours_named"]:
            L.append(f"| {c['page']} | {c['label'] or '(none) ' + c.get('context', '')[:50]} | {c.get('hex') or ('(' + c['hex_from_rgb'] + ' from RGB)' if c.get('hex_from_rgb') else '')} | {c.get('rgb', '')} | "
                     f"{c.get('cmyk', '')} | {c.get('pantone', '')} | {' '.join(x for x in ('RAL ' + c['ral'] if c.get('ral') else '', 'HKS ' + c['hks'] if c.get('hks') else '', 'NCS ' + c['ncs'] if c.get('ncs') else '') if x)} |")
    else: L.append("None found in the text layer. Take colours from the flat colours below and from the page images.")
    L.append("\n## Flat colours seen on the pages\n\nAreas of one colour covering at least 1.5 % of a page (swatches, backgrounds, bars), from the rendering.\n")
    L.append("| HEX | On pages | Largest share of a page |\n|---|---|---|")
    for c in f["colours_flat"]:
        L.append(f"| {c['hex']} | {c['page_count']} ({', '.join(map(str, c['pages'][:8]))}{' ...' if c['page_count'] > 8 else ''}) | {c['share'] * 100:.0f} % |")
    L.append("\n## Typefaces\n\nFonts the PDF itself is set in (a style guide is usually set in the brand's typeface):\n")
    for x in f["fonts_embedded"][:20]:
        L.append(f"- {x['name']} (family {x['family']}, {x['type']}, {'embedded' if x['embedded'] else 'not embedded'}{', subset' if x['subset'] else ''}): {x['chars']} characters")
    if not f["fonts_embedded"]: L.append("- none readable")
    L.append("\nFont names found in the text (heuristic: a list of known families, and capitalised names followed by a weight):\n")
    for x in f["fonts_mentioned"][:20]: L.append(f"- {x['family']}: {x['mentions']}x ({x['why']})")
    if not f["fonts_mentioned"]: L.append("- none")
    ts = f["type_sizes"]
    if ts["body_pt"]: L.append(f"\nBody size of the document {ts['body_pt']} pt; sizes by share of text: " + ", ".join(f"{s['size_pt']} pt ({s['share'] * 100:.0f} %)" for s in ts["by_share"]) + ".")
    L.append("\n## Pages\n\n| Page | First heading or line | Colour values | Single image |\n|---|---|---|---|")
    for p in f["page_index"]:
        L.append(f"| {p['page']} | {p['title'].replace('|', '/')} | {p['colour_values'] or ''} | {'pages/p%03d.jpg' % p['page'] if p['page'] in f['single_pages'] else ''} |")
    if f["outline"]:
        L.append("\n## Bookmarks\n"); L += [f"{'  ' * (o['level'] - 1)}- {o['title']} (p. {o['page']})" for o in f["outline"]]
    L.append(f"\n## Embedded pictures\n\n{len(f['images'])} saved in `images/` (contact sheet `images/sheet_*.jpg`), {f['images_skipped_small']} small or repeated ones skipped.")
    return "\n".join(L) + "\n"

# ================================================================ PowerPoint (standard library only)

def _xml(z, name):
    """Parse a part with namespaces stripped: tags become local names, relationship attributes keep an `r:` prefix."""
    try: root = ET.fromstring(z.read(name))
    except KeyError: return None
    for e in root.iter():
        if "}" in e.tag: e.tag = e.tag.split("}", 1)[1]
        for k in [k for k in e.attrib if k[0] == "{"]:
            ns, local = k[1:].split("}", 1)
            e.attrib[("r:" + local) if "elationships" in ns else local] = e.attrib.pop(k)
    return root

def _rels(z, part):
    root = _xml(z, posixpath.join(posixpath.dirname(part), "_rels", posixpath.basename(part) + ".rels")); out = {}
    for r in (root if root is not None else []):
        t = r.get("Target", ""); ext = r.get("TargetMode") == "External"
        if not ext: t = t.lstrip("/") if t.startswith("/") else posixpath.normpath(posixpath.join(posixpath.dirname(part), t))
        out[r.get("Id")] = (r.get("Type", "").rsplit("/", 1)[-1], t, ext)
    return out

def _rel_of(rels, kind):
    return next((t for k, t, ext in rels.values() if k == kind and not ext), None)

def _mod(hex_, el):
    """Apply the common colour modifiers of DrawingML (lumMod, lumOff, tint, shade) to a hex value."""
    r, g, b = (int(hex_[i:i + 2], 16) / 255 for i in (1, 3, 5)); mods = []
    for m in el:
        v = int(m.get("val", "100000")) / 100000
        if m.tag in ("lumMod", "lumOff"):
            h, l, s = colorsys.rgb_to_hls(r, g, b); l = min(1, max(0, l * v if m.tag == "lumMod" else l + v)); r, g, b = colorsys.hls_to_rgb(h, l, s)
        elif m.tag == "tint": r, g, b = (c + (1 - c) * (1 - v) for c in (r, g, b))
        elif m.tag == "shade": r, g, b = (c * v for c in (r, g, b))
        elif m.tag != "alpha": continue
        mods.append(f"{m.tag} {round(v * 100)}%")
    return "#%02x%02x%02x" % tuple(round(min(1, max(0, c)) * 255) for c in (r, g, b)), mods

def _colour(parent, ctx):
    """Colour of a fill-like element (solidFill, a gradient stop, a font reference): {'hex', 'ref'} or None."""
    if parent is None: return None
    for c in parent:
        if c.tag == "srgbClr": h, ref = "#" + c.get("val", "000000").lower(), None
        elif c.tag == "sysClr": h, ref = "#" + c.get("lastClr", "000000").lower(), None
        elif c.tag == "schemeClr":
            ref = c.get("val"); key = ctx["map"].get(ref, ref); h = ctx["theme"]["colours"].get(key)
            if not h: return {"hex": None, "ref": ref}
        elif c.tag == "prstClr": h, ref = {"black": "#000000", "white": "#ffffff"}.get(c.get("val"), None), c.get("val")
        else: continue
        if h is None: return {"hex": None, "ref": ref}
        h, mods = _mod(h, c)
        out = {"hex": h}
        if ref: out["ref"] = ref + (" " + " ".join(mods) if mods else "")
        return out
    return None

def _fill(spPr, style, ctx):
    if spPr is not None:
        for c in spPr:
            if c.tag == "noFill": return None
            if c.tag == "solidFill": return _colour(c, ctx)
            if c.tag == "gradFill":
                gs = c.find("gsLst/gs"); col = _colour(gs, ctx) if gs is not None else None
                if col: col["gradient"] = True
                return col
            if c.tag in ("blipFill", "pattFill", "grpFill"): return None
    ref = style.find("fillRef") if style is not None else None
    return _colour(ref, ctx) if ref is not None and ref.get("idx", "0") != "0" else None

def _rpr(rPr, ctx):
    if rPr is None: return {}
    o = {}
    if rPr.get("sz"): o["sz"] = int(rPr.get("sz")) / 100
    for k, a in (("b", "b"), ("i", "i")):
        if rPr.get(a) is not None: o[k] = rPr.get(a) in ("1", "true")
    if rPr.get("cap") and rPr.get("cap") != "none": o["caps"] = rPr.get("cap")
    col = _colour(rPr.find("solidFill"), ctx)
    if col: o["colour"] = col
    lat = rPr.find("latin")
    if lat is not None and lat.get("typeface"):
        tf = lat.get("typeface"); o["font"] = ctx["theme"]["fonts"].get("major" if tf.startswith("+mj") else "minor", tf) if tf.startswith("+") else tf
    return o

def _levels(lst, ctx, k=1.0):
    """Text style levels (lvl1pPr ... or defPPr) of a list style: size, weight, colour, font, alignment, bullet, spacing."""
    out = {}
    for lv in (lst if lst is not None else []):
        m = re.match(r"lvl(\d)pPr", lv.tag)
        if not m: continue
        o = _rpr(lv.find("defRPr"), ctx)
        if "sz" in o: o["size_pt"] = o.pop("sz"); o["size_px"] = round(o["size_pt"] * 12700 * k)
        if lv.get("algn"): o["align"] = lv.get("algn")
        if lv.get("marL"): o["indent_px"] = round(int(lv.get("marL")) * k)
        bu = lv.find("buChar")
        if bu is not None: o["bullet"] = bu.get("char")
        elif lv.find("buNone") is not None: o["bullet"] = None
        elif lv.find("buAutoNum") is not None: o["bullet"] = "numbered"
        ls = lv.find("lnSpc/spcPct")
        if ls is not None: o["line_height"] = int(ls.get("val")) / 100000
        sb = lv.find("spcBef/spcPts")
        if sb is not None: o["space_before_pt"] = int(sb.get("val")) / 100
        if "colour" in o: o["colour"] = o["colour"].get("hex") or o["colour"].get("ref")
        if o: out[int(m.group(1))] = o
    return out

def _paras(tx, ctx):
    out = []
    for p in (tx.findall("p") if tx is not None else []):
        pPr = p.find("pPr"); parts, first, field = [], None, None
        for c in p:
            if c.tag in ("r", "fld"):
                t = c.find("t"); parts.append(t.text or "" if t is not None else "")
                if first is None: first = _rpr(c.find("rPr"), ctx)
                if c.tag == "fld": field = c.get("type")
            elif c.tag == "br": parts.append("\n")
        text = "".join(parts)
        if first is None: first = _rpr(p.find("endParaRPr"), ctx) if not text else {}
        o = {"text": text, "lvl": int(pPr.get("lvl", 0)) if pPr is not None else 0}
        if pPr is not None and pPr.get("algn"): o["align"] = pPr.get("algn")
        if pPr is not None and pPr.find("buNone") is not None: o["bullet"] = False
        if field: o["field"] = field
        o.update({k: v for k, v in first.items()})
        out.append(o)
    return out

def _shapes(tree, part, rels, z, ctx, tf=(1, 0, 1, 0)):
    """Flatten a shape tree into dicts with geometry in EMU (group transforms applied), text, fills and media."""
    out = []
    for el in tree:
        tag = el.tag
        if tag == "AlternateContent":
            ch = el.find("Choice"); fb = el.find("Fallback")
            inner = _shapes(ch, part, rels, z, ctx, tf) if ch is not None else []
            out += inner or (_shapes(fb, part, rels, z, ctx, tf) if fb is not None else []); continue
        if tag == "grpSp":
            x = el.find("grpSpPr/xfrm"); t2 = tf
            if x is not None and x.find("chExt") is not None and x.find("ext") is not None:
                o, e, co, ce = x.find("off"), x.find("ext"), x.find("chOff"), x.find("chExt")
                sx = int(e.get("cx")) / (int(ce.get("cx")) or 1) if int(ce.get("cx")) else 1; sy = int(e.get("cy")) / (int(ce.get("cy")) or 1) if int(ce.get("cy")) else 1
                gx, gy = int(o.get("x")) - int(co.get("x")) * sx, int(o.get("y")) - int(co.get("y")) * sy
                t2 = (tf[0] * sx, tf[0] * gx + tf[1], tf[2] * sy, tf[2] * gy + tf[3])
            out += _shapes(el, part, rels, z, ctx, t2); continue
        if tag not in ("sp", "pic", "graphicFrame", "cxnSp"): continue
        nv = next((c for c in el if c.tag.startswith("nv")), None)
        cNv = nv.find("cNvPr") if nv is not None else None
        ph = nv.find("nvPr/ph") if nv is not None else None
        s = {"kind": {"sp": "shape", "pic": "picture", "graphicFrame": "frame", "cxnSp": "line"}[tag], "name": cNv.get("name", "") if cNv is not None else ""}
        if cNv is not None and cNv.get("descr"): s["alt"] = cNv.get("descr")[:200]
        if cNv is not None and cNv.get("hidden") in ("1", "true"): s["hidden"] = True
        if ph is not None: s["ph"] = {"type": ph.get("type") or ("body" if ph.get("idx") else "obj"), "idx": ph.get("idx")}
        spPr = el.find("spPr")
        x = el.find("xfrm") if tag == "graphicFrame" else (spPr.find("xfrm") if spPr is not None else None)
        if x is not None and x.find("off") is not None and x.find("ext") is not None:
            o, e = x.find("off"), x.find("ext")
            s["box"] = [tf[0] * int(o.get("x")) + tf[1], tf[2] * int(o.get("y")) + tf[3], tf[0] * int(e.get("cx")), tf[2] * int(e.get("cy"))]
            if x.get("rot") and x.get("rot") != "0": s["rot"] = round(int(x.get("rot")) / 60000)
            if x.get("flipV") in ("1", "true"): s["flipV"] = True
        if tag == "pic" or (spPr is not None and spPr.find("blipFill") is not None):
            bf = el.find("blipFill") if tag == "pic" else spPr.find("blipFill")
            blip = bf.find("blip") if bf is not None else None
            if blip is not None:
                rid = blip.get("r:embed") or blip.get("r:link")
                svg = next((e.get("r:embed") for e in blip.iter("svgBlip")), None)
                if rid in rels and not rels[rid][2]: s["media"] = rels[rid][1]
                if svg in rels: s["svg"] = rels[svg][1]
                sr = bf.find("srcRect")
                if sr is not None: s["crop"] = [int(sr.get(k, 0)) / 100000 for k in "ltrb"]
            for v in el.iter("videoFile"): s["video"] = rels.get(v.get("r:link"), ("", v.get("r:link"), True))[1]
        if tag in ("sp", "cxnSp"):
            g = spPr.find("prstGeom") if spPr is not None else None
            if g is not None: s["geom"] = g.get("prst")
            elif spPr is not None and spPr.find("custGeom") is not None: s["geom"] = "custom"
            f = _fill(spPr, el.find("style"), ctx)
            if f and f.get("hex"): s["fill"] = f["hex"]; s["fill_ref"] = f.get("ref")
            ln = spPr.find("ln") if spPr is not None else None
            if ln is not None and ln.find("noFill") is None:
                lc = _colour(ln.find("solidFill"), ctx)
                if lc and lc.get("hex"): s["line"] = lc["hex"]; s["line_px_w"] = int(ln.get("w", 12700))
            elif ln is None and tag == "cxnSp":
                lc = _colour(el.find("style/lnRef"), ctx)
                if lc and lc.get("hex"): s["line"] = lc["hex"]
            tx = el.find("txBody")
            if tx is not None:
                ps = _paras(tx, ctx)
                if any(p["text"].strip() for p in ps) or ph is not None: s["paras"] = ps
                bp = tx.find("bodyPr")
                if bp is not None:
                    if bp.get("anchor"): s["anchor"] = bp.get("anchor")
                    if any(bp.get(a) for a in ("lIns", "tIns", "rIns", "bIns")): s["inset"] = [int(bp.get(a, d)) for a, d in (("lIns", 91440), ("tIns", 45720), ("rIns", 91440), ("bIns", 45720))]
                    na = bp.find("normAutofit")
                    if na is not None and na.get("fontScale"): s["font_scale"] = int(na.get("fontScale")) / 100000
                lv = _levels(tx.find("lstStyle"), ctx, ctx["k"])
                if lv: s["levels"] = lv
        if tag == "graphicFrame":
            gd = el.find("graphic/graphicData"); uri = gd.get("uri", "") if gd is not None else ""
            s["frame"] = "table" if uri.endswith("/table") else "chart" if "chart" in uri else "diagram" if "diagram" in uri else "object"
            if s["frame"] == "table":
                s["rows"] = [[" ".join(p["text"] for p in _paras(tc.find("txBody"), ctx)).strip() for tc in tr.findall("tc")] for tr in gd.iter("tr")]
                s["cols"] = [int(c.get("w", 0)) for c in gd.iter("gridCol")]; s["row_h"] = [int(tr.get("h", 0)) for tr in gd.iter("tr")]
                s["cells"] = [[{"paras": _paras(tc.find("txBody"), ctx), "fill": (_colour(tc.find("tcPr/solidFill"), ctx) or {}).get("hex") if tc.find("tcPr") is not None else None,
                                "span": int(tc.get("gridSpan", 1)), "merged": tc.get("hMerge") in ("1", "true") or tc.get("vMerge") in ("1", "true")} for tc in tr.findall("tc")] for tr in gd.iter("tr")]
            elif s["frame"] == "chart":
                c = gd.find("chart"); target = rels.get(c.get("r:id")) if c is not None else None
                root = _xml(z, target[1]) if target and not target[2] else None
                if root is not None:
                    s["chart"] = sorted({e.tag for e in root.iter() if e.tag.endswith("Chart") and e.tag not in ("chart", "plotVisOnly")})
                    s["chart_colours"] = [c for c, _ in Counter("#" + e.get("val").lower() for e in root.iter("srgbClr")).most_common(8)]
                    t = [e.text for e in root.findall("chart/title//t") if e.text]
                    if t: s["chart_title"] = " ".join(t)
            elif s["frame"] == "diagram":
                d = gd.find("relIds"); target = rels.get(d.get("r:dm")) if d is not None else None
                root = _xml(z, target[1]) if target and not target[2] else None
                if root is not None: s["diagram_text"] = [t for t in ("".join(x.text or "" for x in pt.iter("t")).strip() for pt in root.iter("pt")) if t][:40]
        out.append(s)
    return out

_ALIAS = {"ctrTitle": "title", "subTitle": "body", "obj": "body"}
def _match(ph, shapes, by_idx=True):
    cands = [s for s in shapes if s.get("ph")]
    if by_idx and ph.get("idx") is not None:
        for s in cands:
            if s["ph"].get("idx") == ph["idx"]: return s
    t = _ALIAS.get(ph["type"], ph["type"])
    for s in cands:
        if s["ph"]["type"] == ph["type"]: return s
    for s in cands:
        if _ALIAS.get(s["ph"]["type"], s["ph"]["type"]) == t and (ph.get("idx") is None or not by_idx or s["ph"].get("idx") is None or t == "title"): return s
    return None

def _background(cSld, ctx, rels):
    bg = cSld.find("bg") if cSld is not None else None
    if bg is None: return None
    pr = bg.find("bgPr")
    if pr is not None:
        if pr.find("solidFill") is not None: return _colour(pr.find("solidFill"), ctx)
        if pr.find("gradFill") is not None:
            c = _colour(pr.find("gradFill/gsLst/gs"), ctx)
            if c: c["gradient"] = True
            return c
        b = pr.find("blipFill/blip")
        if b is not None and b.get("r:embed") in rels: return {"hex": None, "media": rels[b.get("r:embed")][1]}
    return _colour(bg.find("bgRef"), ctx)

def _theme(z, part):
    root = _xml(z, part) if part else None
    t = {"name": "", "scheme": "", "colours": {}, "custom": [], "fonts": {"major": None, "minor": None}, "font_scheme": ""}
    if root is None: return t
    t["name"] = root.get("name", "")
    cs = root.find("themeElements/clrScheme")
    if cs is not None:
        t["scheme"] = cs.get("name", "")
        for c in cs:
            v = c.find("srgbClr"); s = c.find("sysClr")
            t["colours"][c.tag] = "#" + (v.get("val") if v is not None else s.get("lastClr", "000000") if s is not None else "000000").lower()
    fs = root.find("themeElements/fontScheme")
    if fs is not None:
        t["font_scheme"] = fs.get("name", "")
        for k, tag in (("major", "majorFont"), ("minor", "minorFont")):
            lat = fs.find(tag + "/latin"); t["fonts"][k] = lat.get("typeface") if lat is not None else None
    for c in root.iter("custClr"):
        v = c.find("srgbClr")
        if v is not None: t["custom"].append({"name": c.get("name", ""), "hex": "#" + v.get("val").lower()})
    return t

def _px(box, k):
    return [round(v * k) for v in box] if box else None

def _text(s):
    return "\n".join(p["text"] for p in s.get("paras", [])).strip()

def read_pptx(path):
    """Everything the XML of a PowerPoint file says, as one dict. Geometry in a 1920-wide coordinate system."""
    z = zipfile.ZipFile(path); names = set(z.namelist())
    main = "ppt/presentation.xml"
    root_rels = _rels(z, "")                                                      # _rels/.rels names the main part
    main = _rel_of(root_rels, "officeDocument") or main
    pres = _xml(z, main)
    if pres is None: raise ValueError("not a PowerPoint file: no presentation part")
    prels = _rels(z, main)
    sz = pres.find("sldSz"); cx, cy = int(sz.get("cx")), int(sz.get("cy")); k = 1920 / cx
    D = {"kind": "pptx", "file": os.path.basename(path), "source": os.path.abspath(path),
         "slide_size": {"emu": [cx, cy], "inches": [round(cx / 914400, 2), round(cy / 914400, 2)], "px": [1920, round(cy * k)],
                        "ratio": "16:9" if abs(cx / cy - 16 / 9) < .02 else "4:3" if abs(cx / cy - 4 / 3) < .02 else "16:10" if abs(cx / cy - 1.6) < .02 else f"{cx / cy:.2f}:1",
                        "pt_to_px": round(12700 * k, 3)},
         "embedded_fonts": [{"family": f.find("font").get("typeface"), "styles": [c.tag for c in f if c.tag != "font"]} for f in pres.findall("embeddedFontLst/embeddedFont") if f.find("font") is not None],
         "masters": [], "layouts": [], "slides": [], "notes": []}
    themes, masters, layouts = {}, {}, {}
    def ctx_for(theme, cmap): return {"theme": theme, "map": cmap, "k": k}
    def load_master(part):
        if part in masters: return masters[part]
        root = _xml(z, part); rels = _rels(z, part)
        tp = _rel_of(rels, "theme"); theme = themes.setdefault(tp, _theme(z, tp))
        cm = root.find("clrMap"); cmap = dict(cm.attrib) if cm is not None else {}
        ctx = ctx_for(theme, cmap)
        shapes = _shapes(root.find("cSld/spTree"), part, rels, z, ctx)
        tx = root.find("txStyles")
        styles = {n: _levels(tx.find(n), ctx, k) for n in ("titleStyle", "bodyStyle", "otherStyle")} if tx is not None else {}
        hf = root.find("hf")
        m = {"part": part, "name": (root.find("cSld").get("name") or theme["name"] or posixpath.basename(part)), "theme": theme, "ctx": ctx, "shapes": shapes, "styles": styles,
             "bg": _background(root.find("cSld"), ctx, rels), "layouts": [],
             "header_footer": {a: hf.get(a, "1") in ("1", "true") for a in ("sldNum", "hdr", "ftr", "dt")} if hf is not None else None}
        masters[part] = m; return m
    def load_layout(part):
        if part in layouts: return layouts[part]
        root = _xml(z, part); rels = _rels(z, part)
        m = load_master(_rel_of(rels, "slideMaster"))
        co = root.find("clrMapOvr/overrideClrMapping"); ctx = ctx_for(m["theme"], dict(co.attrib)) if co is not None else m["ctx"]
        shapes = _shapes(root.find("cSld/spTree"), part, rels, z, ctx)
        for s in shapes:
            if s.get("ph"):
                up = _match(s["ph"], m["shapes"], by_idx=False)
                if "box" not in s and up and up.get("box"): s["box"] = list(up["box"]); s["box_from"] = "master"
                s["up"] = up
        l = {"part": part, "name": root.find("cSld").get("name") or posixpath.basename(part), "type": root.get("type"), "master": m, "ctx": ctx, "shapes": shapes,
             "bg": _background(root.find("cSld"), ctx, rels), "show_master_shapes": root.get("showMasterSp", "1") not in ("0", "false"), "used_by": []}
        layouts[part] = l; m["layouts"].append(l); return l
    for mid in pres.findall("sldMasterIdLst/sldMasterId"):
        part = prels.get(mid.get("r:id"), (None, None, None))[1]
        if part in names:
            m = load_master(part)
            for kind, t, ext in _rels(z, part).values():
                if kind == "slideLayout" and t in names: load_layout(t)
    for n, sid in enumerate(pres.findall("sldIdLst/sldId"), 1):
        part = prels.get(sid.get("r:id"), (None, None, None))[1]
        if part not in names: continue
        root = _xml(z, part); rels = _rels(z, part)
        lp = _rel_of(rels, "slideLayout"); l = load_layout(lp) if lp in names else None
        ctx = l["ctx"] if l else ctx_for(_theme(z, None), {})
        co = root.find("clrMapOvr/overrideClrMapping")
        if co is not None and l: ctx = ctx_for(l["master"]["theme"], dict(co.attrib))
        shapes = _shapes(root.find("cSld/spTree"), part, rels, z, ctx)
        for s in shapes:
            if s.get("ph") and l:
                up = _match(s["ph"], l["shapes"])
                if "box" not in s and up and up.get("box"): s["box"] = list(up["box"]); s["box_from"] = "layout"
                s["up"] = up
        notes = ""
        np_ = _rel_of(rels, "notesSlide")
        if np_ in names:
            nroot = _xml(z, np_)
            ns = [s for s in _shapes(nroot.find("cSld/spTree"), np_, {}, z, ctx) if s.get("ph", {}).get("type") == "body"]
            notes = "\n".join(_text(s) for s in ns).strip()
        title = next((s for s in shapes if s.get("ph", {}).get("type") in ("title", "ctrTitle") and _text(s)), None)
        guess = False
        if title is None:
            texts = sorted((s for s in shapes if _text(s) and s.get("box") and s.get("ph", {}).get("type") not in ("sldNum", "ftr", "dt") and len(_text(s)) < 160), key=lambda s: (s["box"][1], s["box"][0]))
            title, guess = (texts[0] if texts else None), True
        tr = root.find("transition")
        if tr is None: tr = next(root.iter("transition"), None)
        sl = {"n": n, "part": part, "hidden": root.get("show") in ("0", "false"), "layout": l, "shapes": shapes, "title_shape": title, "title_guess": guess and title is not None,
              "notes": notes, "bg": _background(root.find("cSld"), ctx, rels), "ctx": ctx,
              "transition": next((c.tag for c in tr), "yes") if tr is not None else None, "animated": root.find("timing") is not None or any(True for _ in root.iter("timing"))}
        if l: l["used_by"].append(n)
        D["slides"].append(sl)
    D["_masters"], D["_layouts"], D["_k"], D["_zip"] = list(masters.values()), list(layouts.values()), k, z
    return D

def _ph_row(s, k, master_styles):
    t = s["ph"]["type"]; lv = (s.get("levels") or {}).get(1) or ((s.get("up") or {}).get("levels") or {}).get(1) or {}
    style = (master_styles.get("titleStyle") if _ALIAS.get(t, t) == "title" else master_styles.get("bodyStyle") if _ALIAS.get(t, t) in ("body", "pic", "tbl", "chart") else master_styles.get("otherStyle") or {}) or {}
    base = style.get(1, {})
    o = {"type": t, "idx": s["ph"].get("idx"), "name": s["name"], "box": _px(s.get("box"), k)}
    for key in ("size_pt", "size_px", "b", "caps", "colour", "font", "align"):
        v = lv.get(key, base.get(key) if key in ("size_pt", "size_px") and t not in ("pic", "chart", "tbl", "dgm", "media", "clipArt") else None)
        if v is not None: o[key] = v
    if s.get("anchor"): o["anchor"] = s["anchor"]
    if s.get("box_from"): o["geometry_from"] = s["box_from"]
    txt = _text(s)
    if txt: o["prompt"] = txt[:120]
    return o

def _decor(shapes, k):
    out = []
    for s in shapes:
        if s.get("ph") or s.get("hidden"): continue
        o = {"kind": s.get("frame") or s["kind"], "name": s["name"], "box": _px(s.get("box"), k)}
        for a, b in (("media", "media"), ("svg", "svg"), ("fill", "fill"), ("line", "line"), ("geom", "geom")):
            if s.get(a): o[b] = posixpath.basename(s[a]) if a in ("media", "svg") else s[a]
        if _text(s): o["text"] = _text(s)[:160]
        out.append(o)
    return out

# ---------------------------------------------------------------- drawing layouts and slides

PH_COLOUR = {"title": "#d6336c", "ctrTitle": "#d6336c", "subTitle": "#ae3ec9", "body": "#1c7ed6", "obj": "#1c7ed6", "pic": "#2f9e44", "chart": "#2f9e44", "tbl": "#2f9e44",
             "dgm": "#2f9e44", "media": "#2f9e44", "clipArt": "#2f9e44", "ftr": "#868e96", "dt": "#868e96", "sldNum": "#868e96", "hdr": "#868e96"}

class _Painter:
    """Draws shapes at a fixed scale. Not a renderer: one typeface, no effects, text sizes from the nearest style found."""
    def __init__(self, D, width=960):
        self.Image, self.ImageDraw, _ = _pil()
        self.D, self.z = D, D["_zip"]; self.k = D["_k"] * width / 1920; self.W = width; self.H = round(D["slide_size"]["emu"][1] * self.k); self.media = {}
    def canvas(self, bgs):
        col = "#ffffff"; img = None
        for bg in bgs:
            if bg and bg.get("hex"): col = bg["hex"]; img = None
            elif bg and bg.get("media"): img = bg["media"]
        im = self.Image.new("RGB", (self.W, self.H), col)
        if img:
            p = self.picture(img, self.W, self.H)
            if p: im.paste(p.convert("RGB"), (0, 0))
        return im
    def picture(self, part, w, h, crop=None):
        key = (part, w, h, tuple(crop or ()))
        if key not in self.media:
            try:
                im = self.Image.open(io.BytesIO(self.z.read(part))); im.load(); im = im.convert("RGBA")
                if crop and any(crop):
                    l, t, r, b = crop; im = im.crop((round(im.width * l), round(im.height * t), round(im.width * (1 - r)), round(im.height * (1 - b))))
                self.media[key] = im.resize((max(1, w), max(1, h)), self.Image.LANCZOS)
            except Exception:
                self.media[key] = None
        return self.media[key]
    def box(self, s):
        b = s.get("box")
        if not b: return None
        x, y, w, h = (v * self.k for v in b)
        if 45 < abs(s.get("rot", 0)) % 180 < 135: x, y, w, h = x + (w - h) / 2, y + (h - w) / 2, h, w       # a quarter turn swaps the sides
        return [round(x), round(y), round(x + max(w, 1)), round(y + max(h, 1))]
    def decor(self, im, s, bg_lum):
        d = self.ImageDraw.Draw(im, "RGBA"); r = self.box(s)
        if not r or s.get("hidden"): return
        x0, y0, x1, y1 = r
        if s.get("media"):
            p = self.picture(s["media"], x1 - x0, y1 - y0, s.get("crop"))
            if p: im.paste(p, (x0, y0), p)
            else:
                d.rectangle(r, fill=(190, 190, 196, 120), outline="#888"); d.line([x0, y0, x1, y1], fill="#888"); d.line([x0, y1, x1, y0], fill="#888")
                d.text((x0 + 4, y0 + 3), posixpath.basename(s.get("svg") or s["media"]), fill="#333", font=_font(11))
            return
        if s["kind"] == "line":
            d.line([x0, y1 if s.get("flipV") else y0, x1, y0 if s.get("flipV") else y1], fill=s.get("line") or "#888", width=max(1, round(s.get("line_px_w", 12700) * self.k))); return
        if s["kind"] == "frame" and s.get("cells") and sum(s.get("cols") or [0]) and s.get("box"):
            bx, by, bw, bh = s["box"]; fx = bw / sum(s["cols"]); hs = s["row_h"] if sum(s["row_h"]) else [1] * len(s["cells"]); fy = bh / sum(hs); cy = by
            for row, rh in zip(s["cells"], hs):
                cx = bx
                for i, c in enumerate(row):
                    cw = sum(s["cols"][i:i + c["span"]]) * fx if i < len(s["cols"]) else 0
                    if not c["merged"] and cw:
                        cell = {"box": [cx, cy, cw, rh * fy], "paras": c["paras"], "fill": c["fill"]}; cr = self.box(cell)
                        d.rectangle(cr, fill=c["fill"], outline=(140, 140, 150, 160))
                        dark = c["fill"] and _lum(_rgb(c["fill"])) < .5
                        self.text(im, cell, {1: 11}, "#ffffff" if dark else ("#111111" if c["fill"] or bg_lum > .5 else "#ffffff"))
                    cx += (s["cols"][i] * fx) if i < len(s["cols"]) else 0
                cy += rh * fy
            return
        if s["kind"] == "frame":
            d.rectangle(r, fill=(120, 140, 160, 40), outline="#567")
            lab = s["frame"] + (": " + ", ".join(s.get("chart", [])) if s.get("chart") else "") + (f" {len(s['rows'])} rows" if s.get("rows") else "")
            d.text((x0 + 6, y0 + 4), lab, fill="#234", font=_font(13)); return
        fill, line = s.get("fill"), s.get("line")
        if fill or line:
            g = s.get("geom") or "rect"; kw = {"fill": fill, "outline": line}
            try:
                if g == "ellipse": d.ellipse(r, **kw)
                elif "ound" in g: d.rounded_rectangle(r, radius=min(x1 - x0, y1 - y0) // 6, **kw)
                elif g in ("line", "straightConnector1"): d.line(r, fill=line or fill)
                else: d.rectangle(r, **kw)
            except Exception: pass
    def text(self, im, s, sizes, default_colour, scale=1.0):
        """Wrapped text of a shape inside its box. `sizes`: level -> pt."""
        r = self.box(s)
        if not r or not s.get("paras"): return
        d = self.ImageDraw.Draw(im); x0, y0, x1, y1 = r; chain = [s, s.get("up") or {}, (s.get("up") or {}).get("up") or {}]
        ins = next((c["inset"] for c in chain if c.get("inset")), [91440, 45720, 91440, 45720]); anchor = next((c["anchor"] for c in chain if c.get("anchor")), None)
        x0 += round(ins[0] * self.k); x1 -= round(ins[2] * self.k); y0 += round(ins[1] * self.k); y1 -= round(ins[3] * self.k); pad = 0
        dalign = next((c["levels"][1]["align"] for c in chain if (c.get("levels") or {}).get(1, {}).get("align")), None); width = max(20, x1 - x0)
        lines = []
        for p in s["paras"]:
            pt = (p.get("sz") or sizes.get(p["lvl"] + 1) or sizes.get(1) or 18) * (s.get("font_scale") or 1) * scale
            f = _font(max(6, pt * 12700 * self.k)); col = (p.get("colour") or {}).get("hex") or default_colour
            indent = p["lvl"] * round(f.size * 1.2)
            for raw in (p["text"].split("\n") if p["text"] else [""]):
                cur = ""
                for w in raw.split(" "):
                    if cur and f.getlength(cur + " " + w) > width - indent: lines.append((cur, f, col, indent, p.get("align"))); cur = w
                    else: cur = (cur + " " + w) if cur else w
                lines.append((cur, f, col, indent, p.get("align")))
        total = sum(round(l[1].size * 1.2) for l in lines)
        y = y0 + pad // 2
        if anchor == "ctr": y = y0 + max(0, (y1 - y0 - total) // 2)
        elif anchor == "b": y = max(y0, y1 - total)
        for t, f, col, indent, al in lines:
            x = x0 + pad + indent; al = al or dalign
            if al == "ctr": x = x0 + (x1 - x0 - f.getlength(t)) / 2
            elif al == "r": x = x1 - pad - f.getlength(t)
            if t: d.text((x, y), t, fill=col, font=f)
            y += round(f.size * 1.2)
    def layout(self, l):
        m = l["master"]; im = self.canvas([m["bg"], l["bg"]]); lum = _lum(im.getpixel((self.W // 2, self.H // 2)))
        for s in (m["shapes"] if l["show_master_shapes"] else []):
            if not s.get("ph"): self.decor(im, s, lum); self.text(im, s, {1: 12}, "#444")
        for s in l["shapes"]:
            if not s.get("ph"): self.decor(im, s, lum); self.text(im, s, {1: 12}, "#444" if lum > .5 else "#ddd")
        d = self.ImageDraw.Draw(im, "RGBA")
        for s in l["shapes"]:
            r = self.box(s)
            if not s.get("ph") or not r: continue
            c = PH_COLOUR.get(s["ph"]["type"], "#e8590c"); rgb = tuple(int(c[i:i + 2], 16) for i in (1, 3, 5))
            d.rectangle(r, fill=rgb + (26,), outline=rgb + (255,), width=2)
            row = _ph_row(s, self.D["_k"], m["styles"]); b = row["box"]
            lab = f"{row['type']}{' #' + row['idx'] if row.get('idx') else ''}  {b[0]},{b[1]}  {b[2]}x{b[3]}" + (f"  {row['size_pt']:g}pt" if row.get("size_pt") else "")
            f = _font(13); tw = f.getlength(lab) + 8
            ly = r[1] + 2 if r[3] - r[1] > 22 else max(0, r[1] - 18)
            lx = max(0, min(r[0] + 2, self.W - tw - 2))
            d.rectangle([lx, ly, lx + tw, ly + 17], fill=rgb + (235,)); d.text((lx + 4, ly + 1), lab, fill="#fff", font=f)
        return im
    def slide(self, sl):
        l = sl["layout"]; m = l["master"] if l else None
        im = self.canvas([m["bg"] if m else None, l["bg"] if l else None, sl["bg"]]); lum = _lum(im.getpixel((self.W // 2, self.H // 2)))
        if l:
            for s in (m["shapes"] if l["show_master_shapes"] else []) + l["shapes"]:
                if not s.get("ph"): self.decor(im, s, lum); self.text(im, s, {1: 12}, "#444" if lum > .5 else "#ddd")
        for s in sl["shapes"]:
            self.decor(im, s, lum)
            if not s.get("paras"): continue
            t = _ALIAS.get(s.get("ph", {}).get("type"), s.get("ph", {}).get("type")); styles = m["styles"] if m else {}
            st = styles.get("titleStyle") if t == "title" else styles.get("bodyStyle") if s.get("ph") and t not in ("sldNum", "ftr", "dt") else styles.get("otherStyle")
            sizes = {lv: v["size_pt"] for lv, v in (st or {}).items() if v.get("size_pt")}
            if not s.get("ph"): sizes = {1: 18}
            if t in ("sldNum", "ftr", "dt"): sizes = {1: 12}
            up = s.get("up")
            for src in (up.get("up") if up else None, up, s):
                for lv, v in ((src or {}).get("levels") or {}).items():
                    if v.get("size_pt"): sizes[lv] = v["size_pt"]
            col = next((v.get("colour") for v in ((s.get("levels") or {}).get(1), ((up or {}).get("levels") or {}).get(1), (st or {}).get(1)) if v and str(v.get("colour", "")).startswith("#")), None)
            if s.get("fill"): col = col if col and abs(_lum(_rgb(col)) - _lum(_rgb(s["fill"]))) > .3 else ("#ffffff" if _lum(_rgb(s["fill"])) < .5 else "#111111")
            elif not col or abs(_lum(_rgb(col)) - lum) < .25: col = "#111111" if lum > .5 else "#ffffff"
            self.text(im, s, sizes, col)
        return im

def _rgb(h): return tuple(int(h[i:i + 2], 16) for i in (1, 3, 5))
def _lum(rgb): return (0.2126 * rgb[0] + 0.7152 * rgb[1] + 0.0722 * rgb[2]) / 255

# ---------------------------------------------------------------- PowerPoint: write the source folder

HTML_EXT = {".html", ".htm"}
_HTML_JS = """()=>{
  const sels=['#deck > .slide:not(.off)','.reveal .slides > section','section.slide','.slide','main > section','body > section'];
  let best=[]; for(const s of sels){ const l=[...document.querySelectorAll(s)]; if(l.length>best.length&&l.length>=3){ best=l; break; } }
  const shown=e=>{ const c=getComputedStyle(e), r=e.getBoundingClientRect(); return c.display!=='none'&&c.visibility!=='hidden'&&parseFloat(c.opacity)>0.5&&r.width>200&&r.height>100&&r.top<innerHeight&&r.bottom>0&&r.left<innerWidth&&r.right>0; };
  const cur=best.filter(shown).sort((a,b)=>(b.classList.contains('active')||b.classList.contains('present'))-(a.classList.contains('active')||a.classList.contains('present')))[0];
  const clean=e=>{ if(!e) return ''; const off=[...e.querySelectorAll('aside.notes,.notes,.footer,.header,.fuss,.kopf')].map(x=>[x,x.style.display]); off.forEach(o=>o[0].style.display='none');
    const t=(e.innerText||'').replace(/[ \\t]+\\n/g,'\\n').replace(/\\n{3,}/g,'\\n\\n').trim(); off.forEach(o=>o[0].style.display=o[1]); return t; };
  return {slides:best.length, hash:/^#\\/\\d+/.test(location.hash)||!!window.vsGo, text:clean(cur), height:document.documentElement.scrollHeight};
}"""

def ingest_html(path, out, name=None):
    """A presentation or page that exists as HTML: every slide is photographed in a browser and read like the
    pages of a PDF (sheets, single pages, colours by area), its words are taken from the slides themselves.
    A deck is paged with its own keys; a plain web page is cut into screens."""
    try: from playwright.sync_api import sync_playwright
    except ImportError: raise RuntimeError("HTML files are read with a browser (Playwright), which is not installed here. Export the presentation as PDF and pass that file.")
    P = _pil()
    if not P: raise RuntimeError("HTML files need Pillow to be read. Export the presentation as PDF and pass that file.")
    Image = P[0]; shots, texts, kind = [], [], "page"
    with sync_playwright() as pw:
        br = pw.chromium.launch(); pg = br.new_page(viewport={"width": 1920, "height": 1080})
        web = bool(re.match(r"https?://", str(path)))
        pg.goto(path if web else "file://" + os.path.abspath(path) + "?export=1", wait_until="load" if web else "domcontentloaded", timeout=45000); pg.wait_for_timeout(2500)      # a VibeUpSlides deck stands still and shows all its click steps
        pg.add_style_tag(content="#ui,#hint,#about,#toast,#loader,#ctl,.controls,.progress{display:none!important} *{animation-duration:0s!important;transition-duration:0s!important} .f,.fragment{opacity:1!important;visibility:visible!important;transform:none!important}")
        info = pg.evaluate(_HTML_JS)
        if info["slides"] >= 3:
            kind = "deck"; last = None; same = 0
            for i in range(1, min(info["slides"], 160) + 1):
                if info["hash"]: pg.evaluate(f"location.hash='#/{i}'")
                elif i > 1: pg.keyboard.press("ArrowRight")
                pg.wait_for_timeout(450); png = pg.screenshot()
                if png == last:
                    same += 1
                    if same >= 2: break                     # the deck does not move on: its end, or keys that do not page it
                    continue
                same = 0; last = png; shots.append(png); texts.append(pg.evaluate(_HTML_JS)["text"])
        else:
            pg.set_viewport_size({"width": 1440, "height": 900}); pg.wait_for_timeout(400)
            full = Image.open(io.BytesIO(pg.screenshot(full_page=True))).convert("RGB"); body = pg.evaluate("document.body.innerText")
            for y in range(0, min(full.height, 900 * 30), 900):
                b = io.BytesIO(); full.crop((0, y, full.width, min(y + 900, full.height))).save(b, "PNG"); shots.append(b.getvalue())
            texts = [body] + [""] * (len(shots) - 1)
        br.close()
    if not shots: raise RuntimeError("nothing could be photographed in this HTML file. Export the presentation as PDF and pass that file.")
    tmp = tempfile.mkdtemp(prefix="vibeupslides_html_"); pdf = os.path.join(tmp, "slides.pdf")
    try:
        ims = [Image.open(io.BytesIO(s)).convert("RGB") for s in shots]
        ims[0].save(pdf, "PDF", save_all=True, append_images=ims[1:], resolution=144)
        f = ingest_pdf(pdf, out, name)
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    md = [f"# {os.path.basename(path)}: text per {'slide' if kind == 'deck' else 'screen'}\n"]
    for i, t in enumerate(texts):
        body = t.strip() or "_(no text taken from this one: read the page image)_"
        _write(os.path.join(out, "text", f"p{i + 1:03d}.md"), f"# Page {i + 1}\n\n{body}\n"); md.append(f"\n## Page {i + 1}\n\n{body}\n")
    _write(os.path.join(out, "text.md"), "".join(md))
    f["file"] = os.path.basename(path) or path; f["source"] = path if re.match(r"https?://", str(path)) else os.path.abspath(path)
    shutil.rmtree(os.path.join(out, "images"), ignore_errors=True); f["images"] = []; f["images_skipped_small"] = 0      # the only pictures in that PDF were the photographs of the slides
    f["notes"] = [n for n in f.get("notes") or [] if "text layer" not in n and "raster pictures" not in n]
    f["notes"].insert(0, (f"an HTML presentation: {len(shots)} slides were photographed at 1920 x 1080 in the language it opens in, with their click steps shown"
                          if kind == "deck" else f"a web page, cut into {len(shots)} screens of 1440 x 900") + ". Typefaces and type sizes are not measured: read them from the page images.")
    for i, t in enumerate(texts):
        if i < len(f.get("page_index") or []):
            first = next((l.strip() for l in t.splitlines() if len(l.strip()) > 2), ""); f["page_index"][i]["title"] = first[:90]; f["page_index"][i]["chars"] = len(t.strip())
    json.dump(f, open(os.path.join(out, "findings.json"), "w", encoding="utf-8"), indent=1, ensure_ascii=False)
    _write(os.path.join(out, "findings.md"), _pdf_findings_md(f))
    return f

def ingest_pptx(path, out, soffice="auto"):
    D = read_pptx(path); z, k = D["_zip"], D["_k"]; notes = D["notes"]
    slides, layouts, masters = D["slides"], D["_layouts"], D["_masters"]
    # media: copy pictures, list large audio and video; remember where each file is used
    uses = {}
    def use(shapes, where, bg=None):
        for s in shapes:
            for key in ("media", "svg"):
                if s.get(key): uses.setdefault(s[key], []).append(where)
        if bg and bg.get("media"): uses.setdefault(bg["media"], []).append(where + " background")
    for m in masters: use(m["shapes"], "master", m["bg"])
    for l in layouts: use(l["shapes"], f"layout '{l['name']}'", l["bg"])
    for s in slides: use(s["shapes"], f"slide {s['n']}", s["bg"])
    media, mdir = [], os.path.join(out, "media"); Image = (_pil() or [None])[0]
    for info in z.infolist():
        if not re.match(r"ppt/(media|embeddings)/", info.filename) or info.is_dir(): continue
        base = posixpath.basename(info.filename); ext = os.path.splitext(base)[1].lower()
        kind = ("image" if ext in (".png", ".jpg", ".jpeg", ".gif", ".bmp", ".tif", ".tiff", ".webp") else "vector" if ext in (".svg", ".emf", ".wmf") else
                "video" if ext in (".mp4", ".mov", ".m4v", ".avi", ".wmv", ".webm") else "audio" if ext in (".mp3", ".wav", ".m4a", ".wma") else "other")
        if kind == "other": continue
        u = uses.get(info.filename, [])
        e = {"file": base, "kind": kind, "bytes": info.file_size, "used": sorted(set(u), key=u.index)[:12], "use_count": len(u)}
        if kind in ("video", "audio") and info.file_size > BIG_MEDIA: e["copied"] = False
        else:
            os.makedirs(mdir, exist_ok=True); data = z.read(info.filename); open(os.path.join(mdir, base), "wb").write(data); e["copied"] = True
            if kind == "image" and Image:
                try: im = Image.open(io.BytesIO(data)); e["width"], e["height"] = im.size; e["alpha"] = im.mode in ("RGBA", "LA", "P") and "transparency" in im.info or im.mode in ("RGBA", "LA")
                except Exception: pass
        on_template = [x for x in u if x.startswith(("master", "layout"))]
        slide_uses = len({x for x in u if x.startswith("slide")})
        if kind in ("image", "vector") and (on_template or (len(slides) >= 6 and slide_uses >= max(3, 0.3 * len(slides)))): e["logo_candidate"] = True
        media.append(e)
    linked_videos = sorted({s["video"] for sl in slides for s in sl["shapes"] if s.get("video")})
    # counts over the slides: typefaces, colours, sizes, words
    fonts, cols, sizes, words, charts = Counter(), Counter(), Counter(), [], Counter()
    for sl in slides:
        w = 0
        for s in sl["shapes"]:
            for p in s.get("paras", []):
                n = len(p["text"].strip())
                if s.get("ph", {}).get("type") not in ("sldNum", "ftr", "dt"): w += len(p["text"].split())
                if not n: continue
                if p.get("font"): fonts[p["font"]] += n
                if p.get("sz"): sizes[p["sz"]] += n
                if (p.get("colour") or {}).get("hex"): cols[(p["colour"]["hex"], "text")] += 1
            if s.get("fill"): cols[(s["fill"], "fill")] += 1
            if s.get("line"): cols[(s["line"], "line")] += 1
            for c in s.get("chart", []): charts[c] += 1
            for r in s.get("rows", []): w += sum(len(c.split()) for c in r)
        words.append(w)
    colour_use = {}
    for (h, role), n in cols.items(): colour_use.setdefault(h, {"hex": h, "count": 0, "as": {}}); colour_use[h]["count"] += n; colour_use[h]["as"][role] = n
    theme_by_hex = {}
    for m in masters:
        for name, h in m["theme"]["colours"].items(): theme_by_hex.setdefault(h, name)
    for c in colour_use.values():
        if c["hex"] in theme_by_hex: c["theme"] = theme_by_hex[c["hex"]]
    # footer and slide number conventions
    def conv(t):
        ms = [(m, s) for m in masters for s in m["shapes"] if s.get("ph", {}).get("type") == t]
        on = [sl for sl in slides if any(s.get("ph", {}).get("type") == t for s in sl["shapes"])]
        texts = Counter(_text(s) for sl in on for s in sl["shapes"] if s.get("ph", {}).get("type") == t and _text(s))
        lays = [l["name"] for l in layouts if any(s.get("ph", {}).get("type") == t for s in l["shapes"])]
        o = {"on_master": bool(ms), "layouts_with_it": len(lays), "slides_with_it": len(on)}
        if ms:
            m, s = ms[0]; row = _ph_row(s, k, m["styles"]); o.update({kk: row[kk] for kk in ("box", "size_pt", "colour", "align", "prompt") if kk in row})
        if texts: o["texts"] = [{"text": tx[:120], "slides": n} for tx, n in texts.most_common(3)]
        return o
    footer = {"slide_number": conv("sldNum"), "footer_text": conv("ftr"), "date": conv("dt")}
    F = {"kind": "pptx", "file": D["file"], "source": D["source"], "slides": len(slides), "hidden_slides": [s["n"] for s in slides if s["hidden"]], "slide_size": D["slide_size"],
         "themes": [{"master": m["name"], "theme": m["theme"]["name"], "colour_scheme": m["theme"]["scheme"], "colours": m["theme"]["colours"], "custom_colours": m["theme"]["custom"],
                     "font_scheme": m["theme"]["font_scheme"], "heading_font": m["theme"]["fonts"]["major"], "body_font": m["theme"]["fonts"]["minor"],
                     "background": (m["bg"] or {}).get("hex") or ((m["bg"] or {}).get("media") and "picture " + posixpath.basename(m["bg"]["media"]))} for m in masters],
         "masters": [{"name": m["name"], "text_styles": {"title": m["styles"].get("titleStyle", {}).get(1, {}), "body": m["styles"].get("bodyStyle", {}), "other": m["styles"].get("otherStyle", {}).get(1, {})},
                      "placeholders": [_ph_row(s, k, m["styles"]) for s in m["shapes"] if s.get("ph")], "fixed_elements": _decor(m["shapes"], k),
                      "header_footer": m["header_footer"], "layouts": [l["name"] for l in m["layouts"]]} for m in masters],
         "layouts": [{"name": l["name"], "type": l["type"], "master": l["master"]["name"], "used_by_slides": len(l["used_by"]), "slides": l["used_by"][:40],
                      "background": (l["bg"] or {}).get("hex") or ((l["bg"] or {}).get("media") and "picture " + posixpath.basename(l["bg"]["media"])),
                      "shows_master_elements": l["show_master_shapes"],
                      "placeholders": [_ph_row(s, k, l["master"]["styles"]) for s in l["shapes"] if s.get("ph")], "fixed_elements": _decor(l["shapes"], k)} for l in layouts],
         "footer": footer, "embedded_fonts": D["embedded_fonts"],
         "fonts_used": [{"family": f, "characters": n} for f, n in fonts.most_common(12)],
         "sizes_used_pt": [{"size": s, "characters": n} for s, n in sizes.most_common(10)],
         "colours_used": sorted(colour_use.values(), key=lambda c: -c["count"])[:24],
         "density": {"words_per_slide_median": statistics.median(words) if words else 0, "words_per_slide_max": max(words) if words else 0,
                     "slides_over_80_words": sum(1 for w in words if w > 80), "slides_with_notes": sum(1 for s in slides if s["notes"]),
                     "slides_with_pictures": sum(1 for s in slides if any(x.get("media") for x in s["shapes"])),
                     "tables": sum(1 for s in slides for x in s["shapes"] if x.get("frame") == "table"), "charts": dict(charts),
                     "diagrams": sum(1 for s in slides for x in s["shapes"] if x.get("frame") == "diagram"),
                     "animated_slides": sum(1 for s in slides if s["animated"]), "transitions": dict(Counter(s["transition"] for s in slides if s["transition"]))},
         "media": media, "linked_videos": linked_videos, "notes": notes}
    F["slide_list"] = []
    md = [f"# {D['file']}: slides in order\n"]
    for sl, w in zip(slides, words):
        title = _text(sl["title_shape"]).replace("\n", " ") if sl["title_shape"] else ""
        kinds = Counter(("picture" if s.get("media") else s.get("frame")) for s in sl["shapes"] if s.get("media") or s.get("frame"))
        F["slide_list"].append({"n": sl["n"], "hidden": sl["hidden"], "layout": sl["layout"]["name"] if sl["layout"] else None, "title": title[:160], "title_guessed": sl["title_guess"],
                                "words": w, "contains": dict(kinds), "notes": bool(sl["notes"])})
        md.append(f"\n## Slide {sl['n']}{' (HIDDEN)' if sl['hidden'] else ''}: {title or '(no title)'}\n\n- layout: {sl['layout']['name'] if sl['layout'] else '?'}"
                  + (" · title guessed from the topmost text" if sl["title_guess"] else "") + f" · {w} words"
                  + ("".join(f" · {n} {kk}{'s' if n > 1 else ''}" for kk, n in kinds.items())) + (f" · transition {sl['transition']}" if sl["transition"] else "") + (" · animated" if sl["animated"] else "") + "\n")
        body = sorted((s for s in sl["shapes"] if s is not sl["title_shape"] and s.get("ph", {}).get("type") not in ("sldNum", "ftr", "dt")), key=lambda s: ((s.get("box") or [0, 0])[1], (s.get("box") or [0, 0])[0]))
        for s in body:
            if s.get("paras") and _text(s):
                md.append("\n" + "\n".join(("  " * p["lvl"] + "- " + p["text"].replace("\n", " / ")) for p in s["paras"] if p["text"].strip()) + "\n")
            if s.get("rows"):
                md.append("\n" + "\n".join("| " + " | ".join(c.replace("\n", " ").replace("|", "/") for c in r) + " |" + ("\n|" + "---|" * len(r) if i == 0 else "") for i, r in enumerate(s["rows"])) + "\n")
            if s.get("chart"): md.append(f"\n[chart: {', '.join(s['chart'])}{' · ' + s['chart_title'] if s.get('chart_title') else ''}{' · colours ' + ' '.join(s['chart_colours']) if s.get('chart_colours') else ''}]\n")
            if s.get("diagram_text"): md.append("\n[diagram] " + " · ".join(s["diagram_text"]) + "\n")
            if s.get("media"): md.append(f"\n[picture: media/{posixpath.basename(s['media'])}{' · alt: ' + s['alt'] if s.get('alt') else ''}]\n")
        if sl["notes"]: md.append("\n**Speaker notes:**\n\n" + "\n".join("> " + x for x in sl["notes"].splitlines()) + "\n")
    _write(os.path.join(out, "slides.md"), "".join(md))
    # drawings: layouts always, slides as rendering (LibreOffice) or schematic
    F["layout_drawings"], F["layout_sheets"], F["sheets"], F["rendering"] = [], [], [], None
    labels = [f"{s['n']}{' HIDDEN' if s['hidden'] else ''}  {s['layout']['name'] if s['layout'] else ''}" for s in slides]
    if _pil():
        P = _Painter(D); ldir = os.path.join(out, "layouts"); os.makedirs(ldir, exist_ok=True); drawn = []
        order = sorted(layouts, key=lambda l: (-len(l["used_by"]), l["name"]))
        for i, l in enumerate(order, 1):
            im = P.layout(l); p = os.path.join(ldir, f"{i:02d}_{slug(l['name'])[:40]}.png"); im.save(p); drawn.append(im); F["layout_drawings"].append(_rel(p, out))
        if drawn:
            Image = P.Image
            F["layout_sheets"] = [_rel(p, out) for p in contact_sheets(lambda i, w: drawn[i].resize((w, round(w * drawn[i].height / drawn[i].width)), Image.LANCZOS), len(drawn),
                                  [f"{l['name']}  ({len(l['used_by'])} slides)" for l in order], ldir, True, "sheet")]
        imgs = [m for m in media if m["kind"] == "image" and m.get("copied")]
        if imgs:
            def mthumb(i, w):
                try: im = P.Image.open(os.path.join(mdir, imgs[i]["file"])).convert("RGBA")
                except Exception: return P.Image.new("RGB", (w, 120), "#ccc")
                im.thumbnail((w, 360)); bg = P.Image.new("RGB", (w, max(im.height, 60)), "#555" if _mostly_light(im) else "#f6f6f6"); bg.paste(im, ((w - im.width) // 2, 0), im); return bg
            contact_sheets(mthumb, len(imgs), [f"{m['file']} {m.get('width', '?')}x{m.get('height', '?')}{' LOGO?' if m.get('logo_candidate') else ''}" for m in imgs], mdir, True, "sheet")
    else:
        notes.append("Pillow is not installed: no drawings of the layouts and slides (pip install pillow)")
    exe = find_soffice() if soffice == "auto" else soffice
    if exe:
        try:
            pdf = office_to_pdf(path, out, exe)
            pdfium, _ = _pdf_libs()
            n_pages = len(pdfium.PdfDocument(pdf)); visible = [s for s in slides if not s["hidden"]]
            lab = labels if n_pages == len(slides) else [labels[s["n"] - 1] for s in visible] if n_pages == len(visible) else None
            if lab is None: notes.append(f"LibreOffice wrote {n_pages} pages for {len(slides)} slides: the sheets are numbered by page, not by slide")
            sheets, pages, seen, _ = render_pdf(pdf, out, None if n_pages <= 60 else set(), lab)
            F["sheets"] = [_rel(p, out) for p in sheets]; F["rendering"] = "libreoffice"; F["rendered_pdf"] = _rel(pdf, out)
            if n_pages == len(visible) != len(slides): notes.append("hidden slides are not in the rendering; their text is in slides.md")
        except Exception as e:
            notes.append(f"rendering through LibreOffice failed ({e}); slides are drawn schematically instead")
    if not F["rendering"] and _pil():
        P = _Painter(D, 640); cache = {}
        def sthumb(i, w):
            if i not in cache: cache.clear(); cache[i] = P.slide(slides[i])
            return cache[i]
        F["sheets"] = [_rel(p, out) for p in contact_sheets(sthumb, len(slides), labels, os.path.join(out, "sheets"), True, "schematic")]
        F["rendering"] = "schematic"
        notes.append("LibreOffice (soffice) was not found: the slide sheets are schematic drawings from the shapes (positions, pictures, fills and text are right; "
                     "typefaces, exact text sizes, effects, charts and diagrams are not). For true images install LibreOffice and ingest again, or ask the user to export the deck as PDF.")
    for d in (F,):
        json.dump(d, open(os.path.join(out, "findings.json"), "w", encoding="utf-8"), indent=1, ensure_ascii=False)
    _write(os.path.join(out, "findings.md"), _pptx_findings_md(F))
    z.close()
    return F

def _style_line(name, v):
    if not v: return None
    return (f"| {name} | {v.get('size_pt', '')} | {v.get('size_px', '')} | {'bold' if v.get('b') else 'regular' if 'b' in v else ''}{' italic' if v.get('i') else ''}{' caps' if v.get('caps') else ''} | "
            f"{v.get('colour', '')} | {v.get('font', '')} | {v.get('align', '')} | {repr(v['bullet']) if v.get('bullet') else ('none' if 'bullet' in v else '')} | {v.get('line_height', '')} |")

def _pptx_findings_md(F):
    ss = F["slide_size"]; d = F["density"]
    L = [f"# Findings: {F['file']}\n",
         f"PowerPoint, {F['slides']} slides ({len(F['hidden_slides'])} hidden{': ' + ', '.join(map(str, F['hidden_slides'])) if F['hidden_slides'] else ''}), slide size {ss['inches'][0]} x {ss['inches'][1]} in ({ss['ratio']}).",
         f"All positions and sizes below are in a {ss['px'][0]} x {ss['px'][1]} px coordinate system (x, y, width, height); 1 pt of type is {ss['pt_to_px']} px there.",
         f"Slide images: {'rendered by LibreOffice' if F['rendering'] == 'libreoffice' else 'SCHEMATIC drawings, not renderings' if F['rendering'] else 'none'} in `sheets/`. Layout drawings in `layouts/`. Slide texts in `slides.md`.\n"]
    for n in F["notes"]: L.append(f"- NOTE: {n}")
    for t in F["themes"]:
        L.append(f"\n## Theme: {t['theme'] or '(unnamed)'} (master '{t['master']}')\n")
        L.append(f"- Heading font: **{t['heading_font']}** · body font: **{t['body_font']}** (font scheme '{t['font_scheme']}')")
        L.append(f"- Colour scheme '{t['colour_scheme']}': " + ", ".join(f"{k} {v}" for k, v in t["colours"].items()))
        L.append("  (dk1/lt1: main text and background, dk2/lt2: second pair, accent1-6: the palette offered in the colour picker, in this order)")
        if t["custom_colours"]: L.append("- Custom colours: " + ", ".join(f"{c['name']} {c['hex']}" for c in t["custom_colours"]))
        if t["background"]: L.append(f"- Master background: {t['background']}")
    for m in F["masters"]:
        L.append(f"\n## Master '{m['name']}': text styles\n\n| Style | pt | px | Weight | Colour | Font | Align | Bullet | Line height |\n|---|---|---|---|---|---|---|---|---|")
        rows = [_style_line("title", m["text_styles"]["title"])] + [_style_line(f"body level {lv}", v) for lv, v in sorted(m["text_styles"]["body"].items()) if int(lv) <= 5] + [_style_line("other text", m["text_styles"]["other"])]
        L += [r for r in rows if r]
        L.append("\nEmpty cells inherit (from the theme font, the level above or PowerPoint's default).\n\nFixed elements on the master (on every slide unless a layout hides them):\n")
        L += [f"- {e['kind']} '{e['name']}' at {e['box']}" + "".join(f" · {kk} {e[kk]}" for kk in ("media", "svg", "fill", "line", "text") if e.get(kk)) for e in m["fixed_elements"]] or ["- none"]
    L.append("\n## Layouts (most used first)\n")
    for i, l in enumerate(sorted(F["layouts"], key=lambda l: (-l["used_by_slides"], l["name"])), 1):
        L.append(f"\n### {i:02d} {l['name']}  ({l['used_by_slides']} slides{', type ' + l['type'] if l['type'] else ''}{', background ' + str(l['background']) if l['background'] else ''}{', master elements hidden' if not l['shows_master_elements'] else ''})\n")
        for p in l["placeholders"]:
            L.append(f"- {p['type']}{' #' + str(p['idx']) if p.get('idx') else ''} '{p['name']}': {p['box']}" + (f" · {p['size_pt']:g} pt" if p.get("size_pt") else "")
                     + "".join(f" · {kk} {p[kk]}" for kk in ("colour", "font", "align", "anchor") if p.get(kk)) + (" · bold" if p.get("b") else "") + (f" · prompt: {p['prompt']!r}" if p.get("prompt") else ""))
        for e in l["fixed_elements"]:
            L.append(f"- fixed {e['kind']} '{e['name']}': {e['box']}" + "".join(f" · {kk} {e[kk]}" for kk in ("media", "svg", "fill", "line", "text") if e.get(kk)))
    L.append("\n## Footer, date and slide number\n")
    for name, key in (("Slide number", "slide_number"), ("Footer text", "footer_text"), ("Date", "date")):
        c = F["footer"][key]
        L.append(f"- {name}: " + (f"on the master at {c.get('box')}" + (f", {c['size_pt']:g} pt" if c.get("size_pt") else "") + (f", {c['colour']}" if c.get("colour") else "") + (f", aligned {c['align']}" if c.get("align") else "") if c["on_master"] else "not on the master")
                 + f"; in {c['layouts_with_it']} layouts, on {c['slides_with_it']} of {F['slides']} slides" + ("; text: " + "; ".join(f"{t['text']!r} ({t['slides']}x)" for t in c["texts"]) if c.get("texts") else ""))
    L.append("\n## What the slides actually use\n")
    L.append("- Typefaces set directly on text (beyond the theme fonts): " + (", ".join(f"{f['family']} ({f['characters']} chars)" for f in F["fonts_used"]) or "none, everything follows the theme"))
    L.append("- Type sizes set directly: " + (", ".join(f"{s['size']:g} pt ({s['characters']})" for s in F["sizes_used_pt"]) or "none"))
    L.append("- Colours set on shapes and text (count of uses): " + (", ".join(f"{c['hex']}{' =' + c['theme'] if c.get('theme') else ''} ({c['count']})" for c in F["colours_used"]) or "none"))
    L.append(f"- Density: median {d['words_per_slide_median']:g} words per slide, maximum {d['words_per_slide_max']}, {d['slides_over_80_words']} slides above 80 words; "
             f"{d['slides_with_pictures']} slides with pictures, {d['tables']} tables, {sum(d['charts'].values())} charts{' (' + ', '.join(f'{kk} {v}' for kk, v in d['charts'].items()) + ')' if d['charts'] else ''}, "
             f"{d['diagrams']} diagrams; {d['slides_with_notes']} slides with speaker notes; {d['animated_slides']} animated; transitions: {d['transitions'] or 'none'}")
    L.append("- Embedded fonts: " + (", ".join(f"{f['family']} ({'/'.join(f['styles'])})" for f in F["embedded_fonts"]) + " (obfuscated inside the file, not extracted: ask the user for the font files)" if F["embedded_fonts"] else "none"))
    L.append(f"\n## Media ({len(F['media'])} files, copies in `media/`, contact sheet `media/sheet_*.jpg`)\n")
    cand = [m for m in F["media"] if m.get("logo_candidate")]
    if cand: L.append("Logo candidates (placed on the master or a layout, or repeated on many slides):\n"); L += [f"- media/{m['file']} {m.get('width', '')}x{m.get('height', '')} · {', '.join(m['used'][:4])}" for m in cand]; L.append("")
    L.append("| File | Kind | Size | Pixels | Used on |\n|---|---|---|---|---|")
    for m in F["media"]:
        L.append(f"| {m['file']}{'' if m['copied'] else ' (NOT COPIED, large)'} | {m['kind']} | {m['bytes'] // 1024} KB | {str(m.get('width', '')) + 'x' + str(m.get('height', '')) if m.get('width') else ''} | {', '.join(m['used'][:5])}{' ...' if m['use_count'] > 5 else ''} |")
    if F["linked_videos"]: L.append("\nLinked videos (outside the file): " + ", ".join(F["linked_videos"]))
    L.append("\n## Slides\n\n| # | Layout | Title | Words | Contains |\n|---|---|---|---|---|")
    for s in F["slide_list"]:
        L.append(f"| {s['n']}{' hidden' if s['hidden'] else ''} | {s['layout']} | {s['title'].replace('|', '/')[:80]}{' (guessed)' if s['title_guessed'] else ''} | {s['words']} | {', '.join(f'{v} {kk}' for kk, v in s['contains'].items())}{' notes' if s['notes'] else ''} |")
    return "\n".join(L) + "\n"

def office_to_pdf(path, out, exe):
    """Convert an office document to PDF with LibreOffice (own profile folder, so a running instance does not block)."""
    tmp = tempfile.mkdtemp(prefix="vs-ingest-")
    try:
        src = os.path.join(tmp, "source" + os.path.splitext(path)[1].lower()); shutil.copy(path, src)
        r = subprocess.run([exe, "--headless", "--norestore", f"-env:UserInstallation=file://{tmp}/profile".replace("\\", "/"), "--convert-to", "pdf", "--outdir", tmp, src],
                           stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=600)
        pdf = os.path.join(tmp, "source.pdf")
        if not os.path.exists(pdf): raise RuntimeError("no PDF written: " + (r.stderr or r.stdout).decode("utf-8", "replace").strip()[:200])
        dst = os.path.join(out, "rendered.pdf"); os.makedirs(out, exist_ok=True); shutil.move(pdf, dst)
        return dst
    finally:
        shutil.rmtree(tmp, ignore_errors=True)

# ================================================================ entry point

def _is_logo(path):
    name = os.path.basename(path).lower()
    if re.search(r"logo|signet|wordmark|wortmarke|bildmarke|brandmark|emblem|favicon", name): return True
    if re.search(r"screen|shot|bildschirm|guide|page|seite|slide|folie|scan", name): return False
    if name.endswith(".svg"): return True
    P = _pil()
    if P:
        try:
            im = P[0].open(path)
            return im.mode in ("RGBA", "LA") and max(im.size) <= 4000 and im.convert("RGBA").getextrema()[3][0] < 20
        except Exception: pass
    return False

def _copy_unique(src, folder):
    os.makedirs(folder, exist_ok=True); dst = os.path.join(folder, os.path.basename(src))
    if os.path.abspath(src) != os.path.abspath(dst): shutil.copy(src, dst)
    return dst

def ingest(brand_dir, paths, soffice="auto"):
    """Read documents into `<brand_dir>/sources/` and sort loose logos, images and fonts into the library.
    Returns a summary dict; `report(summary)` formats it for the terminal."""
    brand_dir = os.path.abspath(brand_dir); src_root = os.path.join(brand_dir, "sources"); os.makedirs(src_root, exist_ok=True)
    exe = find_soffice() if soffice == "auto" else soffice
    S = {"brand_dir": brand_dir, "documents": [], "sorted": [], "unreadable": [], "libreoffice": bool(exe), "pillow": bool(_pil()), "index": os.path.join(src_root, "SOURCES.md")}
    files = []
    for p in paths:
        if re.match(r"https?://", p):
            S["unreadable"].append({"file": p, "why": "a link, not a file. Google Slides: File > Download > PDF or PowerPoint; other online documents: export as PDF. Then pass the file."}); continue
        p = os.path.abspath(os.path.expanduser(p)); ext = os.path.splitext(p)[1].lower()
        if os.path.isdir(p) and ext != ".key":
            for root, dirs, fs in os.walk(p):
                dirs[:] = sorted(d for d in dirs if not d.startswith(".") and not d.lower().endswith(".key")); files += [os.path.join(root, f) for f in sorted(fs) if not f.startswith((".", "~$"))]
        elif not os.path.exists(p): S["unreadable"].append({"file": p, "why": "file not found"})
        else: files.append(p)
    used = set()
    for p in files:
        ext = os.path.splitext(p)[1].lower(); base = os.path.basename(p)
        try:
            if ext in FONT_EXT:
                S["sorted"].append({"file": base, "kind": "font", "to": _rel(_copy_unique(p, os.path.join(brand_dir, "fonts", "inbox")), brand_dir)})
            elif ext in IMG_EXT:
                logo = _is_logo(p); dst = _copy_unique(p, os.path.join(brand_dir, "logos") if logo else os.path.join(src_root, "images"))
                e = {"file": base, "kind": "logo" if logo else "image", "to": _rel(dst, brand_dir)}
                P = _pil()
                if P and ext != ".svg":
                    try: e["width"], e["height"] = P[0].open(p).size
                    except Exception: pass
                S["sorted"].append(e)
            elif ext in (".key", ".numbers", ".pages"):
                S["unreadable"].append({"file": base, "why": "Apple iWork files cannot be read. In Keynote: File > Export To > PDF (and PowerPoint, if the slide master matters), then pass those files."})
            elif ext in (".gslides", ".gdoc", ".gsheet"):
                S["unreadable"].append({"file": base, "why": "a Google Drive shortcut, not the document. In Google Slides: File > Download > PowerPoint (.pptx) or PDF, then pass that file."})
            elif ext == ".pdf" or ext in PPT_EXT or ext in OFFICE_EXT or ext in HTML_EXT:
                name = slug(base); i = 2
                while name in used: name = f"{slug(base)}-{i}"; i += 1
                used.add(name); out = os.path.join(src_root, name)
                if os.path.isdir(out): shutil.rmtree(out)
                os.makedirs(out)
                if ext in OFFICE_EXT:
                    if not exe:
                        shutil.rmtree(out); S["unreadable"].append({"file": base, "why": f"{ext} files are read through LibreOffice, which is not installed. Export the document as PDF (or save a .ppt as .pptx) and pass that file."}); continue
                    f = ingest_pdf(office_to_pdf(p, out, exe), out, name); f["file"] = base; f["source"] = p; f["notes"].append(f"converted from {ext} by LibreOffice; fonts and page breaks may differ from the original")
                    json.dump(f, open(os.path.join(out, "findings.json"), "w", encoding="utf-8"), indent=1, ensure_ascii=False)
                elif ext == ".pdf": f = ingest_pdf(p, out, name)
                elif ext in HTML_EXT: f = ingest_html(p, out, name)
                else: f = ingest_pptx(p, out, exe or None)
                doc = _doc_summary(f, name, out, brand_dir)
                json.dump(doc, open(os.path.join(out, "summary.json"), "w", encoding="utf-8"), indent=1, ensure_ascii=False)
                S["documents"].append(doc)
            else:
                S["unreadable"].append({"file": base, "why": f"{ext or 'this'} files are not read. Useful are: PDF, PowerPoint (.pptx, .potx), presentations as HTML, logos and images (.svg, .png, .jpg), font files (.woff2, .woff, .ttf, .otf)."})
        except RuntimeError as e:
            S["unreadable"].append({"file": base, "why": str(e)})
            if "out" in locals() and os.path.isdir(out) and not os.listdir(out): os.rmdir(out)
        except (zipfile.BadZipFile, ET.ParseError, ValueError, KeyError, OSError) as e:
            S["unreadable"].append({"file": base, "why": f"could not be read ({type(e).__name__}: {e}). Password-protected or damaged files have to be saved again without protection."})
    _write_index(src_root, S)
    return S

def _doc_summary(f, name, out, brand_dir):
    d = {"name": name, "file": f["file"], "source": f["source"], "kind": f["kind"], "folder": _rel(out, brand_dir), "ingested": time.strftime("%Y-%m-%d"), "notes": f["notes"],
         "sheets": [_rel(os.path.join(out, s), brand_dir) for s in f.get("sheets", [])]}
    if f["kind"] == "pdf":
        named = [c for c in f["colours_named"] if c.get("hex") or c.get("hex_from_rgb")]
        d.update({"pages": f["pages"], "format": f["page_sizes"][0]["format"] if f["page_sizes"] else "",
                  "colours": [f"{c.get('hex') or c['hex_from_rgb']}{' ' + c['label'] if c['label'] else ''}" for c in named][:16] or [c["hex"] for c in f["colours_flat"][:8]],
                  "colours_from": "named in the text" if named else "flat areas of the pages (nothing named in the text)",
                  "other_colour_systems": sorted({kk for c in f["colours_named"] for kk in ("cmyk", "pantone", "ral", "hks", "ncs") if c.get(kk)}),
                  "fonts": [x["family"] for x in f["fonts_mentioned"] if x["why"] == "known family"][:6], "fonts_embedded": sorted({x["family"] for x in f["fonts_embedded"]})[:8],
                  "headings": len(f["headings"]), "images": len(f["images"]), "single_pages": len(f["single_pages"]),
                  "key_pages": [p["page"] for p in f["page_index"] if p["key"]][:40]})
    else:
        t = f["themes"][0] if f["themes"] else {}
        d.update({"slides": f["slides"], "hidden": len(f["hidden_slides"]), "format": f["slide_size"]["ratio"], "rendering": f["rendering"],
                  "colours": [f"{v} {kk}" for kk, v in (t.get("colours") or {}).items()], "heading_font": t.get("heading_font"), "body_font": t.get("body_font"),
                  "fonts": [x["family"] for x in f["fonts_used"][:5]], "masters": len(f["masters"]),
                  "layouts": [{"name": l["name"], "slides": l["used_by_slides"]} for l in sorted(f["layouts"], key=lambda l: -l["used_by_slides"])],
                  "layout_sheets": [_rel(os.path.join(out, s), brand_dir) for s in f["layout_sheets"]],
                  "media": len(f["media"]), "logo_candidates": [m["file"] for m in f["media"] if m.get("logo_candidate")][:8],
                  "words_per_slide": f["density"]["words_per_slide_median"], "embedded_fonts": [x["family"] for x in f["embedded_fonts"]]})
    return d

def _write_index(src_root, S):
    """SOURCES.md over every document in sources/, including those of earlier runs."""
    docs = []
    for n in sorted(os.listdir(src_root)):
        p = os.path.join(src_root, n, "summary.json")
        if os.path.exists(p):
            try: docs.append(json.load(open(p, encoding="utf-8")))
            except Exception: pass
    L = ["# Sources of this brand\n", "Documents the user supplied, prepared for study. Paths are relative to the brand folder. Open the sheets as images first, then the findings.",
         "Numbers and hex values were measured by a script; labels, groupings and anything marked as a candidate are guesses to be checked against the images.",
         "These files are study material. They stay in this library and never go into a deck.\n"]
    for d in docs:
        f = d["folder"]
        if d["kind"] == "pdf":
            L.append(f"\n## {d['file']}\n\nPDF, {d['pages']} pages, {d['format']}. Read on {d['ingested']}.\n")
            L.append(f"- Look: `{f}/sheets/` ({len(d['sheets'])} contact sheets, pages in order), single pages in `{f}/pages/` ({d['single_pages']} pages)")
            L.append(f"- Read: `{f}/findings.md` (colours, typefaces, page index), `{f}/text.md` (all text, per page also in `{f}/text/`)")
            if d["key_pages"]: L.append(f"- Pages that name colours or carry a design heading: {', '.join(map(str, d['key_pages']))}")
            L.append(f"- Colours ({d['colours_from']}): {', '.join(d['colours']) or 'none'}" + (f"; also given as {', '.join(d['other_colour_systems'])}" if d["other_colour_systems"] else ""))
            L.append(f"- Typefaces named in the text: {', '.join(d['fonts']) or 'none recognised'}; the PDF is set in: {', '.join(d['fonts_embedded']) or 'unknown'}")
            L.append(f"- {d['headings']} headings found, {d['images']} embedded pictures in `{f}/images/`")
        else:
            L.append(f"\n## {d['file']}\n\nPowerPoint, {d['slides']} slides ({d['hidden']} hidden), {d['format']}, {d['masters']} master(s), {len(d['layouts'])} layouts. Read on {d['ingested']}.\n")
            L.append(f"- Look: `{f}/layouts/sheet_*.jpg` (every layout drawn from its placeholders), `{f}/sheets/` ({len(d['sheets'])} sheets of the slides, "
                     + ("rendered by LibreOffice" if d["rendering"] == "libreoffice" else "SCHEMATIC drawings: positions, pictures and text are right, typefaces and effects are not") + f"), `{f}/media/sheet_*.jpg`")
            L.append(f"- Read: `{f}/findings.md` (theme, master text styles, layouts with placeholder geometry, footer, media), `{f}/slides.md` (titles, text, notes per slide)")
            L.append(f"- Theme colours: {', '.join(d['colours']) or 'none'}")
            L.append(f"- Theme fonts: headings {d['heading_font']}, body {d['body_font']}" + (f"; set directly on slides: {', '.join(d['fonts'])}" if d["fonts"] else "") + (f"; embedded: {', '.join(d['embedded_fonts'])}" if d["embedded_fonts"] else ""))
            L.append("- Layouts by use: " + ", ".join(f"{l['name']} ({l['slides']})" for l in d["layouts"][:14]) + (f" and {len(d['layouts']) - 14} more" if len(d["layouts"]) > 14 else ""))
            L.append(f"- Median {d['words_per_slide']:g} words per slide; {d['media']} media files" + (f", logo candidates: {', '.join(d['logo_candidates'])}" if d["logo_candidates"] else ""))
        L += [f"- NOTE: {n}" for n in d["notes"]]
    loose = os.path.join(src_root, "images")
    if os.path.isdir(loose) and os.listdir(loose):
        L.append(f"\n## Loose images\n\n`sources/images/`: " + ", ".join(sorted(os.listdir(loose))) + " (screenshots or scans the user passed in; open them as images)")
    if S["sorted"]:
        L.append("\n## Sorted into the library in the last run\n"); L += [f"- {x['file']} ({x['kind']}) -> `{x['to']}`" for x in S["sorted"]]
    if S["unreadable"]:
        L.append("\n## Not read in the last run\n"); L += [f"- {x['file']}: {x['why']}" for x in S["unreadable"]]
    _write(os.path.join(src_root, "SOURCES.md"), "\n".join(L) + "\n")

def report(S):
    L = []
    for d in S["documents"]:
        if d["kind"] == "pdf": L.append(f"{d['file']}: PDF, {d['pages']} pages, {len(d['sheets'])} sheets, {d['single_pages']} single pages, {len(d['colours'])} colours ({d['colours_from']}), {d['images']} pictures -> {d['folder']}/")
        else: L.append(f"{d['file']}: PowerPoint, {d['slides']} slides ({d['hidden']} hidden), {len(d['layouts'])} layouts, {d['media']} media files, slides {d['rendering'] or 'not drawn'} -> {d['folder']}/")
        L += [f"  NOTE: {n}" for n in d["notes"]]
    L += [f"{x['file']}: {x['kind']} -> {x['to']}" for x in S["sorted"]]
    L += [f"NOT READ {x['file']}: {x['why']}" for x in S["unreadable"]]
    if any(x["kind"] == "font" for x in S["sorted"]): L.append("fonts wait in fonts/inbox/: confirm the licence with the user, then `vs.py fonts add <brand>`")
    if any(d["kind"] == "pptx" and d["rendering"] == "schematic" for d in S["documents"]): L.append("LibreOffice not found: PowerPoint slides are schematic drawings, not renderings")
    L.append(f"index: {S['index']}")
    return "\n".join(L)

def more_pages(brand_dir, name, numbers):
    """Render further single pages of a PDF source that was ingested before (long documents save only key pages)."""
    out = os.path.join(os.path.abspath(brand_dir), "sources", name); d = json.load(open(os.path.join(out, "summary.json"), encoding="utf-8"))
    pdf = os.path.join(out, "rendered.pdf") if os.path.exists(os.path.join(out, "rendered.pdf")) else d["source"]
    if not os.path.exists(pdf): raise FileNotFoundError(f"the original is no longer at {pdf}")
    return render_pdf(pdf, out, set(numbers), sheets=False)[1]

if __name__ == "__main__":
    a = sys.argv[1:]
    if len(a) >= 4 and a[0] == "pages":
        for n, p in sorted(more_pages(a[1], a[2], [int(x) for x in a[3].split(",")]).items()): print(p)
    elif len(a) >= 2:
        s = ingest(a[0], [x for x in a[1:] if x != "--no-soffice"], soffice=None if "--no-soffice" in a else "auto"); print(report(s))
    else:
        print(__doc__)
