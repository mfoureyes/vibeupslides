# -*- coding: utf-8 -*-
"""Prepare images for VibeUpSlides decks: cut out people, turn logos into stickers.

Requirements: Pillow, plus heavier packages that are only imported when a function needs them:
    pip install "rembg[cpu]" opencv-python-headless numpy
rembg (cut_out, restore_object) and OpenCV with numpy (refine, logo_sticker) are imported lazily, so importing
this module and using compose() or shrink() works with Pillow alone. rembg downloads its models on first use
(isnet-general-use is about 180 MB).

What has worked well:
- Model isnet-general-use for single portraits and people holding objects, u2net_human_seg for group photos.
- birefnet-portrait (almost 1 GB) needs more than 7 GB of memory; on smaller machines the process gets killed.
- Always run refine() after cutting out: it removes semi-transparent leftovers and keeps only large connected areas.
- Objects in mid-air (a thrown toy, say) get lost when cutting out. Cut them out separately with restore_object()
  and put them back in the same place.
- Join two single portraits of a team into one team picture with compose().
- shrink() cut-outs to about 500 pixels height as PNG (620 for the portrait on a contact slide). Every image is
  embedded once per language in the deck, so the HTML otherwise quickly grows beyond 8 MB.

Use as a script:
    python3 cutout.py person photo.jpg out.png [--model u2net_human_seg] [--height 500]
    python3 cutout.py sticker logo.jpg out.png [--width 1000]
"""
import sys
from PIL import Image

_SESSIONS = {}


def _session(model):
    from rembg import new_session
    if model not in _SESSIONS:
        _SESSIONS[model] = new_session(model)
    return _SESSIONS[model]


def refine(im, threshold=110, floor=60, min_share=0.01):
    """Clean the alpha channel: drop pixels below threshold, keep only connected areas of at least min_share of
    the total area, rescale alpha so that floor becomes fully transparent, soften the edge slightly and crop to
    the content."""
    import cv2
    import numpy as np
    rgba = np.array(im.convert("RGBA"))
    alpha = rgba[:, :, 3].astype(float)
    mask = (alpha > threshold).astype(np.uint8)
    count, labels, stats, _ = cv2.connectedComponentsWithStats(mask)
    keep = np.zeros_like(mask)
    for i in range(1, count):
        if stats[i, 4] > min_share * max(mask.sum(), 1):
            keep[labels == i] = 1
    alpha2 = np.where(keep > 0, np.clip((alpha - floor) * 255 / (255 - floor), 0, 255), 0)
    alpha2 = cv2.GaussianBlur(alpha2, (3, 3), 0)
    rgba[:, :, 3] = alpha2.astype(np.uint8)
    out = Image.fromarray(rgba)
    return out.crop(out.getbbox())


def cut_out(path, model="isnet-general-use", crop=None, clean=True):
    """Cut out a person. crop: (left, top, right, bottom) in the original, to cut away table, room etc. beforehand.
    clean=True runs refine() on the result."""
    from rembg import remove
    im = Image.open(path).convert("RGB")
    if crop:
        im = im.crop(crop)
    out = remove(im, session=_session(model))
    return refine(out) if clean else out


def restore_object(cutout, original_path, box, offset=(0, 0), model="isnet-general-use"):
    """Cut out an object that got lost when cutting out the person, and put it back in.
    box: region around the object in the original. offset: top left corner of the crop that was used for the
    person (so (x0, y0) for cut_out(..., crop=(x0, y0, ...))).
    Important: use cut_out(..., clean=False) in that case and crop only after the object is back in."""
    from rembg import remove
    part = remove(Image.open(original_path).convert("RGB").crop(box), session=_session(model))
    result = cutout.copy()
    result.alpha_composite(part, (box[0] - offset[0], box[1] - offset[1]))
    return result.crop(result.getbbox())


def compose(images, overlap=0.3, height=700):
    """Put several cut-outs side by side as one team picture: same height, slightly overlapping.
    The first image is in front."""
    scaled = [im.resize((int(im.width * height / im.height), height), Image.LANCZOS) for im in images]
    shift = int(min(im.width for im in scaled) * overlap)
    width = sum(im.width for im in scaled) - shift * (len(scaled) - 1)
    canvas = Image.new("RGBA", (width, height))
    xs, x = [], 0
    for im in scaled:
        xs.append(x)
        x += im.width - shift
    for im, x in reversed(list(zip(scaled, xs))):
        canvas.alpha_composite(im, (x, 0))
    return canvas


def shrink(im, height=None, width=None):
    """Scale down to at most the given height and/or width, keeping the aspect ratio. Never enlarges."""
    if height and im.height > height:
        im = im.resize((int(im.width * height / im.height), height), Image.LANCZOS)
    if width and im.width > width:
        im = im.resize((width, int(im.height * width / im.width)), Image.LANCZOS)
    return im


def logo_sticker(path, width=1000, outline=None, white_from=18, opaque_from=120):
    """Cut a logo out of its white background and give it a white outline, so it stands on a coloured or dark
    surface. The colours are un-mixed from white so that no grey fringes remain.
    outline: width of the white outline in pixels (default 1.8 % of the logo width).
    white_from / opaque_from: distance from white (0-255) below which a pixel is fully transparent / from which
    it is fully opaque."""
    import cv2
    import numpy as np
    rgb = np.array(Image.open(path).convert("RGB")).astype(float)
    dist = 255 - rgb.min(axis=2)
    alpha = np.clip((dist - white_from) * 255 / (opaque_from - white_from), 0, 255)
    frac = alpha[..., None] / 255.0
    col = np.where(frac > 0.02, (rgb - 255 * (1 - frac)) / np.maximum(frac, 1e-3), 255)
    logo = Image.fromarray(np.dstack([np.clip(col, 0, 255), alpha]).astype(np.uint8))
    logo = logo.crop(logo.getbbox())
    logo_alpha = np.array(logo)[:, :, 3]
    r = outline or max(6, int(logo.width * 0.018))
    pad = r + 4
    padded = cv2.copyMakeBorder(logo_alpha, pad, pad, pad, pad, cv2.BORDER_CONSTANT, 0)
    kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (2 * r + 1, 2 * r + 1))
    dilated = cv2.GaussianBlur(cv2.dilate((padded > 40).astype(np.uint8) * 255, kernel), (5, 5), 0)
    base = np.zeros((padded.shape[0], padded.shape[1], 4), np.uint8)
    base[..., :3] = 255
    base[..., 3] = dilated
    out = Image.fromarray(base)
    out.alpha_composite(logo, (pad, pad))
    return shrink(out, width=width)


if __name__ == "__main__":
    args = sys.argv[1:]

    def opt(name, default=None):
        return args[args.index(name) + 1] if name in args else default

    if len(args) >= 3 and args[0] == "person":
        result = cut_out(args[1], model=opt("--model", "isnet-general-use"))
        shrink(result, height=int(opt("--height", 500))).save(args[2], optimize=True)
    elif len(args) >= 3 and args[0] == "sticker":
        logo_sticker(args[1], width=int(opt("--width", 1000))).save(args[2], optimize=True)
    else:
        print(__doc__)
