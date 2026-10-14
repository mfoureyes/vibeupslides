"""Test of the motion system: every motion set builds, rests in the finished slide, and can be looked at as a film strip.

    python3 tests/motion.py [set ...]      (needs Pillow and Playwright with Chromium in the Python that runs it)

For every set: the master preview of a brand with that set builds without overflow; on every slide the picture after
the animations have finished is the picture of export mode (the resting state is the finished slide); export mode
has no running animation and does not change over time; the film strip is written and shows movement (or none for
the set that does nothing). Then: brand tokens, the deck's intensity levels, a brand's motion.css, clean names.
Works in a temporary workspace and does not touch ~/vibeupslides.
"""
import io, json, os, re, subprocess, sys, tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FW = os.path.join(ROOT, "skills", "vs-update", "framework")
ws = tempfile.mkdtemp(prefix="vibeupslides_motion_test_")
env = dict(os.environ, VIBEUPSLIDES_HOME=ws, VS_NO_VENV="1")
results = []
def ok(name, cond, info=""):
    results.append(bool(cond)); print("ok  " if cond else "FAIL", name, info if not cond else "")
def vs(*args, src=False):
    cli = os.path.join(FW, "vs.py") if src else os.path.join(ws, "vs.py")
    p = subprocess.run([sys.executable, cli, *args], env=env, capture_output=True, text=True)
    return p.returncode, p.stdout + p.stderr

sys.path.insert(0, FW); os.environ["VIBEUPSLIDES_HOME"] = ws
import motion
from PIL import Image, ImageChops
from playwright.sync_api import sync_playwright

code, out = vs("init", "--no-venv", src=True)
ok("init creates the workspace with the motion sets", code == 0 and os.path.exists(os.path.join(ws, "framework", "motion", "rise.css")), out[-300:])

SETS = motion.sets()
ok("the library has a set that does nothing and at least five that move", "none" in SETS and len(SETS) >= 6, str(list(SETS)))
ok("every set has a character line, a fit and its own tokens", all(s.get("character") and s.get("fits") and set(s.get("tokens", {})) == set(motion.TOKENS) for s in SETS.values()))
ok("every set defines every role", all(all(re.search(r"@keyframes\s+" + r + r"\s*\{", s["css"]) for r in motion.ROLES) for s in SETS.values()),
   str({n: [r for r in motion.ROLES if not re.search(r"@keyframes\s+" + r + r"\s*\{", s["css"])] for n, s in SETS.items()}))

BRAND = {"name": "Motion Test", "lang": "en", "confirmed": True,
         "colors": {"accent": "#E4572E", "on_accent": "#FFFFFF", "ink": "#17191C", "deep": "#17191C", "on_deep": "#FFFFFF",
                    "muted": "#5E6470", "line": "#C9CDD3", "soft": "#F1F2F4", "ghost": "#E6E8EB", "paper": "#FFFFFF"},
         "shape": {"radius": 6, "motif": "wedge"}, "footer": {"right": "example.org"}}
def brand(name, **motion_profile):
    d = os.path.join(ws, "library", name); os.makedirs(d, exist_ok=True)
    json.dump(dict(BRAND, motion=motion_profile) if motion_profile else BRAND, open(os.path.join(d, "brand.json"), "w"))
    return d

HIDE = "#ui,#hint,#about,#toast,#loader{display:none!important}"
SKIP = "s.matches('.tslide,.qslide')||s.querySelector('.mbox,iframe,video')"      # timers, quizzes and media differ between live and export by design
FINISH = """async()=>{const fr=()=>new Promise(r=>requestAnimationFrame(()=>requestAnimationFrame(r)));
  document.querySelectorAll('.slide.active .f').forEach(f=>f.classList.add('on')); await fr();
  for(let k=0;k<3;k++){document.getAnimations().forEach(a=>{try{a.finish()}catch(e){}}); await fr();}
  window.vsMotionSync&&vsMotionSync(); await fr();}"""
def shot(pg):
    return Image.open(io.BytesIO(pg.locator("#deck").screenshot())).convert("RGB")
def differing(a, b, tolerance=40, soften=4):
    """Share of pixels whose colour differs clearly. Both pictures are reduced first: an element that a finished
    animation still holds on its own layer may be drawn a fraction of a pixel off, which is no unfinished state."""
    if a.size != b.size: return 1.0
    if soften > 1: a, b = (im.resize((im.width // soften, im.height // soften), Image.BOX) for im in (a, b))
    d = ImageChops.difference(a, b).convert("L").point(lambda v: 255 if v > tolerance else 0)
    return d.histogram()[255] / (a.width * a.height)

only = [a for a in sys.argv[1:] if a in SETS] or list(SETS)
with sync_playwright() as p:
    br = p.chromium.launch()
    for name in only:
        d = brand("b-" + name, set=name)
        code, out = vs("preview", "b-" + name)
        html = os.path.join(d, "preview.html")
        ok(f"[{name}] the master preview builds without overflow", code == 0 and "overflow: clean" in out and os.path.exists(html), out[-500:])
        if not os.path.exists(html): continue
        live = br.new_page(viewport={"width": 1280, "height": 720}); errors = []; live.on("pageerror", lambda e: errors.append(str(e)))
        live.goto("file://" + html); live.wait_for_timeout(900); live.add_style_tag(content=HIDE)
        still = br.new_page(viewport={"width": 1280, "height": 720})
        still.goto("file://" + html + "?export=1"); still.wait_for_timeout(900); still.add_style_tag(content=HIDE)
        ok(f"[{name}] the deck carries its set", live.evaluate("document.documentElement.dataset.motionSet") == name and live.evaluate("document.documentElement.dataset.motion") == "standard")
        n = live.evaluate("document.querySelectorAll('.slide:not(.off)').length")
        bad, moving, changing, compared, moved = [], [], [], 0, 0
        for i in range(1, n + 1):
            for pg in (live, still): pg.evaluate(f"location.hash='#/{i}'")
            live.wait_for_timeout(60)
            if live.evaluate(f"(()=>{{const s=document.querySelector('.slide.active');return !!({SKIP})}})()"): continue
            # a look into the middle of the animation: paused at 0.25 s the slide must not be finished yet (except for the still set)
            live.evaluate("""()=>{const s=document.querySelector('.slide.active'); s.classList.remove('active'); void s.offsetWidth; s.classList.add('active');
                s.querySelectorAll('.f').forEach(f=>{f.style.transition='none'; f.classList.add('on');});
                window.__m=s.getAnimations({subtree:true}).filter(a=>!a.transitionProperty); __m.forEach(a=>{a.pause(); a.currentTime=250;});}""")
            mid = shot(live)
            live.evaluate("__m.forEach(a=>a.play())"); live.evaluate(FINISH); rest = shot(live)
            still.wait_for_timeout(120); a = shot(still)
            running = still.evaluate("document.getAnimations().filter(a=>a.playState==='running').length")
            if i % 4 == 1: still.wait_for_timeout(250)
            b = shot(still)
            compared += 1
            if differing(mid, rest) > .0005: moved += 1
            if differing(rest, a) > .0005: bad.append((i, round(differing(rest, a), 4)))
            if running: moving.append(i)
            if differing(a, b, 8, 1) > 0: changing.append(i)
        ok(f"[{name}] after the animations every slide is the finished slide of export mode ({compared} slides compared)", compared >= 15 and not bad, f"slide, share of pixels: {bad}")
        ok(f"[{name}] export mode has no running animation and does not change", not moving and not changing, f"running {moving} changing {changing}")
        ok(f"[{name}] " + ("nothing moves" if name == "none" else "slides are in motion a quarter second in"), (moved == 0) if name == "none" else moved >= compared * .6, f"{moved} of {compared}")
        ok(f"[{name}] no script errors", not errors, str(errors[:2]))
        live.close(); still.close()
        code, out = vs("motion", "b-" + name, "--strip")
        strip = os.path.join(d, "preview", "motion", f"strip_{name}.png")
        ok(f"[{name}] the film strip is written", code == 0 and os.path.exists(strip), out[-400:])
        if os.path.exists(strip):
            im = Image.open(strip).convert("RGB"); cols, tw, th, left, top, gap = len(motion.STRIP_TIMES), 384, 216, 96, 44, 6
            first = im.crop((left, top, left + tw, top + th)); last = im.crop((left + (cols - 1) * (tw + gap), top, left + (cols - 1) * (tw + gap) + tw, top + th))
            ok(f"[{name}] the strip has four rows of {cols} frames and " + ("stands still" if name == "none" else "shows movement"),
               im.size == (left + cols * (tw + gap), top + 4 * (th + gap)) and ((differing(first, last, 8, 1) == 0) if name == "none" else differing(first, last) > .01), str(im.size))

    # ---------------------------------------------------------------- tokens, intensity, the brand's own motion.css
    d = brand("tok", set="soft", ease="cubic-bezier(.3,0,.1,1)", duration=1.1, stagger=.2, travel=50, change="none")
    open(os.path.join(d, "motion.css"), "w").write("/* signature */\n@keyframes m-wipe{from{rotate:90deg}}\n.signature-probe{order:7}\n")
    brand("bad", set="does-not-exist", ease="url(x);}", duration="fast", change="spin")
    pb = motion.profile({"motion": {"set": "does-not-exist", "ease": "url(x);}", "duration": "fast", "change": "spin"}})
    ok("a broken profile falls back to safe values", pb["set"] == motion.DEFAULT_SET and pb["ease"] == motion.TOKENS["ease"] and pb["change"] == "slide" and isinstance(pb["duration"], float), str(pb))
    ok("a brand without a profile gets the default set with the set's tokens", motion.profile(BRAND) == dict(SETS[motion.DEFAULT_SET]["tokens"], set=motion.DEFAULT_SET), str(motion.profile(BRAND)))
    slides = [{"master": "cover", "title": "A <em>title</em>", "lead": "Lead"}, {"master": "chapter", "number": 3, "title": "Part"},
              {"master": "bullets", "title": "Points", "bullets": ["A", "B", "C"]},
              {"master": "bars", "title": "Figures", "rows": [{"label": "A", "value": 12400, "share": 100}, {"label": "B", "value": 3100, "share": 25}]}]
    pages = {}
    for level, value in (("standard", True), ("off", False), ("off2", "off"), ("calm", "calm"), ("expressive", "expressive")):
        dd = os.path.join(ws, "decks", level); os.makedirs(dd, exist_ok=True)
        json.dump({"title": level, "brand": "tok", "langs": ["en"], "motion": value, "slides": slides}, open(os.path.join(dd, "deck.json"), "w"))
        code, out = vs("build", level, "--no-shots")
        ok(f"a deck with motion {json.dumps(value)} builds", code == 0 and "overflow: clean" in out, out[-400:])
        pg = br.new_page(viewport={"width": 1280, "height": 720}); pg.goto("file://" + os.path.join(dd, level + ".html")); pg.wait_for_timeout(900); pages[level] = pg
    ev = pages["standard"].evaluate
    css = lambda v: ev(f"getComputedStyle(document.documentElement).getPropertyValue('{v}').trim()")
    ok("brand tokens reach the deck", (css("--m-ease"), css("--m-dur"), css("--m-stagger"), css("--m-travel"), css("--m-change-dur")) == ("cubic-bezier(.3,0,.1,1)", "1.1s", "0.2s", "50px", "0s"),
       str((css("--m-ease"), css("--m-dur"), css("--m-stagger"), css("--m-travel"), css("--m-change-dur"))))
    ok("the brand's motion.css is loaded after the set", ev("!!document.getElementById('motion-brand')") and
       ev("document.getElementById('motion-set').compareDocumentPosition(document.getElementById('motion-brand'))&4") == 4)
    ok("true is standard, with the hooks in the markup", ev("document.documentElement.dataset.motion") == "standard" and ev("document.querySelectorAll('.mslide.mcover .mtext .mw').length") >= 2)
    for level in ("off", "off2"):
        e = pages[level].evaluate
        ok(f"{level}: no hooks, the still set, nothing running", e("document.documentElement.dataset.motion") == "off" and e("document.documentElement.dataset.motionSet") == "none"
           and e("document.querySelectorAll('.mcover,.mchap').length") == 0 and not e("!!document.getElementById('motion-brand')")
           and e("document.querySelector('.slide.active').getAnimations({subtree:true}).filter(a=>a.effect.getComputedTiming().activeDuration>0&&a.effect.getKeyframes().length>0).length") == 0)
    def moving(level, slide, sel):
        pg = pages[level]; pg.evaluate(f"location.hash='#/{slide % 4 + 1}'"); pg.wait_for_timeout(80); pg.evaluate(f"location.hash='#/{slide}'"); pg.wait_for_timeout(200)
        return pg.evaluate(f"(()=>{{const e=document.querySelector('.slide.active {sel}');return e?e.getAnimations().filter(a=>a.effect.getKeyframes().length>0).length:-1}})()")
    ok("calm keeps the set and the entrances of titles and elements", pages["calm"].evaluate("document.documentElement.dataset.motionSet") == "soft" and moving("calm", 1, ".mtext .mw>span") == 1 and moving("calm", 3, "li.anim") == 1)
    ok("calm leaves out the large moves", moving("calm", 2, ".wedge") == 0 and moving("calm", 2, ".mreel") == 0 and moving("standard", 2, ".wedge") == 1)
    ok("expressive also moves the titles of content slides", moving("expressive", 3, "h2") == 1 and moving("standard", 3, "h2") == 0)
    travel = lambda level: pages[level].evaluate("getComputedStyle(document.querySelector('.slide')).getPropertyValue('--m-k').trim()")
    ok("intensity scales the way things travel", (travel("calm"), travel("standard"), travel("expressive")) == (".6", "1", "1.6"), str((travel("calm"), travel("standard"), travel("expressive"))))
    pg = pages["standard"]; pg.evaluate("location.hash='#/4'"); pg.wait_for_timeout(200)
    early = pg.evaluate("document.querySelector('.slide.active .mvalue').textContent"); pg.wait_for_timeout(4500)
    late = pg.evaluate("document.querySelector('.slide.active .mvalue').textContent")
    ok("numbers follow their bars and end on the full value", early != "12,400" and late == "12,400", f"{early} -> {late}")
    br.close()

code, out = vs("motion", "tok")
ok("motion lists the sets and marks the brand's", code == 0 and "* soft" in out and all(n in out for n in SETS) and "profile: set soft" in out, out[:300])
code, out = vs("motion", "tok", "--set", "mask")
ok("--set saves the set and keeps the brand's tokens", code == 0 and json.load(open(os.path.join(ws, "library", "tok", "brand.json")))["motion"] == {"set": "mask", "ease": "cubic-bezier(.3,0,.1,1)", "duration": 1.1, "stagger": .2, "travel": 50, "change": "none"}, out[:300])
code, out = vs("motion", "tok", "--reset")
ok("--reset drops the tokens", code == 0 and json.load(open(os.path.join(ws, "library", "tok", "brand.json")))["motion"] == {"set": "mask"}, out[:300])
code, out = vs("motion", "tok", "--set", "nope")
ok("an unknown set is refused", code != 0 and "unknown motion set" in out, out[:200])

# ---------------------------------------------------------------- reading motion from a website (local pages, no network)
import analyze
PAGE = """<!DOCTYPE html><html><head><meta charset="utf-8"><style>body{margin:0;font:18px sans-serif} section{min-height:700px;padding:60px}
.card{width:300px;height:160px;border:1px solid #999;display:inline-block;margin:10px} a.btn{display:inline-block;background:#234;color:#fff;padding:12px 20px;transition:transform .2s ease;margin-top:100px}
a.btn:hover{transform:translateY(-3px)} %s</style></head><body><section><h1>Top</h1><a class="btn" href="#">Button</a></section>
<section><h2 class="r"><span class="i">One</span></h2><div><div class="card r" style="--k:0"><h3 class="i">A</h3></div><div class="card r" style="--k:1"><h3 class="i">B</h3></div><div class="card r" style="--k:2"><h3 class="i">C</h3></div></div></section>
<section><h2 class="r"><span class="i">Two</span></h2><p class="r"><span class="i">Text</span></p><p class="r"><span class="i">More text</span></p></section>%s
<script>const io=new IntersectionObserver(es=>es.forEach(e=>{if(e.isIntersecting)e.target.classList.add('in')}),{threshold:.1});document.querySelectorAll('.r').forEach(e=>io.observe(e));</script></body></html>"""
CASES = {
    "still": ("", "", "rise"),
    "rise": (".r{opacity:0;transform:translateY(30px);transition:opacity .6s cubic-bezier(.2,.7,.2,1),transform .6s cubic-bezier(.2,.7,.2,1);transition-delay:calc(var(--k,0)*.08s)} .r.in{opacity:1;transform:none}", "", "rise"),
    "mask": (".r .i{display:block;clip-path:inset(0 100% 0 0);transition:clip-path .9s cubic-bezier(.7,0,.2,1)} .r.in .i{clip-path:inset(0 0 0 0)}", "", "mask"),      # the observed element holds a clipped child
    "soft": (".r{opacity:0;transform:scale(.9);filter:blur(8px);transition:all 1s cubic-bezier(.16,1,.3,1)} .r.in{opacity:1;transform:none;filter:blur(0)}", "", "soft"),
    "cascade": (".r{opacity:0;transform:translateY(80px);transition:all .5s cubic-bezier(.34,1.56,.64,1);transition-delay:calc(var(--k,0)*.12s)} .r.in{opacity:1;transform:none}"
                " .mq{white-space:nowrap;width:2000px;animation:mq 20s linear infinite} @keyframes mq{to{transform:translateX(-50%)}}", '<div class="mq">running band running band running band</div>', "cascade"),
    "cut": (".r{opacity:0;transition:opacity .3s steps(2,end)} .r.in{opacity:1} a,h1,h2,h3,p,div{transition:color .2s steps(2,end)}", "", "cut"),
}
with sync_playwright() as p:
    br = p.chromium.launch(); got = {}
    for case, (css, extra, want) in CASES.items():
        f = os.path.join(ws, f"site_{case}.html"); open(f, "w").write(PAGE % (css, extra))
        ctx = br.new_context(viewport={"width": 1440, "height": 900}); pg = ctx.new_page(); pg.goto("file://" + f); pg.wait_for_timeout(300)
        pg.evaluate("async()=>{for(let y=0;y<document.body.scrollHeight;y+=700){scrollTo(0,y);await new Promise(r=>setTimeout(r,100));}scrollTo(0,0);}")
        census = dict(pg.evaluate(analyze.MOTION_CENSUS_JS), url="file://" + f)
        facts, prof, line = analyze.read_motion(ctx, "file://" + f, [census], {}, {"radius": 4}); ctx.close()
        got[case] = (prof, facts, line)
        ok(f"site that moves like '{case}' gets the set {want}", prof["set"] == want, f"{prof} | {facts['suggestion']['why']} | {line}")
    br.close()
prof, facts, line = got["still"]
ok("a site without motion gets the calm default with the set's own tokens", facts["amount"] in ("none", "hover only") and prof == dict(SETS["rise"]["tokens"], set="rise") and "calm default" in facts["suggestion"]["why"], str(prof))
prof, facts, line = got["rise"]
ok("measured values become tokens: easing, duration, stagger, travel", (prof["ease"], prof["duration"], prof["stagger"], prof["travel"]) == ("cubic-bezier(.2,.7,.2,1)", .6, .08, 30), str(prof))
ok("scroll reveals are recorded with kind, driver and samples", facts["scroll_reveal"]["found"] and facts["scroll_reveal"]["kinds"].get("rise", 0) >= 4 and facts["scroll_reveal"]["driven_by"].get("css transition") and facts["scroll_reveal"]["samples"])
ok("hover of a button is recorded", any(h["moves"] for h in facts["hover"]["buttons"]), str(facts["hover"]))
ok("a marquee is recognised", got["cascade"][1]["marquees"] and got["cascade"][1]["animations"]["in_use"][0]["kind"] == "marquee", str(got["cascade"][1]["animations"]["in_use"][:1]))
ok("the summary is one line", line.startswith("motion: ") and "\n" not in line)
ok("the drafted profile is valid", all(motion.profile({"motion": g[0]}) == g[0] for g in got.values()), str([g[0] for g in got.values() if motion.profile({"motion": g[0]}) != g[0]]))

# ---------------------------------------------------------------- names
text = open(os.path.join(FW, "motion.py"), encoding="utf-8").read() + "".join(open(os.path.join(FW, "motion", f), encoding="utf-8").read() for f in os.listdir(os.path.join(FW, "motion")))
engine = open(os.path.join(FW, "master.html"), encoding="utf-8").read()
old = re.compile(r"\b(rein|zaehl|keil|mzs|mzb|kline|kpt|mkdraw|mkpt|mwedgein|mdiag|mstamp|mgrow|mroll|mrise|mtint)\b")
ok("no old or German names are left in the motion code and the engine's animations", not old.search(text) and not re.search(r"@keyframes\s+(rein|zaehl|gl|ken|wedge|ghost)\b", engine),
   str(old.findall(text)[:5]))
ok("MOTION_ASSETS and the helpers render.py imports still exist", motion.MOTION_ASSETS and all(callable(getattr(motion, f)) for f in ("chapter_number", "chevron_fill", "bars", "lower_third", "logo_intro", "line_chart")))

print(f"\n{sum(results)} of {len(results)} checks passed" + ("" if all(results) else " | FAILED"))
sys.exit(0 if all(results) else 1)
