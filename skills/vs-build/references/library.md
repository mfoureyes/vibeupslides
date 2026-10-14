# Building the brand library

The analysis measures, you judge. Its draft is right about most things and wrong about a few, and
which few differs from site to site. The library is finished when the owner has seen the preview
and said it looks and sounds like them.

## What the analysis leaves in `library/<brand>/`

| File | Content |
|---|---|
| `brand.json` | draft tokens: colours, typefaces, shape, logos, footer, elements |
| `logos/` | every logo candidate as file and as screenshot (`*_shot.png`), the favicon as `icon.*` |
| `fonts/`, `fonts/pending/`, `fonts/inbox/` | embedded files, files waiting for the user's confirmation, the folder for files the user supplies |
| `images/` | up to twelve large photos from the site |
| `videos/` | the site's own video files (plain mp4 or webm up to 60 MB, at most three) with a still each; `brand.json` lists them under `videos` and marks the one that runs silently behind the page as `background` |
| `elements/icons`, `arrows`, `shapes` | the site's inline SVG icons, arrows and decorative shapes |
| `raw/screens/` | `home.png`, `home_full.png`, further pages, `components/*.png` (not in a backup: after a restore `vs analyze <url> --brand <name> --again` takes them again) |
| `raw/logo_candidates.png`, `raw/elements.png` | contact sheets |
| `raw/components.json` | measured styles of buttons, cards, labels, headings, images, sections, shapes, lists, arrows |
| `raw/copy.md` | titles, headings, navigation, button labels and paragraphs per page |
| `raw/voice.json`, `voice.md` | how the site writes, measured per language, and the drafted voice profile; `brand.json` gets drafted rules under `voice` |
| `raw/extract.json` | all measurements, `census` (most used colours), `notes` |
| `masters/`, `theme.css`, `styleguide.md` | copies of the default masters, an empty theme, the style guide draft |

Read the `NOTE:` lines of the run; they name what the heuristics were unsure about.

## Tokens (`brand.json`)

**Colours.** `accent` is the one colour the brand uses for buttons, links and highlights. If the
draft picked a colour from a widget, a photo or a secondary palette, take the right one from
`census.accent_candidates` in `raw/extract.json` or from the screenshot. `deep` is the dark surface
for cover and chapter slides: a dark tone the site actually shows (hero, footer); if it has none, a
darker shade of `ink`. `on_accent` and `on_deep` must read clearly on their surface. `muted`, `line`,
`soft`, `ghost` are derived from ink and paper and rarely need a change.

A light accent (yellow, lime, pale blue) cannot carry titles and labels on a light slide; the build
darkens it for text. Better: set `colors.accent_text` to a second brand colour that reads on paper,
if the site has one (`colors.accent_on_deep` is the same for dark slides). A site with a dark
background gives a dark `paper` and a light `ink`: that is correct, keep it.

**Logo.** Pick the candidate that is the brand's own mark, complete and legible. Customer and
partner logos are flagged `wall`; a home icon or a decorative graphic is not a logo. If the SVG
renders with empty margins or tiny, use its `_shot.png` or run `vs logo trim <brand>`. For dark
slides: set `logos.primary_inverse` if the site shows a light version; `vs logo inverse <brand>`
makes a white one from a one-colour logo; otherwise leave `inverse_mode` at `"plate"` (the logo
sits on a small paper-coloured plate). A parent or partner organisation that must be on every slide
goes into `logos.partner` (left) next to the brand (right).

**Typefaces.** Covered by step 4 of the skill. `fonts.body.family` and `fonts.head.family` must be
the families you see in the screenshot; `display_weight` is the weight of the largest headings,
`head_weight` that of normal ones, and both must exist among the embedded files.

**Shape.** `radius` is the corner radius of cards, buttons and images in px, as the site shows it.
`motif` is the accent shape on cover, chapter and statement slides: `"wedge"` (diagonal), `"block"`
(straight panel), `"none"`. Choose from what the site looks like. Anything more specific than these
three (a circle, a brand pattern, a cut corner) is done in `theme.css`, with `motif` set to `"none"`.
`head_case` is `"uppercase"` only if the site sets headlines in capitals; `head_tracking` its
letter spacing (`"-0.02em"`), `null` keeps the engine's values.

```json
{
  "name": "Example", "url": "https://example.com", "lang": "en", "langs": ["en"], "confirmed": false,
  "colors": {"accent": "#D50C2F", "on_accent": "#FFFFFF", "ink": "#2B2B2D", "deep": "#2B2B2D", "on_deep": "#FFFFFF",
             "muted": "#6B6F73", "line": "#C4C5C7", "soft": "#F2F2F3", "ghost": "#E9E9EA", "paper": "#FFFFFF"},
  "fonts": {"body": {"family": "Inter", "fallback": "Arial, Helvetica, sans-serif"},
            "head": {"family": "Archivo", "fallback": "Arial, Helvetica, sans-serif"},
            "files": [{"family": "Inter", "weight": "100 900", "style": "normal", "file": "fonts/inter.woff2"}],
            "pending": [], "families": [{"family": "Inter", "roles": ["body"], "source": "google", "licence": "open", "status": "embedded"}],
            "display_weight": 900, "head_weight": 700},
  "shape": {"radius": 8, "motif": "wedge", "head_case": "none", "head_tracking": null, "logo_position": "right"},
  "logos": {"primary": "logos/logo.svg", "primary_inverse": "logos/logo_white.png", "partner": null, "partner_inverse": null,
            "icon": "logos/icon.png", "inverse_mode": "file"},
  "footer": {"left": "", "right": "example.com"},
  "elements": {"icons": ["elements/icons/i01.svg"], "arrows": ["elements/arrows/a01.svg"], "shapes": [], "arrow_glyph": "→", "icon_style": "line"},
  "images": [{"file": "images/photo_01.jpg", "source": "https://example.com/..."}]
}
```

`vs show <brand>` prints the profile with contrast warnings.

## The style guide (`styleguide.md`)

One file, the brand's memory for design. vs-create reads it before every deck, so write it for a
designer who has never seen the website. How the brand writes has its own file, `voice.md`. Fill the draft section by section:

- **Essence.** Three sentences: what kind of organisation, what the design feels like, and the one
  visual idea a slide must carry to be recognisably theirs. Everything else follows from this.
- **Colour, type, layout and shape.** Not the values (they are in `brand.json`) but the use: which
  colour carries large areas, how much accent, size contrast between headline and text, alignment,
  density, edges, shadows.
- **Imagery.** What is shown and how it is photographed; then the treatment as the site applies it:
  crop and aspect ratio, corner radius, overlays, tint or duotone, masks, frames, how text sits on
  images. Then one line per file in `images/`: what it shows and which master suits it. Delete
  files that are not usable (banners with text baked in, third-party logos, decorative backgrounds)
  and remove them from `brand.json`.
- **Icons and arrows.** Line or filled, stroke weight, corners; which saved files are the brand's
  icons; where arrows appear and in which form. The saved files are the brand's **element library**
  (`vs elements <brand>` lists it): look at every icon in `raw/elements.png`, rename each file so the
  part after its number says what it shows (`icon_03.svg` becomes `icon_03_energy.svg`), and list the
  names with their meaning in this section, because decks use icons by that name (`"icon":
  "energy"` on cards, columns and steps). Never draw an icon, an arrow or a shape yourself to fill a
  gap: what the website does not show is left out, or the user supplies the file (into
  `elements/icons/`, `arrows/` or `shapes/` as SVG). A shape you approximate by hand is not theirs. Delete saved elements that are not the brand's
  (social media marks, cookie tool icons).
- **Graphic elements.** Shapes, patterns, rules, gradients, large numerals: what exists, where the
  site uses it, where a slide should.
- **Components.** The label above headings, buttons and chips, cards, lists, tables: each as one
  line a designer could rebuild from, with the values from `raw/components.json`.
- **Voice.** One line that names the languages and points to `voice.md`. The profile itself and
  the rules a build checks are written as `voice.md` describes in this folder of references.
- **Masters.** One line per master: what was changed from the default and why, which were added,
  and which master to prefer for which content. vs-create chooses masters from this list.
- **Open points.** What the user still has to supply or decide (font files, a light logo, photos).

Write in the language the brand writes in. Only what the site shows goes in; do not invent a
tagline, values or rules it does not state.

## The brand stylesheet (`theme.css`)

Loaded after the engine and after the tokens. This is where a deck stops looking like a template.
Work through what you saw, component by component, and restyle the engine's classes
(`references/masters.md` lists them):

| On the website | In `theme.css` |
|---|---|
| the small label above headings (pill, leading line, tracking, case) | `.kicker` |
| headline manner (case, tracking, tight leading, how a word is highlighted: colour, underline, marker) | `h1, h2`, `h1 em, h2 em` |
| cards (border or shadow, radius, padding, accent edge) | `.card`, `.card.accent`, `.card.muted` |
| buttons and chips | `.chip`, `.badge`; `a.vs-btn` for the button as a call to action (closing slide, never a cover) |
| image treatment (radius, tint, overlay, frame, mask) | `.split .image img`, `.gallery figure`, `.fullbleed .image`, `.cover .photo img`, `.person .pic` |
| bullets and arrows | `ul.bullets li::before`, your own `.arrow` |
| rules, dividers, patterns, the accent shape | `.wedge`, `.kpis`, `.agenda .row`, backgrounds on `.slide.dark` |
| large numerals, step circles | `.ghost`, `.card .n`, `.step .n`, `.kpi .w` |

Rules:

- Colours only as tokens: `var(--accent)`, `var(--accent-text)` (accent used as text), `var(--on)`
  (text on the current dark or accent surface), `var(--ink)`, `var(--deep)`, `var(--on-deep)`,
  `var(--on-accent)`, `var(--muted)`, `var(--line)`, `var(--soft)`, `var(--ghost)`, `var(--paper)`;
  corners `var(--radius)`; fonts `var(--font)`, `var(--font-head)`; weights `var(--w-display)`, `var(--w-head)`.
- Saved elements are embedded with `url(el:arrows/arrow.svg)` (path below `elements/`), for
  instance as a mask so they take a token colour:
  `ul.bullets li::before{background:var(--accent);-webkit-mask:url(el:arrows/a01.svg) center/contain no-repeat;mask:url(el:arrows/a01.svg) center/contain no-repeat;width:22px;height:22px;top:12px}`
- Body text stays at 27 px or larger on the 1920 px slide. Do not shrink type to fit a look.
- The accent stays an accent: at most about a fifth of a slide, unless the website itself is
  flooded with its brand colour.
- A new animation rests in its finished state (the start lives only in the `from` keyframe), so
  PDF export and previews stay clean.
- Keep it to what the site shows. A theme is not the place for your own ideas.

## Checking the result

After `vs preview <brand>` look at the contact sheets next to `raw/screens/home.png` and ask:
same colour balance, same typographic voice, same edges and shadows, same way of treating
pictures, do the brand's arrows and icons appear where the site would put them, does the sample
text sound like `raw/copy.md`. Then the hard cases: logo on dark and on accent slides, a long
title on cover and chapter, the accent word in a title on paper and on dark, photos with the
brand's treatment. The overflow line of the preview must say `clean`, and so must the legibility
line: it measures every text of every master (size, contrast to what is behind it, cut off, at the
edge, on top of another text) and every drawn mark (ring, arrow, bar, point, line: at least 1.5 to 1
to its ground or a clearly different colour; a hairline or a line in `--line`, `--soft`, `--ghost` only when it vanishes), in the
light and in the dark scheme, and names what fails (`dark scheme: …` for what only one scheme shows). Correct the master or `theme.css` until
nothing is left; a brand colour that is too pale for text is used for surfaces and marks, not for
words, and small labels are set in the text colour.
