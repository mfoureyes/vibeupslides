"""vibeupslides build script.

Combines master.html (engine and CSS), a brand profile and a slide file into one
self-contained HTML presentation: fonts, logos and images are embedded as data URIs,
so the deck runs offline in any browser. PDFs are rendered only on request.

Command line:
    python3 build.py slides.html out/Deck.html --brand acme [--title "Title"] [--lang en]
                     [--image NAME=path ...] [--pdf] [--check]

From a project's build script:
    import build as B
    B.build("slides.html", "out/Deck.html", brand="acme", title="Title", lang="en",
            images=dict(COVER="images/cover.jpg"))
    print(B.check("out/Deck.html", lang="en"))      # must be an empty list

A brand is a folder with brand.json in the library of the workspace. `brand` may be a path to
that folder or a name that is looked up in <workspace>/library. The workspace is $VIBEUPSLIDES_HOME,
else ~/vibeupslides. Next to brand.json a brand may have theme.css (its own styles on top of the
engine) and elements/ (SVG icons, arrows and shapes; theme.css refers to them as url(el:arrows/a.svg)).

Slide files hold one <section class="slide ..." lang="xx"> per slide. A deck in two languages
has every slide twice, first language first, same order. {{IMG_NAME}} in the slide file is
replaced by the image passed as images=dict(NAME=path).
"""
import base64, io, json, mimetypes, os, re, sys

HERE = os.path.dirname(os.path.abspath(__file__))
SKILL = os.path.dirname(HERE)

DEFAULT_BRAND = {
    "name": "Unbranded",
    "lang": "en",
    "colors": {
        "accent": "#2F5BEA", "on_accent": "#FFFFFF",
        "ink": "#1D1D1F", "deep": "#1D1D1F", "on_deep": "#FFFFFF",
        "muted": "#6B6F76", "line": "#C9CBCF", "soft": "#F2F3F5", "ghost": "#E8E9EC", "paper": "#FFFFFF",
    },
    "fonts": {
        "body": {"family": "Helvetica Neue", "fallback": "Arial, Helvetica, sans-serif"},
        "head": {"family": None},
        "files": [],
        "display_weight": 800, "head_weight": 700,
    },
    "shape": {"radius": 0, "motif": "wedge", "head_case": "none", "head_tracking": None, "logo_position": "right"},
    "logos": {"primary": None, "primary_inverse": None, "partner": None, "partner_inverse": None,
              "icon": None, "inverse_mode": "file"},
    "footer": {"left": "", "right": ""},
}


# ---------------------------------------------------------------- brand profile

def home():
    """The workspace: one local folder with framework/, library/ and decks/."""
    return os.environ.get("VIBEUPSLIDES_HOME") or os.path.join(os.path.expanduser("~"), "vibeupslides")

def library():
    return os.path.join(home(), "library")

def brand_dir(brand):
    """Resolve a brand name or path to its folder."""
    if brand is None:
        return None
    if os.path.isdir(brand) and os.path.exists(os.path.join(brand, "brand.json")):
        return os.path.abspath(brand)
    d = os.path.join(library(), brand)
    if os.path.exists(os.path.join(d, "brand.json")):
        return d
    raise FileNotFoundError(f"Brand '{brand}' not found in {library()}. Saved brands: "
                            f"{', '.join(os.path.basename(x) for x in list_brands()) or 'none'}.")

def _merge(base, over):
    out = dict(base)
    for k, v in (over or {}).items():
        out[k] = _merge(base[k], v) if isinstance(v, dict) and isinstance(base.get(k), dict) else v
    return out

def load_brand(brand):
    """Return the brand profile as a dict, filled up with defaults. '_dir' holds the brand folder."""
    d = brand_dir(brand)
    data = json.load(open(os.path.join(d, "brand.json"), encoding="utf-8")) if d else {}
    b = _merge(DEFAULT_BRAND, data)
    b["_dir"] = d
    return b

def list_brands():
    root = library()
    if not os.path.isdir(root):
        return []
    return [os.path.join(root, n) for n in sorted(os.listdir(root)) if os.path.exists(os.path.join(root, n, "brand.json"))]

def _hex_rgb(h):
    h = h.strip().lstrip("#")
    if len(h) == 3:
        h = "".join(c * 2 for c in h)
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))

def luminance(h):
    def lin(c):
        c /= 255
        return c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4
    r, g, b = (lin(c) for c in _hex_rgb(h))
    return 0.2126 * r + 0.7152 * g + 0.0722 * b

def contrast(a, b):
    la, lb = sorted((luminance(a), luminance(b)), reverse=True)
    return (la + 0.05) / (lb + 0.05)

def readable_on(bg, light="#FFFFFF", dark="#1D1D1F"):
    """White or near-black, whichever reads better on bg."""
    return light if contrast(bg, light) >= contrast(bg, dark) else dark

def brand_warnings(b):
    """Contrast problems that would make slides hard to read."""
    c, out = b["colors"], []
    pairs = [("ink", "paper", 7), ("muted", "paper", 3), ("on_accent", "accent", 3), ("on_deep", "deep", 7)]
    for fg, bg, need in pairs:
        r = contrast(c[fg], c[bg])
        if r < need:
            out.append(f"{fg} {c[fg]} on {bg} {c[bg]} has contrast {r:.1f}, wanted at least {need}")
    if contrast(c["accent"], c["paper"]) < 3 and not c.get("accent_text"):
        out.append(f"accent {c['accent']} is too light for text on paper: titles and labels use a darkened shade "
                   f"({accent_as_text(c['accent'], c['paper'], c['ink'])}). Set colors.accent_text to a brand colour that reads on paper if there is one")
    aod = c.get("accent_on_deep")                           # the accent as text on dark ground: dark slides and the dark scheme (key D)
    if aod and contrast(aod, c["deep"]) < 4.5:
        out.append(f"accent_on_deep {aod} on deep {c['deep']} has contrast {contrast(aod, c['deep']):.1f}, wanted at least 4.5: take a lighter tone of the brand "
                   f"(computed: {accent_as_text(c['accent'], c['deep'], c['on_deep'], need=4.5)}) or remove it")
    return out

def _mix(a, b, t):
    return "#" + "".join(f"{round(x + (y - x) * t):02X}" for x, y in zip(_hex_rgb(a), _hex_rgb(b)))

def accent_as_text(accent, ground, toward, need=3.0):
    """The accent colour, shifted towards `toward` until it reads as text on `ground`."""
    c = accent
    for step in range(1, 10):
        if contrast(c, ground) >= need:
            break
        c = _mix(accent, toward, step / 10)
    return c

def tokens_css(b):
    """CSS custom properties for the brand, placed after the engine defaults."""
    import motion                       # motion tokens of the brand profile: --m-ease, --m-dur, --m-stagger, --m-travel, --m-change-x, --m-change-dur
    c, f, s = b["colors"], b["fonts"], b["shape"]
    fallback = f["body"].get("fallback") or "Arial, Helvetica, sans-serif"
    body = f"'{f['body']['family']}',{fallback}" if f["body"].get("family") else fallback
    head_family = (f.get("head") or {}).get("family")
    head = f"'{head_family}',{(f['head'].get('fallback') or fallback)}" if head_family else "var(--font)"
    radius = s.get("radius", 0)
    radius = f"{radius}px" if isinstance(radius, (int, float)) else radius
    rules = []          # heading case and tracking only when the brand sets them, the engine has tuned defaults
    if s.get("head_case") in ("uppercase", "lowercase"):
        rules.append(f"text-transform:{s['head_case']}")
    if s.get("head_tracking"):
        rules.append(f"letter-spacing:{s['head_tracking']}")
    head_rule = ("\nh1,h2,.chapter h2,.statement h2{" + ";".join(rules) + "}") if rules else ""
    credit_rule = "\n.accent .vs-credit{font-weight:700}" if contrast(c["on_accent"], c["accent"]) < 4.5 else ""   # small type on the accent: bold needs 3 to 1, not 4.5
    return (":root{"
            f"--accent:{c['accent']};--on-accent:{c['on_accent']};--ink:{c['ink']};--deep:{c['deep']};--on-deep:{c['on_deep']};"
            f"--accent-text:{c.get('accent_text') or accent_as_text(c['accent'], c['paper'], c['ink'])};"
            f"--accent-on-deep:{c.get('accent_on_deep') or accent_as_text(c['accent'], c['deep'], c['on_deep'], need=4.5)};"
            f"--muted:{c['muted']};--line:{c['line']};--soft:{c['soft']};--ghost:{c['ghost']};--paper:{c['paper']};"
            f"--font:{body};--font-head:{head};--w-display:{f.get('display_weight', 800)};--w-head:{f.get('head_weight', 700)};"
            f"--radius:{radius};"
            + motion.tokens_css(b) +
            "}" + head_rule + credit_rule)

_FONT_FORMATS = {".woff2": "woff2", ".woff": "woff", ".ttf": "truetype", ".otf": "opentype"}

def fonts_css(b):
    """@font-face rules with the font files embedded. A ready-made CSS file can be given as fonts.css."""
    d, f = b["_dir"], b["fonts"]
    parts = []
    if f.get("css") and d:
        parts.append(open(os.path.join(d, f["css"]), encoding="utf-8").read())
    for face in f.get("files") or []:
        p = os.path.join(d or "", face["file"])
        if not os.path.exists(p):
            print("WARNING: font file missing:", p)
            continue
        ext = os.path.splitext(p)[1].lower()
        data = base64.b64encode(open(p, "rb").read()).decode()
        mime = "font/" + ext[1:] if ext in (".woff", ".woff2", ".ttf", ".otf") else "application/octet-stream"
        rng = f"unicode-range:{face['unicode_range']};" if face.get("unicode_range") else ""
        parts.append("@font-face{font-family:'%s';font-weight:%s;font-style:%s;font-display:block;%s"
                     "src:url(data:%s;base64,%s) format('%s')}" % (
                         face["family"], face.get("weight", "400"), face.get("style", "normal"), rng,
                         mime, data, _FONT_FORMATS.get(ext, "woff2")))
    return "\n".join(parts)


# ---------------------------------------------------------------- embedding

def trim_edges(im, share=.02, tolerance=10):
    """Cut a thin plain edge off a photo: a line of one colour along a side (the white or black rim that
    exports and screenshots leave) shows as a border on any slide that is not of that colour. A side is only
    trimmed when the plain band ends within `share` of the image; a band that goes on is background and stays."""
    if im.width < 300 or im.height < 300:
        return im
    px = im.convert("RGB"); w, h = px.size
    def plain(box):
        ex = px.crop(box).getextrema()
        return all(hi - lo <= tolerance for lo, hi in ex)
    def band(side):
        limit = max(2, int((h if side in "tb" else w) * share)); n = 0
        while n <= limit:
            box = {"t": (0, n, w, n + 1), "b": (0, h - n - 1, w, h - n), "l": (n, 0, n + 1, h), "r": (w - n - 1, 0, w - n, h)}[side]
            if not plain(box): break
            n += 1
        return n if 0 < n <= limit else 0
    t, b, l, r = band("t"), band("b"), band("l"), band("r")
    return im.crop((l, t, im.width - r, im.height - b)) if (t or b or l or r) else im

def datauri(path, width=1600, q=82, trim=False):
    """Image file as data URI. Photos become JPEG, images with transparency stay PNG, SVG stays SVG.
    trim: the image is a picture on a slide; a thin plain edge is cut off (trim_edges). Logos are never trimmed."""
    if path.lower().endswith(".svg"):
        return "data:image/svg+xml;base64," + base64.b64encode(open(path, "rb").read()).decode()
    from PIL import Image, ImageOps
    im = Image.open(path); im = ImageOps.exif_transpose(im)
    if im.mode in ("RGBA", "LA", "P") and path.lower().endswith((".png", ".webp", ".gif")):
        im = im.convert("RGBA")
        if trim and im.getextrema()[3][0] == 255:          # no transparency at all: a photo saved as PNG
            im = trim_edges(im.convert("RGB"))
            if im.width > width:
                im = im.resize((width, round(im.height * width / im.width)), Image.LANCZOS)
            b = io.BytesIO(); im.save(b, "JPEG", quality=q, optimize=True)
            return "data:image/jpeg;base64," + base64.b64encode(b.getvalue()).decode()
        if im.width > width:
            im = im.resize((width, round(im.height * width / im.width)), Image.LANCZOS)
        b = io.BytesIO(); im.save(b, "PNG", optimize=True)
        return "data:image/png;base64," + base64.b64encode(b.getvalue()).decode()
    im = im.convert("RGB")
    if trim: im = trim_edges(im)
    if im.width > width:
        im = im.resize((width, round(im.height * width / im.width)), Image.LANCZOS)
    b = io.BytesIO(); im.save(b, "JPEG", quality=q, optimize=True)
    return "data:image/jpeg;base64," + base64.b64encode(b.getvalue()).decode()

def assets(b, footer_left=None, footer_right=None):
    """Everything the engine script needs at runtime: logos, footer texts, shape settings."""
    d, lg = b["_dir"] or "", b["logos"]
    a = {"name": b.get("name", ""), "motif": b["shape"].get("motif", "wedge"),
         "logo_position": b["shape"].get("logo_position", "right"),
         "inverse_mode": lg.get("inverse_mode", "file")}
    for key, width in (("primary", 800), ("primary_inverse", 800), ("partner", 660), ("partner_inverse", 660)):
        if lg.get(key):
            p = os.path.join(d, lg[key])
            if os.path.exists(p):
                a[key] = datauri(p, width)
            else:
                print("WARNING: logo missing:", p)
    a["footer_left"] = footer_left if footer_left is not None else b["footer"].get("left", "")
    a["footer_right"] = footer_right if footer_right is not None else b["footer"].get("right", "")
    return a

def theme_css(b):
    """The brand's own stylesheet (theme.css), with url(el:path) replaced by the embedded element."""
    d = b.get("_dir")
    p = os.path.join(d, "theme.css") if d else None
    if not p or not os.path.exists(p):
        return ""
    css = re.sub(r"/\*.*?\*/", "", open(p, encoding="utf-8").read(), flags=re.S)
    if not css.strip():
        return ""
    def embed(m):
        f = os.path.join(d, "elements", m.group(1).strip("\"' "))
        if not os.path.exists(f):
            print("WARNING: theme.css refers to a missing element:", m.group(1)); return "url()"
        return 'url("' + datauri(f) + '")'
    return "\n/* ---------- brand theme ---------- */\n" + re.sub(r"url\(\s*el:([^)]+)\)", embed, css)

def export_js():
    """Embed jsPDF and modern-screenshot from js/, so the PDF export (key P) works offline."""
    parts = []
    for name in ("jspdf.umd.min.js", "modern-screenshot.js"):
        p = os.path.join(HERE, "js", name)
        if os.path.exists(p):
            parts.append("<script>" + open(p, encoding="utf-8").read() + "</script>")
        else:
            print("WARNING: missing", p, "(the PDF export inside the deck will not work)")
    return "\n".join(parts)

def favicon(b):
    """Browser tab icon of the brand, embedded as data URI."""
    icon = b["logos"].get("icon")
    p = os.path.join(b["_dir"] or "", icon) if icon else None
    if not p or not os.path.exists(p):
        return ""
    if p.lower().endswith(".svg"):
        return f'<link rel="icon" type="image/svg+xml" href="{datauri(p)}">'
    from PIL import Image
    im = Image.open(p).convert("RGBA")
    out = []
    for size in (32, 192):
        buf = io.BytesIO(); im.resize((size, size), Image.LANCZOS).save(buf, "PNG")
        data = base64.b64encode(buf.getvalue()).decode()
        out.append(f'<link rel="icon" type="image/png" sizes="{size}x{size}" href="data:image/png;base64,{data}">')
        if size == 192:
            out.append(f'<link rel="apple-touch-icon" href="data:image/png;base64,{data}">')
    return "\n".join(out)

def slide_langs(slides):
    """Languages used in a slide file, in order of first appearance."""
    seen = []
    for l in re.findall(r'<section\b[^>]*\blang="([A-Za-z-]+)"', slides):
        if l not in seen:
            seen.append(l)
    return seen


# ---------------------------------------------------------------- build, PDF, check

def mode_assets(mode):
    """Styles and script of a deck mode: reading.css and reading.js for "reading", nothing for "live"."""
    out = []
    for ext in ("css", "js"):
        p = os.path.join(HERE, f"{mode}.{ext}") if re.fullmatch(r"[a-z]+", mode or "") and mode != "live" else ""
        out.append(open(p, encoding="utf-8").read() if p and os.path.exists(p) else "")
    return tuple(out)

def build(slides_path, out, brand=None, title=None, images=None, footer_left=None, footer_right=None,
          pdf=False, lang=None, slides_text=None, mode="live", mode_css="", mode_js="", scheme=None):
    """Write the finished deck to `out`. Returns the output path. slides_text: the slide markup as a
    string instead of a file (slides_path is then ignored). mode: "live" or "reading"; the styles and
    script of a mode come from <mode>.css and <mode>.js next to this file unless they are passed in."""
    if not mode_css and not mode_js:                       # every deck carries both versions; `mode` is the one it opens in
        mode_css, mode_js = mode_assets("reading")
    b = brand if isinstance(brand, dict) else load_brand(brand)
    for w in brand_warnings(b):
        print("WARNING (brand):", w)
    master = open(os.path.join(HERE, "master.html"), encoding="utf-8").read()
    slides = slides_text if slides_text is not None else open(slides_path, encoding="utf-8").read()
    for name, path in (images or {}).items():
        big = any(k in name for k in ("COVER", "FULL"))
        slides = slides.replace("{{IMG_" + name + "}}", datauri(path, 1920 if big else 1400, trim=True))
    left = re.findall(r"\{\{IMG_[A-Z0-9_]+\}\}", slides)
    if left:
        print("WARNING: image placeholders without a file:", sorted(set(left)))
    langs = slide_langs(slides)
    lang = lang or (langs[0] if langs else b.get("lang", "en"))
    title = title or b.get("name") or "Presentation"
    html = (master.replace("{{FONTS}}", fonts_css(b)).replace("{{TOKENS}}", tokens_css(b)).replace("{{THEME}}", theme_css(b))
                  .replace("{{SLIDES}}", slides).replace("{{EXPORT_JS}}", export_js())
                  .replace("{{FAVICON}}", favicon(b)).replace("{{TITLE}}", title)
                  .replace("{{ASSETS}}", json.dumps(assets(b, footer_left, footer_right)))
                  .replace("{{MOTIF}}", b["shape"].get("motif", "wedge"))
                  .replace("{{MODE}}", mode if mode in ("live", "reading") else "live")
                  .replace("{{SCHEME}}", "dark" if (scheme or b.get("scheme")) == "dark" else "light").replace("{{MODE_CSS}}", mode_css).replace("{{MODE_JS}}", mode_js)
                  .replace("{{LANG}}", lang))
    os.makedirs(os.path.dirname(os.path.abspath(out)), exist_ok=True)
    open(out, "w", encoding="utf-8").write(html)
    print(out, round(len(html) / 1024), "kB")
    if pdf:
        if len(langs) > 1:
            for l in langs:
                render_pdf(out, os.path.splitext(out)[0] + "_" + l.upper() + ".pdf", l)
        else:
            render_pdf(out, os.path.splitext(out)[0] + ".pdf", lang)
    return out

def render_pdf(html, pdf, lang=None):
    """Render the deck to a vector PDF with Chromium, one page per slide (1920 x 1080 px).
    ?export=1 switches the deck to export mode: no animation, all click steps visible,
    quiz questions revealed, no buttons."""
    from playwright.sync_api import sync_playwright
    with sync_playwright() as p:
        br = p.chromium.launch()
        pg = br.new_page(viewport={"width": 1920, "height": 1080})
        pg.goto("file://" + os.path.abspath(html) + "?export=1" + (f"&lang={lang}" if lang else ""))
        pg.wait_for_timeout(2500)
        pg.emulate_media(media="print")
        pg.pdf(path=pdf, width="1920px", height="1080px", print_background=True, prefer_css_page_size=True)
        br.close()
    print(pdf, round(os.path.getsize(pdf) / 1024), "kB")

_CHECK_JS = """(()=>{const page=document.querySelector('#deck > .slide.active');
  const s=page.querySelector(':scope > .rs > .slide')||page;      /* reading version: the reduced slide inside its page */
  const sr=s.getBoundingClientRect();const sc=sr.width/1920;
  const words=e=>e?((e.innerText||'').match(/[^\\s]*[\\p{L}\\p{N}][^\\s]*/gu)||[]).length:0;
  const rt=page.querySelector(':scope > .rt'), chrome=words(page.querySelector(':scope > .footer'))+words(page.querySelector(':scope > .rbar'));
  let maxB=0,maxR=0;
  const sel='.slide > *:not(.header):not(.footer):not(.rbar):not(.vs-credit):not(.wedge):not(.ghost):not(.image):not(.photo):not(.biglogo):not(.notes):not(.badge):not(canvas)';
  (s.querySelector('.text')?s.querySelectorAll('.text > *'):s.querySelectorAll(sel)).forEach(e=>{
    const r=e.getBoundingClientRect();maxB=Math.max(maxB,(r.bottom-sr.top)/sc);maxR=Math.max(maxR,(r.right-sr.left)/sc);});
  return {b:Math.round(maxB),r:Math.round(maxR),t:(s.querySelector('h1,h2')||{}).textContent||'',
          skip:s.classList.contains('no-footer'), low:s.classList.contains('fullbleed'),
          n:parseInt(page.getAttribute('data-n'),10)||0, read:words(rt), words:words(page)-chrome-words(rt),
          over:rt?Math.max(rt.scrollHeight-rt.clientHeight,rt.scrollWidth-rt.clientWidth):0, notes:!!(rt&&rt.hasAttribute('data-from'))}})()"""

_LEGIBLE_JS = """(()=>{const page=document.querySelector('#deck > .slide.active');
  const s=page.querySelector(':scope > .rs > .slide')||page;
  const sr=s.getBoundingClientRect(),sc=sr.width/1920,out=[],seen=new Map();
  const skip='.footer,.rbar,.notes,.rt,.ghost,.header,.qopts,[data-quiet],script,style,svg,canvas,video,iframe,[aria-hidden=true]';
  const probe=document.createElement('i');probe.style.color='var(--ghost)';s.appendChild(probe);const ghost=getComputedStyle(probe).color;probe.remove();
  const w=document.createTreeWalker(s,NodeFilter.SHOW_TEXT);
  for(let n;n=w.nextNode();){if(!n.nodeValue.trim())continue;const e=n.parentElement;if(!e||e.closest(skip))continue;
    const r=document.createRange();r.selectNodeContents(n);const rects=[...r.getClientRects()].filter(q=>q.width>1&&q.height>1);if(!rects.length)continue;
    let it=seen.get(e);
    if(!it){const cs=getComputedStyle(e);if(cs.visibility==='hidden'||cs.color===ghost)continue;   /* the ghost colour is for numerals that only decorate */
      let a=1;for(let p=e;p&&p!==page.parentElement;p=p.parentElement)a*=parseFloat(getComputedStyle(p).opacity);
      const m=/^rgb/.test(cs.color)?cs.color.match(/[\\d.]+/g).map(Number):null;
      it={t:'',px:parseFloat(cs.fontSize),bold:parseInt(cs.fontWeight,10)>=600,c:m?m.slice(0,3):null,a:a*(m&&m.length>3?m[3]:1),x0:1e9,y0:1e9,x1:-1e9,y1:-1e9,cut:0,q:[]};
      for(let p=e;p&&p!==s;p=p.parentElement){const ps=getComputedStyle(p);
        if(ps.overflowX!=='visible'||ps.overflowY!=='visible'){const q=p.getBoundingClientRect();it.clip=it.clip?{l:Math.max(it.clip.l,q.left),t:Math.max(it.clip.t,q.top),r:Math.min(it.clip.r,q.right),b:Math.min(it.clip.b,q.bottom)}:{l:q.left,t:q.top,r:q.right,b:q.bottom};}}
      seen.set(e,it);out.push(it);}
    it.t+=n.nodeValue.trim()+' ';
    for(const q of rects){it.q.push([q.left,q.top+q.height*.2,q.right,q.bottom-q.height*.2]);it.x0=Math.min(it.x0,q.left);it.y0=Math.min(it.y0,q.top);it.x1=Math.max(it.x1,q.right);it.y1=Math.max(it.y1,q.bottom);}}
  for(const it of out){if(it.clip)it.cut=Math.round(Math.max(it.clip.l-it.x0,it.x1-it.clip.r,it.clip.t-it.y0,it.y1-it.clip.b,0)/sc);delete it.clip;it.t=it.t.trim().slice(0,48);}
  /* is there a photo or a film under the text of this slide: an image or a background image that takes up a good part of it */
  let photo=false;const area=sr.width*sr.height,pics=[];
  s.querySelectorAll('img,video,.image,.photo,[style*="background-image"]').forEach(e=>{if(e.closest('.header,.footer,.vs-ic'))return;const q=e.getBoundingClientRect();
    const isPic=e.tagName==='IMG'?!/\\.svg|image\\/svg/.test(e.currentSrc||e.src||''):true; if(isPic&&q.width*q.height>area*.12)photo=true;
    if(isPic&&q.width*q.height>area*.04&&q.width>60&&q.height>60)pics.push([Math.max(q.left,sr.left),Math.max(q.top,sr.top),Math.min(q.right,sr.right),Math.min(q.bottom,sr.bottom)]);});
  return {items:out,sx:sr.left,sy:sr.top,sc:sc,photo:photo||pics.length>0,pics:pics}})()"""

_MARKS_JS = r"""(()=>{const page=document.querySelector('#deck > .slide.active');
  const s=page.querySelector(':scope > .rs > .slide')||page;
  const sr=s.getBoundingClientRect(),sc=sr.width/1920,out=[],area=sr.width*sr.height;
  const skip='.placeholder,.footer,.rbar,.notes,.rt,.ghost,.header,.qopts,[data-quiet],script,style,canvas,video,iframe,img,.image,.photo,.vs-credit,.badge,.biglogo,[aria-hidden=true]';
  const rgba=c=>{const m=/^rgba?\(/.test(c)?c.match(/[\d.]+/g).map(Number):null;return m?[m[0],m[1],m[2],m.length>3?m[3]:1]:null;};
  const tok=k=>{const i=document.createElement('i');i.style.color='var(--'+k+')';s.appendChild(i);const c=getComputedStyle(i).color;i.remove();return (rgba(c)||[]).slice(0,3).join();};
  const faint=new Set(['line','soft','ghost'].map(tok)),paper=tok('paper');      /* lines meant to stay quiet, and the slide's own ground */
  const op=e=>{let a=1;for(let p=e;p&&p!==page.parentElement;p=p.parentElement)a*=parseFloat(getComputedStyle(p).opacity);return a;};
  const name=e=>{const c=[...(e.classList||[])].filter(x=>!/^(anim|f|on|in)$/.test(x)).slice(0,2).join('.');return e.tagName.toLowerCase()+(c?'.'+c:'');};
  const where=e=>(e.parentElement&&e.parentElement!==s?name(e.parentElement)+' > ':'')+name(e);
  const add=(e,kind,col,w,q,part,own,thin)=>{const c=rgba(col);if(!c||c[3]<.05)return;const key=c.slice(0,3).join();
    if(key===paper||key===own)return;                    /* a fill in the ground's colour hides what is behind it; a border in the box's own colour is its edge */
    if(/shape|mark/.test(kind)&&w/sc>120)return;          /* a surface or a picture's stand-in, not a mark */
    const a=op(e)*c[3];if(a<.05)return;
    out.push({kind,c:c.slice(0,3),a,box:[q.left,q.top,q.right,q.bottom],d:where(e)+(part||''),faint:faint.has(key)||!!thin});};      /* a hairline is structure, like a line in --line */
  const borders=cs=>['Top','Right','Bottom','Left'].map(k=>({k:k.toLowerCase(),w:parseFloat(cs['border'+k+'Width'])||0,st:cs['border'+k+'Style'],c:cs['border'+k+'Color']})).filter(b=>b.w>=1&&b.st!=='none'&&b.st!=='hidden');
  const pbox=(e,cs,p,q)=>{          /* where a pseudo element is drawn: placed absolutely, from its offsets; else on its element */
    if(p.position!=='absolute'||cs.position==='static')return q;const n=k=>parseFloat(p[k])||0;
    const w=n('width')+n('paddingLeft')+n('paddingRight')+n('borderLeftWidth')+n('borderRightWidth'),h=n('height')+n('paddingTop')+n('paddingBottom')+n('borderTopWidth')+n('borderBottomWidth');
    const bl=parseFloat(cs.borderLeftWidth)||0,bt=parseFloat(cs.borderTopWidth)||0,W=q.width/sc-bl-(parseFloat(cs.borderRightWidth)||0),H=q.height/sc-bt-(parseFloat(cs.borderBottomWidth)||0);
    const x=p.left!=='auto'?n('left'):p.right!=='auto'?W-n('right')-w:0,y=p.top!=='auto'?n('top'):p.bottom!=='auto'?H-n('bottom')-h:0;
    const l=q.left+(bl+x+n('marginLeft'))*sc,t=q.top+(bt+y+n('marginTop'))*sc;return {left:l,top:t,right:l+w*sc,bottom:t+h*sc,width:w*sc,height:h*sc};};
  for(const e of s.querySelectorAll('*')){
    if(e.closest(skip))continue;const cs=getComputedStyle(e);if(cs.display==='none'||cs.visibility==='hidden')continue;
    const q=e.getBoundingClientRect();if(q.width<1&&q.height<1)continue;
    if(e instanceof SVGElement){if(!/^(path|circle|ellipse|line|polyline|polygon|rect)$/.test(e.tagName))continue;
      if(cs.stroke&&cs.stroke!=='none'&&parseFloat(cs.strokeWidth)>0)add(e,'figure line',cs.stroke,0,q);
      if(e.tagName!=='line'&&cs.fill&&cs.fill!=='none'&&!/url/.test(cs.fill))add(e,'figure shape',cs.fill,Math.min(q.width,q.height),q);continue;}
    const own=(rgba(cs.backgroundColor)||[]).slice(0,3).join(),bs=borders(cs);
    if(bs.length===4&&parseFloat(cs.borderTopLeftRadius)>=Math.min(q.width,q.height)*.4&&bs.every(b=>b.c===bs[0].c))add(e,'ring',bs[0].c,0,q,'',own);
    else for(const b of bs)add(e,'line',b.c,0,q,' border-'+b.k,own,b.w<=2);
    if(cs.columnRuleStyle!=='none'&&parseFloat(cs.columnRuleWidth)>=1)add(e,'line',cs.columnRuleColor,0,q,' column-rule','',parseFloat(cs.columnRuleWidth)<=2);
    if(!(e.innerText||'').trim()&&q.width*q.height<area*.25&&!/url\(/.test(cs.backgroundImage))add(e,'shape',cs.backgroundColor,Math.min(q.width,q.height),q);
    for(const ps of ['::before','::after']){const p=getComputedStyle(e,ps);if(!p.content||p.content==='none'||p.content==='normal'||p.display==='none')continue;
      const pw=parseFloat(p.width)||0,ph=parseFloat(p.height)||0,pq=pbox(e,cs,p,q);      /* arrows, ticks and bullets drawn in CSS */
      for(const b of borders(p))add(e,'mark',b.c,0,pq,ps);
      if(pw*ph<area*.25&&(pw>=1||ph>=1)&&!/url\(/.test(p.backgroundImage))add(e,'mark',p.backgroundColor,Math.min(pw||1e9,ph||1e9)*sc,pq,ps);}}
  return {marks:out}})()"""

MIN_TYPE = 18            # slide pixels (the slide is 1920 wide): below this nobody in a room reads it
EDGE = 24                # text closer to the slide's edge than this looks cut
MARK_MIN = 1.5           # a ring, an arrow, a bar or a point below this contrast to its ground is hardly seen
MARK_QUIET = 1.15        # a line in a quiet colour (--line, --soft, --ghost) may be faint, below this it is gone
MARK_HUE = 40            # a mark this far from its ground in colour (CIELAB) stands out even at low contrast: lime on white

_CASCADE = None

def _lum(c):
    f = lambda v: v / 12.92 if v <= .03928 else ((v + .055) / 1.055) ** 2.4
    return .2126 * f(c[0] / 255) + .7152 * f(c[1] / 255) + .0722 * f(c[2] / 255)

def _lab(c):
    f = lambda v: v / 12.92 if v <= .04045 else ((v + .055) / 1.055) ** 2.4
    r, g, b = (f(v / 255) for v in c)
    x, y, z = (.4124 * r + .3576 * g + .1805 * b) / .95047, .2126 * r + .7152 * g + .0722 * b, (.0193 * r + .1192 * g + .9505 * b) / 1.08883
    t = lambda v: v ** (1 / 3) if v > .008856 else 7.787 * v + 16 / 116
    return 116 * t(y) - 16, 500 * (t(x) - t(y)), 200 * (t(y) - t(z))

def _faces(im):
    """Faces in a picture of a slide: [(x0, y0, x1, y1)]. None when no detector is installed (then the check names
    slides with text over a photo and leaves the looking to the reader)."""
    global _CASCADE
    try:
        import cv2, numpy as np
    except Exception:
        return None
    try:
        if _CASCADE is None:
            _CASCADE = [cv2.CascadeClassifier(os.path.join(cv2.data.haarcascades, n)) for n in ("haarcascade_frontalface_default.xml", "haarcascade_frontalface_alt2.xml")]
        g = cv2.cvtColor(np.array(im), cv2.COLOR_RGB2GRAY)
        g = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8, 8)).apply(g)      # photos behind text are darkened: bring the faces back out
        hits = [[tuple(int(v) for v in f) for f in c.detectMultiScale(g, scaleFactor=1.08, minNeighbors=6, minSize=(26, 26))] for c in _CASCADE]
        both = []                                           # a face counts when both detectors see it: one alone sees faces in textures
        for (x, y, w, h) in hits[0]:
            if any(min(x + w, a + c) - max(x, a) > .5 * min(w, c) and min(y + h, b + d) - max(y, b) > .5 * min(h, d) for (a, b, c, d) in hits[1]):
                both.append((x, y, x + w, y + h))
        return both
    except Exception:
        return None

def _legible(r, shot):
    """Findings about one slide from the measured text and its screenshot: type too small, too little contrast
    between text and what is behind it, text cut off, text at the edge, texts on top of each other."""
    from PIL import Image
    import io
    im = Image.open(io.BytesIO(shot)).convert("RGB"); sc = r["sc"]; out = []
    def lum(c):
        f = lambda v: v / 12.92 if v <= .03928 else ((v + .055) / 1.055) ** 2.4
        return .2126 * f(c[0] / 255) + .7152 * f(c[1] / 255) + .0722 * f(c[2] / 255)
    items = [it for it in r["items"] if it["a"] > .05 and it["x1"] > it["x0"]]
    faces = _faces(im) if r.get("photo") else []
    if faces is None:
        out.append("hint: text stands on a photo here and no face detector is installed: look at the slide yourself, no text or number may cover a person's face")
    for pic in r.get("pics") or []:                        # the people in a picture: in view and in its middle, not at its edge
        inside = [f for f in faces or [] if pic[0] <= (f[0] + f[2]) / 2 <= pic[2] and pic[1] <= (f[1] + f[3]) / 2 <= pic[3]]
        if not inside or any(o is not pic and o[0] <= pic[0] and o[1] <= pic[1] and o[2] >= pic[2] and o[3] >= pic[3] for o in r["pics"]): continue
        pw, ph = pic[2] - pic[0], pic[3] - pic[1]
        cut = [f for f in inside if f[0] - pic[0] < .02 * pw or pic[2] - f[2] < .02 * pw or f[1] - pic[1] < .02 * ph]
        cx = sum((f[0] + f[2]) / 2 for f in inside) / len(inside); off = (cx - pic[0]) / pw
        if cut:
            out.append("hint: a person's head is cut by the edge of a picture: move the crop with the slide's \"focus\" or take another picture")
        elif (off < .3 or off > .7) and pw > .25 * im.width:
            out.append(f"hint: the people in a picture stand at its {'left' if off < .5 else 'right'} edge: bring the main subject to the middle with the slide's \"focus\" (\"{'left' if off < .5 else 'right'}\")")
    for (x0, y0, x1, y1) in faces or []:                   # a text or a number over a person's face
        w, h = x1 - x0, y1 - y0
        fx0, fy0, fx1, fy1 = x0 - .15 * w, y0 - .25 * h, x1 + .15 * w, y1 + .3 * h      # the head, not only eyes, nose and mouth
        for it in items:
            hit = False
            for q in it.get("q") or []:
                pad = (q[3] - q[1]) / 3                     # the line as tall as its letters stand
                ow = min(q[2], fx1) - max(q[0], fx0); oh = min(q[3] + pad, fy1) - max(q[1] - pad, fy0)
                if ow > 0 and oh > 0 and ow * oh > .04 * (fx1 - fx0) * (fy1 - fy0): hit = True; break
            if hit:
                line = f'covers a person\'s face in the photo: "{it["t"]}"'
                if line not in out: out.append(line)
    for it in items:
        q = '"' + it["t"] + '"'
        if it["px"] < MIN_TYPE:
            out.append(f"type of {it['px']:.0f} px, the least that reads is {MIN_TYPE}: {q}")
        elif it["px"] < 24 and len(it["t"]) >= 40:          # a sentence, not a label
            out.append(f"hint: running text of {it['px']:.0f} px is small for a room, 24 px and more reads well: {q}")
        if it["c"]:
            box = (max(0, int(it["x0"]) - 3), max(0, int(it["y0"]) - 3), min(im.width, int(it["x1"]) + 3), min(im.height, int(it["y1"]) + 3))
            if box[2] - box[0] > 2 and box[3] - box[1] > 2:
                px = list(im.crop(box).resize((min(48, box[2] - box[0]), min(24, box[3] - box[1]))).getdata())
                away = [c for c in px if sum(abs(c[k] - it["c"][k]) for k in range(3)) > 90] or px      # what is behind the letters; none left: text and ground are alike
                away.sort(key=lum); bg = away[len(away) // 2]
                fg = [bg[k] + (it["c"][k] - bg[k]) * min(1, it["a"]) for k in range(3)]
                hi, lo = sorted((lum(fg), lum(bg)), reverse=True); ratio = (hi + .05) / (lo + .05)
                need = 3.0 if it["px"] >= 24 or (it["bold"] and it["px"] >= 18) else 4.5
                if ratio < need:
                    out.append(f"contrast {ratio:.1f} to 1 between text and ground, needed are {need:g}: {q}")
        if it["cut"] > 3:
            out.append(f"cut off by {it['cut']} px: {q}")
        l, t, rr, b = [(it["x0"] - r["sx"]) / sc, (it["y0"] - r["sy"]) / sc, (it["x1"] - r["sx"]) / sc, (it["y1"] - r["sy"]) / sc]
        if l < EDGE or t < EDGE or rr > 1920 - EDGE or b > 1080 - EDGE:
            out.append(f"at the edge of the slide: {q}")
    import re
    solid = [it for it in items if re.search(r"\w", it["t"])]          # a quotation mark or a bullet may sit behind a text on purpose
    def hit(a, c):                                                      # line by line, inside the letters' height
        for p in a["q"]:
            for q in c["q"]:
                w = min(p[2], q[2]) - max(p[0], q[0]); h = min(p[3], q[3]) - max(p[1], q[1])
                if w > 2 and h > 2 and w * h > .3 * min((p[2] - p[0]) * (p[3] - p[1]), (q[2] - q[0]) * (q[3] - q[1])): return True
    for i, a in enumerate(solid):
        for c in solid[i + 1:]:
            if hit(a, c): out.append(f'texts on top of each other: "{a["t"]}" and "{c["t"]}"')
    return out

def _marks(r, shot):
    """Findings about the drawn parts of one slide: rings, arrows, lines, bars and points that hardly stand out from
    their ground, in brightness and in colour. A colour meant to stay quiet (--line, --soft, --ghost) and a hairline of up to 2 px only count when they vanish."""
    from PIL import Image
    import io
    im = Image.open(io.BytesIO(shot)).convert("RGB"); worst = {}
    for m in r["marks"]:
        x0, y0, x1, y1 = m["box"]; pad = 6
        box = (max(0, int(x0 - pad)), max(0, int(y0 - pad)), min(im.width, int(x1 + pad)), min(im.height, int(y1 + pad)))
        if box[2] - box[0] < 2 or box[3] - box[1] < 2: continue
        w, h = box[2] - box[0], box[3] - box[1]; k = max(1, max(w, h) // 64)
        away = [c for c in im.crop(box).resize((max(1, w // k), max(1, h // k)), Image.NEAREST).getdata() if sum(abs(c[i] - m["c"][i]) for i in range(3)) > 60]
        if not away: continue                               # nothing else in view: no ground to measure against
        away.sort(key=_lum); bg = away[len(away) // 2]
        fg = [bg[i] + (m["c"][i] - bg[i]) * min(1, m["a"]) for i in range(3)]
        hi, lo = sorted((_lum(fg), _lum(bg)), reverse=True); ratio = (hi + .05) / (lo + .05)
        if ratio < (MARK_QUIET if m["faint"] else MARK_MIN) and sum((a - b) ** 2 for a, b in zip(_lab(fg), _lab(bg))) ** .5 < MARK_HUE:
            key = (m["kind"], m["d"], m["faint"]); n, low = worst.get(key, (0, 99)); worst[key] = (n + 1, min(low, ratio))
    out = []
    for (kind, d, faint), (n, ratio) in worst.items():
        times = f" ({n} times)" if n > 1 else ""
        if faint: out.append(f"{kind} in --line, --soft or --ghost or as a hairline does not show, contrast {ratio:.2f} to 1 against its ground: {d}{times}")
        else: out.append(f"{kind} hardly stands out, contrast {ratio:.1f} to 1 against its ground, needed are {MARK_MIN:g}: {d}{times}")
    return out

def check(html, lang=None, bottom=980, right=1820, width=1600):
    """Render every slide and report overflow: content that runs below `bottom` or past `right`
    (in slide pixels, the slide is 1920 x 1080). Returns a list of problems, empty when all is well.
    Content inside a container with overflow:hidden is invisible to this check, look at such slides."""
    from playwright.sync_api import sync_playwright
    problems = []
    with sync_playwright() as p:
        br = p.chromium.launch(); pg = br.new_page(viewport={"width": width, "height": round(width * 9 / 16)})
        pg.goto("file://" + os.path.abspath(html) + (f"?lang={lang}" if lang else "")); pg.wait_for_timeout(800)
        n = pg.evaluate("document.querySelectorAll('#deck > .slide:not(.off)').length")
        for i in range(1, n + 1):
            pg.evaluate(f"location.hash='#/{i}'"); pg.wait_for_timeout(700)
            pg.evaluate("document.querySelectorAll('.slide.active .f').forEach(f=>f.classList.add('on'))"); pg.wait_for_timeout(300)
            r = pg.evaluate(_CHECK_JS)
            if r["skip"]:
                continue   # slides without footer (logo intro, mosaic) use the full area on purpose
            if r["b"] > bottom or r["r"] > right:
                problems.append(dict(slide=i, bottom=r["b"], right=r["r"], title=r["t"].strip()[:60]))
        br.close()
    return problems

def shots(html, out_dir, slides=None, lang=None, width=1600, settle=1800):
    """Screenshot slides as PNG for a visual check. slides: list of 1-based numbers, None for all."""
    from playwright.sync_api import sync_playwright
    os.makedirs(out_dir, exist_ok=True)
    paths = []
    with sync_playwright() as p:
        br = p.chromium.launch(); pg = br.new_page(viewport={"width": width, "height": round(width * 9 / 16)})
        pg.goto("file://" + os.path.abspath(html) + (f"?lang={lang}" if lang else "")); pg.wait_for_timeout(800)
        n = pg.evaluate("document.querySelectorAll('#deck > .slide:not(.off)').length")
        for i in (slides or range(1, n + 1)):
            pg.evaluate(f"location.hash='#/{i}'"); pg.wait_for_timeout(300)
            pg.evaluate("document.querySelectorAll('.slide.active .f').forEach(f=>f.classList.add('on'))")
            pg.wait_for_timeout(settle)
            path = os.path.join(out_dir, f"slide_{i:02d}.png"); pg.screenshot(path=path); paths.append(path)
        br.close()
    return paths


def _look(pg, shot):
    """The legibility findings of the slide on show: its text and its drawn parts."""
    try: return _legible(pg.evaluate(_LEGIBLE_JS), shot) + _marks(pg.evaluate(_MARKS_JS), shot)
    except Exception as e: return [f"could not be checked ({type(e).__name__}: {e})"[:160]]

def _by_scheme(seen, titles):
    """One entry per slide from the findings in each scheme ({scheme: {slide: findings}}): what all schemes show
    once and as it is, what only one shows with the scheme in front ("dark scheme: ...", after "hint: ")."""
    out = []
    for i in sorted(titles):
        each = {k: v.get(i, []) for k, v in seen.items()}
        common = [f for f in next(iter(each.values())) if all(f in v for v in each.values())]
        found = list(common)
        for k, v in each.items():
            for f in v:
                if f not in common:
                    found.append(("hint: " + k + " scheme: " + f[6:]) if f.startswith("hint: ") else (k + " scheme: " + f) if len(each) > 1 else f)
        if found: out.append(dict(slide=i, title=titles[i], findings=found))
    return out

def inspect(html, out_dir=None, lang=None, slides=None, bottom=930, right=1800, width=1280, per_sheet=6, stats=None, legible=None, schemes=True):
    """Fast look at a deck in one browser session: overflow check plus contact sheets.
    Runs in export mode (no animation, all click steps shown), about a tenth of a second per slide.
    Returns (problems, sheet paths). slides: 1-based numbers to look at, None for all.
    In a reading version the reader text is checked against its column as well (problem with `reader_text`).
    stats: a list that receives one dict per page for the density report: slide (page number), n (number in
    the deck file), words (visible on the slide, without footer and section bar), read (words of the reader
    text), notes (the reader text is the speaker notes as they are), title.
    legible: a list that receives one dict per slide with findings on legibility (slide, title, findings): type that is
    too small, text with too little contrast to its ground, text cut off or at the edge, texts on top of each other,
    rings, arrows, lines and bars that hardly stand out from their ground.
    schemes: look at the slides in the other scheme as well (light and dark, key D) and label what only one of them
    shows ("dark scheme: ..."); a finding both show is named once, without a label."""
    from playwright.sync_api import sync_playwright
    from PIL import Image
    import io
    problems, shots_ = [], []
    with sync_playwright() as p:
        br = p.chromium.launch(); pg = br.new_page(viewport={"width": width, "height": round(width * 9 / 16)})
        errors = []; pg.on("pageerror", lambda e: errors.append(str(e)))
        pg.goto("file://" + os.path.abspath(html) + "?export=1" + (f"&lang={lang}" if lang else "")); pg.wait_for_timeout(900)
        n = pg.evaluate("document.querySelectorAll('#deck > .slide:not(.off)').length")
        page_is_reading = pg.evaluate("!!document.querySelector('#deck > .slide > .rs')")      # the reduced slide of a reading version is checked in the live one
        look = legible is not None and not page_is_reading
        first = pg.evaluate("document.documentElement.getAttribute('data-scheme')") or "light"
        seen = {first: {}}; titles = {}
        for i in (slides or range(1, n + 1)):
            if i < 1 or i > n:
                continue
            pg.evaluate(f"location.hash='#/{i}'"); pg.wait_for_timeout(110)
            r = pg.evaluate(_CHECK_JS)
            floor = max(bottom, 980) if r.get("low") else bottom      # full-bleed text sits low on purpose
            if not r["skip"] and (r["b"] > floor or r["r"] > right):
                problems.append(dict(slide=i, bottom=r["b"], right=r["r"], title=r["t"].strip()[:60]))
            if r["over"] > 4:
                problems.append(dict(slide=i, reader_text=f"{r['over']} px too long for its column", title=r["t"].strip()[:60]))
            if stats is not None:
                stats.append(dict(slide=i, n=r["n"], words=r["words"], read=r["read"], notes=r["notes"], title=" ".join(r["t"].split())[:60]))
            shot = pg.screenshot() if out_dir or legible is not None else None
            if look:
                titles[i] = " ".join(r["t"].split())[:60]; seen[first][i] = _look(pg, shot)
            if out_dir:
                shots_.append((i, shot))
        if look and schemes and seen[first]:                # the same slides in the other scheme: only those that change with it
            other = "dark" if first == "light" else "light"; seen[other] = {}
            dk = lambda: pg.evaluate("[...document.querySelectorAll('#deck > .slide:not(.off)')].map(s=>s.classList.contains('vs-dk'))")
            was = dk()
            pg.goto("file://" + os.path.abspath(html) + "?export=1&scheme=" + other + (f"&lang={lang}" if lang else "")); pg.wait_for_timeout(900)
            now = dk()
            for i in seen[first]:
                if i - 1 < len(was) and i - 1 < len(now) and was[i - 1] == now[i - 1]:
                    seen[other][i] = seen[first][i]; continue      # a dark, accent or photo slide looks the same in both
                pg.evaluate(f"location.hash='#/{i}'"); pg.wait_for_timeout(110)
                seen[other][i] = _look(pg, pg.screenshot())
        br.close()
    if look:
        legible += _by_scheme(seen, titles)
    for e in errors[:3]:
        problems.append(dict(slide=0, error=e[:200]))
    sheets = []
    if out_dir and shots_:
        os.makedirs(out_dir, exist_ok=True)
        for old in os.listdir(out_dir):
            if old.startswith("sheet_" + (lang or "") ) and old.endswith(".png"):
                os.remove(os.path.join(out_dir, old))
        tw, th, gap, cols = 640, 360, 8, 2 if per_sheet <= 6 else 3
        for s in range(0, len(shots_), per_sheet):
            part = shots_[s:s + per_sheet]
            rows = (len(part) + cols - 1) // cols
            sheet = Image.new("RGB", (cols * tw + (cols + 1) * gap, rows * (th + 26) + (rows + 1) * gap), "#3a3a3a")
            from PIL import ImageDraw
            d = ImageDraw.Draw(sheet)
            for k, (num, png) in enumerate(part):
                x, y = gap + (k % cols) * (tw + gap), gap + (k // cols) * (th + 26 + gap)
                sheet.paste(Image.open(io.BytesIO(png)).convert("RGB").resize((tw, th), Image.LANCZOS), (x, y + 26))
                d.text((x + 4, y + 7), f"slide {num}", fill="#ffffff")
            path = os.path.join(out_dir, f"sheet_{lang + '_' if lang else ''}{s // per_sheet + 1}.png"); sheet.save(path); sheets.append(path)
    return problems, sheets


if __name__ == "__main__":
    args = sys.argv[1:]
    if len(args) < 2:
        print(__doc__); sys.exit(1)
    slides, out = args[0], args[1]
    opt = dict(brand=None, title=None, lang=None)
    images = {}
    for i, a in enumerate(args):
        if a in ("--brand", "--title", "--lang"):
            opt[a[2:]] = args[i + 1]
        if a == "--image":
            k, v = args[i + 1].split("=", 1); images[k] = v
    build(slides, out, images=images, pdf="--pdf" in args, **opt)
    if "--check" in args:
        for l in slide_langs(open(slides, encoding="utf-8").read()) or [opt["lang"]]:
            print("check", l, check(out, lang=l))
