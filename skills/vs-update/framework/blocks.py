# -*- coding: utf-8 -*-
"""More building blocks for VibeUpSlides decks.

- header_band(text, color)              coloured header line above a column, instead of grey note boxes
- verdict_columns(columns)              columns with a header band each, e.g. Fits / Clarify first / Does not fit
- team_card(image, name, text, journey) cut-out photo standing flush on top of a card
- team_row(cards, weights)              row of team cards, with wider columns for group photos
- path_tags(steps)                      small colour tags joined by arrows, e.g. Us -> Partner
- map_with_pins(image, pins, ...)       map section with pins positioned in percent
- contact_block(...)                    cut-out portrait, name, role, mail, LinkedIn, QR code

Images appear as {{IMG_NAME}} in the result; fill them in at build time with images=dict(NAME=path).
Cut-out photos and logo stickers are made with cutout.py.
"""

ACCENT, DEEP, MUTED, LINE = "var(--accent)", "var(--deep)", "var(--muted)", "var(--line)"


def _on(color):
    """Text colour for text sitting on a fill of the given colour."""
    return {ACCENT: "var(--on-accent)", DEEP: "var(--on-deep)", MUTED: "var(--paper)"}.get(color, "#fff")      # paper: white in a light look, dark where the whole look is dark


def _img(name):
    return "{{IMG_" + name + "}}"


def header_band(text, color=ACCENT):
    """Coloured header line above a column. Any colour works (ACCENT, DEEP, MUTED or a CSS colour)."""
    return f'<div style="background:{color};color:{_on(color)};font-size:25px;font-weight:700;padding:13px 20px">{text}</div>'


def verdict_columns(columns, weights="1.25fr 1fr 1fr", font=22):
    """columns: list of (title, colour, [bullets]). Typical use is three columns:
    Fits (ACCENT), Clarify first (DEEP), Does not fit (MUTED)."""
    cols = ""
    for title, color, bullets in columns:
        li = "".join(f'<li style="font-size:{font}px;margin-bottom:14px;line-height:1.34">{p}</li>' for p in bullets)
        cols += f'<div class="anim" style="min-width:0">{header_band(title, color)}<ul class="bullets" style="margin-top:20px">{li}</ul></div>'
    return f'<div style="margin-top:40px;display:grid;grid-template-columns:{weights};gap:44px">{cols}</div>'


def path_tags(steps):
    """steps: list of (text, accent). Each tag marks who is responsible for a step:
    accent colour (accent=True) for your own organisation, deep colour for partners."""
    def tag(text, accent):
        color = ACCENT if accent else DEEP
        return (f'<span style="display:inline-block;font-size:17px;font-weight:700;letter-spacing:.03em;padding:5px 10px;'
                f'background:{color};color:{_on(color)}">{text}</span>')
    arrow = f'<span style="font-size:22px;color:{MUTED};margin:0 6px">&rarr;</span>'
    return ('<div style="display:flex;flex-wrap:wrap;align-items:center;gap:4px 0;margin:14px 0 16px">'
            + arrow.join(tag(text, accent) for text, accent in steps) + '</div>')


def team_card(image, name, text, journey=None, image_height=260):
    """Cut-out photo (PNG with transparency) standing flush on top of a card. journey: optional steps for path_tags()."""
    photo = (f'<div style="height:{image_height}px;display:flex;align-items:flex-end;justify-content:center">'
             f'<img src="{_img(image)}" alt="" style="max-height:{image_height}px;max-width:100%;width:auto;height:auto;display:block"></div>')
    tags = path_tags(journey) if journey else ""
    return (f'<div class="anim" style="min-width:0;display:flex;flex-direction:column">{photo}'
            f'<div class="card" style="padding:22px 22px;flex:1"><h3 style="font-size:28px;margin:0">{name}</h3>'
            f'{tags}<p style="font-size:21px;line-height:1.36;margin:0">{text}</p></div></div>')


def team_row(cards, weights=None):
    """cards: list of finished team_card(...) strings. weights e.g. "1fr 1.5fr 1fr": make columns with group photos
    wider, otherwise the people get too small. Keep the title above on one line (font-size 52px), then everything
    fits above the footer."""
    grid = weights or f"repeat({len(cards)},minmax(0,1fr))"
    return f'<div style="margin-top:22px;display:grid;grid-template-columns:{grid};gap:20px">{"".join(cards)}</div>'


def _pin(x, y, text, accent=True):
    color = ACCENT if accent else DEEP
    return (f'<div style="position:absolute;left:{x}%;top:{y}%;transform:translate(-50%,-100%);z-index:3;display:flex;flex-direction:column;align-items:center">'
            f'<div style="background:{color};color:{_on(color)};font-size:20px;font-weight:700;padding:8px 14px;white-space:nowrap">{text}</div>'
            f'<div style="width:0;height:0;border-left:10px solid transparent;border-right:10px solid transparent;border-top:14px solid {color}"></div></div>')


def map_with_pins(image, pins, width=960, height=530, credit=""):
    """Map section with pins. pins: list of (x_percent, y_percent, text, accent). The tip of a pin points at the place.
    credit: pass the attribution your map source requires (e.g. "Map data &copy; ..."); it is shown in the bottom
    right corner of the map. Empty (the default) renders no credit element."""
    markers = "".join(_pin(x, y, text, accent) for x, y, text, accent in pins)
    credit_html = (f'<div style="position:absolute;right:12px;bottom:12px;z-index:2;font-size:13px;letter-spacing:.04em;'
                   f'color:#fff;background:rgba(43,43,45,.72);padding:5px 9px">{credit}</div>') if credit else ""
    return (f'<div class="anim" style="position:relative;width:{width}px;height:{height}px;overflow:hidden">'
            f'<img src="{_img(image)}" alt="" style="width:100%;height:100%;object-fit:cover;object-position:50% 40%;display:block">{markers}{credit_html}</div>')


def contact_block(portrait, name, role, mail, linkedin=None, qr=None, qr_text="", labels=("Mail", "LinkedIn")):
    """Contact slide: cut-out portrait on the left (flush at the bottom), name, role, mail and LinkedIn as links,
    QR code on the right. Read the QR code back from the built deck to test it (pick the image by its size, not
    the last PNG on the slide)."""
    linkedin_row = (f'<div><span style="display:inline-block;width:120px;color:{MUTED}">{labels[1]}</span>'
                    f'<a href="{linkedin}" style="color:inherit">{linkedin.replace("https://www.", "")}</a></div>') if linkedin else ""
    qr_html = (f'<div class="anim"><img src="{_img(qr)}" alt="" style="width:250px;height:250px;display:block">'
               f'<p style="font-size:18px;color:{MUTED};margin-top:12px;line-height:1.35">{qr_text}</p></div>') if qr else "<div></div>"
    return (f'<div style="margin-top:20px;display:grid;grid-template-columns:420px 1fr 250px;gap:60px;align-items:center">'
            f'<div class="anim" style="height:520px;display:flex;align-items:flex-end;justify-content:center">'
            f'<img src="{_img(portrait)}" alt="" style="max-height:520px;max-width:100%;width:auto;height:auto;display:block"></div>'
            f'<div class="anim"><div style="font-size:44px;font-weight:var(--w-display);line-height:1.1">{name}</div>'
            f'<div style="font-size:26px;color:{ACCENT};font-weight:700;margin-top:10px">{role}</div>'
            f'<div style="margin-top:28px;font-size:25px;line-height:1.7">'
            f'<div><span style="display:inline-block;width:120px;color:{MUTED}">{labels[0]}</span>'
            f'<a href="mailto:{mail}" style="color:inherit">{mail}</a></div>{linkedin_row}</div></div>{qr_html}</div>')
