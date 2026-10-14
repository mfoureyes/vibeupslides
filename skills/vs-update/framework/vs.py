#!/usr/bin/env python3
"""vibeupslides: one command for the whole framework.

    vs.py init                                   set up the workspace (framework, Python environment, browser)
    vs.py status                                 versions, brands, decks, update check
    vs.py update                                 take over a newer framework from the installed skills
    vs.py backup [--out <folder>]                brands and decks as one file, to keep them beyond a session or pass them on
    vs.py restore <file>                         bring the brands and decks of a backup into the workspace
    vs.py doctor                                 what this environment allows: folder, Python, browser, network, local server

  Brand library (the vs-build skill)
    vs.py ingest <brand> <files...>              read documents the user has: style guide PDF, PowerPoint master, logos, fonts
    vs.py analyze <url> --brand <name>           read a website, create the brand library, build the master preview
    vs.py preview <brand>                        rebuild the master slides of a brand and their contact sheets
    vs.py brands | show <brand>                  list brands, show one
    vs.py set <brand> key=value ...              change brand.json, e.g. colors.accent=#D50C2F shape.motif=block
    vs.py logo trim|inverse <brand> [file]       cut margins off the logo, make a white version for dark slides
    vs.py fonts <brand>                          licence and file status of every typeface
    vs.py fonts accept <brand> [family]          use downloaded files whose licence the user confirmed
    vs.py fonts add <brand> <files...> [--family F] [--weight 700] [--style italic]
    vs.py fonts google <brand> "<Family>" --role head|body      take an open typeface as substitute
    vs.py videos <brand> [url]                   save the website's own video files into the library, for video slides and backgrounds
    vs.py elements <brand>                       the brand's library of icons, arrows and shapes from its website, by the names a deck uses
    vs.py masters <brand> [--full]               the master slides of a brand with their slots
    vs.py voice <brand> [files...] [--again]     how the brand writes: measure its texts, draft voice.md and the rules a build checks; files are sample texts to add
    vs.py voice <brand> --check "text" [--lang de]   check one piece of text against the brand's rules
    vs.py motion --deck <deck> [--compare] [--set <name>|brand] [--level calm|standard|expressive]
                                                 the movement of one presentation: the sets side by side on its own slides, its own set and strength
    vs.py motion <brand> [--compare] [--strip [set|all]] [--set <name>] [--level calm|expressive] [--reset] [--site]
                                                 motion sets with their character, among them `site`, copied from the brand's website; all sets playing side by side;
                                                 film strip of a set as a picture; choose the brand's set; --site makes the copied set again

  Decks (the vs-create skill)
    vs.py new <deck> --brand <name> [--langs en,de] [--from <deck>]
                                                 a deck folder with deck.json, sources/, research/, images/; --from takes sources and research of an earlier deck along
    vs.py shared <brand> [slide <name> --from <deck> --slide N | fact <key> <value> [--lang de]]
                                                 what the brand's decks share: slides (team, contact) and facts (address, figures); make a slide shared, set a fact
    vs.py design --examine <files, addresses> | <brand> --style <name> [--ground --ink --accent --head --body --radius …] | --gallery [--with <brand>] [--pick a,b,c]
                                                 a look from nothing: read the examples a user likes, make a look of their own from them (or from one of six styles), show looks side by side
    vs.py forms <brand> [--promote <deck> --slide N --name <name>]
                                                 forms of the brand's own: its masters and who uses them, free slides whose form came up again; make such a slide a master
    vs.py refresh [--brand <name>] [--check] [--all] [--except <deck>]
                                                 build again every deck that is behind its brand (shared slides and facts, look, framework); --check only lists them
    vs.py langs <deck> [--add fr] | vs.py langs --brand <name> [--add fr]
                                                 the languages of a deck or a brand; add one later without rebuilding masters or decks: lists the texts to translate
    vs.py build <deck> [--pdf] [--handout] [--only 3,7] [--no-shots]
    vs.py build <deck> --mode reading|live       the other version of the deck next to the main one: to be read, or to be presented
    vs.py titles <deck>                          the slide titles in a row, per language: the argument without the slides
    vs.py video <deck> --slide 3 --seconds 7
    vs.py edit <deck> [--port N] [--no-open] [--reopen]
                                                 edit the deck in the browser: type into the slides, reorder, duplicate and delete; every change goes into deck.json
    vs.py apply <deck> [file]                    every built deck can be edited where it is opened, without a server (the pencil): it saves the changes into itself
                                                 and into <deck>.edits.json; this brings them into deck.json and builds the deck
    vs.py present <deck> [--port N] [--no-open]  serve the deck folder on this computer (needed for YouTube, better for the presenter view)
    vs.py pack <deck>                            zip of the HTML and the files it links, for sending a deck with video

The workspace is one local folder, $VIBEUPSLIDES_HOME or ~/vibeupslides (in Cowork: a folder the user shared):
    framework/   the engine (replaced on update)      library/<brand>/   brand.json, styleguide.md, voice.md, theme.css, masters/, elements/, fonts/, logos/, images/
    decks/<deck>/   deck.json, images/, the built HTML; with video also the video files and assets/
"""
import json, os, re, shutil, subprocess, sys, time

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
REPO = "mfoureyes/vibeupslides"
REMOTE_VERSION = f"https://raw.githubusercontent.com/{REPO}/main/skills/vs-update/framework/VERSION"


def home():
    return os.environ.get("VIBEUPSLIDES_HOME") or os.path.join(os.path.expanduser("~"), "vibeupslides")

def version(folder=HERE):
    try: return open(os.path.join(folder, "VERSION"), encoding="utf-8").read().strip()
    except OSError: return "0"

def _v(s):
    return tuple(int(x) for x in re.findall(r"\d+", s)[:3]) or (0,)

def sandboxed():
    """True in a session that runs in a virtual machine and sees the user's folders as mounts (Cowork): the home
    folder does not last there, and a Python environment made there does not run on the user's computer."""
    v = os.environ.get("VIBEUPSLIDES_SANDBOX")
    if v is not None: return v not in ("", "0")
    return (os.path.expanduser("~").startswith("/sessions/") or os.environ.get("CLAUDE_CODE_REMOTE", "").lower() in ("1", "true")
            or "cowork" in os.environ.get("CLAUDE_CODE_ENTRYPOINT", ""))

def temporary():
    """True when the workspace lives in the session itself and is gone with it: brands and decks are kept with backup."""
    ws, user = os.path.realpath(home()) + os.sep, os.path.realpath(os.path.expanduser("~")) + os.sep
    return sandboxed() and ws.startswith(user) and not ws.startswith(os.path.join(user, "mnt") + os.sep)   # ~/mnt holds the user's folders

def outbox():
    """Where a session puts files for the user; the workspace when there is no such place."""
    for p in (os.environ.get("VIBEUPSLIDES_OUTBOX"), "/mnt/user-data/outputs", os.path.join(os.path.expanduser("~"), "mnt", "outputs")):
        if p and os.path.isdir(p): return p
    return home()

BACKUP_PREFIX = "vibeupslides-workspace"

def cmd_backup(args):
    """Brands and decks as one file: to keep them beyond a session, or to pass a brand on."""
    import zipfile
    ws = home(); dest = arg(args, "--out") or outbox(); os.makedirs(dest, exist_ok=True)
    out = os.path.join(dest, BACKUP_PREFIX + ".zip"); n = 0                 # one name: the newest replaces the one before
    with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as z:
        z.writestr("workspace.json", json.dumps({"vibeupslides": version(), "date": time.strftime("%Y-%m-%d %H:%M")}))
        for top in ("library", "decks"):
            for d, dirs, files in os.walk(os.path.join(ws, top)):
                dirs[:] = [x for x in dirs if x not in ("__pycache__", "preview", "shots", "built")]   # contact sheets: preview and build make them again
                if os.path.basename(d) == "raw" and os.path.dirname(os.path.dirname(d)) == os.path.join(ws, "library"):
                    dirs[:] = [x for x in dirs if x != "screens"]      # the screenshots of the website: `analyze --again` takes them again
                for f in files:
                    if f == ".DS_Store" or f == "_edit.html" or f.endswith(" (edit).html"): continue
                    if f == "preview.html" and os.path.dirname(d) == os.path.join(ws, "library"): continue      # the master preview: built again by `preview`
                    full = os.path.join(d, f); z.write(full, os.path.relpath(full, ws)); n += 1
    lib, decks = os.path.join(ws, "library"), os.path.join(ws, "decks")
    print(f"backup: {out} ({os.path.getsize(out) / 2**20:.1f} MB, {n} files)")
    print("brands:", ", ".join(sorted(os.listdir(lib))) if os.path.isdir(lib) and os.listdir(lib) else "none", "| decks:", ", ".join(sorted(os.listdir(decks))) if os.path.isdir(decks) and os.listdir(decks) else "none")
    print("Contact sheets and the screenshots of the website are left out; `vs.py preview <brand>`, `vs.py build <deck>` and `vs.py analyze <url> --brand <brand> --again` make them again.")
    print("Give this file to the user to keep, or put it into their connected folder. In a new session `vs.py restore <file>` brings brands and decks back.")

def cmd_restore(args):
    import zipfile
    src = positional(args)[0]; ws = home(); n = 0; tops = {}
    with zipfile.ZipFile(src) as z:
        for m in z.infolist():
            name = m.filename.replace("\\", "/"); parts = name.split("/")
            if m.is_dir() or parts[0] not in ("library", "decks") or len(parts) < 3 or ".." in parts or name.startswith("/"): continue
            dst = os.path.join(ws, *parts); os.makedirs(os.path.dirname(dst), exist_ok=True)
            with z.open(m) as a, open(dst, "wb") as b: shutil.copyfileobj(a, b)
            tops.setdefault(parts[0], set()).add(parts[1]); n += 1
    print(f"restored {n} files from {os.path.basename(src)} | brands: {', '.join(sorted(tops.get('library', []))) or 'none'} | decks: {', '.join(sorted(tops.get('decks', []))) or 'none'}")

def _platform():
    import platform
    return f"{sys.platform}-{platform.machine()}"

def _home_venv():
    return os.path.join(os.path.expanduser("~"), ".vibeupslides", "venv")

def _venv_dirs(ws):
    return [d for d in (os.environ.get("VIBEUPSLIDES_VENV"), os.path.join(ws, ".venv"), _home_venv()) if d]

def _venv(ws):
    """(folder, python) of the Python environment to use: $VIBEUPSLIDES_VENV, the workspace's own, or the one in the
    home folder. One made on another system (a workspace in a shared folder) is passed over."""
    for d in _venv_dirs(ws):
        try:
            if open(os.path.join(d, ".platform"), encoding="utf-8").read().strip() != _platform(): continue
        except OSError:
            pass
        for rel in ("bin/python", "Scripts/python.exe"):
            p = os.path.join(d, rel)
            if os.path.exists(p): return d, p
    return None, None

def _venv_python(ws):
    return _venv(ws)[1]

def die(msg):
    print("ERROR:", msg); sys.exit(1)

def arg(args, flag, default=None):
    return args[args.index(flag) + 1] if flag in args and args.index(flag) + 1 < len(args) else default

def positional(args, flags_with_value=()):
    out, skip = [], False
    for a in args:
        if skip: skip = False; continue
        if a in flags_with_value: skip = True; continue
        if a.startswith("--"): continue
        out.append(a)
    return out


# ---------------------------------------------------------------- workspace, versions, updates

def payload_candidates():
    """Places where the installed vs-update skill keeps the framework."""
    ws, out = home(), []
    try:
        src = open(os.path.join(ws, ".source"), encoding="utf-8").read().strip()
        if src: out.append(src)
    except OSError:
        pass
    for root in (os.environ.get("VIBEUPSLIDES_PAYLOAD"), os.environ.get("CLAUDE_PLUGIN_ROOT") and os.path.join(os.environ["CLAUDE_PLUGIN_ROOT"], "skills", "vs-update", "framework")):
        if root: out.append(root)
    for base in (os.path.expanduser("~/.claude/skills"), os.path.expanduser("~/.agents/skills"), os.path.join(os.getcwd(), ".claude", "skills"),
                 os.path.join(os.getcwd(), ".agents", "skills"), os.path.expanduser("~/.codex/skills"), os.path.expanduser("~/.cursor/skills")):
        out.append(os.path.join(base, "vs-update", "framework"))
    seen, res = set(), []
    for p in out:
        rp = os.path.realpath(p)
        if rp not in seen and os.path.exists(os.path.join(rp, "VERSION")):
            seen.add(rp); res.append(rp)
    return res

def newest_payload():
    c = sorted(payload_candidates(), key=lambda p: _v(version(p)), reverse=True)
    return c[0] if c else None

LAUNCHER = ('#!/usr/bin/env python3\n"""vibeupslides launcher. The framework lives in framework/, see framework/vs.py."""\n'
            'import os, sys\nws = os.path.dirname(os.path.abspath(__file__))\nos.environ.setdefault("VIBEUPSLIDES_HOME", ws)\n'
            'cli = os.path.join(ws, "framework", "vs.py")\n'
            'import runpy; sys.argv[0] = cli; runpy.run_path(cli, run_name="__main__")\n')

def _ensure_env():
    """Run inside the workspace's own Python and keep the launcher current. An update is carried out by the code
    of the version before it, so the launcher it writes can be an old one: the first run of the new framework
    puts that right."""
    ws = os.path.abspath(home())
    if os.path.dirname(os.path.abspath(__file__)) != os.path.join(ws, "framework"):
        return                                             # run from the skill or a checkout, not from a workspace
    lp = os.path.join(ws, "vs.py")
    try:
        if os.path.exists(lp) and open(lp, encoding="utf-8").read() != LAUNCHER:
            open(lp, "w", encoding="utf-8").write(LAUNCHER)
    except OSError:
        pass
    vdir, py = _venv(ws)
    if py and os.path.realpath(sys.prefix) != os.path.realpath(vdir) and not os.environ.get("VS_NO_VENV"):
        os.execv(py, [py, os.path.abspath(__file__)] + sys.argv[1:])

def sync_framework(src, quiet=False):
    """Copy the framework into the workspace. Library and decks are never touched."""
    ws = home(); dst = os.path.join(ws, "framework")
    if os.path.realpath(src) == os.path.realpath(dst):
        return False
    old = version(dst) if os.path.isdir(dst) else None
    names = lambda folder: {n for n in os.listdir(os.path.join(folder, "scenes")) if os.path.exists(os.path.join(folder, "scenes", n, "scene.json"))} if os.path.isdir(os.path.join(folder, "scenes")) else set()
    came = sorted(names(src) - names(dst)) if old else []      # scenes this version brings that the workspace did not have
    tmp = dst + ".new"
    if os.path.exists(tmp): shutil.rmtree(tmp)
    shutil.copytree(src, tmp, ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))
    if os.path.isdir(dst): shutil.rmtree(dst)
    os.rename(tmp, dst)
    open(os.path.join(ws, ".source"), "w", encoding="utf-8").write(os.path.realpath(src))
    open(os.path.join(ws, "vs.py"), "w", encoding="utf-8").write(LAUNCHER)
    if came:
        try:
            log = _new_scenes(); log.update({n: version(dst) for n in came})
            os.makedirs(os.path.join(ws, ".cache"), exist_ok=True); json.dump(log, open(os.path.join(ws, ".cache", "new_scenes.json"), "w", encoding="utf-8"))
        except OSError: pass
    if not quiet:
        print(f"framework {old or '(none)'} -> {version(dst)} in {dst}")
    if came:
        pass      # the catalogue of animated scenes is parked: nothing to announce
    return True

def changelog_since(old, folder=HERE):
    """The entries of CHANGELOG.md that are newer than `old`."""
    try: text = open(os.path.join(folder, "CHANGELOG.md"), encoding="utf-8").read()
    except OSError: return ""
    out = []
    for block in re.split(r"(?m)^## ", text)[1:]:
        ver = block.split("\n", 1)[0].strip()
        if _v(ver) > _v(old or "0"):
            out.append("## " + block.strip())
    return "\n\n".join(out)

def remote_version():
    """Latest published version, asked at most once a day. Silent when offline."""
    cache = os.path.join(home(), ".cache", "latest.json")
    try:
        c = json.load(open(cache))
        if time.time() - c["t"] < 86400: return c["v"]
    except Exception:
        pass
    v = None
    try:
        import urllib.request
        v = urllib.request.urlopen(REMOTE_VERSION, timeout=3).read().decode().strip()
        if not re.fullmatch(r"\d+(\.\d+){1,2}", v): v = None
    except Exception:
        v = None
    try:
        os.makedirs(os.path.dirname(cache), exist_ok=True); json.dump({"t": time.time(), "v": v}, open(cache, "w"))
    except OSError:
        pass
    return v

def ensure_current():
    """Before a build: take over a newer framework from the installed skills, say so if a newer release exists."""
    ws = home()
    if os.path.realpath(HERE) != os.path.realpath(os.path.join(ws, "framework")):
        return
    cur = version()
    src = newest_payload()
    if src and _v(version(src)) > _v(cur):
        sync_framework(src)
        print(f"UPDATED: the framework was brought up to {version(src)}. What is new:\n{changelog_since(cur, src)}\n")
        sys.stdout.flush(); py = sys.executable
        os.execv(py, [py, os.path.join(ws, "framework", "vs.py")] + sys.argv[1:])
    latest = remote_version()
    installed = version(src) if src else cur
    if latest and _v(latest) > _v(installed):
        print(f"UPDATE AVAILABLE: VibeUpSlides {latest} is published, installed is {installed}. Run the vs-update skill to get it.\n")

def cmd_init(args):
    ws = home()
    for d in ("library", "decks", ".cache"):
        os.makedirs(os.path.join(ws, d), exist_ok=True)
    sync_framework(HERE, quiet=True)
    print("workspace:", ws, "| framework", version(os.path.join(ws, "framework")))
    old = os.path.join(os.path.expanduser("~"), ".vibeupslides", "brands")       # brands saved by VibeUpSlides 0.1
    if os.path.isdir(old):
        for n in sorted(os.listdir(old)):
            if os.path.exists(os.path.join(old, n, "brand.json")) and not os.path.exists(os.path.join(ws, "library", n)):
                shutil.copytree(os.path.join(old, n), os.path.join(ws, "library", n))
                os.environ["VIBEUPSLIDES_HOME"] = ws; _scaffold(n)
                print(f"brand '{n}' taken over from {old} (colours, fonts, logos); it still needs its style guide, theme and masters: vs-build")
    py = _venv_python(ws)
    if not py and "--no-venv" not in args:
        # in a sandbox the workspace is a folder of the user's computer: the environment stays outside it
        vdir = os.environ.get("VIBEUPSLIDES_VENV") or (_home_venv() if sandboxed() else os.path.join(ws, ".venv"))
        print("creating the Python environment in", vdir, "...")
        if os.path.isdir(vdir): shutil.rmtree(vdir)
        subprocess.check_call([sys.executable, "-m", "venv", vdir])
        open(os.path.join(vdir, ".platform"), "w", encoding="utf-8").write(_platform())
        py = _venv_python(ws)
    py = py or sys.executable
    def has(mod):
        return subprocess.call([py, "-c", f"import {mod}"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL) == 0
    if not (has("PIL") and has("playwright") and has("pypdfium2") and has("pypdf")):
        print("installing pillow, playwright, pypdfium2 and pypdf ...")
        subprocess.check_call([py, "-m", "pip", "install", "--quiet", "--disable-pip-version-check", "pillow", "playwright", "pypdfium2", "pypdf"])
    if not has("cv2"):                                      # finds faces in photos, so that no text is set over one; the checks work without it, by eye
        print("installing opencv (for the check that no text covers a face) ...")
        if subprocess.call([py, "-m", "pip", "install", "--quiet", "--disable-pip-version-check", "opencv-python-headless>=4.8,<5"]) != 0:
            print("opencv could not be installed: slides with text over a photo are named, look at them yourself")
    probe = "from playwright.sync_api import sync_playwright as s\nwith s() as p:\n    b=p.chromium.launch(); b.close()"
    if subprocess.call([py, "-c", probe], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL) != 0:
        print("installing Chromium for Playwright (about 150 MB, once) ...")
        if subprocess.call([py, "-m", "playwright", "install", "chromium"]) != 0:
            print("the browser could not be installed here")
    ok = subprocess.call([py, "-c", probe], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL) == 0
    print("python:", py, "| browser:", "ready" if ok else "NOT WORKING, run: " + py + " -m playwright install chromium")
    print(f"\nReady. From now on every step is one command:\n    python3 {os.path.join(ws, 'vs.py')} <command>")
    _temporary_note()
    if not sandboxed():
        print("To stop permission prompts for it, allow this command and this folder once:")
        cmd_permissions([])

def _temporary_note():
    if temporary():
        print("TEMPORARY WORKSPACE: this folder belongs to the session and does not last. After a brand or a deck is made or changed, run"
              f" `vs.py backup` and give the user the file it writes ({outbox()}); in a new session `vs.py restore <file>` brings everything back.")

def _legible_report(found, lang=None, limit=40):
    """Print what the look at every slide found: type too small, too little contrast, text cut off, at the edge or on top of other text."""
    tag = f"[{lang}] " if lang else ""
    hints = [(x, f[6:]) for x in found for f in x["findings"] if f.startswith("hint: ")]
    found = [dict(x, findings=[f for f in x["findings"] if not f.startswith("hint: ")]) for x in found]; found = [x for x in found if x["findings"]]
    n = sum(len(x["findings"]) for x in found)
    def tell():
        if hints: print(tag + f"  {len(hints)} hint(s), not faults: " + "; ".join(f"slide {x['slide']}: {f}" for x, f in hints[:4])[:600] + (" ..." if len(hints) > 4 else ""))
    if not n:
        print(tag + "legibility: clean"); tell(); return True
    print(tag + f"legibility: {n} finding(s) on {len(found)} slide(s)"); shown = 0
    for x in found:
        for f in x["findings"]:
            if shown < limit: print(f"  LEGIBILITY slide {x['slide']} ({x['title'][:40]}): {f}")
            shown += 1
    if shown > limit: print(f"  ... and {shown - limit} more")
    tell()
    return False

def cmd_permissions(args):
    ws = home().replace(os.path.expanduser("~"), "~")
    rules = [f"Bash(python3 {ws}/vs.py:*)", f"Read({ws}/**)", f"Edit({ws}/**)", f"Write({ws}/**)"]
    print(json.dumps({"permissions": {"allow": rules}}, indent=2))

def cmd_doctor(args):
    """What this environment allows: one report to read or to pass on."""
    import platform, socket, urllib.request, tempfile
    ws = home(); rows = []
    def row(name, ok, note=""):
        rows.append((name, ok, note)); print(f"{'ok  ' if ok else ('FAIL' if ok is False else '?   ')} {name}" + (f": {note}" if note else "")); sys.stdout.flush()
    print(f"vibeupslides {version()} doctor | {platform.platform()} | python {platform.python_version()} ({sys.executable})")
    print(f"home {os.path.expanduser('~')} | cwd {os.getcwd()} | sandboxed {sandboxed()} | user {os.environ.get('USER', '?')}")
    print("env:", {k: v for k, v in os.environ.items() if k.startswith(("VIBEUPSLIDES", "COWORK")) or k in ("CLAUDE_PLUGIN_ROOT", "CLAUDE_CODE_ENTRYPOINT")},
          "| other names:", " ".join(sorted(k for k in os.environ if k.startswith(("CLAUDE", "ANTHROPIC")) and k not in ("CLAUDE_PLUGIN_ROOT", "CLAUDE_CODE_ENTRYPOINT"))))
    print(f"temporary workspace {temporary()} | files for the user go to {outbox()} | additional directories {os.environ.get('CLAUDE_ADDITIONAL_DIRECTORIES', '-')} | environment {os.environ.get('CLAUDE_CODE_REMOTE_ENVIRONMENT_TYPE', '-')}")
    for mnt in (os.path.join(os.path.expanduser("~"), "mnt"), "/mnt", "/mnt/user-data"):
        if os.path.isdir(mnt): print(f"{mnt}:", sorted(os.listdir(mnt)))
    try: print("network mounts:", [l.split()[1] + " (" + l.split()[2] + ")" for l in open("/proc/mounts") if l.split()[2].startswith(("fuse", "nfs", "virtiofs", "9p", "cifs"))])
    except OSError: pass
    print("this file:", os.path.abspath(__file__))
    row("workspace", os.path.isdir(os.path.join(ws, "framework")), ws)
    try:
        t = os.path.join(ws, ".cache", "doctor.tmp"); os.makedirs(os.path.dirname(t), exist_ok=True)
        open(t, "w").write("x"); os.replace(t, t + "2"); row("workspace is writable", True)
    except OSError as e:
        row("workspace is writable", False, str(e))
    try:
        os.remove(os.path.join(ws, ".cache", "doctor.tmp2")); row("files in the workspace can be deleted (updates, rebuilding)", True)
    except OSError as e:
        row("files in the workspace can be deleted (updates, rebuilding)", False, f"{e}: the user has to allow deleting in this folder")
    row("framework source (for updates)", bool(newest_payload()), str(payload_candidates()))
    vdir, py = _venv(ws); row("python environment", bool(py), vdir or "none: run init")
    for mod in ("PIL", "playwright", "pypdfium2", "pypdf"):
        row("  module " + mod, subprocess.call([py or sys.executable, "-c", f"import {mod}"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL) == 0)
    probe = "from playwright.sync_api import sync_playwright as s\nwith s() as p:\n    b=p.chromium.launch(); pg=b.new_page(); pg.set_content('<p>x</p>'); pg.screenshot(); b.close()"
    r = subprocess.run([py or sys.executable, "-c", probe], capture_output=True, text=True)
    row("browser for checks, contact sheets and PDF", r.returncode == 0, next((l.strip() for l in r.stderr.splitlines() if "shared libraries" in l or "Executable doesn't exist" in l), (r.stderr.strip().splitlines() or [""])[-1])[:300])
    for name, url in (("network: PyPI (setup)", "https://pypi.org/simple/pillow/"), ("network: GitHub (update check)", REMOTE_VERSION.rsplit("/", 4)[0]),
                      ("network: any website (analyze)", "https://example.com/"), ("network: Google Fonts", "https://fonts.googleapis.com/css2?family=Inter"),
                      ("network: YouTube (video slides)", "https://www.youtube.com/")):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
            code = urllib.request.urlopen(req, timeout=8).status; row(name, True, str(code))
        except Exception as e:
            code = getattr(e, "code", None)
            row(name, True if code in (403, 404) else False, f"{type(e).__name__}: {e}"[:200])
    try:
        s = socket.socket(); s.bind(("127.0.0.1", 0)); port = s.getsockname()[1]; s.close(); row("local server (edit, present)", True, f"a port opens here ({port}), " + ("but the browser of the user does not reach it from this session: edit and present need the Code tab or a terminal" if sandboxed() else "and the browser of the user reaches it"))
    except OSError as e:
        row("local server (edit, present)", False, str(e))
    row("a browser of the user can be opened from here", None if sandboxed() else (shutil.which("open") or shutil.which("xdg-open") or shutil.which("start")) is not None, "not from a sandbox: built files are handed to the user" if sandboxed() else "")
    try: free = shutil.disk_usage(ws if os.path.isdir(ws) else os.path.expanduser("~")).free // 2**20
    except OSError: free = -1
    row("disk space", free > 600 or free < 0, f"{free} MB free")
    bad = [n for n, ok, _ in rows if ok is False]
    print(f"\n{len(rows) - len(bad)} of {len(rows)} fine." + (" Not working: " + "; ".join(bad) if bad else ""))

def cmd_status(args):
    ws = home(); fw = os.path.join(ws, "framework")
    print("workspace:", ws)
    print("framework:", version(fw) if os.path.isdir(fw) else "not installed (run init)")
    src = newest_payload()
    print("installed skills:", version(src) if src else "not found", f"({src})" if src else "")
    latest = remote_version()
    print("published:", latest or "unknown (offline or not published yet)")
    if src and _v(version(src)) > _v(version(fw)): print("-> the skills are newer than the workspace framework: run `vs.py update`")
    if latest and src and _v(latest) > _v(version(src)): print("-> a newer release exists: run the vs-update skill")
    _temporary_note()
    import build as B
    print("\nbrands:")
    for d in B.list_brands():
        b = json.load(open(os.path.join(d, "brand.json"), encoding="utf-8"))
        own = len([f for f in os.listdir(os.path.join(d, "masters")) if f.endswith(".html")]) if os.path.isdir(os.path.join(d, "masters")) else 0
        state = "confirmed" if b.get("confirmed") else "NOT YET CONFIRMED by the user"
        print(f"  {os.path.basename(d):22s} {b.get('name', ''):28s} {own} masters, {state}, framework {b.get('framework', '?')}")
    if not B.list_brands(): print("  none yet: run the vs-build skill")
    print("\ndecks:")
    root = os.path.join(ws, "decks")
    for n in sorted(os.listdir(root)) if os.path.isdir(root) else []:
        p = os.path.join(root, n, "deck.json")
        if os.path.exists(p):
            try: d = json.load(open(p, encoding="utf-8")); print(f"  {n:22s} {d.get('title', ''):28s} brand {d.get('brand')}, {len(d.get('slides', []))} slides")
            except ValueError: print(f"  {n:22s} deck.json is not valid JSON")

def cmd_update(args):
    ws = home(); cur = version(os.path.join(ws, "framework"))
    src = newest_payload()
    if not src: die("the vs-update skill was not found. Install the skill set: npx skills add " + REPO)
    if _v(version(src)) <= _v(cur) and "--force" not in args:
        print(f"The workspace framework is current ({cur})."); latest = remote_version()
        if latest and _v(latest) > _v(cur): print(f"A newer release ({latest}) is published. Update the skills first: npx skills update   (or: npx skills add {REPO})")
        return
    sync_framework(src)
    print("\nWhat is new:\n" + (changelog_since(cur, src) or "(no changelog entries)"))
    import render, build as B
    defaults = {n for n, m in render.load_masters(None).items() if m["body"] is not None and not m["meta"].get("preview_only") and not m["meta"].get("hidden")}
    for d in B.list_brands():
        own = {f[:-5] for f in os.listdir(os.path.join(d, "masters"))} if os.path.isdir(os.path.join(d, "masters")) else set()
        new = sorted(defaults - own)
        if new: print(f"brand {os.path.basename(d)}: new default masters it does not have yet: {', '.join(new)} (used from the framework until the brand gets its own)")


# ---------------------------------------------------------------- style

THEME_SKELETON = """/* Brand theme for {name}. Loaded after the engine and the tokens of brand.json.
   Write here what makes slides look like the website beyond colour and type: the label above titles,
   cards, buttons and chips, how images are treated, arrows, graphic elements. Use the tokens
   (var(--accent), var(--accent-text), var(--ink), var(--deep), var(--on), var(--muted), var(--line),
   var(--soft), var(--paper), var(--radius), var(--font-head)), never hex values.
   Elements saved in elements/ can be used as url(el:arrows/arrow.svg). See the vs-build skill. */

/* ---------- label above titles (.kicker) ---------- */

/* ---------- titles and accent word (h1, h2, em) ---------- */

/* ---------- cards, chips, badges ---------- */

/* ---------- images (.split .image, .gallery figure, .fullbleed .image, .person .pic) ---------- */

/* ---------- bullets, arrows, icons ---------- */

/* ---------- graphic elements (accent shape .wedge, patterns, rules) ---------- */
"""

STYLEGUIDE_SKELETON = """# Style guide: {name}

Source: {url} · read on {date} · framework {version}
This file is the brand's memory. Decks are designed and written from it. Fill every section from
what the website shows (screenshots in raw/screens, measurements in raw/components.json, copy in
raw/copy.md). Lines marked TODO are judgements the analysis could not make.

## Essence
TODO: three sentences. What kind of organisation is this, what does its design feel like (calm, loud,
technical, warm, playful, austere), and what is the one visual idea a slide must carry to be recognisably theirs.

## Colour
{colours}
TODO: how the site uses them: which colour carries large areas, where the accent appears, how much of it.

## Type
{type}
TODO: headline style (size contrast, case, tracking, tight or airy), how single words are highlighted.

## Layout and shape
Corner radius {radius}px · accent shape "{motif}".
TODO: grid and density, alignment (left, centred), white space, hard or soft edges, shadows or flat, typical section rhythm.

## Imagery
TODO: what is shown (people, product, places, illustration, abstract), how it is photographed (light, colour,
distance, staged or documentary), how images are treated (crop, radius, overlays, duotone, masks, frames).
Usable photos in images/: TODO one line per file: what it shows and which master suits it.

## Icons and arrows
{elements}
TODO: line or filled, stroke weight, corner style, where arrows appear (buttons, links, lists) and which form.

## Graphic elements
TODO: shapes, patterns, rules, gradients, dividers, decorative numerals: what exists on the site and where a
slide should use it. Name the files in elements/ that carry them.

## Components
TODO: label above headings (case, tracking, pill or plain, leading line), buttons and chips, cards
(border, shadow, radius, padding), lists, tables. Each as one line a designer could rebuild from.

## Motion
Profile in brand.json under "motion" (set, ease, duration, stagger, travel, change). What the site does is measured in raw/motion.json.
TODO: how the site moves (what enters how, how fast, how much at once, hover behaviour), which motion set was chosen
and why it fits the brand's character, whether the brand has a signature move of its own (motion.css), and which
intensity suits which occasion. See references/motion.md of the vs-build skill.

## Voice
Language: {lang}. How the brand writes is its own file: voice.md (the profile a writer works from), with the
rules a build checks in brand.json under "voice". See references/voice.md of the vs-build skill.

## Masters
TODO: one line per master in masters/: what was changed from the default and why, and which masters were
added for this brand. Which master to prefer for which content.

## Open points
{open}
"""

def _brand_info(b):
    f = b["fonts"]
    info = dict(b); info.pop("_dir", None)
    info["body_font"] = f["body"].get("family") or "System font"
    info["head_font"] = (f.get("head") or {}).get("family") or info["body_font"]
    return info

def _standins(b, tmp):
    """Images for the samples of the masters: the brand's own photos, neutral stand-ins otherwise."""
    from PIL import Image, ImageDraw
    d, c = b["_dir"], b["colors"]
    os.makedirs(tmp, exist_ok=True)
    photos = [os.path.join(d, p["file"]) for p in b.get("images") or [] if os.path.exists(os.path.join(d, p["file"]))]
    def stand(name, w, h, person=False):
        path = os.path.join(tmp, name)
        im = Image.new("RGB", (w, h), c["soft"]); dr = ImageDraw.Draw(im); cx, cy, u = w // 2, h // 2, min(w, h) // 8
        if person:
            dr.ellipse((cx - u, cy - 2 * u, cx + u, cy), fill=c["line"]); dr.rounded_rectangle((cx - 2 * u, cy + u // 3, cx + 2 * u, h + u), radius=u, fill=c["line"])
        else:
            dr.rounded_rectangle((cx - u * 1.4, cy - u, cx + u * 1.4, cy + u), radius=u // 5, outline=c["line"], width=max(4, u // 9))
            dr.ellipse((cx - u // 2, cy - u // 2, cx + u // 2, cy + u // 2), outline=c["line"], width=max(4, u // 9))
        im.save(path, quality=88); return path
    pick = lambda i, name, w, h: photos[i % len(photos)] if photos else stand(name, w, h)
    lg = b["logos"]
    logo = os.path.join(d, lg["primary"]) if lg.get("primary") and os.path.exists(os.path.join(d, lg["primary"])) else None
    inv = os.path.join(d, lg["primary_inverse"]) if lg.get("primary_inverse") and os.path.exists(os.path.join(d, lg["primary_inverse"])) else logo
    return {"photo": pick(0, "full.jpg", 1920, 1080), "tall": pick(1, "tall.jpg", 900, 1080), "wide": pick(2, "wide.jpg", 1200, 900),
            "portrait": stand("portrait.jpg", 600, 600, True), "logo": logo or "", "logo_inv": inv or ""}

def _render_and_build(deck, b, out, deck_dir=None, standins=None, title=None, pdf=False, mode=None, edit=False):
    import build as B, render, shared
    deck, _ = shared.resolve(deck, b["_dir"])               # shared slides and facts of the brand
    if deck.get("motion_set"):                              # a presentation may move in another set than its brand
        import motion as M
        if deck["motion_set"] in M.sets(b["_dir"]): b = dict(b, motion=dict(b.get("motion") or {}, set=deck["motion_set"]))
        else: print(f"WARNING: the deck names the motion set '{deck['motion_set']}', which does not exist: the brand's set is used")
    # a deck carries its own editing (the pencil): the version to present, not handouts, previews or samples
    own = bool(deck_dir) and not deck.get("sample") and not deck.get("handout") and (mode or deck.get("mode") or "live") == "live" and os.path.exists(os.path.join(deck_dir, "deck.json"))
    edit = edit or own
    masters = render.load_masters(b["_dir"])
    env = {"mode": mode or deck.get("mode") or "live", "brand_dir": b["_dir"], "deck_dir": deck_dir, "standins": standins or {}, "brand_name": b.get("name", ""), "brand_info": _brand_info(b),
           "brand": b, "out_dir": os.path.dirname(os.path.abspath(out)), "edit": edit}
    slides = render.render_deck(deck, masters, env)
    images = dict(env["images"])
    if env.get("need_logo_inv"):
        lg = b["logos"]; p = lg.get("primary_inverse") or lg.get("primary")
        if p: images["LOGO_INV"] = os.path.join(b["_dir"], p)
    B.build(None, out, brand=b, title=title or deck.get("title"), images=images, slides_text=slides, pdf=pdf, mode=env["mode"],
            footer_left=deck.get("footer_left"), footer_right=deck.get("footer_right"), lang=(deck.get("langs") or [None])[0], scheme=deck.get("scheme"))
    if edit and deck_dir and os.path.exists(os.path.join(deck_dir, "deck.json")):      # which deck file the page was built from: changes made on it are told apart by this
        import edit as E
        html = open(out, encoding="utf-8").read()
        info = "<script>window.VS_EDIT=" + json.dumps({"deck": os.path.basename(os.path.normpath(deck_dir)), "base": E.base_of(deck_dir),
                                                       "report": E.report(deck_dir, deck), "masters": E.templates(deck, masters, env), "fields": E.field_variants(deck, masters, env)}, ensure_ascii=False).replace("</", "<\\/") + "</script>"
        open(out, "w", encoding="utf-8").write(html.replace("</head>", info + "\n</head>", 1) if "</head>" in html else info + html)
    return env

def brand_langs(b):
    """The languages a brand presents in: "langs" in brand.json (a list or "de,en"), else its one "lang"."""
    v = b.get("langs")
    if isinstance(v, str): v = [x.strip() for x in v.split(",")]
    v = [x for x in (v or []) if x]
    return v or [b.get("lang") or "en"]

def cmd_preview(args):
    import build as B, render
    name = positional(args)[0] if positional(args) else die("which brand?")
    b = B.load_brand(name); d = b["_dir"]
    langs = brand_langs(b) if b.get("langs") else ["en"]     # the languages the brand presents in; samples written per language switch with L
    import intro
    masters = render.load_masters(d)
    deck = render.sample_deck(masters, langs)
    for s in deck["slides"]:                                # one line for the user about each master, shown above the button bar
        a = intro.about(s["master"], masters[s["master"]]["meta"])
        if a: s["about"] = render.fit_langs(a, langs)
    if "--no-intro" not in args:                            # the preview introduces itself, on the brand's own masters
        deck["slides"] = [render.fit_langs(s, langs) for s in intro.slides(b.get("name"), len(deck["slides"]), masters)] + deck["slides"]
    deck["title"] = f"{b.get('name', name)} master slides"
    out = os.path.join(d, "preview.html")
    env = _render_and_build(deck, b, out, standins=_standins(b, os.path.join(d, "raw", "standins")))
    problems, sheets, legible = [], [], {}
    for lang in langs:
        legible[lang] = []
        pr, sh = B.inspect(out, os.path.join(d, "preview"), lang=lang, legible=legible[lang])
        problems += [dict(x, lang=lang) if len(langs) > 1 else x for x in pr]; sheets += sh
    print(f"\nmaster slides: {len(deck['slides'])} | {out}")
    for i, s in enumerate(deck["slides"], 1): print(f"  {i:2d} {s['master']}" + ("  (introduction)" if s.get("intro") else ""))
    print("overflow:", problems or "clean")
    if not all([_legible_report(legible[lang], lang if len(langs) > 1 else None) for lang in langs]):
        print("  Fix these in the brand's masters and theme.css: larger type, a colour that stands out from its ground, more room. A text over a photo needs the photo darkened or a ground of its own.")
    _voice_report(deck, b, langs, sample=True)
    for w in env["warnings"]: print("WARNING:", w)
    print("contact sheets to look at:"); [print("  " + s) for s in sheets]

def _voice_report(deck, b, langs, mode="live", sample=False):
    """Check the texts of a deck against the brand's voice rules and print one block per language."""
    import render, voice
    v = b.get("voice")
    if not isinstance(v, dict):
        print(f"voice: this brand has no voice rules yet (vs.py voice {os.path.basename(b['_dir'])})"); return True
    clean = True
    for lang in langs:
        found = voice.check_deck(deck, v, lang, render._resolve_lang, mode)
        print((f"[{lang}] " if len(langs) > 1 or not sample else "") + voice.report(found, voice.rules_for(v, lang), sample)); clean = clean and not found
    return clean

def cmd_voice(args):
    """vs.py voice <brand> [files...] [--again] | vs.py voice <brand> --check "text" [--lang de]"""
    import build as B, voice
    pos = positional(args, ("--check", "--lang"))
    name = pos[0] if pos else die("which brand? vs.py voice <brand> [sample texts...]")
    b = B.load_brand(name); d = b["_dir"]; langs = brand_langs(b)
    text = arg(args, "--check")
    if text is not None:
        lang = arg(args, "--lang") or voice.language(text, langs if b.get("langs") else None) or langs[0]
        rules = voice.rules_for(b.get("voice"), lang)
        print(f"[{lang}] " + voice.report([(0, "text", "text", f) for f in voice.check_text(text, rules, lang)], rules).replace("slide 0 (text), text: ", "")); return
    if pos[1:]:
        added, refused = voice.add_samples(d, pos[1:])
        for f in added: print("sample text added: voice/samples/" + f)
        for f in refused: print(f"not a text file (.txt, .md): {f}. Read PDF, Word and PowerPoint files with: vs.py ingest {name} <file>")
    m, rules, wrote = voice.draft(d, b.get("name", name), langs if b.get("langs") else None, force="--again" in args)
    print(f"VOICE of {b.get('name', name)}\n" + voice.summary(m))
    print("\nnumbers: " + os.path.join(d, "raw", "voice.json"))
    print("profile: " + os.path.join(d, "voice.md") + (" (drafted now: fill every TODO from the texts)" if wrote else " (kept as it is)"))
    cur = B.load_brand(name).get("voice") or {}
    print("rules in brand.json" + (" (drafted now from the measurement, confirm them with the user)" if rules else "") + ":\n" + json.dumps(cur, indent=2, ensure_ascii=False))
    if not rules and not wrote: print("Measured again. --again redrafts the rules from the measurement; voice.md is never overwritten.")
    print(f"change a rule: vs.py set {name} voice.sentence_max=22 'voice.avoid=[\"leverage => use\"]' voice.de.address=Sie")

def _scaffold(name, url=""):
    """Give a freshly analysed brand its own masters, theme and style guide draft."""
    import build as B, render
    d = B.brand_dir(name); data = json.load(open(os.path.join(d, "brand.json"), encoding="utf-8"))
    md = os.path.join(d, "masters"); os.makedirs(md, exist_ok=True)
    copied = 0
    for n, m in render.load_masters(None).items():
        if m["body"] is not None and not m["meta"].get("preview_only") and not m["meta"].get("hidden") and not os.path.exists(os.path.join(md, n + ".html")):
            shutil.copy(m["path"], os.path.join(md, n + ".html")); copied += 1
    if not os.path.exists(os.path.join(d, "theme.css")):
        open(os.path.join(d, "theme.css"), "w", encoding="utf-8").write(THEME_SKELETON.format(name=data.get("name", name)))
    for sub in ("elements/icons", "elements/arrows", "elements/shapes", "fonts/inbox"):
        os.makedirs(os.path.join(d, sub), exist_ok=True)
    sg = os.path.join(d, "styleguide.md")
    if not os.path.exists(sg):
        c, f, s = data.get("colors", {}), data.get("fonts", {}), data.get("shape", {})
        notes = []
        try: notes = json.load(open(os.path.join(d, "raw", "extract.json"), encoding="utf-8")).get("notes", [])
        except Exception: pass
        el = data.get("elements") or {}
        fams = f.get("families") or []
        type_lines = "\n".join(f"- {x.get('family')}: {', '.join(x.get('roles', []))}, {x.get('status')} ({x.get('note', '')})" for x in fams) or \
            f"- Body: {f.get('body', {}).get('family')} · Headings: {(f.get('head') or {}).get('family') or 'same as body'}"
        open(sg, "w", encoding="utf-8").write(STYLEGUIDE_SKELETON.format(
            name=data.get("name", name), url=data.get("url", url), date=time.strftime("%Y-%m-%d"), version=version(),
            colours="\n".join(f"- {k}: {v}" for k, v in c.items()), type=type_lines + f"\n- Weights: display {f.get('display_weight')}, headings {f.get('head_weight')}",
            radius=s.get("radius", 0), motif=s.get("motif", "wedge"), lang=data.get("lang", "en"),
            elements=f"Saved: {len(el.get('icons', []))} icons, {len(el.get('arrows', []))} arrows, {len(el.get('shapes', []))} shapes in elements/ (contact sheet raw/elements.png). "
                     f"Arrow glyph on the site: {el.get('arrow_glyph')}. Icon style guess: {el.get('icon_style')}.",
            open="\n".join("- " + n for n in notes) or "- none"))
    data["framework"] = version(); data.setdefault("confirmed", False)
    json.dump(data, open(os.path.join(d, "brand.json"), "w", encoding="utf-8"), indent=2, ensure_ascii=False)
    import voice
    voice.draft(d, data.get("name", name), brand_langs(data) if data.get("langs") else None)      # voice.md and the rules, from the texts read so far
    return d, copied

def cmd_analyze(args):
    import build as B
    pos = positional(args, ("--brand", "--pages"))
    url = pos[0] if pos else die("which website?")
    name = arg(args, "--brand") or die("give the brand a folder name: --brand <name>")
    name = re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")
    out = os.path.join(B.library(), name)
    if os.path.exists(os.path.join(out, "brand.json")) and "--again" not in args:
        die(f"brand '{name}' exists. Use --again to read the website again (brand.json is redrafted; styleguide.md, theme.css and masters stay).")
    import analyze
    analyze.extract(url, name=name, pages=int(arg(args, "--pages", 4)), fonts="--no-fonts" not in args, out=out)
    d, copied = _scaffold(name, url)
    if "--no-videos" not in args:
        try: analyze.fetch_videos(url, d)
        except Exception as e: print("videos could not be read:", str(e)[:120])
    print(f"\nlibrary: {d}\n{copied} default masters copied as starting points, theme.css and styleguide.md drafted.")
    cmd_fonts([name])
    cmd_preview([name])
    print("\nNEXT (vs-build): look at raw/screens/home.png, raw/logo_candidates.png, raw/elements.png, raw/screens/components/ and the contact sheets above;"
          "\ncorrect brand.json, choose the motion set (`motion <brand> --strip all`), write styleguide.md, voice.md (`voice <brand>`), theme.css and the brand's masters,"
          "\nrebuild with `preview`, then show the user preview.html.")

def cmd_videos(args):
    """vs.py videos <brand> [url]: save the website's own video files into the library (videos/, brand.json "videos")."""
    import build as B, analyze
    pos = positional(args)
    name = pos[0] if pos else die("which brand? vs.py videos <brand> [url]")
    b = B.load_brand(name)
    url = pos[1] if len(pos) > 1 else (b.get("url") or die("the brand has no website on record: vs.py videos <brand> <url>"))
    vids = analyze.fetch_videos(url, b["_dir"])
    for v in vids:
        print(f"  brand:{v['file']}" + (f"  {v.get('width')}x{v.get('height')}" if v.get("width") else "") + (f"  {v.get('seconds')} s" if v.get("seconds") else "")
              + ("  background loop: use it in the slot video of chapter, cover_photo, fullbleed and statement slides" if v.get("background") else ""))
    if vids: print("These files belong to the website's owner: use them for this brand only.")

def cmd_ingest(args):
    import build as B, ingest
    pos = positional(args)
    if len(pos) < 2: die("usage: vs.py ingest <brand> <files or folders...>")
    name = re.sub(r"[^a-z0-9]+", "-", pos[0].lower()).strip("-")
    d = os.path.join(B.library(), name); os.makedirs(d, exist_ok=True)
    print(ingest.report(ingest.ingest(d, pos[1:])))
    print("\nNEXT (vs-build): open", os.path.join(d, "sources", "SOURCES.md"), "first; see references/documents.md for how to weigh documents against the website.")

def cmd_elements(args):
    """vs.py elements <brand>: the icons, arrows and shapes in the brand's library, with the names a deck can use."""
    import build as B, render
    pos = positional(args)
    b = B.load_brand(pos[0] if pos else die("which brand? vs.py elements <brand>")); d = b["_dir"]; total = 0
    for kind, use in (("icons", 'in a deck: "icon": "<name>" on the items of cards, columns and steps; in a master: {{>icon <name>}}'),
                      ("arrows", "in a master: {{>el arrows/<file>}}; in theme.css: url(el:arrows/<file>)"), ("shapes", "in a master: {{>el shapes/<file>}}; in theme.css: url(el:shapes/<file>)")):
        names = render.element_names(d, kind); files = sorted(set(names.values())); total += len(files)
        print(f"{kind} ({len(files)})" + (f"   {use}" if files else ""))
        for f in files:
            short = sorted((n for n, x in names.items() if x == f), key=len)[0]
            print(f"  {short:28s} elements/{kind}/{f}")
    el = b.get("elements") or {}
    if el.get("icon_style"): print(f"\nicon style on the website: {el.get('icon_style')}" + (f", stroke {el.get('icon_stroke_width')}" if el.get("icon_stroke_width") else "") + f" | arrow glyph: {el.get('arrow_glyph')}")
    sheet = os.path.join(d, "raw", "elements.png")
    if os.path.exists(sheet): print("contact sheet as the website analysis saved it:", sheet)
    if not total: print("\nThe library holds no icons, arrows or shapes: the website shows none as SVG. Icons the user supplies go into elements/icons/ as .svg files (one colour: fill or stroke \"currentColor\").")
    else: print("\nRename a file to give it a name that says what it shows (icon_03.svg -> icon_03_energy.svg): the name after the number is what a deck writes.")

def cmd_masters(args):
    import build as B, render
    pos = positional(args)
    print(render.catalog(B.brand_dir(pos[0]) if pos else None, full="--full" in args))

def cmd_fonts(args):
    import build as B
    pos = positional(args, ("--family", "--weight", "--style", "--role"))
    sub = pos[0] if pos and pos[0] in ("accept", "add", "google") else None
    name = (pos[1] if sub else pos[0]) if len(pos) > (1 if sub else 0) else die("which brand?")
    d = B.brand_dir(name); p = os.path.join(d, "brand.json"); data = json.load(open(p, encoding="utf-8"))
    f = data.setdefault("fonts", {}); files = f.setdefault("files", []); fams = f.setdefault("families", [])
    def fam(family):
        for x in fams:
            if x.get("family", "").lower() == family.lower(): return x
        x = {"family": family, "roles": [], "source": "user", "licence": "ask", "status": "missing", "files": 0, "weights": [], "note": ""}
        fams.append(x); return x
    def save(): json.dump(data, open(p, "w", encoding="utf-8"), indent=2, ensure_ascii=False)
    if sub == "accept":
        want = pos[2].lower() if len(pos) > 2 else None
        keep, moved = [], 0
        for rec in f.get("pending") or []:
            if want and rec["family"].lower() != want:
                keep.append(rec); continue
            src = os.path.join(d, rec["file"]); dst_rel = "fonts/" + os.path.basename(rec["file"])
            if os.path.exists(src): shutil.move(src, os.path.join(d, dst_rel))
            files.append(dict(rec, file=dst_rel)); moved += 1
            x = fam(rec["family"]); x.update(status="embedded", licence="confirmed by user", note="licence confirmed by the user")
            x["files"] = len([y for y in files if y["family"] == rec["family"]])
        f["pending"] = keep
        save(); print(f"{moved} font file(s) activated.")
    elif sub == "add":
        paths = pos[2:] or sorted(os.path.join(d, "fonts", "inbox", x) for x in os.listdir(os.path.join(d, "fonts", "inbox")))
        if not paths: die("no font files given and fonts/inbox is empty")
        for src in paths:
            base = os.path.basename(src); low = base.lower()
            if not low.endswith((".woff2", ".woff", ".ttf", ".otf")): print("skipped (not a font file):", base); continue
            weight = arg(args, "--weight")
            if not weight:
                weight = next((w for k, w in (("thin", "100"), ("extralight", "200"), ("ultralight", "200"), ("light", "300"), ("regular", "400"), ("book", "400"), ("medium", "500"),
                                              ("semibold", "600"), ("demibold", "600"), ("extrabold", "800"), ("ultrabold", "800"), ("black", "900"), ("heavy", "900"), ("bold", "700"))
                               if k in low.replace("-", "").replace("_", "")), None) or (re.search(r"(?<!\d)([1-9]00)(?!\d)", low) or [None, "400"])[1]
                if "variable" in low or "[wght]" in low or "-vf" in low: weight = "100 900"
            style = arg(args, "--style") or ("italic" if "italic" in low or "oblique" in low else "normal")
            family = arg(args, "--family") or re.split(r"[-_ ]?(thin|extralight|ultralight|light|regular|book|medium|semibold|demibold|extrabold|ultrabold|black|heavy|bold|italic|variable|\d00|\[)", os.path.splitext(base)[0], flags=re.I)[0] or base
            dst_rel = "fonts/" + base
            if os.path.abspath(src) != os.path.abspath(os.path.join(d, dst_rel)): shutil.copy(src, os.path.join(d, dst_rel))
            if os.path.dirname(os.path.abspath(src)) == os.path.join(d, "fonts", "inbox"): os.remove(src)
            files[:] = [x for x in files if x["file"] != dst_rel] + [{"family": family, "weight": weight, "style": style, "file": dst_rel}]
            x = fam(family); x.update(status="embedded", source="user", licence="supplied by user", note="files supplied by the user")
            x["weights"] = sorted(set(x.get("weights", [])) | {int(w) for w in weight.split()}); x["files"] = len([y for y in files if y["family"] == family])
            print(f"added {base}: family '{family}', weight {weight}, {style}")
        save(); print("If the family name differs from what brand.json uses for body or headings, set it: vs.py set", name, 'fonts.head.family="..."')
    elif sub == "google":
        family = pos[2] if len(pos) > 2 else die('which family? e.g. fonts google acme "Inter" --role body')
        role = arg(args, "--role", "body")
        import urllib.request, urllib.parse
        q = urllib.parse.quote_plus(family)
        css = None
        for spec in (f"{q}:ital,wght@0,100..900;1,100..900", f"{q}:wght@100..900", f"{q}:wght@300;400;500;600;700;800;900", f"{q}:wght@400;700", q):
            try:
                req = urllib.request.Request(f"https://fonts.googleapis.com/css2?family={spec}&display=block", headers={"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 Chrome/126.0 Safari/537.36"})
                css = urllib.request.urlopen(req, timeout=15).read().decode(); break
            except Exception:
                continue
        if not css: die(f"'{family}' was not found on Google Fonts (or no network).")
        blocks = re.findall(r"/\*\s*([\w-]+)\s*\*/\s*@font-face\s*\{([^}]*)\}", css)
        keep = [(s, blk) for s, blk in blocks if s in ("latin", "latin-ext")] or blocks
        files[:] = [x for x in files if x["family"] != family]
        n = 0
        for subset, blk in keep:
            u = re.search(r"url\(([^)]+)\)", blk).group(1); w = re.search(r"font-weight:\s*([^;]+)", blk).group(1).strip(); st = re.search(r"font-style:\s*([^;]+)", blk).group(1).strip()
            rel = f"fonts/{re.sub(r'[^a-z0-9]+', '-', family.lower())}-{w.replace(' ', '-')}-{st}-{subset}.woff2"
            open(os.path.join(d, rel), "wb").write(urllib.request.urlopen(u, timeout=30).read())
            rng = re.search(r"unicode-range:\s*([^;]+)", blk)
            files.append({"family": family, "weight": w, "style": st, "file": rel, **({"unicode_range": rng.group(1).strip()} if rng else {})}); n += 1
        old = (f.get(role) or {}).get("family")
        f.setdefault(role, {})["family"] = family
        x = fam(family); x.update(source="google", licence="open", status="embedded", files=n, note=f"open typeface from Google Fonts" + (f", stands in for {old}" if old and old != family else ""))
        if role not in x["roles"]: x["roles"].append(role)
        if old and old != family: fam(old).update(note=f"replaced by {family} until its files are supplied")
        save(); print(f"{family}: {n} file(s) from Google Fonts, now the {role} typeface" + (f" (substitute for {old})" if old and old != family else ""))
    b = B.load_brand(name)
    print(f"\nFONTS of {b.get('name', name)}")
    print(f"  body: {b['fonts']['body'].get('family')} · headings: {(b['fonts'].get('head') or {}).get('family') or 'same as body'}")
    for x in b["fonts"].get("families") or []:
        print(f"  {x.get('family')}: {x.get('status')}, source {x.get('source')}, licence {x.get('licence')}, {x.get('files', 0)} file(s). {x.get('note', '')}")
    ask = [x for x in b["fonts"].get("families") or [] if x.get("status") in ("pending", "missing")]
    if ask:
        print("  ASK THE USER about: " + ", ".join(x["family"] for x in ask) + ". Pending files are activated with `fonts accept`, own files go into "
              + os.path.join(b["_dir"], "fonts", "inbox") + " and are taken over with `fonts add`.")


# ---------------------------------------------------------------- build

def _deck_dir(name):
    if os.path.isdir(name) and os.path.exists(os.path.join(name, "deck.json")): return os.path.abspath(name)
    if os.path.isfile(name): return os.path.dirname(os.path.abspath(name))
    d = os.path.join(home(), "decks", name)
    if os.path.exists(os.path.join(d, "deck.json")): return d
    die(f"deck '{name}' not found in {os.path.join(home(), 'decks')}")

DECK_PARTS = {"sources": "what the user supplied for this deck: documents, earlier slides, figures, briefs, e-mails",
              "research": "what was found out for it, with where it comes from, and the agreed line of argument (outline.md)",
              "images": "pictures of this deck, named in slots as images/<file>"}

def _deck_parts(d):
    """Every deck folder has the same parts, so that a later deck can be made from what an earlier one rests on."""
    for part in DECK_PARTS: os.makedirs(os.path.join(d, part), exist_ok=True)

def _lang_gaps(slide, langs):
    """Texts of a slide that are written per language and lack one of the deck's languages: [(path, languages it has)]."""
    out = []
    def walk(v, path):
        if isinstance(v, dict):
            if v and set(v) <= set(langs) | {"*"} | {k for k in v if re.fullmatch(r"[a-z]{2,3}(-[A-Za-z]{2,4})?", str(k))} and all(not isinstance(x, (dict, list)) for x in v.values()) \
                    and any(k in langs for k in v) and "*" not in v:
                miss = [l for l in langs if l not in v]
                if miss and any(isinstance(x, str) and re.search(r"[^\W\d_]{2}", re.sub(r"<[^>]+>", "", x)) for x in v.values()): out.append((".".join(path), [l for l in langs if l in v]))
                return
            for k, x in v.items():
                if k not in ("edited", "config", "brief"): walk(x, path + [str(k)])
        elif isinstance(v, list):
            for i, x in enumerate(v, 1): walk(x, path + [str(i)])
    walk(slide, [])
    return out

def cmd_langs(args):
    """vs.py langs <deck> [--add fr] | vs.py langs --brand <name> [--add fr]: the languages of a deck or a brand; add one later.
    Nothing is rebuilt from scratch: masters, theme and decks stay, texts that lack the new language are listed for translation."""
    import build as B, brandtools
    lang = (arg(args, "--add") or "").strip().lower(); pos = positional(args, ("--add", "--brand"))
    if lang and not re.fullmatch(r"[a-z]{2,3}(-[a-z]{2,4})?", lang): die("a language is given by its code: de, en, fr, es, it, nl, pt ...")
    if arg(args, "--brand"):
        name = arg(args, "--brand"); data = brandtools._read(name); langs = brand_langs(data)
        if lang and lang not in langs:
            langs.append(lang); data["langs"] = langs; brandtools._write(name, data)
            print(f"brand {name}: languages are now {', '.join(langs)}.")
            print(f"The master slides are not rebuilt: their sample texts fall back to the nearest language until you add \"{lang}\" to the samples you care about (the JSON head of a master), then `vs.py preview {name}`.")
            print(f"Voice: measure or write the rules for {lang} (`vs.py voice {name} <texts in {lang}>`, and the section for {lang} in voice.md). New decks of this brand start with {', '.join(langs)}.")
            print(f"Existing decks keep their languages; add it where it is wanted: vs.py langs <deck> --add {lang}")
        else:
            print(f"brand {name}: {', '.join(langs)}")
        return
    d = _deck_dir(pos[0] if pos else die("which deck? vs.py langs <deck> [--add fr]   or   vs.py langs --brand <name> [--add fr]"))
    import edit
    deck = edit.load(d); langs = deck.get("langs") or [deck.get("lang") or "en"]
    if lang and lang not in langs:
        langs.append(lang); deck["langs"] = langs; edit.save(d, deck)
        print(f"deck {os.path.basename(d)}: languages are now {', '.join(langs)}. Write every text below in {lang}, as {{\"{langs[0]}\": ..., \"{lang}\": ...}}, in the brand's voice for {lang}; then build.")
        import voice
        n = 0
        for i, s in enumerate(deck.get("slides") or [], 1):
            gaps = dict(_lang_gaps(s, langs))
            for path, text in voice.slots(s):
                parts = path.split(".")
                if parts[-1] in langs or parts[-1] == "*":      # one language's text of a text written per language
                    if parts[-1] != langs[0]: continue
                    path = ".".join(parts[:-1])
                    if path not in gaps: continue
                elif not re.search(r"[^\W\d_]{2}\s+\S*[^\W\d_]{2}", re.sub(r"<[^>]+>", "", text)): continue      # a single word or a figure stands for every language
                print(f"TRANSLATE slide {i}, {path}: {json.dumps(text, ensure_ascii=False)[:160]}"); n += 1
        print(f"{n} text(s). A text that is right in every language (a name, a figure) stays as it is.")
    else:
        print(f"deck {os.path.basename(d)}: {', '.join(langs)}")

def cmd_new(args):
    import build as B
    pos = positional(args, ("--brand", "--langs", "--title", "--from", "--author"))
    name = re.sub(r"[^a-z0-9]+", "-", (pos[0] if pos else die("name the deck")).lower()).strip("-")
    origin = None
    if arg(args, "--from"):                                 # a deck made from an earlier one: its sources, its research, its brand
        od = _deck_dir(arg(args, "--from")); origin = json.load(open(os.path.join(od, "deck.json"), encoding="utf-8"))
    brand = arg(args, "--brand") or (origin or {}).get("brand") or (os.path.basename(B.list_brands()[0]) if len(B.list_brands()) == 1 else die("which brand? --brand <name>"))
    B.brand_dir(brand)
    d = os.path.join(home(), "decks", name)
    if os.path.exists(os.path.join(d, "deck.json")): die(f"deck '{name}' exists: {d}")
    _deck_parts(d)
    if origin:
        for part in ("sources", "research"):
            if os.path.isdir(os.path.join(od, part)): shutil.copytree(os.path.join(od, part), os.path.join(d, part), dirs_exist_ok=True)
    langs = arg(args, "--langs").split(",") if arg(args, "--langs") else brand_langs(json.load(open(os.path.join(B.brand_dir(brand), "brand.json"), encoding="utf-8")))
    if not arg(args, "--langs") and "en" not in langs: langs = langs + ["en"]      # a deck always has an English version, unless the languages are named
    bj = json.load(open(os.path.join(B.brand_dir(brand), "brand.json"), encoding="utf-8"))
    deck = {"title": arg(args, "--title") or name.replace("-", " ").capitalize(), "brand": brand, "langs": langs, "motion": True,
            "author": arg(args, "--author") or (origin or {}).get("author") or bj.get("author") or "",
            "brief": {"occasion": "", "presenter": "", "audience": "", "length": "", "look": "", "handout": ""},
            "slides": [{"master": "cover", "title": "Title with one <em>accent</em> word", "lead": "One sentence.", "notes": ""}]}
    if origin:
        deck["from"] = os.path.basename(od); deck["langs"] = langs if arg(args, "--langs") else (origin.get("langs") or langs)
    json.dump(deck, open(os.path.join(d, "deck.json"), "w", encoding="utf-8"), indent=2, ensure_ascii=False)
    print("deck:", os.path.join(d, "deck.json"))
    for part, what in DECK_PARTS.items(): print(f"  {part + '/':10s} {what}")
    print("brand photos are named as brand:images/<file>.")
    if origin:
        print(f"made from the deck '{os.path.basename(od)}': its sources and research are copied; its slides are in {os.path.join(od, 'deck.json')} to take over what fits"
              f" (\"{origin.get('title', '')}\", {len(origin.get('slides') or [])} slides, brief: {json.dumps(origin.get('brief') or {}, ensure_ascii=False)})")

MODES = ("live", "reading")
DENSITY = {"live": 50, "reading": 250}      # words a page may show before the report flags it; a deck sets its own in "density"

def _density(stats, mode, limit):
    """One report line: the words visible per page (reading: slide plus reader text), pages above the limit named."""
    if not stats: return "density: nothing to count"
    total = lambda s: s["words"] + s["read"]
    where = lambda s: f"page {s['slide']}" + (f" (slide {s['n']} of deck.json)" if s["n"] and s["n"] != s["slide"] else "")
    over = [f"{where(s)}: {total(s)} words" + (f" ({s['words']} on the slide, {s['read']} reader text)" if s["read"] else "") + (f" \"{s['title']}\"" if s["title"] else "")
            for s in stats if total(s) > limit]
    line = f"density ({mode}, flag above {limit} words): " + " ".join(f"{s['slide']}:{total(s)}" + ("!" if total(s) > limit else "") for s in stats)
    return line + ("".join("\n    WORDY " + o for o in over) if over else " | none above the limit")

def cmd_titles(args):
    """The slide titles in a row, per language: the argument of the deck without its slides."""
    import render
    pos = positional(args)
    d = _deck_dir(pos[0] if pos else die("which deck?"))
    try: deck = json.load(open(os.path.join(d, "deck.json"), encoding="utf-8"))
    except ValueError as e: die(f"deck.json is not valid JSON: {e}")
    try:
        import build as B, shared
        deck, _ = shared.resolve(deck, B.brand_dir(deck.get("brand")))
    except Exception:
        pass
    for lang, rows in render.titles(deck).items():
        print(f"[{lang}]")
        w = max([len(m) + (len(o) + 8 if o else 0) for _, m, o, _ in rows] or [0])
        for n, master, only, title in rows:
            print(f"{n:3d}  {(master + (f' ({only} only)' if only else '')).ljust(w)}  {title or '(no title)'}")

def cmd_build(args):
    import build as B
    if "--no-update" not in args: ensure_current()
    pos = positional(args, ("--only", "--mode"))
    d = _deck_dir(pos[0] if pos else die("which deck?"))
    try: deck = json.load(open(os.path.join(d, "deck.json"), encoding="utf-8"))
    except ValueError as e: die(f"deck.json is not valid JSON: {e}")
    b = B.load_brand(deck.get("brand") or die("deck.json names no brand"))
    if not b.get("confirmed"): print("NOTE: this brand has not been confirmed by the user yet (vs-build).")
    _deck_parts(d)
    import shared
    deck, sh = shared.resolve(deck, b["_dir"])
    if sh["slides"] or sh["facts"]: print("shared with the brand's other decks: " + ", ".join(filter(None, ["slides " + ", ".join(sh["slides"]) if sh["slides"] else "", "facts " + ", ".join(sh["facts"]) if sh["facts"] else ""])))
    for line in sh["problems"]: print("SHARED:", line)
    handout = "--handout" in args
    deck["handout"] = handout
    main = deck.get("mode") or "live"; mode = arg(args, "--mode") or main      # the main mode of the deck, or the other version on request
    if main not in MODES or mode not in MODES: die(f"the mode is one of: {', '.join(MODES)} (deck.json says \"{main}\", asked for \"{mode}\")")
    other = "" if mode == main else mode
    title = deck.get("title") or os.path.basename(d)
    fn = re.sub(r"[^\w-]+", "_", title).strip("_") + ("_" + other if other else "") + ("_handout" if handout else "")
    out = os.path.join(d, fn + ".html")
    t0 = time.time()
    env = _render_and_build(deck, b, out, deck_dir=d, title=title + (" " + other if other else ""), pdf="--pdf" in args, mode=mode)
    langs = deck.get("langs") or ["en"]
    only = [int(x) for x in arg(args, "--only", "").split(",") if x.strip().isdigit()] or None
    limit = (deck.get("density") or {}).get(mode, DENSITY[mode])
    clean = readable = True
    for lang in langs:
        stats, found = [], []
        problems, sheets = B.inspect(out, None if "--no-shots" in args else os.path.join(d, "shots" + ("_" + other if other else "")), lang=lang, slides=only, stats=stats, legible=found)
        print(f"[{lang}] overflow:", problems or "clean"); clean = clean and not problems
        readable = _legible_report(found, lang) and readable
        print(f"[{lang}] " + _density(stats, mode, limit))
        if isinstance(b.get("voice"), dict):
            import render, voice
            print(f"[{lang}] " + voice.report(voice.check_deck(deck, b["voice"], lang, render._resolve_lang, mode), voice.rules_for(b["voice"], lang)))
        for s in sheets: print("  sheet:", s)
    if mode == "reading":
        origin = env.get("read_origin") or {}; nums = lambda k: ", ".join(str(n) for n in sorted(origin.get(k, ())))
        if origin.get("notes"): print(f"reader text missing, the speaker notes are shown as they are (rewrite them as prose in \"read\"): slides {nums('notes')} of deck.json")
        if origin.get("none"): print(f"no reader text and no notes, shown full size: slides {nums('none')} of deck.json")
    for i, s in enumerate(deck.get("slides") or [], 1):      # a language added later: texts that do not have it yet
        for path, has in _lang_gaps(s, langs):
            print(f"TRANSLATE slide {i}, {path}: has {', '.join(has)}, not {', '.join(l for l in langs if l not in has)}; write it in the brand's voice for that language")
    if not deck.get("author") and deck.get("credit") is not False:
        print("AUTHOR: deck.json names no \"author\": the last slide credits the person who made the deck. Ask the user for their name once, set it in the deck and as the brand's default (vs.py set <brand> author=\"Name\").")
    try:                                                    # free slides in a form the brand has used before: time for a master
        import forms, render
        raw = json.load(open(os.path.join(d, "deck.json"), encoding="utf-8"))
        for line in forms.note(b["_dir"], os.path.basename(d), raw, set(render.load_masters(None))): print(line.replace("<brand>", os.path.basename(b["_dir"])))
    except Exception: pass
    rp = os.path.join(d, "research", "report.md")
    if not os.path.exists(rp) or os.path.getsize(rp) < 200:
        print("RESEARCH: research/report.md is missing or empty. Write it from this conversation, in the user's language: what the deck is for, the audience, the line of argument, facts with their sources, decisions and open points, so that another deck on the topic can be made from it.")
    if "en" not in langs and deck.get("english") is not False and not deck.get("sample"):
        print("ENGLISH: this deck has no English version. Add it now, without asking: put \"en\" into \"langs\" and write every text in both languages"
              " ({\"" + langs[0] + "\": ..., \"en\": ...}), in the brand's voice for English. Only if the user said they want none, set \"english\": false in deck.json.")
    if not isinstance(b.get("voice"), dict): print(f"voice: this brand has no voice rules yet (vs.py voice {os.path.basename(b['_dir'])})")
    import edit
    for line in edit.todo(deck): print(line)                # texts the user changed while editing
    for i, s in enumerate(edit.load(d).get("slides") or [], 1):      # shared slides the user changed for every presentation
        if isinstance(s, dict) and s.get("for_all") and s.get("shared"):
            print(f"SHARED: the user changed slide {i} (the shared slide '{s['shared']}') for all presentations. When its texts are corrected (no REVIEW line left for it): "
                  f"vs.py shared {os.path.basename(b['_dir'])} push --from {os.path.basename(d)} --slide {i}")
    for w in env["warnings"]: print("WARNING:", w)
    import media
    media.prune(d)
    if env.get("media"):
        what, online = media.summary(env["media"])
        print(f"this deck is a folder: {d} holds the HTML and what it links ({what}); present with `vs.py present {os.path.basename(d)}`, send with `vs.py pack {os.path.basename(d)}`"
              + (f"; needs to be online for {', '.join(online)}" if online else ""))
    print(f"\n{out}\n{len(deck.get('slides', []))} slides, {len(langs)} language(s), {time.time() - t0:.1f} s" + ("" if clean else " | FIX THE OVERFLOW: shorten text, never shrink type")
          + ("" if readable else " | FIX THE LEGIBILITY: every text must be readable; change the picture, the master or the theme, or shorten, never leave it")
          + (f" | NOT FINISHED: {len(edit.waiting(deck))} text(s) the user typed are not corrected or translated yet (the REVIEW lines); the deck is not handed over like this" if edit.waiting(deck) else ""))

def _deck_html(d, handout=False):
    """The built HTML files of a deck folder: the main version before the other mode's (<Title>_reading.html, <Title>_live.html), newest first."""
    other = lambda f: any(f.endswith(f"_{m}.html") or f.endswith(f"_{m}_handout.html") for m in MODES)
    return sorted((f for f in os.listdir(d) if f.endswith(".html") and not f.startswith("_") and not f.endswith(" (edit).html") and (handout or "_handout" not in f)), key=lambda f: (other(f), -os.path.getmtime(os.path.join(d, f))))

def _new_scenes():
    """Scenes that came with updates of the framework: {name: version it came with}."""
    try: return json.load(open(os.path.join(home(), ".cache", "new_scenes.json"), encoding="utf-8"))
    except (OSError, ValueError): return {}

def cmd_scenes(args):
    import build as B, media
    pos = positional(args, ("--choose", "--export"))
    if not media.load_scenes(B.brand_dir(pos[0]) if pos else None):
        print("Animated scenes are not part of this version of VibeUpSlides. Decks move through the brand's motion set (vs.py motion <brand>)."); return
    if pos and arg(args, "--export"):                       # a scene of the brand's own, packed to pass it on (to the catalogue's keeper, to another workspace)
        import zipfile
        bd = B.brand_dir(pos[0]); name = arg(args, "--export"); s = media.load_scenes(bd).get(name) or die(f"no scene '{name}'")
        dest = os.path.join(outbox(), f"vibeupslides-scene-{name}.zip"); n = 0
        with zipfile.ZipFile(dest, "w", zipfile.ZIP_DEFLATED) as z:
            for d, _, files in os.walk(s["dir"]):
                for f in files:
                    if f != ".DS_Store": z.write(os.path.join(d, f), os.path.join(name, os.path.relpath(os.path.join(d, f), s["dir"]))); n += 1
            z.writestr(os.path.join(name, "ORIGIN.txt"), f"scene {name}, made for the brand {pos[0]} with VibeUpSlides {version()}\n")
        print(f"{dest} ({n} files). A scene is a folder: unpacked into framework/scenes/ it joins the catalogue, into library/<brand>/scenes/ it belongs to one brand. "
              "Before it leaves the user's hands, check with them that it carries nothing of theirs that must stay with them (logos, photos, names).")
        return
    if pos and ("--gallery" in args or arg(args, "--choose") is not None):
        import brandtools
        bd = B.brand_dir(pos[0]); scenes = media.load_scenes(bd)
        if arg(args, "--choose") is not None:               # the scenes the user picked for this brand
            want = [x.strip() for x in arg(args, "--choose").split(",") if x.strip()]
            bad = [x for x in want if x not in scenes]
            if bad: die(f"no such scene: {', '.join(bad)}. Scenes: {', '.join(scenes)}")
            data = brandtools._read(pos[0]); data["scenes"] = want; data["scenes_seen"] = sorted(scenes); brandtools._write(pos[0], data)
            print(f"scenes of {pos[0]}: {', '.join(want) or 'none chosen'}. Decks of this brand use these first.")
            return
        print(_scene_gallery(pos[0], bd, scenes)); return
    print(media.scene_catalog(B.brand_dir(pos[0]) if pos else None, full="--full" in args))
    print('\nIn a deck: {"master": "scene", "scene": "<name>", "config": {...}}. The forward key runs through the steps first, then moves on.')

def _quick_build(d):
    """Build the deck's main HTML again without the checks: after a change made on the page that is being shown."""
    import build as B, contextlib, io
    deck = json.load(open(os.path.join(d, "deck.json"), encoding="utf-8")); b = B.load_brand(deck.get("brand"))
    title = deck.get("title") or os.path.basename(d)
    with contextlib.redirect_stdout(io.StringIO()):
        _render_and_build(deck, b, os.path.join(d, re.sub(r"[^\w-]+", "_", title).strip("_") + ".html"), deck_dir=d, title=title, mode=deck.get("mode") or "live")

def cmd_present(args):
    import edit, media, serve
    pos = positional(args, ("--port",))
    d = _deck_dir(pos[0] if pos else die("which deck?"))
    html = _deck_html(d)
    if not html: die("build the deck first: vs.py build " + os.path.basename(d))
    port = arg(args, "--port")
    if port is not None and not port.isdigit(): die("--port takes a number")
    online = media.referenced_files(d, html[:1])[1]
    notes = [f"Needs to be online for: {', '.join(online)}"] if online else []
    notes.append("Notes written in the presenter view (M) are saved into deck.json and stay on the slide.")
    api = edit.make_api(d, lambda: _quick_build(d), only=("state", "notes")) if os.path.exists(os.path.join(d, "deck.json")) else None
    try: serve.present(d, html[0], int(port) if port else None, "--no-open" not in args, notes, api=api, label="presenting")
    except OSError as e: die(str(e))
    try:
        for line in edit.todo(edit.load(d)): print(line)
    except (OSError, ValueError): pass

def cmd_edit(args):
    """vs.py edit <deck>: the deck in the browser with its texts open for typing. Changes go into deck.json."""
    import build as B, contextlib, edit, io, serve, voice
    ensure_current()                                         # a newer framework is taken over before the page opens, not after
    pos = positional(args, ("--port",))
    d = _deck_dir(pos[0] if pos else die("which deck?")); name = os.path.basename(d)
    port = arg(args, "--port")
    if port is not None and not port.isdigit(): die("--port takes a number")
    if "--file" in args:                                    # kept for sessions that learnt it: the deck's own file is the editing page
        for f in os.listdir(d):
            if f.endswith(" (edit).html"): os.remove(os.path.join(d, f))
        cmd_build([name, "--no-update"]); return
    out = os.path.join(d, edit.EDIT_HTML)
    def rebuild():
        deck = edit.load(d); b = B.load_brand(deck.get("brand") or die("deck.json names no brand"))
        with contextlib.redirect_stdout(io.StringIO()):      # the page is built after every change; the report comes at the end
            _render_and_build(dict(deck, mode="live"), b, out, deck_dir=d, title=(deck.get("title") or name) + " (edit)", mode="live", edit=True)
        return b
    try: b = rebuild()
    except ValueError as e: die(str(e))
    rules = lambda lang: voice.rules_for(B.load_brand(edit.load(d).get("brand")).get("voice"), lang)
    def library():
        import render
        return render.load_masters(B.load_brand(edit.load(d).get("brand"))["_dir"]), render.fit_langs
    how = "wait" if "--reopen" in args else "--no-open" not in args      # --reopen: the user's page from before reloads itself; open one only if none is there
    try: serve.present(d, edit.EDIT_HTML, int(port) if port else None, how, api=edit.make_api(d, rebuild, rules, finish=lambda: _quick_build(d), library=library))
    except OSError as e: die(str(e))
    finally:
        if os.path.exists(out): os.remove(out)
    n = edit.depth(d)[0]
    print(f"{n} version(s) of deck.json are kept in {os.path.join(d, '.history')}. Building the deck with what was changed:\n")
    cmd_build([name, "--no-update"])
    if edit.waiting(edit.load(d)):
        print(f"\nNEXT: the user's page says that their changes are being corrected and translated and that it opens again by itself. Do every REVIEW line above"
              f"\n(write the corrected text and the translations into deck.json, remove the \"edited\" entries), then start `vs.py edit {name} --reopen`: the waiting page reloads.")
    else:
        print("\nNothing waits for correction or translation: the editing is finished.")

def cmd_apply(args):
    """vs.py apply <deck> [file]: bring the changes of a deck edited as a file into deck.json, then build."""
    import edit, glob
    pos = positional(args)
    d = _deck_dir(pos[0] if pos else die("which deck?")); name = os.path.basename(d)
    src = pos[1] if len(pos) > 1 else None
    if not src:
        found = [f for p in (d, os.environ.get("VIBEUPSLIDES_UPLOADS"), "/mnt/user-data/uploads", outbox()) if p and os.path.isdir(p)
                 for f in glob.glob(os.path.join(p, "*.edits*.json"))]
        src = max(found, key=os.path.getmtime) if found else die(f"no file with changes found: vs.py apply {name} <{name}.edits.json>")
    try: data = json.load(open(src, encoding="utf-8"))
    except (OSError, ValueError) as e: die(f"{src} cannot be read: {e}")
    if not isinstance(data, dict) or not data.get("vibeupslides_edits"): die(f"{src} is not a file of changes saved by an editing page")
    if data.get("deck") and data["deck"] != name: die(f"these changes belong to the deck '{data['deck']}', not to '{name}'")
    import hashlib
    keep = os.path.join(d, ".history", "applied"); os.makedirs(keep, exist_ok=True)
    mark = hashlib.sha1(json.dumps(data.get("ops") or [], sort_keys=True).encode()).hexdigest()[:16] + "-" + str(data.get("base") or "")
    if os.path.exists(os.path.join(keep, mark + ".json")):
        print(f"These changes were applied before ({os.path.basename(src)} is the same file as last time): nothing to do. The deck is current."); return
    if not (data.get("ops") or []):
        print("The file holds no changes: nothing to do."); return
    def library():
        import build as B, render
        return render.load_masters(B.load_brand(edit.load(d).get("brand"))["_dir"]), render.fit_langs
    done, notes = edit.apply_edits(d, data, library)
    print(f"{done} of {len(data.get('ops') or [])} change(s) from {os.path.basename(src)} are in deck.json; the version before is kept in {os.path.join(d, '.history')}")
    for n in notes: print("NOTE:", n)
    try: shutil.copy(src, os.path.join(keep, mark + ".json"))
    except OSError: pass
    if os.path.dirname(os.path.abspath(src)) == os.path.abspath(d):
        try: os.remove(src)
        except OSError: pass
    print()
    cmd_build([name, "--no-update"])
    if edit.waiting(edit.load(d)):
        print(f"\nNEXT: do every REVIEW line above (write the corrected text and the translations into deck.json, remove the \"edited\" entries), build again"
              f"\n(`vs.py build {name}`) and give the user the new file in place of the one they edited.")
    else:
        print("\nNothing waits for correction or translation. Give the user the new file in place of the one they edited.")

def _decks():
    root = os.path.join(home(), "decks")
    for n in sorted(os.listdir(root)) if os.path.isdir(root) else []:
        p = os.path.join(root, n, "deck.json")
        if os.path.exists(p):
            try: yield n, os.path.join(root, n), json.load(open(p, encoding="utf-8"))
            except ValueError: pass

def cmd_shared(args):
    """vs.py shared <brand>                                   what the brand's decks share, and which deck uses what
       vs.py shared <brand> slide <name> --from <deck> --slide N    make slide N of a deck a shared slide; the deck names it from then on
       vs.py shared <brand> fact <key> <value> [--lang de]    set a fact (address, team.size); with --lang for one language
       vs.py shared <brand> push --from <deck> --slide N      take what a deck changed on a shared slide into the library, for every deck"""
    import build as B, shared
    pos = positional(args, ("--from", "--slide", "--lang"))
    name = pos[0] if pos else die("which brand? vs.py shared <brand>")
    bd = B.brand_dir(name)
    if len(pos) > 1 and pos[1] == "slide":
        sname = pos[2] if len(pos) > 2 else die("name the shared slide: vs.py shared <brand> slide <name> --from <deck> --slide N")
        d = _deck_dir(arg(args, "--from") or die("--from <deck>")); n = int(arg(args, "--slide") or die("--slide N"))
        deck = json.load(open(os.path.join(d, "deck.json"), encoding="utf-8")); slides = deck.get("slides") or []
        if not 1 <= n <= len(slides): die(f"the deck has {len(slides)} slides")
        if slides[n - 1].get("shared"): die(f"slide {n} already is the shared slide '{slides[n - 1]['shared']}'")
        try: path = shared.put_slide(bd, sname, slides[n - 1])
        except ValueError as e: die(str(e))
        import edit
        slides[n - 1] = {"shared": sname}; edit.save(d, deck)
        print(f"shared slide '{sname}': {path}\nslide {n} of {os.path.basename(d)} names it now. Other decks use it as {{\"shared\": \"{sname}\"}}; a field next to it replaces that field for the one deck.")
        return
    if len(pos) > 1 and pos[1] == "push":
        import edit
        d = _deck_dir(arg(args, "--from") or die("--from <deck>")); n = int(arg(args, "--slide") or die("--slide N"))
        deck = edit.load(d); slides = deck.get("slides") or []
        if not 1 <= n <= len(slides) or not slides[n - 1].get("shared"): die(f"slide {n} of {os.path.basename(d)} is not a shared slide")
        s = slides[n - 1]; sname = str(s["shared"])
        if s.get("edited"): die(f"slide {n} still has texts the user typed that are not corrected (REVIEW): correct and translate them first")
        lib = shared.slides(bd)
        if sname not in lib: die(f"the brand has no shared slide '{sname}'")
        new = dict(lib[sname]); new.update({k: v for k, v in s.items() if k not in ("shared", "for_all", "edited")})
        shared.put_slide(bd, sname, new); slides[n - 1] = {"shared": sname}; edit.save(d, deck)
        others = [dn for dn, _, dk in _decks() if dn != os.path.basename(d) and sname in shared.uses(dk)[0]]
        print(f"the shared slide '{sname}' is now as slide {n} of {os.path.basename(d)} shows it.")
        if others: print(f"ASK the user once: {len(others)} other presentation(s) use it ({', '.join(others)}). Update them now? If yes: vs.py refresh --brand {name}")
        else: print("No other presentation uses it: nothing else to do.")
        return
    if len(pos) > 1 and pos[1] == "fact":
        if len(pos) < 4: die("vs.py shared <brand> fact <key> <value> [--lang de]")
        key, value = pos[2], " ".join(pos[3:]); lang = arg(args, "--lang")
        if lang:
            old = shared.facts(bd); node = old
            for p in key.split("."): node = node.get(p) if isinstance(node, dict) else None
            cur = node if isinstance(node, dict) else ({} if node is None else {"*": node}); cur[lang] = value; value = cur
        shared.set_fact(bd, key, value)
        print(f"fact {key} = {json.dumps(value, ensure_ascii=False)}  (in a deck's text: {{{{fact.{key}}}}}). Bring the decks up to date: vs.py refresh --brand {name}")
        return
    lib, facts = shared.slides(bd), shared.facts(bd)
    use_s, use_f = {}, {}
    for n, d, deck in _decks():
        if deck.get("brand") != name: continue
        s, f = shared.uses(deck)
        for x in s: use_s.setdefault(x, []).append(n)
        for x in f: use_f.setdefault(x, []).append(n)
    print(f"shared by the decks of {name}: {shared.folder(bd)}")
    print("\nslides (in a deck: {\"shared\": \"<name>\"}):")
    for k, s in lib.items(): print(f"  {k:18s} master {s.get('master', '?'):16s} used by: {', '.join(use_s.get(k, [])) or 'no deck yet'}")
    if not lib: print("  none yet. Make one from a slide that exists: vs.py shared " + name + " slide team --from <deck> --slide 7")
    def flat(node, pre=""):
        for k, v in node.items():
            if isinstance(v, dict) and not (v and set(v) <= set(brand_langs(json.load(open(os.path.join(bd, "brand.json"), encoding="utf-8")))) | {"*"}): yield from flat(v, pre + k + ".")
            else: yield pre + k, v
    print("\nfacts (in a text: {{fact.<key>}}):")
    for k, v in flat(facts): print(f"  {k:18s} {json.dumps(v, ensure_ascii=False)[:70]:72s} used by: {', '.join(use_f.get(k, [])) or 'no deck yet'}")
    if not facts: print("  none yet. Set one: vs.py shared " + name + " fact address \"Example Street 1, 10115 Berlin\"")
    for k in sorted(set(use_s) - set(lib)): print(f"MISSING shared slide '{k}', named by: {', '.join(use_s[k])}")
    for line in shared.errors(bd): print("SHARED:", line)
    print(f"\nAfter a change: vs.py refresh --brand {name}")

DESIGN_PAGE = '''<!doctype html><html lang="__LANG__"><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1"><title>__HEAD__</title>
<style>
body{margin:0;padding:28px 32px 56px;background:#161616;color:#eee;font:15px/1.45 system-ui,sans-serif}
h1{font-size:22px;font-weight:600;margin:0 0 4px} p{margin:0;color:#aaa;max-width:900px}
.bar{display:flex;flex-wrap:wrap;gap:8px;margin:20px 0 24px}
button{font:inherit;color:#eee;background:#2a2a2a;border:1px solid #444;border-radius:6px;padding:7px 14px;cursor:pointer} button.on{background:#eee;color:#161616;border-color:#eee}
.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(440px,1fr));gap:26px}
.cell h2{font-size:18px;font-weight:600;margin:12px 0 2px} .cell h2 code{font-weight:400;color:#7ad;margin-left:8px;font-size:14px}
.cell p{font-size:13.5px} .cell p+p{margin-top:4px;color:#888}
.frame{position:relative;aspect-ratio:16/9;background:#000;border-radius:6px;overflow:hidden}
iframe{position:absolute;inset:0;width:100%;height:100%;border:0;pointer-events:none}
</style>
<h1>__HEAD__</h1><p>__TEXT__</p>
<div class="bar" id="bar"></div><div class="grid" id="grid"></div>
<script>
var styles=__STYLES__, slides=__SLIDES__, decks=__DECKS__, n=1;
function deck(name){ var s=atob(decks[name]), a=new Uint8Array(s.length); for(var i=0;i<s.length;i++) a[i]=s.charCodeAt(i); return URL.createObjectURL(new Blob([a],{type:"text/html"})); }
var bar=document.getElementById("bar"), grid=document.getElementById("grid");
function play(){ document.querySelectorAll("iframe").forEach(function(f){ f.contentWindow.postMessage({vs:"replay",slide:n},"*"); }); }
slides.forEach(function(s,i){ var b=document.createElement("button"); b.textContent=s; if(!i) b.className="on";
  b.onclick=function(){ n=i+1; bar.querySelectorAll("button").forEach(function(x){x.classList.remove("on");}); b.classList.add("on"); play(); }; bar.appendChild(b); });
styles.forEach(function(s){ var c=document.createElement("div"); c.className="cell";
  c.innerHTML='<div class="frame"><iframe></iframe></div><h2>'+s.title+'<code>'+s.name+'</code></h2><p>'+s.character+'</p><p>'+s.fits+'</p>'; grid.appendChild(c); c.querySelector("iframe").src=deck(s.name); });
</script></html>
'''

def cmd_design(args):
    """vs.py design --examine <files or addresses>                      examples the user likes: their colours measured, their pictures to look at
       vs.py design <brand> --style <nearest> --ground "#…" --ink "#…" --accent "#…" --head "Typeface" --body "Typeface" --radius N [--motif …] [--motion <set>]
                                                                    a look of the user's own, developed from the examples
       vs.py design [--lang de]                                         the styles a look can start from when there are no examples
       vs.py design --gallery [--pick a,b,c] [--name "Name"] [--topic "Title"] [--lang de]
                                                                    one page that shows the styles side by side on the same six slides
       vs.py design <brand> --style <name> [--name "Name"] [--accent "#hex"] [--langs de,en] [--author "First Last"]
                                                                    a library of the user's own from that style, with its master slides and preview"""
    import base64, build as B, design, tempfile
    import html as html_mod
    OWN = ("ground", "ink", "deep", "head", "body", "radius", "motif", "motion", "head_case", "head_weight", "display_weight")
    pos = positional(args, ("--style", "--name", "--accent", "--langs", "--lang", "--pick", "--topic", "--author", "--with") + tuple("--" + k.replace("_", "-") for k in OWN))
    own = {k: arg(args, "--" + k.replace("_", "-")) for k in OWN}
    if "--examine" in args:                                 # examples the user likes: what can be measured, and the pictures to look at
        srcs = [a for a in args[args.index("--examine") + 1:] if not a.startswith("--")] or die("which examples? vs.py design --examine <files or addresses of web pages>")
        found = design.examine(srcs, os.path.join(home(), "design", "examples"))
        for r in found:
            if r.get("note"): print(f"{r['name']}: {r['note']}"); continue
            print(f"{r['name']} ({r['kind']}, {r['pages']} page(s)): {'dark' if r['dark'] else 'light'} ground {r['ground']} | type {r['ink'] or 'not found'} | colour that marks {r['accent'] or 'none'}")
            for pth in r["look_at"]: print("  look at: " + pth)
        good = [r for r in found if not r.get("note")]
        if good:
            print("\nMeasured are only the colours. Read the rest from the pictures, example by example, and write it down before you build: the kind of typeface for titles and for text (serif, grotesque, condensed, rounded, mono; "
                  "light or heavy; capitals), how large titles are against the text, corners (sharp, soft, round), rules and frames (none, hairlines, thick), how full a slide is, what the accent colour is used for, "
                  "whether pictures bleed or sit in frames. Then ask the user what exactly they like about each example, and build the look from what the examples share:"
                  "\n  vs.py design <name> --style <nearest style> --ground \"#…\" --ink \"#…\" --accent \"#…\" --head \"Open typeface\" --body \"Open typeface\" --radius N [--motif none|wedge|block] [--motion <set>] [--head-case uppercase]"
                  "\nand write what the styles do not carry into the library's theme.css.")
        return
    lang = arg(args, "--lang") or (arg(args, "--langs") or "en").split(",")[0]; de = lang[:2] == "de"; all_styles = design.styles()
    cache = os.path.join(home(), ".cache", "fonts")
    if "--gallery" in args:
        pick = [x.strip() for x in (arg(args, "--pick") or "").split(",") if x.strip()] or list(all_styles)
        bad = [x for x in pick if x not in all_styles]
        if bad: die(f"no such style: {', '.join(bad)}. Styles: {', '.join(all_styles)}")
        tmp = tempfile.mkdtemp(prefix="vibeupslides_design_"); decks = {}; notes = set(); mine = arg(args, "--with"); first = []
        slides = design.sample(arg(args, "--name"), lang, arg(args, "--topic"))
        try:
            if mine:                                        # the look made from the user's examples stands first, the styles beside it
                mb = B.load_brand(mine); slides = design.sample(arg(args, "--name") or mb.get("name"), lang, arg(args, "--topic"))
                _render_and_build({"title": mine, "langs": [lang], "sample": True, "motion": "standard", "slides": slides}, mb, os.path.join(tmp, "_mine.html"))
                decks[mine] = base64.b64encode(open(os.path.join(tmp, "_mine.html"), "rb").read()).decode()
                first = [{"name": mine, "title": html_mod.escape(mb.get("name") or mine), "character": "Aus deinen Beispielen entwickelt." if de else "Developed from your examples.", "fits": ""}]
                if not arg(args, "--pick"): pick = pick[:2]
            for s in pick:
                bd = os.path.join(tmp, s); os.makedirs(bd)
                notes.update(design.make(bd, s, cache, name=arg(args, "--name"), langs=[lang]))
                _render_and_build({"title": s, "langs": [lang], "sample": True, "motion": "standard", "slides": slides}, B.load_brand(bd), os.path.join(tmp, s + ".html"))
                decks[s] = base64.b64encode(open(os.path.join(tmp, s + ".html"), "rb").read()).decode()
        finally:
            shutil.rmtree(tmp, ignore_errors=True)
        out_dir = os.path.join(home(), "design"); os.makedirs(out_dir, exist_ok=True); out = os.path.join(out_dir, "styles.html")
        open(out, "w", encoding="utf-8").write(DESIGN_PAGE.replace("__LANG__", "de" if de else "en")
            .replace("__HEAD__", "Welcher Look passt?" if de else "Which look fits?")
            .replace("__TEXT__", "Jede Kachel zeigt dieselben Folien in einem anderen Stil. Oben die Folie wählen, dann den Stil nennen, der es sein soll, gern mit dem, was anders sein soll (andere Farbe, ruhiger, kräftiger)." if de else
                     "Every tile shows the same slides in another style. Pick a slide above, then name the style you want, and what should be different about it (another colour, calmer, bolder).")
            .replace("__STYLES__", json.dumps(first + [{"name": k, "title": html_mod.escape(design._t(all_styles[k]["meta"].get("title"), lang)), "character": html_mod.escape(design._t(all_styles[k]["meta"].get("character"), lang)),
                                                "fits": html_mod.escape(design._t(all_styles[k]["meta"].get("fits"), lang))} for k in pick if k != mine]))
            .replace("__SLIDES__", json.dumps([("Titel", "Aussage", "Liste", "Zahlen", "Zusammenhang", "Karten") if de else ("Cover", "Statement", "List", "Figures", "Flow", "Cards")][0]))
            .replace("__DECKS__", json.dumps(decks)))
        print(f"styles side by side: {out} ({os.path.getsize(out) / 2**20:.1f} MB)")
        for nline in sorted(notes): print("NOTE:", nline.replace(os.path.basename(tmp), "<brand>"))
        print("Give the page to the user. When they have chosen: vs.py design <brand> --style <name> [--name \"…\"] [--accent \"#hex\"]"); return
    if not pos or not arg(args, "--style"):
        print(design.catalog(lang)); print("\nshow them side by side: vs.py design --gallery [--pick a,b,c] [--name \"Name\"] [--lang de]   make one the user's own: vs.py design <brand> --style <name>"); return
    name, style = pos[0], arg(args, "--style")
    if style not in all_styles: die(f"no such style: {style}. Styles: {', '.join(all_styles)}")
    if not re.match(r"^[a-z0-9][a-z0-9_-]*$", name): die("the folder name of a library is lower case letters, digits, - and _")
    bd = os.path.join(home(), "library", name)
    if os.path.exists(os.path.join(bd, "brand.json")): die(f"there is a library '{name}' already. Change it with vs.py set {name} … or choose another name.")
    os.makedirs(bd, exist_ok=True)
    try: notes = design.make(bd, style, cache, name=arg(args, "--name") or name, accent=arg(args, "--accent"), langs=[x.strip() for x in arg(args, "--langs").split(",")] if arg(args, "--langs") else None, author=arg(args, "--author"), own=own)
    except (ValueError, IndexError) as e: shutil.rmtree(bd, ignore_errors=True); die(f"{e} (colours are hex values such as #E5352B)")
    _scaffold(name)
    given = ", ".join(f"{k} {v}" for k, v in own.items() if v)
    design.journal(bd, (f"a look of its own, leaning on the style `{style}`: {given}" if given else f"started from the style `{style}`") + (f", accent colour {arg(args, '--accent')}" if arg(args, "--accent") else "") + ".", f"# How the look of {arg(args, '--name') or name} came about\n")
    print(f"library {name}: {bd}\nfrom the style {style}" + (f", accent {arg(args, '--accent')}" if arg(args, "--accent") else ""))
    for nline in notes: print("NOTE:", nline)
    print(f"NEXT: vs.py preview {name}, give the user the preview, write what they decide into design.md (design.journal), then confirm: vs.py confirm {name}")

def cmd_forms(args):
    """vs.py forms <brand>                                        the brand's own masters with the decks that use them, and free forms that came up more than once
       vs.py forms <brand> --promote <deck> --slide N --name <name>    make that free slide a master of the brand; every slide of the same form in the brand's decks uses it from then on
       vs.py forms <brand> --part <name> --from <deck> --slide N --block K       make block K of that free slide a part of the brand; every free slide holding the same block uses it
       vs.py forms <brand> --part <name> --from-master <master> --block K       make block K of one of the brand's masters a part; every master of the brand holding it word for word uses it"""
    import build as B, edit, forms, render
    pos = positional(args, ("--promote", "--slide", "--name", "--part", "--from", "--from-master", "--block"))
    name = pos[0] if pos else die("which brand? vs.py forms <brand>")
    bd = B.brand_dir(name); mem = forms.load(bd)
    if arg(args, "--part"):
        return _forms_part(args, name, bd)
    if arg(args, "--promote"):
        d = _deck_dir(arg(args, "--promote")); deck = edit.load(d); langs = deck.get("langs") or [deck.get("lang") or "en"]
        n = int(arg(args, "--slide") or die("which slide? --slide N")); new = arg(args, "--name") or die("name the master: --name <name>")
        if not re.match(r"^[a-z][a-z0-9_]*$", new): die("a master's name is lower case letters, digits and _")
        if new in render.load_masters(bd): die(f"there is a master '{new}' already")
        slides = deck.get("slides") or []
        if not 1 <= n <= len(slides) or slides[n - 1].get("master") != "free": die(f"slide {n} of {os.path.basename(d)} is not a free slide")
        k = forms.mark((forms._bodies(slides[n - 1], langs) or [""])[0]) or die("this slide has too little of a form of its own to be a master")
        text, _, slots = forms.to_master(new, slides[n - 1], langs)
        os.makedirs(os.path.join(bd, "masters"), exist_ok=True); open(os.path.join(bd, "masters", new + ".html"), "w", encoding="utf-8").write(text)
        changed = []
        for dn, dd, dk in _decks():                         # every slide of this form, in every deck of the brand
            if dk.get("brand") != name and B.brand_dir(dk.get("brand")) != bd: continue
            dl = dk.get("langs") or [dk.get("lang") or "en"]; hit = []
            for i, s in enumerate(dk.get("slides") or []):
                if isinstance(s, dict) and s.get("master") == "free" and forms.mark((forms._bodies(s, dl) or [""])[0]) == k:
                    _, conv, sl = forms.to_master(new, s, dl)
                    if len(sl) == len(slots): dk["slides"][i] = conv; hit.append(i + 1)
            if hit: edit.save(dd, dk); changed.append(f"{dn} (slide {', '.join(map(str, hit))})")
        mem = forms.load(bd); mem["seen"].pop(k, None); mem["own"][new] = {"made": time.strftime("%Y-%m-%d"), "from": f"{os.path.basename(d)}, slide {n}", "decks": [c.split(" ")[0] for c in changed]}
        json.dump(mem, open(forms.path(bd), "w", encoding="utf-8"), indent=1, ensure_ascii=False)
        print(f"master '{new}': {os.path.join(bd, 'masters', new + '.html')}\nits texts are the slots {', '.join(slots)}: give them names that say what they hold, write its `use`, and check it in the preview (vs.py preview {name})."
              f"\nnow using it: {', '.join(changed) or 'no deck'}. Build them again: vs.py refresh --brand {name}")
        return
    defaults = set(render.load_masters(None)); own = {n: m for n, m in render.load_masters(bd).items() if n not in defaults}
    use = {}
    for dn, dd, dk in _decks():
        if dk.get("brand") != name: continue
        for s in dk.get("slides") or []:
            if isinstance(s, dict) and s.get("master") in own: use.setdefault(s["master"], set()).add(dn)
    print(f"forms of {name}'s own (masters the framework does not have):")
    for n in sorted(own): print(f"  {n}: {own[n]['meta'].get('use', '')[:110]} | used by: {', '.join(sorted(use.get(n, []))) or 'no deck yet'}" + (f" | made {mem['own'][n].get('made')}" + (f" from {mem['own'][n]['from']}" if mem['own'][n].get('from') else "") if n in mem["own"] else ""))
    if not own: print("  none yet")
    rep = {k: v for k, v in mem["seen"].items() if len(v.get("uses") or []) > 1}
    print("\nfree slides in a form that came up more than once (make them masters: --promote <deck> --slide N --name <name>):")
    for k, v in rep.items(): print("  " + "; ".join(f"{u['deck']} slide {u['slide']} ({u.get('title', '')})" for u in v["uses"]) + f" | first seen {v.get('first')}")
    if not rep: print("  none")
    parts = render.load_parts(bd); puse = {}
    for dn, dd, dk in _decks():
        if dk.get("brand") != name: continue
        for s in dk.get("slides") or []:
            ps = s.get("parts") if isinstance(s, dict) else None
            for e in (ps if isinstance(ps, list) else [ps] if isinstance(ps, dict) else []):
                if isinstance(e, dict) and e.get("part"): puse.setdefault(str(e["part"]), set()).add(dn)
    inm = {}
    for mn, m in render.load_masters(bd).items():
        for pn in re.findall(r"\{\{>part\s+([\w-]+)", m.get("body") or ""): inm.setdefault(pn, []).append(mn)
    print("\nparts of the brand (blocks used by several slides or masters):")
    for n in sorted(parts): print(f"  {n}: {parts[n]['meta'].get('use', '')[:100]} | in masters: {', '.join(sorted(inm.get(n, []))) or '-'} | in decks: {', '.join(sorted(puse.get(n, []))) or '-'}")
    if not parts: print("  none yet")
    rp = {k: v for k, v in mem["parts"].items() if len(v.get("uses") or []) > 1 and len({u.get("form") for u in v["uses"]}) > 1}
    print("\nblocks that recur inside free slides of different forms (make them parts: --part <name> --from <deck> --slide N --block K):")
    for k, v in rp.items(): print("  " + "; ".join(f"{u['deck']} slide {u['slide']} block {u['block']}" for u in v["uses"]) + f" | first seen {v.get('first')}")
    if not rp: print("  none")
    sm = forms.shared_in_masters(bd)
    print("\nblocks the brand's masters hold word for word (make them parts: --part <name> --from-master <master> --block K):")
    for h, where in sm: print("  " + ", ".join(f"{m} block {b}" for m, b in where) + f" | {re.sub(r'<[^>]+>', ' ', h)[:60].strip()}")
    if not sm: print("  none")

def _forms_part(args, brand, bd):
    """vs.py forms <brand> --part <name> (--from <deck> --slide N | --from-master <master>) --block K"""
    import build as B, edit, forms, render
    new = arg(args, "--part")
    if not re.match(r"^[a-z][a-z0-9_]*$", new): die("a part's name is lower case letters, digits and _")
    if new in render.load_parts(bd): die(f"there is a part '{new}' already")
    k = int(arg(args, "--block") or die("which block? --block K (the build and vs.py forms <brand> name it)"))
    os.makedirs(os.path.join(bd, "parts"), exist_ok=True); dest = os.path.join(bd, "parts", new + ".html")
    if arg(args, "--from-master"):
        mn = arg(args, "--from-master"); mp = os.path.join(bd, "masters", mn + ".html")
        if not os.path.exists(mp): die(f"the brand has no master of its own called '{mn}'")
        blocks = forms.master_blocks(open(mp, encoding="utf-8").read())
        if not 1 <= k <= len(blocks): die(f"master {mn} has {len(blocks)} blocks")
        h = blocks[k - 1][1]; key = forms._norm(h)
        slots = sorted(set(re.findall(r"\{\{[#^/]?\s*([\w.]+)\s*\}\}", h)) - {"b", "lang", "brand"})
        meta = {"name": new, "use": "A part of this brand's own, a block several masters hold. Say here what it is for.", "slots": {s: "a slot of the slide that uses it" for s in slots}, "in_masters": True}
        open(dest, "w", encoding="utf-8").write("<!--vs " + json.dumps(meta, ensure_ascii=False) + " -->\n" + h.strip() + "\n")
        changed = []
        for fn in sorted(os.listdir(os.path.join(bd, "masters"))):
            if not fn.endswith(".html"): continue
            p = os.path.join(bd, "masters", fn); text = open(p, encoding="utf-8").read(); hit = False
            for _, b in forms.master_blocks(text):
                if forms._norm(b) == key and b in text: text = text.replace(b, "{{>part " + new + "}}", 1); hit = True
            if hit: open(p, "w", encoding="utf-8").write(text); changed.append(fn[:-5])
        print(f"part '{new}': {dest}\nused by the masters {', '.join(changed)} as {{{{>part {new}}}}}; it fills itself from the slots of each slide ({', '.join(slots) or 'none'})."
              f"\nwrite its `use`, check the preview (vs.py preview {brand}) and build the brand's decks again: vs.py refresh --brand {brand}")
        return
    d = _deck_dir(arg(args, "--from") or die("from where? --from <deck> --slide N, or --from-master <master>")); deck = edit.load(d)
    langs = deck.get("langs") or [deck.get("lang") or "en"]; slides = deck.get("slides") or []
    n = int(arg(args, "--slide") or die("which slide? --slide N"))
    if not 1 <= n <= len(slides) or slides[n - 1].get("master") != "free": die(f"slide {n} of {os.path.basename(d)} is not a free slide")
    first = (forms._bodies(slides[n - 1], langs) or [""])[0]; bl = forms.blocks(first)
    if not 1 <= k <= len(bl): die(f"slide {n} has {len(bl)} blocks")
    h = first[bl[k - 1][0]:bl[k - 1][1]]; key = forms.part_mark(h) or die("this block has too little of a form of its own to be a part (two elements and a class at least)")
    text, sample = forms.to_part(new, h); open(dest, "w", encoding="utf-8").write(text)
    changed = []
    for dn, dd, dk in _decks():                             # every free slide of the brand holding a block of this form
        if dk.get("brand") != brand and B.brand_dir(dk.get("brand")) != bd: continue
        dl = dk.get("langs") or [dk.get("lang") or "en"]; hit = []
        for i, s in enumerate(dk.get("slides") or []):
            if not isinstance(s, dict) or s.get("master") != "free": continue
            body = s.get("body"); per = isinstance(body, dict) and set(body) <= set(dl) | {"*"}
            bodies = dict(body) if per else {"": str(body or "")}
            found = {l: [(a, b) for a, b in forms.blocks(v) if forms.part_mark(v[a:b]) == key] for l, v in bodies.items()}
            m = min(len(v) for v in found.values()) if found else 0
            if not m: continue
            ps = s.get("parts"); ps = ps if isinstance(ps, list) else [ps] if isinstance(ps, dict) else []
            for j in range(m):
                vals = {l: forms.words(v[found[l][j][0]:found[l][j][1]]) for l, v in bodies.items()}
                if any(len(w) != len(sample) for w in vals.values()): continue
                e = {"part": new}
                for x in range(len(sample)):
                    per_l = {l: w[x] for l, w in vals.items()}
                    e[f"t{x + 1}"] = per_l if per and len(set(per_l.values())) > 1 else next(iter(per_l.values()))
                ps.append(e); found_n = len(ps)
                for l in bodies:
                    a, b = found[l][j]; v = bodies[l]
                    bodies[l] = v[:a] + f'<vs-part n="{found_n}"></vs-part>' + v[b:]
                    shift = len(f'<vs-part n="{found_n}"></vs-part>') - (b - a)
                    found[l] = [(x + shift, y + shift) if x > a else (x, y) for x, y in found[l]]
            if ps:
                s["parts"] = ps; s["body"] = bodies if per else bodies[""]; hit.append(i + 1)
        if hit: edit.save(dd, dk); changed.append(f"{dn} (slide {', '.join(map(str, hit))})")
    mem = forms.load(bd); mem["parts"].pop(key, None)
    mem["own_parts"][new] = {"made": time.strftime("%Y-%m-%d"), "from": f"{os.path.basename(d)}, slide {n}, block {k}", "decks": [c.split(" ")[0] for c in changed]}
    json.dump(mem, open(forms.path(bd), "w", encoding="utf-8"), indent=1, ensure_ascii=False)
    print(f"part '{new}': {dest}\nits texts are the slots {', '.join(sample)}: give them names that say what they hold (in the part and in the decks), write its `use`."
          f"\nnow using it: {', '.join(changed) or 'no deck'}. A slide names it with \"parts\": [{{\"part\": \"{new}\", ...}}]; a master with {{{{>part {new}}}}}."
          f"\nBuild the decks again: vs.py refresh --brand {brand}")

def cmd_refresh(args):
    """vs.py refresh [--brand <name>] [--all]: build again every deck that uses a shared slide or a fact (--all: every deck).
    The files a deck had before are kept in its .history/built/."""
    import contextlib, io, shared
    import build as B
    brand = arg(args, "--brand"); every = "--all" in args; done = 0; check = "--check" in args; skip = arg(args, "--except"); behind = []
    def newest(folder, names):
        t = 0
        for nme in names:
            p = os.path.join(folder, nme)
            if os.path.isdir(p):
                for dd, _, ff in os.walk(p): t = max([t] + [os.path.getmtime(os.path.join(dd, x)) for x in ff])
            elif os.path.exists(p): t = max(t, os.path.getmtime(p))
        return t
    for n, d, deck in _decks():
        if brand and deck.get("brand") != brand: continue
        if skip and n == skip: continue
        s, f = shared.uses(deck)
        built = [x for x in _deck_html(d, handout=True)]
        try: bd = B.brand_dir(deck.get("brand"))
        except SystemExit: continue
        when = min([os.path.getmtime(os.path.join(d, x)) for x in built] or [0])
        why = [w for w, names in (("what the brand's decks share", ["shared"]), ("the brand's look", ["theme.css", "masters", "motion.css", "motion", "brand.json"]), ("the framework", [os.path.join(home(), "framework", "VERSION")]))
               if built and newest(bd, names) > when]
        if check:
            if why: behind.append(n); print(f"{n}: behind, changed since it was built: {', '.join(why)}" + (f" (uses {', '.join(s + f)})" if s or f else ""))
            continue
        if not (every or why): continue
        if not built and not every:
            print(f"{n}: uses {', '.join(s + f)}, was never built: left alone"); continue
        keep = os.path.join(d, ".history", "built", time.strftime("%Y%m%d-%H%M%S")); os.makedirs(keep, exist_ok=True)
        for x in built + [x for x in os.listdir(d) if x.endswith(".pdf")]:
            try: shutil.copy2(os.path.join(d, x), os.path.join(keep, x))
            except OSError: pass
        runs = [[n, "--no-update", "--no-shots"] + (["--pdf"] if any(x.endswith(".pdf") for x in os.listdir(d)) else [])]
        main = deck.get("mode") or "live"
        for m in MODES:
            if m != main and any(x.endswith(f"_{m}.html") for x in built): runs.append([n, "--no-update", "--no-shots", "--mode", m])
        if any("_handout" in x for x in built): runs.append([n, "--no-update", "--no-shots", "--handout"])
        buf = io.StringIO(); failed = None
        for r in runs:
            try:
                with contextlib.redirect_stdout(buf): cmd_build(r)
            except SystemExit: failed = buf.getvalue().strip().splitlines()[-1:] or ["failed"]
        out = buf.getvalue(); done += 1
        flags = [l.strip() for l in out.splitlines() if l.strip().startswith(("SHARED:", "LEGIBILITY", "WORDY", "VOICE")) or ("overflow:" in l and "clean" not in l)]
        print(f"{n}: built again ({', '.join(s + f) or 'no shared parts'}; {len(runs)} file(s))" + (" | FAILED: " + failed[0] if failed else "") + (f" | {len(flags)} finding(s), build it alone to see them: vs.py build {n}" if flags else ""))
        for l in flags[:3]: print("    " + l[:200])
    if check:
        print(f"\n{len(behind)} deck(s) are behind." + (f" Ask the user whether to bring them up to date; if yes: vs.py refresh" + (f" --brand {brand}" if brand else "") if behind else " Nothing to do."))
        return
    print(f"\n{done} deck(s) brought up to date." + ("" if done else " Every deck is as new as its brand (--all builds every deck anyway)."))
    if done: print("The files from before are kept in each deck's .history/built/. Decks that were sent out as files do not change by themselves: send the new file where it matters.")

def _scene_gallery(name, bd, scenes):
    """One file that shows every scene of the catalogue with its still, and plays it on a click: for the user to choose from."""
    import base64, html as H, build as B, media
    b = json.load(open(os.path.join(bd, "brand.json"), encoding="utf-8")); chosen = b.get("scenes") or []
    de = brand_langs(b)[0] == "de"
    T = ({"h": "Animierte Szenen für ", "p": "Szenen können, was Folienprogramme nicht können: 3D, Physik, bewegte Schrift. Ein Klick auf ein Bild spielt die Szene (Pfeiltasten gehen durch ihre Schritte, Esc schließt). "
          "Ein Klick auf den Text darunter wählt sie aus. Kopiere am Ende die Zeile unten und schick sie Claude.", "copy": "Auswahl kopieren", "copied": "Kopiert", "mine": "Meine Szenen: ", "none": "Noch keine Szene gewählt",
          "new": "neu", "close": "Schließen", "keys": "→ nächster Schritt · Esc schließt", "steps": "Schritte", "self": "läuft von selbst", "on": "braucht Internet", "off": "läuft ohne Internet"} if de else
         {"h": "Animated scenes for ", "p": "Scenes do what slide software cannot: 3D, physics, moving type. Click a picture to watch one (arrow keys run its steps, Esc closes). "
          "A click on the text below ticks it. At the end copy the line at the bottom and send it to Claude.", "copy": "Copy my choice", "copied": "Copied", "mine": "My scenes: ", "none": "No scene chosen yet",
          "new": "new", "close": "Close", "keys": "→ next step · Esc closes", "steps": "steps", "self": "plays by itself", "on": "needs internet", "off": "works offline"})
    cards, plays = [], {}
    seen = b.get("scenes_seen"); fresh = set(_new_scenes()) - set(seen or []) if seen is not None else set()
    for n, s in sorted(scenes.items(), key=lambda kv: (n not in fresh if (n := kv[0]) else 0, kv[1]["meta"].get("category", "~"), kv[0])):
        m = s["meta"]; poster = os.path.join(s["dir"], m.get("poster") or "poster.jpg")
        img = "data:image/jpeg;base64," + base64.b64encode(open(poster, "rb").read()).decode() if os.path.exists(poster) else ""
        try:                                                # as it would run in a slide: the scene's example, the brand's colours and type
            tokens = media.token_values(B.load_brand(name)); css = {}
            for prop, token in (m.get("vars") or {}).items():
                if tokens.get(token) and token not in ("font", "font_head"): css[prop] = tokens[token]
            page = media.embed_scene_html(open(os.path.join(s["dir"], "index.html"), encoding="utf-8").read(), m.get("sample") if isinstance(m.get("sample"), dict) else {}, css, None, int(m.get("steps") or 0) or None)
            plays[n] = base64.b64encode(page.encode("utf-8")).decode()
        except (OSError, ValueError, KeyError, TypeError, SystemExit):
            try: plays[n] = base64.b64encode(open(os.path.join(s["dir"], "index.html"), "rb").read()).decode()
            except OSError: pass
        steps = int(m.get("steps") or 0)
        facts = [m.get("category") or "", f"{steps} {T['steps']}" if steps else T["self"], T["on"] if m.get("online") else T["off"]]
        if m.get("showcase") is False and s["origin"] != "brand" and n not in chosen: continue      # bound to one motif: a model for a brand's own scene
        cards.append(f'<button class="c{" on" if n in chosen else ""}" data-n="{H.escape(n)}"><i style="background-image:url({img})"></i><b>{H.escape(m.get("title", n))}{" <u>" + T["new"] + "</u>" if n in fresh else ""}</b>'
                     f'<small>{H.escape(" · ".join(f for f in facts if f))}</small><span>{H.escape(m.get("use", ""))}</span><em>{H.escape(n)}</em></button>')
    page = ("<!DOCTYPE html><html lang='en'><head><meta charset='utf-8'><meta name='viewport' content='width=device-width, initial-scale=1'><title>Scenes for " + H.escape(b.get("name", name)) + "</title><style>"
            "body{margin:0;background:#17171a;color:#e9eaee;font:15px/1.45 system-ui,sans-serif}header{padding:28px 32px 8px;max-width:1100px}h1{margin:0 0 6px;font-size:26px}p{margin:0;color:#aab1bd}"
            "main{display:grid;grid-template-columns:repeat(auto-fill,minmax(300px,1fr));gap:16px;padding:20px 32px 120px}"
            ".c{all:unset;cursor:pointer;display:flex;flex-direction:column;gap:5px;padding:10px;border-radius:12px;background:#222226;border:2px solid transparent}.c:hover{background:#2a2a2f}.c.on{border-color:#7fd88a}"
            ".c i{display:block;aspect-ratio:16/9;border-radius:8px;background:#000 center/cover}.c b{font-size:17px;margin-top:4px}.c u{text-decoration:none;font-size:11px;font-weight:700;letter-spacing:.06em;text-transform:uppercase;background:#ff7a59;color:#111;border-radius:999px;padding:2px 8px;vertical-align:middle}.c small{color:#8fd3a8}.c span{color:#c9ced8}.c em{font-style:normal;color:#7b828f;font-family:ui-monospace,monospace;font-size:12px}"
            "#bar{position:fixed;left:0;right:0;bottom:0;padding:14px 32px;background:#101013;border-top:1px solid #333;display:flex;gap:16px;align-items:center}#bar code{flex:1;color:#fff;font-size:14px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}"
            "#bar button,#x{font:600 14px system-ui;color:#111;background:#fff;border:0;border-radius:8px;padding:10px 16px;cursor:pointer}"
            "#play{position:fixed;inset:0;background:rgba(0,0,0,.92);display:none;place-items:center;z-index:9}#play.on{display:grid}#play iframe{width:min(92vw,160vh);aspect-ratio:16/9;border:0;border-radius:10px;background:#000}#x{position:fixed;top:18px;right:22px}"
            "#play p{position:fixed;bottom:18px;left:0;right:0;text-align:center}"
            "</style></head><body><header><h1>" + T["h"] + H.escape(b.get("name", name)) + "</h1><p>" + T["p"] + "</p></header><main>" + "".join(cards) + "</main>"
            "<div id='bar'><code id='pick'></code><button id='copy'>" + T["copy"] + "</button></div><div id='play'><button id='x'>" + T["close"] + "</button><iframe></iframe><p>" + T["keys"] + "</p></div><script>"
            "var TT=" + json.dumps(T, ensure_ascii=False) + ",P=" + json.dumps(plays) + ",pick=document.getElementById('pick'),play=document.getElementById('play'),fr=play.querySelector('iframe');"
            "function line(){var l=[].map.call(document.querySelectorAll('.c.on'),function(c){return c.getAttribute('data-n')});pick.textContent=l.length?TT.mine+l.join(', '):TT.none;}"
            "function close(){play.classList.remove('on');fr.removeAttribute('srcdoc');}"
            "document.querySelectorAll('.c').forEach(function(c){c.addEventListener('click',function(e){if(e.target.tagName==='I'&&P[c.getAttribute('data-n')]){fr.srcdoc=decodeURIComponent(escape(atob(P[c.getAttribute('data-n')])));play.classList.add('on');setTimeout(function(){fr.focus();},200);}else{c.classList.toggle('on');line();}});});"
            "document.getElementById('x').onclick=close;addEventListener('keydown',function(e){if(e.key==='Escape')close();});"
            "document.getElementById('copy').onclick=function(){navigator.clipboard&&navigator.clipboard.writeText(pick.textContent);this.textContent=TT.copied;};line();</script></body></html>")
    out = os.path.join(bd, "preview", "scenes.html"); os.makedirs(os.path.dirname(out), exist_ok=True)
    open(out, "w", encoding="utf-8").write(page)
    return (f"scene gallery: {out} ({len(cards)} scenes, {os.path.getsize(out) / 2**20:.1f} MB). Give it to the user: a click on a picture plays the scene, a click on the text ticks it, "
            f"the bar at the bottom holds their choice to copy. Record it with: vs.py scenes {name} --choose a,b,c")

def cmd_pack(args):
    import media, zipfile
    pos = positional(args)
    d = _deck_dir(pos[0] if pos else die("which deck?"))
    html = _deck_html(d, handout=True)
    if not html: die("build the deck first: vs.py build " + os.path.basename(d))
    files, online = media.referenced_files(d, html)
    name = os.path.basename(d); out = os.path.join(os.path.dirname(d), name + ".zip")
    with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as z:
        for rel in sorted(html) + files:
            stored = rel.lower().endswith((".mp4", ".m4v", ".webm", ".mov", ".ogv", ".jpg", ".jpeg", ".png", ".webp", ".woff2"))      # already compressed
            z.write(os.path.join(d, rel), name + "/" + rel.replace(os.sep, "/"), zipfile.ZIP_STORED if stored else zipfile.ZIP_DEFLATED)
    print(f"{out}  {os.path.getsize(out) / 1048576:.1f} MB: {len(html)} HTML file(s), {len(files)} linked file(s)")
    for rel in files[:12]: print("  " + rel)
    if len(files) > 12: print(f"  ... and {len(files) - 12} more")
    if not files: print("This deck links no files: the HTML alone is the whole deck.")
    if online: print("NEEDS TO BE ONLINE when shown: " + ", ".join(online))
    else: print("Runs offline. Unpack the folder and open the HTML; keep the files together.")

def cmd_video(args):
    import video_export
    pos = positional(args, ("--slide", "--seconds", "--format", "--lang", "--hide"))
    d = _deck_dir(pos[0] if pos else die("which deck?"))
    html = _deck_html(d)
    if not html: die("build the deck first")
    out = os.path.join(d, f"slide_{arg(args, '--slide', '1')}.mp4")
    video_export.render(os.path.join(d, html[0]), int(arg(args, "--slide", 1)), float(arg(args, "--seconds", 6)), out, lang=arg(args, "--lang"),
                        fmt=arg(args, "--format", "16:9"), hide=tuple(a for i, a in enumerate(args) if i and args[i - 1] == "--hide"))
    print(out)


MOTION_COMPARE = '''<!doctype html><html lang="en"><meta charset="utf-8"><title>__BRAND__ motion sets</title>
<style>
body{margin:0;padding:28px 32px 48px;background:#161616;color:#eee;font:15px/1.45 system-ui,sans-serif}
h1{font-size:22px;font-weight:600;margin:0 0 4px} p{margin:0;color:#aaa}
.bar{display:flex;flex-wrap:wrap;gap:8px;margin:20px 0 24px;align-items:center}
button{font:inherit;color:#eee;background:#2a2a2a;border:1px solid #444;border-radius:6px;padding:7px 14px;cursor:pointer}
button.on{background:#eee;color:#161616;border-color:#eee} button.go{margin-left:auto}
.grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(420px,1fr));gap:24px}
.cell h2{font-size:16px;font-weight:600;margin:10px 0 2px} .cell h2 span{font-weight:400;color:#7ad;margin-left:8px}
.cell p{font-size:13px} .cell code{color:#ccc}
.frame{position:relative;aspect-ratio:16/9;background:#000;border-radius:6px;overflow:hidden}
.cell.cur .frame{outline:2px solid #7ad}
iframe{position:absolute;inset:0;width:100%;height:100%;border:0;pointer-events:none}
</style>
<h1>__HEAD__</h1>
<p>__TEXT__</p>
<div class="bar" id="bar"></div><div class="grid" id="grid"></div>
<script>
var sets=__SETS__, slides=__SLIDES__, cur="__CURRENT__", n=1, decks=__DECKS__;
function deck(name){ var s=atob(decks[name]), a=new Uint8Array(s.length); for(var i=0;i<s.length;i++) a[i]=s.charCodeAt(i);
  return URL.createObjectURL(new Blob([a],{type:"text/html"})); }
var bar=document.getElementById("bar"), grid=document.getElementById("grid");
function play(){ document.querySelectorAll("iframe").forEach(function(f){ f.contentWindow.postMessage({vs:"replay",slide:n},"*"); }); }
slides.forEach(function(s,i){ var b=document.createElement("button"); b.textContent=s; if(!i) b.className="on";
  b.onclick=function(){ n=i+1; bar.querySelectorAll("button").forEach(function(x){x.classList.remove("on");}); b.classList.add("on"); play(); }; bar.appendChild(b); });
var g=document.createElement("button"); g.textContent="__PLAY__"; g.className="go"; g.onclick=play; bar.appendChild(g);
sets.forEach(function(s){ var c=document.createElement("div"); c.className="cell"+(s.name===cur?" cur":"");
  c.innerHTML='<div class="frame"><iframe></iframe></div><h2>'+s.title+' <code>'+s.name+'</code>'+(s.name===cur?'<span>__CUR__</span>':'')+'</h2><p>'+s.character+'</p>';
  grid.appendChild(c); c.querySelector('iframe').src=deck(s.name); });
</script></html>
'''

def _motion_deck(args, pos):
    """vs.py motion --deck <deck> [--compare] [--set <name>|brand] [--level calm|standard|expressive|off]
    The movement of one presentation: the sets side by side on its own slides, and the set and strength it uses."""
    import base64, build as B, edit, motion, tempfile
    import html as html_mod
    d = _deck_dir(arg(args, "--deck")); dname = os.path.basename(d); deck = edit.load(d)
    b = B.load_brand(deck.get("brand") or die("deck.json names no brand")); all_sets = motion.sets(b["_dir"])
    chosen, level = arg(args, "--set"), arg(args, "--level")
    if chosen or level:
        if chosen and chosen != "brand" and chosen not in all_sets: die(f"unknown motion set '{chosen}'. Sets: {', '.join(all_sets)} (or `brand` for the brand's own)")
        if chosen == "brand": deck.pop("motion_set", None)
        elif chosen: deck["motion_set"] = chosen
        if level: deck["motion"] = motion.intensity(level)
        edit.save(d, deck)
    cur = deck.get("motion_set") if deck.get("motion_set") in all_sets else motion.profile(b)["set"]
    print(f"movement of {dname}: set {cur}" + ("" if deck.get("motion_set") in all_sets else " (the brand's)") + f", strength {motion.intensity(deck.get('motion', True))}")
    if chosen or level: print(f"written into deck.json; build it: vs.py build {dname}")
    if "--compare" not in args:
        if not (chosen or level): print(f"the sets side by side on this deck's slides: vs.py motion --deck {dname} --compare   choose: vs.py motion --deck {dname} --set <name> [--level calm|standard|expressive]")
        return
    # a few typical slides of the deck: its first, a chapter, a list, a figure, then whatever follows
    slides = [s for s in deck.get("slides") or [] if isinstance(s, dict)]; kind = lambda s: str(s.get("master") or s.get("shared") or "")
    groups = [lambda s: True, lambda s: kind(s).startswith("chapter"), lambda s: kind(s) in ("bullets", "cards", "steps", "columns", "process", "agenda"),
              lambda s: kind(s) in ("big_number", "kpis", "bars", "figure", "line_chart", "timeline", "phases")]
    picked = []; fits = lambda s: kind(s) not in ("timer", "scene", "video", "video_title", "embed") and not kind(s).startswith("quiz")
    for g in groups:
        hit = next((i for i, s in enumerate(slides) if i not in picked and g(s) and fits(s)), None)
        if hit is not None: picked.append(hit)
    for i, s in enumerate(slides):                          # fewer than four kinds found: other masters the deck uses
        if len(picked) >= 4: break
        if i not in picked and fits(s) and kind(s) not in [kind(slides[k]) for k in picked]: picked.append(i)
    picked = sorted(picked)[:5]
    if not picked: die("the deck has no slides yet")
    lang = (deck.get("langs") or [deck.get("lang") or "en"])[0]; de = lang[:2] == "de"
    import render, shared
    langs = deck.get("langs") or [lang]; whole, _ = shared.resolve(deck, b["_dir"]); slides = [s for s in whole.get("slides") or [] if isinstance(s, dict)]
    part = dict(deck, langs=[lang], sample=True, contents=False, motion=motion.intensity(level or deck.get("motion", True)),      # one language: every text taken in it first
                slides=[dict(render._resolve_lang(slides[i], lang, langs), step=False) for i in picked])
    if part["motion"] == "off": part["motion"] = "standard"
    live = tempfile.mkdtemp(prefix="vibeupslides_compare_"); decks = {}
    try:
        for s in all_sets:
            _render_and_build(dict(part, motion_set=s), b, os.path.join(live, s + ".html"), deck_dir=d)
            decks[s] = base64.b64encode(open(os.path.join(live, s + ".html"), "rb").read()).decode()
    finally:
        shutil.rmtree(live, ignore_errors=True)
    os.makedirs(os.path.join(d, "shots"), exist_ok=True)
    out = os.path.join(d, "shots", "motion.html"); title = html_mod.escape(re.sub(r"<[^>]+>", "", str(render_title(deck, lang) or dname)))
    labels = [(("Folie " if de else "Slide ") + str(i + 1)) for i in picked]
    open(out, "w", encoding="utf-8").write(MOTION_COMPARE
        .replace("__HEAD__", (title + ": die Bewegungssets nebeneinander") if de else (title + ": the motion sets side by side"))
        .replace("__TEXT__", "Jede Kachel spielt dieselbe Folie dieser Präsentation in einem anderen Set. Folie wählen, beliebig oft abspielen, dann das Set nennen, das es sein soll." if de else
                 "Every tile plays the same slide of this presentation in another set. Pick a slide, play it as often as you like, then name the set you want.")
        .replace("__PLAY__", "Noch einmal abspielen" if de else "Play again").replace("__CUR__", "jetzt gewählt" if de else "current set")
        .replace("__BRAND__", title).replace("__CURRENT__", cur)
        .replace("__SETS__", json.dumps([{"name": k, "title": v.get("title", k), "character": v.get("character", "")} for k, v in all_sets.items()]))
        .replace("__SLIDES__", json.dumps(labels)).replace("__DECKS__", json.dumps(decks)))
    print(f"\nmotion sets side by side on slides {', '.join(str(i + 1) for i in picked)} of {dname}: {out} ({os.path.getsize(out) / 2**20:.1f} MB)"
          f"\nchoose for this deck: vs.py motion --deck {dname} --set <name> [--level calm|standard|expressive]   for every deck of the brand: vs.py motion {os.path.basename(b['_dir'])} --set <name>")

def render_title(deck, lang):
    t = deck.get("title")
    return t.get(lang, next(iter(t.values()), "")) if isinstance(t, dict) else t

def cmd_motion(args):
    """vs.py motion <brand> [--strip [set|all]] [--set <name>] [--level calm|standard|expressive] [--reset]"""
    import build as B, brandtools, motion, render, tempfile
    import html as html_mod
    all_sets = motion.sets()
    strip = None
    if "--strip" in args:                                  # --strip takes an optional set name
        k = args.index("--strip")
        strip = args[k + 1] if k + 1 < len(args) and (args[k + 1] in all_sets or args[k + 1] in ("all", "site")) else "current"
        args = args[:k + 1] + args[k + (2 if strip != "current" else 1):]
    pos = positional(args, ("--set", "--level", "--deck"))
    if arg(args, "--deck"): return _motion_deck(args, pos)
    name = pos[0] if pos else die("which brand? vs.py motion <brand> [--strip [set|all]] [--set <name>]")
    chosen = arg(args, "--set")
    all_sets = motion.sets(B.brand_dir(name))               # with the brand's own sets, such as the one copied from its website
    if "--site" in args:                                    # make the set copied from the website again, from what was measured
        try: facts = json.load(open(os.path.join(B.brand_dir(name), "raw", "motion.json"), encoding="utf-8"))
        except (OSError, ValueError): die(f"the website of {name} was not measured yet: vs.py analyze <url> --brand {name} --again")
        path = motion.write_site_set(B.brand_dir(name), facts, (facts.get("pages") or [""])[0])
        print(f"set copied from the website: {path}" if path else "the website shows no entrance that could be copied: no `site` set")
        all_sets = motion.sets(B.brand_dir(name))
    if chosen or "--reset" in args:
        if chosen and chosen not in all_sets: die(f"unknown motion set '{chosen}'. Sets: {', '.join(all_sets)}")
        data = brandtools._read(name); m = data.get("motion") if isinstance(data.get("motion"), dict) else {}
        if chosen: m["set"] = chosen
        if "--reset" in args: m = {"set": m.get("set", motion.DEFAULT_SET)}      # drop the brand's own tokens, the set's defaults apply
        data["motion"] = m; brandtools._write(name, data)
        print(f"motion set of {name}: {m['set']}" + (" (tokens reset to the set's own)" if "--reset" in args else ""))
    b = B.load_brand(name); d = b["_dir"]; p = motion.profile(b)
    own = {k: v for k, v in (b.get("motion") or {}).items() if k in motion.TOKENS}
    print(f"motion sets (* is the set of {name}):\n" + motion.catalog(p["set"], d))
    if "site" not in all_sets: print("  (no set copied from the website: it was not measured, or shows no entrance that could be copied; `vs.py motion " + name + " --site` tries again)")
    print(f"\nprofile: set {p['set']} | ease {p['ease']} | duration {p['duration']:g} s | stagger {p['stagger']:g} s | travel {p['travel']:g} px | change {p['change']}")
    print("tokens from brand.json: " + (", ".join(own) or "none, the set's own values apply") + " | motion.css: " + ("present" if os.path.exists(os.path.join(d, "motion.css")) else "none"))
    try: sug = json.load(open(os.path.join(d, "raw", "motion.json"), encoding="utf-8")).get("suggestion") or {}
    except (OSError, ValueError): sug = {}
    if sug: print(f"the website analysis suggested: {sug.get('set')} ({sug.get('why')})")
    compare = "--compare" in args
    if strip is None and not compare:
        print(f"\ncompare all sets live: vs.py motion {name} --compare   film strip of a set: vs.py motion {name} --strip [set|all]   choose one: vs.py motion {name} --set <name>   single tokens: vs.py set {name} motion.duration=0.6")
        return
    level = motion.intensity(arg(args, "--level", "standard"))
    masters = render.load_masters(d)
    wanted = [n for n in ("cover", "chapter", "bullets", "bars" if "bars" in masters else "kpis") if n in masters and masters[n]["meta"].get("sample") is not None]
    slides = [dict(render.fit_langs(masters[n]["meta"]["sample"], ["en"]), master=n, step=False) for n in wanted]
    if compare:                                            # every set plays the same slides side by side, for the user to choose from
        import base64                                      # one file that carries all decks, so it opens anywhere and can be sent
        live = tempfile.mkdtemp(prefix="vibeupslides_compare_"); decks = {}
        stand = _standins(b, os.path.join(d, "raw", "standins"))
        try:
            for s in all_sets:
                _render_and_build({"title": "motion " + s, "langs": ["en"], "sample": True, "motion": level, "slides": slides},
                                  dict(b, motion=dict(b.get("motion") or {}, set=s)), os.path.join(live, s + ".html"), standins=stand)
                decks[s] = base64.b64encode(open(os.path.join(live, s + ".html"), "rb").read()).decode()
        finally:
            shutil.rmtree(live, ignore_errors=True)
        os.makedirs(os.path.join(d, "preview", "motion"), exist_ok=True)
        out = os.path.join(d, "preview", "motion", "compare.html")
        open(out, "w", encoding="utf-8").write(MOTION_COMPARE.replace("__HEAD__", "__BRAND__: the motion sets side by side").replace("__PLAY__", "Play again").replace("__CUR__", "current set")
            .replace("__TEXT__", "Every tile plays the same slide in another set. Pick a slide, press Play again as often as you like, then name the set you want.")
            .replace("__BRAND__", html_mod.escape(b.get("name", name))).replace("__CURRENT__", p["set"])
            .replace("__SETS__", json.dumps([{"name": k, "title": v.get("title", k), "character": v.get("character", "")} for k, v in all_sets.items()]))
            .replace("__SLIDES__", json.dumps(wanted)).replace("__DECKS__", json.dumps(decks)))
        print(f"\nmotion sets side by side: {out}\nchoose one: vs.py motion {name} --set <name>")
        if strip is None: return
    tmp = tempfile.mkdtemp(prefix="vibeupslides_motion_"); stand = _standins(b, os.path.join(d, "raw", "standins"))
    print()
    try:
        for s in (list(all_sets) if strip == "all" else [p["set"] if strip == "current" else strip]):
            bb = dict(b, motion=dict(b.get("motion") or {}, set=s))
            html = os.path.join(tmp, s + ".html")
            _render_and_build({"title": "motion", "langs": ["en"], "sample": True, "motion": level, "slides": slides}, bb, html, standins=stand)
            out = os.path.join(d, "preview", "motion", f"strip_{s}" + ("" if level == "standard" else "_" + level) + ".png")
            q = motion.profile(bb)
            motion.film_strip(html, out, labels=wanted, lang="en",
                              title=f"{b.get('name', name)} | set {s} | {level} | ease {q['ease']} | {q['duration']:g} s | stagger {q['stagger']:g} s | travel {q['travel']:g} px | change {q['change']}")
            print("film strip:", out)
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    print("Each row is one slide, the frames run from left to right; the last frame must be the finished slide.")


def main():
    a = sys.argv[1:]
    if not a or a[0] in ("-h", "--help", "help"):
        print(__doc__); return
    cmd, rest = a[0], a[1:]
    _ensure_env()
    import brandtools
    simple = {"init": cmd_init, "status": cmd_status, "update": cmd_update, "permissions": cmd_permissions, "doctor": cmd_doctor, "backup": cmd_backup, "restore": cmd_restore, "analyze": cmd_analyze, "videos": cmd_videos, "voice": cmd_voice, "ingest": cmd_ingest, "preview": cmd_preview,
              "masters": cmd_masters, "elements": cmd_elements, "fonts": cmd_fonts, "new": cmd_new, "build": cmd_build, "titles": cmd_titles,"video": cmd_video,
              "scenes": cmd_scenes, "motion": cmd_motion, "present": cmd_present, "edit": cmd_edit, "apply": cmd_apply, "shared": cmd_shared, "forms": cmd_forms, "design": cmd_design, "refresh": cmd_refresh, "langs": cmd_langs, "pack": cmd_pack}
    try:
        if cmd in simple: simple[cmd](rest)
        elif cmd == "brands":
            import build as B
            for d in B.list_brands(): print(os.path.basename(d))
        elif cmd == "show": brandtools.show(rest[0])
        elif cmd == "set": brandtools.set_values(rest[0], rest[1:])
        elif cmd == "confirm": brandtools.set_values(rest[0], ["confirmed=true"])
        elif cmd == "logo":
            {"trim": brandtools.trim, "inverse": brandtools.inverse}[rest[0]](rest[1], rest[2] if len(rest) > 2 else None)
        else:
            die(f"unknown command '{cmd}'. Run vs.py help.")
    except (FileNotFoundError, ValueError, KeyError, IndexError) as e:
        die("an argument is missing. Run vs.py help." if isinstance(e, IndexError) else (f"missing field {e}" if isinstance(e, KeyError) else str(e)))

if __name__ == "__main__":
    main()
