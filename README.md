# VibeUpSlides

A set of four agent skills for Claude that make presentations look like your company, or like you
if you have no company look yet.

## Install

**Claude Code and other agents** (as skills):

```bash
npx skills add mfoureyes/vibeupslides
```

**Claude Code** (as a plugin):

```text
/plugin marketplace add mfoureyes/vibeupslides
/plugin install vibeupslides@vibeupslides
```

**Cowork**: either add the GitHub repository `mfoureyes/vibeupslides` as a plugin marketplace in
Cowork's plugin settings and install `vibeupslides` from it, or download
[`vibeupslides.plugin`](https://github.com/mfoureyes/vibeupslides/releases/latest/download/vibeupslides.plugin)
from the latest release, add it to a chat and ask Claude to install it; Cowork then offers to save
the plugin.

Updates: the skills check once a day whether a newer version is published and tell you; say
"update VibeUpSlides" to get it.

## The four skills

| Skill | When | What it does |
|---|---|---|
| **vs-build** | once per brand | Reads your website, your documents and a few of your texts and builds a brand library: style guide, brand stylesheet, your own master slides, icons, arrows, graphic elements, photo style, typefaces, and a voice profile of how your company writes |
| **vs-design** | when you have no brand | Develops a look of your own from examples you like (slides, a web page, pictures), or lets you choose one of eight styles, shows the options side by side on the same slides and lets the look grow with what you correct and show |
| **vs-create** | for every deck | Asks what the deck is for and how it should look, helps with the content, writes it in your company's voice and builds it from the library in seconds |
| **vs-update** | when there is something new | Updates the skills and the framework and tells you what changed |

Then say something like:

> Take our design from https://example.com and set up our slides.

and later:

> Build a ten-minute pitch deck for Thursday.

## How it works

**A framework, not a page generator.** Decks are not written as web pages. A deck is a short
content file that names master slides and fills their slots; the framework renders it, embeds
fonts, logos and images, checks every slide for overflow and makes contact sheets. A build takes a
few seconds. New markup is written only when a deck needs a look the library does not have, and
then it becomes a master slide.

**A library per brand.** The onboarding analyses the website in one run: colours by area,
typefaces with their licence situation, logo candidates, photos and how they are treated, the
site's icons, arrows and shapes as SVG, its buttons, cards, labels and sections, and its copy. From
that the agent writes a style guide, a stylesheet and master slides that belong to this brand. You
look at the preview and say what is off.

**Your words, not only your colours.** The onboarding also measures how the company writes (how
readers are addressed, sentence length, its own terms) and records it as a voice profile with real
sentences and before-and-after pairs. Every deck is written from it, and every build checks each
slide against the brand's rules: the address, sentence length, fixed terms, words you do not use.

**Editable like a slide program.** `vs.py edit <deck>` opens a deck in the browser: click a text and
type, reorder and duplicate list items and slides, undo. Every change is written back into the deck's
content file, so both languages, the reading version and the PDF stay in step, and the agent
continues from what you wrote.

**Editable without a server, too.** Every presentation carries its own editing: open the file with
a double click, press the pencil, type into the slides, move, copy and delete slides and list
items, insert a new slide from one of your masters. In Chrome and Edge you name the folder of your
presentations once, and from then on every change is saved in the presentation file itself. The
agent then takes your changes over, corrects and translates what you typed and builds the deck
again.

**Every text can be read.** Each build measures every text on every slide: type that is too small,
too little contrast to what is behind it (photos included), text cut off, at the edge or on top of
other text is named by slide, and a deck with such a finding is not finished.

**Motion from your website.** The analysis copies the way your site's elements arrive into a
motion set of your own. You compare it side by side with the built-in sets and choose.

**What your decks share.** A team slide, the address, a key figure live once in the brand library.
Decks name them instead of copying them, and after a change `vs.py refresh` brings every deck up
to date.

**A library that grows.** When a slide written by hand comes up again, or a block inside slides
(a band with the conclusion, a contact box), the agent makes it a master or a part of the brand,
so that every deck uses the same one and a change reaches all of them.

**Click steps as you explain.** Parts of a slide appear click by click in reading order; the deck
or the editing panel can put them in another order or join them into one step.

**One local folder.**

```
~/vibeupslides/
  framework/            the engine, replaced by updates
  library/<brand>/      brand.json  styleguide.md  voice.md  theme.css  masters/  motion/  shared/  elements/  fonts/  logos/  images/
  decks/<deck>/         deck.json  sources/  research/  images/  the built HTML
```

In Cowork the session runs in the cloud: brands and decks are kept as one file,
`vibeupslides-workspace.zip`, in the folder you connect, next to the decks that were built.

**One command.** Everything the skills do runs through `python3 ~/vibeupslides/vs.py`, so you can
allow it once instead of confirming every step. The first run creates the folder with its own
Python environment (Pillow, Playwright, Chromium).

## What a deck can do

One self-contained HTML file that runs offline in any browser:

- **Presenter view** (M): current and next slide, speaker notes, clock, elapsed time
- **Timer slides** and **quiz slides**, run from the slide or from the presenter view
- **Motion**: eight motion sets and one copied from your website; counters, growing bars, line charts
- **Video** and embedded players; a **reading version** of the same deck
- **PDF export** inside the deck (P), searchable; vector PDFs and handouts from the build
- **Video export** of single slides as MP4
- **One or two languages** in one file (L)
- Outline, overview, deep links, swipe on tablets

## Typefaces

Decks only embed fonts that are clearly allowed. Open typefaces (Google Fonts and the like) are
used at once. Files a site serves itself wait until you confirm your licence covers embedding.
Typefaces from font services are named, and you supply the files if you have them; until then an
open stand-in is used and marked as one.

## Without an agent

```bash
python3 skills/vs-update/framework/vs.py init
```

```bash
python3 ~/vibeupslides/vs.py analyze https://example.com --brand example
```

```bash
python3 ~/vibeupslides/vs.py new kickoff --brand example
```

```bash
python3 ~/vibeupslides/vs.py build kickoff
```

`vs.py help` lists all commands. The deck file is described in
[deck-format.md](skills/vs-create/references/deck-format.md), master slides in
[masters.md](skills/vs-build/references/masters.md).

## Test

```bash
python3 tests/smoke.py
```

Sets up a temporary workspace, builds a library preview and a deck in two languages and drives the
deck in headless Chromium: paging, click steps, language switch, timer, quiz, PDF export,
presenter view, and the update path.

## A word on rights

Read brands you are allowed to use: your own organisation's, or a client's who asked you to.
Typefaces stay under their foundry's licence. Use other organisations' logos and photos of people
only with consent.

## Licence

MIT, see [LICENSE](LICENSE). Decks embed [jsPDF](https://github.com/parallax/jsPDF) and
[modern-screenshot](https://github.com/qq15725/modern-screenshot), both MIT
([notices](skills/vs-update/framework/js/LICENSES.txt)).
