#!/usr/bin/env python3
"""Pack VibeUpSlides as a plugin file for Cowork and Claude Code: out/vibeupslides.plugin

    python3 tools/plugin.py
"""
import json, os, zipfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
man = json.load(open(os.path.join(ROOT, ".claude-plugin", "plugin.json"), encoding="utf-8"))
ver = open(os.path.join(ROOT, "skills", "vs-update", "framework", "VERSION"), encoding="utf-8").read().strip()
assert man["version"] == ver, f"plugin.json says {man['version']}, the framework is {ver}"
out = os.path.join(ROOT, "out", "vibeupslides.plugin"); os.makedirs(os.path.dirname(out), exist_ok=True)
n = 0
with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as z:
    for top in (".claude-plugin", "skills", "README.md", "LICENSE"):
        p = os.path.join(ROOT, top)
        files = [p] if os.path.isfile(p) else [os.path.join(d, f) for d, dirs, fs in os.walk(p) for f in fs
                                                if "__pycache__" not in d and not f.endswith(".pyc") and f != ".DS_Store"]
        for f in sorted(files):
            z.write(f, os.path.relpath(f, ROOT)); n += 1
print(f"{out}: VibeUpSlides {ver}, {n} files, {os.path.getsize(out) / 2**20:.1f} MB")
