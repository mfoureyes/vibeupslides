# The deck file

`decks/<deck>/deck.json` is the whole deck: settings and a list of slides. Every slide names a
master and fills its slots. `vs masters <brand>` lists the masters of a brand with their slots;
`vs masters <brand> --full` adds a filled example for each.

## Deck fields

| Field | Meaning |
|---|---|
| `title` | title of the deck, also the file name of the HTML |
| `brand` | folder name of the brand library |
| `langs` | list of languages, e.g. `["en"]` or `["de", "en"]`; the first is the start language |
| `mode` | the main mode: `"live"` (default, a deck to present) or `"reading"` (a deck that is read without a speaker): the version the file opens in. See "Two versions" below |
| `scheme` | `"dark"`: the deck opens with dark slides (light slides take the brand's dark colour). Default `"light"`. Anyone can switch with the key D; a brand can set the same field in `brand.json` |
| `density` | word limits of the density report, e.g. `{"live": 50, "reading": 250}` (these are the defaults) |
| `contents` | `false`: no generated contents page in the reading version |
| `motion` | how much moves: `"off"` (or `false`), `"calm"`, `"standard"` (default, same as `true`) or `"expressive"`. The kind of movement comes from the brand's motion profile |
| `motion_set` | the motion set of this deck where it should differ from the brand's (`rise`, `soft`, `sweep`, `mask`, `draw`, `cascade`, `cut`, `site`, …). Written by `vs motion --deck <deck> --set <name>`; `--set brand` removes it |
| `footer_left`, `footer_right` | override the footer texts of the brand for this deck |
| `brief` | the answers about purpose, presenter, audience, length, look and handout. Not rendered; the memory of the project |
| `slides` | the list of slides |

## Fields every slide can have

| Field | Meaning |
|---|---|
| `master` | name of the master |
| `notes` | speaker notes, shown in the presenter view |
| `read` | text for readers, shown beside the slide in the reading version only: prose for someone who was not in the room. A string (a blank line starts a paragraph) or a list of paragraphs |
| `only` | `"live"` or `"reading"`: the slide exists in this version only |
| `icon` (on items of `cards`, `columns`, `steps`) | the name of an icon from the brand's library, as `vs elements <brand>` lists it. Only icons the library holds: a name that is not there is reported and left out |
| `fit` | `false`: the engine does not enlarge the body of this slide to fill it (also as a field of the deck, for all slides) |
| `step` | `true`: the slide builds up click by click, on any master: the rows of its blocks in reading order, the first stands with the slide (blocks in one row come one by one). `false`: a slide whose master builds up on click arrives as a whole. Not set: as the master does it |
| `order` | the click steps of this slide in an order of their own. The steps as the slide has them are numbered 1, 2, 3 …; `[3, [1, 2]]` (or `"3, 1+2"`) shows step 3 on the first click and steps 1 and 2 together on the next; an entry with a 0 (`[0, 2]`) puts those steps on the slide from the start. Steps not named follow in their own order. Only on a slide that has click steps (from its master or `step`) |
| `move` | how much moves on this one slide: `"calm"`, `"expressive"` or `"off"`. Not set: as the deck (`motion`) |
| `voice` | `false`: the text of this slide is not checked against the brand's voice rules (text taken over word for word, other people's words) |
| `edited` | written by the editing mode, not by you: texts the user changed, waiting to be corrected in the language they were written in and translated into the others, `[{"path": "bullets.2", "from": "de", "to": ["en"], "text": "..."}]`. Do that, then remove the entry |
| `source` | source line in the footer, for numbers and photos |
| `name` | name of the slide in outline and presenter view (default: its title) |
| `chapter` | starts a chapter with this name; the `chapter` master does it by itself from its title |
| `parts` | blocks of the brand's own on this slide (`vs masters <brand>` lists them): `[{"part": "takeaway", "t1": "...", "t2": "..."}]`, each with the slots of its part, texts per language like any slot. They stand at the end of the slide, before the notes; a free body places one with `<vs-part n="1"></vs-part>` (the number counts the list from 1) |
| `lang` | show this slide in one language only |
| `handout` | `false`: left out of the handout build |

Everything else is a slot of the master. Slots take HTML: `<em>` marks the accent word of a title,
`<b>` a bold word. Slots a master does not know are ignored; a missing optional slot leaves its
element out.

## Shared slides and facts

What many decks of a brand have in common is kept once, in the brand's library:

```
library/<brand>/shared/slides/team.json     {"master": "team", "title": {...}, "people": [...]}   one slide, as it would stand in a deck
library/<brand>/shared/facts.json           {"address": "Example Street 1, 10115 Berlin", "team": {"size": 42}, "claim": {"de": "…", "en": "…"}}
```

In a deck:

```json
{"shared": "team"}
{"shared": "team", "title": "The team for this project"}
{"master": "closing", "title": "Thank you", "lead": "{{fact.address}} · {{fact.team.size}} people"}
```

The first is the slide as it is in the library today. In the second, the field next to `shared`
replaces that field for this deck; everything else still follows the library. A fact can stand in
any text; `a.b` reaches into a group; a fact with one value per language makes the text differ by
language. A name the brand does not have is reported by the build (`SHARED: …`) and the
placeholder stays visible.

```
vs shared <brand>                                         what exists, and which deck uses what
vs shared <brand> slide team --from kickoff --slide 7     make slide 7 of a deck the shared slide "team"; the deck names it from then on
vs shared <brand> fact address "Example Street 1"         set a fact; --lang de sets it for one language
vs refresh --brand <brand>                                build again every deck that uses a shared slide or a fact (--all: every deck)
```

`refresh` rebuilds each such deck in the versions it had (reading version, handout, PDF) and keeps
the files from before in the deck's `.history/built/<time>/`. A deck that must not follow a
change copies the slide in instead of naming it.

## The deck's folder

`vs new <deck>` makes `decks/<deck>/` with `deck.json`, `sources/` (what the user supplied),
`research/` (what was found out, with its origin, and `outline.md`) and `images/`. A build adds the
HTML, `shots/` and, for decks with video, `assets/`. `vs new <deck> --from <other>`
copies sources and research of an earlier deck, notes it as `"from"` in the deck file and prints
that deck's brief.

## Photos behind text

`"focus": "right"` on a slide (also `"left top"`, `"30% 20%"`) says which part of its photo stays
in view when the picture is cropped. Use it to keep faces clear of the text: a build reports a text
or number that covers a person's face as a fault.

## Two languages

Any text can be an object with one entry per language; everything else is shared:

```json
{"master": "kpis",
 "title": {"de": "Drei Zahlen zum <em>Projekt</em>", "en": "Three numbers about the <em>project</em>"},
 "items": [{"value": "12", "label": {"de": "Wochen", "en": "weeks"}},
           {"value": "5", "label": {"de": "Werke", "en": "plants"}}]}
```

Lists can be per language as a whole: `"bullets": {"de": ["...", "..."], "en": ["...", "..."]}`.
Both languages always have the same slides in the same order.

## Two versions: to present and to read

One deck file gives two documents, and both are in every built HTML: `mode` names the one the
file opens in, the key V (or the button LIVE / READ, or `?mode=reading` in the address) shows the
other, and the export button offers the PDF of either. `vs build <deck> --mode reading` (or
`--mode live`) writes a second file that opens in the other version and checks it, on request
only. `references/modes.md` says when to offer it and what to rewrite first.

```json
{"title": "Field report", "brand": "acme", "langs": ["en"], "mode": "live",
 "slides": [
  {"master": "bullets", "title": "Half of every week is spent in <em>meetings</em>",
   "bullets": ["19 hours a week.", "Two thirds end without a decision."],
   "notes": "19 hours: mention the survey. Ask the room about the two thirds.",
   "read": ["We asked twelve teams to log every meeting for one quarter. On average a team member spent 19 hours a week in meetings.",
            "Two thirds of these meetings ended without a decision that anyone wrote down."]},
  {"master": "statement", "text": "A meeting without a decision is a <em>reading</em>.", "only": "live"},
  {"master": "table", "title": "Sources and <em>method</em>", "head": ["Source", "Scope"], "rows": [["Survey", "12 teams"]], "only": "reading"}]}
```

What the reading version does with the same slides:

- A slide with `read` becomes a page with the whole slide reduced on the left and the text in a
  column on the right. A slide without `read` takes its `notes` as they are, and the build lists
  those slides ("reader text missing ..."), so that they get rewritten. A slide with neither is
  shown full size.
- All click steps are visible, motion is off, `timer` slides are left out, quiz slides show their
  answer, video and embed slides show their poster with the address as a link.
- A contents page is generated after the cover when the deck has at least two chapters, and every
  page carries a bar with all chapter names, the current one marked. Page numbers stay.
- Speaker notes are not in the file at all.

Built live, a deck never shows `read` on a slide; where a slide has `read` but no `notes`, the
presenter view shows the reader text as notes.

## Images

Put files into `decks/<deck>/images/` and name them in a slot: `"photo": "images/team.jpg"`.
Photos of the brand library: `"photo": "brand:images/photo_01.jpg"`. The style guide says what
each library photo shows. A path that does not exist gives a warning and the master's placeholder.
Use photos the user supplies or the library has; no stock pictures unless asked, and a credit in
`source` where one is due. Keep decks light: photos about 2000 px wide at most, cut-outs about
500 px high.

## Video and embeds

A deck that uses one of these is **a folder, not a single file**: the HTML plus the files it links.
The build says so in one line. Everything else about the deck stays the same.

**video**: a file, or a YouTube or Vimeo link. A video is always shown whole, never cropped: in the
boxed layout the box takes the shape of the video (16:9 until the file has loaded; `ratio` says it
beforehand for other shapes), in the full layout bars fill what the video leaves free. Every boxed media slide (`video`, `embed`) has a box in the shape of a video, 16:9.

```json
{"master": "video", "src": "media/demo.mp4", "poster": "images/demo.jpg", "title": "The product in 40 seconds"}
{"master": "video", "src": "https://youtu.be/VIDEOID", "start": "1:05", "end": 95, "poster": "images/talk.jpg",
 "layout": "boxed", "kicker": "Keynote", "title": "What she said about <em>trust</em>", "caption": "Source: conference channel"}
```

| Slot | Meaning |
|---|---|
| `src` | file relative to the deck folder, `brand:<path>` for a file of the brand library (copied to `assets/` at build), or an https address |
| `poster` | still image: shown before the video plays and in PDF, overview and presenter preview. Always give one; without it a neutral field with the title stands in |
| `layout` | `"full"` (default, video fills the slide, no logo and footer) or `"boxed"` (title above, footer as usual) |
| `title`, `kicker`, `caption` | printed in the boxed layout; `title` is always the slide's name in the outline, `caption` also lies on a full video |
| `start`, `end` | seconds, `"1:30"` or `"1m30s"`. Vimeo knows no end time |
| `autoplay` | `true` (default): plays when the slide becomes current. `false`: waits for K or a click |
| `loop`, `muted`, `controls` | `true` or `false` (default `false`) |
| `fit` | `"cover"` fills and crops (default when full), `"contain"` shows the whole frame (default when boxed) |

Files: mp4 with H.264 and AAC plays in every browser, webm too except in old Safari. The file is
linked, never embedded; keep it in the deck folder (for example `media/`). YouTube and Vimeo links
become the privacy-friendly players (`youtube-nocookie.com`, Vimeo with `dnt`); they need to be
online, and YouTube plays only when the deck is started with `vs present` (opened as a file the
slide shows the poster and a link to the video). Any other address goes into a plain iframe.

**embed**: a live website, Figma file, Loom recording, or an HTML file of the deck folder.

```json
{"master": "embed", "url": "https://example.org/pricing", "poster": "images/pricing.jpg", "title": "The live pricing page"}
```

Slots: `url`, `poster`, `layout`, `title`, `kicker`, `caption`, and `allow` for rights the page
really needs (`autoplay`, `encrypted-media`, `picture-in-picture`, `clipboard-write`; camera,
microphone and the like are never passed on). The page runs sandboxed and cannot navigate the deck
away. Many sites forbid being embedded and stay blank: try it, give a poster, and put the address
into the notes as plan B. Once the presenter clicks into the page, keys go to the page; the button
bar of the deck stays visible as the way back.

In PDFs, contact sheets, the overview and the presenter's preview of the next slide both show
their poster, never a live player. Missing file: a warning at build and a placeholder
on the slide.

**video_title**: the same slots as `video`, with one line of title above the film. The video takes
all the room below the title, in its own shape; nothing lies on the picture. Plain `video` is the
film alone, as large as the slide, without any text: the right choice whenever the film speaks for
itself. `video` with `"layout": "boxed"` is the small version under title and logo.

```json
{"master": "video", "src": "media/demo.mp4", "poster": "images/demo.jpg", "title": "Product film"}
{"master": "video_title", "src": "media/demo.mp4", "poster": "images/demo.jpg", "title": "The product in <em>40 seconds</em>"}
```

### A video behind the text

`chapter`, `cover_photo`, `fullbleed` and `statement_photo` take a slot `video`: a file that plays
silently in a loop behind the text while the slide is shown. Use it for the slides between the
parts of a deck, when the brand has a film that fits (`vs videos <brand>` saves the website's own
videos into the library and says which one runs as a background there).

```json
{"master": "chapter", "number": 2, "title": "What we <em>learned</em>", "video": "brand:videos/video_01.mp4"}
{"master": "fullbleed", "photo": "images/site.jpg", "video": "media/site.mp4", "title": "On site in May"}
```

The photo stays the still for PDFs, overviews and the reading version, so keep it. A background
video fills the slide and is cropped at the edges; that is the difference to a `video` slide, which
shows a film as content and never crops it. One or two such slides per deck, not every chapter.

## Built-in masters

**timer**: a countdown that stands after the slide explaining the task.

```json
{"master": "timer", "kicker": "Exercise", "minutes": 20,
 "heading": "{duration} for the <em>interviews</em>",
 "steps": [{"n": "1", "title": "Ask", "text": "One person asks, one answers."}],
 "facts": [{"label": "Duration", "value": "{duration}"}, {"label": "Format", "value": "In pairs"}]}
```

`{duration}` becomes "20 minutes" and follows the buttons while presenting. Empty `steps` give the
centred clock for breaks. Timers are left out of handouts and reading versions.

**quiz_choice**, **quiz_true_false**, **quiz_estimate**: questions to the audience.

```json
{"master": "quiz_choice", "question": "How many repairs were planned ahead last year?",
 "answers": ["A quarter", "A third", "More than half"], "correct": 2,
 "explanation": "Sixty percent were planned ahead.", "source": "Maintenance report 2025"}
{"master": "quiz_true_false", "statement": "Slides carry their own logos.", "is_true": false, "explanation": "The framework places them."}
{"master": "quiz_estimate", "question": "How many pixels wide is a slide?", "number": 1920, "unit": "pixels", "explanation": "1920 by 1080."}
```

`correct` counts from 0; `null` makes it a poll. `"advance": true` reveals with the next forward
click (say so in the notes). The question is a full sentence, answers fit on one line, the number
of an estimate needs a source. In the handout build and in the reading version the answers are shown.

**logo_intro**: logo sting for videos. **raw**: `{"master": "raw", "html": "..."}` for a slide
written by hand; use the tokens (`var(--accent)` ...), never hex colours. Prefer `free` (title plus
`body`) so the slide keeps the brand's title style, and prefer a new master through vs-build when
the look will be needed again.

## Figures and charts

```json
{"master": "bars", "title": "Most stoppages come from a few <em>causes</em>", "source": "Report 2025",
 "rows": [{"label": "Late maintenance", "value": 240, "share": 100}, {"label": "Operating errors", "value": 33, "share": 14}]}
{"master": "line_chart", "title": "Planned repairs grow every <em>year</em>", "source": "Report 2025",
 "axis": ["2022", "2023", "2024"], "ymax": 300,
 "series": [{"values": [120, 180, 240], "color": "var(--accent)", "labels": true}]}
```

`share` is the bar width in percent of the widest bar. Real numbers only, with a source.

A finding with a column chart is the master `figure` with numbers instead of an image. The columns
come up one after the other from left to right; `mark` names the column that carries the point:

```json
{"master": "figure", "topic": "Finding", "title": "Downtime has fallen in every quarter since the <em>switch</em>",
 "columns": [{"label": "Q1", "value": 310}, {"label": "Q2", "value": 300}, {"label": "Q3", "value": 241}],
 "mark": 3, "callout": "The drop begins when the pilot plant went live.", "source": "Plant log 2025"}
```

A chart that exists as an image file (`image`) cannot build up: it is a picture. Use `columns`,
`bars` or `line_chart` whenever the numbers are at hand. 

**Builds on forward presses.** `timeline` shows one bar per forward press in the order of its
rows, then the milestones; `phases` one phase (its whole column) per press; the first part stands
when the slide appears. Write the rows in the order in which you explain them. `"step": false` on
the slide lets it build by itself instead (for decks that run unattended). A `figure` with
`columns` builds by itself; `"step": true` makes every column a press of its own. The figure of
`big_number` counts up from 0 when it is a whole number ("240", "1,240"), in at most three
seconds. Say the number of presses in the notes.

## Commands

```bash
vs new <deck> --brand <brand> [--langs de,en] [--title "..."]
vs build <deck> [--only 3,7] [--no-shots] [--pdf] [--handout]
vs build <deck> --mode reading|live
vs titles <deck>
vs video <deck> --slide 1 --seconds 6 [--format 16:9|1:1|9:16] [--hide .kicker]
vs present <deck> [--port N] [--no-open]
vs pack <deck>
```

`build` writes `<Title>.html` into the deck folder, checks every slide for overflow (content must
end 150 px above the footer and 120 px before the right edge) and writes contact sheets to
`shots/`. `--pdf` adds a vector PDF per language, `--handout` builds `<Title>_handout.html`.

`--mode` builds the version that is not the deck's main mode, next to the main one:
`<Title>_reading.html` (or `<Title>_live.html` for a reading deck), contact sheets in
`shots_reading/` (`shots_live/`), with `--pdf` also `<Title>_reading_<LANG>.pdf`. In a reading
version the overflow check also reports reader text that is too long for its column
(`'reader_text': '120 px too long for its column'`); shorten the text or split the slide.

Every build prints a density line per language: the words visible on each page (title, labels and
body; footer and notes not counted; in a reading version the reader text included), with `!` and a
`WORDY` line for pages above the limit of the mode. The defaults are 50 words for a live slide and
250 for a reading page; `density` in the deck file changes them. It is a report, not a failure: a
table may be over the limit for good reason, a slide of full sentences in a live deck usually is not.

`titles` prints the slide titles in order, per language, with the slide's number in the deck file
and its master, and nothing else. Read them as a chain before designing slides: they must give the
argument without the bodies. `(no title)` marks slides that have none (statements, timers, photos).
A deck without video or embed is one self-contained HTML file. With them the build prints
"this deck is a folder: ..."; then `present` shows it over a local address and `pack` writes
`decks/<deck>.zip` with the HTML and every file it links, and says if the deck needs to be online.

## Importing an existing PowerPoint

Read text and notes with `python-pptx` if it is available (`slide.notes_slide.notes_text_frame.text`),
otherwise ask the user for a PDF or the text. Detect hidden slides and ask whether they come along.
Pull images (`shape.image.blob`) into the deck's `images/` folder and drop tiny ones. Then propose
a storyline, get it confirmed and write the deck file: titles rewritten as full sentences in the
brand's voice, numbers, tables and images unchanged, outdated content (old dates) marked for the user.
