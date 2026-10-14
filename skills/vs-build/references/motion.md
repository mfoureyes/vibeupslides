# Motion: how a brand moves

Motion is part of the brand, like colour and type. The framework only says *where* something may
move (the hooks in the masters) and *when* (the order on a slide). *How* it moves is decided here,
once per brand, in three layers:

| Layer | Where | What it decides |
|---|---|---|
| Motion set | `brand.json` → `motion.set` | the idea of movement, applied to every hook |
| Motion tokens | `brand.json` → `motion.ease`, `duration`, `stagger`, `travel`, `change` | the brand's tempo and distances |
| Signature move | `motion.css` in the brand folder (optional) | one or two moves only this brand has |

A deck then chooses how much of it plays (`"motion"` in `deck.json`: `"off"`, `"calm"`,
`"standard"`, `"expressive"`); that is vs-create's decision per occasion and does not change the set.

You cannot watch an animation. Work from two things instead: the measurements in
`raw/motion.json`, and film strips (`vs.py motion <brand> --strip`), which show a set as a row of
frames. Never choose a set from its name alone. The user can watch: `vs.py motion <brand> --compare`
writes `preview/motion/compare.html`, all sets playing the same slides side by side. Narrow the
choice with the strips, then let the user pick from that page.

## The profile in brand.json

```json
"motion": {"set": "rise", "ease": "cubic-bezier(.22,.61,.36,1)", "duration": 0.6, "stagger": 0.09, "travel": 24, "change": "fade"}
```

| Field | Meaning | Range |
|---|---|---|
| `set` | name of the motion set | see `vs.py motion <brand>` |
| `ease` | easing of entrances, a CSS timing function | `cubic-bezier(...)`, `ease-out`, `linear`, `steps(n,end)` |
| `duration` | base duration of one entrance in seconds; larger moves take a multiple of it | 0.35 to 1.2 |
| `stagger` | delay between siblings (cards, bullets, rows) in seconds | 0 to 0.25 |
| `travel` | distance an element covers on its way in, in slide pixels (the slide is 1920 wide) | 0 to 80 |
| `change` | how one slide follows the next: `slide`, `fade` or `none` (cut) | |

Every field but `set` is optional: a field that is missing takes the set's own value. Write only
what you measured or decided, so the set keeps its character.

## The sets

`vs.py motion <brand>` prints the current list with one line of character each. At the time of
writing:

| Set | Idea | Fits |
|---|---|---|
| `rise` | fade and short rise, quiet, one after the other | calm corporate brands; the default |
| `soft` | scale and soft blur, things come into focus | soft, friendly, rounded brands |
| `sweep` | the accent shape sweeps across at its own angle, words rise out of a mask | brands with a strong graphic shape and hard edges |
| `mask` | straight masks open over text and pictures, nothing travels | editorial brands, large quiet type |
| `draw` | a rule is drawn, the content unrolls from it, numbers tick | technical brands, grids and hairlines |
| `cascade` | pieces drop in one after the other and settle with a small bounce | lively, playful brands |
| `cut` | hard cuts and steps, no easing, words flash in the accent colour | loud, poster-like brands |
| `none` | nothing moves | documents, formal reports |

## Reading raw/motion.json

The analysis opens the site, counts what it finds and scrolls through it once more to see what
changes. Read the file in this order:

1. `amount`: `none`, `hover only`, `little`, `some`, `much`. This is the first fact for the style
   guide and the ceiling for the brand: a site that does not move does not get a loud set.
2. `scroll_reveal`: elements below the fold, compared before and after they were scrolled into
   view. `kinds` counts what happened: `fade` (opacity), `rise` or `drop` (vertical travel),
   `slide` (sideways), `scale`, `blur`, `mask` (a clip or a line rising out of a cut-off parent).
   `distance_px`, `duration_s`, `easing` and `stagger_s` are the measured values; `driven_by` says
   whether CSS or a script moves the elements (with a script the easing is unknown and the
   duration was measured by watching, `measured_by_watching_s`). `waiting` much larger than
   `revealed` is normal: closed menus and carousel slides also wait.
3. `transitions`: durations and easings of all elements that carry a transition, weighted by how
   many elements use them. These are mostly interface transitions (hover, menus): they are shorter
   than an entrance on a slide. The most frequent easing that is not plain `ease` is the brand's
   curve.
4. `animations.in_use`: keyframe animations running on the page, with `does` (what the keyframes
   change) and `kind` (`entrance`, `loop`, `marquee`, `spinner or loader`). Ignore spinners.
5. `hover`: what changed on up to three buttons and three cards (colour only, or does the element
   lift, does the image zoom, does an arrow move). This tells you how physical the brand is.
6. `marquees`, `background_video`, `libraries`, `canvas_elements`, `smooth_scroll`: signs of a site
   that stages itself. GSAP, Lenis, Lottie, Three.js or a marquee mean someone designed motion
   on purpose; look at the site's screenshots and copy for what it wants to feel like.
7. `suggestion`: the drafted profile with `why` and `measured` (which tokens come from the site).
   It is a draft made by simple rules. Check it against the points above and against the brand.

## Choosing the set

Decide from behaviour first, character second, and write the reason into the style guide.

- **The site reveals with masks or clipped lines** → `mask`. Typical for editorial sites.
- **The site scales or blurs things in**, or it only fades and its shapes are round (radius 14 px
  and more, pills, soft shadows) → `soft`.
- **The site fades and rises** by a short distance → `rise`, with the measured distance, duration
  and easing as tokens.
- **Long distances, overshooting easings** (a `cubic-bezier` with a value above 1), staggered
  groups, marquees → `cascade`.
- **Stepped timing, instant state changes, blinking cursors, huge type on flat colour** → `cut`.
- **Line drawings, stroke animations, diagrams that build up, grid lines** → `draw`.
- **A strong accent shape** in the brand (a diagonal, a bar, a block that also appears in
  `shape.motif`) and a confident tone → `sweep`. The sweep leans as far as `--m-skew` says
  (22% of the slide width by default, 0% with the motif `block`); set it in `motion.css` to the
  angle of the brand's own shape.

**When the site has no motion** (`amount` is `none` or `hover only`): keep the drafted `rise` with
the set's own tokens and `change: fade`. Do not read missing motion as permission to pick
anything. Only the brand's character may move you one step: a strictly typographic, editorial
identity may take `mask`; a brand whose documents are formal throughout may take `none`. Say in
the style guide that the site does not move and that the choice comes from the design.

**When site and character disagree** (a playful brand with a static site, a law firm whose agency
added a marquee): the character of the brand wins over a single effect, but never choose a louder
set than the site's `amount` supports without asking the user.

The occasion is not your concern here. A brand with `cascade` can still give a quiet board
presentation: vs-create sets `"motion": "calm"` for that deck.

## Choosing the tokens

- `ease`: the easing measured on reveals; if there is none, the most frequent easing of the
  site's transitions that is not plain `ease`. Keep the set's own easing when the site offers only
  `ease` and `linear`. `cut` and `draw` bring their own timing; leave `ease` out for them.
- `duration`: the measured reveal duration. If only interface transitions were measured, take
  about twice their typical value (0.2 s on buttons becomes about 0.45 s on a slide). People in a
  room need longer than a reader at a screen; below 0.35 s an entrance reads as a flicker.
- `stagger`: the measured step between siblings, otherwise the set's own.
- `travel`: the measured distance for `rise` and `cascade`. A site that fades without travel gets
  about 10.
- `change`: `fade` for most brands, `slide` when the site itself moves sideways (carousels, page
  transitions), `none` for `cut` and `none`.

Set single values with `vs.py set <brand> motion.duration=0.55`; `vs.py motion <brand> --reset`
drops all tokens again.

## A signature move: motion.css

A signature move is one movement that belongs to this brand alone and that people would recognise
without the logo: the way its shape enters, how its accent word arrives, a rule that draws before
every kicker. Write `motion.css` only when the site (or the brand's films and guidelines) shows
such a move and the chosen set does not already do it. One or two moves; a brand whose every
element has its own trick has none.

`motion.css` lies next to `theme.css` and is loaded after the set. The simplest way is to redefine
the keyframes of one role; the framework keeps the timing and the order.

```css
/* on chapter slides the accent shape comes down from the top edge, as the banner does on the website */
@keyframes m-wipe { from { translate: 0 -100%; } }
/* the sweep leans like the brand's own diagonal */
.slide { --m-skew: 12%; }
```

Roles: `m-item` (elements with `anim`, bar rows), `m-title` (h1, chapter titles), `m-label`
(kicker, lead, attribution), `m-word` and `m-accent` (words and accent word of an `mtext`
heading), `m-shape` (accent shape), `m-wipe` (its large move on chapter slides), `m-logo` (big
logo), `m-numeral` and `m-roll` (chapter numeral and its reels), `m-figure` (large numbers),
`m-drift` (slow movement of a full-bleed photo), `m-bar`, `m-mark` (quotation mark), `m-photo`,
`m-rule` and `m-panel` (lower third), `m-sting` (logo intro).

Rules for everything you write there:

- **The resting state is the finished slide.** Put start values into the `from` keyframe and leave
  `to` out, so the element ends as its own styles say. A `to` is only allowed where it looks
  exactly like the resting state (`clip-path: inset(0)`). Animations fill backwards. PDF export,
  overviews and previews show slides at rest and must be right without special cases.
- Use `translate`, `scale` and `rotate` as separate properties in keyframes, not `transform`:
  many elements already carry a transform for their position.
- Use the tokens: `var(--md)` (duration), `var(--me)` (easing), `var(--mt)` (travel), `var(--ms)`
  (stagger); they already include the deck's intensity. Colours only through the brand tokens.
- Click steps (`.f`) may only differ in `opacity` and `transform` from their shown state.
- Bars must grow through `width` or `scale`, the numbers next to them follow the bar.
- Nothing loops, nothing moves for longer than about two seconds after the slide appeared (the
  slow drift of a full-bleed photo is the one exception).
- Movement for elements only this brand has (its own shapes in its own masters) also belongs
  here, written with the same tokens and the same idea as the set.

## The set copied from the website

`analyze` writes `motion/site.css` into the brand's library when the site shows how its elements
arrive: fading, rising, sliding, growing, coming into focus, uncovered by a mask, with the
measured duration, easing, stagger and distance. It is a motion set like the framework's, named
`site`, and plays wherever a set plays (`--strip site`, `--compare`, `--set site`). Its
description says what it rests on: elements watched while scrolling carry measured distances.
When the site plays its entrances as keyframe animations (Animate.css, its own `@keyframes`), the
set takes over those keyframes themselves (`frames` in `raw/motion.json`): their real ways, scale,
blur and intermediate steps, scaled from the site's width to the slide and held within bounds (a
third of the element, 90 px), with the animation's duration and easing. Only where no keyframes
can be read does it fall back to the framework's distances. It copies how
things enter, not everything a site does: scroll-linked effects, hover states, marquees and 3D
have no place on a slide. Correct the file by hand where a strip shows a flaw, with the tokens as
in any `motion.css`; `vs motion <brand> --site` writes it again from `raw/motion.json` and
overwrites such corrections. The user chooses between `site` and the framework's sets on the
comparison page; never decide that for them.

## Checking with the film strip

```bash
python3 ~/vibeupslides/vs.py motion <brand>                    # sets, the brand's profile, the site's suggestion
python3 ~/vibeupslides/vs.py motion <brand> --compare          # all sets playing side by side, a page for the user
python3 ~/vibeupslides/vs.py motion <brand> --strip            # film strip of the brand's set
python3 ~/vibeupslides/vs.py motion <brand> --strip all        # one strip per set, to compare
python3 ~/vibeupslides/vs.py motion <brand> --strip cascade --level calm
python3 ~/vibeupslides/vs.py motion <brand> --set mask         # save the choice
```

A strip (`preview/motion/strip_<set>.png`) has four rows (cover, chapter, bullets, figures) and
six frames each, taken at 0.1, 0.3, 0.6, 1.0, 1.6 and 3.0 seconds after the slide appeared, built
with the brand's own masters, theme and `motion.css`. Read it like this:

- **Last frame**: is it the finished slide, complete and in place? If not, a keyframe leaves
  something behind.
- **First frames**: is anything half visible that looks like a mistake (a title cut through the
  middle, a shape covering the text it should reveal, a word in the wrong colour)?
- **Order**: does the eye get the shape first, then the title, then the details? Is the title
  readable by 1.0 s on the cover? An audience waits for nothing longer than that.
- **Fit**: put the strip next to `raw/screens/home.png`. Would this movement surprise someone who
  knows the website? Compare with the neighbouring set (`rise` against `soft`, `mask` against
  `sweep`) before you decide.
- After writing `motion.css`, make the strip again and look at the rows the move touches.

Then rebuild the preview (`vs.py preview <brand>`), which must stay free of overflow, and note in
the style guide under Motion: what the site does (two sentences from `raw/motion.json`), the set
and the reason, the tokens and where they come from, the signature move if there is one, and which
intensity suits which occasion.
