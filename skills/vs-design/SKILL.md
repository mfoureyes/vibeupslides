---
name: vs-design
description: "VS-Design, the VibeUpSlides skill for people without a brand: develops a look for presentations from nothing. Asks what the slides are for and for examples the user likes (slides, a web page, pictures), reads them, develops a look of the user's own from what they share and shows it next to two alternatives; without examples it offers six styles of its own to choose from (grid, magazine, night, workshop, poster, light). Then builds the first deck at once. The look grows with what the user corrects, with further examples and with the decks they build. Use when someone needs a good presentation quickly and has no corporate design, no website to take one from, or says they have no brand, no logo, no style yet; also for a personal talk, a club, a school project, a new venture before it has a design. German: kein Corporate Design, keine Marke, ohne Logo, Design von null, Look entwickeln, Stil aus Beispielen, Stil auswählen, schnell eine gute Präsentation, eigener Stil, Folien gestalten ohne Vorlage."
---

# VS-Design: a look from nothing

The fourth VibeUpSlides skill, for people who have no brand and need a good presentation soon.
**vs-build** reads a look from a website and documents; **vs-design** develops one from examples
the user likes and lets it grow; both end in the same thing, a library in `library/<name>/`, and
**vs-create** builds decks from it. If the user has a website or a corporate design of their own,
this is the wrong skill: hand over to vs-build.

**The way is: examples in, a look of their own out.** The six styles VibeUpSlides carries are the
fallback for a user who has nothing to show, and the alternatives a developed look is shown next
to. They are never the first answer when there are examples.

The user is in a hurry. From the first message to the first deck there is one message of
questions and one choice of theirs. Everything else is decided by you and said in a sentence, so
that they can object.

## Start

```bash
python3 SKILL_DIR/scripts/bootstrap.py
```

`SKILL_DIR` is the folder of this file. The script finds the workspace (`~/vibeupslides` unless
`VIBEUPSLIDES_HOME` says otherwise), sets it up if it is missing, prints the command, from then on
`python3 ~/vibeupslides/vs.py <command>`, written `vs` below, and runs `vs status`.

If the script is not at that path (the skill came as a plugin and its files live elsewhere), find it:
`find ~/.claude /mnt/skills -path '*vs-update/scripts/bootstrap.py' 2>/dev/null | head -1`.

**In Cowork**, or any session that does not run on the user's computer, read what the script prints:

- `NO WORKSPACE YET`: the session sees folders the user shared. Ask once in which of them VibeUpSlides
  should keep its brands and decks, then run the script again with `--home <that folder>/vibeupslides`.
- `TEMPORARY WORKSPACE`: the session runs in the cloud and sees no folder of the user as a path; the
  workspace is gone when the session ends. VibeUpSlides still runs here, in this session, where the
  browser for checks works; do not move it into a shell on the user's computer. What lasts is one
  file, `vibeupslides-workspace.zip`, the user's brands and decks:
  - **At the start**: if the user connected a folder of their computer (it is reached through
    file tools, not as a path), look there for `vibeupslides-workspace.zip`, copy it into this
    session and run `vs restore <file>`. An uploaded one is restored by the script itself. If
    there is neither and the user has worked with VibeUpSlides before, ask for the file.
  - **After a brand or a deck was made or changed** and the user is content: run `vs backup`, then
    put the file it writes into the connected folder, replacing the one there, together with what
    was built (`preview.html`, the deck's HTML, a PDF), so the user opens it on their computer with
    a double click. Without a connected folder hand the same files over in the chat, and suggest
    once to connect a folder ("add folder" in the plus menu) so nothing has to be uploaded again.
  - Say in one sentence, the first time, where their brands and decks are kept.

Either way the command is the one the script prints, with its path instead of `~/vibeupslides`, and
the Python environment is set up again in a new session (one to two minutes). Nothing can be opened
in the user's browser from there: hand them the built file (`preview.html`, the deck's HTML, a PDF)
the way the session shares files. `vs edit` and `vs present` serve an address only the session
itself reaches; for editing in the browser and for YouTube the user needs the Code tab or a
terminal on their own computer. Editing needs neither: the deck's own file carries it (vs-create describes it).
`vs doctor` reports what the session allows.

## 1. One message of questions

1. **What is the presentation for, and who sees it?** One or two sentences are enough (a pitch in
   front of a jury on Thursday, the annual meeting of the club, a talk at a conference).
2. **What should stand on it as the sender?** A name, their own or the project's. A logo file if
   they have one.
3. **Show me two or three things you like the look of.** Slides or a deck (PDF, PowerPoint, HTML),
   the address of a web page, a poster, a screenshot, a photo of something printed. They do not
   have to be presentations and they do not have to match each other. Say that "nothing at hand"
   is a complete answer: then they choose from styles in the next step.

Take the language from how they write to you, and add English unless they say no (vs-create
builds every deck in both from the start). Do not ask them to describe their taste in words:
examples say it better, and without examples the styles do.

## 2. With examples: develop the look

```bash
vs design --examine ~/Downloads/deck.pdf https://example.org ~/Desktop/poster.png
```

photographs what needs it (every slide of a deck, a web page screen by screen) and prints for each
example what can be measured: the ground, the colour of the type, the colour that marks, light or
dark, and the pictures to look at. **Look at every picture.** The measurement gives colours only;
the rest you read with your eyes, and you write it down, example by example, before you build:

| Read from the pictures | Becomes |
|---|---|
| the kind of typeface for titles and for text: serif, grotesque, condensed, rounded, mono; light or heavy; capitals or not | `--head`, `--body` (the nearest **open** typeface on Google Fonts), `--head-case`, `--head-weight` |
| how large titles are against the text, how tight the lines | type sizes and line heights in `theme.css` |
| corners: sharp, soft, round | `--radius` |
| rules and frames: none, hairlines, thick bars | `theme.css` (cards, figures, the label above titles) |
| what the accent colour is used for: one word, whole areas, thin marks | `--accent`, `--motif`, `theme.css` |
| how full a slide is, how much ground stays free | margins and sizes in `theme.css`; a note for vs-create in `design.md` |
| how pictures sit: bleeding to the edge, framed, round, tinted | the picture rules in `theme.css` |
| how a slide is arranged: where the title stands, which share the picture takes, what overlaps what (a person in front of the type, a picture breaking out of a band, a figure larger than the slide, circles running into each other), where the small text goes | masters of the look's own (see "Arrangements become masters" below) |
| whether things move, and how | `--motion` (the set that is closest) |

Then find **what the examples share**, not their average: if two of three are quiet and one is
loud, ask which side they are on. Ask one question that settles the look: "What I see in all
three: much white, heavy black titles, one strong colour used sparingly. Is that what you like
about them, or something else?" Their answer decides.

Build the look as theirs:

```bash
vs design nordlicht --style raster --name "Nordlicht" --ground "#F3EFE6" --ink "#161616" --accent "#0B6E4F" \
   --head "DM Serif Display" --body "DM Sans" --radius 8 --motion soft --langs de,en --author "First Last"
```

`--style` names the style that is nearest; the look leans on it only for what you do not say
yourself. From ground, type and accent the command mixes the whole set of colours and checks that
every one reads. Then open `library/<name>/theme.css` and write in what you read from the
pictures and no style carries: this file is where the look becomes their own, so do not leave it
as the style left it. Run `vs preview <name>` and look at the contact sheets next to the pictures
of the examples: someone who sees both should say they belong to the same taste, and nobody
should say one is a copy of the other.

### Arrangements become masters

Colours, type and `theme.css` change how the slides look; they do not change how a slide is
built. The default masters give every look the same structure: title top left, content below. When
the examples arrange their slides in ways of their own, the arrangement is often what the user
likes most, and a look that only recolours the defaults loses it. So read the arrangements too.

1. **Inventory.** Go through the example slides one by one and write down each arrangement in a
   sentence: what the slide does (opens, states one figure, asks for money, compares, tells a path,
   closes) and how it is built ("a narrow white column with title and text, the photo takes two
   thirds and carries one huge word, the person stands in front of the word"; "a blue band across
   the slide with one big sum, an upright photo breaks out of the band"). Leave out what is only
   a recoloured default.
2. **Decide per arrangement:** a default master changed in `theme.css` serves it, or it needs a
   master of its own. Write the masters of the look's own into `library/<name>/masters/`, usually
   six to ten, with low `order` numbers so that they lead the preview, and a `use` that tells
   vs-create when to prefer them over the defaults. The defaults stay as the reserve for
   everything the own forms do not cover.
3. **Free ways are allowed.** Text does not have to stand top left; a photo may take two thirds or
   bleed off two edges; a figure may be larger than anything else and run into a picture or a
   disc; a person may stand in front of the type (cut out with `cutout.py`, offered as an optional
   slot `cutout`, so the master also works without it); bands, rings and overlapping circles may
   carry content. Write them with the engine's tokens, so that they follow D (dark) and the
   accent, and mark planes that bleed on purpose with the class `image`, so that the overflow
   check leaves them out while the text in them is still checked.
4. **The same limits as every master** (vs-build's `references/masters.md`): text at least 24 px,
   contrast 4.5 to 1 (3 to 1 from 24 px), content ends at 930 px unless it is a picture, no text
   over a face, every text over a photo on a scrim that holds whatever photo comes later. Check
   each own master in light and in dark before you show it.
5. **Principle, not a copy.** Take the idea of an arrangement and build it with this look's own
   proportions, number of elements and wording; samples are new sentences, never the example's
   text, names or figures.

Record the inventory in `design.md`: arrangement in a sentence, the master it became.

**A look, not a copy.** Take what they like about an example (calm, much white, large figures, a
serif for titles), never the design of someone else as it stands: no logo, no name, no picture
and no exact layout of another company goes into the library, and a typeface that is not open is
replaced by the nearest open one. If the examples are all from one company and they want exactly
that, say that you make them a look in that spirit which is theirs.

**An example only as inspiration.** When the user says an example is only an inspiration and must
not be traceable, nothing of it goes into the library: no name, no file name, no source address,
no description that points back to it, in `design.md` neither. `vs design --examine` copies the
examples into `design/examples/`; delete that folder once you have read them.

Show it next to two alternatives, so that the choice is real:

```bash
vs design --gallery --with nordlicht --pick magazin,nacht --lang de
```

writes `design/styles.html`: their developed look first, then two of the styles (one bolder, one
quieter than what you made), all on the same six slides with their name on the cover. Give them
the file with one sentence on what you took from which example. They say what fits and what to
change; change it in the library (step 4) and show again.

## 3. Without examples: three styles to choose from

```bash
vs design --lang de
```

lists the six styles with what each is like and what it fits. Choose three for this user: the one
you would pick for what they told you, one that is clearly bolder, one that is clearly quieter.
Never three of a kind.

```bash
vs design --gallery --pick raster,nacht,plakat --name "Their name" --lang de
```

Give them the page and one sentence per style on why it could fit, your recommendation first.
They answer with a name and, often, a wish ("the dark one, but in our green"):

```bash
vs design nordlicht --style nacht --name "Nordlicht" --accent "#2FBF71" --langs de,en --author "First Last"
```

A user who chose a style and later shows an example is led back to step 2: the library stays,
the look moves towards the example.

## 4. Make it theirs, and write it down

The library now holds colours, open typefaces (embedded, no licence question), a stylesheet, the
master slides and `design.md`, the record of how this look came about. A logo file they gave you
goes in through `vs ingest nordlicht logo.svg` and `vs logo`; without one the name stands as
type, which is a clean solution and not a gap: do not draw a logo.

Carry out their wishes in the library, where they belong:

| They say | You change |
|---|---|
| another colour | `vs set <name> colors.accent=#…` (and `accent_text` if it must read as small type) |
| calmer, bolder, rounder, more air | `theme.css`: type sizes and weights, radius, rules, the motif |
| another typeface | `vs fonts google <name> "Family" --role head` (open typefaces only) |
| it should move more, less | `vs motion <name> --compare`, then `--set` |

Run `vs preview <name>`, look at the contact sheets yourself first (overflow and legibility must
be clean; a light accent colour as text and a dark ground are the usual faults), then give them
`preview.html`. It introduces itself. When they are content: `vs confirm <name>`.

**Write every decision into `design.md`**, one line each with its date and where it came from:
which examples were shown and what was taken from each ("2026-10-14: serif titles and the warm
ground from the magazine spread they showed; the heavy rules from their poster"), and every
correction after that ("titles one step bolder, too thin on the projector"). It is the memory of
this look: a later session reads it before it changes anything and does not ask again what was
decided once.

## 5. The first deck, at once

Do not stop at the library. Hand over to **vs-create** in the same conversation with what you
know already (what the deck is for, who sees it, the name): it asks what is still missing,
proposes the storyline and builds. The user came for a presentation, not for a design system.

## How the look grows

A look made in ten minutes is a start. It becomes a foundation through use, and three things feed
it. Each time, change the library, not the single deck, and note it in `design.md`.

- **Their corrections.** Whatever they say about a deck that is about the look and not about the
  content ("the cards are too tight", "I like the chapter slide") is a rule for all decks: change
  the master or `theme.css`, run `vs refresh --brand <name>` so that the decks they have follow.
- **Further examples.** Whenever they show something they like, later too: `vs design --examine`
  it, ask what exactly they like about it, and move the look towards that: a way of setting
  figures, a kind of diagram, the amount of white. A slide form they want as it is becomes a
  master (vs-build's `references/masters.md`, "A deck the user already has is the model").
- **The decks themselves.** A slide written freely that comes up again becomes a master
  (`FORMS:` in a build, `vs forms <name> --promote …`, see vs-create). After a few decks the
  library holds the forms this person actually uses.

When a look has grown far from its style, that is the point: `design.md` says how it got there.
If the user one day has a website or a corporate design, vs-build can read it into the same
library; say that the masters and decks stay and the colours, typefaces and logo are replaced.

## What this skill does not do

- It designs no logo and invents no brand name.
- It uses open typefaces only, so that every deck may be passed on.
- It does not copy the design of a company the user names ("make it look like …"): take what
  they like about it (calm, much white, large figures) into their own look.

## Commands

```
vs design --examine <files, addresses of web pages>     read examples: colours measured, pictures to look at
vs design <name> --style <nearest> --ground "#…" --ink "#…" --accent "#…" --head "…" --body "…" --radius N
                 [--motif none|wedge|block] [--motion <set>] [--head-case uppercase] [--head-weight N]
                 [--name "…"] [--langs de,en] [--author "…"]         a look of their own
vs design --gallery [--with <name>] [--pick a,b,c] [--name "…"] [--topic "…"] [--lang de]
vs design [--lang de]                                   the six styles (the fallback)
vs design <name> --style <style> [--accent "#hex"] …    a library from a style as it is
vs preview <name>        vs confirm <name>        vs set <name> key=value
vs fonts google <name> "Family" [--role body|head]
vs motion <name> --compare | --set <set>
vs ingest <name> <files>        vs forms <name>        vs refresh --brand <name>
```
