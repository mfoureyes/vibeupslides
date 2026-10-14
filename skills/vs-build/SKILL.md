---
name: vs-build
description: "VS-Build, the onboarding of VibeUpSlides: builds a company's brand library for presentations, once. Reads the website and existing documents (style guide PDF, PowerPoint master, logos, fonts, sample texts), analyses colours, typefaces, logo, imagery, icons, arrows, graphic elements and how the company writes, and writes a style guide, a voice profile with checkable rules, a brand stylesheet and the brand's own master slides into one local folder. Use when a user wants presentations in their company's look, names a website to take the design from, has no brand library yet, or wants to change or re-read one (new logo, fonts, master slide, wording rules, relaunch). Also: brand analysis, corporate design for slides, tone of voice, onboarding. German: Styleguide, Markenanalyse, Masterfolien, Corporate Design, Marke einlesen, Marke aufbauen, Sprachprofil, Tonalität, Unternehmenssprache."
---

# VS-Build: from a website to a brand library

One of four VibeUpSlides skills. **vs-build** builds the library a brand's decks stand on, its
design and its language, from a website and documents; **vs-design** makes a look for people who
have no brand; **vs-create** creates decks from either, **vs-update** keeps the framework current.
A user without a website or a corporate design of their own belongs to vs-design: hand over.

People install VibeUpSlides because they want decks that look like their own company. This skill is
that onboarding. Its result is a library folder that carries the whole look and feel and the way
the company writes, so that later decks are assembled from the brand's master slides in seconds
instead of being designed anew, and read like the company wrote them.

## The one command

Everything runs through one command. Find it first:

```bash
python3 SKILL_DIR/scripts/bootstrap.py
```

`SKILL_DIR` is the folder of this file. The script sets up the workspace on first use (one local
folder, `~/vibeupslides` unless `VIBEUPSLIDES_HOME` says otherwise, with its own Python environment) and
prints the command, from then on always:

```bash
python3 ~/vibeupslides/vs.py <command>
```

Written `vs` below. On first setup in Claude Code, offer the user once to allow this command and the workspace
folder permanently (the setup prints the rules; `vs permissions` prints them again), so they are
not asked at every step. Add them to the user's settings only if they say yes.

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
terminal on their own computer. Editing needs neither: every built deck carries its own.
`vs doctor` reports what the session allows.

```
~/vibeupslides/
  framework/            the engine, replaced by updates, never edited
  library/<brand>/      brand.json  styleguide.md  voice.md  theme.css  motion.css  masters/  voice/  elements/  fonts/  logos/  images/  sources/  raw/  preview.html
  decks/<deck>/         deck.json, images/, the built HTML
```

## The onboarding in six steps

Do them in order. Steps 1, 4 and 6 talk to the user, the others are your work.

### Lead the user through it

The user should always know where they are and what is asked of them. Open with the route in four
or five short lines, in their language, for example: "1. You tell me what the slides are for and
give me what you have. 2. I read your website and build the look. 3. You choose how the slides
move. 4. You check the master slides and how the texts sound.
5. We note the facts every deck needs, and you confirm." From then on begin every message that
asks something with where they are ("Step 3 of 5: motion"), ask one thing or one bundle at a
time, say what you are doing while they wait, and never let a step pass in silence: what you
decided for them, you name in one sentence so they can object.

The user's own decisions, each with something to look at, never from a description alone:

| What | They look at | You record |
|---|---|---|
| the look | `preview.html` | their corrections, then `vs confirm` |
| the motion | `preview/motion/compare.html`: the copy of their website (`site`) next to the VibeUpSlides sets | `vs motion <brand> --set <name>` |
| the voice | the description, the rules, three before-and-after pairs | `voice.md`, the rules |
| the basics | the list of facts and shared slides you propose | `vs shared <brand> fact …`, shared slides |

### 1. Ask what the slides are for, then for the material, then read it in one run each

Ask in **one** message, in this order, and skip what the request already answers:

1. **What for.** Why do they want these slides, and for whom: their own company's presentations,
   a pitch or proposal to a customer in that customer's look, talks, workshops. This is the first
   question, and it is an open one. Do not open with a question about permission: the purpose says
   whose brand it is. The answer is used throughout: it decides which masters matter, and later
   how decks are written (a sales deck mirrors the customer's own words and goes into their
   problem, it does not recite the sender's corporate identity). Record it word for word in
   `brand.json` (`vs set example 'purpose="..."'`) and in the style guide.
2. **Folder name.** Propose one; they confirm with a word.
3. **Languages.** In which language or languages they present. Set them right after the analysis
   (`vs set example langs=de,en`, the first is the start language).
4. **Typefaces.** Do they have the brand's font files and a licence that allows embedding them in
   documents? If yes, they name the files. If not, say now that you will take an open typeface that
   is close in character, and do that after the analysis without asking again (step 4).
5. **Documents.** A style guide or brand manual as PDF, logo files, and above all **the best
   presentation they already have** (PowerPoint, PDF or an HTML presentation: its slides are
   photographed one by one). Ask for it by name: "Which of your presentations are you happy with?" A
   good deck of their own is the model for the masters, ahead of the website: what it does well is
   taken over as it is, never rebuilt roughly.
6. **Texts.** Two or three texts they consider typical of how the company writes (a newsletter, a
   text about the company, a customer letter): the voice profile is built from them.
7. **Their name.** The last slide of every deck credits the person who made it ("Made by …, with a
   little help from VibeUpSlides by vibeup.berlin"). Record it as the brand's default
   (`vs set example 'author="First Last"'`); a deck made by someone else names its own `author`.

Say that "website only" is a complete answer to 5 and 6. Documents often define what a website
does not show (slide types, grids, chart styles, logo and imagery rules, tone of voice). Read them
first:

```bash
vs ingest example ~/Downloads/styleguide.pdf ~/Downloads/master.pptx
```

`references/documents.md` explains what this produces and how to weigh a document against the
website when they disagree. Sample texts as `.txt` or `.md` go in with `vs voice example <files>`
(after the website is read; other formats through `vs ingest`). Then the website:

```bash
vs analyze https://example.com --brand example
```

One run, about a minute. It declines cookie banners, reads a few pages and writes the library:
a draft `brand.json`, logo candidates, typefaces sorted by licence situation, photos, the site's
icons, arrows and shapes as SVG, measurements of its buttons, cards, labels, images and sections,
its copy, screenshots, the site's own video files where they can be saved (`videos/`), a copy of
the default master slides as starting points, a measurement of how the site writes with a drafted
voice profile (`voice.md`, rules in `brand.json`), and a first preview.
If the site cannot be read (login, bot protection), do not work around it: ask the user for a style
guide, screenshots or brand files and fill the library by hand.

### 2. Look before you write

Open these as images, in this order, and form a picture of the brand before changing anything:

| File in `library/<brand>/` | What it tells you |
|---|---|
| `sources/SOURCES.md`, then the sheets it points to | what the user's own documents define, if any were read |
| `raw/screens/home.png`, `home_full.png` | the overall feeling, density, how colour and shape are used |
| `raw/screens/components/*.png` | hero, buttons, cards, labels, image treatment up close |
| `raw/logo_candidates.png` | which file is the real logo, and whether a light version exists |
| `raw/elements.png` | the icons, arrows and shapes that were saved: the brand's element library (`vs elements <brand>` lists it) |
| `preview/sheet_en_*.png` | what the default masters look like with only colours and type applied |

Then read `raw/components.json` (measured styles) and `raw/copy.md` (the site's words), and run
`vs voice <brand>` for the measurement of the language: address, sentence length, frequent words,
candidates for fixed terms, per language.

### 3. Correct the tokens

Fix what the heuristics got wrong in `brand.json` with `vs set <brand> key=value` (or edit the file):
accent and deep colour, the logo choice (`vs logo trim`, `vs logo inverse` for a white version),
corner radius, accent shape (`shape.motif`: `wedge`, `block` or `none`), heading case and weights.
`references/library.md` explains every field and how to judge it.

### 4. Clarify the typefaces and the open design questions with the user

The website cannot tell you how this company wants to present. Before you build the library, ask
once, in one message, with your own reading as the suggested answer to each point so the user can
reply with a few words:

- **Use**: only what step 1 left open: which decks will be built most, and are they mostly
  presented live or sent to be read.
- **Base**: light or dark slides as the default, and how much of the accent colour (a detail, or
  whole coloured slides). Say what the website does and what you would do.
- **Imagery**: do they have own photos to use, which of the photos found on the site may be used,
  which subjects or styles to avoid.
- **Graphic elements**: name the shapes, icons and arrows you found and how you plan to use them;
  ask whether one of them is the brand's signature and whether anything must not be used.
- **Languages**: asked in step 1; set in `brand.json`, the masters' samples are written in each of
  them and every new deck starts with them. Ask here only if it is still open.
- **Voice**: how the audience is addressed in each language, words and names that are fixed, words
  the company does not use, and, if none came in step 1, two or three texts that show how it writes.
- **Motion**: how lively the slides may be (hardly any, calm, clearly animated). The choice between
  the sets follows in step 5 with a page to look at.
- **Must-haves and no-gos**: slides they need that a default deck lacks, and things earlier decks
  got wrong.

Do not ask what the website or the documents already answer. Record the answers in `styleguide.md`.
The typefaces belong in the same message:

```bash
vs fonts example
```

lists every typeface with its status. Decks only embed what is clearly allowed:

| Status | Meaning | What to do |
|---|---|---|
| embedded | open licence (Google Fonts and the like), files saved | nothing |
| pending | the site serves the files itself, licence unknown; files wait in `fonts/pending/` | **ask the user** whether their licence covers embedding in documents. Yes: `vs fonts accept example` |
| missing | identified, but served by a font service (Adobe Fonts, Monotype ...) or not downloadable | **ask the user** whether they have the font files and a licence that allows embedding. They put the files into `library/<brand>/fonts/inbox/`, then `vs fonts add example` |
| system | no web font | nothing |

The user answered in step 1 whether they have the files. If they do, take them in
(`vs fonts add`), and ask only about files the site itself serves (pending). If they do not, do
not ask again: choose an open typeface that is close in character for every typeface that is
missing or pending, set it as stand-in, and tell them in one sentence which one stands in for
which and that the real files can be supplied at any time:

```bash
vs fonts google example "Inter" --role body
```

The user can supply the real files at any later time; `vs fonts add` swaps them in and every deck
built afterwards uses them.

### 5. Build the library: style guide, theme, motion, master slides

Where the user gave you a presentation they are happy with, that deck is the model: every slide
form it has becomes a master that matches it (`references/masters.md`, "A deck the user already
has is the model"). Otherwise work from the website, not from the default masters: take an inventory of the site's own patterns
(how it shows pictures, its grids, its list rows, its figures) and give each one a place in the
library, with its movement (an animation of the site that works as a transition or an entrance
becomes the deck's own, in the brand's motion set); leave
out what only a visitor can operate; keep the main subject of every picture in the middle of its
frame and text off faces.
`references/masters.md`, "Start from the website, not from the defaults", is the method, read it
before the first master.

This is the heart of the skill. The default masters are examples, not the result. The brand's
slides must look and read like its website. Read `references/library.md` for the method and
`references/masters.md` for the template format and the markup, then write these:

- **`styleguide.md`**: fill every section of the draft from what you saw and measured: essence,
  colour use, type, layout and shape, imagery and image treatment, icons and arrows, graphic
  elements, components and motion. No `TODO` may remain. Nothing is invented: what the site does
  not show is recorded as "not defined on the site".
- **`voice.md` and the voice rules**: how the company writes. The profile is what vs-create writes
  every slide from: address and perspective, tone with evidence, sentences, the brand's words and
  the ones it avoids, fixed terms, ten real sentences, before-and-after pairs, rules for slide
  text. The rules in `brand.json` under `voice` (address, sentence length, fixed terms, words to
  avoid) are what every build checks slide by slide. `references/voice.md` has the method.
- **`theme.css`**: the brand's stylesheet on top of the engine. It carries everything beyond
  colour and type: how the label above a title looks, cards, chips and buttons, how images are
  cropped, rounded, tinted or framed, the bullet and arrow style, rules, patterns and the accent
  shape. Built with the tokens, using the saved elements (`url(el:arrows/arrow.svg)`).
- **The element library**: the icons, arrows and shapes the analysis saved in `elements/` are what
  slides are decorated with. Go through them (`vs elements example`, `raw/elements.png`): delete
  what is not the brand's, rename every icon so its file says what it shows
  (`icon_03_energy.svg`), and list the names with their meaning in the style guide. Decks then set
  them by name on cards, columns and steps, and your masters use them (`{{>icon energy}}`,
  `url(el:arrows/...)`). Give the masters' samples real icons where the brand has some.
  The analysis also reads icons the site keeps in an svg sprite (`from_sprite` in
  `raw/components.json`), often more than a hundred. A note about an icon font says only that
  those glyphs are not saved; never tell the user the brand has no icons while the website shows
  some: look at `raw/elements.png` and the screenshots first.
- **Motion**: how the brand moves. The analysis measured the website's own motion
  (`raw/motion.json`) and drafted a profile. Compare the motion sets as film strips
  (`vs motion example --strip all`), choose the one whose idea of movement fits the brand's
  character, set its tokens from the measured timing, and write a `motion.css` only if the brand
  has a signature move of its own. `references/motion.md` has the method. Motion that came with the
  framework is never the default answer; a quiet brand gets quiet motion.
  The analysis also copies the way the website's own elements arrive into a set that belongs to
  this brand, `site` (`motion/site.css` in the library; `vs motion example` says what it does and
  whether it rests on elements watched while scrolling or only on the site's entrance animations).
  Look at its film strip (`vs motion example --strip site`) like at any other set and correct the
  file where a frame looks wrong. **Choosing the motion is a step of its own, and it is the
  user's:** `vs motion example --compare` writes `preview/motion/compare.html`, one file on which
  the copy of the website and the framework's sets play the same slides of this brand side by
  side. Give it to the user and ask one question: the motion of your website (`site`), or one of
  the VibeUpSlides sets, of which you name the one or two that fit the brand best and why. Set what
  they choose (`vs motion example --set <name>`). If the website shows nothing that could be
  copied, say so and offer the framework's sets alone.
- **Video**: if the site runs a film behind its hero, it is in `videos/` and marked `background`
  in `brand.json`. Put it behind the chapter slide or a photo slide of this brand (slot `video`,
  sample `"video": "@video"`) when the site does the same, and say so in the style guide. A film
  that is content belongs on a `video` slide, where it is shown whole. `vs videos example` reads
  the videos again.
- **`masters/`**: the brand's own master slides. Rework the copied defaults so that composition,
  proportions and details follow the website, and add masters for things this brand needs and the
  defaults lack (a hero in the site's manner, a slide for its typical card, its way of showing
  numbers or steps). Every master keeps its header with slots and a sample in the brand's voice,
  written from the real sentences of the voice profile, so the preview already sounds like the
  company. The preview reports samples that break a voice rule (`VOICE master ...`); fix them.

Rebuild and look after every round, it takes a few seconds:

```bash
vs preview example
```

Compare the contact sheets with the website screenshots side by side. Keep going until a stranger
would say both come from the same company. Then check the hard cases yourself: logo on dark and on
accent, a light accent colour as text, long titles, the photo masters with the brand's own photos.

### 5b. The basics

**The basics every deck needs.** Facts and slides that return in many decks are kept once, so
that all decks can be brought up to date at once. Propose them from what the website and the
documents say, and let the user correct the list: the address, contact details, founding year,
number of people, the two or three key figures, the claim, as facts
(`vs shared example fact address "…"`, per language with `--lang`); the team, the contact slide,
"about us", references, as shared slides once a first deck has them
(`vs shared example slide team --from <deck> --slide 7`). Say what this is for in one sentence:
when something changes, it is changed here, and every presentation follows.

### 6. Show the user and get the confirmation

Give the user `library/<brand>/preview.html` (send the file if they follow from another device) and
say how to look at it: arrow keys change slides, the animation plays on every change, R plays it
again. The file introduces itself: its first three slides say what it is, which keys there are and
what comes next, and a line above every master slide says what that master is for. The master
slides start at slide 4; when the user names a slide by its number, it is the number the file
shows. If the user has not chosen the motion yet, give them `preview/motion/compare.html` as well
and put the choice to them: like the website, or which VibeUpSlides set. Ask in
one message: do the colours and the logo fit, are the typefaces right, do the slides feel like the
website, does the motion fit, is anything missing. Ask about the voice with something to react to:
the one-paragraph description, the rules, and three before-and-after pairs from `voice.md`; is this
how they write, is the address right in every language, which words are missing from the avoid
list. Apply the answers, rebuild, then:

```bash
vs confirm example
```

The library is now the base for every deck. Say so, and that decks are created with vs-create.

## Changing a library later

The same skill, entered at the right step: a new logo or colour (step 3), fonts supplied later
(step 4), a new master slide or a changed look (step 5), new texts or wording rules (`vs voice
<brand> <files>`, then revise `voice.md` and the rules), a relaunch of the website
(`vs analyze <url> --brand <name> --again` redrafts `brand.json` and the raw data and leaves the
style guide, voice profile, theme and masters in place for you to revise), **a further language**
(`vs langs --brand <name> --add fr`: nothing is rebuilt, the masters stay, their sample texts fall
back until you add the language to the samples that matter; write the voice rules for it; a deck
gets it with `vs langs <deck> --add fr`, which lists every text to translate). Always finish with `vs preview` and
tell the user what changed.

## Rules

- **Whose brand.** The purpose from step 1 says whose brand it is and what the decks are for. A
  brand of another organisation is built for decks addressed to it or made for it (a pitch, a
  proposal, commissioned work); a deck in its look is never presented as coming from that
  organisation unless it does.
- **Typefaces are licensed.** Never activate pending files or point to download sites on your own
  judgement; the user confirms.
- **Other people's material.** Logos of customers or partners and photos of people that the site
  shows are saved for analysis; they go onto slides only when the user says they may.
- **Nothing is drawn by hand.** An icon, an arrow or a shape the website does not show is left out
  or supplied by the user as a file. Do not approximate the brand's graphics with a shape of your
  own, however close: it is not theirs, and it shows.
- **Tokens, not hex values** in `theme.css` and masters, so a colour change in `brand.json` reaches
  every slide.
- **The framework folder is never edited.** Brand-specific things live in the library; a wish that
  needs an engine change is a request for the VibeUpSlides project.
- **Work economically.** Never read `preview.html` or image files as text. Look at contact sheets
  and component screenshots; open single slides only when a detail is in doubt.

## References

| File | Read it when |
|---|---|
| `references/library.md` | steps 3 and 5: judging the analysis, the fields of `brand.json`, writing the style guide and `theme.css` |
| `references/voice.md` | steps 2, 5 and 6: measuring how the company writes, writing `voice.md`, setting the rules a build checks |
| `references/masters.md` | step 5: the master template format, slots, helpers, and the markup and classes of the engine |
| `references/documents.md` | step 1 and 2: reading style guides and slide masters the user has, and weighing them against the website |
| `references/motion.md` | step 5: choosing how the brand moves, from the website's own motion and the brand's character |
