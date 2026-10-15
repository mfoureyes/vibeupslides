---
name: vs-create
description: "VS-Create, the everyday skill of VibeUpSlides: creates presentations from a brand library made with vs-build. Asks what the deck is for, helps develop the content on researched structures (pitch, keynote, company, sales, proposal, consulting, conference talk, workshop), writes every text in the company's voice, builds the deck in seconds as HTML from the brand's master slides and opens it for editing in the browser. Presenter view with notes, video, timer and quiz slides, PDF export, one or two languages, a reading and a live version. Use for: presentation, slide deck, slides, pitch deck, keynote, workshop slides, investor pitch, sales deck, speaker notes, handout, change a slide, edit slides myself, add slides, translate a deck, convert a PowerPoint. German: Präsentation, Foliensatz, Folien, Pitch-Deck, Vortrag, Workshop-Folien, Folie ändern, Folien selbst bearbeiten, Text ändern."
---

# VS-Create: decks from the brand library

One of four VibeUpSlides skills and the one for every day. **vs-build** made the brand library
(or **vs-design**, for people without a brand), **vs-create** creates decks from it, **vs-update**
keeps the framework current.

A deck is a content file, not a web page. You write `deck.json`: which master slide, which text in
which slot. The framework renders it through the brand's master slides, checks every slide and
makes contact sheets, in a few seconds. New HTML is written only when a deck needs a look the
library does not have yet, and then it becomes a master so it is there next time.

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
    put the file it writes into the connected folder, replacing the one there. Then run
    `vs handover <deck>` (for a brand `vs handover --brand <name>`) and copy the folder it writes
    into the connected folder as it is, with all its subfolders: the presentation, `README.md`,
    `research/`, `sources/`, `images/`, `assets/` (a brand: preview, motion comparison, style guide,
    voice). No single files loose in the folder: one folder per deck and per brand, next to the
    backup file. Without a connected folder hand the presentation over in the chat, and suggest
    once to connect a folder ("add folder" in the plus menu) so nothing has to be uploaded again.
  - Say in one sentence, the first time, where their brands and decks are kept.

Either way the command is the one the script prints, with its path instead of `~/vibeupslides`, and
the Python environment is set up again in a new session (one to two minutes). Nothing can be opened
in the user's browser from there: hand them the built file (`preview.html`, the deck's HTML, a PDF)
the way the session shares files. `vs edit` and `vs present` serve an address only the session
itself reaches; for editing in the browser and for YouTube the user needs the Code tab or a
terminal on their own computer. Editing needs neither: the deck's own file carries it (see "The
user edits the deck themselves").
`vs doctor` reports what the session allows.

`status` shows versions, brands and decks. Act on it:

- **`UPDATE AVAILABLE` or "the skills are newer"**: tell the user in one sentence what is waiting
  and that vs-update brings it. Do not interrupt a deck for it unless they want to; a build takes
  over a newer installed framework by itself and says so.
- **No brand, or the brand is "not yet confirmed"**: the library comes first. Ask one thing: is
  there a website or a corporate design to take the look from? Yes: hand over to vs-build. No, or
  they just need a good presentation soon: hand over to vs-design, which develops a look from
  examples they like (or lets them choose a style) and comes back here within minutes. A deck built on an unconfirmed library will have to be redone.
- **Several brands**: ask which one, unless the request makes it obvious.
- **The deck exists** (the user wants to change or continue one): read its `deck.json`, its `brief`
  is already answered, go to step 4.

## How to ask

**Every question goes through the question tool.** Whenever you ask the user something (a round
of questions, a choice, a yes or no), use the question tool the environment offers
(`AskUserQuestion` in Claude Code and Cowork): up to four questions per call, two to four short
options each, the recommended option first and marked "(Recommended)"; the user can always type
an answer of their own. Plain text only where there is no such tool, or for an answer nobody can
pick from options (a web address, a name, files to share): ask for that in one short line next to
the tool's questions. Never write a numbered list of questions into a message instead.

## 1. Read the library

Read `library/<brand>/styleguide.md` and `library/<brand>/voice.md` fully, note the `purpose` the
user gave when the brand was built (`brand.json`, style guide), and list the masters:

```bash
vs masters <brand>
```

Both are binding. The style guide decides which pictures fit and which master suits which content.
The voice profile decides how every title and sentence is written: its real sentences and its
before-and-after pairs are the model, and its rules in `brand.json` are checked by every build.
A brand without `voice.md` (a library made before 0.5.0) still has its voice in the style guide;
say that vs-build can give it a profile, and write from what is there.

## 2. Ask what the deck is for and how it should look

Before any storyline, ask in **one round** of the question tool (see "How to ask"). Skip what
the request already answers.

1. **Purpose and kind of deck.** What is the deck meant to achieve, and which kind is it: investor
   pitch, keynote, conference talk, company presentation, sales deck, proposal, strategy or
   consulting deck, workshop. `references/structures.md` has a researched structure for each and
   the questions that belong to it (for a keynote: the one idea in one or two sentences; for a
   proposal: is there a brief whose order must be followed). Read the section for the kind at hand
   before you ask, and ask its questions in the same round.
2. **Presented or read.** Every deck has a main mode: `live` (a person presents, the slide
   supports) or `reading` (it is sent and must work without a speaker). Ask which one this deck is
   first. The other version can be built later from the same file; offer it, do not build it unasked.
3. **Who presents, to whom, how long.** The user live, someone else, or nobody (it is read); who is
   in the room; the length of the slot.
4. **Look.** Within the brand: calm or bold, text-led or image-led, mostly light or mostly dark
   slides, how much motion (off, calm, standard, expressive), and whether a video has a place.
   Offer what the library makes possible.
5. **Language.** One, or two in one deck with a switch.

**Whose words.** Refer to the purpose recorded with the brand. A deck that is meant to win someone
(sales deck, proposal, pitch) is written from the audience's side: ask how the customer describes
their problem, in their own words (a brief, an e-mail, their website), use those words, and spend
the first slides on their situation before anything about the sender. The brand's voice decides
how the sender sounds, not what the deck is about.

Then choose the features from the structure for this kind of deck and the answers: how much
motion, timers and quizzes (workshops; a question or two in a long talk), video, notes
(full for live decks, none needed in a reading deck, where `read` texts carry the content).
When the content suggests otherwise the content wins, and you say why in a sentence.

Tell the user in two or three sentences what the deck gets and why. They confirm or strike.

## 3. Propose the storyline

Work the way `references/structures.md` describes: the answer in one sentence, three to five
supporting blocks, then only the titles. Write the slide sequence into the chat: one line per slide
with its title as a full sentence and the master it uses, following the structure for this kind of
deck; where the sources disagree on the order, offer the variants and let the user choose. The
titles read in a row must give the argument. Wait for the confirmation. For long decks go block by
block. Once the deck file exists, `vs titles <deck>` prints the titles in order for this check.

If a slide needs a look no master has, say so here and choose: `free` (title plus your own body,
for a one-off), or a new master through vs-build (when the look will be needed again).

## 4. Write the deck file

```bash
vs new kickoff --brand example          # the brand's languages plus English; --langs de,en names them yourself
```

creates the deck's folder. Every deck has the same parts, and you keep them in order, because a
later deck is made from what this one rests on:

```
decks/kickoff/
  deck.json        the deck
  sources/         what the user supplied for it: documents, earlier slides, figures, briefs, e-mails. Save what they give you here, under a name that says what it is.
  research/        report.md: the research report (see below); outline.md: the agreed line of argument, title by title; what you found, each file with where it comes from
  images/          pictures of this deck
```

When a deck is made from an earlier one (a keynote from the company presentation, a proposal from
the sales deck), start it with `vs new keynote --from company`: sources and research come along,
the command prints the earlier deck's brief, and its slides are there to take over what fits.
Read `sources/` and `research/` of a deck before asking the user for something they have already
given.

**The research report.** Every deck gets `research/report.md`, written from the conversation, in
the language the user writes in. It is what the deck rests on, kept so that another deck on the
topic can be made from it without the conversation: a sales deck today, a TED-style talk on the
same subject next month. Write it when the storyline is agreed and bring it up to date when the
deck changes. It holds, in prose and short lists: what the deck is for and for whom; the one
message; the line of argument and why this order; every fact, figure and quotation with its
source (link or document, date) and how sure it is; what the user said and decided in the chat,
in their words where it matters (examples, stories, objections, what they ruled out); material
that was left out and why; open questions. It is not the slides retold. A build reminds you with
`RESEARCH:` while it is missing.

Fill the deck file:

```json
{
  "title": "Kickoff", "brand": "example", "langs": ["en"], "motion": true,
  "brief": {"occasion": "workshop", "presenter": "user, live", "audience": "new teams", "length": "30 min", "look": "calm, image-led", "handout": "PDF of what was shown"},
  "slides": [
    {"master": "cover", "kicker": "Kickoff", "title": "How we start <em>together</em>", "lead": "What the next twelve weeks look like.", "notes": "Welcome everyone."},
    {"master": "chapter", "number": 1, "title": "The <em>plan</em>"},
    {"master": "kpis", "title": "Three numbers about the <em>project</em>", "source": "Project plan 2025",
     "items": [{"value": "12", "label": "weeks"}, {"value": "5", "label": "plants"}, {"value": "34", "unit": "%", "label": "less downtime"}]},
    {"master": "split", "photo": "brand:images/photo_01.jpg", "title": "The pilot starts in <em>plant A</em>", "bullets": ["From the first of March.", "With both shifts."]}
  ]
}
```

**Choose the form from what the slide says, not from habit.** Three masters in a row of the same
kind (figures, columns with icons, cards) is a sign that the content was poured into what was at
hand. Something that repeats is a `cycle`; who gives what to whom is a `flow`; stages that build
on each other are `stairs`; one figure against others is `compare`; things that each have a
picture are `tiles`; two questions at once are a `matrix`; many that become few are a `funnel`;
what rests on what is a `pyramid`; two states are `before_after`; one thing and its parts are a
`hub`; a path with an end is `steps` or `process`; dates are a `timeline`. A slide
may carry more than a title and three lines: a lead sentence, the structure, and one sentence
below that says what follows (`note`), as long as it stays one idea.
**What comes up again becomes the brand's.** A slide no master fits is written freely (`free`).
The brand remembers the form of every free slide (`forms.json` in its library), and a build prints
`FORMS:` when a deck uses a form that was used before, in this deck or another. Then make it a
master without being asked: `vs forms <brand> --promote <deck> --slide N --name <name>` writes the
master and puts it in place of every slide of that form in all decks of the brand. Give its slots
names that say what they hold, write its `use`, look at it in the preview, run
`vs refresh --brand <brand>`, and tell the user in one sentence that this form is now part of
their library. From then on a change to the master reaches every deck. `vs forms <brand>` lists
the brand's own forms and which deck uses what; read it before writing a free slide, the form may
exist already.
The same holds one level down, for **parts**: a block that comes up inside slides of different
forms (a band with the conclusion, a contact box, a row of logos). A build prints `FORMS: block K
of slide N recurs …`; make it a part without being asked: `vs forms <brand> --part <name> --from
<deck> --slide N --block K` writes `parts/<name>.html` and puts `"parts": [{"part": <name>, …}]` on
every slide holding that block. When two of the brand's own masters hold the same block, the build
says so too; `--part <name> --from-master <master> --block K` makes it one part that the masters use
as `{{>part <name>}}`. Name the slots, write its `use`, run `vs refresh --brand <brand>`, and tell the
user in one sentence. `vs masters <brand>` lists the parts with their slots: put one on any slide
with `"parts"` (deck-format.md) instead of writing the block again.

The engine fills the slide by itself: where the body of a slide ends well above the footer, it is
enlarged by up to 40 percent. `"fit": false` on a slide (or the deck) keeps the sizes as they are.

`references/deck-format.md` has every field: the common ones (`notes`, `read`, `only`, `source`,
`name`, `chapter`, `lang`, `handout`), the deck's `mode` and `motion`, two languages
(`{"en": "...", "de": "..."}` in any slot), images, video and embeds, and the built-in
timer and quiz masters. Record the answers of step 2 in `brief`; it is the memory of the
project, and a later session continues from it without asking again.

**Pictures.** The main subject of a photo stands in the middle of its frame, whole. Set the crop
with the slide's `"focus"` (`"left"`, `"right top"`, `"30% 20%"`), look at every picture slide on the
contact sheet, and act on what the build points out (a head cut by the edge, people at the edge
of a picture, a text over a face).

**What the brand's decks share.** A slide that returns in many decks (team, contact, references,
"about us") and values many decks name (address, phone, number of employees, founding year) live
once in the brand's library, and a deck names them instead of copying them: `{"shared": "team"}` as
a slide, a field next to it to replace that field for this deck only, `{{fact.address}}` inside
any text. `vs shared <brand>` lists what exists and which deck uses what. When you are about to
write such a slide or value into a deck, look there first; when a new deck shows that a slide is
of this kind, make it shared (`vs shared <brand> slide team --from kickoff --slide 7`) and tell the
user. When the user says something about the company changed (a new team member, a new address),
change it there (`shared/slides/<name>.json`, `vs shared <brand> fact address "…"`) and run
`vs refresh --brand <brand>`: every deck that uses it is built again, the files from before are
kept in each deck's `.history/built/`. Say which decks changed, and that files already sent out
do not change by themselves. `references/deck-format.md` has the details.

**Every deck has an English version.** Whatever language the user works in, the deck carries
English as well (`"langs": ["de", "en"]`, the user's language first), and every text is written
in both from the start, each in the brand's voice for that language, not word for word. The L key
and the language button switch. A further language comes later with `vs langs <deck> --add fr`: it
lists every text to translate, nothing else is rebuilt. This holds for decks that exist as well: when a build prints
`ENGLISH: this deck has no English version`, add it in the same turn, without asking, and build
again; it is not something to offer. Leave English out only when the user says they do not want
it, and record that as `"english": false` in the deck file.

Write in the brand's voice: before the first title, read the ten real sentences and the
before-and-after pairs of `voice.md` again, and write so that a sentence could stand next to
them. `vs voice <brand> --check "sentence"` tries a wording against the rules.

Writing rules, on top of the brand's voice:

- Titles are full, plain sentences, as a person would say them in the room. Not allowed: counting
  titles ("5 reasons"), lists of attributes as a title, "not X but Y", punchlines, keyword chains
  without a verb, emojis. Read every title aloud; if it sounds like an advert, rewrite it.
- One message per slide; the content backs up the title. One accent word (`<em>`) per title at most.
- Nothing is invented. A missing number or photo is left out or marked, and you tell the user.
  Numbers carry their source in `source`.
- Text from a document the user supplied is used word for word. If such a slide breaks a voice
  rule, it stays as it is and gets `"voice": false`; so do slides with other people's words.
- Speaker notes on every slide of a live deck: short, full sentences, the numbers and names, the
  transition to the next slide.

## 5. Build and look

```bash
vs build kickoff
```

It prints the overflow result per language, a density line (words per slide, flagged against a
limit that fits the mode), a voice line and the paths of the contact sheets. Overflow must be
`clean`: shorten the text or split the slide, never shrink type. The legibility line must be
`clean` as well: it names every text that is hard to read, by slide (`LEGIBILITY slide 4 (…):
contrast 1.8 to 1 between text and ground …`, type under 18 px, text cut off, at the edge of the
slide, or on top of another text), and every ring, arrow, bar or line that hardly stands out; it
looks at the light and the dark scheme and puts `dark scheme:` or `light scheme:` before what only one shows. A deck is not handed over with such a finding: take another
picture or master, move the accent word, shorten, or correct the brand's master or theme
(`pitfalls.md`). Slides flagged as wordy in a live
deck usually carry text that belongs in the notes. The voice line names every text that breaks a
rule of the brand, by slide and slot (`VOICE slide 4 (bullets), bullets.2: sentence of 31 words
(limit 22)`): rewrite it in the brand's voice until the line says `clean`. A finding that is wrong
(a product name that contains an avoided word) is a matter for the rules, tell the user. Open the contact sheets and look
at every slide once; after later changes only at the ones you changed (`--only 3,7`).
Rebuild as often as needed, it takes seconds.

## 6. Hand over

**Ask about the other presentations, only when there is a reason.** Other decks are touched only
when this session changed something they share: a shared slide or a fact (made, changed or pushed),
a part or a master of the brand (made or changed), the brand's look, or the framework was updated.
Then, and only then, run `vs refresh --brand <brand> --check --except <this deck>` once at the end.
If it lists decks that are behind, ask the user once, naming them: "Shall I bring your other
presentations up to date as well?" If yes, `vs refresh --brand <brand>`, put the new files into
their folder and say in one line which changed. Nothing shared changed: no check, no question.
When this deck holds news for all of them (a new address, a new team member, a new figure), say
so in one sentence and offer to put it into the brand's facts or shared slides.

**Their own slides are the bar.** When the user has a deck on the topic already, or the brand was
built from one, a new deck must not fall behind it: take over the slides that are good as they
are (same form, same content), and write new ones to the same density. Before handing over, put
your deck next to theirs: wherever theirs shows a relation as a picture (a loop, a path, a
comparison, tiles with photos) and yours shows a list of text in the same place, change yours.

**Offer the movement once.** With the first deck of a brand, or when the user asks how it moves,
run `vs motion --deck <deck> --compare` and give them `shots/motion.html`: every motion set plays
slides of their own deck side by side. They name a set and how strong it should be; write it with
`vs motion --deck <deck> --set <name> --level calm|standard|expressive`, build again, and ask
whether the choice should hold for every deck of the brand (`vs motion <brand> --set <name>`).
What is explained in parts builds up click by click: set `"step": true` on such a slide, on any
master. The click steps come in reading order; when the explanation goes another way, or two parts
belong on one click, set `"order"` (deck-format.md). The user can do the same in the editing panel
("On click", "Order": they click the parts in the new order, with Shift to join one to the step
before; the strength of movement, "Play").

Name the version in half a sentence when you hand a deck over ("built with VibeUpSlides 0.9.5", from
the status line of the setup), so that the user can tell which state they are testing.
A button (`button: {label, url}` on the closing slide) is a call to action with a real target; a
cover has none. The last slide credits the person who made the deck (`"author"` in the deck file,
from the brand's default): "Made by …, with a little help from VibeUpSlides by vibeup.berlin". When
a build prints `AUTHOR:`, ask for the name once. `"credit": false` leaves the line out, only if the
user asks for that.

Give the user the HTML from `decks/<deck>/` (send the file if they follow from another device) and
the keys that matter: arrows to move, **M** presenter view, **P** PDF, **F** full screen, **L**
language. `references/presenting.md` has the rest. PDFs only when asked: `vs build kickoff --pdf`.
A deck with video or embeds is a folder, not a single file: present it with
`vs present kickoff` (a local address in the browser, which also lets YouTube play and removes the
pop-up and full-screen limits of the presenter view) and send it with `vs pack kickoff`.

## The other version

When the user wants the deck they presented as something to send, or a reading deck as something to
present, build the other mode from the same file: `vs build kickoff --mode reading` (or
`--mode live`). `references/modes.md` has the rules. For a reading version, write a `read` text on
every slide that needs one: prose for someone who was not in the room, not the speaker cues; the
build lists the slides that still fall back to the notes. Rewrite titles that only worked with a
voice. For a live version of a reading deck, move the prose into `notes`, keep a sentence title and
one piece of evidence on the slide, and split dense pages. Slides that belong to one version only
get `"only": "live"` or `"only": "reading"`. After an event, ask what was actually shown and mark
skipped slides with `"only": "live"` before building the version to send.

## The user edits the deck themselves

```bash
vs edit kickoff
```

opens the deck in the browser with its texts open for typing, on a local address. Offer it at the
handover and whenever the user wants to change wording: it is faster for them than describing a
change, and they see the slide while they write. The pencil in the button bar (key E) opens and
closes the editing. They click a text and type (Enter saves, Escape discards), move, duplicate or
remove list items and cards with the small bar beside the text, and from the panel above the
button bar move, duplicate or delete slides, insert a new slide from a master, add a text field the
slide does not use yet, write speaker notes and the reader text, and undo (also Cmd/Ctrl+Z). The
page warns when a text runs off the slide and marks where, and names what breaks the brand's voice.

Every change goes into `deck.json`. The built HTML is never edited. So after an editing session
**read `deck.json` again before you change anything**: the user's wording is in it, and it stands.

**After Done: correct, translate, reopen.** Nothing is corrected or translated while the user
types. Every text they change is noted on its slide, and the page tells them that it will be
corrected and translated after the editing. When they press **Done**, the page says that their
changes are taken over and that it opens again by itself, and waits. The command ends, builds the
deck and lists what was changed:

```
REVIEW slide 3, bullets.2: written in de by the user; correct spelling, grammar and punctuation
there without rewording it, translate it into en, then remove the entry from the slide's "edited"
```

The user is now looking at a waiting page, so this is your work at once and without asking:

1. For every such line read the slide's `"edited"` entry (`path`, `from`, `to`, `text`).
2. **Correct** the text in the language it was written in: typing errors, spelling, grammar,
   punctuation, the spelling of the brand's fixed terms. Do not reword it, shorten it or change its
   tone; it is the user's sentence. Write the corrected text at that path for `from`.
3. **Translate** the corrected text into every language in `to`, in the brand's voice for that
   language (`voice.md`), and write it at the same path.
4. Remove the entry (the whole `"edited"` key when the list is empty).
5. Start the editing again: `vs edit <deck> --reopen`. The waiting page notices and reloads at
   the slide the user was on; a browser page is opened only if none is waiting.
6. Tell the user in two or three sentences what you corrected (old and new wording, so they can
   object) and which slides you translated. Mention what the voice line of the build still
   reports about their texts, without changing it.

**Every built deck can be edited where it is opened.** The presentation file itself carries the
editing: the pencil in its button bar (key E) opens it, no server and no second file. This is the
way in Cowork and wherever no local server reaches the user. Say in two or three sentences how it
works when you hand a deck over:

- Open the file with a double click (Chrome or Edge), press the pencil, click a text and type;
  move, copy or delete slides, insert a new slide from one of the brand's masters and write notes
  in the panel; the small bar beside a list item moves, copies or removes that item.
- Press "Choose folder …" once and name the folder their presentations are in (the connected
  folder; the browser asks for this once and cannot be told the place). From then on every change
  is saved at once into the presentation file itself, under its own name, so it can be shown and
  passed on as it is, and into `<deck>.edits.json` beside it; later presentations in that folder
  save without the question. In other browsers Done downloads the file of changes.
- "Text field" adds a field the slide's master offers and the slide does not use yet (one per
  slide in the file; slides with pictures get theirs from you).
- All of it shows in the file at once, the new order of the slides included, and Undo takes it
  back. What still comes from you: the correction of what they typed, its translation into the
  deck's other languages, pictures, and a new PDF.
- On a slide the brand's decks share, the page says so: what they change there holds for this
  deck only, unless they press "For all presentations". Then the build prints a `SHARED:` line:
  correct the slide's texts first (its `REVIEW` lines), then run the `vs shared <brand> push …`
  it names. That command takes the slide into the library and names the other decks that use it;
  ask the user once whether to update them (`vs refresh --brand <brand>`), as it says.

**No slide goes out with a mistake.** A text the user typed counts as unchecked until you have
corrected it: the page marks it in yellow on the slide (not in the presenter mode, a PDF or
print), counts the unchecked texts next to the pencil, and a build ends with `NOT FINISHED` while
any is left. So correct at once and completely whenever changes come in; never hand over or
describe as done a deck with a `REVIEW` line open. The one exception is the user's own word: with
"Keep text as it is" they release a text themselves, and its `REVIEW` line then says not to
correct it, only to translate it; do exactly that, even if you would spell it differently.

What the user sees of it, so you can tell them: while typing, the browser underlines spelling
mistakes in the slide's language; the panel says where the change was saved and how many texts
are unchecked. After you applied, corrected and translated them, the new file shows a dot on the
pencil, and opening it lists, text by text, what was taken over as it was, what was corrected
(old and new wording) and into which languages it was translated.

**Take their changes over without being asked.** Whenever the user comes back to a deck, for
whatever reason, look first whether `<deck>.edits.json` lies next to it (in their connected
folder, or uploaded), and if so bring it in before anything else:

```bash
vs apply <deck> <file>
```

It writes the changes into `deck.json`, builds the deck and prints the same `REVIEW` lines as
above; changes that were applied before are recognised and skipped, so an old file does no harm.
Do steps 1 to 4, build again, put the new presentation and the new `vibeupslides-workspace.zip`
into the folder in place of the old ones, and report as in step 6. New slides, new text fields
and the order of list items are not offered on the page: the user tells you and you change
`deck.json`.

When the user presses Done without having changed a text, nothing happens for you: the page goes
back to the plain deck, its own HTML is brought up to date, and the command keeps running so the
pencil can open the editing again. Stop it (the background task, or Ctrl-C) when the user says they
are finished or moves on to something else. Never ask them to log in anywhere or to run something
for any of this.

Run `vs edit` in the background where your environment allows it, so the conversation stays open
while the user edits; you are told when it ends. Notes can also be written in the presenter view
(key M): they are saved and noted the same way, also during `vs present`, and the same `REVIEW`
lines appear when that command ends.

When the command ends it builds
the deck and prints the usual report: fix overflow and voice findings the user left behind only
with their consent, it is their text. The versions before each change are in
`decks/<deck>/.history/`. Charts, timer and quiz slides, images and new slides that need a picture
are not editable there: those changes come through you.

## Changing a deck

Edit `deck.json`, rebuild, look at the changed slides. A different look for the whole deck is a
matter of `motion`, the masters chosen and the surfaces they offer, not of new CSS. If the user
wants the brand itself to look or sound different (logo, colours, a master, the address, a word
to avoid), that is vs-build; every deck
picks the change up at its next build.

## Working economically

- Never read a built HTML file or an image file as text. Look at contact sheets.
- Do not write Python or HTML for a deck. The deck file and the masters are the whole interface.
- One build command does rendering, embedding, the check and the sheets; do not run them apart.

## References

| File | Read it when |
|---|---|
| `references/structures.md` | planning: the structure, questions, lengths and typical mistakes for each kind of deck |
| `references/modes.md` | the live and the reading version: differences and how to convert one into the other |
| `references/deck-format.md` | writing `deck.json`: all fields, languages, images, video, timer, quiz, charts, importing a PowerPoint |
| `references/presenting.md` | keys, presenter view, second screen, PDF and video, what to tell the user |
| `references/pitfalls.md` | something looks wrong or a build misbehaves |
