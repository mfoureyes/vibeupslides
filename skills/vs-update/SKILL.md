---
name: vs-update
description: "VS-Update, the updater of VibeUpSlides: checks whether the VibeUpSlides skill set and its framework are current, pulls new versions, brings the local workspace up to date and explains what is new and what it means for existing brand libraries and decks. Use when the user asks for an update, new features or the version of VibeUpSlides, when vs-create or vs-build reports that an update is available, or when something in VibeUpSlides behaves like an old version. German: Update, aktualisieren, neue Funktionen, Version."
---

# VS-Update: keeping VibeUpSlides current

One of four VibeUpSlides skills. **vs-build** makes the brand library (**vs-design** a look for people without a brand), **vs-create** creates
decks, **vs-update** updates both skills and the framework they share.

There are two things that can be old:

- the **skills** as installed for the agent (this folder and its siblings), updated from GitHub;
- the **framework** in the workspace (`~/vibeupslides/framework`), a copy of the one that ships in
  this skill's `framework/` folder.

Brand libraries and decks are never touched by an update. They live in `library/` and `decks/`.

## How to ask

**Every question goes through the question tool.** Whenever you ask the user something (a round
of questions, a choice, a yes or no), use the question tool the environment offers
(`AskUserQuestion` in Claude Code and Cowork): up to four questions per call, two to four short
options each, the recommended option first and marked "(Recommended)"; the user can always type
an answer of their own. Plain text only where there is no such tool, or for an answer nobody can
pick from options (a web address, a name, files to share): ask for that in one short line next to
the tool's questions. Never write a numbered list of questions into a message instead.

## 1. See where things stand

```bash
python3 SKILL_DIR/scripts/bootstrap.py
```

`SKILL_DIR` is the folder of this file. The script finds the workspace, prints the command (written
`python3 ~/vibeupslides/vs.py` below; in Cowork the workspace is the folder `vibeupslides` in a folder
the user shared, and the script prints that path) and runs `status`.
If the script is not at that path (the skill came as a plugin and its files live elsewhere), find it:
`find ~/.claude /mnt/skills -path '*vs-update/scripts/bootstrap.py' 2>/dev/null | head -1`.

It prints three versions: the workspace framework, the installed skills, and the published release
(asked from GitHub at most once a day; "unknown" when offline). Tell the user in one sentence
which of the three differ.

## 2. Update the skills

Only if the published version is newer than the installed skills. This changes installed skills,
so say what you are about to do, then run:

```bash
npx skills update
```

If that does not bring the new version (older installer, or the set was installed from a folder),
install the set again over the old one:

```bash
npx skills add mfoureyes/vibeupslides
```

A set installed from a local folder is updated by installing from that folder again.

Installed as a plugin (Cowork), the skills are updated where plugins are managed: tell the user to
update or reinstall the VibeUpSlides plugin there. The next run of the script above then makes the
workspace take the new framework over.

## 3. Update the workspace

```bash
python3 ~/vibeupslides/vs.py update
```

It replaces `framework/` with the one from the installed skills, prints the changelog entries
since the old version, and lists for each brand which new default masters exist that the brand
does not have its own version of yet. vs-create does this step by itself before a build when it
finds the installed skills newer than the workspace.

## 4. Tell the user what changed

From the changelog, in plain words and in their language: what is new, what they can now ask for,
and whether anything needs doing:

- **New default masters**: usable in decks at once in the framework's neutral look. Offer to give
  the brand its own version through vs-build.
- **New engine features** (keys, export, presenter view): existing decks get them at their next
  build; a deck that was already delivered as HTML keeps its old engine until it is rebuilt.
- **Changes to the library format**: the changelog says if a brand needs a step; do it with
  vs-build and rebuild the preview (`vs.py preview <brand>`).
- **Skills that were renamed** (0.5.0: vs-style became vs-build, the former vs-build became
  vs-create): an installation from before still holds a folder `vs-style`, and its `vs-build` is
  the old deck builder. Install the set again (`npx skills add mfoureyes/vibeupslides`) and remove the
  leftover `vs-style` folder from the skills directory, with the user's consent.

Then rebuild one preview or deck to confirm the update works, and say that it does. End with one
thing they can try now that is new, as a sentence they can say ("Try: …").

## Rules

- Never edit files in `framework/` by hand, in the workspace or in this skill: the next update
  overwrites them. A fix belongs in the VibeUpSlides project.
- Do not delete or move anything in `library/` or `decks/` as part of an update.
- If an update fails halfway, the workspace keeps its old `framework/`; run `vs.py update` again
  after fixing the cause, and report what happened.
