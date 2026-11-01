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
| `minutes` | the length the talk must have, in minutes. The presenter view spreads it over the slides by their `weight` and shows the time left per slide, whether the talk is on time and when it will end. Not set and no `plan` on the slides: the presenter view only measures. See "Length and time plan" below |
| `event` | where and when the deck is shown: `{"date": "2026-11-04", "start": "10:45", "place": "…", "audience": "…", "guest": "…"}`. `start` gives the schedule of the presenter view its clock times before the talk starts. Not rendered otherwise |
| `copy_to` | folders the build copies its files into and reads back, e.g. a shared or cloud folder: `["~/Nextcloud/Talks/2026-11"]`. The build says what it copied and names older files of the deck there that it did not renew |
| `scripts` | `true`: the deck's languages in another script (Chinese, Japanese, Cyrillic …) get matching system faces behind the brand's family. Only when the user wants it, see "Writing systems" |
| `brief` | the answers about purpose, presenter, audience, length, look and handout. Not rendered; the memory of the project |
| `slides` | the list of slides |

## Fields every slide can have

| Field | Meaning |
|---|---|
| `master` | name of the master |
| `notes` | speaker notes, shown in the presenter view |
| `read` | a paragraph for readers, set under the title in the reading version only: what the slide means for someone who was not in the room. A string or a list of paragraphs. Short: two or three sentences. The same as `reading.explain` |
| `reading` | the slide as the reading version shows it: `explain` (the paragraph under the title) and any slot of the master with a text of its own for readers, e.g. `"bullets"` as full sentences or a longer `"lead"`. See "Two versions" below |
| `cues` | the notes as talking points: a list of three to five short lines per language. The presenter view switches between the whole text (`notes`) and these |
| `only` | `"live"` or `"reading"`: the slide exists in this version only |
| `icon` (on items of `cards`, `columns`, `steps`) | the name of an icon from the brand's library, as `vs elements <brand>` lists it. Only icons the library holds: a name that is not there is reported and left out |
| `fit` | `false`: the engine does not enlarge the body of this slide to fill it (also as a field of the deck, for all slides) |
| `step` | `true`: the slide builds up click by click, on any master: the rows of its blocks in reading order, the first stands with the slide (blocks in one row come one by one). `false`: a slide whose master builds up on click arrives as a whole. Not set: as the master does it |
| `order` | the click steps of this slide in an order of their own. The steps as the slide has them are numbered 1, 2, 3 …; `[3, [1, 2]]` (or `"3, 1+2"`) shows step 3 on the first click and steps 1 and 2 together on the next; an entry with a 0 (`[0, 2]`) puts those steps on the slide from the start. Steps not named follow in their own order. Only on a slide that has click steps (from its master or `step`) |
| `move` | how much moves on this one slide: `"calm"`, `"expressive"` or `"off"`. Not set: as the deck (`motion`) |
| `deepen` | the name of a deepening this slide belongs to, e.g. `"Method"` (`true` names it `more`). It is left out of the short version and can be taken in while presenting. See "Deepenings" below |
| `show` | `true` or `false`: the presenter's own choice for this slide, over what `deepen` says. Written by the presenter view when the deck runs with `vs present` or `vs edit`; leave it alone unless the user asks |
| `weight` | the slide's share of the length (`minutes`): 1 is an ordinary slide, 2 twice as long, 0.5 half. Not set: 1, chapter slides 0.4, the cover 0.6 |
| `plan` | planned seconds on this slide, fixed: they are not spread. For slides whose time is known (a pitch of 10 minutes by a guest, a video). Timer slides count with their minutes |
| `voice` | `false`: the text of this slide is not checked against the brand's voice rules (text taken over word for word, other people's words) |
| `edited` | written by the editing mode, not by you: texts the user changed, waiting to be corrected in the language they were written in and translated into the others, `[{"path": "bullets.2", "from": "de", "to": ["en"], "text": "..."}]`. Do that, then remove the entry |
| `source` | source line in the footer, for numbers and photos |
| `source_url` | the address of the source (`https://…`): the source line in the footer becomes a link to it, in the deck and in the PDF |
| `buttons` | buttons on this slide: one or a list of `{"label": …, "url": …, "style": "secondary"}` (label per language like any text). `url` is a web page, `mailto:` an address, or a file of the deck folder. They stand at the foot of the slide, or where the master places `{{>buttons}}`. The closing masters also take one `button` slot. See "Links and buttons" below |
| `qr` | `false`: no QR codes beside the buttons of this slide. By default the live version shows one beside every button that leads to a web page or a mail address |
| `name` | name of the slide in outline and presenter view (default: its title) |
| `chapter` | starts a chapter with this name; the `chapter` master does it by itself from its title |
| `parts` | blocks of the brand's own on this slide (`vs masters <brand>` lists them): `[{"part": "takeaway", "t1": "...", "t2": "..."}]`, each with the slots of its part, texts per language like any slot. They stand at the end of the slide, before the notes; a free body places one with `<vs-part n="1"></vs-part>` (the number counts the list from 1) |
| `lang` | show this slide in one language only |
| `handout` | `false`: left out of the handout build |

Everything else is a slot of the master. Slots take HTML: `<em>` marks the accent word of a title,
`<b>` a bold word, `<a href="https://…">` a link. Slots a master does not know are ignored; a missing optional slot leaves its
element out.

## Links and buttons

- **Links in the text are for readers.** Any text can hold `<a href="https://…">the words</a>` (or
  `mailto:`). In the reading version, the handout and while editing the link is underlined in the accent
  colour and opens beside the deck; in the PDF it stays a link. On the screen of a talk nobody clicks and a
  line under words reads as emphasis: there a link is plain text and does nothing. So put links where
  readers are: into the `reading` texts of a slide (a link only in the live text is reported, `LINKS:`),
  and where a number or a claim rests on a source with an address, link the words that make the claim
  there and give the slide `source` with `source_url`: the footer line is a link in every version.
  What the room should act on is a button (below), with its QR code.
- **Formatting in the editor.** The user selects words and uses the menu Format or the keys: ⌘K
  (Ctrl+K) link, ⌘B bold, ⌘I italic, ⌘⇧X struck through; the same again takes it off. `<b>`, `<i>`,
  `<s>` and `<a>` are kept in the deck file; the accent word of a title stays `<em>`.
- **Buttons.** A slide that asks for an action (book a meeting, download the paper, write to us) carries it
  as a button, not as an address in the text: `"buttons": [{"label": {"de": "Termin vereinbaren", "en":
  "Book a meeting"}, "url": "https://…"}]`, a second one with `"style": "secondary"` (outlined). One or two
  per slide. They look like the brand's button (`a.vs-btn` in the brand's theme, taken from the website by
  vs-build) and work in the HTML, online and in the PDF. Use them on reading versions and decks that are
  sent, and on the closing slide of a talk.
- **QR codes.** In the live version a QR code stands beside every button that leads to a web page or a mail
  address, so the room takes the link with their phones. The reading version and the handout leave it out
  (they have the link itself). `"qr": false` on a slide leaves it out there too. Links to a file of the deck
  folder get no QR code: a phone cannot reach it.

## Writing systems

Only on request. For a language whose script the brand's typeface rarely covers (Chinese, Japanese,
Korean, Cyrillic, Greek, Hebrew, Arabic, Thai, Devanagari) the browser takes a face of its own, and the
build says so once (`SCRIPTS:`). When the user wants it (the letters look mixed or wrong), `"scripts":
true` in the deck sets system faces of that script behind the brand's family, on those slides only:
the brand face still sets every letter it has, the rest comes from one matching face. Chinese,
Japanese and Korean then also lose the slanted `<em>` (there are no italics; the accent colour stays)
and break lines by their own rules. Never set it without the user. Right-to-left languages (Hebrew, Arabic) need more than a face and are not laid out yet: say
so to the user before writing such a deck.

## Length and time plan

When the length of the talk is known, write it as `minutes` and give each slide a `weight` that
follows the storyline: the slides that carry the argument get more, transitions and chapter slides
less. The presenter view divides the minutes by these weights; typed into the presenter view, another
length ("5 minutes" on the day) is divided the same way. `vs plan <deck>` prints the plan per slide
and per chapter; check it against the length before handing over.

```json
{"minutes": 20, "slides": [
  {"master": "cover", "title": "…"},
  {"master": "bullets", "title": "…", "weight": 2},
  {"master": "video", "src": "assets/demo.mp4", "plan": 90}]}
```

Without `minutes` and without `plan` there is no plan: the presenter view measures how long the talk
and each slide took. That is the right choice when nobody knows the length yet.

## Deepenings

A deck can carry more than the talk needs: slides with `"deepen": "<name>"` stand in the deck
but not in the short version. While presenting, the film strip of the presenter view shows them
grey with the name of their deepening; a click on one takes it in and goes there, the box under it
takes it into the prepared talk or leaves any slide out without going there. When skipped slides
follow the current one, a yellow button next to Next takes them in. X opens or closes all
deepenings; `?deepen=all` or `?deepen=Method,Cases` opens them from the address. The PDF and the
handout hold the talk as prepared; the checks of the build look at every slide.

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
`research/` (what was found out, with its origin, and `outline.md`), `images/` and `assets/` (videos
and files the slides link). A build adds the HTML, `shots/` and `README.md` (what the deck is, its
files, how to open it and go on, in the deck's first language; written anew each time, never by
hand). `vs handover <deck>` copies all of it, without the working files, into one tidy folder for
the user. `vs new <deck> --from <other>`
copies sources and research of an earlier deck, notes it as `"from"` in the deck file and prints
that deck's brief. `--variant` makes the same talk for another occasion: slides, length,
deepenings and choices, images and assets come along too, `event` starts empty and the deck notes
`"variant_of"`.

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
           {"value": "48", "label": {"de": "Kunden", "en": "clients"}}]}
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

- Every slide stays a whole slide in its master. A slide with `reading` (or `read`) is in the file
  twice: as it is for the live version, and for the reading version with its texts for readers,
  the paragraph `explain` under the title. Where those texts need the room, the body of the slide
  is set smaller, by a fifth at most (27 px become about 22); beyond that the build reports the
  overflow: shorten the text or split the slide.
- A slide without `reading` and `read` is shown as in the live version; the build lists the content
  slides among them ("no text for readers ..."), so that each is looked at: most need a sentence of
  explanation, a few say everything themselves.

```json
{"master": "bullets", "title": "We work in three <em>places</em>",
 "bullets": ["Office.", "Workshop.", "Lab."],
 "reading": {"explain": "The three places are ten minutes apart, so a team can test in the morning what it built the day before.",
             "bullets": ["The office has 40 desks that teams use for a year.", "The workshop has 3D printers and a laser cutter.", "In the lab, teams invite customers to trials."]}}
```
- All click steps are visible, motion is off, `timer` slides are left out, quiz slides show their
  answer, video and embed slides show their poster with the address as a link.
- A contents page is generated after the cover when the deck has at least two chapters. Page
  numbers stay.
- Speaker notes are not shown.

Built live, a deck never shows `read` or `reading`; where a slide has `read` but no `notes`, the
presenter view shows the reader text as notes.

## Notes and talking points

`notes` is the whole speaking text in the language of the slide, written to be read aloud if need
be; `cues` are the same as three to five short talking points. The presenter view shows either,
switched in the notes panel. Write both on every slide of a live deck; the build lists slides that
have notes but no cues (`CUES: …`).

```json
{"master": "steps", "title": "…", "notes": {"en": "The support has three steps. First the team applies with one page …"},
 "cues": {"en": ["Apply: one page", "Start: three months of coaching", "Grow: funding and network"]}}
```

## Handout

`vs handout <deck>` builds `<Title>_handout.html` and a PDF per language: the talk as prepared,
deepenings left out unless taken in, no timers, quizzes answered, pages numbered without gaps.
Slides with `"handout": false` stay out. Run it at every hand-over of a presented deck.

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
{"master": "quiz_choice", "question": "How many visitors come back for a second visit?",
 "answers": ["A quarter", "A third", "More than half"], "correct": 2,
 "explanation": "Sixty percent come back.", "source": "Visitor survey 2025"}
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
{"master": "bars", "title": "The first cause is twice as large as the <em>next</em>", "source": "Report 2025",
 "rows": [{"label": "Cause A", "value": 240, "share": 100}, {"label": "Cause B", "value": 120, "share": 50}]}
{"master": "line_chart", "title": "The figure grows every <em>year</em>", "source": "Report 2025",
 "axis": ["2022", "2023", "2024"], "ymax": 300,
 "series": [{"values": [120, 180, 240], "color": "var(--accent)", "labels": true}]}
```

`share` is the bar width in percent of the widest bar. Real numbers only, with a source.

A finding with a column chart is the master `figure` with numbers instead of an image. The columns
come up one after the other from left to right; `mark` names the column that carries the point:

```json
{"master": "figure", "topic": "Finding", "title": "The figure has fallen in every quarter since the <em>change</em>",
 "columns": [{"label": "Q1", "value": 310}, {"label": "Q2", "value": 300}, {"label": "Q3", "value": 241}],
 "mark": 3, "callout": "The drop begins in the quarter of the change.", "source": "Report 2025"}
```

Two or three series side by side, or stacked when the parts of each column count as well as the
whole, are a `column_chart`; the first series takes the accent colour, the others two greys:

```json
{"master": "column_chart", "title": "Every quarter beats last <em>year</em>", "source": "Report 2026",
 "axis": ["Q1", "Q2", "Q3", "Q4"], "unit": "m €",
 "series": [{"label": "2026", "values": [12, 14, 13, 17]}, {"label": "2025", "values": [9, 11, 12, 13]}]}
```

`"stacked": true` stands the series on one another with the total above each column; with one
series, `"highlight": 4` keeps the fourth column in the accent colour and greys the others. Parts
of one whole are a `share`: a ring with the part that counts in the middle, or with `"pie": true` a
full circle, for parts that matter about equally. Two to five parts, adding up to 100.

A roadmap is a `roadmap`, in one of two forms. Milestones on a line, the current one marked:

```json
{"master": "roadmap", "title": "The first stage is live, two more follow by <em>autumn</em>",
 "milestones": [{"date": "Jan 2027", "label": "First version", "state": "done"},
   {"date": "Mar 2027", "label": "Second version", "text": "Open to every team.", "state": "now"},
   {"date": "Jun 2027", "label": "Integration"}, {"date": "Oct 2027", "label": "Done"}]}
```

Or three horizons when the dates are not fixed yet, `"horizons": [{"label": "Now", "when": "Q1",
"items": [{"title": "...", "text": "..."}]}, {"label": "Next", ...}, {"label": "Later", ...}]`; the
further out, the lighter the column. Both build one column or milestone per forward press.

A chart that exists as an image file (`image`) cannot build up: it is a picture. Use `columns`,
`bars`, `column_chart` or `line_chart` whenever the numbers are at hand. 

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
A slide of the original that already works (one clear message, a good chart, a strong photo) is taken
over as it is, in content and wording, and set in the brand's master; say which ones you kept.
