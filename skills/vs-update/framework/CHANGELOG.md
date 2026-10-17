# Changelog

## 0.9.13
- The plugin carries its display name, VibeUpSlides, for the plugin directory; nothing changes in the skills or the framework.

For brand libraries made with an earlier version:
- Nothing to do.

## 0.9.12
- The sample texts of all masters, of the styles' own masters (manifest, schimmer, laut, horizont), of the style gallery and of the examples in the references are generic placeholders that say what belongs in each slot; no sample tells a story of its own any more.

For brand libraries made with an earlier version:
- Nothing to do. A library keeps the sample texts it was built with; `vs.py preview <brand>` shows them as they are.

## 0.9.11
- The credit line on the last slide has a place of its own in **manifest**, **schimmer**, **laut** and **horizont** and reads at 4.5 to 1: in manifest at the foot of the black band under the contact details, in schimmer under the floating labels, in laut at the top right across from the arrow, in horizont on a small label of the paper colour over the sky. Before, it lay on the contact details or the thanks, or faded into the ground.
- A long statement in **manifest** (three lines and more) opens its lines so the capitals no longer lie into each other; a short one keeps the poster look. In **laut** a longer title on the cover and the closing breaks into two lines that stand above the foot; a short one still runs off it.
- The legibility check measures how close to the edge the letters are drawn, not their line box, so tight display type at the top of a slide is no longer reported as cut. A display line that runs off the slide on purpose carries `vs-bleed` and is left out of that check. Masters with `"prepare": "display"` get `_wrap_<slot>` (more than one line) and `_long_<slot>` (three lines) to set a longer line differently.

For brand libraries made with an earlier version:
- A library made from manifest, schimmer, laut or horizont takes the fixed masters and theme with `vs.py design <brand> --style <style>` again (this starts the look anew from the style), or keeps its own; `vs.py refresh` builds its decks again.

## 0.9.10
- A tenth style, **horizont** (Horizon), elegant and warm like a culture magazine on screen: a fine serif (Newsreader) set large on white, short notes in a clean grotesque (Instrument Sans), a spectral arc of light over the cover, a vivid evening horizon with a lake and a small figure behind chapters and the closing, half slides in deep green or glowing ember, thin rules, plus signs, a sparkle and a brush stroke. The lights are small soft pictures; in the dark scheme the arc glows on night and the horizon turns to dusk, by the same rule.
- Masters of its own: `cover` (the name inside the arc), `statement`, `chapter` (an outlined pill, the title in two lines with a small underlined word between, a brush stroke), `closing`, `split` (a green or ember field with the photo in it, white app cards floating over it and a call to action in an outlined pill; on white a title in serif capitals over a rule, a sparkle with notes, a black chip, a photo card), `kpis` beside a field of ember, `cards` as a band of coloured tiles along the foot, and a new one, `mission`: lines of serif set flush right with small photos inside them like words and short notes beside them.
- Its own moves in `motion.css`: the arc breathes, the horizon drifts, the ember flickers, the sparkle turns, the plus signs twinkle, photos in the sentence open, the pill drops in, the brush stroke is drawn, the tiles rise from the foot. Transform and opacity only; export, motion off and reduced motion show everything at rest.
- A style may now bring sample photos (`styles/<name>/images/`): they are copied into the library's `samples/` and shown only in the samples of its masters (`brand:samples/…`), never as the brand's photos. Horizont brings seven from Unsplash, credited in `CREDITS.md`.

For brand libraries made with an earlier version:
- Nothing to do. A library that wants the new look starts from the style: `vs.py design <brand> --style horizont`.

## 0.9.9
- A ninth style, **laut** (Loud), loud and self-assured like a streetwear campaign: violet, a hot red-orange and powder pink in flat fields, heavy tight capitals (Inter Tight 800) that run off the edge, a giant word in a darker tone behind the text, a flared serif (Gloock) for small lines, an asterisk, a striped sun and round chips, all under one still print grain. Light slides turn violet in the dark scheme, by the same rule.
- Masters of its own: `cover` and `closing` (a giant word behind, a paragraph in red capitals over it, the title in pink from edge to edge running off the foot), `statement` (a paragraph in big red capitals on pink, a serif line, a giant asterisk turning in the back), `chapter` (the name huge, the number giant in pink behind), `kpis` on violet, `cards` as flat fields with a number chip, and a new one, `frame`: a photo in a red frame with a question over it and a year set upright, a red band with the answer and a button.
- Its own moves in `motion.css`: the giant word drifts, the title rises from the edge it runs off, asterisks pop in and turn, the arrow chip slides in and nudges, the sun rolls in, the upright figure slides up. Transform and opacity only; export, motion off and reduced motion show everything at rest.

For brand libraries made with an earlier version:
- Nothing to do. A library that wants the new look starts from the style: `vs.py design <brand> --style laut`.

## 0.9.8
- An eighth style, **schimmer** (Shimmer), calm and a little playful like a product launch: night slides lit by a ribbon of light in coral and magenta, light slides with the same light as a soft wash rising from the floor, Inter in bold, small labels in JetBrains Mono that fly in and float. The light is the main theme on every slide; only slides dense with text, a table, an agenda or a team show it through frosted glass at the right edge. Light and dark scheme follow the same rule.
- Masters of its own: `cover` with floating labels, `statement`, `chapter`, `kpis` as results (figures that count up, notes in floating bubbles, a name tag that flies in like a cursor), `cards` that step down with icons, `progress` (a score as rounded columns, the one that counts in the accent), `goals` (cards hanging from a line), `closing`.
- A style may bring its own `motion.css` (here: drifting light, flying and floating labels, the cursor, growing columns); `vs.py design` copies it into the library. Only transform and opacity move, the light is a small soft picture: smooth on a projector. Export, motion off and reduced motion show everything at rest.
- Photos lit like the night slides: a brand whose `shape.photo` is `glow` gets its photos in black and white, darkened, with soft light of its colours (`shape.glow`) laid in when the deck is built; nothing is mixed while presenting.

For brand libraries made with an earlier version:
- Nothing to do. A library that wants the new look starts from the style: `vs.py design <brand> --style schimmer`.

## 0.9.7
- A seventh style, **manifest** (Manifesto), after a poster series in red, black and cream: towering condensed capitals (Anton) beside a classic serif in italics (DM Serif Display) and a tight grotesque in small capitals for everything else (Inter Tight); hard colour bands, a ruler and a frame like an instrument with a wireframe sphere, a four-pointed star, a plus, a grain like print. Its motion set is `rise`, smooth and short.
- The style brings masters of its own: `cover` and `closing` in three bands with the title from edge to edge, `statement` like a poster with a side column (a stacked figure, a red line, a red box) and a foot line, `chapter` with the number in the serif on a black panel, `kpis` on black, `big_number` as a red panel with the reading of an instrument beside it, `cards` as numbered rows, and two new ones: `claim_panel` (a claim with a photo set into its first line, a figure, two reasons) and `services` (an upright word, serif capitals, a red strip with the offers). Every other master takes the look through the theme: on light slides the title stands on a red band that runs to the top and both edges.
- Where lines overlap on purpose (the serif laid over the capitals), the serif always lies on top; such lines carry `vs-overlap`, and the legibility check no longer reports them as texts on top of each other.
- A style may bring masters of its own (`styles/<name>/masters/`); `vs.py design` copies them into the new library, where they take the place of the framework's.
- Photos in a coarse print screen: a brand whose `shape.photo` is `halftone` gets every photo of its decks as dots of its ink colour on its paper colour when the deck is built.
- A display line as large as its box is wide: `class="vs-fill"` (with `data-max`, `data-min`, `data-lines`) sets the size in the browser, the way a poster sets its word from edge to edge. The `display` prepare step works out sizes and whether the accent word closes a line (`_tail_title`, `_tail_text`, `_tail_lead`), and the first word apart from the rest (`_head`, `_rest`).
- A brand can name a third typeface, `fonts.serif` (family, fallback), beside body and head; it is fetched with the others and reaches the theme as `--font-serif`. A style's footer may say `$name`: the name of the library.
- Coloured areas that fill their part of a slide on purpose carry `band` and are left out of the overflow check.
- The big chapter number counts up again at full size: the rules of the column chart (`.mcol`) had shrunk it to a sliver on every brand since 0.9.0.

For brand libraries made with an earlier version:
- Nothing to do; `vs.py refresh` builds the decks again with the chapter number fixed. A library that wants the new look starts from the style: `vs.py design <brand> --style manifest`.

## 0.9.6
- The six built-in styles build a deck of stock masters without a legibility finding: the credit line on an accent slide is set in the full text colour (bold where the accent leaves less than 4.5 to 1), the accent of **leicht** and **werkstatt** is a shade darker, and the marked word in a **plakat** title takes the text colour that belongs on the accent.

For brand libraries made with an earlier version:
- A library made from leicht or werkstatt keeps its accent; `vs.py set <brand> colors.accent=#586BDA` (leicht) or `#BC5419` (werkstatt) takes the new one. `vs.py refresh` builds the decks again with the credit line fixed.

## 0.9.5
- Every presentation carries its editing, also one whose main version is the reading version and the second file `build --mode` writes; only handouts (which leave slides out), previews and samples do not.


## 0.9.4
- The reading version shows the pencil too: pressing it (or E) opens the version to present at the same slide with the editing on. Before, editing was simply missing in the reading version.


## 0.9.3
- `venn`: what all circles share is filled in the accent colour, and the shared word stands inside it (two short lines with three circles, three with two); a longer word is set in a box over the middle. The circles overlap a little more, so the middle has room.
- `cycle`: the whole ring stands out on any ground (a tone of the text colour instead of the light surface colour), the accent arc on top of it.

For brand libraries made with an earlier version:
- Copy the masters `venn` and `cycle` again and give them the brand's look.

## 0.9.2
- Every question to the user goes through the question tool (options to click, the recommended one first), in all four skills.
- Diagrams build up the way they are explained: `venn` circle by circle with its point of the list and the shared word last; `spectrum` the scale first, then each mark where it stands on the line (it no longer travels in with the motion set); `cycle` station by station with its point; `matrix` the axes, then the fields one by one.
- Every deck folder has the same parts, `sources/`, `research/`, `images/` and `assets/`, and a `README.md` the build writes (what the deck is, its files, how to open it and go on). `vs.py handover <deck>` (or `--brand <name>`) writes one tidy folder for the user; in Cowork this folder goes into the connected folder instead of single files.

For brand libraries made with an earlier version:
- Copy the masters `venn`, `spectrum`, `cycle` and `matrix` again and give them the brand's look.

## 0.9.1
- Icons from an svg sprite: the analysis reads the symbols a site keeps in a sprite, also one its script loads afterwards (the site of a large IT services company: 159 icons and 5 arrows), each drawn once with the site's own colours.
- Text in the accent colour on dark ground (dark slides, the dark scheme, key D) is a tone light enough to read (contrast 4.5:1 instead of 2:1). A brand whose `accent_on_deep` is too dark is told so.
- `venn`: the names stand in the middle of the part of each circle that is its own, the shared word in the middle of what all share.
- `spectrum`: the scale comes first, then the marks one by one.
- The sample texts of the masters are neutral.

For brand libraries made with an earlier version:
- Copy the masters `venn` and `spectrum` again and give them the brand's look.
- Build the preview again: dark slides and the dark scheme may show new legibility findings where the theme puts the accent text on a light box inside a dark slide (for example `.dark .kicker{background:var(--paper);color:var(--accent-text)}`); use `--accent` or `--ink` there.
- If the website keeps its icons in a sprite and the library has none: `vs.py analyze <url> --brand <name> --again` reads them. It drafts brand.json anew (style guide, theme and masters stay), so keep a copy of brand.json and carry the confirmed values over.

## 0.9.1
- The legibility check looks at every slide in the dark scheme as well (key D, `?scheme=dark`), in `vs.py preview` and `vs.py build`. What only one scheme shows is labelled (`LEGIBILITY slide 4 (…): dark scheme: contrast 2.1 to 1 …`); what both show is named once. Slides that are dark, accent or photo slides look the same in both and are measured once.
- The check measures the drawn parts of a slide too: rings, arrows, bars, points, lines in figures and lines drawn in CSS (borders, `::before`, `::after`) that hardly stand out from their ground: below 1.5 to 1 and without a clearly different colour (a strong lime on white stands out, a pale mint on cream does not). A hairline of up to 2 px or a line in `--line`, `--soft` or `--ghost` may stay quiet and only counts when it vanishes (below 1.15 to 1). An element marked `data-quiet` or `ghost` is left out, as with text.

For brand libraries made with an earlier version:
- Run `vs.py preview <brand>` once and correct what it now names: usually an accent colour that is too pale for rings, bullets and bars on paper, or marks in a fixed colour on the dark ground (draw them in `--accent-text`, `--ink` or `--line` so that they follow the scheme).

## 0.9.0
- The project is called **VibeUpSlides** now. The plugin is `vibeupslides`, the repository `mfoureyes/vibeupslides`, the workspace `~/vibeupslides` (`VIBEUPSLIDES_HOME`), the Cowork backup `vibeupslides-workspace.zip`. The skills keep their names (`vs-build`, `vs-create`, `vs-design`, `vs-update`), and so does `vs.py`.
- The click steps of a slide in an order of their own: `"order": [3, [1, 2]]` shows step 3 first and steps 1 and 2 together on the next click; an entry with a 0 puts steps on the slide from the start. In the editing panel "Order" numbers the steps, the parts are clicked in the new order, with Shift to join one to the step before.
- Parts: a block that recurs inside slides of different forms (a band with the conclusion, a contact box) becomes a part of the brand, `parts/<name>.html`. A build says when it sees one (`FORMS: block K of slide N recurs …`); `vs.py forms <brand> --part <name> --from <deck> --slide N --block K` makes it a part and puts `"parts"` on every slide holding it. Blocks that several of the brand's masters hold word for word become one part with `--from-master <master> --block K`, used in the masters as `{{>part <name>}}`. `vs.py masters <brand>` lists the parts.
- "For all presentations" in the editing panel, on a slide the brand's decks share: what the user changes there goes into the library once the texts are corrected (`vs.py shared <brand> push --from <deck> --slide N`), and the other decks that use it are named for one question whether to update them. The agent checks the other decks only when something shared changed.
- The set `sweep` shows the title of cover, chapter and photo slides while its shape still sweeps (after about 0.6 s instead of more than 1 s).
- Four more masters: `venn` (two or three fields and what they share), `spectrum` (where things stand between two poles), `waterfall` (how one figure becomes another) and `share` (parts of a whole as a ring).
- The motion set copied from a website takes over the site's own keyframes where it plays its entrances as keyframe animations: the real ways, scale, blur and intermediate steps, with the animation's duration and easing.

For brand libraries made with an earlier version:
- Move the workspace from `~/vibeslides` to `~/vibeupslides` (or set `VIBEUPSLIDES_HOME`). A backup named `vibeslides-workspace.zip` is still restored.
- Copy the masters `venn`, `spectrum`, `waterfall` and `share` into the library and give them the brand's look.
- Run `vs.py analyze <url> --brand <name> --again` once if the brand's `site` set should take over the website's keyframes.

## 0.8.6
- A fourth skill, **vs-design**, for people without a brand who need a good presentation soon. It develops a look from examples the user likes: `vs.py design --examine <files, addresses>` photographs slides and web pages and measures their colours, the agent reads the rest from the pictures, and `vs.py design <name> --style <nearest> --ground … --ink … --accent … --head … --body … --radius …` makes a look of the user's own, with a full set of colours mixed and checked for legibility. Without examples there are six styles of vibeupslides' own to choose from (grid, magazine, night, workshop, poster, light). `vs.py design --gallery [--with <name>]` shows looks side by side on the same six slides. The look grows with corrections, further examples and the decks that are built; `design.md` in the library keeps every decision.
- The header band of the verdict columns reads in a dark look as well.
- Five more masters: `matrix` (four fields along two questions), `funnel` (many become few), `pyramid` (what rests on what), `before_after` (two states set against each other) and `hub` (one thing and what belongs to it).
- A brand's library grows with its decks: the brand remembers the form of every slide that was written freely, a build says when such a form comes up again (`FORMS:`), and `vs.py forms <brand> --promote <deck> --slide N --name <name>` makes it a master that every deck of the brand uses, so that a change reaches all of them. `vs.py forms <brand>` lists the brand's own forms and who uses them.
- `vs.py ingest` reads presentations that exist as HTML: every slide is photographed in the browser and read like the pages of a PDF, with its words. A plain web page is cut into screens.
- Editing a presentation in its own file is complete: "Text field" adds a field the slide does not use yet (the build leaves the slide once more with each such field), and a copied quiz or timer slide works at once. Editing belongs to the version to present; the reading version shows no pencil.

For brand libraries made with an earlier version:
- Copy the masters `matrix`, `funnel`, `pyramid`, `before_after` and `hub` into the library and give them the brand's look.

## 0.8.5
- Slides fill their area: where the body of a content slide ends well above the footer, everything below the title is enlarged by up to 40 percent, as far as it still fits. `"fit": false` on a slide or the deck keeps the sizes.
- An animation of the website that works as a transition between slides or as an entrance is taken into the brand's motion, so that every deck moves like the site.
- Five new masters for what lists do badly: `cycle` (a loop of stations), `flow` (boxes joined by arrows), `stairs` (stages that build on each other), `compare` (one figure against bars) and `tiles` (things that each have a picture).
- A presentation the user is happy with is the model for a brand's masters, ahead of the website: the onboarding asks for it, takes an inventory of its slide forms and matches each one, compared side by side. Decks are written to the density of the user's own slides and choose the form from what a slide says.
- The catalogue of animated scenes is taken out. Decks move through the brand's motion set; scenes come back once there is a structured way to use them. The onboarding no longer offers a gallery of scenes, a build no longer asks for scenes in a deck, and the master `scene` is no longer among the masters a brand gets or a deck is offered.

For brand libraries made with an earlier version:
- Copy the masters `cycle`, `flow`, `stairs`, `compare` and `tiles` into the library and give them the brand's look. Build the preview again and look at every master: bodies are larger now where a slide was half empty.
- Delete `masters/scene.html` from the library (it shows an empty box in the preview) and `"scenes"` from brand.json. A deck that used a scene of the catalogue shows a placeholder on that slide: replace the slide.

## 0.8.4
- The master preview introduces itself: three slides at its start, built from the brand's own masters, say what the file is, which keys there are, what comes next and what a presentation can do (`vs.py preview <brand> --no-intro` leaves them out). On every master slide a line above the slide says what the master is for. The numbers of the master slides in the preview move up by three.
- The motion sets side by side on a presentation's own slides: `vs.py motion --deck <deck> --compare` writes `shots/motion.html`. A presentation can move in another set than its brand (`"motion_set"` in the deck file, `vs.py motion --deck <deck> --set <name>`, `--set brand` goes back) and at its own strength (`--level`).
- How a single slide moves can be set in the deck and in the editing panel: `"step": true` lets any slide build up click by click (the rows of its blocks in reading order, the first stands with the slide; blocks in one row one by one), `"step": false` lets a slide with click steps arrive as a whole, `"move"` is `calm`, `expressive` or `off` for this slide alone. The panel has "On click", the strength of movement and "Play", which shows the slide's animation with its steps.

## 0.8.3
- Editing a presentation in its own file shows everything at once: a slide moved, copied or deleted stands in its new place right away (it was only marked until the changes were applied), the copy can be edited like any slide, and Undo and Redo take each step back and forth.
- List items can be moved, copied and removed in the file, with the small bar beside the text, as with the local server.
- "New slide" works in the file: the build leaves one slide per master and language in the page (masters that need no picture, film or script), and `vs.py apply` adds the same slide to the deck file.
- The line that credits the maker stays on the last slide when the order changes.
- The backup is smaller: it leaves out the screenshots of the website (`raw/screens`), which `vs.py analyze <url> --brand <name> --again` takes again.
- A change made on a slide the brand's decks share stays in this deck and is set up properly: the deck takes that field from the shared slide first, so the other language keeps its text. The page says that the slide is shared, and the `REVIEW` line tells the agent to ask whether the change should hold for every deck.

## 0.8.2
- The scenes the user chose for a brand are part of its decks: a build says so while a deck of four or more slides uses none of them, and the skill plans them in without being asked.
- The main subject of a picture belongs in the middle of its frame: the guidance says so for masters and decks, and the check points out heads cut by a frame's edge and people standing at the edge of a picture.
- An animated pattern of a brand's website becomes a scene of the brand, shown in its gallery with the catalogue's scenes. `vs.py scenes <brand> --export <name>` packs such a scene as a file to pass it on.

## 0.8.1
- The ring around the marked number of a column chart is as wide as the number needs; it ran through wide numbers.
- No text over a face: every build and master preview finds faces in photos that lie behind text and reports a text or number that covers one as a fault. A slide's `"focus"` says which part of its photo stays in view.
- The onboarding designs more freely and from the website: it takes an inventory of the site's own patterns (how pictures are shown, grids, list rows, figures) and gives each a place in the library, with its movement. Things only a visitor can operate (plus and arrow circles, "read more", tabs) stay out.
- The examples in the catalogue of scenes speak of VibeUpSlides and vibeup, and the gallery plays every scene with its example in the brand's colours. `tools/scene_posters.py` makes the stills again.
- The backup leaves out the master preview, which is built again from the library.

For brand libraries made with an earlier version:
- Run `vs.py preview <brand>`: remove buttons without a function from the masters, clear what covers a face, and look at the website once more for patterns the library does not carry yet.

## 0.8.0
- The onboarding leads the user through it: the route is said at the start, every question says where they are, and each decision of theirs comes with something to look at. New among them: the animated scenes, on one page that shows the whole catalogue and plays each scene on a click (`vs.py scenes <brand> --gallery`, `--choose a,b,c`), and the basics every deck needs (facts and shared slides).
- The catalogue of scenes is made to grow: scenes that fit any brand are offered to every user, scenes bound to one motif (`"showcase": false`) stay as models for a brand's own scenes, and an update that brings new scenes says so and marks them in the gallery.
- A language can be added later without rebuilding anything: `vs.py langs --brand <name> --add fr` for the brand, `vs.py langs <deck> --add fr` for a deck, which lists every text to translate; a build names texts that lack one of the deck's languages.
- The last slide credits the person who made the deck: "Made by …, with a little help from VibeUpSlides by vibeup.berlin" (`author` in the deck file, the brand's default from brand.json; `"credit": false` leaves it out).
- Every deck has a research report, `research/report.md`, written from the conversation in the user's language, so that another deck on the topic can be made from it; a build reminds of it while it is missing.
- `vs.py refresh --check` lists the decks that are behind their brand (shared slides and facts, look, framework), so that the user can be asked, when a deck is finished, whether the others should be brought up to date; `vs.py refresh` then builds exactly those.

For brand libraries made with an earlier version:
- Run `vs.py scenes <brand> --gallery` and let the user choose; set the brand's `author`; collect the brand's facts with `vs.py shared <brand> fact …`.

## 0.7.4
- No slide goes out with a mistake unnoticed: a text the user typed is unchecked until it has been corrected. The page marks it in yellow on the slide and counts the unchecked texts next to the pencil; a build ends with `NOT FINISHED` while any is left. With "Keep text as it is" the user releases a text themselves; it is then translated and not corrected.

## 0.7.3
- Editing shows what happens to a text: the browser's spell check is on while typing, the panel says where a change was saved and how many changes wait for correction and translation, and the deck built afterwards lists, when the pencil is opened, what was taken over as it was, what was corrected (old and new wording) and into which languages it was translated.

## 0.7.2
- Saving while editing asks for a folder once, not once per deck: name the folder your presentations are in, and this deck and later ones below it save into their own files without the question.
- A build says when a deck has no English version, and the skill adds it without asking.

## 0.7.1
- Editing without a local server, for Cowork and everywhere else: every built deck carries its own editing, opened with the pencil. The user types into the slides, writes notes and reader text, moves, copies and deletes slides (marked until applied), undoes and redoes. In Chrome and Edge they name the deck's folder once; from then on every change is saved at once into the presentation file itself, which shows it wherever it is opened, and into `<deck>.edits.json`. `vs.py apply <deck> <file>` brings the changes into deck.json, builds the deck and lists what to correct and translate; changes applied before are skipped.
- A new deck always has an English version next to the brand's languages.
- The brand's button is a call to action with a real link (`button: {label, url}` on the closing slide, `a.vs-btn`), not a decoration of the cover.
- Running text under 24 px is pointed out as a hint.

## 0.7.0
- Every build and every master preview now checks that all text can be read: type under 18 px, too little contrast between a text and what is behind it (measured on the rendered slide, so photos and gradients count), text cut off by its box, text at the edge of the slide and texts on top of each other are named by slide (`LEGIBILITY slide 4 (…): …`). A deck with such a finding is not finished.
- The default masters no longer set labels, table heads and small notes under 18 px.
- The motion of the website can be taken over: the analysis copies the way the site's elements arrive (fade, rise, slide, scale, focus, mask, with the measured timing) into a set of the brand's own, `site`, which plays next to the framework's sets on the comparison page. Choosing between the copy and a VibeUpSlides set is a step of the onboarding the user takes. `vs.py motion <brand> --site` makes the copy again.
- Every deck folder has the same parts: `sources/` for what the user supplied, `research/` for what was found out, `images/`. `vs.py new <deck> --from <other>` starts a deck from an earlier one and takes its sources and research along.
- What a brand's decks share lives once in the library: shared slides (`{"shared": "team"}`) and facts (`{{fact.address}}`). `vs.py shared <brand>` lists them and who uses them, makes a deck's slide a shared one and sets facts; `vs.py refresh` builds every deck that uses them again after a change and keeps the files from before.

For brand libraries made with an earlier version:
- Run `vs.py preview <brand>` and correct what the legibility line names in the brand's masters and `theme.css`: raise type under 18 px, set small labels in a colour with enough contrast. Numerals that only decorate take `var(--ghost)`; an element that is pale on purpose gets `data-quiet`.

## 0.6.3
- Cowork with a connected folder: VibeUpSlides keeps running in the cloud session, and the user's brands and decks are kept as one file, `vibeupslides-workspace.zip`, in the folder they connected, next to the built decks. The backup has one name, so the newest replaces the one before, and leaves out contact sheets, which a build makes again.
- A workspace inside a folder of the user is no longer called temporary. `doctor` tells writing from deleting, which such folders may forbid, and names the missing system library when the browser does not start.

## 0.6.2
- Cowork in the cloud, where a session sees no folder of the user: the workspace is set up in the session and says that it is temporary. `vs.py backup` writes brands and decks into one file for the user to keep, `vs.py restore <file>` brings them back, and the setup restores an uploaded backup by itself. The same file passes a brand on to someone else.
- Such sessions are recognised (they were taken for the user's own computer), `doctor` no longer claims that the user's browser can be opened or reaches the local server there, and reports where files for the user go.
- The skills say how to find the setup script when a plugin keeps it in another place.

## 0.6.1
- The descriptions of vs-build and vs-create are shortened to the 1024 characters a plugin allows; installing the plugin in Cowork failed on them.

## 0.6.0
- First step towards Cowork: VibeUpSlides installs as a plugin, and in a session that sees only folders the user shared the workspace is the folder `vibeupslides` inside one of them. The setup looks for it there, asks once where it should be when there is none, and keeps the Python environment outside that folder, so the same workspace works from Cowork and from the user's own computer.
- `vs.py doctor` reports in one run what an environment allows: folder, Python environment, browser, network, local server.
- The setup script records where the installed skills live on every run, so updates are found when that place changes; the three skills start with the same script.
- Setup goes on when the browser cannot be installed, and says so.

## 0.5.9
- The onboarding opens with what the slides are for instead of a question about permission, and asks for languages and font files in the same first message. Without font files an open typeface close in character is set without asking again. The purpose is recorded with the brand (`purpose` in brand.json) and decks refer to it: a sales deck or proposal is written from the customer's side, in their words.

## 0.5.8
- The brand's element library reaches the slides: the icons the website analysis saves can be set on the items of `cards`, `columns` and `steps` (`"icon": "energy"`), `vs.py elements <brand>` lists icons, arrows and shapes by the names a deck uses, and a name that is not in the library is reported instead of leaving a gap.
- The onboarding names the saved icons and records them in the style guide; nothing is drawn by hand to fill a gap.

For brand libraries made with an earlier version:
- `cards`, `columns`, `steps`: add `{{#icon}}<div class="vs-ic">{{>icon icon}}</div>{{/icon}}` before the title of an item (see the default masters).
- Run `vs.py elements <brand>`, rename the icon files so they say what they show, list them in the style guide.

## 0.5.7
- The editing panel is grouped and says what each button does: order of this slide (forward, back), this slide (duplicate, delete), insert (new slide, text field), for the slide (notes, reader text), history, Done. Every button explains itself on hover.
- The hint that text runs off the slide appeared on slides where nothing ran off: in a window that scales the slide by an odd factor, parts that stand exactly at the margin measured a fraction beyond it. The measure now allows for that, the hint shows only when two looks in a row agree (at once while typing) and clears itself.

## 0.5.6
- A hint shows where it applies: texts that run off the slide are outlined in orange and a dashed line shows the edge they cross; the text a voice finding is about is outlined as well.
- New in the editing panel: insert a new slide from one of the brand's masters (those that need no picture), filled with the master's sample text; add a text field the slide's master offers and the slide does not use yet (a label above the title, a lead); write the reader text of the slide next to its notes.

## 0.5.5
- Turning the slides while editing: with the cursor in a text, Page Up and Page Down always turn the slide, and an arrow key does when the cursor already stands at the end (forward) or the start (back) of the text; what was typed is saved first. The panel says how to leave a text.
- Done without anything to correct or translate simply closes the editing and shows the deck as before; the pencil opens it again. The server stops only when texts wait for the agent.

## 0.5.4
- After the editing, the texts the user changed are corrected (spelling, grammar, punctuation, without rewording) as well as translated. Every changed text is noted on its slide (`"edited"` in deck.json, formerly `"translate"`), also in a deck with one language; the command lists them as `REVIEW slide 3, bullets.2 ...`.
- Done tells the user that their changes are taken over and that the page opens again by itself. The page waits and reloads as soon as the editing is started again: `vs.py edit <deck> --reopen` (opens a browser page only if none is waiting). When nothing was changed, Done ends the editing for good.

## 0.5.3
- Notes can be written in the presenter view: click the notes, type, click elsewhere. They are saved into `deck.json` and stand on the slide from then on. This works whenever the deck comes from the local server, while editing (`vs.py edit`) and while presenting (`vs.py present`).
- Translation happens after the editing, not while typing: a text changed in one language leaves the other languages as they are and is noted on the slide (`"translate"` in deck.json). The page says so. The button Done ends the editing from the browser; the command then builds the deck and lists what is to be translated (`TRANSLATE slide 3, bullets.2 ...`), and the agent translates it in the brand's voice. No translator command, no login.

## 0.5.2
- The editing lives in the deck's button bar: an edit button (pencil, key E) opens and closes it, its controls open above the bar. Closed, the deck behaves as always, so a timer or a quiz can be tried while `vs.py edit` runs.
- Speaker notes can be written in the editing panel.
- What breaks the brand's voice is said in the language of the page.

## 0.5.1
- Editing mode: `vs.py edit <deck>` opens the deck in the browser with its texts open for typing. Click a title, a bullet, a card or a label and write; Enter saves, Escape discards. Every change is written into `deck.json` in the language that is shown, never into the built HTML, so both languages, the reading version and the PDF follow.
- In the same mode: move a list item or a card up and down, duplicate or remove it (the small bar beside the text that has the focus, in every language's list at once); move the slide earlier or later, duplicate or delete it; undo and redo (buttons, or Cmd/Ctrl+Z).
- While typing the page warns when the text runs off the slide; after saving it names what breaks the brand's voice rules.
- The version before every change is kept in `<deck>/.history/`. Stopping the server (Ctrl-C) builds the deck with the changes and prints the usual report.
- Not editable in this first stage: text that a helper or a built-in master draws (charts, bars, verdict columns, timer, quiz), speaker notes and reader texts, slots that are still empty, images.

## 0.5.0
- The skills have new names that say what they do: **vs-build** builds a brand (formerly vs-style), **vs-create** creates presentations (formerly vs-build), vs-update stays. The commands of `vs.py` are unchanged; `vs.py build <deck>` still builds a deck.
- Voice profile: how a company writes is now part of its brand library. `vs.py voice <brand> [files...]` measures the company's own texts (website, documents that were read in, sample texts the user names) per language: address, sentence length, frequent words, candidates for fixed terms. It drafts `voice.md`, the profile every deck is written from, and rules in `brand.json` under `voice`.
- Every build checks every slide against the brand's voice rules and names what breaks one, by slide and slot: the address (Sie or du and the like), sentences that are too long, fixed terms written differently, words the brand avoids, the gender form in German, exclamation marks. `"voice": false` on a slide leaves text alone that is taken over word for word. `vs.py voice <brand> --check "text"` tries a single wording.
- The preview checks the masters' sample texts in the same way.
- A new brand gets its voice profile drafted during `analyze`; the style guide's Voice section points to it.

For installations made with an earlier version:
- Install the skill set again and remove the leftover skill folder `vs-style`; the folder `vs-build` now holds the brand skill, `vs-create` the deck skill.

For brand libraries made with an earlier version:
- Run `vs.py voice <brand>` once: it writes `voice.md` and drafts the rules. Move the Voice section of `styleguide.md` into `voice.md`, complete the sections that are new (ten real sentences, before and after), correct the rules and confirm them with the user.
- `terms`: add `"voice": false` to the sample, legal text is not the brand's voice.

## 0.4.3
- Video slides show the film as large as possible and uncovered: `video` is the video alone, as large as the slide and in its own shape, with no title; `video_title` sets one line of title above the video and gives the video all the room below. Nothing lies on the picture any more.
- `video_title` is always black, whatever the brand's colours are, with the video centred under a centred title.

## 0.4.2
- Entrances read like the slide: the blocks of every slide enter row by row from top to bottom, and what stands side by side in a row comes together, with one clear beat per row. The engine works the order out from where the blocks stand; `data-wave` and `data-seq` say it differently where the content asks for it. Masters that mark no block get their content marked by the engine.
- `summary`, `profile`, `reference` and `requirements` mark all their parts; requirements stand first, the answers follow. The callout of a chart appears when the chart stands.
- `phases`: every phase comes as a whole column that fills from top to bottom, the first with the slide, the others on forward presses.
- New master `video_title`: the video fills the whole slide, the title lies over its top.
- Brands with several languages (`langs` in brand.json): the preview is built in all of them and switches with L, sample texts can be written per language, new decks start with the brand's languages.

For brand libraries made with an earlier version:
- `summary`: `anim` on the blocks of context and facts. `profile`: `anim` on main and side (side with `data-wave="2"`). `reference`: `anim` and `data-wave="2"` on the side. `requirements`: `anim` on need, arrow and answer instead of the row, arrow and answer with `data-wave="2"`. `steps`: `data-seq` on the container.
- `phases`: take the cells from the default master (`anim` for the first phase, `f` for the others, `--r` per row, `.vs-ph .f.on{transition-delay:calc(var(--r,0)*var(--mb))}`).
- Set `langs` in brand.json and write the samples per language if the brand presents in more than one.

## 0.4.1
- Builds are triggered by the presenter: `phases` shows one phase (its whole column) per forward press, `timeline` one bar per press and the milestones last; the first part stands with the slide. `"step": false` lets a slide build by itself, `"step": true` on a `figure` with columns makes every column a press.
- Click steps can be grouped and ordered: elements with the same `data-o` appear together, the numbers give the order.
- The figure of `big_number` counts up from 0, fast and never longer than three seconds.
- The ring on a marked column is centred on its number exactly.
- Every boxed media slide (`video`, `embed`, `scene`) has a box in the shape of a video, 16:9.
- Photos lose a thin plain edge when they are embedded, so no white line shows on dark slides.
- The first run after an update repairs the launcher and switches to the workspace's own Python.

For brand libraries made with an earlier version:
- `big_number`: wrap the value in `<span class="mcountup">`.
- `phases`: default `"step": true`; the head cells and the cells of every phase but the first get `f` and `data-o="{{@i}}"` (see the default master), plus `.vs-ph .f{transform:none}`.
- `timeline`: default `"step": true`; bars get `{{#step}}{{^@first}} f{{/@first}}{{/step}}` and `data-o="{{@i}}"`, milestones `{{#step}} f{{/step}}` and `data-o="99"`.

## 0.4.0
- One file, both versions: every deck carries the live and the reading version. The key V or the button LIVE / READ shows the other one at the same slide, the export button offers the PDF of either. `vs.py build --mode` still writes a second file that opens in the other version.
- New switches in the button bar and on the keyboard: A turns the animations off and on, D switches between light and dark slides (`"scheme": "dark"` in deck.json or brand.json makes dark the start).
- Charts build up: the `figure` master draws a column chart from numbers (`columns`, `mark`) whose columns come up from left to right; the `timeline` master builds its bars along time, then the milestones.
- A video behind the text: `chapter`, `cover_photo`, `fullbleed` and `statement_photo` take a slot `video` that plays silently in a loop while the slide is shown.
- Videos are never cropped: a `video` slide shows the whole frame, and in the boxed layout the box takes the shape of the video (slot `ratio` for shapes other than 16:9).
- The website's own video files are saved into the brand library (`videos/`, during `analyze` and with `vs.py videos <brand>`); the one that runs behind the page is marked as background.
- `vs.py motion <brand> --compare` writes one self-contained page on which all motion sets play the same slides side by side, for the user to choose from.
- The onboarding asks more before it builds: use, base, imagery, graphic elements, voice, motion, must-haves.
- The launcher switches to the workspace's own Python reliably; before, `python3 vs.py` could run without the installed packages.

For brand libraries made with an earlier version (their masters are copies and do not change by themselves):
- `figure`: copy the new default body, or add the `columns` branch (`{{>columns columns}}`, class `vs-fig-cols`) and scope the ring rule to `.vs-fig-img>i`; give the sample `columns` and `mark` instead of an image.
- `timeline`: add `mgantt` to `.vs-tl`, `mgbar` and `--s`/`--p` to the bars, `mgpoint` and `--s` to the milestones, and take `anim` off the rows.
- `chapter`, `cover_photo`, `fullbleed`, `statement_photo`: add `{{>bgvideo}}` (inside the photo layer, or first in the section) and the slot `video`.
- `video`: nothing to change in the body; set the sample's `src` to `@video`.
- Run `vs.py videos <brand>` once, then `vs.py preview <brand>` and look at it with D (dark) and V (reading).

## 0.3.0
- Onboarding reads documents the user already has: style guide PDFs, PowerPoint masters, logos and fonts (`vs.py ingest`).
- Motion belongs to the brand: eight motion sets, a motion profile per brand, the website's own motion is measured, intensity per deck (`vs.py motion`).
- Video from local files, YouTube, Vimeo and other players; embeds; 26 animated scenes as a slide type (`vs.py scenes`).
- Decks with media are folders: `vs.py present` serves a deck locally, `vs.py pack` zips it for sending.
- Two versions of every deck: a main mode (live or reading) and the other one on request (`vs.py build --mode`), with reader texts, contents page and section bar.
- Deck planning rests on researched structures for eight kinds of decks; `vs.py titles` prints the titles in a row, the build reports words per slide.
- 18 new master slides for proposals, consulting decks, people and proof, keynotes.
- Brands without a motion profile now get the calm set `rise`; the earlier look is the set `sweep`.

## 0.2.0
- The skill is now a set of three: vs-style (brand library), vs-build (decks), vs-update (updates).
- One workspace folder (`~/vibeupslides`) with framework, library and decks, and one command for everything: `vs.py`.
- Decks are a content file (`deck.json`) rendered through master slides; a build takes seconds.
- Every brand has its own master slides, a brand stylesheet (`theme.css`), saved icons, arrows and shapes, and one style guide.
- The website analysis records buttons, cards, labels, image treatment, icons, arrows and graphic elements.
- Typefaces are classified by licence situation; files of unclear origin wait for the user's confirmation.
- Before each build the framework checks whether it is current.

## 0.1.0
- First version: one skill, brand profile from a website, decks from generator scripts.
