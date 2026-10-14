# Master slides

A master is one HTML template in `library/<brand>/masters/`. A deck names a master per slide and
fills its slots; nobody writes slide HTML for a deck. The brand's masters are therefore where its
look lives, together with `theme.css`.

`vs masters <brand> --full` lists every master with slots and sample. Masters in the brand folder
win over framework masters of the same name. The built-in ones (`timer`, `quiz_choice`,
`quiz_true_false`, `quiz_estimate`, `logo_intro`, `raw`) are not templates; style them through
`theme.css` (classes `.tslide`, `.qslide`).

## File format

```html
<!--vs {"name": "cards", "order": 46,
        "use": "Two to four similar things as cards. At most one accent card.",
        "slots": {"kicker": "small label above the title (optional)",
                  "title": "the title as a full sentence, <em> marks the one accent word",
                  "cols": "2, 3 or 4",
                  "items": "list of {n, tag, title, text, style}; style is \"\", \"accent\" or \"muted\""},
        "defaults": {"cols": 3},
        "sample": {"kicker": "Our offer", "title": "Three ways to <em>start</em>", "cols": 3, "items": [...]}} -->
<section class="slide center" {{attrs}}>
  {{#kicker}}<div class="kicker">{{kicker}}</div>{{/kicker}}
  <h2>{{title}}</h2>
  <div class="cards c{{cols}}">
    {{#items}}<div class="card {{style}} anim">{{#n}}<div class="n">{{n}}</div>{{/n}}<h3>{{title}}</h3><p>{{text}}</p></div>{{/items}}
  </div>
  {{notes}}
</section>
```

The header is one JSON object in a `<!--vs ... -->` comment at the very top:

| Key | Meaning |
|---|---|
| `name` | the name decks use (default: the file name) |
| `order` | position in the preview and in the list |
| `use` | one or two sentences: what this master is for and its limits. vs-create picks masters by this |
| `slots` | every slot with a description of what goes in and how long it may be |
| `defaults` | slot values used when a deck leaves them out |
| `sample` | realistic content for the preview, written in the brand's voice and language |
| `full_images` | `true` for masters whose photo fills the slide (embedded at 1920 px instead of 1400) |
| `is_chapter` | `true`: the title becomes the chapter name in outline and footer |
| `handout` | `false`: left out of handout builds |

## Template tags

| Tag | Result |
|---|---|
| `{{title}}`, `{{item.text}}` | the slot value, inserted as HTML; empty when missing |
| `{{#items}} ... {{/items}}` | repeated for every item of a list; shown once if the slot is set; skipped if empty |
| `{{^photo}} ... {{/photo}}` | shown when the slot is missing or empty (placeholders) |
| `{{.}}` | the current item of a list of plain texts |
| `{{@i}}`, `{{@ii}}` | number of the current item: 1, 2 ... and 01, 02 ... |
| `{{#items.0}} ... {{/items.0}}` | shown once if the list has at least one item (for wrappers like `<ul>`) |
| `{{attrs}}` | required on the `<section>`: language, title, chapter and source of the slide |
| `{{notes}}` | required inside the section: the speaker notes |
| `{{#motion}} ... {{/motion}}` | shown unless the deck's motion is off (`"motion": false` or `"off"`); wrap the hook classes `mslide mtext` and the like in it |
| `{{lang}}`, `{{brand}}` | language of the slide, name of the brand |
| `{{>el arrows/a01.svg}}`, `{{>icon check}}` | inlines an SVG from `elements/` (the second from `elements/icons/check.svg`), class `el` |
| `{{>chapter_number number}}` | the rolling chapter numeral |
| `{{>bars rows}}` | counting figures with bars; rows are `{label, value, share}` |
| `{{>columns columns}}` | column chart that builds up from left to right; rows are `{label, value}`, the slide's `mark` names the column with the ring |
| `{{>bgvideo}}` | the slot `video` of the slide as a silent loop behind the text; write it inside the photo layer (`.image`, `.photo`) or first in the section. Empty without a video |
| `{{>chevron_fill stages}}` | process arrows that fill on click; stages are `{tag, title, text}` |
| `{{>line_chart axis series ymax}}` | animated line chart; series are `{values, color, labels}` |
| `{{>verdict columns}}` | columns with coloured header bands; columns are `{title, color, bullets}` |
| `{{>lower_third name role}}` | name strap for video slides |
| `{{>part takeaway}}` | a part of the brand (`parts/takeaway.html`), filled from the slots of the slide. A block that several of the brand's masters need is written once as a part, not copied into each: a change then reaches all of them (`vs forms <brand> --part <name> --from-master <master> --block K` does it for blocks already copied) |

Image slots: a deck gives a file path (`images/team.jpg` in the deck folder, `brand:images/photo_01.jpg`
from the library); the template uses the slot as `src`. Samples use the stand-ins `@photo`, `@tall`,
`@wide`, `@portrait`, `@logo`, `@logo_inv`, which the preview fills with the brand's own photos.
A `<style>` block inside a master is fine for rules only that master needs; scope them with a
class of your own so they do not leak.

## Writing a brand's masters

1. Start from the copied default and change what the website does differently: composition
   (where the title sits, how wide the text column is), the proportion of image to text, how
   numbers, steps and cards are shown, where the accent shape or the brand's own graphic appears.
   Shared details (label, card, bullet, image treatment) belong in `theme.css`, not in every master.
2. Add masters for what the brand needs and the defaults lack. Typical: a hero that follows the
   site's hero, a slide built around its characteristic card or icon row, a numbers slide in its
   manner, a section opener with its pattern. Give each a clear `use`.
3. Remove masters the brand should not use (delete the file; the framework default then still
   exists, so say in the style guide that it is not to be used).
4. Where the brand has icons, show them: the items of `cards`, `columns` and `steps` take `icon`
   (a name from `vs elements <brand>`), your own masters use `{{>icon name}}` inside a `.vs-ic` box.
   Give the samples of these masters the brand's real icons so the preview shows the library at work.
5. Rewrite every `sample` in the brand's voice and language, from the real sentences in `voice.md`
   and real offers on the site. `vs preview` reports samples that break a voice rule; a sample that
   is not the brand's own words (contract terms, a quote) carries `"voice": false`. Mark invented figures as samples in `source`.
6. Keep slots stable. If a deck already uses a master, add slots, do not rename them.

Limits that keep slides clean: content ends 150 px above the footer (930 px) and at 1800 px on the
right; titles are full sentences and get room for three lines on content slides; body text is at
least 27 px and no text under 18 px, labels and table heads included; text and its ground differ
by at least 4.5 to 1, from 24 px on (bold from 18 px) by 3 to 1; a ring, an arrow, a bar or a point by 1.5 to 1 or a clearly different colour;
at most one large movement per slide. `vs preview` reports overflow and legibility per master, in
the light and the dark scheme. Marks drawn in `--accent` or a fixed colour keep that colour on the
dark ground: draw them in `--accent-text`, `--ink` or `--line` where they must follow the scheme.
A numeral that only decorates takes `var(--ghost)` or the class `ghost`; an element that is pale on
purpose carries `data-quiet`; both are left out.

## A deck the user already has is the model

A company that hands you a presentation it is happy with has already solved most of what the
masters are for. The rule is the user's own: take what is good as it is, and do not make it worse.
A rough rebuild of a good slide is worse than no master.

1. **Inventory.** Go through the page images of the ingested deck (`sources/<name>/`) and list
   every slide form in `styleguide.md` as a table: the form (cover, chapter with number, loop
   diagram, timeline, programme grid with logos, case with photo …), the pages that show it, how
   often it is used, and the master it becomes. Forms used once for one argument are listed too.
2. **Match, do not approximate.** Build each form as a master that a viewer could not tell from the
   page: the same proportions and positions, the same number of elements, the same weights and
   type sizes relative to the slide (measure them on the page image; a 1920 px slide is the
   scale), the same use of colour, the same density of text. Start from the default master that is
   closest (`cycle`, `flow`, `stairs`, `compare`, `tiles`, `matrix`, `funnel`, `pyramid`,
   `before_after`, `hub`, `timeline`, `process`, `cards` …) and
   change it until it matches; where none is close, write a new one.
3. **Compare side by side.** Put the page image next to the master's contact sheet at the same
   size, form by form. Differences you can see are faults to fix, not style. Say openly which
   forms you could not match and why, and leave those slides to be taken over as pictures or
   rebuilt later, rather than shipping a weaker version.
4. **Then the website.** It fills what the deck does not have (icons, photo treatment, movement)
   and decides where the two disagree only if the user says the deck is outdated.

A master made from a slide of theirs keeps that slide's wording as its sample, so the preview
shows their own slides again and they can judge at a glance.

## Start from the website, not from the defaults

The default masters are a set to fall back on, not the design. A brand's slides should look as if
the people who made its website had made them. Be free: build what the site suggests.

**Take an inventory of the site.** Go through `raw/screens/home_full.png` and the page
screenshots from top to bottom and write down every pattern that gives the site its character:
how pictures are shown (framed like prints, tilted, with a caption strip, cut into shapes,
overlapping), the grid of projects, products or portfolio companies (picture, label, name, line),
the list rows (news, events, jobs: a date, a title, a rule between), the band of figures, the
hero, quotes, the footer. For each one decide which master carries it, and build a master of the
brand's own where no default does it justice. A photo treatment such as a polaroid frame is a
component in `theme.css` that every photo master uses, not a single slide. A list design from
the site makes the agenda, the contents and any list of the brand; a portfolio grid makes cards,
team and references. Record the inventory in the style guide as a table (pattern on the site →
master or component), and count the library as unfinished while a pattern that would serve slides
well has no place in it.

**Take the movement with the pattern.** If the site's photos drop in tilted, settle or fan out,
write that for the component in the brand's `motion.css`, with the tokens, so that pictures on
slides arrive the way they do on the site. The measured values are in `raw/motion.json`.

**What does not come along.** Things a visitor operates and an audience cannot: plus and arrow
circles that open something, "read more", tabs, carousel dots, form fields, cookie notes. On a
slide they are buttons without a function. Leave them out, however typical they look; a real link
with a target is the only exception (see Buttons).

**The main subject in the middle.** A picture is cropped so that what it is about (the people,
the product, the building) stands in the middle of its frame, whole, not at the edge and not cut
off. Check every photo master with the brand's own pictures, set the crop of the samples with
`"focus"`, and prefer a frame in the picture's own proportions over a crop that loses the subject.
The check points out heads cut by a frame's edge and people standing at the edge of a picture.

**The site's own animations become the deck's movement.** Where the website has an animation
that can serve a deck, take it over: how a page or a section changes (a wipe, a mask that opens, a
shape that sweeps across) becomes the change from slide to slide or the entrance of the chapter
slides; how headings, pictures and figures arrive becomes the entrance of the same parts on a
slide. The `site` set carries the entrances that were measured; what goes beyond it is written
into the brand's `motion.css` (`references/motion.md`), so that it applies to every deck by
itself. Show it to the user on the comparison page before it is the brand's set. Animations that
are a show of their own (3D objects, physics, long intros) stay on the website.

**Faces.** Where a photo lies behind text, no text and no number may cover a person's face. Place
the text of such a master where the brand's own pictures are free, and give the photo room to be
moved: a slide's `"focus"` (`"right"`, `"left top"`, `"30% 20%"`) says which part of the picture
stays in view. `vs preview` and every build find faces and report `covers a person's face in the
photo`; that is a fault like overflow. Solve it by moving the text or the picture, by another
crop, or by a master that sets text beside the photo instead of on it, never by a darker overlay.

## Classes and markup of the engine

The slide is 1920 by 1080 px. Header with logos, footer, page number and chapter name are added by
the engine; masters carry no logos.

**Surfaces and modifiers**

| Class or attribute | Effect |
|---|---|
| (none) | content slide on the paper colour |
| `dark` | deep surface, light text (`--on` is `--on-deep`) |
| `accent` | accent surface (`--on` is `--on-accent`) |
| `center` | centres short content vertically |
| `anim` on an element | a block that enters by itself when the slide appears, in the way of the brand's motion set. The engine orders the blocks of a slide by rows from top to bottom; blocks that stand side by side in a row come together |
| `data-wave="2"` on a block | it enters after all blocks of the first wave (answers after questions, a side column after the main one) |
| `data-seq` on a container | its blocks are a sequence: each is a beat of its own in the order of the markup, also side by side (steps 1, 2, 3) |
| `data-o="2"` on `f` elements | elements with the same number appear together as one step, and the numbers give the order of the steps (a column of a table, all milestones of a schedule) |
| `mcountup` on the element that holds a figure | a whole number counts up from 0 when the slide appears, fast and at most three seconds; other values simply stand |
| `f` on an element | click step, appears on the next key press. Never together with `anim` |
| `no-header`, `no-footer` | slide without logos or without footer |
| `<em>` inside `h1`/`h2` | the accent word of a title |
| `data-export="off"` | element is left out of the PDF export |

**Layout classes**

| Layout | Classes |
|---|---|
| Cover | `dark cover` or `accent cover` with `<div class="wedge"></div>`; photo version `cover withphoto` with `<div class="photo"><img></div>`; `.text` holds `.kicker`, `h1`, `.lead`, optional `.meta` (`div > small + text`) |
| Chapter | `dark chapter` or `accent chapter`, `<div class="wedge narrow"></div>`, `<div class="ghost">01</div>`, `.text` |
| Statement | `dark statement`, `.text > h2`, `.who` |
| Agenda | `agenda`, rows `.row` with `.n`, `.t` (`<small>` subline), `.z`; `current` marks one |
| Cards | `.cards c2|c3|c4` with `.card` (`.n`, `.m`, `h3`, `p`), `.card.accent`, `.card.muted` |
| Steps | `.steps` with `.step` (`.n`, `h3`, `p`), `.step.filled` |
| Key figures | `.kpis` with `.kpi` (`.w` value with `<small>` unit, `.b` label) |
| Columns | `.columns`, `.columns s3`, with `h3` and `ul.bullets` or `p` |
| Bullets | `ul.bullets`, plus `main` directly under a title |
| Photo and text | `split br` or `split bl` with `.image > img` and `.text` |
| Full bleed | `fullbleed` with `.image > img` and `.text` |
| Gallery | `.gallery g2|g3` with `figure > img + figcaption` (`<b>` title) |
| Team | `.team` with `.person` (`.pic > img`, `b`, `span`, `small`) |
| Chevron | `.chevron` with `.c` (`.m`, `h3`, `p`), `.c.current` |
| Table | `table.tab`, cells `.w` bold, `.z` accent |
| Quote | `quote` or `accent quote` with `.mark`, `h2`, `.who` |
| Exercise | `exercise` with `.badge` and `.frame` (content plus `aside > div > small + span`) |
| Small parts | `.kicker`, `.lead`, `.callout`, `.chip`, `.chip.accent`, `.badge`, `.placeholder`, `.ghost`, `.caption` |

**Motion hooks.** A master only marks where something may move; how it moves comes from the
brand's motion set, its tokens and its `motion.css` (see `motion.md`), and the deck's `motion`
field decides how much of it plays. Hooks on the section, always with `mslide`: `mcover` (cover:
accent shape, big logo, then the title), `mchap` with `.wedge.mwipe` (chapter: the large move of
the accent shape), `mcount` (chapter numeral, with `{{>chapter_number number}}`), `mstatement`,
`mquote` (quotation mark, quote, attribution), `mphoto` (the photo is revealed), `mkpi` (with
`bars`: numbers follow their bars), `mlt` (lower third). `mtext` on `h1`/`h2` splits the heading
into words so the set can move each one, the `<em>` word last. Hooks without `mslide`: `anim`
(entrance, staggered among siblings), `f` (click step), and for things that build along a time
axis `mgantt` on the container with `mgbar` on every bar (`style="--s:<first period>;--p:<periods>"`)
and `mgpoint` on every milestone (`--s:<period>`): bars are uncovered from left to right at an even
pace, the points follow. Anything that shows data should build in the order it is read: columns
and bars one after the other, a schedule along time, never all at once and never as a still image
when the numbers are at hand. With `shape.motif` set to `none` the accent
shape and its moves are absent. Do not write `animation` or `@keyframes` into a master or into
`theme.css`: movement that only this brand has goes into `motion.css`. A master's resting state is
the finished slide; nothing may be hidden by default and shown by an animation.

**An entrance reads like the slide.** Parts appear in the order in which the slide is read: row by
row from top to bottom, and what stands in one row comes together. Mark every part of the content
as a block (`anim`), not only some of them: a slide on which one row moves and the rest just stands
looks broken. A master that marks no block at all gets its parts below the title marked by the
engine (table rows one after the other, everything else as it stands in the section). Never stagger
the cells of one row, and never let a comment on a chart appear before the chart.

**Builds follow the logic of the content, and the presenter triggers them.** Anything that is told
in parts (the phases of an approach, the bars of a schedule, the stages of a process) appears part
by part on forward presses, in the order in which it is explained: phases as whole columns from
left to right, a schedule bar by bar and the milestones last. The first part comes with the slide,
so the slide is never empty. Give such a master the default `"step": true` and write
`{{#step}}{{^@first}} f{{/@first}}{{/step}}`, so a deck can switch the steps off with
`"step": false`. What is one statement (a single chart, a figure) builds by itself when the slide
appears. Never let parts of an explanation run off on a timer.

**A mark belongs to its number.** A ring, a box or an underline that points at a value is drawn on
the element that holds the value (a pseudo-element, centred with `left:50%;top:50%;translate:-50% -50%`
and `box-sizing:border-box`), never placed beside it by hand with pixel or percent offsets: only
then is the number in the middle whatever its width. On an image (`mark_x`, `mark_y` of `figure`)
the ring can only be set by eye; draw the chart from numbers instead whenever they are at hand.

**Film on black.** The video slides (`video`, `video_title`) are black in every brand, with the
film centred and nothing lying on it. Do not recolour them in `theme.css` or in a brand copy of
the master; the brand shows in the logo and in the accent word of the title.

**Pictures without borders.** Photos sit on the slide without frame, outline or rim, in the light
and in the dark scheme. The build cuts a thin plain edge off every photo (the white line that
exports leave); do not add borders in `theme.css`, and look at the photo slides once with D.

**Samples in the brand's languages.** When the brand presents in more than one language (`langs`
in `brand.json`, e.g. `["de", "en"]`, the first is the start language), write every sample text
per language: `"title": {"de": "...", "en": "..."}`, also inside lists and in `defaults` (labels).
The preview then switches with L like any deck, and new decks start with these languages. A text
written as a plain string serves every language.

**Dark slides.** Every deck can be switched to dark slides (key D): light slides then take the
deep colour through their tokens (`--paper`, `--ink`, `--muted`, `--line`, `--soft`, `--ghost`,
`--accent-text` are redefined on the slide), and the logo for dark ground is used. A master that
is written with the tokens follows by itself; a master with fixed colours (`#fff`, `black`) does
not. Check `preview.html` once with D before you show it.

**Things that go wrong**

- On `dark statement` or a cover the accent shape reaches far to the left. Limit the text width
  (`max-width:1000px`), otherwise a title runs into it and an accent word disappears.
- `.card`, `.person` and similar set dark text for light slides. On `dark` slides cards adapt; on
  `accent` slides set colours explicitly with `var(--on)`.
- A grid inside `.image` drops the second photo; use two absolutely positioned half-height divs.
- The order of `anim` blocks comes from where they stand on the slide, not from the markup: check a new master once by paging to it and watching in which order its rows arrive.
- Photo credits stand small in the corner of the image, not in the footer.
- **Buttons.** A website's hero carries a button because a visitor is meant to click on; an audience cannot. Do not copy it onto a cover, chapter or content master. The brand's button belongs where a deck asks for an action: the closing slide (slot `button`: `{label, url}`) and a call-to-action master if the brand needs one. It is a real link (`<a class="vs-btn" href="{{url}}" target="_blank" rel="noopener" onclick="event.stopPropagation()">`), shown only when it has a target, and it takes the look of the site's button from `theme.css` (`a.vs-btn{…}` from the measurements in `raw/components.json`: fill, text colour, radius, weight, padding).
- The overflow check cannot see text clipped by `overflow:hidden`; the legibility check reports it as cut off.
