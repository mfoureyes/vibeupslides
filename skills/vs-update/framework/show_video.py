# -*- coding: utf-8 -*-
"""A whole slideshow as one video (MP4, H.264, 1920x1080, 30 fps): every slide plays its animations frame by frame,
then stands until its time is up. Time per slide: 5 s plus 1 s per 3 words, at least 8 and at most 26 s.
    python3 show_video.py deck.html out.mp4 --langs en,de
"""
import argparse, json, os, shutil, subprocess, tempfile
from playwright.sync_api import sync_playwright

FPS = 30
def seconds(words): return max(8, min(26, round(5 + words / 3)))

def render(deck, out, langs):
    tmp = tempfile.mkdtemp(prefix="vs_show_")
    segs, plan = [], []
    try:
        with sync_playwright() as p:
            b = p.chromium.launch()
            for lang in langs:
                pg = b.new_page(viewport={"width": 1920, "height": 1080})
                pg.goto("file://" + os.path.abspath(deck) + f"?lang={lang}&kiosk=99999&kiosklang=off#/1"); pg.wait_for_timeout(2500)
                n = pg.evaluate("document.querySelectorAll('#deck > .slide[lang=\"%s\"]').length" % lang)
                n = pg.evaluate("parseInt((document.querySelector('#cnt span,.cnt span')||{textContent:'/ 0'}).textContent.replace(/\\D/g,''))") or n
                for i in range(1, n + 1):
                    pg.evaluate(f"location.hash='#/{i}'"); pg.wait_for_timeout(500)
                    pg.evaluate("document.querySelectorAll('#deck > .slide.active .f').forEach(e=>e.classList.add('on'))")
                    pg.keyboard.press("r"); pg.wait_for_timeout(60)
                    end = pg.evaluate("""(()=>{window.__a=document.querySelector('#deck > .slide.active').getAnimations({subtree:true}).filter(a=>{const t=a.effect&&a.effect.getComputedTiming(); return t&&isFinite(t.endTime)});
                        __a.forEach(a=>a.pause()); return Math.max(0,...__a.map(a=>a.effect.getComputedTiming().endTime))})()""")
                    words = pg.evaluate("(document.querySelector('#deck > .slide.active').innerText||'').split(/\\s+/).filter(w=>/\\w/.test(w)).length")
                    anim = min(max(end / 1000, 0.5), 4.0); total = seconds(words)
                    d = os.path.join(tmp, f"{lang}_{i:03d}"); os.makedirs(d)
                    for k in range(int(anim * FPS) + 1):
                        pg.evaluate(f"__a.forEach(a=>a.currentTime={k * 1000 / FPS})")
                        pg.screenshot(path=os.path.join(d, f"f{k:04d}.png"))
                    seg = d + ".mp4"
                    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-framerate", str(FPS), "-i", os.path.join(d, "f%04d.png"),
                                    "-vf", f"tpad=stop_mode=clone:stop_duration={total - anim:.3f},format=yuv420p", "-t", str(total),
                                    "-c:v", "libx264", "-preset", "veryfast", "-crf", "20", "-r", str(FPS), seg], check=True)
                    shutil.rmtree(d); segs.append(seg); plan.append((lang, i, words, total))
                    print(lang, i, words, "words", total, "s", flush=True)
                pg.close()
            b.close()
        lst = os.path.join(tmp, "list.txt")
        open(lst, "w").write("".join(f"file '{s}'\n" for s in segs))
        subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-f", "concat", "-safe", "0", "-i", lst, "-c", "copy", "-movflags", "+faststart", out], check=True)
        json.dump(plan, open(os.path.splitext(out)[0] + "_plan.json", "w"))
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    print(out, os.path.getsize(out) // 1024 // 1024, "MB,", sum(x[3] for x in plan), "s")

if __name__ == "__main__":
    ap = argparse.ArgumentParser(); ap.add_argument("deck"); ap.add_argument("out"); ap.add_argument("--langs", default="en,de")
    a = ap.parse_args(); render(a.deck, a.out, a.langs.split(","))
