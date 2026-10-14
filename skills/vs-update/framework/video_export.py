# -*- coding: utf-8 -*-
"""Render one slide of a built deck to video, frame by frame, so it plays evenly.

    python3 video_export.py deck.html --slide 11 --seconds 7 --out logo.mp4 [--lang en] [--fps 30] [--format 16:9|1:1|9:16]

All animations of the slide are paused and set to the matching time for every frame (Web Animations API).
Result: MP4 (H.264), 1920 by 1080 at 16:9. The kicker and the controls of the slide stay as they are; hide
whatever should not be in the video with --hide ".selector" (repeatable). Without --lang the deck's default
language is used. Needs Playwright with Chromium, and ffmpeg.
"""
import argparse, os, shutil, subprocess, tempfile

FORMATS = {"16:9": (1920, 1080), "1:1": (1080, 1080), "9:16": (1080, 1920)}

def render(deck, slide, seconds, out, lang=None, fps=30, fmt="16:9", hide=()):
    from playwright.sync_api import sync_playwright
    w, h = FORMATS[fmt]
    tmp = tempfile.mkdtemp(prefix="vibeupslides_video_")
    query = f"?lang={lang}" if lang else ""
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(); page = browser.new_page(viewport={"width": w, "height": h})
            page.goto("file://" + os.path.abspath(deck) + f"{query}#/{slide}"); page.wait_for_timeout(2500)
            for sel in hide:
                page.evaluate(f"document.querySelectorAll('.slide.active {sel}').forEach(e=>e.style.visibility='hidden')")
            page.keyboard.press("r"); page.wait_for_timeout(50)  # "r" replays the slide's animations
            page.evaluate("window.__anims=document.querySelector('.slide.active').getAnimations({subtree:true}); __anims.forEach(a=>a.pause())")
            for i in range(int(fps * seconds)):
                page.evaluate(f"__anims.forEach(a=>a.currentTime={i * 1000 / fps})")
                page.screenshot(path=os.path.join(tmp, f"f{i:05d}.png"))
            browser.close()
        subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-framerate", str(fps), "-i", os.path.join(tmp, "f%05d.png"),
                        "-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", "18", "-preset", "slow", "-movflags", "+faststart", out],
                       check=True)
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    print(out, os.path.getsize(out) // 1024, "kB")

if __name__ == "__main__":
    ap = argparse.ArgumentParser(description="Render one slide of a built deck to MP4, frame by frame.")
    ap.add_argument("deck", help="built deck (HTML file)")
    ap.add_argument("--slide", type=int, required=True, help="slide number")
    ap.add_argument("--seconds", type=float, default=6, help="length of the video (default 6)")
    ap.add_argument("--out", required=True, help="output file (.mp4)")
    ap.add_argument("--lang", default=None, help="deck language to show (default: the deck's default)")
    ap.add_argument("--fps", type=int, default=30)
    ap.add_argument("--format", default="16:9", choices=list(FORMATS))
    ap.add_argument("--hide", action="append", default=[], metavar="SELECTOR",
                    help="CSS selector inside the slide to hide; repeatable")
    args = ap.parse_args()
    render(args.deck, args.slide, args.seconds, args.out, args.lang, args.fps, args.format, args.hide)
