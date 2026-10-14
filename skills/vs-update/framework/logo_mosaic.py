# -*- coding: utf-8 -*-
"""Slide: a logo assembles from tiles that first show other logos (customers, portfolio companies, partners).
Use: html, css, n = mosaic_slide("images/tiles", lang="en", logo_path="brand/logo_inverse.png")
     add(html); add("<style>" + css + "</style>")
The tiles are prepared logos (dark on white, trimmed), file names W1.png, W2.png, ...
The inverse (light) logo is cut into a grid of tiles. Every tile first shows one of the other logos, then turns over
flat (gets narrow, gets wide again) and shows exactly its piece of the logo on the back. Appearing and turning run
from the centre outwards. At the end all pieces sit together without gaps, then the real logo takes over.
The slide uses the mfade keyframes from motion.py, so MOTION_ASSETS has to be in the deck."""
import base64, io, glob, math, os, random
from PIL import Image

def b64(im, fmt="PNG"):
    b = io.BytesIO(); im.save(b, fmt, optimize=True); return base64.b64encode(b.getvalue()).decode()

def tile_image(path, w=240, h=120, pad=16):
    im = Image.open(path).convert("RGB")
    im.thumbnail((w - 2 * pad, h - 2 * pad), Image.LANCZOS)
    tile = Image.new("RGB", (w, h), "white"); tile.paste(im, ((w - im.width) // 2, (h - im.height) // 2))
    return tile

def mosaic_slide(tile_dir, lang="en", logo_path=None, kicker="", row=None, title="Logo mosaic",
                 width=1640, tile_w=40, tile_h=20, threshold=0.03, seed=7,
                 t_in=(0.15, 2.6), t_flip=(3.25, 1.45), t_done=5.05, zoom=4.2, focus=(0.75, 0.5)):
    """tile_dir: folder with the tile logos W1.png, W2.png, ... logo_path: the logo that is assembled (required,
    a light logo with transparency, the slide is dark). kicker: small line at the top left. row: sentence below
    the logo, nothing is shown if None. Returns (html, css, number of tiles).
    width: logo width in px. tile_w, tile_h: tile width and height in px. threshold: minimum share of logo pixels for a
    grid cell to get a tile. seed: random seed for the choice of tiles. t_in: (start, spread) in seconds for
    the tiles appearing, t_flip: (start, spread) for turning over, t_done: second at which the real logo takes
    over. zoom: scale at the start of the camera move. focus: point (x, y as share of the logo) from which
    everything spreads outwards."""
    if not logo_path:
        raise ValueError("mosaic_slide needs logo_path: the path of the logo to assemble (a light logo with transparency).")
    logo = Image.open(logo_path).convert("RGBA")
    height = round(width * logo.height / logo.width)
    big = logo.resize((width, height), Image.LANCZOS)
    a = big.split()[3]
    columns, rows = math.ceil(width / tile_w), math.ceil(height / tile_h)
    cells = []
    for r in range(rows):
        for c in range(columns):
            box = (c * tile_w, r * tile_h, min(width, (c + 1) * tile_w), min(height, (r + 1) * tile_h))
            px = a.crop(box); hist = px.histogram()
            density = sum(i * n for i, n in enumerate(hist)) / (255 * max(1, px.width * px.height))
            if density >= threshold: cells.append((c, r))
    files = sorted(glob.glob(os.path.join(tile_dir, "W*.png")), key=lambda p: int(os.path.basename(p)[1:-4]))
    rnd = random.Random(seed)
    assigned = {}
    for c, r in cells:
        neighbours = {assigned.get((c + dx, r + dy)) for dx in (-1, 0, 1) for dy in (-1, 0, 1)}
        assigned[(c, r)] = rnd.choice([i for i in range(len(files)) if i not in neighbours])
    fx, fy = focus[0] * width, focus[1] * height        # from the inside outwards: the focus point of the logo
    dmax = max(math.hypot((c + .5) * tile_w - fx, ((r + .5) * tile_h - fy) * 1.6) for c, r in cells)
    tiles = []
    for c, r in cells:
        d = math.hypot((c + .5) * tile_w - fx, ((r + .5) * tile_h - fy) * 1.6) / dmax
        appear = t_in[0] + t_in[1] * d ** 0.8 + rnd.random() * 0.1
        flip = t_flip[0] + t_flip[1] * d + rnd.random() * 0.06
        tiles.append(f'<i style="left:{c*tile_w}px;top:{r*tile_h}px;--a:{appear:.2f}s;--f:{flip:.2f}s">'
                     f'<b style="background-image:var(--k{assigned[(c,r)]})"></b>'
                     f'<s style="background-position:{-c*tile_w}px {-r*tile_h}px"></s></i>')
    vars_css = ";".join(f"--k{i}:url(data:image/png;base64,{b64(tile_image(p))})" for i, p in enumerate(files))
    logo_uri = "data:image/png;base64," + b64(big)
    row_html = f'<p class="mmline">{row}</p>' if row else ""
    kick = f'<div class="kicker mmkick">{kicker}</div>' if kicker else ""
    if lang == "de":
        notes = ("Etwa sieben Sekunden. Kacheln mit Logos tauchen von der Mitte nach außen auf, die Kamera fährt zurück. "
                 "Dann drehen sich die Kacheln von innen nach außen um und zeigen auf der Rückseite ihr Stück des Logos, "
                 f"bis das Logo fugenlos dasteht. {len(tiles)} Kacheln, {len(files)} verschiedene Logos.")
    else:
        notes = ("About seven seconds. Tiles with logos appear from the centre outwards while the camera pulls back. "
                 "Then the tiles turn over from the inside outwards and show their piece of the logo on the back, "
                 f"until the logo stands there without gaps. {len(tiles)} tiles, {len(files)} different logos.")
    html = f'''
<section class="slide dark mslide mmosaic no-header no-footer" lang="{lang}" data-title="{title}">
  {kick}
  <div class="mmstage" style="width:{width}px;height:{height}px;margin-left:{-width//2}px;margin-top:{-height//2}px">
    <div class="mmzoom" style="transform-origin:{fx:.0f}px {fy:.0f}px;--logo:url({logo_uri});{vars_css}">
      {"".join(tiles)}
    </div>
    <img class="mmlogo" src="{logo_uri}" alt="">
  </div>
  {row_html}
  <aside class="notes">{notes}</aside>
</section>'''
    css = f'''
.mmosaic{{background:var(--deep)}}
.mmstage{{position:absolute;left:50%;top:47%}}
.mmzoom{{position:absolute;inset:0;opacity:0}}
.mmzoom i{{position:absolute;width:{tile_w}px;height:{tile_h}px}}
.mmzoom b{{position:absolute;inset:1.5px;background-color:#fff;background-size:cover;background-position:center}}
.mmzoom s{{position:absolute;inset:0;background-image:var(--logo);background-size:{width}px {height}px;background-repeat:no-repeat}}
.active .mmzoom{{animation:mmtravel 3s cubic-bezier(.55,0,.2,1) .2s both,mmvisible {t_done}s step-end both}}
@keyframes mmtravel{{from{{transform:scale({zoom})}}to{{transform:none}}}}
@keyframes mmvisible{{from{{opacity:1}}to{{opacity:0}}}}
.active .mmzoom b{{animation:mmin .5s cubic-bezier(.2,.7,.2,1) var(--a) both,mmclose .17s cubic-bezier(.6,0,1,.6) var(--f) forwards}}
@keyframes mmin{{from{{transform:scale(0)}}to{{transform:none}}}}
@keyframes mmclose{{from{{transform:none}}to{{transform:scaleX(0)}}}}
.active .mmzoom s{{animation:mmopen .2s cubic-bezier(0,.4,.4,1) calc(var(--f) + .17s) both}}
@keyframes mmopen{{from{{transform:scaleX(0)}}to{{transform:none}}}}
.mmlogo{{position:absolute;left:0;top:0;width:100%;height:100%}}
.active .mmlogo{{animation:mmlogo {t_done}s step-end both}}
@keyframes mmlogo{{from{{opacity:0}}to{{opacity:1}}}}
.mmkick{{position:absolute;left:var(--pad);top:70px;color:color-mix(in srgb,var(--on-deep) 55%,transparent)}}
.mmline{{position:absolute;left:0;right:0;bottom:120px;text-align:center;font-size:26px;color:color-mix(in srgb,var(--on-deep) 75%,transparent)}}
.active .mmkick,.active .mmline{{animation:mfade .8s {t_done+0.3:.2f}s var(--ease) both}}
'''
    return html, css, len(tiles)

if __name__ == "__main__":
    import sys
    if len(sys.argv) < 3:
        sys.exit("usage: logo_mosaic.py <tile folder> <logo.png>")
    h, c, n = mosaic_slide(sys.argv[1], logo_path=sys.argv[2])
    print(n, "tiles", round(len(h) / 1024), "kB")
