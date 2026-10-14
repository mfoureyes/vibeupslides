"""Video, embeds and scenes: the things a deck links instead of embedding.

A deck without them is one self-contained HTML file. A deck with them is a folder: the HTML plus
the files it refers to. Local video files stay where they are in the deck folder (files from the
brand library or from elsewhere are copied to assets/), scenes are copied to assets/scenes/<name>/,
remote players and websites are loaded from the network while their slide is current.

Every such slide carries one box the engine in master.html works on:

    <div class="mbox" data-media="video|player|iframe|scene" data-src="..." ...>
      <div class="mposter">poster image, or a neutral placeholder with title and URL</div>
      <button class="mplay">, <div class="mnote">        (play button and message, filled by the engine)
    </div>

The live element (<video> or <iframe>) is created by the engine when the slide becomes current.
In export mode, overview and presenter previews only the poster is shown.
"""
import hashlib, json, os, re, shutil, urllib.parse

HERE = os.path.dirname(os.path.abspath(__file__))

VIDEO_EXT = (".mp4", ".m4v", ".webm", ".mov", ".ogv", ".ogg")
TOKENS = ("accent", "on_accent", "ink", "deep", "on_deep", "muted", "line", "soft", "ghost", "paper", "font", "font_head")

# Sandbox of the iframes. Scripts are needed by every player, website and scene; navigating the top
# window (allow-top-navigation*), modal dialogs, downloads and pointer lock are never granted.
#   remote pages: allow-same-origin lets the page keep its own origin (cookies, storage), without it YouTube,
#     Vimeo, Figma and most websites do not run. That origin is never the deck's, so the page cannot reach
#     the deck. Forms for search and login fields, pop-ups so that "watch on ..." links open in a new tab
#     (and work there, hence escape-sandbox), presentation for the players' cast button.
#   local pages (scenes, local HTML): scripts only. Without allow-same-origin they run in an origin of their
#     own, so a scene can neither read the deck nor lift its own sandbox.
SANDBOX_REMOTE = "allow-scripts allow-same-origin allow-forms allow-popups allow-popups-to-escape-sandbox allow-presentation"
SANDBOX_LOCAL = "allow-scripts"
ALLOW_PLAYER = "autoplay; encrypted-media; picture-in-picture; fullscreen"
ALLOW_EMBED = "fullscreen"                                   # what a website gets unless the slide asks for more
ALLOW_OPTIONAL = ("autoplay", "encrypted-media", "picture-in-picture", "clipboard-write", "fullscreen")


# ---------------------------------------------------------------- small helpers

def _esc(v):
    return str(v).replace("&", "&amp;").replace('"', "&quot;").replace("<", "&lt;").replace(">", "&gt;")

def _plain(v):
    return re.sub(r"<[^>]+>", "", str(v or "")).strip()

def _flag(v, default=False):
    if v is None or v == "":
        return default
    return str(v).strip().lower() not in ("false", "0", "no", "off") if isinstance(v, str) else bool(v)

def seconds(v):
    """90, "90", "1:30", "1m30s", "90s" -> seconds as a number, None if empty or unreadable."""
    if v is None or v == "" or v is False:
        return None
    if isinstance(v, (int, float)):
        return max(0, v)
    s = str(v).strip().lower()
    if re.fullmatch(r"\d+(\.\d+)?", s):
        return float(s) if "." in s else int(s)
    if re.fullmatch(r"\d+(:\d{1,2}){1,2}", s):
        n = 0
        for part in s.split(":"):
            n = n * 60 + int(part)
        return n
    m = re.fullmatch(r"(?:(\d+)h)?(?:(\d+)m)?(?:(\d+)s?)?", s)
    if m and any(m.groups()):
        return int(m.group(1) or 0) * 3600 + int(m.group(2) or 0) * 60 + int(m.group(3) or 0)
    return None

def _num(v):
    return str(int(v)) if float(v) == int(v) else f"{v:g}"

def is_remote(v):
    return bool(re.match(r"https?://", str(v or ""), re.I))

def _base(env):
    """The folder the built HTML lies in: relative links start here, assets/ is created here."""
    return env.get("out_dir") or env.get("deck_dir") or os.getcwd()

def _warn(env, msg):
    if msg not in env.setdefault("warnings", []):
        env["warnings"].append(msg)

def _note(env, kind, ref, online=False):
    env.setdefault("media", []).append({"kind": kind, "ref": ref, "online": bool(online)})

def _url(rel):
    return urllib.parse.quote(rel.replace(os.sep, "/"), safe="/")


# ---------------------------------------------------------------- remote players

_YT = re.compile(r"^https?://(?:www\.|m\.|music\.)?(?:youtube\.com/(?:watch\?(?:[^#]*&)?v=|embed/|shorts/|live/|v/)|youtu\.be/|youtube-nocookie\.com/embed/)([A-Za-z0-9_-]{6,20})", re.I)
_VIMEO = re.compile(r"^https?://(?:www\.|player\.)?vimeo\.com/(?:video/|channels/[^/]+/|groups/[^/]+/videos/)?(\d{5,})(?:/([0-9a-f]{6,}))?", re.I)

def player(url, start=None, end=None, autoplay=True, loop=False, muted=False):
    """Recognise a YouTube or Vimeo link. Returns {provider, id, embed, watch} with the privacy-friendly
    embed URL (youtube-nocookie.com, Vimeo with dnt=1), or None for any other address."""
    url = str(url).strip()
    q = urllib.parse.parse_qs(urllib.parse.urlsplit(url).query)
    m = _YT.match(url)
    if m:
        vid = m.group(1)
        if start is None:
            start = seconds((q.get("t") or q.get("start") or [None])[0])
        p = [("rel", "0"), ("playsinline", "1"), ("enablejsapi", "1")]          # enablejsapi: the K key can pause the player
        if start: p.append(("start", str(int(start))))
        if end: p.append(("end", str(int(end))))
        if autoplay: p.append(("autoplay", "1"))
        if muted: p.append(("mute", "1"))
        if loop: p += [("loop", "1"), ("playlist", vid)]                         # YouTube loops only with a playlist of one
        return {"provider": "youtube", "id": vid, "embed": f"https://www.youtube-nocookie.com/embed/{vid}?" + urllib.parse.urlencode(p),
                "watch": f"https://www.youtube.com/watch?v={vid}" + (f"&t={int(start)}s" if start else "")}
    m = _VIMEO.match(url)
    if m:
        vid, h = m.group(1), m.group(2) or (q.get("h") or [None])[0]
        if start is None:
            start = seconds(urllib.parse.urlsplit(url).fragment.replace("t=", "")) if "t=" in urllib.parse.urlsplit(url).fragment else None
        p = [("dnt", "1"), ("title", "0"), ("byline", "0"), ("portrait", "0")]
        if h: p.append(("h", h))
        if autoplay: p.append(("autoplay", "1"))
        if muted: p.append(("muted", "1"))
        if loop: p.append(("loop", "1"))
        t = f"#t={int(start)}s" if start else ""                                 # Vimeo has no end time in the embed
        return {"provider": "vimeo", "id": vid, "embed": f"https://player.vimeo.com/video/{vid}?" + urllib.parse.urlencode(p) + t,
                "watch": f"https://vimeo.com/{vid}" + (f"/{h}" if h else "") + t}
    return None


# ---------------------------------------------------------------- files of the deck folder

def link_file(rel, env, what="video"):
    """A file named in a slot -> its address relative to the built HTML, or None with a warning.
    Files inside the deck folder are linked where they are. `brand:` files and files from elsewhere are
    copied to assets/, so the deck folder holds everything it needs."""
    rel = str(rel).strip()
    base = os.path.realpath(_base(env))
    if rel.startswith("brand:"):
        src = os.path.join(env.get("brand_dir") or "", rel[6:])
    else:
        src = rel if os.path.isabs(rel) else os.path.join(env.get("deck_dir") or base, os.path.expanduser(rel))
    if not os.path.isfile(src):
        _warn(env, f"{what} not found: {rel}")
        return None
    real = os.path.realpath(src)
    if real.startswith(base + os.sep):
        return _url(os.path.relpath(real, base))
    dst = os.path.join(base, "assets", os.path.basename(real))
    if os.path.exists(dst) and os.path.realpath(dst) != real and (os.path.getsize(dst) != os.path.getsize(real) or os.path.getmtime(dst) < os.path.getmtime(real)):
        os.remove(dst)
    if not os.path.exists(dst):
        os.makedirs(os.path.dirname(dst), exist_ok=True)
        shutil.copy2(real, dst)
    return _url(os.path.relpath(dst, base))


# ---------------------------------------------------------------- scenes

def scene_dirs(brand_dir=None):
    """Where scenes live: the brand's own first (they win on equal name), then the framework's."""
    out = []
    if brand_dir:
        out.append(("brand", os.path.join(brand_dir, "scenes")))
    out.append(("framework", os.path.join(HERE, "scenes")))
    return out

def load_scenes(brand_dir=None):
    """{name: {"meta": scene.json, "dir": folder, "origin": "brand"|"framework"}}"""
    out = {}
    for origin, folder in reversed(scene_dirs(brand_dir)):
        if not os.path.isdir(folder):
            continue
        for n in sorted(os.listdir(folder)):
            d = os.path.join(folder, n)
            if not os.path.isfile(os.path.join(d, "index.html")) or not os.path.isfile(os.path.join(d, "scene.json")):
                continue                                   # a folder without scene.json is not a finished scene
            try:
                meta = json.load(open(os.path.join(d, "scene.json"), encoding="utf-8"))
            except (OSError, ValueError):
                continue
            if not isinstance(meta, dict):
                continue
            out[meta.get("name") or n] = {"meta": meta, "dir": d, "origin": origin}
    return out

def scene_catalog(brand_dir=None, full=False):
    """Text list of the scenes, for choosing one while writing a deck."""
    lines = []
    try: chosen = json.load(open(os.path.join(brand_dir, "brand.json"), encoding="utf-8")).get("scenes") or []
    except (OSError, ValueError, TypeError): chosen = []
    if chosen: lines.append("* marks the scenes the user chose for this brand: use these first, others only when a slide asks for one.")
    hidden = []
    for name, s in sorted(load_scenes(brand_dir).items(), key=lambda kv: (kv[1]["meta"].get("category", "~"), kv[0])):
        m = s["meta"]; steps = int(m.get("steps") or 0)
        if m.get("showcase") is False and s["origin"] != "brand" and name not in chosen and not full:
            hidden.append(name); continue                  # bound to one motif: a model for a brand's own scene, not offered as it is
        facts = [m.get("category") or "uncategorised", f"{steps} step{'' if steps == 1 else 's'}" if steps else "plays by itself",
                 "needs to be online" if m.get("online") else "works offline"]
        if m.get("loop"): facts.append("loops")
        if not m.get("poster") or not os.path.exists(os.path.join(s["dir"], m["poster"])): facts.append("no poster")
        lines.append(f"{'* ' if name in chosen else ''}{name}  [{s['origin']}]  {m.get('title', name)} · " + " · ".join(facts))
        if m.get("use"): lines.append(f"    {m['use']}")
        for key, desc in (m.get("config") or {}).items():
            lines.append(f"    config.{key}: {desc}")
        if m.get("vars"): lines.append("    vars: " + ", ".join(f"{k} = {v}" for k, v in m["vars"].items()))
        if m.get("notes"): lines.append(f"    notes: {m['notes']}")
        if full and m.get("sample") is not None:
            lines.append("    sample: " + json.dumps({"master": "scene", "scene": name, "config": m["sample"]}, ensure_ascii=False))
    if hidden: lines.append("models for a brand's own scene, bound to one motif and not offered as they are (--full shows them): " + ", ".join(hidden))
    return "\n".join(lines) or "no scenes yet (framework/scenes/<name>/ or library/<brand>/scenes/<name>/)"

def token_values(brand):
    """Brand tokens as CSS values, under the names a scene.json may map its custom properties to."""
    b = brand or {}
    c, f = b.get("colors") or {}, b.get("fonts") or {}
    body_f = f.get("body") or {}
    fallback = body_f.get("fallback") or "Arial, Helvetica, sans-serif"
    body = f"'{body_f['family']}',{fallback}" if body_f.get("family") else fallback
    head_f = f.get("head") or {}
    head = f"'{head_f['family']}',{head_f.get('fallback') or fallback}" if head_f.get("family") else body
    out = {k: c[k] for k in TOKENS if k in c}
    out.update(font=body, font_head=head)
    return out

# Runs inside the scene. Keys arrive from the deck as messages and are dispatched as keyboard events;
# keys pressed while the scene has the focus are reported to the deck, which counts the scene's steps
# and keeps its own shortcuts working. Only real key presses are reported, never the dispatched ones.
_ADAPTER = """(function(){
  var CODES={ArrowDown:40,ArrowUp:38,ArrowLeft:37,ArrowRight:39,PageDown:34,PageUp:33,Home:36,End:35," ":32,Enter:13};
  function fire(type,key){
    var c=CODES[key]||0, e;
    try{ e=new KeyboardEvent(type,{key:key,code:key===" "?"Space":key,keyCode:c,which:c,bubbles:true,cancelable:true}); }catch(x){ return; }
    (document.activeElement||document.body||document.documentElement).dispatchEvent(e);
  }
  window.addEventListener("message",function(e){
    var d=e.data; if(!d||d.vs!=="key"||e.source!==window.parent) return;
    fire("keydown",d.key); fire("keyup",d.key);
  });
  window.addEventListener("keydown",function(e){
    if(!e.isTrusted||e.metaKey||e.ctrlKey||e.altKey) return;
    /* a scene without steps plays by itself and must not see the paging keys (it would pause or skip): they belong to the deck */
    if(window.VS_SCENE&&window.VS_SCENE.steps===0&&CODES[e.key]){ e.stopImmediatePropagation(); e.preventDefault(); }
    try{ window.parent.postMessage({vs:"scene-key",key:e.key},"*"); }catch(x){}
  },true);
  window.addEventListener("load",function(){ try{ window.parent.postMessage({vs:"scene-ready"},"*"); }catch(x){} });
})();"""

def _script_json(v):
    return json.dumps(v, ensure_ascii=False).replace("</", "<\\/").replace("<!--", "<\\!--")

def embed_scene_html(text, config=None, css_vars=None, fonts_css=None, steps=None):
    """index.html of a scene -> the version that runs inside a slide: class vs-embedded on the root element,
    window.VS_SCENE and the key adapter before any script of the scene, the brand's values on its custom properties."""
    def root(m):
        attrs = m.group(1)
        c = re.search(r'\bclass\s*=\s*(["\'])(.*?)\1', attrs, re.S)
        if c:
            if "vs-embedded" in c.group(2).split(): return m.group(0)
            return "<html" + attrs[:c.start(2)] + (c.group(2) + " vs-embedded").strip() + attrs[c.end(2):] + ">"
        return f'<html{attrs} class="vs-embedded">'
    had_root = bool(re.search(r"<html\b", text, re.I))
    text = re.sub(r"<html\b([^>]*)>", root, text, count=1, flags=re.I)
    head = "\n<script>window.VS_SCENE=" + _script_json({"config": config or {}, "embedded": True, "steps": steps}) + ";"
    if not had_root:
        head += "document.documentElement.classList.add('vs-embedded');"
    head += "</script>\n<script>" + _ADAPTER + "</script>\n"
    if fonts_css:     # the brand's @font-face rules, so a brand typeface written to a font variable can load in here
        head += "<style>" + fonts_css.replace("</", "<\\/") + "</style>\n"
    if css_vars:      # html.vs-embedded:root is more specific than the scene's own :root, wherever its stylesheet stands
        head += "<style>html.vs-embedded:root{" + "".join(f"{k}:{str(v).replace('<', '').replace('}', '')};" for k, v in css_vars.items()) + "}</style>\n"
    for pat in (r"<head\b[^>]*>", r"<html\b[^>]*>", r"<!doctype[^>]*>"):
        m = re.search(pat, text, re.I)
        if m:
            return text[:m.end()] + head + text[m.end():]
    return head + text

def _scene_images(v, env, folder, inline=False):
    """Images named in a scene's config were turned into {{IMG_x}} placeholders by the renderer.
    A scene loads files, not data URIs from the deck: copy them next to the scene and name the copy."""
    if isinstance(v, dict): return {k: _scene_images(x, env, folder, inline) for k, x in v.items()}
    if isinstance(v, list): return [_scene_images(x, env, folder, inline) for x in v]
    m = re.fullmatch(r"\{\{IMG_([A-Z0-9_]+)\}\}", v) if isinstance(v, str) else None
    path = (env.get("images") or {}).get(m.group(1)) if m else None
    if not path:
        return v
    if inline:        # scene.json says "images": "data": a scene that draws images to a canvas or WebGL texture cannot read
        import build as B                                  # files from inside its sandbox, data URIs it can
        return B.datauri(path, 1600)
    os.makedirs(os.path.join(folder, "media"), exist_ok=True)
    name = hashlib.md5(path.encode()).hexdigest()[:6] + "_" + os.path.basename(path)
    shutil.copy2(path, os.path.join(folder, "media", name))
    return "media/" + urllib.parse.quote(name)

def prepare_scene(name, env, config=None, css_vars=None, steps=None):
    """Copy a scene into <deck>/assets/scenes/<name>/ and write the page one slide shows.
    Returns {"src": address relative to the built HTML, "meta": scene.json, "dir": the copy} or None with a warning."""
    scenes = env.get("scenes")
    if scenes is None:
        scenes = env["scenes"] = load_scenes(env.get("brand_dir"))
    s = scenes.get(str(name))
    if not s:
        _warn(env, f"scene not found: {name}" + (f" (available: {', '.join(sorted(scenes))})" if scenes else " (no scenes installed)"))
        return None
    base = _base(env)
    folder_name = re.sub(r"[^A-Za-z0-9._-]+", "-", os.path.basename(s["dir"])) or "scene"
    root = os.path.join(base, "assets", "scenes"); dst = os.path.join(root, folder_name)
    done = env.setdefault("scenes_copied", set())
    if dst not in done:                                    # once per build; pages of other builds (handout) stay, prune() clears old ones
        shutil.copytree(s["dir"], dst, ignore=shutil.ignore_patterns("__pycache__", ".DS_Store", "slide-????????.html"), dirs_exist_ok=True)
        done.add(dst)
    meta = s["meta"]
    tokens = token_values(env.get("brand"))
    fonts = ""
    if env.get("brand") and any(tok in ("font", "font_head") for tok in list((meta.get("vars") or {}).values()) + list((css_vars or {}).values())):
        if "scene_fonts" not in env:                       # only scenes that take a brand typeface carry its files
            import build as B
            try: env["scene_fonts"] = B.fonts_css(env["brand"])
            except Exception: env["scene_fonts"] = ""      # the scene then keeps its own typeface
        fonts = env["scene_fonts"]
    values = {}
    for prop, token in list((meta.get("vars") or {}).items()) + list((css_vars or {}).items()):
        if not str(prop).startswith("--"):
            _warn(env, f"scene {name}: '{prop}' is not a custom property (they start with --)"); continue
        if token in ("font", "font_head") and not fonts: continue      # no loadable brand typeface: the scene keeps its own
        if token in tokens: values[prop] = tokens[token]
        elif token in TOKENS: continue                     # a token this brand does not define: the scene keeps its own value
        else: values[prop] = token                         # a slide may also give a plain CSS value
    cfg = _scene_images(config or {}, env, dst, meta.get("images") == "data")            # passed on as given: scenes merge it with a shallow Object.assign
    unknown = sorted(set(cfg) - set(meta.get("config") or cfg)) if isinstance(cfg, dict) else []
    if unknown:
        _warn(env, f"scene {name}: config keys it does not document: {', '.join(unknown)}")
    try: steps = max(0, int(steps if steps not in (None, "") else meta.get("steps") or 0))      # the slide's own number wins over the scene's
    except (TypeError, ValueError): steps = 0
    html = embed_scene_html(open(os.path.join(dst, "index.html"), encoding="utf-8").read(), cfg, values, fonts, steps)
    page = "slide-" + hashlib.md5((_script_json(cfg) + json.dumps(values, sort_keys=True) + fonts + str(steps)).encode()).hexdigest()[:8] + ".html"
    open(os.path.join(dst, page), "w", encoding="utf-8").write(html)
    return {"src": _url(os.path.relpath(os.path.join(dst, page), base)), "meta": meta, "dir": dst, "steps": steps}


# ---------------------------------------------------------------- the box on the slide

def _poster_image(path, env):
    """Register an image file for embedding and return its placeholder (same naming as the renderer)."""
    name = "FULL_" + hashlib.md5(path.encode()).hexdigest()[:10].upper()
    env.setdefault("images", {})[name] = path
    return "{{IMG_" + name + "}}"

def _box(kind, attrs, poster, title, line="", label="", fit="cover"):
    a = "".join(f' data-{k}' + ("" if v is True else f'="{_esc(v)}"') for k, v in attrs.items() if v not in (None, False, ""))
    if poster:
        inner = f'<img src="{poster}" alt="">' + (f'<span class="murl">{_esc(line)}</span>' if line else "")
    else:
        inner = ('<div class="mph">' + (f'<small>{_esc(label)}</small>' if label else "") + (f'<b>{_esc(title)}</b>' if title else "")
                 + (f'<span>{_esc(line)}</span>' if line else "") + '</div>')
    live = '<button class="mplay" type="button" data-export="off" aria-label="Play"></button><div class="mnote" data-export="off"></div>' if kind else ""
    return (f'<div class="mbox {fit}"' + (f' data-media="{kind}"' if kind else "") + a + '>'
            f'<div class="mposter">{inner}</div>{live}</div>')

def _labels(env):
    de = env.get("lang") == "de"
    return {"video": "Video", "embed": "Website" if not de else "Webseite", "scene": "Scene" if not de else "Szene",
            "missing": "File to come" if not de else "Datei folgt"}

def _short(url):
    return re.sub(r"^https?://(www\.)?", "", str(url)).rstrip("/")

def _slide(env):
    return env.get("slide") or {}

def _brand_video(env, background=None):
    """The brand's own video for the samples (@video): (address for a slot, poster path or None), or (None, None)."""
    b = env.get("brand") or {}
    vids = [v for v in (b.get("videos") or []) if v.get("file") and os.path.isfile(os.path.join(b.get("_dir") or "", v["file"]))]
    if background is not None:
        vids = sorted(vids, key=lambda v: bool(v.get("background")) != background)
    if not vids:
        return None, None
    poster = os.path.join(b["_dir"], vids[0]["poster"]) if vids[0].get("poster") else None
    return "brand:" + vids[0]["file"], (poster if poster and os.path.isfile(poster) else None)

def video_box(env):
    """{{>video}}: a local video file, a YouTube or Vimeo link, a remote video file, or any other address as an iframe."""
    s, L = _slide(env), _labels(env)
    src = str(s.get("src") or s.get("url") or s.get("file") or "").strip()
    title = _plain(s.get("title") or s.get("name"))
    full = (s.get("layout") or "full") != "boxed"
    # a video is shown whole; "cover" (fills the area, crops) only when the slide asks for it
    fit = "cover" if str(s.get("fit") or "").lower() == "cover" else "contain"
    ratio = re.sub(r"\s*[:/x]\s*", " / ", str(s.get("ratio") or "").strip())
    ratio = ratio if re.fullmatch(r"\d+(\.\d+)? / \d+(\.\d+)?", ratio) else None
    poster = s.get("poster") or ""
    if src == "@video":                                    # sample of a master: the brand's own film, a placeholder without one
        src, own = _brand_video(env, background=False)
        src = src or ""
        if own and not poster: poster = _poster_image(own, env)
    start, end = seconds(s.get("start")), seconds(s.get("end"))
    autoplay, loop, muted = _flag(s.get("autoplay"), True), _flag(s.get("loop")), _flag(s.get("muted"))
    if not src:
        if not env.get("sample"): _warn(env, "video slide without a file or link (slot src)")
        return _box("", {}, poster, title, "", L["video"], fit)
    if is_remote(src):
        p = player(src, start, end, autoplay, loop, muted)
        if p:
            _note(env, p["provider"], p["watch"], True)
            # YouTube answers "error 153" when the page is a file:// document: the engine then shows the poster and a link
            return _box("player", {"provider": p["provider"], "embed": p["embed"], "url": p["watch"], "nofile": p["provider"] == "youtube",
                                   "allow": ALLOW_PLAYER, "sandbox": SANDBOX_REMOTE, "online": True, "ratio": ratio}, poster, title, _short(p["watch"]), L["video"], fit)
        if urllib.parse.urlsplit(src).path.lower().endswith(VIDEO_EXT):
            _note(env, "remote video", src, True)
            return _box("video", {"src": src, "url": src, "start": start and _num(start), "end": end and _num(end), "autoplay": autoplay, "loop": loop,
                                  "muted": muted, "controls": _flag(s.get("controls")), "online": True, "ratio": ratio}, poster, title, _short(src), L["video"], fit)
        _note(env, "embed", src, True)
        return _box("iframe", {"embed": src, "url": src, "allow": ALLOW_PLAYER, "sandbox": SANDBOX_REMOTE, "online": True}, poster, title, _short(src), L["video"], fit)
    rel = link_file(src, env, "video")
    if not rel:
        return _box("", {}, poster, title, f"{L['missing']}: {src}", L["video"], fit)
    if not rel.lower().endswith(VIDEO_EXT):
        _warn(env, f"{src}: browsers play mp4 (H.264) and webm; this file type may not play")
    _note(env, "video", urllib.parse.unquote(rel))
    return _box("video", {"src": rel, "start": start and _num(start), "end": end and _num(end), "autoplay": autoplay, "loop": loop, "muted": muted,
                          "controls": _flag(s.get("controls")), "ratio": ratio}, poster, title, "", L["video"], fit)

def background_video(env):
    """{{>bgvideo}}: the slot `video` of a photo, chapter or statement slide as a silent loop behind the text.
    Local files only (deck folder, or brand:<path> for a file of the brand library); nothing is written without one."""
    s = _slide(env)
    src = str(s.get("video") or "").strip()
    if src == "@video":
        src = _brand_video(env, background=True)[0] or ""
    if not src:
        return ""
    if is_remote(src):
        if not urllib.parse.urlsplit(src).path.lower().endswith(VIDEO_EXT):
            _warn(env, f"background video must be a video file, not a player page: {src}")
            return ""
        _note(env, "remote video", src, True)
        return f'<div class="bgvideo" data-bgvideo="{_esc(src)}" data-export="off"></div>'
    rel = link_file(src, env, "background video")
    if not rel:
        return ""
    _note(env, "video", urllib.parse.unquote(rel))
    return f'<div class="bgvideo" data-bgvideo="{_esc(rel)}" data-export="off"></div>'

def embed_box(env):
    """{{>embed}}: a website, Figma, Loom and the like in a sandboxed iframe, or a local HTML file of the deck folder."""
    s, L = _slide(env), _labels(env)
    src = str(s.get("url") or s.get("src") or "").strip()
    title = _plain(s.get("title") or s.get("name"))
    poster = s.get("poster") or ""
    if not src:
        if not env.get("sample"): _warn(env, "embed slide without an address (slot url)")
        return _box("", {}, poster, title, "", L["embed"])
    want = [x.strip().lower() for x in re.split(r"[;,]", str(s.get("allow") or "")) if x.strip()]
    refused = [x for x in want if x not in ALLOW_OPTIONAL]
    if refused:
        _warn(env, f"embed {src}: not granted to the page: {', '.join(refused)} (possible: {', '.join(ALLOW_OPTIONAL)})")
    allow = "; ".join(dict.fromkeys([ALLOW_EMBED] + [x for x in want if x in ALLOW_OPTIONAL]))
    if is_remote(src):
        p = player(src)                                    # a video link in an embed slide still gets the privacy-friendly player
        _note(env, "embed", src, True)
        if p:
            return _box("player", {"provider": p["provider"], "embed": p["embed"], "url": p["watch"], "nofile": p["provider"] == "youtube",
                                   "allow": ALLOW_PLAYER, "sandbox": SANDBOX_REMOTE, "online": True}, poster, title, _short(p["watch"]), L["embed"])
        return _box("iframe", {"embed": src, "url": src, "allow": allow, "sandbox": SANDBOX_REMOTE, "online": True}, poster, title, _short(src), L["embed"])
    rel = link_file(src, env, "page")
    if not rel:
        return _box("", {}, poster, title, f"{L['missing']}: {src}", L["embed"])
    _note(env, "page", urllib.parse.unquote(rel))
    return _box("iframe", {"embed": rel, "allow": allow, "sandbox": SANDBOX_LOCAL}, poster, title, "", L["embed"])

def scene_box(env):
    """{{>scene}}: an animated scene from the brand library or the framework, copied into the deck folder."""
    s, L = _slide(env), _labels(env)
    name = str(s.get("scene") or "").strip()
    title = _plain(s.get("title") or s.get("name"))
    poster = s.get("poster") or ""
    if not name:
        if not env.get("sample"): _warn(env, "scene slide without a scene (slot scene, see `vs.py scenes`)")
        return _box("", {}, poster, title, "", L["scene"])
    config, css_vars = s.get("config"), s.get("vars")
    p = prepare_scene(name, env, config if isinstance(config, dict) else {}, css_vars if isinstance(css_vars, dict) else {}, s.get("steps"))
    if not p:
        return _box("", {}, poster, title or name, f"{L['missing']}: {name}", L["scene"])
    meta = p["meta"]
    if not poster and meta.get("poster") and os.path.exists(os.path.join(p["dir"], meta["poster"])):
        poster = _poster_image(os.path.join(p["dir"], meta["poster"]), env)
    steps = p["steps"]
    _note(env, "scene", name, meta.get("online"))
    return _box("scene", {"embed": p["src"], "scene": name, "steps": str(steps), "sandbox": SANDBOX_LOCAL, "allow": "autoplay; fullscreen",
                          "online": bool(meta.get("online"))}, poster, title or meta.get("title") or name, "", L["scene"])


# ---------------------------------------------------------------- what a built deck refers to

_BOX = re.compile(r'<div class="mbox[^"]*"([^>]*)>')
_ATTR = re.compile(r'\bdata-([a-z]+)(?:="([^"]*)")?')

def scan(html):
    """The media boxes of a built deck: one dict of data attributes per box."""
    out = []
    for m in _BOX.finditer(html):
        d = {k: (v.replace("&quot;", '"').replace("&lt;", "<").replace("&gt;", ">").replace("&amp;", "&") if v is not None else True) for k, v in _ATTR.findall(m.group(1))}
        d = {k: (True if v == "" and k in ("autoplay", "loop", "muted", "online", "nofile", "controls") else v) for k, v in d.items()}
        if d.get("media"):
            out.append(d)
    return out

def summary(items):
    """One line about the linked media of a deck, for the build output. items: env["media"]."""
    seen, parts, online = set(), {}, []
    for it in items or []:
        key = (it["kind"], it["ref"])
        if key in seen: continue
        seen.add(key)
        kind = "video" if it["kind"] in ("video", "remote video", "youtube", "vimeo") else it["kind"]
        parts[kind] = parts.get(kind, 0) + 1
        if it["online"]: online.append(it["ref"] if it["kind"] != "scene" else f"scene {it['ref']}")
    text = ", ".join(f"{n} {k}{'s' if n > 1 else ''}" for k, n in parts.items())
    return text, online

def referenced_files(deck_dir, html_files):
    """Files under the deck folder the built HTML files refer to, relative paths. A scene counts with its whole folder."""
    root = os.path.realpath(deck_dir); out, online = set(), []
    def add(path):
        real = os.path.realpath(path)
        if real.startswith(root + os.sep) and os.path.isfile(real):
            out.add(os.path.relpath(real, root))
    for fn in html_files:
        for box in scan(open(os.path.join(deck_dir, fn), encoding="utf-8").read()):
            ref = box.get("src") or box.get("embed") or ""
            if box.get("online") is True:
                online.append(("scene " + str(box.get("scene"))) if box["media"] == "scene" else str(box.get("url") or ref))
            if not ref or is_remote(ref):
                continue
            path = os.path.join(deck_dir, urllib.parse.unquote(ref))
            if box["media"] == "scene":
                for d, _, files in os.walk(os.path.dirname(path)):
                    for f in files:
                        if f != ".DS_Store": add(os.path.join(d, f))
            else:
                add(path)
    return sorted(out), list(dict.fromkeys(online))

def prune(deck_dir):
    """Remove scene pages no built HTML of the deck folder shows any more (they are written per slide and build)."""
    root = os.path.join(deck_dir, "assets", "scenes")
    if not os.path.isdir(root):
        return
    htmls = [f for f in os.listdir(deck_dir) if f.endswith(".html")]
    used = {urllib.parse.unquote(str(b.get("embed"))) for b in scan_all(deck_dir, htmls) if b.get("media") == "scene"}
    for n in os.listdir(root):
        d = os.path.join(root, n)
        if not os.path.isdir(d): continue
        for f in os.listdir(d):
            if re.fullmatch(r"slide-[0-9a-f]{8}\.html", f) and f"assets/scenes/{n}/{f}" not in used:
                os.remove(os.path.join(d, f))
        if not any(u.startswith(f"assets/scenes/{n}/") for u in used):
            shutil.rmtree(d)
    if not used:
        shutil.rmtree(root)
        try: os.rmdir(os.path.dirname(root))
        except OSError: pass

def scan_all(deck_dir, html_files):
    out = []
    for fn in html_files:
        out += scan(open(os.path.join(deck_dir, fn), encoding="utf-8").read())
    return out
