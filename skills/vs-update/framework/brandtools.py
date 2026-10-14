"""Tools for a brand in the library: show and change values, logo and font helpers. Used through vs.py."""
import json, os, sys

import build as B


def _path(brand):
    return os.path.join(B.brand_dir(brand), "brand.json")

def _read(brand):
    return json.load(open(_path(brand), encoding="utf-8"))

def _write(brand, data):
    json.dump(data, open(_path(brand), "w", encoding="utf-8"), indent=2, ensure_ascii=False)

def show(brand):
    b = B.load_brand(brand)
    print("folder:", b["_dir"])
    print(json.dumps({k: v for k, v in b.items() if k not in ("_dir", "images", "logo_candidates")}, indent=2, ensure_ascii=False))
    for w in B.brand_warnings(b):
        print("WARNING:", w)
    for f in ("styleguide.md", "voice.md", "theme.css", "masters"):
        print(f, "present" if os.path.exists(os.path.join(b["_dir"], f)) else "MISSING")

def set_values(brand, pairs):
    data = _read(brand)
    for pair in pairs:
        key, value = pair.split("=", 1)
        try: value = json.loads(value)
        except ValueError: pass
        node = data
        parts = key.split(".")
        for p in parts[:-1]:
            node = node.setdefault(p, {})
        node[parts[-1]] = value
        print("set", key, "=", value)
    _write(brand, data)
    for w in B.brand_warnings(B.load_brand(brand)):
        print("WARNING:", w)

def _raster(path, height=600):
    """Open a logo as RGBA image. SVG files are rendered with Chromium."""
    from PIL import Image
    if path.lower().endswith(".svg"):
        import base64, io
        from playwright.sync_api import sync_playwright
        uri = "data:image/svg+xml;base64," + base64.b64encode(open(path, "rb").read()).decode()
        with sync_playwright() as p:
            br = p.chromium.launch(); pg = br.new_page(viewport={"width": 2400, "height": 1400})
            pg.set_content(f'<body style="margin:0;background:transparent"><img id="l" src="{uri}" style="height:{height}px;width:auto;display:block"></body>')
            pg.wait_for_timeout(300)
            png = pg.locator("#l").screenshot(omit_background=True); br.close()
        return Image.open(io.BytesIO(png)).convert("RGBA")
    return Image.open(path).convert("RGBA")

def _with_alpha(im):
    """A logo on an opaque light ground gets its transparency from the brightness of each pixel."""
    from PIL import ImageOps
    alpha = im.getchannel("A")
    if alpha.getextrema()[0] > 250:
        alpha = ImageOps.invert(im.convert("L")).point(lambda v: min(255, int(v * 1.25)))
        im = im.copy(); im.putalpha(alpha)
    return im

def trim(brand, logo=None):
    """Cut transparent or white margins off the logo, saved as <name>_trim.png and set as logos.primary."""
    data = _read(brand); d = B.brand_dir(brand)
    rel = logo or data["logos"]["primary"]
    im = _with_alpha(_raster(os.path.join(d, rel)))
    box = im.getchannel("A").point(lambda v: 255 if v > 12 else 0).getbbox()
    if box: im = im.crop(box)
    out = os.path.splitext(rel)[0] + "_trim.png"
    im.save(os.path.join(d, out))
    if not logo or rel == data["logos"].get("primary"):
        data["logos"]["primary"] = out; _write(brand, data)
    print("trimmed logo:", out, im.size)
    return out

def inverse(brand, logo=None):
    """White silhouette of the logo for dark and accent slides, saved as <name>_white.png and set as
    logos.primary_inverse. Right for one-colour logos. A logo with several colours or a photo in it
    needs a real light version from the brand owner; until then keep logos.inverse_mode at "plate"."""
    from PIL import Image
    data = _read(brand); d = B.brand_dir(brand)
    rel = logo or data["logos"]["primary"]
    im = _with_alpha(_raster(os.path.join(d, rel)))
    white = Image.new("RGBA", im.size, (255, 255, 255, 0)); white.putalpha(im.getchannel("A"))
    box = white.getchannel("A").point(lambda v: 255 if v > 12 else 0).getbbox()
    if box: white = white.crop(box)
    out = os.path.splitext(rel)[0] + "_white.png"
    white.save(os.path.join(d, out))
    data["logos"]["primary_inverse"] = out; data["logos"]["inverse_mode"] = "file"; _write(brand, data)
    print("white logo:", out, white.size)
    return out
