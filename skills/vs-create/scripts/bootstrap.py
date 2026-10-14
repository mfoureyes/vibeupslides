#!/usr/bin/env python3
"""Set up or find the VibeUpSlides workspace and print the command to use.

    python3 bootstrap.py [--home <folder>]

The workspace is one folder on the user's computer: $VIBEUPSLIDES_HOME or ~/vibeupslides. In a session
that runs elsewhere (Cowork) and sees folders the user shared, it is the folder `vibeupslides` inside
one of them; the script looks for it there, and when there is none yet it says so and stops, so the
user can be asked where it should be (`--home`). In a session that sees no folder of the user at
all, the workspace is set up in the session, says that it is temporary, and takes brands and decks
from a backup file the user uploaded (`vs.py backup` writes it). If the workspace or its Python environment does not exist yet,
the framework is copied there from the vs-update skill and an environment with Pillow and Playwright
is created (one to two minutes). Afterwards everything runs through
    python3 <workspace>/vs.py <command>
"""
import glob, os, subprocess, sys

here = os.path.dirname(os.path.realpath(__file__))
user = os.path.expanduser("~")
args = sys.argv[1:]
remote = user.startswith("/sessions/") or os.environ.get("CLAUDE_CODE_REMOTE", "").lower() in ("1", "true") or "cowork" in os.environ.get("CLAUDE_CODE_ENTRYPOINT", "")
sandbox = os.environ.get("VIBEUPSLIDES_SANDBOX", "1" if remote else "") not in ("", "0")

def is_ws(p):
    return os.path.exists(os.path.join(p, "vs.py")) and os.path.isdir(os.path.join(p, "framework"))

def shared():
    """Folders of the user's computer this session can see, without the session's own."""
    own = ("/mnt/user-data", "/mnt/attach", "/mnt/skills", "/mnt/sandboxing", os.path.realpath(user), os.path.realpath(os.getcwd()))
    found = sorted(glob.glob(os.path.join(user, "mnt", "*"))) + [p for p in os.environ.get("CLAUDE_ADDITIONAL_DIRECTORIES", "").split(os.pathsep) if p]
    out = []
    for p in found:
        if os.path.isdir(p) and not os.path.basename(p).startswith(".") and os.path.basename(p) not in ("outputs", "uploads", "user-data") \
                and not any(os.path.realpath(p) == o or os.path.realpath(p).startswith(o + os.sep) for o in own[:4]) and os.path.realpath(p) not in own and p not in out:
            out.append(p)
    return out

ws = os.path.abspath(args[args.index("--home") + 1]) if "--home" in args and args.index("--home") + 1 < len(args) else os.environ.get("VIBEUPSLIDES_HOME")
if not ws:
    places = [os.path.join(user, "vibeupslides")]
    for base in ([os.getcwd()] + shared() if sandbox else []):
        places += [base, os.path.join(base, "vibeupslides")]
    ws = next((p for p in places if is_ws(p)), None)
    if not ws and sandbox and shared():
        print("NO WORKSPACE YET. This session sees only folders the user shared, and VibeUpSlides keeps brands and decks in one of them.")
        print("shared folders:", ", ".join(shared()) or "none")
        print("Ask the user in which folder of their computer VibeUpSlides should keep its files (they may have to share one with this session first), then run:")
        print(f"    python3 {os.path.abspath(__file__)} --home <that folder>/vibeupslides")
        sys.exit(2)
    ws = ws or places[0]
os.environ["VIBEUPSLIDES_HOME"] = ws

skills = os.path.dirname(os.path.dirname(here))
payload = next((p for p in (os.path.join(skills, "vs-update", "framework"), os.path.join(os.path.dirname(here), "framework"))
                if os.path.exists(os.path.join(p, "vs.py"))), None)
launcher = os.path.join(ws, "vs.py")
envs = [os.environ.get("VIBEUPSLIDES_VENV"), os.path.join(ws, ".venv"), os.path.join(user, ".vibeupslides", "venv")]
if is_ws(ws) and any(e and os.path.exists(os.path.join(e, b)) for e in envs for b in ("bin/python", "Scripts/python.exe")):
    if payload:                                            # where updates come from: this installation, wherever it lives now
        try: open(os.path.join(ws, ".source"), "w", encoding="utf-8").write(os.path.realpath(payload))
        except OSError: pass
    print("workspace ready:", ws)
    print("command: python3", launcher, flush=True)
    sys.exit(subprocess.call([sys.executable, launcher, "status"]))
if not payload:
    sys.exit("The framework was not found next to this skill. Install the whole set: npx skills add mfoureyes/vibeupslides")
code = subprocess.call([sys.executable, os.path.join(payload, "vs.py"), "init"] + (["--no-venv"] if os.environ.get("VS_NO_VENV") else []))
if code == 0:
    print("command: python3", launcher, flush=True)
    if sandbox and not os.listdir(os.path.join(ws, "library")):   # a new session: brands and decks come from the backup the user uploaded
        ups = [f for d in (os.environ.get("VIBEUPSLIDES_UPLOADS"), "/mnt/user-data/uploads", os.path.join(user, "mnt", "uploads")) if d and os.path.isdir(d)
               for f in glob.glob(os.path.join(d, "*slides-workspace*.zip"))]
        if ups:
            subprocess.call([sys.executable, launcher, "restore", max(ups, key=os.path.getmtime)])
        else:
            print("No backup file was uploaded. If the user connected a folder, look there for vibeupslides-workspace.zip; if they have made brands with VibeUpSlides before, ask for it. Then: vs.py restore <file>", flush=True)
sys.exit(code)
