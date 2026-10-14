# Modes: the deck that is presented and the deck that is read

Read this when the user wants a deck to be sent, read beforehand or left behind, or asks for "the
other version" of a deck that exists. Sources are in `research/deck-typen.md` in the repository.

## Two versions, two documents

In the **live version** the person speaking carries the argument and the slide supports them. In
the **reading version** the slide carries the argument alone, because nobody is there to explain
it. Nearly all sources say one deck cannot do both well: slides with enough text to be read alone
are too dense for a room, and slides made for a room say too little in an inbox.

Where the terms come from:

- **Slideument** (Garr Reynolds): the mixed form of slide and document. He advises against it.
- **Slidedoc** (Nancy Duarte, 2014): the reading version as a format in its own right, a document
  in slide form with one clear message per page, to read beforehand or to leave behind.
- Edward Tufte and Amazon (the six-page memo, shareholder letter 2017) go further and prefer
  running prose altogether. Worth mentioning when a user's reading deck is really a report.

## The differences

| | Live version | Reading version |
|---|---|---|
| Who carries the argument | the speaker | the slide itself |
| Text | few words, key terms | full sentences, about 100 words, at most around 250 per page (Duarte, one source) |
| Title | a claim as a sentence, with an image or a number | a claim as a sentence; the titles in a row give the argument |
| Notes | only for the speaker | move onto the page as running text |
| Click steps, animation | sparingly, where they pace an explanation | none, only the final state |
| Charts | the voice explains | label at the data point, source line |
| Orientation | minimal | contents, page numbers, appendix, sources |
| Timers, quizzes, exercises | active | the question with its answer or result, otherwise left out |

## Converting

**Live to reading**
1. Put what the speaker says onto the page as prose. Notes are cues for someone who knows the
   material; a reader needs the full thought.
2. Rewrite titles into claims where they are not, and read them as a chain: they must give the
   argument without the body.
3. Label charts at the data point and add the sources.
4. Add contents and page numbers; move detail into an appendix.
5. Reduce click steps to the final state.
6. Give pure image slides one sentence, or merge them into a neighbour. A photo that worked as a
   pause in a talk is an empty page in a document.
7. Remove timers; show quiz questions with their answers.

**Reading to live**
1. Move the prose into the notes. On the slide stay the sentence title and one piece of evidence.
2. Split dense pages: one idea per slide.
3. Let the type be large; shorten the text until it fits rather than shrinking it.
4. Move sources and detail into the appendix.
5. Add click steps only where they pace an explanation.

## What research supports and what is convention

- **Supported (consensus):** the same text on the slide and in the spoken word harms learning;
  slightly different key terms help (Kalyuga, Chandler and Sweller 1999; Yue, Bjork and Bjork
  2013). So a live slide never carries the sentences the speaker says.
- **Too coarse:** "people cannot read and listen at the same time". A meta-analysis (Adesope and
  Nesbit 2012, 57 studies) finds advantages for spoken plus written under certain conditions; key
  terms beat verbatim text. Do not use the popular short form as an argument.
- **Supported (one source):** long texts are understood better written than spoken (Leahy and
  Sweller 2016). This is the case for a reading version of its own.
- **Supported (one research group):** a sentence heading with visual evidence leads to better
  understanding and recall than a keyword title with bullets (Garner and Alley 2013).
- **Convention, not research:** every fixed word count and every fixed type size, including the
  100 and 250 words above. Treat them as a sense of scale and let the overflow check decide.

## Accessibility of the reading version

A reading version is a document and is used like one, also with a screen reader.

- Contrast of 4.5:1 for text, 3:1 for large type (WCAG 1.4.3). The brand tokens are checked when
  the library is made; do not set text on photos without the master's darkening.
- One descriptive title per page. A page without a title (a photo, a quote) gets a `name`.
- A reading order that was checked: what is read first comes first in the slots.
- Alternative texts for images and charts that carry content.
- A tagged PDF (WebAIM).

---

## How VibeUpSlides does it

The fields and commands are listed in `references/deck-format.md`; this is how they work together.

### The model

- Every deck has a **main mode**: `"mode": "live"` or `"mode": "reading"` in `deck.json`. A deck
  without the field counts as `live`. The main mode is the answer to "who carries the argument"
  in step 2 of vs-create, and it is what a plain `vs build <deck>` produces (`<Title>.html`).
- **Both versions are in every built file.** It opens in the main mode; the key V, the button
  LIVE / READ in the button bar or `?mode=reading` in the address show the other one at the same
  slide, and the export button offers the PDF of either. Slides marked `only` and the generated
  contents page appear in their version only.
- The **other version as a file of its own** is built on request from the same deck file, as a second output next to the
  first: `vs build <deck> --mode reading` writes `<Title>_reading.html`, which opens in the reading
  version and is checked as one (reader texts against their column); `--mode live` writes
  `<Title>_live.html` for a deck whose main mode is reading. Contact sheets go to `shots_reading/`
  or `shots_live/`, `--pdf` adds `<Title>_reading_<LANG>.pdf`. One file keeps the two versions
  from drifting apart. Nothing builds the other version by itself.
- Every slide can carry a slot **`read`**: prose written for the reader, per language like any
  other slot, a string or a list of paragraphs. It is shown only in the reading version.
- When `read` is missing, the reading version takes the slide's `notes` as they are. Notes are
  cues, so the agent rewrites them as prose into `read` before handing a reading version over. The
  build prints the numbers of the slides where it fell back ("reader text missing, the speaker
  notes are shown as they are ...") and of the slides that have neither.
- In the other direction, a deck built live never shows `read` on a slide; the presenter view
  shows it where `notes` is missing.
- A slide meant for one version only (appendix and source pages for readers; a pause image for
  the room) carries `"only": "reading"` or `"only": "live"`. The existing `"handout": false` keeps
  its meaning: the handout is the record of what was shown at an event; the reading version is the
  document that argues on its own.

### The reading page

The page stays 16:9, so the reading version can be paged through, printed and exported like any
deck. A slide **with** reader text is shown whole but reduced to 60 percent in a frame on the left;
the text stands in a column on the right, set as reading text (26 px on the 1920 px page, about
11 pt on a printed A4 sheet, 45 to 50 characters a line), centred against the slide while it is
short. The column holds roughly 170 words. A slide **without** reader text and without notes is
shown full size: covers, chapter openers, the closing slide, and any slide that says everything
itself.

| Element | In the reading version |
|---|---|
| Click steps (`step`, process stages, reveals) | all shown, the final state; one key press is one page |
| Motion | at rest, whatever `motion` says |
| `timer` slides | left out |
| Quiz slides | the question with the answer and explanation shown, nothing to click |
| Videos and embeds | the poster, the address as a link; no player is loaded |
| Speaker notes | not shown; they only stand in for a missing `read` |
| `source` | in the footer of the page, as on the live slide |
| Page numbers | in the footer of every page, counted in the reading version |
| Section bar | on every page except cover slides (the closing slide is one) when the deck has at least two chapters: all chapter names in a row, the current one marked, each a link to its first page |
| Contents | one page after the cover, generated from the chapters when there are at least two, with the page each chapter starts on; `"contents": false` in the deck file leaves it out |
| Presenter view, notes panel | no buttons for them; outline, overview, language switch and PDF export work as in any deck |

### The checks

- **Overflow** runs on the reading layout: the reduced slide is measured like a full one, and the
  reader text is measured against its column (`'reader_text': '120 px too long for its column'`).
  Text that is too long runs visibly over the footer rather than being cut, so it cannot go
  unnoticed. Shorten it or split the slide.
- **Density**: every build prints the words visible per page and flags pages above the limit of
  the mode: 50 words for a live slide (a sentence title plus one piece of evidence; more than that
  is being read while the speaker talks), 250 for a reading page including its reader text (the
  figure from the table above). `"density": {"live": 50, "reading": 250}` in the deck file sets
  other limits. Both numbers are conventions: a flag is a reason to look, not an error.
- **Titles**: `vs titles <deck>` prints the titles in order with slide number and master, per
  language. Use it in both directions of a conversion and before a deck is designed at all: the
  chain of titles must give the argument.

### What to ask the user before building the other version

For a reading version of a live deck:
1. Who reads it and when: beforehand to prepare a decision, afterwards as a record, or forwarded
   to people who were not there? This decides how much the prose must explain.
2. May slides be merged, split or added (contents, appendix), or must the page count match what
   was shown?
3. Are the notes complete enough to write from? Where a slide has no notes, ask for the content;
   do not invent what the speaker would have said.
4. For exercises and polls: is there a result to show, or does the slide drop out?
5. For videos: is there a public link that may be printed?

For a live version of a reading deck:
1. Who presents, to whom, and how long is the slot? The slot decides how many pages survive.
2. Has the audience read the document? If so, repeat nothing: name the goal of the meeting and
   keep the summary, the points to decide and the next steps.
3. Which pages are the argument and which are reference? Reference goes to the appendix.

### What to write or rewrite

For the reading version:
- **`read` on every content slide**: two to five sentences of prose in the brand's voice that say
  what the speaker would say, with the numbers and names. Write for someone who was not in the
  room: no "as you can see", no references to the event. Text from a document the user supplied is
  used word for word.
- **Titles**: check the chain. A live title that leans on the voice ("And then this happened")
  becomes a claim that stands alone. Change the title in the slot, so both versions gain.
- **Charts and figures**: add `source` where it is missing and name the data point that matters
  in `read`.
- **Image-only slides**: one sentence in `read`, or mark them `"only": "live"`.
- **Orientation**: the contents page and the section bar are generated from the chapters, so a
  deck of more than about ten pages needs chapters (inference). Add an appendix chapter marked
  `"only": "reading"` for sources and detail.
- Then build with `vs build <deck> --mode reading`, look at the contact sheets in `shots_reading/`
  and resolve overflow by shortening `read` or splitting the slide, never by shrinking type. The
  build names the slides that still show raw notes; it is done when that line is gone.

For the live version:
- **`notes` on every slide**, written from `read`: short full sentences, the numbers and names,
  the transition to the next slide.
- **Thin the slots**: the title and one piece of evidence stay; sentences that repeat what will be
  said go. If thinning would damage the reading version, split the page into a live slide and a
  slide marked `"only": "reading"` instead.
- **Split** pages that carry more than one idea; add `step` only where the explanation needs
  pacing; mark reference pages `"only": "reading"`.
- Choose the features for the occasion as in step 2 of vs-create (motion, quiz, timer) and confirm
  them with the user.

Record in `brief` which version is the main one and who the other was made for, so a later session
knows why both exist.
