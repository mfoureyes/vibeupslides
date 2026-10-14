# Pitfalls

Check here when a slide looks wrong or a build misbehaves.

## Content

- **Overflow.** The build names the slide and how far the content runs (`bottom` beyond 930,
  `right` beyond 1800). Shorten the text, drop a point or split the slide in two. Never shrink type.
- **A title runs into the accent shape** on a statement or cover: it is too long for that master.
  Shorten it or use a content master.
- **An accent word is invisible**: `<em>` sits where the accent shape or an accent surface is.
  Move the `<em>` to an earlier word.
- **A slot shows nothing**: the name is misspelt or the master has no such slot. `vs masters <brand>`
  lists the exact names.
- **Text looks cut off inside a card or table cell**: the legibility line reports it (`cut off by
  … px`). Shorten.
- **`covers a person's face in the photo`.** A text or a number lies over a face. Move the picture
  with the slide's `"focus"` (`"right"`, `"left top"`, `"30% 20%"`), take another photo or crop, or
  use a master that sets the text beside the picture. Never leave it, and do not darken the photo
  to hide it. Without a face detector the build says `text stands on a photo here`: look at the
  sheet yourself.
- **Legibility findings.** `contrast … between text and ground`: over a photo, take a calmer or
  darker picture, or a master that gives the text its own ground; an accent word on an accent or
  photo surface moves to another word; a pale brand colour used for words is a matter for the
  brand's `theme.css`. `type of … px`: the master sets it too small; raise it in the brand's
  master to 18 px or more, and tell the user if that changes the brand's masters. `at the edge` and
  `on top of each other`: the text is too long for its place or a master is misplaced; shorten or
  correct the master. The check does not see pictures of text and the dark mode of a deck.

## Images

- **"image not found"**: paths are relative to the deck folder (`images/x.jpg`) or start with
  `brand:` for the library (`brand:images/photo_01.jpg`).
- **The deck is heavy and pages slowly**: every image is embedded once per language. Keep photos
  around 2000 px wide and the whole deck under about 8 MB.
- **A QR code must be read back** from the built deck, not from the source file; embedding
  recompresses images.

## Deck file

- **"deck.json is not valid JSON"**: usually a trailing comma or an unescaped quote inside a text.
  Quotes inside a text are written `\"`.
- **Two languages out of step**: a slot has an entry for one language only. The other language
  then falls back to the first entry; the build does not warn. Check both sheets.
- **Timer or quiz does nothing in the room**: the deck was opened from an old file. Rebuild and
  open the new HTML.

## Brand

- **The logo is invisible on dark slides**, **type looks thin or generic**, **the accent is too
  pale for text**: these are library matters. Hand over to vs-build (`vs fonts <brand>`,
  `vs logo inverse <brand>`, `colors.accent_text`).
- **The deck looks like a template, not like the website**: the brand's masters and `theme.css`
  are still close to the defaults. That is vs-build, step 5.
- **The voice line reports the same thing on many slides**: the rule does not fit (a fixed term
  that is also an ordinary word, an avoided word inside a product name). Change the rule with
  vs-build (`vs set <brand> voice...`), do not bend the text. Texts that are not the brand's own
  words get `"voice": false` on their slide.
- **"this brand has no voice rules yet"**: the library was made before 0.5.0. `vs voice <brand>`
  measures its texts and drafts profile and rules; finishing them is vs-build.

## Presenting

- **The presenter view does not open**: Chrome blocks pop-ups once per file. Click the button in
  the panel the deck shows, or allow `file:///*` under `chrome://settings/content/popups`.
- **The audience sees the presenter view**: the projector is set to "mirror" instead of "extend".
- **No sound** on timer or quiz: the browser needs one click or key press in the deck first.
