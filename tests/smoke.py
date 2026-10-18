"""Smoke test of the framework: workspace, brand library, master preview, deck build, and the deck in a browser.

    python3 tests/smoke.py        (needs Pillow and Playwright with Chromium in the Python that runs it)

Works in a temporary workspace and does not touch ~/vibeupslides.
"""
import json, os, subprocess, sys, tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FW = os.path.join(ROOT, "skills", "vs-update", "framework")
ws = tempfile.mkdtemp(prefix="vibeupslides_smoke_")
env = dict(os.environ, VIBEUPSLIDES_HOME=ws, VS_NO_VENV="1")
results = []
def ok(name, cond, info=""):
    results.append(bool(cond)); print("ok  " if cond else "FAIL", name, info if not cond else "")
def vs(*args, src=False):
    cli = os.path.join(FW, "vs.py") if src else os.path.join(ws, "vs.py")
    p = subprocess.run([sys.executable, cli, *args], env=env, capture_output=True, text=True)
    return p.returncode, p.stdout + p.stderr

code, out = vs("init", "--no-venv", src=True)
ok("init creates the workspace", code == 0 and os.path.exists(os.path.join(ws, "vs.py")) and os.path.isdir(os.path.join(ws, "framework", "masters")), out[-400:])

# a hand-written brand with a light accent, as the analysis would leave it
lib = os.path.join(ws, "library", "smoke"); os.makedirs(lib)
json.dump({"name": "Smoke Test", "lang": "fr", "confirmed": True,
           "colors": {"accent": "#C8F031", "on_accent": "#10140A", "ink": "#10140A", "deep": "#10140A", "on_deep": "#FFFFFF",
                      "muted": "#5E6657", "line": "#C9CEC2", "soft": "#F1F3EE", "ghost": "#E6E9E1", "paper": "#FFFFFF"},
           "shape": {"radius": 14, "motif": "block"}, "footer": {"right": "example.org"}}, open(os.path.join(lib, "brand.json"), "w"))
sys.path.insert(0, FW); os.environ["VIBEUPSLIDES_HOME"] = ws
import vs as cli
cli._scaffold("smoke")
ok("scaffold gives the brand its own masters, theme and style guide",
   len(os.listdir(os.path.join(lib, "masters"))) >= 20 and os.path.exists(os.path.join(lib, "theme.css")) and os.path.exists(os.path.join(lib, "styleguide.md")))

# a brand master and a theme rule must win over the defaults
p = os.path.join(lib, "masters", "statement.html"); t = open(p, encoding="utf-8").read()
open(p, "w", encoding="utf-8").write(t.replace('<div class="wedge narrow"></div>', '<div class="wedge narrow"></div><i class="smoke-mark"></i>'))
open(os.path.join(lib, "theme.css"), "a", encoding="utf-8").write("\n.smoke-mark{display:block;height:7px}\n")

code, out = vs("preview", "smoke")
ok("preview builds every master without overflow", code == 0 and "overflow: clean" in out, out[-600:])
ok("contact sheets written", os.path.exists(os.path.join(lib, "preview", "sheet_en_1.png")))
ok("the preview introduces itself on the brand's masters and says what each master is for",
   "1 bullets  (introduction)" in out and "3 cards  (introduction)" in out and 'data-about="One sentence that stands alone."' in open(os.path.join(lib, "preview.html"), encoding="utf-8").read()
   and "(introduction)" not in vs("preview", "smoke", "--no-intro")[1] and vs("preview", "smoke")[0] == 0, out[:400])
code, out = vs("masters", "smoke")
ok("catalog lists masters with slots", "cards  [brand]" in out and "timer  [framework]" in out and "items:" in out, out[:300])

code, out = vs("new", "demo", "--brand", "smoke", "--langs", "fr,de")
deck = {"title": "Smoke", "brand": "smoke", "langs": ["fr", "de"], "slides": [
    {"master": "cover", "title": {"fr": "Un <em>essai</em>", "de": "Ein <em>Test</em>"}, "lead": {"fr": "Sous-titre", "de": "Untertitel"}, "notes": {"fr": "Note", "de": "Notiz"}},
    {"master": "chapter", "number": 1, "title": {"fr": "Partie", "de": "Teil"}},
    {"master": "bullets", "title": {"fr": "Trois points", "de": "Drei Punkte"}, "bullets": ["A", "B", "C"], "step": True},
    {"master": "bars", "title": {"fr": "Chiffres", "de": "Zahlen"}, "source": "test", "rows": [{"label": "A", "value": 12400, "share": 100}, {"label": "B", "value": 3100, "share": 25}]},
    {"master": "timer", "kicker": "X", "minutes": 5, "heading": "{duration}", "steps": [{"n": "1", "title": "A", "text": "B"}], "facts": [{"label": "X", "value": "{duration}"}]},
    {"master": "quiz_choice", "question": {"fr": "Laquelle ?", "de": "Welche?"}, "answers": ["A", "B", "C"], "correct": 1, "explanation": "B."},
    {"master": "quiz_estimate", "question": {"fr": "Combien ?", "de": "Wie viele?"}, "number": 12400, "unit": "x"},
    {"master": "statement", "text": {"fr": "Une <em>phrase</em>.", "de": "Ein <em>Satz</em>."}},
    {"master": "closing", "title": {"fr": "Merci", "de": "Danke"}}]}
json.dump(deck, open(os.path.join(ws, "decks", "demo", "deck.json"), "w"))
code, out = vs("build", "demo")
html = os.path.join(ws, "decks", "demo", "Smoke.html")
ok("build runs clean in both languages", code == 0 and out.count("overflow: clean") == 2 and os.path.exists(html), out[-600:])
ok("build looks at every slide for legibility", out.count("legibility: clean") == 2, out[-900:])
th = os.path.join(lib, "theme.css"); keep_theme = open(th, encoding="utf-8").read()
open(th, "a", encoding="utf-8").write("\n.lead{font-size:12px!important;color:rgba(128,128,128,.1)!important}\n.slide h2{position:relative;left:-400px}\n")
code, out = vs("build", "demo", "--no-shots")
ok("type that is too small, text without contrast and text at the edge are reported with slide and text",
   "LEGIBILITY slide 1" in out and "type of 12 px" in out and "contrast 1." in out and '"Sous-titre"' in out and "at the edge of the slide" in out and "FIX THE LEGIBILITY" in out, out[-1200:])
open(th, "w", encoding="utf-8").write(keep_theme)
code, out = vs("build", "demo", "--handout", "--no-shots")
hand = open(os.path.join(ws, "decks", "demo", "Smoke_handout.html"), encoding="utf-8").read()
ok("handout drops the timer slide and reveals the quiz", code == 0 and 'class="slide dark tslide' not in hand and "qsolved" in hand)

from playwright.sync_api import sync_playwright
with sync_playwright() as p:
    br = p.chromium.launch(); ctx = br.new_context(viewport={"width": 1280, "height": 720}, accept_downloads=True)
    pg = ctx.new_page(); errors = []; pg.on("pageerror", lambda e: errors.append(str(e)))
    pg.goto("file://" + html); pg.wait_for_timeout(1500); ev = pg.evaluate
    ok("starts in the first language with nine slides", ev("document.documentElement.lang") == "fr" and ev("document.querySelectorAll('.slide:not(.off)').length") == 9)
    ok("brand tokens and motif", ev("getComputedStyle(document.documentElement).getPropertyValue('--accent').trim()") == "#C8F031" and ev("document.documentElement.dataset.motif") == "block")
    ok("light accent gets a readable text shade", ev("getComputedStyle(document.documentElement).getPropertyValue('--accent-text').trim()") != "#C8F031")
    ok("theme.css is applied", ev("getComputedStyle(document.querySelector('.smoke-mark')).height") == "7px")
    ok("the brand's master is used", ev("document.querySelectorAll('.smoke-mark').length") == 2)
    pg.keyboard.press("ArrowRight"); pg.keyboard.press("ArrowRight"); pg.wait_for_timeout(300)
    for _ in range(3): pg.keyboard.press("ArrowRight")
    ok("click steps", ev("location.hash") == "#/3" and ev("document.querySelectorAll('.slide.active .f.on').length") == 3)
    pg.keyboard.press("l"); pg.wait_for_timeout(500)
    ok("language switch", ev("document.documentElement.lang") == "de" and "Drei Punkte" in ev("document.querySelector('.slide.active h2').textContent"))
    pg.keyboard.press("l"); pg.wait_for_timeout(400)
    ev("location.hash='#/4'"); pg.wait_for_timeout(2600)
    num = lambda sel: ev(f"document.querySelector('.slide.active {sel}').textContent").replace(" ", " ").replace(" ", " ")
    ok("bars count up in the slide language", num(".mvalue") == "12 400", num(".mvalue"))
    ev("location.hash='#/5'"); pg.wait_for_timeout(600); pg.keyboard.press("t"); pg.wait_for_timeout(1500)
    st = ev("document.querySelector('.slide.active').vsTimer.status()")
    ok("timer runs", st["running"] and st["remaining"] < 300, str(st))
    ev("document.querySelector('.slide.active').vsTimer.finish()")
    ev("location.hash='#/6'"); pg.wait_for_timeout(600); pg.keyboard.press("a"); pg.wait_for_timeout(300)
    wrong = ev("document.querySelectorAll('.slide.active .qopt.qwrong').length"); pg.keyboard.press("b"); pg.wait_for_timeout(600)
    ok("quiz: wrong answer marked, right answer solves", wrong == 1 and ev("document.querySelector('.slide.active').vsQuiz.solved()"))
    ev("location.hash='#/7'"); pg.wait_for_timeout(600); pg.keyboard.press("a"); pg.wait_for_timeout(2600)
    ok("estimate counts up", num(".qnumber") == "12 400", num(".qnumber"))
    with pg.expect_download(timeout=60000) as dl: pg.keyboard.press("p")
    ok("PDF export from the deck", dl.value.suggested_filename == "Smoke_FR.pdf")
    with pg.expect_popup() as pop: pg.keyboard.press("m")
    w = pop.value; w.wait_for_timeout(800); before = ev("location.hash"); w.click("#m-forward"); pg.wait_for_timeout(400)
    ok("presenter view shows and drives the deck", w.evaluate("!!document.querySelector('#m-cur .slide')") and ev("location.hash") != before)
    ok("no script errors", not errors, str(errors[:3]))
    br.close()

# ---------------------------------------------------------------- video, embeds, scenes, present, pack
import shutil, signal, time, zipfile, http.client
ok("a deck without media stays one file", "this deck is a folder" not in out and not os.listdir(os.path.join(ws, "decks", "demo", "assets")))
md = os.path.join(ws, "decks", "media"); os.makedirs(os.path.join(md, "images")); os.makedirs(os.path.join(md, "demo")); os.makedirs(os.path.join(lib, "media"))
from PIL import Image
Image.new("RGB", (960, 540), "#224466").save(os.path.join(md, "images", "poster.png"))
open(os.path.join(md, "demo", "page.html"), "w").write("<!DOCTYPE html><html><body><h1 id='local'>local page</h1></body></html>")
FFMPEG = shutil.which("ffmpeg") or ("/opt/homebrew/bin/ffmpeg" if os.path.exists("/opt/homebrew/bin/ffmpeg") else None)
clip = os.path.join(md, "clip.webm")
if FFMPEG:      # two seconds of test picture with a tone, as VP8: the Chromium of Playwright has no H.264
    r = subprocess.run([FFMPEG, "-v", "error", "-y", "-f", "lavfi", "-i", "testsrc=size=320x180:rate=15", "-f", "lavfi", "-i", "sine=frequency=440",
                        "-t", "2", "-c:v", "libvpx", "-b:v", "150k", "-c:a", "libopus", clip], capture_output=True, text=True)
    if r.returncode != 0 or not os.path.exists(clip): FFMPEG = None
if FFMPEG: shutil.copy(clip, os.path.join(lib, "media", "lib.webm"))
else: print("skip the local video checks: ffmpeg is missing or cannot write VP8")

# a test scene of the brand with two steps, following the scene contract
sc = os.path.join(lib, "scenes", "two-step"); os.makedirs(sc)
os.makedirs(os.path.join(lib, "scenes", "half-done")); open(os.path.join(lib, "scenes", "half-done", "index.html"), "w").write("<html></html>")
Image.new("RGB", (960, 600), "#662244").save(os.path.join(sc, "poster.jpg"))
json.dump({"name": "two-step", "title": "Two Step", "category": "type", "use": "Test scene: a word and a counter.", "steps": 2, "loop": False, "online": False,
           "vars": {"--ts-accent": "accent", "--ts-font": "font_head"}, "config": {"label": "one word", "image": "an image"}, "sample": {"label": "Hello"},
           "notes": "Only for the smoke test.", "poster": "poster.jpg"}, open(os.path.join(sc, "scene.json"), "w"))
open(os.path.join(sc, "index.html"), "w").write("""<!DOCTYPE html>
<html lang="en"><head><meta charset="utf-8"><title>Two Step</title>
<style>:root{--ts-accent:#ff0000;--ts-font:serif} body{margin:0;background:#111;color:var(--ts-accent);font:80px var(--ts-font)} .vs-embedded .demo{display:none}</style></head>
<body><section class="demo">demo wrapper</section><div id="out"></div>
<script>
const CONFIG = {label: "default", image: ""};
if (window.VS_SCENE && window.VS_SCENE.config) Object.assign(CONFIG, window.VS_SCENE.config);
let step = 0; const show = () => { document.getElementById("out").textContent = CONFIG.label + " " + step; document.documentElement.dataset.step = step; }; show();
addEventListener("keydown", e => { if (e.target.closest("input")) return;
  if (["ArrowDown", "ArrowRight", "PageDown", " "].includes(e.key)) step = Math.min(2, step + 1);
  else if (["ArrowUp", "ArrowLeft", "PageUp"].includes(e.key)) step = Math.max(0, step - 1); show(); });
</script></body></html>""")
code, out = vs("scenes", "smoke")
ok("scenes lists the brand's scene with steps and skips unfinished folders", code == 0 and "two-step  [brand]" in out and "2 steps" in out and "works offline" in out and "half-done" not in out, out[:400])

YT = "dQw4w9WgXcQ"
mslides = [
    {"master": "cover", "title": "Media"},
    {"master": "video", "src": "clip.webm", "poster": "images/poster.png", "title": "Local clip", "start": 0.4},
    {"master": "video", "src": f"https://youtu.be/{YT}?t=30", "end": 45, "poster": "images/poster.png", "title": "Remote clip"},
    {"master": "embed", "url": "demo/page.html", "layout": "boxed", "title": "A local page", "caption": "Caption"},
    {"master": "scene", "scene": "two-step", "config": {"label": "Hallo", "image": "images/poster.png"}},
    {"master": "video", "src": "brand:media/lib.webm", "layout": "boxed", "title": "From the library", "autoplay": False, "muted": True},
    {"master": "video", "src": "nope.mp4", "title": "Missing"},
    {"master": "embed", "url": "https://example.org/", "allow": "autoplay; camera", "title": "Remote page"},
    {"master": "video", "src": "https://vimeo.com/76979871", "start": "1:05", "loop": True, "title": "Vimeo"},
    {"master": "scene", "scene": "two-step", "steps": 0, "name": "self-playing", "title": "self-playing", "config": {"label": "Loop"}},
    {"master": "closing", "title": "End"}]
if not FFMPEG: mslides = [s for s in mslides if s.get("src") not in ("clip.webm", "brand:media/lib.webm")]
at = lambda title: 1 + next(i for i, s in enumerate(mslides) if s.get("title") == title or s.get("scene") == title)
json.dump({"title": "Media", "brand": "smoke", "langs": ["en"], "slides": mslides}, open(os.path.join(md, "deck.json"), "w"))
code, out = vs("build", "media")
mhtml = os.path.join(md, "Media.html"); mtext = open(mhtml, encoding="utf-8").read() if os.path.exists(mhtml) else ""
ok("media deck builds clean and says it is a folder", code == 0 and "overflow: clean" in out and "this deck is a folder" in out and "needs to be online" in out, out[-900:])
ok("missing file and refused permission give warnings", "WARNING: video not found: nope.mp4" in out and "not granted to the page: camera" in out, out[-900:])
sys.path.insert(0, FW)
import media as M
boxes = M.scan(mtext); by = lambda **kw: [b for b in boxes if all(b.get(k) == v for k, v in kw.items())]
yt = by(provider="youtube")[0]
ok("YouTube link becomes the privacy-friendly embed with start and end",
   yt["embed"].startswith(f"https://www.youtube-nocookie.com/embed/{YT}?") and "start=30" in yt["embed"] and "end=45" in yt["embed"] and "autoplay=1" in yt["embed"]
   and yt["url"] == f"https://www.youtube.com/watch?v={YT}&t=30s" and yt.get("nofile") is True, str(yt))
vm = by(provider="vimeo")[0]
ok("Vimeo link becomes the player address", vm["embed"].startswith("https://player.vimeo.com/video/76979871?dnt=1") and "loop=1" in vm["embed"] and vm["embed"].endswith("#t=65s"), str(vm))
ex = by(embed="https://example.org/")[0]
ok("embeds are sandboxed without top navigation and get a conservative allow list",
   all("allow-scripts" in b["sandbox"] and "top-navigation" not in b["sandbox"] for b in boxes if b["media"] != "video") and ex["allow"] == "fullscreen; autoplay"
   and by(media="scene")[0]["sandbox"] == "allow-scripts" and by(embed="demo/page.html")[0]["sandbox"] == "allow-scripts", str(ex))
if FFMPEG:
    ok("video is linked, not embedded; library file is copied into assets/", 'data-src="clip.webm"' in mtext and 'data-src="assets/lib.webm"' in mtext
       and os.path.exists(os.path.join(md, "assets", "lib.webm")) and len(mtext) < 3_000_000 and "video/webm;base64" not in mtext)
spage = os.path.join(md, by(media="scene")[0]["embed"]); stext = open(spage, encoding="utf-8").read() if os.path.exists(spage) else ""
ok("scene is copied with tokens, config, embedded class and key adapter",
   'class="vs-embedded"' in stext and "--ts-accent:#C8F031" in stext and '"label": "Hallo"' in stext and "scene-key" in stext
   and stext.index("window.VS_SCENE=") < stext.index("const CONFIG") and '"image": "media/' in stext and len(os.listdir(os.path.join(os.path.dirname(spage), "media"))) == 1, stext[:600])

with sync_playwright() as p:
    br = p.chromium.launch(); ctx = br.new_context(viewport={"width": 1280, "height": 720})
    pg = ctx.new_page(); errors = []; pg.on("pageerror", lambda e: errors.append(str(e)))
    pg.on("console", lambda m: errors.append("console: " + m.text) if m.type == "error" and "ERR_" not in m.text else None)
    pg.goto("file://" + mhtml); pg.wait_for_timeout(1200); ev = pg.evaluate
    state = lambda: ev("(document.querySelector('.slide.active .mbox')||document.body).getAttribute('data-state')")
    def wait_state(want, ms=6000):
        try: pg.wait_for_function(f"(document.querySelector('.slide.active .mbox')||document.body).getAttribute('data-state')==={json.dumps(want)}", timeout=ms); return True
        except Exception: return False
    ok("no player exists before its slide is current", ev("document.querySelectorAll('.mlive').length") == 0)
    if FFMPEG:
        ev(f"location.hash='#/{at('Local clip')}'")
        ok("local video plays when its slide becomes current", wait_state("playing") and ev("!document.querySelector('.slide.active video').paused"), str(state()))
        ok("it starts at the start time", ev("document.querySelector('.slide.active video').currentTime") >= 0.4)
        pg.keyboard.press("k"); pg.wait_for_timeout(300)
        if not ev("document.querySelector('.slide.active video').paused"): pg.keyboard.press("k"); pg.wait_for_timeout(300)     # first K after a muted start turns the sound on
        ok("K pauses", ev("document.querySelector('.slide.active video').paused") and state() == "paused", str(state()))
        pg.keyboard.press("k")
        ok("K plays again", wait_state("playing"))
        with pg.expect_popup() as pop: pg.keyboard.press("m")
        w = pop.value; w.wait_for_timeout(700)
        ok("presenter view shows the poster and a control, no second player",
           w.evaluate("document.querySelectorAll('video,iframe').length") == 0 and w.evaluate("!!document.querySelector('#m-cur .mposter img')")
           and w.evaluate("document.getElementById('m-media').classList.contains('show')") and w.evaluate("document.getElementById('m-media').getAttribute('data-state')") == "playing")
        w.click("#m-v-toggle"); pg.wait_for_timeout(400)
        ok("presenter control pauses the video in the room", ev("document.querySelector('.slide.active video').paused") and w.evaluate("document.getElementById('m-media').getAttribute('data-state')") == "paused")
        w.click("#m-v-toggle")
        ok("and plays it again", wait_state("playing"))
        w.click("#m-forward"); pg.wait_for_timeout(500)
        ok("leaving pauses and rewinds", ev("(()=>{var v=document.querySelector('video.mlive');return v.paused&&Math.abs(v.currentTime-0.4)<0.05&&!v.parentNode.hasAttribute('data-state')})()"))
        w.evaluate("document.getElementById('m-close').click()"); pg.wait_for_timeout(300)
        ev(f"location.hash='#/{at('From the library')}'")
        ok("autoplay off waits with a play button", wait_state("idle") and ev("getComputedStyle(document.querySelector('.slide.active .mplay')).display") == "block")
        pg.click(".slide.active .mplay")
        ok("a click on the button plays", wait_state("playing"))
    ev(f"location.hash='#/{at('Remote clip')}'"); pg.wait_for_timeout(500)
    ok("YouTube in a file:// deck: poster, message and link instead of a player",
       state() == "file" and ev("document.querySelectorAll('.slide.active iframe').length") == 0 and ev("!!document.querySelector('.slide.active .mposter img')")
       and ev("document.querySelector('.slide.active .mnote a').href") == f"https://www.youtube.com/watch?v={YT}&t=30s" and ev("getComputedStyle(document.querySelector('.slide.active .mnote')).display") == "block", str(state()))
    ev(f"location.hash='#/{at('A local page')}'")
    ok("embed loads its page while the slide is current", wait_state("loaded") and any("local page" in (f.evaluate("document.body.innerText") or "") for f in pg.frames if f != pg.main_frame))
    ev(f"location.hash='#/{at('two-step')}'"); wait_state("loaded")
    frame = lambda: next((f for f in pg.frames if "assets/scenes/two-step/" in f.url), None)
    ok("the embed is unloaded, the scene is loaded", len(pg.frames) == 2 and frame() is not None and state() == "loaded")
    fe = frame().evaluate
    ok("scene runs embedded with the brand's colour and the deck's config",
       fe("document.documentElement.classList.contains('vs-embedded')") and fe("getComputedStyle(document.documentElement).getPropertyValue('--ts-accent').trim()") == "#C8F031"
       and fe("document.getElementById('out').textContent") == "Hallo 0" and fe("getComputedStyle(document.querySelector('.demo')).display") == "none")
    here = ev("location.hash"); pg.keyboard.press("ArrowRight"); pg.keyboard.press("ArrowRight"); pg.wait_for_timeout(300)
    ok("two forward presses stay on the slide and reach the scene", ev("location.hash") == here and fe("document.documentElement.dataset.step") == "2", fe("document.documentElement.dataset.step"))
    pg.keyboard.press("ArrowLeft"); pg.wait_for_timeout(200)
    ok("a back press goes back inside the scene", ev("location.hash") == here and fe("document.documentElement.dataset.step") == "1")
    pg.keyboard.press("r"); wait_state("loaded"); pg.wait_for_timeout(200)
    ok("R reloads the scene", frame().evaluate("document.documentElement.dataset.step") == "0")
    frame().click("#out"); pg.keyboard.press("ArrowDown"); pg.keyboard.press("ArrowDown"); pg.wait_for_timeout(300)       # the scene has the focus now
    ok("keys pressed inside the scene are counted by the deck", ev("location.hash") == here and frame().evaluate("document.documentElement.dataset.step") == "2")
    pg.keyboard.press("ArrowDown"); pg.wait_for_timeout(500)
    ok("the third press moves to the next slide and unloads the scene", ev("location.hash") == f"#/{at('two-step') + 1}" and frame() is None)
    ev(f"location.hash='#/{at('self-playing')}'"); wait_state("loaded")
    ev("window.__sent=0;(function(){var f=document.querySelector('.slide.active iframe.mlive'),w=f.contentWindow,o=w.postMessage;try{w.postMessage=function(){window.__sent++;return o.apply(w,arguments);};}catch(e){window.__sent=-1;}})()")
    zf = next(f for f in pg.frames if "assets/scenes/two-step/" in f.url); zf.click("#out"); pg.keyboard.press("PageDown"); pg.wait_for_timeout(300)
    inside = (ev("location.hash"), zf.evaluate("document.documentElement.dataset.step") if not zf.is_detached() else "gone")
    ev(f"location.hash='#/{at('self-playing')}'"); wait_state("loaded"); ev("window.focus()"); pg.mouse.click(5, 5); pg.keyboard.press("ArrowRight"); pg.wait_for_timeout(300)
    ok("a scene with steps 0 gets no key presses: forward moves straight on", ev("location.hash") == f"#/{at('self-playing') + 1}" and ev("window.__sent") <= 0
       and inside[0] == f"#/{at('self-playing') + 1}", str(inside) + str(ev("window.__sent")))
    ev(f"location.hash='#/{at('Missing')}'"); pg.wait_for_timeout(300)
    ok("a missing file shows a placeholder with the title", "Missing" in ev("document.querySelector('.slide.active .mph').textContent") and state() is None)
    ev(f"location.hash='#/{at('two-step')}'"); wait_state("loaded"); pg.keyboard.press("o"); pg.wait_for_timeout(500)
    ok("overview shows posters only and stops the scene", ev("document.querySelectorAll('#ov video,#ov iframe').length") == 0 and ev("document.querySelectorAll('#ov .mposter img').length") >= 2 and len(pg.frames) == 1)
    pg.keyboard.press("Escape"); pg.wait_for_timeout(300)
    with pg.expect_download(timeout=60000) as dl: pg.keyboard.press("p")
    ok("PDF export from a media deck", dl.value.suggested_filename == "Media_EN.pdf")
    xp = ctx.new_page(); xp.on("pageerror", lambda e: errors.append(str(e)))
    for title in (("Local clip",) if FFMPEG else ()) + ("two-step", "Remote clip"):
        xp.goto("file://" + mhtml + f"?export=1#/{at(title)}"); xp.wait_for_timeout(500)
        ok(f"export mode shows the poster, not a player ({title})", xp.evaluate("document.querySelectorAll('video,iframe').length") == 0 and len(xp.frames) == 1
           and xp.evaluate("(()=>{var i=document.querySelector('.slide.active .mposter img');return !!i&&i.naturalWidth>0&&getComputedStyle(i).visibility==='visible'})()"))
    ok("export mode names the address of a remote video", xp.evaluate("getComputedStyle(document.querySelector('.slide.active .murl')).display") == "block" and "youtube.com/watch" in xp.evaluate("document.querySelector('.slide.active .murl').textContent"))
    xp.close()

    # present: the same deck over http
    srv = subprocess.Popen([sys.executable, os.path.join(ws, "vs.py"), "present", "media", "--no-open"], env=env, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
    line = srv.stdout.readline(); url = line.strip().split(" ")[-1]
    ok("present serves the deck on 127.0.0.1", url.startswith("http://127.0.0.1:") and url.endswith("/Media.html"), line)
    port = int(url.split(":")[2].split("/")[0])
    def req(path, headers=None, host=None):
        c = http.client.HTTPConnection("127.0.0.1", port, timeout=5); c.putrequest("GET", path, skip_host=True); c.putheader("Host", host or f"127.0.0.1:{port}")
        for k, v in (headers or {}).items(): c.putheader(k, v)
        c.endheaders(); r = c.getresponse(); body = r.read(); c.close(); return r.status, r.getheader("Content-Range"), body
    outside = [req(x)[0] for x in ("/../demo/deck.json", "/%2e%2e/demo/deck.json", "/..%2fdemo%2fdeck.json", "/.hidden", "/demo/", "//etc/passwd")]
    os.symlink(os.path.join(ws, "decks", "demo", "deck.json"), os.path.join(md, "link.json"))
    ok("present serves nothing outside the deck folder", outside == [404] * 6 and req("/link.json")[0] == 404 and req("/deck.json")[0] == 200 and req("/Media.html", host="evil.example")[0] == 403, str(outside))
    os.remove(os.path.join(md, "link.json"))
    st, rng, body = req("/images/poster.png", {"Range": "bytes=10-19"})
    ok("present answers byte ranges", st == 206 and len(body) == 10 and rng.startswith("bytes 10-19/"), f"{st} {rng}")
    ctx.route("**/*youtube-nocookie.com/**", lambda r: r.fulfill(status=200, content_type="text/html", body="<html><body>player stand-in</body></html>"))
    hp = ctx.new_page(); hp.on("pageerror", lambda e: errors.append(str(e))); hp.goto(url + f"#/{at('Remote clip')}")
    try: hp.wait_for_selector(".slide.active iframe.mlive", timeout=6000, state="attached"); src = hp.evaluate("document.querySelector('.slide.active iframe.mlive').src")
    except Exception: src = ""
    ok("over http the YouTube slide gets the player with the right address",
       src.startswith(f"https://www.youtube-nocookie.com/embed/{YT}?") and "start=30" in src and "end=45" in src and f"origin=http%3A%2F%2F127.0.0.1%3A{port}" in src
       and "allow-top-navigation" not in hp.evaluate("document.querySelector('.slide.active iframe.mlive').getAttribute('sandbox')"), src)
    if FFMPEG:
        hp.evaluate(f"location.hash='#/{at('Local clip')}'")
        try: hp.wait_for_function("(()=>{var v=document.querySelector('.slide.active video');return v&&!v.paused&&v.currentTime>=0.4})()", timeout=6000); played = True
        except Exception: played = False
        ok("over http the local video plays from its start time", played)
    hp.evaluate(f"location.hash='#/{at('two-step')}'")
    try: hp.wait_for_function("(document.querySelector('.slide.active .mbox')||document.body).getAttribute('data-state')==='loaded'", timeout=6000)
    except Exception: pass
    hp.keyboard.press("ArrowRight"); hp.wait_for_timeout(300); hf = next((f for f in hp.frames if "assets/scenes/two-step/" in f.url), None)
    ok("over http the scene takes its steps", hf is not None and hf.evaluate("document.documentElement.dataset.step") == "1")
    hp.close()
    srv.send_signal(signal.SIGINT)
    try: rc = srv.wait(timeout=20); rest = srv.stdout.read()
    except subprocess.TimeoutExpired: srv.kill(); rc, rest = -1, ""
    ok("present stops cleanly on Ctrl-C and says what it is good for", rc == 0 and "stopped" in rest and "YouTube" in rest and "Traceback" not in rest, f"{rc} {rest[-300:]}")
    ok("no script errors with media", not errors, str(errors[:3]))
    br.close()

code, out = vs("pack", "media")
zp = os.path.join(ws, "decks", "media.zip"); names = zipfile.ZipFile(zp).namelist() if os.path.exists(zp) else []
want = ["media/Media.html", "media/demo/page.html", "media/assets/scenes/two-step/index.html", "media/assets/scenes/two-step/" + os.path.basename(spage)] + (["media/clip.webm", "media/assets/lib.webm"] if FFMPEG else [])
ok("pack zips the HTML with what it links and says the deck needs to be online",
   code == 0 and all(n in names for n in want) and "media/deck.json" not in names and not any("shots" in n for n in names) and "NEEDS TO BE ONLINE" in out and "youtube" in out, out + str(names))
code, out = vs("pack", "demo")
ok("pack of a deck without media: the HTML alone", code == 0 and "links no files" in out and "Runs offline" in out, out)

# ---------------------------------------------------------------- modes: one deck file, a version to present and a version to read
LL = lambda fr, de: {"fr": fr, "de": de}
wordy = "Une phrase bien trop longue pour une salle, que personne ne lira pendant que quelqu'un parle devant."
rdeck = {"title": "Modes", "brand": "smoke", "langs": ["fr", "de"], "slides": [
    {"master": "cover", "title": LL("Deux <em>versions</em>", "Zwei <em>Fassungen</em>"), "notes": LL("Saluer.", "Begrüßen.")},
    {"master": "chapter", "number": 1, "title": LL("Avant", "Vorher")},
    {"master": "bullets", "title": LL("Trois points", "Drei Punkte"), "bullets": ["A", "B", "C"], "step": True, "notes": LL("Note orale", "Sprechnotiz"),
     "read": LL(["Texte pour qui lit.", "Second paragraphe."], ["Text für Lesende.", "Zweiter Absatz."])},
    {"master": "bars", "title": LL("Chiffres", "Zahlen"), "rows": [{"label": "A", "value": 12, "share": 100}], "notes": LL("Montrer la barre.", "Balken zeigen.")},
    {"master": "timer", "kicker": "X", "minutes": 5, "heading": "{duration}"},
    {"master": "quiz_choice", "question": LL("Laquelle ?", "Welche?"), "answers": ["A", "B", "C"], "correct": 1, "explanation": "B.", "read": LL("La bonne est B.", "Richtig ist B.")},
    {"master": "statement", "text": LL("Une <em>pause</em>.", "Eine <em>Pause</em>."), "only": "live"},
    {"master": "chapter", "number": 2, "title": LL("Après", "Nachher")},
    {"master": "cards", "title": LL("Cartes", "Karten"), "items": [{"title": "A", "text": "B"}], "read": " ".join(["Ce texte est beaucoup trop long pour sa colonne."] * 40)},
    {"master": "bullets", "title": LL("Trop de mots", "Zu viele Worte"), "bullets": [wordy] * 4, "only": "live"},
    {"master": "table", "title": LL("Sources", "Quellen"), "head": ["A", "B"], "rows": [["1", "2"]], "only": "reading"},
    {"master": "closing", "title": LL("Merci", "Danke")}]}
rd = os.path.join(ws, "decks", "modes"); os.makedirs(rd)
json.dump(rdeck, open(os.path.join(rd, "deck.json"), "w"))
code, out = vs("titles", "modes")
seq = [l.split(None, 2) for l in out.split("[de]")[0].splitlines() if l[:3].strip().isdigit()]
ok("titles prints number, master and title per language, and says where a title is missing",
   code == 0 and out.index("[fr]") < out.index("[de]") and [s[0] for s in seq] == [str(i) for i in range(1, 13)] and seq[2][1:] == ["bullets", "Trois points"]
   and "Deux versions" in seq[0][2] and "(no title)" in seq[4][2] and "(live only)" in seq[9][2] and "Drei Punkte" in out.split("[de]")[1], out)
code, out = vs("build", "modes")
live = os.path.join(rd, "Modes.html"); lt = open(live, encoding="utf-8").read() if os.path.exists(live) else ""
ok("the main mode is live; the file carries both versions, each slide marked with the one it is for",
   code == 0 and 'data-mode="live"' in lt and 'class="read"' in lt and 'data-only="reading"' in lt and 'data-only="live"' in lt and "tslide" in lt and "rcontents" in lt, out[-600:])
with sync_playwright() as p:
    br = p.chromium.launch(); ctx = br.new_context(viewport={"width": 1280, "height": 720}, accept_downloads=True)
    pg = ctx.new_page(); errors = []; pg.on("pageerror", lambda e: errors.append(str(e)))
    pg.goto("file://" + live); pg.wait_for_timeout(1500); ev = pg.evaluate
    shown = "[...document.querySelectorAll('#deck > .slide:not(.off)')]"
    ok("shown live: reader text, the contents page and reading-only slides stay out, the timer stays in",
       ev(shown + ".length") == 11 and ev(shown + ".every(s=>!s.matches('.rcontents,.rpage')&&s.getAttribute('data-only')!=='reading')") and ev(shown + ".some(s=>s.matches('.tslide'))")
       and ev("!document.getElementById('mode-style')") and ev("[...document.querySelectorAll('.read')].every(r=>getComputedStyle(r).display==='none')"))
    pg.evaluate("window.vsGo(4)"); pg.wait_for_timeout(300); pg.keyboard.press("v"); pg.wait_for_timeout(1800)
    ok("the key V opens the reading version of the same file at the same slide",
       ev("document.documentElement.getAttribute('data-mode')") == "reading" and ev(shown + ".length") == 10 and ev("document.querySelector('#deck > .slide.active').getAttribute('data-n')") == "4"
       and ev("!!document.querySelector('#deck > .slide.active > .rt')"))
    pg.mouse.move(300, 300); pg.mouse.move(420, 380); pg.wait_for_timeout(200); pg.click("#ctl [data-act=pdf]"); pg.wait_for_timeout(200)
    with pg.expect_download(timeout=120000) as dl: pg.click("#xmenu [data-x=live]")
    pg.wait_for_timeout(800)
    ok("the export menu offers both versions; the other one is opened and exported", dl.value.suggested_filename == "Modes_FR.pdf" and ev("document.documentElement.getAttribute('data-mode')") == "live")
    pg.keyboard.press("d"); pg.wait_for_timeout(300)
    dark = ev("(()=>{var s=document.querySelector('#deck > .slide.active');return [s.classList.contains('vs-dk'),getComputedStyle(s).backgroundColor,getComputedStyle(document.querySelector('#deck > .slide.dark')).backgroundColor]})()")
    ok("the key D gives light slides the deep colour and D again takes it back", dark[0] and dark[1] == dark[2], str(dark))
    pg.keyboard.press("d"); pg.wait_for_timeout(200)
    light = ev("document.querySelector('#deck > .slide.active').classList.contains('vs-dk')")
    pg.keyboard.press("a"); pg.wait_for_timeout(200)
    off = ev("document.documentElement.getAttribute('data-motion')")
    pg.evaluate("window.vsGo(3)"); pg.wait_for_timeout(60)
    still = ev("document.querySelector('#deck > .slide.active').getAnimations({subtree:true}).length")
    pg.keyboard.press("a"); pg.wait_for_timeout(200)
    ok("the key A switches the animations off and on", not light and off == "off" and still == 0 and ev("document.documentElement.getAttribute('data-motion')") == "standard", str([light, off, still]))
    ok("no script errors while switching", not errors, str(errors[:3]))
    br.close()
ok("the density report flags the wordy live slide and no other", "density (live, flag above 50 words)" in out and out.count("WORDY") == 2 and "WORDY page 10:" in out and "Trop de mots" in out, out)
code, out = vs("build", "modes", "--mode", "reading", "--pdf")
rhtml = os.path.join(rd, "Modes_reading.html"); rt = open(rhtml, encoding="utf-8").read() if os.path.exists(rhtml) else ""
ok("the other version is built next to it with its own name, sheets and PDFs",
   code == 0 and 'data-mode="reading"' in rt and os.path.exists(live) and os.path.exists(os.path.join(rd, "shots_reading", "sheet_fr_1.png")) and os.path.exists(os.path.join(rd, "shots", "sheet_fr_1.png"))
   and os.path.exists(os.path.join(rd, "Modes_reading_FR.pdf")) and os.path.exists(os.path.join(rd, "Modes_reading_DE.pdf")), out[-800:])
ok("the reading file carries both versions too", 'data-only="live"' in rt and "Sources" in rt and "Quellen" in rt)
ok("the build lists the slides whose reader text is still the speaker notes", 'rewrite them as prose in "read"): slides 1, 4 of deck.json' in out, out)
ok("reader text that is too long for its column is reported as overflow, in both languages", out.count("too long for its column") == 2 and "'slide': 8, 'reader_text'" in out and "FIX THE OVERFLOW" in out, out)
ok("the reading density counts the reader text against its own limit", "density (reading, flag above 250 words)" in out and "WORDY page 8 (slide 9 of deck.json)" in out and "reader text)" in out, out)
with sync_playwright() as p:
    br = p.chromium.launch(); ctx = br.new_context(viewport={"width": 1280, "height": 720}, accept_downloads=True)
    pg = ctx.new_page(); errors = []; pg.on("pageerror", lambda e: errors.append(str(e)))
    pg.goto("file://" + rhtml); pg.wait_for_timeout(1500); ev = pg.evaluate
    A = "#deck > .slide.active"; txt = lambda sel: ev(f"(document.querySelector({json.dumps(A + ' ' + sel)})||{{textContent:''}}).textContent")
    ok("reading deck: ten pages in the first language", ev("document.querySelectorAll('#deck > .slide:not(.off)').length") == 10 and ev("document.documentElement.lang") == "fr")
    ok("reading leaves out the timer and live-only slides and takes the reading-only one",
       ev("[...document.querySelectorAll('#deck > .slide:not(.off)')].every(s=>!s.matches('.tslide')&&s.getAttribute('data-only')!=='live')")
       and ev("[...document.querySelectorAll('#deck > .slide:not(.off)')].some(s=>s.getAttribute('data-only')==='reading'&&!s.matches('.rcontents'))"))
    ok("a slide with notes only shows them as reader text, marked as such", txt(".rt[data-from=notes] .rti") == "Saluer." and ev(f"!document.querySelector('{A} .rbar')"))
    pg.keyboard.press("ArrowRight"); pg.wait_for_timeout(300)
    rows = ev("[...document.querySelectorAll('#deck > .slide.active .rtoc a')].map(a=>a.textContent+'|'+a.getAttribute('href'))")
    ok("the contents page follows the cover and names every chapter with its page", ev(f"document.querySelector('{A}').classList.contains('rcontents')") and rows == ["01Avant3|#/3", "02Après7|#/7"], str(rows))
    pg.click(A + " .rtoc li:nth-child(2) a"); pg.wait_for_timeout(400)
    ok("a contents entry opens its chapter; the section bar marks it", ev("location.hash") == "#/7" and txt("h2") == "Après" and txt(".rbar .cur") == "Après"
       and ev(f"document.querySelectorAll('{A} .rbar a').length") == 2 and ev(f"!document.querySelector('{A} > .rt')"))
    ev("location.hash='#/4'"); pg.wait_for_timeout(400)
    box = ev(f"(()=>{{var p=document.querySelector('{A}'),s=p.querySelector('.rs > .slide').getBoundingClientRect(),t=p.querySelector('.rt').getBoundingClientRect(),w=p.getBoundingClientRect().width;"
             "return [s.width/w,s.height/s.width,(t.left-s.right)/w,t.width/w]})()")
    ok("a slide with reader text is shown reduced with the text in a column beside it",
       txt(".rti") == "Texte pour qui lit.Second paragraphe." and 0.55 < box[0] < 0.68 and abs(box[1] - 9 / 16) < 0.01 and box[2] > 0.01 and box[3] > 0.22 and "Note orale" not in ev(f"document.querySelector('{A}').innerHTML"), str(box))
    ok("all click steps are visible and the page number stays", ev(f"[...document.querySelectorAll('{A} .f')].every(f=>getComputedStyle(f).opacity==='1')") and ev(f"document.querySelectorAll('{A} .f').length") == 3
       and txt("> .footer .nr") == "04" and txt(".rbar .cur") == "Avant")
    pg.keyboard.press("ArrowRight"); pg.wait_for_timeout(300)
    ok("one forward press moves one page, there are no steps to click through", ev("location.hash") == "#/5" and txt(".rti") == "Montrer la barre.")
    pg.keyboard.press("ArrowRight"); pg.wait_for_timeout(300)
    ok("quiz questions show their answer", ev(f"!!document.querySelector('{A} .qslide.qopen .qopt.qright')") and "B." in txt(".qexplain") and txt(".rti") == "La bonne est B.")
    pg.keyboard.press("l"); pg.wait_for_timeout(500)
    ok("language switch in a reading deck", ev("document.documentElement.lang") == "de" and txt(".rti") == "Richtig ist B." and txt(".rbar .cur") == "Vorher")
    pg.keyboard.press("l"); pg.wait_for_timeout(300); pg.keyboard.press("o"); pg.wait_for_timeout(600)
    ok("overview of a reading deck shows the pages", ev("document.querySelectorAll('#ov .th').length") == 10 and ev("document.querySelectorAll('#ov .th .rpage .rti').length") == 5)
    pg.keyboard.press("Escape"); pg.wait_for_timeout(300)
    with pg.expect_download(timeout=90000) as dl: pg.keyboard.press("p")
    ok("PDF export from a reading deck, and the deck stays at rest afterwards", dl.value.suggested_filename == "Modes_reading_FR.pdf" and ev("document.documentElement.classList.contains('export')"))
    ok("no script errors in the reading deck", not errors, str(errors[:3]))
    br.close()
rdeck["mode"] = "reading"; json.dump(rdeck, open(os.path.join(rd, "deck.json"), "w"))
code, out = vs("build", "modes", "--no-shots"); code2, out2 = vs("build", "modes", "--mode", "live", "--no-shots")
lv = os.path.join(rd, "Modes_live.html"); lvt = open(lv, encoding="utf-8").read() if os.path.exists(lv) else ""
ok("with reading as the main mode the plain build is the reading version and --mode live builds the other one",
   code == 0 and code2 == 0 and 'data-mode="reading"' in open(live, encoding="utf-8").read() and 'data-mode="live"' in lvt and "tslide" in lvt and "Une <em>pause</em>" in lvt, out2[-500:])
ok("built live, reader text serves as speaker notes where there are none", '<aside class="notes"><p>La bonne est B.</p></aside>' in lvt and '<aside class="notes">Note orale</aside>' in lvt)
code, out = vs("build", "modes", "--mode", "print")
ok("an unknown mode is refused", code != 0 and "live, reading" in out, out)


# builds on forward presses, a counting figure, the ring on a number, media boxes, photo edges
import re as _re
def sample(m):
    return dict(json.loads(_re.match(r"<!--vs (.*?) -->", open(os.path.join(FW, "masters", m + ".html"), encoding="utf-8").read(), _re.S).group(1))["sample"], master=m)
bd = os.path.join(ws, "decks", "builds"); os.makedirs(os.path.join(bd, "images"))
from PIL import Image
rim = Image.linear_gradient("L").rotate(90).resize((1200, 800)).convert("RGB").point(lambda v: v // 2); rim.paste((255, 255, 255), (0, 0, 1200, 5)); rim.save(os.path.join(bd, "images", "rim.png"))
json.dump({"title": "Builds", "brand": "smoke", "langs": ["en"], "slides": [
    {"master": "cover", "title": "Builds"},
    dict(sample("big_number"), value="1,240", unit=""),
    sample("figure"), sample("phases"), sample("timeline"), dict(sample("timeline"), step=False),
    {"master": "video", "layout": "boxed", "title": "Film"}, {"master": "embed", "layout": "boxed", "title": "Page"},
    {"master": "gallery", "title": "Photos", "items": [{"photo": "images/rim.png", "title": "A", "text": "a"}, {"photo": "images/rim.png", "title": "B", "text": "b"}, {"photo": "images/rim.png", "title": "C", "text": "c"}]},
]}, open(os.path.join(bd, "deck.json"), "w"))
code, out = vs("build", "builds", "--no-shots")
ok("a deck with charts, schedule, phases and media builds", code == 0 and "overflow: clean" in out, out[-600:])
with sync_playwright() as p:
    br = p.chromium.launch(); pg = br.new_page(viewport={"width": 1280, "height": 720}); errors = []; pg.on("pageerror", lambda e: errors.append(str(e)))
    pg.goto("file://" + os.path.join(bd, "Builds.html")); pg.wait_for_timeout(1500); ev = pg.evaluate; A = "#deck > .slide.active"
    key = lambda k, ms=350: (pg.keyboard.press(k), pg.wait_for_timeout(ms))
    key("ArrowRight", 120); mid = ev(f"document.querySelector('{A} .mcountup').textContent"); pg.wait_for_timeout(3100); end = ev(f"document.querySelector('{A} .mcountup').textContent")
    ok("a big number counts up to its value within three seconds and keeps its separator", mid != "1,240" and int(mid.replace(",", "")) < 1240 and end == "1,240", str([mid, end]))
    key("ArrowRight", 2600)
    ring = ev(f"""(()=>{{const b=document.querySelector('{A} .mcol.mk b'),r=document.createRange();r.selectNodeContents(b);const t=r.getBoundingClientRect(),x=b.getBoundingClientRect(),a=getComputedStyle(b,'::after');
        return [Math.abs((t.left+t.width/2)-(x.left+x.width/2)),Math.abs((t.top+t.height/2)-(x.top+x.height/2)),a.translate,a.boxSizing,a.left,a.top,x.width,x.height]}})()""")
    ok("the ring of a marked column is centred on its number", ring[0] < 1 and ring[1] < 1.5 and ring[2] == "-50% -50%" and ring[3] == "border-box"
       and abs(float(ring[4][:-2]) - ring[6] / 2 * 1920 / 1280) < 1 and abs(float(ring[5][:-2]) - ring[7] / 2 * 1920 / 1280) < 1, str(ring))
    key("ArrowRight", 1500)
    shown = lambda: ev(f"[...document.querySelectorAll('{A} .vs-ph-head th')].slice(1).map(h=>getComputedStyle(h).opacity==='1'?1:0).join('')")
    s0 = shown(); cells0 = ev(f"document.querySelectorAll('{A} td.f.on').length"); key("ArrowRight", 600); s1 = shown(); cells1 = ev(f"document.querySelectorAll('{A} td.f.on').length")
    key("ArrowRight", 600); s2 = shown(); still = ev(f"document.querySelector('{A}').matches('.vs-phs')")
    ok("phases build one whole column per forward press, the first with the slide", (s0, s1, s2) == ("100", "110", "111") and cells0 == 0 and cells1 >= 2 and still, str([s0, s1, s2, cells0, cells1]))
    key("ArrowLeft", 400); back = shown(); key("ArrowRight", 300); key("ArrowRight", 600)
    bars = lambda: ev(f"[...document.querySelectorAll('{A} .mgbar')].map(b=>getComputedStyle(b).opacity==='1'?1:0).join('')")
    pts = lambda: ev(f"[...document.querySelectorAll('{A} .mgpoint')].every(b=>b.classList.contains('on'))")
    seq = [bars()]
    for i in range(4): key("ArrowRight", 300); seq.append(bars())
    p0 = pts(); key("ArrowRight", 300); p1 = pts(); on_tl = ev(f"document.querySelector('{A}').matches('.vs-tln')"); pend = ev(f"document.querySelectorAll('{A} .f:not(.on)').length")
    ok("a step back hides the last phase again", back == "110", back)
    ok("the schedule builds one bar per forward press, then all milestones together", seq == ["10000", "11000", "11100", "11110", "11111"] and not p0 and p1 and on_tl and pend == 0, str([seq, p0, p1, on_tl, pend]))
    key("ArrowRight", 2600)
    auto = ev(f"[document.querySelectorAll('{A} .f').length, document.querySelectorAll('{A} .mgbar').length, [...document.querySelectorAll('{A} .mgbar')].every(b=>getComputedStyle(b).opacity==='1')]")
    ok('with "step": false the schedule builds by itself', auto == [0, 5, True], str(auto))
    ratios = []
    for i in range(2):
        key("ArrowRight", 500); ratios.append(ev(f"(()=>{{const r=document.querySelector('{A} .mbox').getBoundingClientRect();return r.width/r.height}})()"))
    ok("boxed media boxes have the shape of a video", all(abs(r - 16 / 9) < .02 for r in ratios), str(ratios))
    key("ArrowRight", 600)
    top = ev(f"""(async()=>{{const im=document.querySelector('{A} figure img');await im.decode();const c=document.createElement('canvas');c.width=im.naturalWidth;c.height=im.naturalHeight;
        const x=c.getContext('2d');x.drawImage(im,0,0);const d=x.getImageData(c.width/2,0,1,3).data;return [d[0],d[1],d[2],d[4],d[5],d[6]]}})()""")
    ok("a thin white rim is cut off a photo", max(top) < 200, str(top))
    ok("no script errors in the builds deck", not errors, str(errors[:3]))
    br.close()

# entrances follow the reading order; previews in the brand's languages; the video with its title
od = os.path.join(ws, "decks", "order"); os.makedirs(od)
json.dump({"title": "Order", "brand": "smoke", "langs": ["en"], "slides": [
    {"master": "cover", "title": "Order"}, sample("summary"), sample("requirements"), sample("kpis"), sample("table"), sample("steps"),
    {"master": "terms", "title": "Terms", "sections": [{"head": "1", "text": "One."}, {"head": "2", "text": "Two."}]},
    dict(sample("video_title"), src=""),
]}, open(os.path.join(od, "deck.json"), "w"))
code, out = vs("build", "order", "--no-shots")
with sync_playwright() as p:
    br = p.chromium.launch(); pg = br.new_page(viewport={"width": 1280, "height": 720}); errors = []; pg.on("pageerror", lambda e: errors.append(str(e)))
    pg.goto("file://" + os.path.join(od, "Order.html")); pg.wait_for_timeout(1500); ev = pg.evaluate; A = "#deck > .slide.active"
    rows = lambda sel: ev(f"[...document.querySelectorAll('{A} {sel}')].map(e=>parseFloat(e.style.getPropertyValue('--i')))")
    pg.keyboard.press("ArrowRight"); pg.wait_for_timeout(200)
    c, pt, fa = rows(".vs-sum-ctx > div"), rows(".vs-sum-pts > div"), rows(".vs-sum-facts > div")
    ok("a summary enters row by row from top to bottom, each row together", code == 0 and len(set(c)) == 1 and len(set(pt)) == 1 and len(set(fa)) == 1 and c[0] < pt[0] < fa[0], str([c, pt, fa]))
    pg.keyboard.press("ArrowRight"); pg.wait_for_timeout(200)
    need, ans = rows(".vs-req-need"), rows(".vs-req-ans")
    ok("requirements stand first from top to bottom, then the answers in the same order", need == sorted(need) and ans == sorted(ans) and len(set(need)) == len(need) and max(need) < min(ans), str([need, ans]))
    pg.keyboard.press("ArrowRight"); pg.wait_for_timeout(200); k = rows(".kpi")
    pg.keyboard.press("ArrowRight"); pg.wait_for_timeout(200); tr = rows("tr.anim")
    pg.keyboard.press("ArrowRight"); pg.wait_for_timeout(200); st = rows(".step")
    pg.keyboard.press("ArrowRight"); pg.wait_for_timeout(200); auto = ev(f"[...document.querySelectorAll('{A} > .anim')].length")
    ok("figures in a row come together, table rows one after the other, steps of a sequence from left to right", len(k) >= 2 and len(set(k)) == 1 and tr == sorted(tr) and len(set(tr)) == len(tr) and st == sorted(st) and len(set(st)) == len(st), str([k, tr, st]))
    ok("a slide whose master marks no block gets its content as one block", auto == 1, str(auto))
    pg.keyboard.press("ArrowRight"); pg.wait_for_timeout(300)
    vt = ev(f"(()=>{{const s=document.querySelector('{A}'),b=s.querySelector('.mbox').getBoundingClientRect(),r=s.getBoundingClientRect(),h=s.querySelector('h2').getBoundingClientRect();return [h.bottom<=b.top,b.width/r.width,b.width/b.height,b.bottom<=r.bottom+1]}})()")
    ok("video_title: the title stands above the video, the video takes the room below in the shape of a video", vt[0] and vt[1] > .7 and abs(vt[2] - 16 / 9) < .02 and vt[3], str(vt))
    ok("no script errors in the order deck", not errors, str(errors[:3]))
    br.close()
bj = os.path.join(lib, "brand.json"); bd2 = json.load(open(bj)); bd2["langs"] = ["de", "en"]; json.dump(bd2, open(bj, "w"))
mp = os.path.join(lib, "masters", "bullets.html"); mt = open(mp, encoding="utf-8").read(); mm = _re.match(r"<!--vs (.*?) -->\n", mt, _re.S); mj = json.loads(mm.group(1))
mj["sample"]["title"] = {"de": "Deutscher <em>Titel</em>", "en": "English <em>title</em>"}; open(mp, "w", encoding="utf-8").write("<!--vs " + json.dumps(mj) + " -->\n" + mt[mm.end():])
code, out = vs("preview", "smoke"); pv = open(os.path.join(lib, "preview.html"), encoding="utf-8").read()
ok("the preview is built in the brand's languages, samples written per language switch, the others serve both",
   code == 0 and "overflow: clean" in out and 'lang="de"' in pv and 'lang="en"' in pv and "Deutscher <em>Titel</em>" in pv and "English <em>title</em>" in pv
   and os.path.exists(os.path.join(lib, "preview", "sheet_de_1.png")) and os.path.exists(os.path.join(lib, "preview", "sheet_en_1.png")), out[-500:])
code, out = vs("new", "twolang", "--brand", "smoke")
ok("a new deck starts with the brand's languages", code == 0 and json.load(open(os.path.join(ws, "decks", "twolang", "deck.json")))["langs"] == ["de", "en"], out[-300:])

# voice profile: measured from the brand's own texts, drafted as voice.md and rules, checked by every build
ok("scaffold drafts the voice profile", os.path.exists(os.path.join(lib, "voice.md")) and "## Before and after" in open(os.path.join(lib, "voice.md"), encoding="utf-8").read())
st = os.path.join(ws, "about.txt")
open(st, "w", encoding="utf-8").write("Über das Smoke Lab\n\n" + "Das Smoke Lab begleitet Teams von der ersten Idee bis zum Markt. Wir zeigen Ihnen, wie Sie in zwölf Wochen zu einem Prototyp kommen. "
    "Im Smoke Lab arbeiten Gründer:innen und Forscher:innen an einem Tisch. Sprechen Sie uns an, wenn Sie Ihr Vorhaben vorstellen möchten. Wir freuen uns auf Ihre Fragen.\n\n"
    "About the Smoke Lab\n\nThe Smoke Lab takes teams from the first idea to the market. We show you how to reach a prototype in twelve weeks. At the Smoke Lab founders and researchers share one table.\n")
code, out = vs("voice", "smoke", st, os.path.join(lib, "brand.json"))
vj = json.load(open(os.path.join(lib, "raw", "voice.json"), encoding="utf-8")); vr = json.load(open(bj)).get("voice") or {}
ok("voice measures the sample texts per language and drafts the rules",
   code == 0 and "sample text added" in out and "not a text file" in out and set(vj["langs"]) == {"de", "en"} and vj["langs"]["de"]["address"].get("Sie", 0) >= 3
   and vr.get("de", {}).get("address") == "Sie" and vr.get("de", {}).get("gender") == ":innen" and "Smoke Lab" in vr.get("terms", []) and vr.get("sentence_max"), out[-700:] + str(vr))
code, out = vs("set", "smoke", "voice.sentence_max=12", 'voice.avoid=["synergy => working together"]', "voice.exclamation=false")
vd = os.path.join(ws, "decks", "voiced"); os.makedirs(vd)
json.dump({"title": "Voiced", "brand": "smoke", "langs": ["de", "en"], "slides": [
    {"master": "cover", "title": {"de": "Wie wir im Smoke Lab arbeiten", "en": "How we work at the Smoke Lab"}, "lead": {"de": "Ein Überblick für Sie.", "en": "An overview."}},
    {"master": "bullets", "title": {"de": "Das smoke lab hilft dir!", "en": "Real synergy for every team"},
     "bullets": [{"de": "Gründer*innen finden hier Platz.", "en": "A place for founders."},
                 {"de": "Kurz.", "en": "This sentence is far too long for a slide because it goes on and on and never comes to an end at all."}]},
    {"master": "statement", "voice": False, "text": {"de": "Du schaffst das!", "en": "Synergy!"}}]}, open(os.path.join(vd, "deck.json"), "w"))
code, out = vs("build", "voiced", "--no-shots")
de = out[out.index("[de] voice"):out.index("[en] overflow")] if "[de] voice" in out and "[en] overflow" in out else ""; en = out[out.index("[en] voice"):] if "[en] voice" in out else ""
ok("a build reports what breaks the voice, per language, slide and slot",
   code == 0 and "slide 2 (bullets), title" in de and "fixed term is \"Smoke Lab\"" in de and "this brand says \"Sie\"" in de and "exclamation mark" in de and "slide 2 (bullets), bullets.1" in de and "\":innen\"" in de
   and "working together" in en and "bullets.2: sentence of" in en and "(limit 12)" in en, out[-1200:])
ok("a slide with voice false is left alone, a clean slide is not reported", "slide 3" not in de + en and "slide 1" not in de + en, de + en)
code, out = vs("voice", "smoke", "--check", "Wir zeigen Ihnen das Smoke Lab.", "--lang", "de")
ok("voice --check passes a sentence in the brand's voice", code == 0 and "voice: clean" in out, out)
code, out = vs("preview", "smoke")
ok("the preview checks the masters' samples against the voice", code == 0 and "voice:" in out, out[-400:])

# element library: icons of the brand on slides, by name
os.makedirs(os.path.join(lib, "elements", "icons"), exist_ok=True)
open(os.path.join(lib, "elements", "icons", "icon_01_energy.svg"), "w").write('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24"><path d="M13 2 4 14h7l-1 8 9-12h-7z" fill="currentColor"/></svg>')
code, out = vs("elements", "smoke")
ok("elements lists the brand's icons by the name a deck uses", code == 0 and "icons (1)" in out and "energy" in out and "icon_01_energy.svg" in out, out)
idk = os.path.join(ws, "decks", "icons"); os.makedirs(idk)
json.dump({"title": "Icons", "brand": "smoke", "langs": ["en"], "slides": [{"master": "cards", "title": "Cards", "items": [{"icon": "energy", "title": "A", "text": "One."}, {"icon": "nothere", "title": "B", "text": "Two."}]},
           {"master": "steps", "title": "Steps", "items": [{"icon": "icon_01_energy", "title": "A", "text": "One."}, {"title": "B", "text": "Two."}]}]}, open(os.path.join(idk, "deck.json"), "w"))
code, out = vs("build", "icons", "--no-shots"); ih = open(os.path.join(idk, "Icons.html"), encoding="utf-8").read() if code == 0 else ""
ok("an icon of the library stands on cards and steps, a name that is not there is reported", code == 0 and "overflow: clean" in out and ih.count('<div class="vs-ic"><svg class="el"') == 2 and "icon not found in the brand's library: nothere" in out, out[-500:])

# editing mode: the edit build marks where every slot's text stands, changes go back into deck.json
import edit as E, signal, socket, time as _time, urllib.request
ed = os.path.join(ws, "decks", "edited"); os.makedirs(ed)
edeck = {"title": "Edited", "brand": "smoke", "langs": ["de", "en"], "slides": [
    {"master": "cover", "kicker": "Abend", "title": {"de": "Ein <em>Titel</em>", "en": "A <em>title</em>"}, "lead": {"de": "Für Sie.", "en": "For you."}},
    {"master": "bullets", "title": {"de": "Drei Punkte", "en": "Three points"}, "bullets": {"de": ["Eins.", "Zwei.", "Drei."], "en": ["One.", "Two.", "Three."]}},
    {"master": "cards", "title": "Cards", "items": [{"title": "A", "text": {"de": "Erste.", "en": "First."}}, {"title": "B", "text": "Second."}]},
    {"master": "closing", "title": {"de": "Danke", "en": "Thanks"}}]}
json.dump(edeck, open(os.path.join(ed, "deck.json"), "w"))
ok("sanitize keeps inline emphasis and drops what a browser adds", E.sanitize('<div>Ein <em>Wort</em>&nbsp;<span style="x">mehr</span><script>x</script></div>') == "Ein <em>Wort</em> <span>mehr</span>".replace("<span>mehr</span>", "mehr") or E.sanitize('<div>Ein <em>Wort</em>&nbsp;<span style="x">mehr</span><script>x</script></div>') == "Ein <em>Wort</em> <span>mehr</span>", E.sanitize('<div>Ein <em>Wort</em>&nbsp;<span style="x">mehr</span><script>x</script></div>'))
dk = json.loads(json.dumps(edeck))
E.set_text(dk, 1, "title", "de", "Neu"); E.set_text(dk, 1, "kicker", "en", "Evening"); E.set_text(dk, 2, "bullets.2", "en", "Deux."); E.set_text(dk, 3, "items.2.text", "de", "Zweite.")
ok("a text is written in the language shown; a shared text becomes one per language",
   dk["slides"][0]["title"] == {"de": "Neu", "en": "A <em>title</em>"} and dk["slides"][0]["kicker"] == {"de": "Abend", "en": "Evening"}
   and dk["slides"][1]["bullets"]["en"][1] == "Deux." and dk["slides"][1]["bullets"]["de"][1] == "Zwei." and dk["slides"][2]["items"][1]["text"] == {"de": "Zweite.", "en": "Second."}, str(dk["slides"][:3]))
took = E.carry(dk, 1, "title", "de", "Neu"); wait = E.waiting(dk)
ok("a changed text is noted for correction and translation, the other language keeps its text; a figure is not noted",
   took == ["en"] and dk["slides"][0]["title"] == {"de": "Neu", "en": "A <em>title</em>"} and wait == [(1, {"path": "title", "from": "de", "to": ["en"], "text": "Neu"})]
   and E.carry(json.loads(json.dumps(edeck)), 1, "kicker", "de", "12") == [], str(dk["slides"][0]))
ok("the note becomes a line for the agent", "REVIEW slide 1, title: written in de by the user; correct spelling" in E.todo(dk)[0] and "translate it into en" in E.todo(dk)[0])
del dk["slides"][0]["edited"]
ok("voice findings can be given in German", "diese Marke" in " ".join(__import__("voice").check_text("Toll!", {"exclamation": False}, "de", ui="de")))
E.carry(dk, 2, "bullets.3", "de", "Drei."); E.item_op(dk, 2, "bullets.1", "delete"); E.item_op(dk, 2, "bullets.2", "up")
ok("what waits for translation stays on its item when the list changes", dk["slides"][1]["edited"][0]["path"] == "bullets.1" and dk["slides"][1]["bullets"]["de"][0] == "Drei.", str(dk["slides"][1]))
dk["slides"][1] = json.loads(json.dumps(edeck["slides"][1])); dk["slides"][1]["bullets"]["en"][1] = "Deux."
E.item_op(dk, 2, "bullets.3", "up"); E.item_op(dk, 3, "items.1.title", "duplicate"); at = E.slide_op(dk, 2, "later")
ok("list items move in every language, cards duplicate, slides move",
   dk["slides"][2]["bullets"] == {"de": ["Eins.", "Drei.", "Zwei."], "en": ["One.", "Three.", "Deux."]} and len(dk["slides"][1]["items"]) == 3 and at == 3 and dk["slides"][1]["master"] == "cards", str(dk["slides"][1:3]))
try: E.set_text(dk, 9, "title", "de", "x"); bad = False
except ValueError: bad = True
ok("a place that is not in the deck file is refused", bad)
sk = socket.socket(); sk.bind(("127.0.0.1", 0)); eport = sk.getsockname()[1]; sk.close()
srv = subprocess.Popen([sys.executable, os.path.join(ws, "vs.py"), "edit", "edited", "--port", str(eport), "--no-open"], env=env, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
base = f"http://127.0.0.1:{eport}"
for _ in range(60):
    try: urllib.request.urlopen(base + "/_edit.html", timeout=1).read(100); break
    except Exception: _time.sleep(.25)
def post(action, body, headers=None):
    rq = urllib.request.Request(f"{base}/__vs/{action}", data=json.dumps(body).encode(), headers=headers or {"Content-Type": "application/json"}, method="POST")
    try: return json.loads(urllib.request.urlopen(rq, timeout=20).read())
    except urllib.error.HTTPError as e: return {"ok": False, "code": e.code}
dj = lambda: json.load(open(os.path.join(ed, "deck.json"), encoding="utf-8"))
ok("the edit server refuses requests a foreign page could send", post("slide", {"n": 1, "op": "delete"}, {"Content-Type": "text/plain"}).get("code") == 403
   and post("slide", {"n": 1, "op": "delete"}, {"Content-Type": "application/json", "Origin": "http://evil.example"}).get("code") == 403 and len(dj()["slides"]) == 4)
with sync_playwright() as p:
    br = p.chromium.launch(); pg = br.new_page(viewport={"width": 1280, "height": 720}); errors = []; pg.on("pageerror", lambda e: errors.append(str(e)))
    pg.goto(base + "/"); pg.wait_for_timeout(1500); A = "#deck > .slide.active"
    ok("the edit page opens with its button in the button bar, the panel open and the texts marked",
       pg.locator("#ctl #vse-btn.on").count() == 1 and pg.locator("#ctl #vse").is_visible() and pg.locator(f"{A} [data-s=title]").count() == 1 and pg.locator(f"{A} [data-s=title] .mw").count() == 0
       and "export" not in pg.url)
    pg.locator("#vse-btn").click(); pg.wait_for_timeout(200)
    closed = not pg.locator("#ctl #vse").is_visible() and pg.locator(f"{A} [data-s=title]").get_attribute("contenteditable") is None
    pg.keyboard.press("e"); pg.wait_for_timeout(200)
    ok("the edit button closes and opens the editing; closed, the deck is as always", closed and pg.locator("#ctl #vse").is_visible() and pg.locator(f"{A} [data-s=title]").get_attribute("contenteditable") is not None)
    pg.locator("#vse > .row button.go").click(); pg.wait_for_timeout(800)
    ok("Done with nothing changed goes back to the plain deck and keeps the server", pg.locator("#vsend").count() == 0 and not pg.locator("#ctl #vse").is_visible()
       and srv.poll() is None and os.path.exists(os.path.join(ed, "Edited.html")))
    pg.keyboard.press("e"); pg.wait_for_timeout(200)
    pg.locator(f"{A} [data-s=title]").click(); pg.keyboard.press("Meta+ArrowDown" if sys.platform == "darwin" else "Control+End"); pg.keyboard.press("ArrowLeft"); pg.wait_for_timeout(200)
    stays = pg.evaluate(f"document.querySelector('{A}').getAttribute('data-n')") == "1"
    pg.keyboard.press("ArrowRight"); pg.keyboard.press("ArrowRight"); pg.wait_for_timeout(500)
    turned = pg.evaluate(f"document.querySelector('{A}').getAttribute('data-n')") == "2"
    pg.locator(f"{A} [data-s=title]").click(); pg.keyboard.press("PageUp"); pg.wait_for_timeout(500)
    ok("in a text the arrow keys move the cursor, at its end they turn the slide, Page Up always does", stays and turned and pg.evaluate(f"document.querySelector('{A}').getAttribute('data-n')") == "1")
    pg.locator(f"{A} [data-s=title]").click(); pg.keyboard.press("End"); pg.keyboard.type(" heute"); pg.keyboard.press("Enter"); pg.wait_for_timeout(700)
    tde = dj()["slides"][0]["title"]["de"]
    ok("typing into a title writes the deck file and keeps the accent word", tde in ("Ein <em>Titel heute</em>", "Ein <em>Titel</em> heute"), str(dj()["slides"][0]["title"]))
    ok("the other language keeps its title and the slide notes what waits for translation",
       dj()["slides"][0]["title"]["en"] == "A <em>title</em>" and dj()["slides"][0]["edited"] == [{"path": "title", "from": "de", "to": ["en"], "text": tde}]
       and "EN" in pg.locator("#vse-msg").inner_text(), str(dj()["slides"][0]) + pg.locator("#vse-msg").inner_text())
    pg.locator("#vse > .row button").nth(6).click(); pg.locator("#vse-notes textarea").first.fill("Erste Zeile.\n\nZweiter Absatz."); pg.locator("#vse-notes textarea").nth(1).fill("Für Leser."); pg.locator("#vse-notes button").click(); pg.wait_for_timeout(900)
    ok("speaker notes and the reader text are written from the panel", dj()["slides"][0]["notes"]["de"] == "Erste Zeile.<br><br>Zweiter Absatz." and dj()["slides"][0]["read"]["de"] == "Für Leser.", str(dj()["slides"][0]))
    pg.locator("#vse > .row button").nth(6).click(); pg.wait_for_timeout(300)
    with pg.context.expect_page() as pop: pg.keyboard.press("m")
    pw = pop.value; pw.wait_for_timeout(1500); nb = pw.locator("#m-npt")
    shows = "Zweiter Absatz." in nb.inner_text() and nb.get_attribute("contenteditable") == "true"
    nb.click(); pw.keyboard.press("End"); pw.keyboard.type(" sofort"); pw.locator("#m-l-notes").click(); pw.wait_for_timeout(900)
    ok("notes written in the presenter view are saved and stand on the slide", shows and dj()["slides"][0]["notes"]["de"].endswith("sofort")
       and "sofort" in pg.evaluate("document.querySelector('#deck > .slide.active > .notes').textContent") and "sofort" in nb.inner_text(), str(dj()["slides"][0].get("notes")))
    pw.close(); pg.wait_for_timeout(300)
    pg.locator(f"{A} [data-s=lead]").click(); pg.keyboard.press("End"); pg.keyboard.type(" Mehr"); pg.keyboard.press("Escape"); pg.wait_for_timeout(400)
    ok("Escape discards what was typed", dj()["slides"][0]["lead"]["de"] == "Für Sie." and pg.locator(f"{A} [data-s=lead]").inner_text().strip() == "Für Sie.")
    pg.locator(f"{A} [data-s=lead]").click(); pg.keyboard.press("End"); pg.keyboard.type(" " + "Wort " * 400); pg.wait_for_timeout(400)
    warn = pg.locator("#vse-msg.warn").count(); marked = pg.locator(f"{A} [data-s=lead].vs-over").count(); lineon = pg.locator("#vsl.on").count(); pg.keyboard.press("Escape"); pg.wait_for_timeout(300)
    ok("text that runs off the slide is flagged while typing, the text and the line it crosses are marked", warn == 1 and marked == 1 and lineon == 1
       and pg.locator("#vse-msg.warn").count() == 0 and pg.locator("#deck .vs-over").count() == 0 and pg.locator("#vsl.on").count() == 0, str([warn, marked, lineon]))
    pg.locator("#vse > .row button").nth(5).click(); pg.wait_for_timeout(500); fields = pg.locator("#vse-pick .list button b").all_inner_texts()
    pg.locator("#vse-pick .list button", has_text="logo").first.click() if False else None
    pg.locator("#vse > .row button").nth(4).click(); pg.wait_for_timeout(500); offered = pg.locator("#vse-pick .list button b").all_inner_texts()
    pg.locator("#vse-pick .list button").filter(has=pg.locator("b", has_text="Statement")).first.click(); pg.wait_for_timeout(1800)
    ok("a new slide from a master is inserted after the one shown, with the master's sample text",
       len(offered) > 15 and [x["master"] for x in dj()["slides"]][:2] == ["cover", "statement"] and dj()["slides"][1].get("text") and pg.evaluate(f"document.querySelector('{A}').getAttribute('data-n')") == "2", str(offered[:6]))
    pg.once("dialog", lambda d: d.accept()); pg.locator("#vse > .row button").nth(3).click(); pg.wait_for_timeout(1800)
    pg.locator("#vse > .row button").nth(5).click(); pg.wait_for_timeout(500); fields = pg.locator("#vse-pick .list button b").all_inner_texts()
    if "kicker" in fields: pg.locator("#vse-pick .list button").filter(has=pg.locator("b", has_text="kicker")).first.click(); pg.wait_for_timeout(1800)
    ok("a field the slide does not use yet can be added and is then open for typing", "kicker" in fields and dj()["slides"][1].get("kicker") and pg.locator(f"{A} [data-s=kicker]").count() == 1, str(fields))
    pg.keyboard.press("Meta+z" if sys.platform == "darwin" else "Control+z"); pg.wait_for_timeout(1800); pg.keyboard.press("ArrowLeft"); pg.wait_for_timeout(400)
    pg.keyboard.press("ArrowRight"); pg.wait_for_timeout(400)
    pg.locator(f"{A} [data-s='bullets.3']").click(); pg.wait_for_timeout(200); pg.locator("#vsi button").nth(0).click(); pg.wait_for_timeout(1800)
    ok("a list item moves up in both languages and the page comes back to the slide", dj()["slides"][1]["bullets"] == {"de": ["Eins.", "Drei.", "Zwei."], "en": ["One.", "Three.", "Two."]}
       and pg.evaluate(f"document.querySelector('{A}').getAttribute('data-n')") == "2", str(dj()["slides"][1]["bullets"]))
    pg.locator("#vse > .row button").nth(2).click(); pg.wait_for_timeout(1800)
    ok("duplicating a slide adds it after the one shown", [x["master"] for x in dj()["slides"]] == ["cover", "bullets", "bullets", "cards", "closing"] and pg.evaluate(f"document.querySelector('{A}').getAttribute('data-n')") == "3")
    pg.keyboard.press("Meta+z" if sys.platform == "darwin" else "Control+z"); pg.wait_for_timeout(1800)
    ok("undo takes the last change back", len(dj()["slides"]) == 4 and len(os.listdir(os.path.join(ed, ".history", "redo"))) == 1)
    ok("no script errors on the edit page", not errors, str(errors[:3]))
    pg.locator("#vse > .row button.go").click(); pg.wait_for_timeout(800)
    ok("Done ends the editing and tells the user that the page comes back by itself", pg.locator("#vsend .spin").count() == 1 and "von selbst" in pg.locator("#vsend").inner_text(), pg.locator("#vsend").inner_text())
    try: sout = srv.communicate(timeout=120)[0]
    except subprocess.TimeoutExpired: srv.kill(); sout = srv.communicate()[0]
    ok("after Done the command builds the deck with the changes, says what is to be corrected and translated and removes the edit page",
       "overflow:" in sout and "REVIEW slide 1, title: written in de by the user" in sout and "--reopen" in sout and os.path.exists(os.path.join(ed, "Edited.html"))
       and not os.path.exists(os.path.join(ed, "_edit.html")), sout[-900:])
    srv2 = subprocess.Popen([sys.executable, os.path.join(ws, "vs.py"), "edit", "edited", "--port", str(eport), "--reopen"], env=env, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
    for _ in range(40):
        pg.wait_for_timeout(500)
        if pg.locator("#vsend").count() == 0 and pg.locator("html.vs-editing #ctl #vse-btn").count() == 1 and "n=" in pg.url: break
    ok("when the editing is started again the waiting page reloads by itself", pg.locator("#vsend").count() == 0 and pg.locator("#ctl #vse").is_visible(),
       pg.url + str(pg.evaluate("[sessionStorage.getItem('vs-edit'), document.documentElement.className, !!document.getElementById('vsend'), !!document.getElementById('vse-btn')]")) + str(errors))
    br.close()
srv2.send_signal(signal.SIGTERM)
try: s2out = srv2.communicate(timeout=120)[0]
except subprocess.TimeoutExpired: srv2.kill(); s2out = ""
if not results[-1]: print("second edit server said:", s2out[:1500])
code, out = vs("pack", "edited")
ok("pack and present leave the edit page and the history out", code == 0 and "_edit" not in out and ".history" not in out, out)

# a session that only sees shared folders (Cowork): the workspace is found there, the Python environment stays outside
fake = tempfile.mkdtemp(prefix="vibeupslides_home_"); os.makedirs(os.path.join(fake, "mnt", "Docs")); os.makedirs(os.path.join(fake, "mnt", "outputs"))
boot = os.path.join(ROOT, "skills", "vs-create", "scripts", "bootstrap.py")
senv = {k: v for k, v in env.items() if k != "VIBEUPSLIDES_HOME"}; senv.update(HOME=fake, VIBEUPSLIDES_SANDBOX="1")
p = subprocess.run([sys.executable, boot], env=senv, capture_output=True, text=True)
ok("without a workspace in a shared folder the setup stops and says what to ask", p.returncode == 2 and "NO WORKSPACE YET" in p.stdout and "Docs" in p.stdout and "outputs" not in p.stdout.split("shared folders:")[1].split("\n")[0], p.stdout + p.stderr)
shared_ws = os.path.join(fake, "mnt", "Docs", "vibeupslides")
subprocess.run([sys.executable, os.path.join(FW, "vs.py"), "init", "--no-venv"], env=dict(senv, VIBEUPSLIDES_HOME=shared_ws), capture_output=True, text=True)
venv = os.path.join(fake, ".vibeupslides", "venv"); os.makedirs(os.path.join(venv, "bin")); os.symlink(sys.executable, os.path.join(venv, "bin", "python"))
p = subprocess.run([sys.executable, boot], env=senv, capture_output=True, text=True)
ok("the workspace in a shared folder is found again and remembers where updates come from", p.returncode == 0 and "workspace ready: " + shared_ws in p.stdout
   and open(os.path.join(shared_ws, ".source")).read() == os.path.realpath(FW), p.stdout + p.stderr)
ok("the four skills carry the same setup script", len({open(os.path.join(ROOT, "skills", n, "scripts", "bootstrap.py")).read() for n in ("vs-build", "vs-create", "vs-update", "vs-design")}) == 1)
open(os.path.join(venv, ".platform"), "w").write("other-system")
os.environ["HOME"], keep = fake, os.environ.get("HOME")
ok("a Python environment made on another system is passed over", cli._venv(shared_ws) == (None, None))
open(os.path.join(venv, ".platform"), "w").write(cli._platform())
ok("the environment in the home folder is used when the workspace has none", cli._venv(shared_ws)[0] == venv)
os.environ["HOME"] = keep
# a session that sees no folder of the user (Cowork in the cloud): temporary workspace, brands and decks travel as a backup file
code, out = vs("backup", "--out", fake)
bk = [f for f in os.listdir(fake) if f.startswith("vibeupslides-workspace") and f.endswith(".zip")]
ok("backup writes brands and decks into one file, without contact sheets", code == 0 and bk == ["vibeupslides-workspace.zip"] and "smoke" in out
   and not any("/preview/" in n or "/shots/" in n for n in __import__("zipfile").ZipFile(os.path.join(fake, bk[0])).namelist()), out)
os.environ["HOME"], keep = fake, os.environ.get("HOME"); os.environ["VIBEUPSLIDES_SANDBOX"] = "1"
ok("a workspace in a folder of the user is not temporary, one in the session is", not cli.temporary() if not os.environ.update(VIBEUPSLIDES_HOME=shared_ws) else 0)
os.environ["VIBEUPSLIDES_HOME"] = os.path.join(fake, "vibeupslides"); ok("a workspace in the session is temporary", cli.temporary())
os.environ.update(HOME=keep, VIBEUPSLIDES_HOME=ws); del os.environ["VIBEUPSLIDES_SANDBOX"]
cloud = tempfile.mkdtemp(prefix="vibeupslides_cloud_"); ups = os.path.join(cloud, "uploads"); os.makedirs(ups); shutil.copy(os.path.join(fake, bk[0]), ups)
cenv = {k: v for k, v in env.items() if k != "VIBEUPSLIDES_HOME"}; cenv.update(HOME=cloud, CLAUDE_CODE_REMOTE="true", VIBEUPSLIDES_UPLOADS=ups, VIBEUPSLIDES_OUTBOX=ups)
p = subprocess.run([sys.executable, boot], env=cenv, capture_output=True, text=True)
ok("without any folder of the user the workspace is set up in the session, says it is temporary and takes the uploaded backup",
   p.returncode == 0 and "TEMPORARY WORKSPACE" in p.stdout and "restored" in p.stdout and os.path.exists(os.path.join(cloud, "vibeupslides", "library", "smoke", "brand.json"))
   and os.path.exists(os.path.join(cloud, "vibeupslides", "decks", "demo", "deck.json")), p.stdout[-900:] + p.stderr[-600:])
import zipfile
evil = os.path.join(cloud, "evil.zip")
with zipfile.ZipFile(evil, "w") as z: z.writestr("library/../../escaped.txt", "x"); z.writestr("framework/vs.py", "x"); z.writestr("library/b/brand.json", "{}")
p = subprocess.run([sys.executable, os.path.join(cloud, "vibeupslides", "vs.py"), "restore", evil], env=cenv, capture_output=True, text=True)
ok("restore takes only brands and decks and nothing outside the workspace", "restored 1 files" in p.stdout and not os.path.exists(os.path.join(cloud, "escaped.txt"))
   and open(os.path.join(cloud, "vibeupslides", "framework", "vs.py")).read() != "x", p.stdout + p.stderr)
code, out = vs("doctor")
ok("doctor reports what the environment allows", code == 0 and "ok   workspace is writable" in out and "browser for checks" in out, out[-600:])
import re
descs = {n: re.search(r'(?m)^description: "?(.*?)"?$', open(os.path.join(ROOT, "skills", n, "SKILL.md"), encoding="utf-8").read()).group(1) for n in ("vs-build", "vs-create", "vs-update", "vs-design")}
ok("skill descriptions fit the 1024 characters a plugin allows", all(0 < len(d) <= 1024 for d in descs.values()), str({n: len(d) for n, d in descs.items()}))
man = json.load(open(os.path.join(ROOT, ".claude-plugin", "plugin.json")))
ok("the plugin manifest carries the framework's version", man["name"] == "vibeupslides" and man["version"] == open(os.path.join(FW, "VERSION")).read().strip())

# editing a deck that is opened as a file: the page keeps a journal, Done saves it, apply brings it into deck.json
code, out = vs("new", "filed", "--brand", "smoke", "--langs", "fr,de")
json.dump({"title": "Filed", "brand": "smoke", "langs": ["fr", "de"], "slides": [
    {"master": "cover", "title": {"fr": "Un titre", "de": "Ein Titel"}, "lead": {"fr": "Sous-titre", "de": "Untertitel"}},
    {"master": "statement", "text": {"fr": "Premiere phrase.", "de": "Erster Satz."}},
    {"master": "bullets", "title": {"fr": "Points", "de": "Punkte"}, "bullets": ["A", "B"]},
    {"master": "closing", "title": {"fr": "Merci", "de": "Danke"}}]}, open(os.path.join(ws, "decks", "filed", "deck.json"), "w"))
code, out = vs("build", "filed", "--no-shots")
page_file = os.path.join(ws, "decks", "filed", "Filed.html")
ok("a built deck carries its own editing", code == 0 and "VS_EDIT" in open(page_file, encoding="utf-8").read() and 'id="vse' not in open(os.path.join(lib, "preview.html"), encoding="utf-8").read().split("<script")[0]
   and "VS_EDIT" not in open(os.path.join(lib, "preview.html"), encoding="utf-8").read(), out[-300:])
edits = os.path.join(ws, "filed.edits.json")
with sync_playwright() as p:
    br = p.chromium.launch(); pg = br.new_page(viewport={"width": 1600, "height": 900}, accept_downloads=True)
    pg.add_init_script("window.showSaveFilePicker=undefined;window.showDirectoryPicker=undefined")
    pg.goto("file://" + page_file + "?lang=fr"); pg.wait_for_timeout(1200)
    closed = pg.evaluate("!!document.getElementById('vse-btn') && !document.documentElement.classList.contains('vs-editing')")
    words = pg.evaluate("document.querySelectorAll('#deck > .slide.active h1 .mw, #deck > .slide.active h2 .mw').length")
    pg.evaluate("document.getElementById('vse-btn').click()"); pg.wait_for_timeout(300)
    has_panel = closed and pg.evaluate("document.documentElement.classList.contains('vs-editing') && !document.querySelector('#deck > .slide.active [data-s=title] .mw')")
    pg.evaluate("""()=>{const e=document.querySelector('#deck > .slide.active [data-s="title"]'); e.focus(); e.innerHTML='Un titre neuf'; e.blur();}"""); pg.wait_for_timeout(300)
    pg.evaluate("location.hash='#/2'"); pg.wait_for_timeout(400)
    pg.evaluate("""()=>{const b=[...document.querySelectorAll('#vse button')]; b.find(x=>/back|hinten/.test(x.textContent)).click();}"""); pg.wait_for_timeout(200)
    pg.evaluate("location.hash='#/3'"); pg.wait_for_timeout(400)
    pg.on("dialog", lambda d: d.accept())
    pg.evaluate("""()=>{const b=[...document.querySelectorAll('#vse button')]; b.find(x=>/Delete|Löschen/.test(x.textContent)).click();}"""); pg.wait_for_timeout(200)
    marked = pg.evaluate("""[...document.querySelectorAll('#deck > .slide[lang=fr]:not(.off)')].map(s=>s.getAttribute('data-n')).join()+' '+document.getElementById('cnt').textContent.replace(/\\s+/g,'')""")
    pg.evaluate("location.hash='#/2'"); pg.wait_for_timeout(400)      # the bullets, now second: its list, a copy of the slide, a text in the copy, a new slide, and one step back
    pg.evaluate("""()=>{document.querySelector('#deck > .slide.active [data-s="bullets.2"]').focus();}"""); pg.wait_for_timeout(200)
    pg.evaluate("""()=>{[...document.querySelectorAll('#vsi button')].find(x=>x.textContent==='↑').click();}"""); pg.wait_for_timeout(300)
    listed = pg.evaluate("""['fr','de'].map(l=>[...document.querySelectorAll('#deck > .slide[data-n="3"][lang='+l+'] [data-s^="bullets."]')].map(e=>e.getAttribute('data-s')+'='+e.textContent).join()).join(' ')""")
    pg.evaluate("document.activeElement.blur()"); pg.wait_for_timeout(100)
    pg.evaluate("""()=>{const b=[...document.querySelectorAll('#vse button')]; b.find(x=>/^(Duplicate|Duplizieren)$/.test(x.textContent)).click();}"""); pg.wait_for_timeout(300)
    pg.evaluate("""()=>{const e=document.querySelector('#deck > .slide.active [data-s="title"]'); e.focus(); e.innerHTML='Copie'; e.blur();}"""); pg.wait_for_timeout(300)
    pg.evaluate("""()=>{const b=[...document.querySelectorAll('#vse button')]; b.find(x=>/^(New slide|Neue Folie)$/.test(x.textContent)).click();}"""); pg.wait_for_timeout(300)
    offered = pg.evaluate("document.querySelectorAll('#vse-pick .list button').length")
    pg.evaluate("""()=>{[...document.querySelectorAll('#vse-pick .list button')].find(b=>/statement/i.test(b.textContent)).click()}"""); pg.wait_for_timeout(400)
    fresh = pg.evaluate("""(()=>{const s=document.querySelector('#deck > .slide.active'); return [s.getAttribute('data-n'), !!s.querySelector('[data-s="text"]'), !!s.querySelector(':scope > .footer'), [...document.querySelectorAll('#deck > .slide[lang=fr]:not(.off)')].map(s=>s.getAttribute('data-n')).join(), [...document.querySelectorAll('#deck > .slide[lang=fr]:not(.off) .vs-credit')].length, !!document.querySelector('#deck > .slide[data-n="4"][lang=fr] > .vs-credit')];})()""")
    pg.evaluate("""()=>{const b=[...document.querySelectorAll('#vse button')]; b.find(x=>/^(Undo|Rückgängig)$/.test(x.textContent)).click();}"""); pg.wait_for_timeout(300)
    undone = pg.evaluate("""[...document.querySelectorAll('#deck > .slide[lang=fr]:not(.off)')].map(s=>s.getAttribute('data-n')).join()""")
    pg.evaluate("""()=>{const b=[...document.querySelectorAll('#vse button')]; b.find(x=>/^(Redo|Wiederholen)$/.test(x.textContent)).click();}"""); pg.wait_for_timeout(300)
    pg.reload(); pg.wait_for_timeout(1200)
    kept = pg.evaluate("""document.querySelector('#deck > .slide[data-n="1"][lang="fr"] [data-s="title"]').textContent""")
    again = pg.evaluate("""[...document.querySelectorAll('#deck > .slide[lang=fr]:not(.off)')].map(s=>s.getAttribute('data-n')).join()+' '+document.querySelector('#deck > .slide[data-n="5"][lang=fr] [data-s="title"]').textContent+' '+[...document.querySelectorAll('#deck > .slide[data-n="5"][lang=de] [data-s^="bullets."]')].map(e=>e.textContent).join('')""")
    raw = pg.evaluate("""[document.querySelectorAll('#deck > .slide[data-n="1"][lang="fr"] .vs-raw').length, document.getElementById('vse-flag').textContent]""")
    pg.evaluate("document.getElementById('vse-btn').click()"); pg.wait_for_timeout(300)      # editing closed: the changed title is animated word by word again
    resplit = pg.evaluate("""document.querySelectorAll('#deck > .slide[data-n="1"][lang="fr"] [data-s="title"] .mw').length""")
    pg.evaluate("document.getElementById('vse-btn').click()"); pg.wait_for_timeout(300)
    with pg.expect_download() as dl:
        pg.evaluate("""()=>{const b=[...document.querySelectorAll('#vse button')]; b.find(x=>/^(Done|Fertig)$/.test(x.textContent)).click();}""")
    dl.value.save_as(edits); said = pg.evaluate("(document.getElementById('vsend')||{}).textContent||''")
    br.close()
ok("a deck opened as a file can be edited: the pencil opens it, texts change on the page, a moved and a deleted slide show at once", has_panel and marked == "1,3,4 03/03" and kept == "Un titre neuf", f"{has_panel} {marked} {kept}")
ok("in the file a list item moves in every language, a slide is copied and the copy edited, a new slide comes from a master, undo takes it back, and the credit stays on the last slide",
   listed == "bullets.1=B,bullets.2=A bullets.1=B,bullets.2=A" and offered >= 10 and fresh == ["6", True, True, "1,3,5,6,4", 1, True] and undone == "1,3,5,4", f"{listed} | {offered} | {fresh} | {undone}")
ok("a reload brings all of it back from the journal", again == "1,3,5,6,4 Copie BA", again)
ok("a text the user typed is marked as unchecked on the slide and counted next to the pencil", raw[0] == 1 and "2" in raw[1], str(raw))      # the title and the title of the copy
ok("titles keep their word by word animation, before and after a change", words >= 2 and resplit == 3, f"{words} {resplit}")
ok("Done saves the changes into a file and says what to do with it", os.path.exists(edits) and len(json.load(open(edits))["ops"]) == 7 and "filed" in said, said)
code, out = vs("apply", "filed", edits)
fd = json.load(open(os.path.join(ws, "decks", "filed", "deck.json")))
ok("apply brings them into deck.json: the text in its language, the slide moved, the slide deleted, and what to review",
   code == 0 and fd["slides"][0]["title"]["fr"] == "Un titre neuf" and fd["slides"][0]["title"]["de"] == "Ein Titel" and [s["master"] for s in fd["slides"]] == ["cover", "bullets", "bullets", "statement", "closing"]
   and fd["slides"][1]["bullets"] == ["B", "A"] and fd["slides"][1]["title"]["fr"] == "Points" and fd["slides"][2]["title"] == {"fr": "Copie", "de": "Punkte"}
   and "REVIEW slide 1, title" in out and "REVIEW slide 3, title" in out and "7 of 7" in out, out[:900] + str([s["master"] for s in fd["slides"]]))
fd["slides"][0]["title"]["fr"] = "Un titre nouveau"; fd["slides"][0].pop("edited", None); fd["slides"][2].pop("edited", None); json.dump(fd, open(os.path.join(ws, "decks", "filed", "deck.json"), "w"))
vs("build", "filed", "--no-shots"); fh = open(os.path.join(ws, "decks", "filed", "Filed.html"), encoding="utf-8").read()
rp = json.loads(re.search(r"window\.VS_EDIT=(\{.*?\})</script>", fh).group(1).replace("<\\/", "</"))["report"]; rp = [r for r in rp if r["slide"] == 1]
ok("the deck built after the correction tells the user what became of their text", len(rp) == 1 and rp[0]["typed"] == "Un titre neuf" and rp[0]["now"] == "Un titre nouveau" and rp[0]["changed"] and rp[0]["langs"] == ["de"] and not rp[0]["pending"], str(rp))
code, out = vs("apply", "filed", edits)
kp = tempfile.mkdtemp(); kf = os.path.join(kp, "k.json")
json.dump({"vibeupslides_edits": 1, "deck": "filed", "ops": [{"a": "text", "n": 2, "lang": "fr", "path": "text", "html": "Exactement ainsi.", "ok": True}]}, open(kf, "w"))
code, outk = vs("apply", "filed", kf)
ok("a text the user released is not to be corrected, only translated, and a deck with open texts is not finished",
   "REVIEW slide 2, text: written in fr by the user; they want it exactly as it stands, do not correct it, translate it into de" in outk and "NOT FINISHED: 1 text(s)" in outk, outk[-700:])
fk = json.load(open(os.path.join(ws, "decks", "filed", "deck.json"))); fk["slides"][1].pop("edited", None); json.dump(fk, open(os.path.join(ws, "decks", "filed", "deck.json"), "w"))
ok("the same changes are not applied twice", code == 0 and "applied before" in out and len(json.load(open(os.path.join(ws, "decks", "filed", "deck.json")))["slides"]) == 5, out)
bj = os.path.join(lib, "brand.json"); bwas = open(bj).read(); bone = json.loads(bwas); bone["langs"] = ["fr"]; json.dump(bone, open(bj, "w"))
code, out = vs("new", "einsprachig", "--brand", "smoke")
open(bj, "w").write(bwas)
code2, out2 = vs("build", "edited", "--no-shots")      # de and en; the deck demo is fr and de
ok("a build says when a deck has no English version", "ENGLISH:" not in out2 and "ENGLISH:" in vs("build", "demo", "--no-shots")[1], out2[-300:])
ok("a new deck always has an English version", json.load(open(os.path.join(ws, "decks", "einsprachig", "deck.json")))["langs"] == ["fr", "en"], out)

# saving into the deck's folder (Chrome, Edge): the folder is named once, then every change goes into the presentation file itself
import http.server, threading, functools
fdir = os.path.join(ws, "decks", "filed"); vs("build", "filed", "--no-shots")
httpd = http.server.ThreadingHTTPServer(("127.0.0.1", 0), functools.partial(type("Q", (http.server.SimpleHTTPRequestHandler,), {"log_message": lambda *a: None}), directory=fdir))
threading.Thread(target=httpd.serve_forever, daemon=True).start()
with sync_playwright() as p:
    br = p.chromium.launch(); pg = br.new_page(viewport={"width": 1600, "height": 900})
    # a folder of the browser's own stands in for the folder the user would pick; it holds a copy of the presentation
    pg.add_init_script("""window.showDirectoryPicker=async()=>{const d=await navigator.storage.getDirectory(); const n=decodeURIComponent(location.pathname.split('/').pop());
      const sub=await (await d.getDirectoryHandle('decks',{create:true})).getDirectoryHandle('filed',{create:true});
      const h=await sub.getFileHandle(n,{create:true}); const w=await h.createWritable(); await w.write(await (await fetch(location.pathname)).text()); await w.close(); return d;}""")
    pg.goto(f"http://127.0.0.1:{httpd.server_address[1]}/Filed.html?lang=de"); pg.wait_for_timeout(1500)
    pg.evaluate("document.getElementById('vse-btn').click()"); pg.wait_for_timeout(300)
    pg.evaluate("""()=>{[...document.querySelectorAll('#vse button')].find(x=>/folder|Ordner/.test(x.textContent)).click();}"""); pg.wait_for_timeout(900)
    linked = pg.evaluate("""[...document.querySelectorAll('#vse button')].some(x=>x.classList.contains('good'))""")
    pg.evaluate("""()=>{const e=document.querySelector('#deck > .slide.active [data-s="title"]'); e.focus(); e.innerHTML='Gespeicherter Titel'; e.blur();}"""); pg.wait_for_timeout(1500)
    saved, log = pg.evaluate("""async()=>{const d=await (await (await navigator.storage.getDirectory()).getDirectoryHandle('decks')).getDirectoryHandle('filed'); const t=async n=>await (await (await d.getFileHandle(n)).getFile()).text(); return [await t('Filed.html'), await t('filed.edits.json')];}""")
    br.close()
httpd.shutdown()
again = os.path.join(ws, "Filed_saved.html"); open(again, "w", encoding="utf-8").write(saved)
with sync_playwright() as p:                                 # the saved file, opened somewhere else: no folder, nothing kept by the browser
    br = p.chromium.launch(); pg = br.new_page(viewport={"width": 1600, "height": 900})
    pg.goto("file://" + again + "?lang=de"); pg.wait_for_timeout(1300)
    shows = pg.evaluate("""document.querySelector('#deck > .slide[data-n="1"][lang="de"] [data-s="title"]').textContent""")
    br.close()
ok("with a folder above the deck named once, a change is saved into the presentation file under its own name and into the file of changes", linked and saved.count('id="vs-journal"') == 1 and "Gespeicherter Titel" in saved
   and json.loads(log)["ops"][0]["html"] == "Gespeicherter Titel", f"{linked} {saved.count('vs-journal')} {log[:200]}")
ok("the saved presentation shows the change wherever it is opened", shows == "Gespeicherter Titel", shows)

# every deck folder has the same parts; a deck made from another takes its sources and research along
open(os.path.join(ws, "decks", "filed", "sources", "brief.txt"), "w").write("the brief")
code, out = vs("new", "keynote", "--from", "filed")
kd = os.path.join(ws, "decks", "keynote"); kdeck = json.load(open(os.path.join(kd, "deck.json")))
ok("a new deck has sources, research and images, and one made from another deck takes its sources along",
   code == 0 and all(os.path.isdir(os.path.join(kd, x)) for x in ("sources", "research", "images")) and open(os.path.join(kd, "sources", "brief.txt")).read() == "the brief"
   and kdeck["brand"] == "smoke" and kdeck["from"] == "filed" and kdeck["langs"] == ["fr", "de"], out)

# what a brand's decks share: a slide and a fact live in the library, decks name them, refresh brings all decks up to date
code, out = vs("shared", "smoke", "slide", "thanks", "--from", "filed", "--slide", "3")
fdk = json.load(open(os.path.join(ws, "decks", "filed", "deck.json")))
ok("a slide of a deck becomes a shared slide of the brand", code == 0 and fdk["slides"][2] == {"shared": "thanks"} and os.path.exists(os.path.join(lib, "shared", "slides", "thanks.json")), out)
vs("shared", "smoke", "fact", "address", "Rue Exemple 1")
vs("shared", "smoke", "fact", "city", "Berlin-DE", "--lang", "de"); vs("shared", "smoke", "fact", "city", "Berlin-FR", "--lang", "fr")
fdk["slides"][1]["text"] = {"fr": "Venez: {{fact.address}}.", "de": "Kommen Sie: {{fact.address}}."}
fdk["slides"][0]["lead"] = "{{fact.city}}"
json.dump(fdk, open(os.path.join(ws, "decks", "filed", "deck.json"), "w"))
kdeck["slides"] = [{"shared": "thanks", "title": {"fr": "Merci a tous", "de": "Danke an alle"}}, {"master": "statement", "text": "{{fact.missing}}"}]
json.dump(kdeck, open(os.path.join(kd, "deck.json"), "w"))
code, out = vs("build", "filed", "--no-shots")
fh = open(os.path.join(ws, "decks", "filed", "Filed.html"), encoding="utf-8").read()
ok("a deck shows the shared slide and the facts, a fact by language in each language",
   code == 0 and "Rue Exemple 1" in fh and "Berlin-DE" in fh and "Berlin-FR" in fh and "Merci" in fh and "{{fact" not in fh and "shared with the brand's other decks: slides thanks, facts address, city" in out, out[:600])
code, out = vs("build", "keynote", "--no-shots")
kh = open(os.path.join(kd, "Keynote.html"), encoding="utf-8").read()
ok("a deck replaces single fields of a shared slide, and a fact that does not exist is reported", "Merci a tous" in kh and "SHARED: the fact 'missing'" in out, out[:600])
tl = json.load(open(os.path.join(lib, "shared", "slides", "thanks.json")))["title"]; sd = {"brand": "smoke", "langs": ["fr", "de"], "slides": [{"shared": "thanks"}]}
E.set_text(sd, 1, "title", "de", "Vielen Dank"); E.carry(sd, 1, "title", "de", "Vielen Dank")
ok("a text changed on a shared slide becomes the deck's own in that language, the other keeps the shared text, and the page and the agent are told",
   sd["slides"][0]["shared"] == "thanks" and sd["slides"][0]["title"] == {"fr": tl["fr"], "de": "Vielen Dank"} and "shared slide 'thanks'" in E.todo(sd)[0] and 'data-shared="thanks"' in fh, str(sd) + E.todo(sd)[0])
code, out = vs("shared", "smoke")
ok("shared lists slides and facts with the decks that use them", code == 0 and "thanks" in out and "filed, keynote" in out and "address" in out, out)
vs("shared", "smoke", "fact", "address", "Nouvelle Rue 9")
tj = os.path.join(lib, "shared", "slides", "thanks.json"); t = json.load(open(tj)); t["title"] = {"fr": "Au revoir", "de": "Auf Wiedersehen"}; json.dump(t, open(tj, "w"))
code, out = vs("refresh", "--brand", "smoke")
fh = open(os.path.join(ws, "decks", "filed", "Filed.html"), encoding="utf-8").read()
ok("refresh builds every deck that uses what changed and keeps the files from before",
   code == 0 and "Nouvelle Rue 9" in fh and "Au revoir" in fh and "Rue Exemple 1" not in fh and "filed: built again" in out and "keynote: built again" in out
   and os.path.isdir(os.path.join(ws, "decks", "filed", ".history", "built")), out)

kdk = json.load(open(os.path.join(kd, "deck.json"))); E.set_anim(kdk, 1, "all", True); json.dump(kdk, open(os.path.join(kd, "deck.json"), "w"))
code, out = vs("build", "keynote", "--no-shots"); kh = open(os.path.join(kd, "Keynote.html"), encoding="utf-8").read()
code2, out2 = vs("shared", "smoke", "push", "--from", "keynote", "--slide", "1")
ok("a shared slide changed for all presentations goes into the library, and the other decks that use it are named for one question",
   "SHARED: the user changed slide 1" in out and 'data-forall="1"' in kh and code2 == 0 and json.load(open(tj))["title"] == {"fr": "Merci a tous", "de": "Danke an alle"}
   and json.load(open(os.path.join(kd, "deck.json")))["slides"][0] == {"shared": "thanks"} and "ASK the user once: 1 other presentation(s) use it (filed)" in out2, out[-400:] + out2)

# the motion of the website as a set of the brand's own
import motion as MO
watched = {"scroll_reveal": {"found": True, "duration_s": .8, "easing": "cubic-bezier(.2,.8,.2,1)", "stagger_s": .06, "distance_px": 40,
           "samples": [{"kinds": ["rise", "fade"], "before": {"ty": 40, "tx": 0, "scale": 1, "blur": 0, "opacity": 0}}] * 3 + [{"kinds": ["scale", "fade"], "before": {"ty": 0, "tx": 0, "scale": .9, "blur": 0, "opacity": 0}}]}}
css = MO.site_set(watched, "https://example.org") or ""
ok("what was watched on the website becomes a motion set with its timing", '"name": "site"' in css and "rise by about 40 px" in css and '"duration": 0.8' in css and "cubic-bezier(.2,.8,.2,1)" in css
   and "@keyframes m-item{from{opacity:0;translate:0 calc(var(--mt)*1);scale:0.9}}" in css and all(f"@keyframes {r}{{" in css for r in MO.ROLES), css[:700])
ok("a website that shows no entrance yields no set", MO.site_set({"scroll_reveal": {"found": False}, "animations": {"in_use": []}}) is None)
MO.write_site_set(lib, watched, "https://example.org")
code, out = vs("motion", "smoke", "--set", "site")
ok("the brand's own set is listed with the framework's and can be chosen", code == 0 and "motion set of smoke: site" in out and "Copied from the website" in out and "* site" in out, out[:500])
code, out = vs("build", "demo", "--no-shots")
ok("a deck plays the set copied from the website", code == 0 and 'data-set="site"' in open(html, encoding="utf-8").read(), out[-300:])
vs("motion", "smoke", "--set", "rise")

# the movement of one presentation: the sets on its own slides, its own set and strength, click steps and strength per slide
code, out = vs("new", "moves", "--brand", "smoke", "--langs", "fr,de"); md = os.path.join(ws, "decks", "moves")
json.dump({"title": "Moves", "brand": "smoke", "langs": ["fr", "de"], "slides": [
    {"master": "cover", "title": {"fr": "Un titre", "de": "Ein Titel"}},
    {"master": "cards", "title": {"fr": "Cartes", "de": "Karten"}, "step": True, "move": "calm", "items": [{"title": "Un", "text": "a"}, {"title": "Deux", "text": "b"}, {"title": "Trois", "text": "c"}]},
    {"master": "bullets", "title": {"fr": "Points", "de": "Punkte"}, "bullets": ["A", "B"], "step": False},
    {"master": "closing", "title": {"fr": "Merci", "de": "Danke"}}]}, open(os.path.join(md, "deck.json"), "w"))
code, out = vs("motion", "--deck", "moves", "--set", "mask", "--level", "expressive"); code2, out2 = vs("build", "moves", "--no-shots")
mh = open(os.path.join(md, "Moves.html"), encoding="utf-8").read()
ok("a presentation can move in a set of its own and at its own strength", code == 0 and code2 == 0 and 'data-set="mask"' in mh and "setAttribute('data-motion','expressive')" in mh
   and json.load(open(os.path.join(md, "deck.json")))["motion_set"] == "mask", out + out2[-300:])
code, out = vs("motion", "--deck", "moves", "--compare"); cmp_file = os.path.join(md, "shots", "motion.html")
ok("the motion sets play side by side on the deck's own slides", code == 0 and os.path.exists(cmp_file) and "slides 1, 2, 3, 4 of moves" in out and '"cascade"' in open(cmp_file, encoding="utf-8").read(), out[-400:])
vs("motion", "--deck", "moves", "--set", "brand")
with sync_playwright() as p:
    br = p.chromium.launch(); pg = br.new_page(viewport={"width": 1600, "height": 900})
    look = lambda: pg.evaluate("(()=>{const s=document.querySelector('#deck > .slide.active'); return [...s.querySelectorAll('.f')].map(f=>f.getAttribute('data-o')+(f.classList.contains('on')?'+':'-')).join(' ');})()")
    pg.goto("file://" + os.path.join(md, "Moves.html") + "?lang=fr#/2"); pg.wait_for_timeout(1200); at0 = look()
    pg.keyboard.press("ArrowRight"); pg.wait_for_timeout(300); at1 = look()
    pg.keyboard.press("ArrowRight"); pg.keyboard.press("ArrowRight"); pg.wait_for_timeout(500)
    flat = pg.evaluate("(()=>{const s=document.querySelector('#deck > .slide.active'); return [location.hash, s.getAttribute('data-step'), s.querySelectorAll('.f').length, s.querySelectorAll('li.anim').length];})()")
    pg.evaluate("document.getElementById('vse-btn').click()"); pg.wait_for_timeout(300)
    pg.evaluate("""()=>{[...document.querySelectorAll('#vse button')].find(x=>/^(On click|Auf Klick)$/.test(x.textContent)).click()}"""); pg.wait_for_timeout(300)
    turned = pg.evaluate("(()=>{const s=document.querySelector('#deck > .slide.active'); return [s.getAttribute('data-step'), s.querySelectorAll('.f').length, s.querySelectorAll('.f.on').length];})()")
    pg.evaluate("sessionStorage.clear()"); pg.goto("file://" + os.path.join(md, "Moves.html") + "?mode=reading#/2"); pg.wait_for_timeout(1500)
    rd_pen = pg.evaluate("!!document.getElementById('vse-btn') && !document.getElementById('vse')"); pg.keyboard.press("e"); pg.wait_for_timeout(2000)
    rd_to = [pg.evaluate("document.documentElement.getAttribute('data-mode')"), pg.evaluate("document.documentElement.classList.contains('vs-editing')"), "mode=live" in pg.url]
    br.close()
ok("a slide builds up click by click when the deck says so, on any master, and arrives whole when it says no", at0 == "1- 2-" and at1 == "1+ 2-" and flat == ["#/3", "0", 0, 2] and 'data-move="calm"' in mh, f"{at0} | {at1} | {flat}")
ok("the reading version shows the pencil, and it opens the version to present with the editing on", rd_pen and rd_to == ["live", True, True], str([rd_pen, rd_to]))
rdk = json.load(open(os.path.join(md, "deck.json"))); rdk["mode"] = "reading"; json.dump(rdk, open(os.path.join(md, "deck.json"), "w"))
vs("build", "moves", "--no-shots"); rdh = open(os.path.join(md, "Moves.html"), encoding="utf-8").read()
rdk["mode"] = "live"; json.dump(rdk, open(os.path.join(md, "deck.json"), "w")); vs("build", "moves", "--no-shots")
ok("a deck whose main version is the reading one carries its editing too", 'data-mode="reading"' in rdh and "window.VS_EDIT=" in rdh)
ok("the editing panel turns the click steps of a slide on, and the change comes into the deck file", turned[0] == "1" and turned[1] >= 1 and turned[1] == turned[2]
   and E.apply_edits(md, {"ops": [{"a": "anim", "n": 3, "key": "step", "value": True}, {"a": "anim", "n": 2, "key": "move", "value": ""}]})[0] == 2
   and json.load(open(os.path.join(md, "deck.json")))["slides"][2]["step"] is True and "move" not in json.load(open(os.path.join(md, "deck.json")))["slides"][1], str(turned))

# forms a brand's decks come to share: a free slide whose form comes up again becomes a master of the brand
import forms as FM
import render as RD0
fbody = lambda a, b: f'<div class="cards c2" style="margin-top:60px"><div class="card"><h3>{a}</h3><p>Text {a}.</p></div><div class="card"><h3>{b}</h3><p>Text {b}.</p></div></div>'
for nme, (x, y) in (("formsa", ("Alpha", "Beta")), ("formsb", ("Gamma", "Delta"))):
    vs("new", nme, "--brand", "smoke", "--langs", "fr,en"); fp = os.path.join(ws, "decks", nme, "deck.json")
    json.dump({"title": nme, "brand": "smoke", "langs": ["fr", "en"], "author": "A", "slides": [{"master": "cover", "title": "T"}, {"master": "free", "title": "Libre", "body": fbody(x, y)}]}, open(fp, "w"))
out_a = vs("build", "formsa", "--no-shots")[1]; out_b = vs("build", "formsb", "--no-shots")[1]
code, out = vs("forms", "smoke", "--promote", "formsb", "--slide", "2", "--name", "pair")
fa = json.load(open(os.path.join(ws, "decks", "formsa", "deck.json")))["slides"][1]
ok("a free form that comes up again is noticed, becomes a master of the brand and takes its place in every deck that had it",
   "FORMS:" not in out_a and "FORMS: slide 2" in out_b and "slide 2 of formsa" in out_b and code == 0 and os.path.exists(os.path.join(lib, "masters", "pair.html"))
   and fa == {"title": "Libre", "master": "pair", "t1": "Alpha", "t2": "Text Alpha.", "t3": "Beta", "t4": "Text Beta."} and vs("build", "formsa", "--no-shots")[0] == 0
   and "pair:" in vs("forms", "smoke")[1] and "formsa, formsb" in vs("forms", "smoke")[1] and FM.mark("<p>x</p>") is None, out_b[-500:] + out + str(fa))

# parts: a block that recurs inside free slides of different forms becomes a part of the brand
band = '<div class="smoke-band" style="margin-top:40px"><b>{a}</b><p>{b}</p></div>'
vs("new", "partsa", "--brand", "smoke", "--langs", "fr,en"); ppath = os.path.join(ws, "decks", "partsa", "deck.json")
json.dump({"title": "Parts", "brand": "smoke", "langs": ["fr", "en"], "author": "A", "slides": [{"master": "cover", "title": "T"},
    {"master": "free", "title": "Un", "body": {"fr": '<ul class="bullets"><li>A</li><li>B</li></ul>' + band.format(a="Bilan", b="Ça marche."), "en": '<ul class="bullets"><li>A</li><li>B</li></ul>' + band.format(a="Takeaway", b="It works.")}},
    {"master": "free", "title": "Deux", "body": '<div class="cards c2"><div class="card"><h3>X</h3></div><div class="card"><h3>Y</h3></div></div>' + band.format(a="Bilan", b="Encore.")}]}, open(ppath, "w"))
out_p = vs("build", "partsa", "--no-shots")[1]
code, out = vs("forms", "smoke", "--part", "takeaway", "--from", "partsa", "--slide", "2", "--block", "2")
pd = json.load(open(ppath)); built = vs("build", "partsa", "--no-shots"); ph = open(os.path.join(ws, "decks", "partsa", "Parts.html"), encoding="utf-8").read()
ok("a block that recurs inside slides of other forms is noticed, becomes a part of the brand and stands where it stood, in every language",
   "FORMS: block 2 of slide 2 recurs" in out_p and "slide 3 of partsa" in out_p and code == 0 and os.path.exists(os.path.join(lib, "parts", "takeaway.html"))
   and pd["slides"][1]["parts"] == [{"part": "takeaway", "t1": {"fr": "<b>Bilan</b>", "en": "<b>Takeaway</b>"}, "t2": {"fr": "Ça marche.", "en": "It works."}}]
   and pd["slides"][1]["body"]["en"].endswith('<vs-part n="1"></vs-part>') and pd["slides"][2]["parts"][0]["t2"] == "Encore." and built[0] == 0
   and ph.count('class="smoke-band"') == 4 and "<vs-part" not in ph and "takeaway  [part]" in vs("masters", "smoke")[1], out_p[-400:] + out + built[1][-300:])
for m in ("bullets", "cards"):                              # two masters of the brand that hold the same block become one part
    mp = os.path.join(lib, "masters", m + ".html"); mt = open(mp, encoding="utf-8").read()
    open(mp, "w", encoding="utf-8").write(mt.replace("{{notes}}", '{{#strip}}<div class="smoke-strip"><b>{{strip_label}}</b><p>{{strip}}</p></div>{{/strip}}\n  {{notes}}', 1))
told = vs("build", "partsa", "--no-shots")[1]
code, out = vs("forms", "smoke", "--part", "strip", "--from-master", "bullets", "--block", re.search(r"--from-master bullets --block (\d+)", told).group(1) if re.search(r"--from-master bullets --block (\d+)", told) else "0")
pd["slides"].append({"master": "bullets", "title": "Points", "bullets": ["Un", "Deux"], "strip_label": "Note", "strip": "Une bande."}); json.dump(pd, open(ppath, "w"))
built = vs("build", "partsa", "--no-shots"); ph = open(os.path.join(ws, "decks", "partsa", "Parts.html"), encoding="utf-8").read()
ok("a block several masters of the brand hold word for word is told once and becomes one part the masters use",
   "FORMS: the masters bullets, cards hold the same block" in told and code == 0 and "{{>part strip}}" in open(os.path.join(lib, "masters", "cards.html"), encoding="utf-8").read()
   and '<p data-s="strip">Une bande.</p>' in ph and "hold the same block" not in vs("build", "partsa", "--no-shots")[1], told[-500:] + out)

# the click steps of a slide in an order of the deck's own
import render as RD
ok("an order of click steps is written for the engine as it is meant", RD._order([3, [1, 2]]) == "3,1+2" and RD._order("0+2, 3") == "0+2,3" and RD._order("x") == "" and 'data-order="3,1+2"' in RD._attrs({"order": [3, [1, 2]]}, "en"))
od = json.load(open(ppath)); od["slides"].append({"master": "bullets", "title": "Ordre", "bullets": ["A", "B", "C", "D"], "step": True, "order": [[0, 2], [4, 1], 3]}); json.dump(od, open(ppath, "w"))
vs("build", "partsa", "--no-shots"); nlast = len(od["slides"])
with sync_playwright() as p:
    br = p.chromium.launch(); pg = br.new_page(viewport={"width": 1280, "height": 720})
    pg.goto("file://" + os.path.join(ws, "decks", "partsa", "Parts.html") + f"#/{nlast}"); pg.wait_for_timeout(1200)
    shown = lambda: pg.evaluate("Array.from(document.querySelectorAll('#deck > .slide.active li')).filter(e=>!e.classList.contains('f')||e.classList.contains('on')).map(e=>e.textContent.trim()).join('')")
    seq = [shown()]
    for _ in range(2): pg.keyboard.press("ArrowRight"); pg.wait_for_timeout(300); seq.append(shown())
    br.close()
ok("the click steps come in the order the deck gives: one with the slide, two joined on one click", seq == ["B", "ABD", "ABCD"], str(seq))
E.set_anim(od, nlast, "order", "2,1"); s_o = od["slides"][-1]["order"]; E.set_anim(od, nlast, "order", "")
ok("the editing writes an order into the deck file and takes it out again", s_o == [2, 1] and "order" not in od["slides"][-1], str(s_o))

# the motion copied from a website takes over the site's own keyframes
import motion as MO3
fx = MO3.frames_css({"opacity": ["from 0", "to 1"], "transform": ["from translate3d(0,-100%,0)", "to translateZ(0)"]})
sx = MO3.site_set({"animations": {"in_use": [{"name": "fadeInDown", "kind": "entrance", "does": ["fade", "rise"], "duration": 0.8, "easing": "cubic-bezier(.2,.8,.2,1)", "count": 12, "width": 400,
                                               "frames": {"opacity": ["from 0", "to 1"], "transform": ["from translate3d(0,-100%,0)", "to none"]}}]}})
ok("the set copied from a website plays the site's own keyframes, with their real way, duration and easing",
   fx == "0%{opacity:0;translate:0 -33%}" and "@keyframes m-item{0%{opacity:0;translate:0 -33%}}" in sx and '"duration": 0.8' in sx and "cubic-bezier(.2,.8,.2,1)" in sx
   and MO3.frames_css({"transform": ["0% matrix(1,0,0,1,0,0)"]}) is None, fx + sx[:600])

# icons a site keeps in an svg sprite come with the colours its css gives them
import analyze as AN
with sync_playwright() as p:
    br = p.chromium.launch(); pg = br.new_page()
    pg.set_content('<svg style="display:none"><symbol id="brand--search" viewBox="0 0 24 24"><path class="fg" d="M2 2h20v20z"/></symbol>'
        '<symbol id="sector_energy" viewBox="0 0 48 48"><circle class="bg" cx="24" cy="24" r="24"/><path class="fg" d="M10 10h20v20z"/></symbol>'
        '<symbol id="site-logo" viewBox="0 0 10 10"><path d="M0 0h10v10z"/></symbol></svg><style>.bg{fill:#2F6FDB}.fg{fill:#EEEEEE}</style><p>page</p>')
    sp = pg.evaluate(AN.SPRITE_JS, 50); br.close()
syms = {s["id"]: s for s in sp["symbols"]}
ok("the icons of an svg sprite are read with the colours the site's css gives them", set(syms) == {"brand--search", "sector_energy", "site-logo"}
   and 'fill="rgb(47, 111, 219)"' in syms["sector_energy"]["markup"] and not syms["sector_energy"]["mono"] and "class=" not in syms["brand--search"]["markup"], str(sp)[:600])
import build as BD3
ok("text in the accent colour on dark ground is a tone light enough to read", BD3.contrast(BD3.accent_as_text("#2F6FDB", "#0B2545", "#FFFFFF", need=4.5), "#0B2545") >= 4.5
   and "accent_on_deep" in " ".join(BD3.brand_warnings({"colors": dict(json.load(open(os.path.join(lib, "brand.json")))["colors"], accent="#2F6FDB", deep="#0B2545", on_deep="#FFFFFF", accent_on_deep="#2F6FDB")})))

# a tidy folder for the user: the presentation, README.md and the same parts in every deck
hb = os.path.join(ws, "handover"); os.makedirs(hb, exist_ok=True)
code, out = vs("handover", "partsa", "--out", hb); code2, out2 = vs("handover", "--brand", "smoke", "--out", hb)
hd = os.path.join(hb, "partsa")
ok("handover writes one folder per deck with the presentation, README.md and research, sources, images and assets, and one per brand",
   code == 0 and os.path.exists(os.path.join(hd, "Parts.html")) and all(os.path.isdir(os.path.join(hd, x)) for x in ("research", "sources", "images", "assets"))
   and "Parts.html" in open(os.path.join(hd, "README.md"), encoding="utf-8").read() and os.path.exists(os.path.join(ws, "decks", "partsa", "README.md"))
   and code2 == 0 and os.path.exists(os.path.join(hb, "smoke-brand", "preview.html")) and os.path.exists(os.path.join(hb, "smoke-brand", "README.md")), out + out2)
ok("every skill asks through the question tool", all("## How to ask" in open(os.path.join(ROOT, "skills", s, "SKILL.md"), encoding="utf-8").read() for s in ("vs-build", "vs-create", "vs-design", "vs-update")))

# a presentation that exists as HTML is read slide by slide; the build leaves fields a slide could still take
import ingest as IG
hsrc = os.path.join(ws, "ing_html"); os.makedirs(hsrc, exist_ok=True)
hf = IG.ingest_html(os.path.join(md, "Moves.html"), hsrc, "moves")
ok("an HTML presentation is photographed slide by slide and read with its words", hf["pages"] == 4 and os.path.exists(os.path.join(hsrc, "sheets")) and "Cartes" in open(os.path.join(hsrc, "text.md"), encoding="utf-8").read()
   and "HTML presentation: 4 slides" in hf["notes"][0], str(hf.get("notes")))
vinfo = json.loads(re.search(r"window\.VS_EDIT=(\{.*?\})</script>", open(os.path.join(md, "Moves.html"), encoding="utf-8").read()).group(1).replace("<\\/", "</"))
ok("the build leaves each slide once more with a field it does not use yet, and apply adds that field to the deck file",
   any(f["slot"] == "lead" and 'data-s="lead"' in f["html"]["fr"] for f in vinfo["fields"].get("3", []))
   and E.apply_edits(md, {"ops": [{"a": "fill", "n": 3, "slot": "lead"}]}, lambda: (RD0.load_masters(lib), RD0.fit_langs))[0] == 1
   and json.load(open(os.path.join(md, "deck.json")))["slides"][2].get("lead"), str(list(vinfo["fields"])))

# a look from nothing: the styles side by side, and a library of the user's own from one of them
import design as DS
code, out = vs("design", "--lang", "de"); sty = list(DS.styles())
ok("twelve styles of vibeupslides' own are offered, each with what it is like and what it fits", code == 0 and sty == ["raster", "magazin", "nacht", "werkstatt", "plakat", "zine", "manifest", "silber", "horizont", "schimmer", "laut", "leicht"] and "Raster." in out and "fits:" in out, out[:300])
code, out = vs("design", "--gallery", "--pick", "raster,nacht", "--name", "Nordlicht", "--lang", "de"); gp = os.path.join(ws, "design", "styles.html")
ok("the styles are shown side by side on the same slides", code == 0 and os.path.exists(gp) and '"name": "nacht"' in open(gp, encoding="utf-8").read() and "Welcher Look passt?" in open(gp, encoding="utf-8").read(), out[-300:])
code, out = vs("design", "eigen", "--style", "magazin", "--name", "Eigen & Art", "--accent", "#0a7d5a", "--langs", "de,en", "--author", "Ada Lovelace"); el = os.path.join(ws, "library", "eigen")
eb = json.load(open(os.path.join(el, "brand.json")))
ok("one of them becomes the user's own library, with their name, colour, languages, masters and a record of how it came about",
   code == 0 and eb["name"] == "Eigen & Art" and eb["colors"]["accent"] == "#0A7D5A" and eb["colors"]["on_accent"] == "#FFFFFF" and eb["langs"] == ["de", "en"] and eb["style"] == "magazin" and eb["author"] == "Ada Lovelace"
   and os.path.exists(os.path.join(el, "masters", "cover.html")) and "font-style:italic" in open(os.path.join(el, "theme.css"), encoding="utf-8").read()
   and "started from the style `magazin`" in open(os.path.join(el, "design.md"), encoding="utf-8").read() and vs("design", "eigen", "--style", "nacht")[0] != 0, out)
code, out = vs("preview", "eigen")
ok("its master slides build without overflow", code == 0 and "overflow: clean" in out, out[-500:])
from PIL import Image as PI0
exd = os.path.join(ws, "ex"); os.makedirs(exd, exist_ok=True); exi = PI0.new("RGB", (800, 450), "#101820"); exi.paste("#F2F2F2", (60, 60, 500, 110)); exi.paste("#FF5A1F", (60, 300, 260, 360)); exi.save(os.path.join(exd, "poster.png"))
code, out = vs("design", "--examine", os.path.join(exd, "poster.png"), os.path.join(md, "Moves.html"), os.path.join(exd, "missing.pdf"))
exf = {r["name"]: r for r in json.load(open(os.path.join(ws, "design", "examples", "findings.json")))}
ok("examples the user likes are read: a picture and a deck give their ground, type and marking colour, and the pictures to look at",
   code == 0 and exf["poster"]["dark"] and exf["poster"]["accent"].upper().startswith("#F") and exf["moves"]["pages"] == 4 and exf["moves"]["look_at"] and "could not be read" in exf["missing"]["note"]
   and "Measured are only the colours" in out, out[:600])
code, out = vs("design", "ausbeispiel", "--style", "nacht", "--name", "Aus Beispiel", "--ground", exf["poster"]["ground"], "--accent", exf["poster"]["accent"], "--head", "No Such Typeface 123", "--radius", "4", "--langs", "de,en")
ab = json.load(open(os.path.join(ws, "library", "ausbeispiel", "brand.json"))); DSc = DS._contrast
ok("a look of the user's own is made from what the examples show: every colour mixed from ground, type and accent so that it reads",
   code == 0 and ab["derived"] and ab["colors"]["paper"].lower() == exf["poster"]["ground"].lower() and ab["shape"]["radius"] == 4 and ab["fonts"]["head"]["family"] == "No Such Typeface 123"
   and DSc(ab["colors"]["ink"], ab["colors"]["paper"]) >= 7 and DSc(ab["colors"]["muted"], ab["colors"]["soft"]) >= 4.5 and DSc(ab["colors"].get("accent_text", ab["colors"]["accent"]), ab["colors"]["paper"]) >= 4.5
   and "could not be fetched" in out and "a look of its own, leaning on the style `nacht`" in open(os.path.join(ws, "library", "ausbeispiel", "design.md"), encoding="utf-8").read(), out[-400:] + str(ab["colors"]))
code, out = vs("design", "--gallery", "--with", "ausbeispiel", "--lang", "de")
ok("the developed look is shown first, next to two of the styles", code == 0 and open(gp, encoding="utf-8").read().count('"name": ') == 3 and '"name": "ausbeispiel"' in open(gp, encoding="utf-8").read(), out[-300:])

# a language added later, the credit on the last slide, the research report, decks that are behind
code, out = vs("langs", "filed", "--add", "es")
ok("a language is added to a deck later and the texts to translate are listed", code == 0 and "languages are now fr, de, es" in out and "TRANSLATE slide 1, title" in out
   and json.load(open(os.path.join(ws, "decks", "filed", "deck.json")))["langs"] == ["fr", "de", "es"], out[:500])
code, out = vs("build", "filed", "--no-shots")
ok("a build names texts that lack a language, a missing author and a missing research report", "TRANSLATE slide 1, title: has fr, de, not es" in out and "AUTHOR:" in out and "RESEARCH:" in out, out[-900:])
code, out = vs("langs", "--brand", "smoke", "--add", "es")
ok("a language is added to a brand without rebuilding its masters", code == 0 and "not rebuilt" in out and "es" in json.load(open(os.path.join(lib, "brand.json")))["langs"], out)
fdk = json.load(open(os.path.join(ws, "decks", "filed", "deck.json"))); fdk["author"] = "Ada Lovelace"; fdk["langs"] = ["fr", "de"]; json.dump(fdk, open(os.path.join(ws, "decks", "filed", "deck.json"), "w"))
os.makedirs(os.path.join(ws, "decks", "filed", "research"), exist_ok=True); open(os.path.join(ws, "decks", "filed", "research", "report.md"), "w").write("# Rapport\n" + "Ce que la présentation doit faire. " * 12)
code, out = vs("build", "filed", "--no-shots")
fh = open(os.path.join(ws, "decks", "filed", "Filed.html"), encoding="utf-8").read()
ok("the last slide credits the person who made the deck, in each language, and the checks are quiet", fh.count('class="vs-credit"') == 2 and "Créé par Ada Lovelace, avec un peu d'aide de VibeUpSlides par vibeup.berlin" in fh
   and "Erstellt von Ada Lovelace, mit ein bisschen Hilfe von VibeUpSlides von vibeup.berlin" in fh and "AUTHOR:" not in out and "RESEARCH:" not in out and out.count("overflow: clean") == 2, out[-700:])
code, out = vs("build", "demo", "--no-shots"); code2, out2 = vs("scenes")
ok("the catalogue of animated scenes is not part of the package: nothing ships, nothing is offered, no build asks for a scene",
   not os.path.isdir(os.path.join(FW, "scenes")) and "SCENES:" not in out and "not part of this version" in out2 and "scene  [" not in vs("masters", "smoke")[1]
   and not os.path.exists(os.path.join(lib, "masters", "scene.html")) and "scenes" not in vs("help")[1].split("The workspace")[0].replace("scenes/", ""), out2 + out[-300:])
code, out = vs("refresh", "--brand", "smoke", "--check", "--except", "filed")
ok("the decks that are behind their brand are listed, for the question whether to bring them up to date", code == 0 and "demo: behind" in out and "filed:" not in out and "Ask the user" in out, out)

# the ring on a marked column grows with its number; a slide's focus moves its photo
import motion as MO2
ok("the ring around a marked number is as wide as the number needs", "width:max(96px,calc(100% + 64px))" in MO2.HOOKS_CSS)
import render as RD
ok("a slide's focus is passed to its photo, and nothing else is", 'style="--focus:right top"' in RD._attrs({"focus": "Right Top"}, "en") and "style" not in RD._attrs({"focus": "x;color:red"}, "en"))
import build as BD2
ok("a face detector is at hand or its absence is said", BD2._faces(__import__("PIL.Image", fromlist=["Image"]).new("RGB", (320, 180), "#888")) in ([], None))

# update path: a newer payload is taken over before a build
newer = os.path.join(ws, "payload"); shutil.copytree(FW, newer, ignore=shutil.ignore_patterns("__pycache__"))
open(os.path.join(newer, "VERSION"), "w").write("99.0.0"); open(os.path.join(newer, "CHANGELOG.md"), "w").write("# Changelog\n\n## 99.0.0\n- test entry\n")
open(os.path.join(ws, ".source"), "w").write(newer)
code, out = vs("build", "demo", "--no-shots")
ok("a build takes over a newer installed framework and says what is new", code == 0 and "UPDATED" in out and "test entry" in out and open(os.path.join(ws, "framework", "VERSION")).read().strip() == "99.0.0", out[:500])

print(f"\n{sum(results)}/{len(results)} passed", "" if all(results) else "- FAILED", "| workspace", ws)
sys.exit(0 if all(results) else 1)
