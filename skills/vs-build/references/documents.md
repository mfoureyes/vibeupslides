# Documents the brand already has

A website shows how a brand looks on a screen. It rarely shows the things a slide needs most: the
layout grid, which slide types exist, how charts and tables are styled, the icon set, how much
space the logo wants, how the brand speaks. Those live in a style guide and in the slide master
people already present with. If such documents exist, read them before you write anything, so the
brand's masters follow them instead of being guessed from a home page.

## The best deck they have comes first

Ask for the presentation the user is happy with, by name, and read it before anything else. Its
slides are the model for the masters (`masters.md`, "A deck the user already has is the model"):
the forms it uses, how full its slides are, how large the type is, where diagrams replace lists. A
library that looks like the website but loses the good slides the company already has is a step
back for them, and they will say so.

## Ask once, at the start

Ask in the same message as the website question, so the user answers both in one go. Name the
kinds that help, because people do not think of a five-year-old PowerPoint as "brand material":

- a style guide or brand manual (PDF), also a one-page colour and type sheet
- the current slide master or a good recent deck (PowerPoint .pptx or .potx)
- logo files (SVG or PNG, also the white version), the brand's font files
- screenshots of anything else that shows the design

Ask how old each document is and whether it is still the valid one; you need that later to weigh
it. Keynote and Google Slides files cannot be read: ask for an export as PDF, and as PowerPoint if
the master matters. Having nothing is fine. Then the website is the only source and the six steps
run as usual. Do not ask again later; if a document turns up afterwards, ingest it then.

## Run the ingestion

```bash
vs ingest <brand> <file or folder> [more files ...]
```

It can run before or after `vs analyze`, and again whenever a document arrives; each document gets
its own folder and the index is rewritten. A PowerPoint file takes seconds, a long PDF up to a minute.

| In `library/<brand>/` | What it is |
|---|---|
| `sources/SOURCES.md` | the index: every document, what was found, where to look. Start here |
| `sources/<doc>/sheets/` | contact sheets of all pages or slides, in order |
| `sources/<doc>/pages/` | single PDF pages, large enough for small print (long PDFs: only pages that name colours or carry a design heading; `python3 framework/ingest.py pages <brand folder> <doc> 12,13` renders more) |
| `sources/<doc>/findings.md` | PDF: colour values with the label next to them, flat colours seen on the pages, typefaces named and embedded, page index. PowerPoint: theme colours and fonts, text styles of the master, every layout with its placeholders in a 1920-wide coordinate system, footer and slide-number conventions, media, density |
| `sources/<doc>/text.md`, `slides.md` | the words: per page, or per slide with layout name, title, body and speaker notes |
| `sources/<doc>/layouts/` | one drawing per slide layout: placeholders as labelled boxes, fixed elements in place |
| `sources/<doc>/images/`, `media/` | pictures embedded in the PDF, the media files of the deck, each with a contact sheet |
| `logos/`, `fonts/inbox/`, `sources/images/` | loose logo files, font files and screenshots the user passed in |

Font files only wait in `fonts/inbox/`. They still need the licence question of step 4 before
`vs fonts add` takes them over. Typefaces embedded inside a PowerPoint are not extracted; ask the
user for the files.

Without LibreOffice on the machine, PowerPoint slides are not rendered but drawn schematically from
their shapes: positions, pictures, fills and text are right, the typeface, exact text sizes,
effects, vector graphics (EMF) and charts are not. That is enough to judge composition and
density, not enough to judge the look. If the look of the old deck matters, ask the user to export
it as PDF and ingest that as well.

## What to look at first

Images before text, as with the website. Open `SOURCES.md`, then:

1. The style guide's contact sheets, all of them, for the overall system. Then the single pages
   for colour, type, logo, layout and imagery, and read their small print: minimum sizes, clear
   space, forbidden uses, tints. These rules are exactly what a website cannot tell you.
2. The layout sheet of the PowerPoint and the "Layouts (most used first)" list. The layouts that
   carry most slides are the slide types this brand actually works with.
3. The slide sheets, for density and habits: how much text sits on a slide, whether titles are
   statements or labels, how pictures, tables and logos are placed, what the footer carries.
4. `findings.md` for the exact values, and `text.md` or `slides.md` for the voice.

The findings are measured, their labels are guessed: a hex value is exact, but which name stands
beside it comes from the order of the text. Check each colour against the page image before it
goes into `brand.json`.

## When sources disagree

They will, because they were made at different times for different media. The order of trust
follows who decided what, and when:

- **A current official style guide outranks the website** for colours, typefaces, logo rules and
  tone of voice. It is the decision; the website is one application of it, often with compromises
  (a web-safe substitute font, a link blue the CMS brought along).
- **The website outranks an old slide master.** A relaunch usually reaches the site first and the
  PowerPoint template years later, if ever. Where the master shows other colours or typefaces
  than site and style guide, the master is what is out of date.
- **An existing slide master defines the slide types and the density**, even when its look is
  dated. People have built their talks around those layouts; a library that offers the same
  types, in the current look, feels like theirs from the first deck. Treat it as a strong hint
  for the brand's masters, not as a template to copy.
- A recent deck made by a designer counts more than the bare template for how the brand is
  really used. A style guide older than the last relaunch counts for little.

Print values need care: a colour given only as CMYK or Pantone has no single correct screen
value. Take the hex the guide names; if it names none, take the colour from the website and note it.

Where a conflict matters (two different accent colours, another typeface, a different logo), do
not choose silently. Show the user both, say where each comes from, and ask. A small difference
(two near-identical greys) you decide yourself and note in the style guide.

## Where the findings go

- **`brand.json`**: colour tokens from the style guide's named values; the typefaces it
  prescribes (then step 4 as usual); the logo files the user supplied in place of what the site
  offered; footer text and slide numbering as the master does it.
- **`styleguide.md`**: every section gains what the documents define: the rules for logo and
  imagery, the grid, chart and table style, the icon set. What the documents say about language
  (address, wording rules, terms) goes into `voice.md` and the voice rules; their running text is
  measured by `vs voice <brand>` together with the website. Write next to each statement where it comes from (style guide p. 12, slide master,
  website), and record open conflicts and the user's decisions. "Not defined on the site" becomes
  "not defined in any source" only if the documents are silent too.
- **`theme.css`**: what the documents show beyond tokens: label and bullet style, how tables and
  charts look, image crops and frames, rules and shapes. Rebuild them with tokens and CSS; take
  proportions from the placeholder geometry, which is given in the 1920-wide system the masters use.
- **`masters/`**: rework the defaults as in step 5, and add a master for each slide type the
  documents define and the defaults lack: the brand's profile, reference or contact slide, its
  agenda, its chapter divider, its way of showing three columns. Start with the most used layouts.
  Name the slots after what the placeholders hold and write the sample from the documents' own wording.

## What stays out

`sources/` is study material in the user's own library. Nothing in it is copied into a deck,
shipped, or passed on: no pages, no slide texts, no pictures from someone's old presentation.
Exceptions are the brand's own logo and its own photos or icons, when the user confirms they may
be used; those you copy deliberately into `logos/`, `images/` or `elements/`. Sample text in the
masters is written new, in the brand's voice, and never contains names, numbers or clients from
an ingested deck.
