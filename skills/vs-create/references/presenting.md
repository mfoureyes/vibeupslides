# Presenting, presenter view, export

## Keys

| Key | Action |
|---|---|
| → ↓ space PageDown Enter | next click step or slide |
| ← ↑ PageUp Backspace | back |
| Home, End | first, last slide |
| M | presenter view |
| S | swap deck and presenter view between the screens |
| F | full screen |
| G | outline with chapters |
| O | overview of all slides |
| N | notes panel in the deck |
| L | next language (decks with two languages); the presenter view has the same switch |
| A | animations on or off: off means everything stands, slides and click steps cut |
| D | dark or light slides: light slides take the brand's dark colour, slides that are already dark, coloured or a photo stay |
| V | the other version of the deck: live or reading, opened at the same slide |
| X | open or close all deepenings (slides left out of the short version) |
| P | PDF export of the version on screen, downloaded without a print dialogue |
| R | replay the animation of the slide; restart the video, reload the page |
| K | play or pause the video of the slide |
| T | start or pause the timer on a timer slide |
| A to D, 1 to 4 | choose a quiz answer; 0 resets |
| Esc | close a panel |

Swiping works on tablets. A click on the slide does not advance, so text can be selected.
Each slide has an address (`Deck.html#/7`); `?lang=en` forces a language, `?mode=reading` or
`?mode=live` the version, `?scheme=dark` dark slides, `?motion=off` a deck at rest. The button bar
appears only when the mouse really moves and hides after three seconds. It has a button for every
switch above; the export button offers the PDF of the live version and the PDF of the reading
version. The choices for animation and dark slides are remembered per deck in the browser.

## Video and embeds while presenting

- A video starts when its slide becomes current and is paused and rewound when the slide is left.
  **K** or a click on the video pauses and plays, **R** starts it again.
- Browsers allow sound only after a click or key press in the deck window. If the very first thing
  shown is a video, it starts muted and the deck says so; K turns the sound on. If even that is
  refused, the poster shows a play button.
- Players and websites are loaded only while their slide is current. Offline, a slide that
  needs the network shows its poster and a short message.
- The presenter view shows the poster, never a second player, with play/pause, restart and the
  running time for a video. The buttons drive what the room sees.

## Present over a local address

```bash
vs present <deck> [--port N] [--no-open]
```

Serves the deck folder on this computer only (`http://127.0.0.1:8787/<Title>.html`, another free
port if that one is taken), opens the browser and runs until Ctrl-C. Use it whenever the deck has a
YouTube video: YouTube refuses to play in a page opened as a file. It also helps the presenter view:
the browser remembers the pop-up and second-screen permission for this address, and full screen from
the presenter view works without the extra click. Nothing outside the deck folder is served and
nothing is reachable from other computers.

## Sending a deck with media

`vs pack <deck>` writes `decks/<deck>.zip`: the HTML files and everything they link (videos,
local pages). The receiver unpacks it and opens the HTML; the files must stay together. The
output says if the deck needs to be online when shown (remote video, websites). A deck without media needs no packing: its HTML file is the whole deck.

## Presenter view

Like the presenter view of PowerPoint or Keynote. **M** opens a second window for the laptop; the deck
itself goes full screen on the projector. The current slide stands in the middle and takes all the
room the other panels leave; Back and Next are at the top right, with the clicks still to come on
the slide. Around it four panels: the **schedule**, the **next slide**, the **notes** (A− A+; Full text
or Cues when the deck has talking points) and the
**film strip** with every slide of the deck. Each panel can be dragged by its header to another edge
(top, left, right, bottom), its size changed at its inner edge, two panels at one edge against each
other at the line between them; **View** hides panels, moves them and resets the layout. The layout
is kept in the browser. Timer, quiz and video controls appear under the slide when the slide has
them. All keys work in that window too.

**Time.** Opening the deck or the presenter view starts nothing: the schedule says Ready. The time
runs from the start of the talk, the first step forward from the first slide or the Start button;
the clock times of the plan count from that moment. Back on the first slide after a rehearsal, the
button **Reset time** sets it to Ready again (during the talk ↺ in the top bar, on a second click).
Reloading the deck keeps the time; after eight hours untouched it starts afresh.

- **With a plan** (`minutes` or `plan` in the deck, or a length typed into Target): the time left on
  the slide, green, yellow from 80 %, red with a plus when over; a bar of all slides sized by their
  plan, done slides green or red, chapter marks with the planned and the reached clock time; the
  yellow line is where the clock says you should be, the white one where you are; On time, over or
  ahead, and the expected end.
- **Without a plan** the time is measured: the bar grows with the time each slide took.
- **`event.start`** in the deck ("10:45") gives the plan its clock times before the talk starts.
- **Report** downloads a table (CSV): plan against actual per slide and per chapter, and every
  change of slide with its clock time.

**Film strip and deepenings.** The film strip shows every slide, also those left out of the talk
(grey, with the name of their deepening). A click goes to a slide and takes a skipped one in; the
box under a slide takes it into the talk or leaves it out without going there. When the deck runs
with `vs present` (or `vs edit`) the choice is saved into `deck.json`; opened as a file it holds in
this browser only, and the strip says so. When skipped slides follow the current one, a yellow button
next to Next takes them in and goes to the first; Next itself passes them by.

What to tell the user:

- **Projector on "extend", not "mirror".** Mirrored, the audience sees the presenter view.
- **Chrome or Edge.** They detect the second screen: the first M asks for the permission "window
  management", the deck then says to press M once more, and from then on one press puts the deck
  full screen on the projector and the presenter view on the laptop. Safari and Firefox only open
  the window; drag it over by hand.
- **Pop-ups.** Chrome blocks the window once per file. The deck shows a panel with a button
  "Open presenter view"; one click opens it. For good: add `file:///*` under
  `chrome://settings/content/popups`, "allowed to send pop-ups".
- **Full screen from the presenter view** (F or the button) needs one click in the deck window when
  the deck is opened as a file; the deck shows a panel saying so. Served over http it works directly.
- **Wrong screens.** S in the deck swaps them. The choice is kept for the session.
- **One screen only.** Start the deck with F and switch between the two windows.
- **After reloading the deck** the old presenter window is dead. Press M again.

Notes are speaking text: short, full sentences, the most important first, with the numbers, names
and the transition to the next slide.

## PDF

**In the deck (P or the download button).** Made in the browser without a print dialogue and
downloaded as `Title_EN.pdf`. Export mode: no animation, all click steps visible, quiz questions
revealed, no buttons, current language (press L first for the other one). Videos and embeds
appear as their poster image, remote ones with their address. Each slide is an image at
2880 by 1620 px with the text invisibly on top, so the PDF is searchable. Roughly 0.4 seconds and
150 kB per slide. Elements that must not appear get `data-export="off"`.

**From the build.** `vs build <deck> --pdf` writes a vector PDF with real text next to the HTML,
one file per language, smaller and sharper. Use it when the PDF is sent or printed.

Render PDFs only when the user asks for one for this version.

## Video

`vs video <deck> --slide 1 --seconds 6` renders one slide frame by frame to MP4 (needs ffmpeg), for
logo intros and lower thirds. `--format 1:1` or `9:16` fits the 16:9 slide into the frame.
