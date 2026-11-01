# The best form for a slide

Read this when you plan the slides (step 3) and whenever a slide carries figures, a sequence or a
structure. The background, with sources, is in the repository's `research/display-forms.md`.

## First the statement, then the form

Write the title of the slide first, as a full sentence. Then ask what kind of statement it is.
The kind decides the form, not the master that was used last, and not the data that happens to be
at hand. One slide, one statement: when a title holds two (it grew and it is ahead of the others),
it is two slides or one form that shows both.

| The slide says … | Kind | Form in the framework | When to build one freely |
|---|---|---|---|
| one figure matters | magnitude, single | `big_number`, `kpis` (three at most) | a figure set against a picture of its size (a stadium, a year) |
| A is larger than B, a ranking | comparison | `bars` (named things, longest first), `compare` (one against others) | many items with a long tail: show the top five and "the rest" |
| it grew, fell, turned | change over time | `line_chart` (many points), `column_chart` or `figure` with `columns` (few points), `big_number` with the change | an event that explains the turn, marked on the line |
| the parts of a whole | part to whole | `share` (ring, or `pie`), `column_chart` stacked (parts over time), `tiles` | parts within parts: a treemap as a free slide |
| how one figure becomes another | deviation, bridge | `waterfall` | |
| above or below a target | deviation | `bars` with the target in the note, `before_after` | bars from a middle line, left minus, right plus |
| how something is spread | distribution | `bars` over bands (ages, price ranges) | a dot or bar strip per person or case |
| two things go together | correlation | `matrix` (qualitative, four fields) | a scatter of points with the one that matters named |
| what follows what | sequence, process | `steps`, `process`, `stairs` (building on each other), `cycle` (repeating), `flow` (who gives what to whom) | see "Processes" below |
| what lies ahead | plan, roadmap | `roadmap` (milestones or now, next, later), `timeline` (bars over months), `phases` (proposal) | |
| how something is built | structure, hierarchy | `pyramid`, `hub`, `governance`, `sections` | an organisation chart, a system with its interfaces |
| what overlaps | relation | `venn`, `matrix` | |
| two states | change of state | `before_after`, `split` | |
| a choice, a decision | choice | `verdict`, `price_table`, `effort_table`, `compare` | |
| where | position | `figure` with a map image | the places as points on a simple outline |
| many become few | narrowing | `funnel` | |

Rules every chart keeps, master or free:

- Real numbers with a source (`source`), and the unit on the slide.
- The title says what the reader should see ("revenue has doubled"), not what the chart is
  ("revenue 2022 to 2025").
- One thing in the accent colour: the bar, the part, the line the title is about. The rest is ink
  and grey.
- Labels at the data, not in a legend, wherever that fits; a legend only for two or three series.
- Bars and columns start at zero. A line may start higher when the change is the point; say so.
- A pie or a ring with two to five parts; more parts are bars. Never 3D, never two pies side by side
  to compare (two columns stacked to 100 % do that better).
- Few numbers live: three figures a room can take in, ten belong in the reading version.

## Research where the slide deserves it

Most slides find their form in the table. The two or three slides that carry the argument (the one
number of a pitch, the comparison a decision rests on, the process the whole proposal is about)
deserve a look further: search how strong presentations and data journalism show this kind of
statement (newspapers' graphics desks, consulting reports, the catalogues in the research file),
and take the form that makes the statement plainest. Note in `research/report.md` which form you
chose for which slide and why, in one line each.

## A master only when it is the best form

A master is the right choice when its form fits the statement. When no master fits, do not bend the
statement into the nearest master: write the slide freely (`free`, title plus a body in the brand's
tokens, never hex colours). A free slide goes through the same checks as every other slide
(overflow, legibility, density, the voice), so it has to hold the same sizes: body text 24 px and
more, labels 20 px and more.

**A new form goes into the repertoire at once.** The build notices a free slide in a form the brand
does not have yet and prints `FORMS: slide N is written freely in a form the brand does not have yet`.
Make it a master straight away, without asking:

```bash
vs forms <brand> --promote <deck> --slide N --name <name>
```

Give its slots names that say what they hold, write its `use` (what statement it is for, as in the
table above), look at it in the preview, and tell the user in one line: "New form in your
repertoire: <name> (slide N). `vs forms <brand> --remove <name>` takes it out again." When the user
says they do not want it, run that: the slides become free slides again, word for word, and the
form is not proposed again.

**Similar forms become one.** When the free slide is close to a master the brand already made
(`FORMS: … close to the brand's master X`), do not make a second one: give X what the slide needs
(an optional slot, room for one more item), set the slide on X and say in one line what X can do now.
`vs forms <brand>` lists the brand's own masters, the free forms not in the repertoire yet, and
masters that are close to one another.

## Processes from their context

A process is drawn as it is, not as the nearest master draws it. Before choosing `steps` or
`process`, ask what the process has: branches (a decision, two ways), a loop (back to an earlier
step), roles (who does which step: lanes), hand-overs between organisations, waiting times, a
part that runs in parallel. A straight line of four to six steps is `steps` or `process`; something
that repeats is `cycle`; who gives what to whom is `flow`. Anything else is written freely in the
shape it has: lanes for roles, a fork for a decision, an arrow back for a loop, and the step the
slide is about in the accent colour. The drawing explains itself: an arrow joins each step to the next,
every hand-over is an arrow that crosses into the other lane, and the end is marked; a reader who
skips the text still sees the path. Use the words of the context (the client's names for the
steps, their systems, their roles), not "Step 1". Such a slide then goes into the repertoire like
any new form.
