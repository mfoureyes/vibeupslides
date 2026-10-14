# Structures: how each kind of deck is built

Read this in step 3 of vs-create, after the user has said what the deck is for and before you
propose a storyline. It gives, per kind of deck, the questions to ask, the slide sequence with the
master that suits each slide, guidance on length and density, the points where the sources
disagree, and the mistakes to check the storyline against. `modes.md` covers the difference between
a deck that is presented and one that is read.

**How firm is this?** Almost all of it is practice knowledge from authors, investors, consultants
and vendors, not controlled research. Studies exist only on single questions (text and speech at
the same time, sentence headings). The markers say how firmly to hold a rule:

- **(consensus)**: several independent sources say it. Follow it unless the user decides otherwise.
- **(one source)**: found in one place. Offer it, do not insist.
- **(inference)**: put together from the sources by the researcher. A reasonable default, no more.

Numbers without a marker inside a sequence come from the source named in that section. Sources and
what could not be checked are in `research/deck-typen.md` in the repository.

Masters are named as they ship with the framework (`vs masters <brand>` shows what the brand
actually has; a brand may have more or differently named ones). The document masters (`summary`,
`phases`, `timeline`, `requirements`, `reference`, `figure` and the others for proposals) take an
optional `topic`: a short label above the title that names the subject, while the title stays a
claim. What is still missing is listed at the end.

## What holds for every kind

1. **The title is a claim.** It says what the slide shows, as a full sentence, and the titles read
   in a row give the argument. The same rule comes independently from pitch, conference talk,
   consulting deck and reading version (consensus), and it is the one point with some research
   behind it: a sentence heading with visual evidence led to better understanding and recall than
   a keyword title with bullets (Garner and Alley 2013, one research group).
2. **Argument before slides.** Decide what the deck says before choosing any master. Designing
   first hides a missing argument behind a finished look (consensus).
3. **Start with the audience, not with yourself.** Company size, history and "we" sentences at the
   start are the mistake named most often in sales and company presentations, and in spirit in
   keynote and pitch too (the strongest consensus in the research).
4. **One idea per slide, details in the appendix.** A slide that needs two titles is two slides.
5. **A clear next step at the end.** The last slide says what happens now, not only "thank you".
6. **Two versions are two documents.** Nearly all sources say one deck cannot be good on stage and
   good in the inbox at once. Settle the main mode first; see `modes.md`.

## The method, before any slide is written

This is the consulting way of building a deck (consensus there); it works for every kind.

1. **Write the answer in one sentence.** What should the audience know, believe or decide at the
   end? If you cannot write it, ask the user until you can. For a keynote it is the one idea, for
   a pitch what the company does, for a proposal the guiding thought.
2. **Find three to five supporting blocks** that carry the answer and do not overlap. They become
   the chapters. More than five means two blocks are really one, or the deck covers too much.
3. **Write only the titles** of all slides, as claims (the "ghost deck"). No body text, no charts.
4. **Read the titles in a row.** They must tell the whole argument to someone who sees nothing
   else. Fix gaps, repetitions and topic titles ("Market", "Our team") here.
5. **Then fill:** choose the master per slide and write the slots. This list of titles with
   masters is what you show the user as the storyline.

## Choosing the structure

| The user wants | Section |
|---|---|
| money from investors, a jury or demo-day slot | 1 Investor pitch |
| one idea on a stage, a general audience | 2 Keynote |
| a result or method in front of a specialist audience | 3 Conference talk |
| to introduce the organisation | 4 Company presentation |
| to win a customer in a meeting | 5 Sales deck |
| to answer a brief or tender with scope, plan and price | 6 Proposal |
| a recommendation to management, a board or a client | 7 Strategy or consulting deck |
| people to work and learn in the room | 8 Workshop or training |

A deck may mix them: a workshop often opens with a short talk, a company presentation is what a
sales deck's single company slide expands from. Take the structure of the main purpose and borrow
blocks. The research has no structure of its own for a pure document to read or for video and
social clips; for a document take the structure of its content (most often 6 or 7) in reading mode.

---

## 1. Investor pitch

**Right when** founders ask for funding or compete in front of a jury. The sequence below is the
seed-stage form, merged from Sequoia, Y Combinator (Aaron Harris) and Guy Kawasaki. The merge is an
inference; each single slide is consensus.

**Ask the user**
- What does the company do, in one sentence a stranger understands? (The most common mistake is
  that this stays unclear.)
- Which stage, how much is asked for, and what will it make possible in about a year?
- Which traction numbers are real and can be sourced? Are there financials at all?
- Live on a stage (how many minutes), in a meeting, or sent ahead by mail? This decides the mode.
- The one revenue model. If they name several, ask which one the pitch stands on.

**Sequence (10 to 13 slides)**
1. Title: the name and one sentence on what you do. `cover`
2. Problem: who has it and how they get by today. `bullets` or `split`
3. Solution: what you do and the concrete benefit. `split` with the product, or `columns`
4. Why now: what has changed that makes this possible or urgent (Sequoia). `statement` or `bullets`
5. Traction: a few telling numbers. `kpis`, `line_chart` or `bars`; one single number
   `big_number`
6. Insight: why this works and why you. `statement`
7. Business model: how money is made, one model. `steps` or `columns`
8. Market, calculated bottom-up (customers times price, not a share of a huge total). `bars`,
   `kpis` or `table` for the calculation
9. Competition: who else, and where you differ. `table` or `verdict`
10. Team: who, and why these people. `team`
11. Financials and milestones, if they exist. `table` or `line_chart`; milestones `process` or
    `timeline`
12. Ask: the sum and what it enables in about a year (YC). `kpis` or `bullets`, then `closing`
    with the contact

**Demo-day short form (2.5 to 5 minutes, 5 to 8 slides, after YC):** what you do · problem ·
product and customer · traction (first, straight after "what you do", when the numbers are
strong) · market · team · business model · a closing slide with the three or four points to
remember (`bullets`).

**Length, density, timing (live)**
- About 10 slides for the live pitch (consensus). Kawasaki: 10 slides, 20 minutes, type of 30
  point or more.
- On a stage more than about 7 words per slide is too much (YC, one source). Prefer `statement`,
  `kpis` and image masters there and move sentences into the notes.
- German formats: 3 to 8 minutes for the pitch, 30 to 60 seconds for an elevator pitch (BPW
  Berlin-Brandenburg). Ask for the exact slot.
- A deck that is sent gets 2 to 4 minutes of an investor's time on average (DocSend 2015 and 2022,
  known here only through press reports). So the sent version must work from the titles alone
  (Reid Hoffman), and YC prepares a separate, somewhat longer deck for follow-up meetings. Offer
  that as the reading version.

**Where the sources disagree**
- *Position of the team.* German sources put it early, YC and Sequoia late. Default: late, because
  the sequence follows the investor sources and the problem should come first. Offer early when the
  team is the strongest argument or the format is a German competition (inference). The user decides.
- *Position of traction.* The merged order has it fifth; YC puts it directly after the solution.
  Default: directly after the solution when the numbers are strong, otherwise as listed.
- *Length.* Kawasaki 10 slides, Hoffman 20 to 25. Default: about 10 for live; the longer form
  belongs to the sent or follow-up deck.
- *Financial slide.* The most-read slide in 2015, present in only a quarter of decks in 2022.
  Default: include it only when real figures exist. Never fill it with invented projections.

**Check the storyline against (consensus)**
- Is it clear by slide 1 what the company does?
- Too much text for the room?
- Is competition there? Leaving it out reads as not knowing the market.
- Is the market calculated bottom-up?
- One revenue model, not several?

---

## 2. Keynote

**Right when** one person carries one idea to a general audience for 15 to 45 minutes. The
structure comes from Nancy Duarte (the contrast between what is and what could be) and
Gallo (three parts), with TED's own rules as a stricter supplement.

**Ask the user**
- The one idea in one or two sentences. TED's test: is it new, is it interesting, can it be backed
  up? Everything in the talk must link back to it (Chris Anderson).
- Who is in the room and what do they already know? The explanation starts there.
- Which stories, examples or a demo are available? Each block of the middle needs one.
- Is it an idea talk or a product or company keynote? (See the variants.)
- The slot in minutes, and whether slides are wanted at all.

**Sequence**
1. Opening at the shared "what is": name the topic fast and why it matters, with an example the
   audience can follow or a surprising fact; no row of statistics (TED). `cover_photo` or `cover`,
   then `fullbleed` or `statement`
2. The gap or the opponent: the problem the idea answers. `statement` or `fullbleed`
3. The one idea as a sentence, said early. `statement`; over a photo `statement_photo`
4. The middle in about three blocks. Each sets today against the better future and each has a
   story, an example or a demo. `chapter` to open a block; `fullbleed`, `split`, `quote` for
   stories; `kpis` or one chart (`figure`) for evidence; a single number `big_number`; a
   passage that is only spoken `blank`
5. One high point: the reveal, the moment of insight. `statement`, `statement_photo` or
   `fullbleed`; a live demo needs no slide, announce it with a `statement` and show `blank`
   while it runs
6. Close in the world where the idea has been adopted, with a call to act. `statement`, then
   `closing`

**TED supplement** (official TED material and Chris Anderson). Use it when the user gives a TEDx
talk or wants that style.
- Time: under 18 minutes. One major idea as the through-line.
- Get the idea out as quickly as possible, then explain from what the audience already knows.
- Evidence in the order needed for understanding, from the least to the most exciting, then cut
  hard. A frequent arc is the detective story: problem, search, moment of insight.
- Address objections and counter-arguments.
- Close on what changes when the idea is put into practice, not on a mere summary; a call to
  action only when it fits. No selling, no company logos at the end.
- The structure stays invisible: no talking about the talk, no agenda slide.
- Slides are "by no means necessary". No slide supports more than one point; as little text as
  possible; no bullet points; photos full-bleed; one message per chart; nothing in the outermost
  corners; text may appear step by step, effects sparingly. Videos of 60 seconds at most
  (Anderson). Only images with cleared rights.
- Preparation to pass on to the user: do not read out, rehearse against the clock.

**Length, density, timing (live)**
- One idea per slide, one or two lines of text (TEDx); one large image rather than several small
  ones (Garr Reynolds). The notes carry what is said, and the slide never repeats it word for word.
- "One slide per minute" is a planning aid without evidence. Use it to estimate, not as a rule.
- TED asks for type of 42 point or more; in VibeUpSlides the masters set the type, so the practical
  rule is: when text does not fit, shorten it.
- Talks longer than a TED slot need a through-line per section (inference): give each block its
  own one-sentence message and a `chapter` slide.

**Where the sources disagree**
- *Call to action.* Duarte ends with one; TED only when it fits and never as a sales call.
  Default: a call to act for company and product keynotes, a picture of the changed world for idea
  talks. The user decides.
- *Promotion.* TED forbids promoting one's own products; that contradicts the purpose of a product
  launch and does not transfer. What does transfer (Anderson): do not boast about the organisation,
  tell the story of the problem that was solved.
- *Slides at all.* TED notes that many of the best talks have none. If the user's material is a
  story without visual evidence, offer a deck of very few slides.

**Check the storyline against (consensus)**
- Too much ground? Anderson calls this the biggest problem of first drafts; go deeper instead.
- Is the idea said within the first minutes, or does the audience wait to learn what this is about?
- Is it about the idea, or about the speaker's organisation and its history?
- Does it open with a row of numbers?
- Is this one deck trying to be slides and handout at once? Then build two versions.

Thinly supported, do not present as fact: in one analysis of 1,239 transcripts clarity of
explanation and structure was the strongest single factor for views but explained only about a
fifth of the variance (preprint, correlation only). Gallo's often-quoted share of 65 percent
emotion comes from the analysis of a single talk.

---

## 3. Conference talk

**Right when** a result, method or project is presented to a specialist audience in 20 to 30
minutes. The structure follows mainly Simon Peyton Jones; the slide form follows Alley's
assertion-evidence approach.

**Ask the user**
- If the audience remembers one thing, what is it? (This becomes slide 2 or 3 and the last slide.)
- Which one or two examples carry the talk? The talk is built on them, not on the general case.
- Which figures, charts or screenshots exist as evidence, and what is their source?
- Is there a paper or page to point to? What questions are expected (for backup slides)?
- The slot, and how much of it is discussion.

**Sequence**
1. Motivation, about 20 percent of the time: what the problem is and why it is interesting. The
   first two minutes win or lose the audience. `cover`, then `split`, `fullbleed` or `bullets`
2. The key message, said outright: "If you remember only one thing, then this." `statement`
3. Orientation only now, and only if needed: where the talk goes. `steps` with `current`, or
   nothing. No outline slide at the very start.
4. Main part, about 80 percent: narrow and deep, by example. Leave out the general case rather
   than the example. `split`, `process`, `steps`, `gallery`
5. Evidence slides: a sentence heading that states the finding, below it one figure instead of
   bullets (Alley). `figure` for a chart, diagram or screenshot that exists as an image, with a
   callout on the point that matters; `line_chart`, `bars`, `kpis`, `table` when the deck draws
   the data itself
6. Repeat the key message and point to the paper. `statement`, then `closing` with the link
7. Backup slides for questions, after the closing slide, each with `"handout": false` unless the
   user wants them handed out. `table`, charts

**Length, density, timing (live)**
- 20 percent motivation, 80 percent main part (Peyton Jones).
- One finding per evidence slide; the chart carries a source line and the title says what it shows.
- Full sentences in titles, few words below them. The detail lives in the paper.

**Where the sources disagree**
- *Headings.* Alley asks for full sentences as headings, Naegle advises against them, Reynolds
  would rather have no text at all. Default: sentence headings, because that is the variant with
  research behind it (Garner and Alley 2013, one research group) and the writing rule of vs-create.
  If the user prefers image-led slides, the claim moves into the notes and must still exist.
- *Outline slide.* Peyton Jones bans it, Gallo recommends a road map. Default: no outline at the
  start, a short orientation after the key message when the talk has more than two parts. The user
  decides.

**Check the storyline against**
- Does the talk try to cover the whole paper instead of one thing in depth?
- Is the key message said explicitly, early and again at the end?
- Does each evidence slide state its finding in the title, or only name its topic?
- Does it start with an outline before the audience knows why to care?

---

## 4. Company presentation

**Right when** the organisation introduces itself: to prospects, partners, applicants, visitors.
There is no named model with an author; the sequence is an inference from agency and consultant
guides. Hold it loosely and let the occasion cut it.

**Ask the user**
- Who is it for, and what is their problem or interest? The deck opens there.
- Three to five key figures that are current and can be sourced.
- The services or fields, and for each the benefit for the customer.
- What sets the organisation apart, concretely (a claim anyone could make does not count).
- Which references may be named, and is there one case with task, solution and result?
- What should the audience do afterwards?

**Sequence**
1. Title with the name and the claim. `cover` or `cover_photo`
2. What we exist for: which problem of the customer we solve. `statement` or `split`
3. Key figures: three to five, graspable in seconds. `kpis`
4. Services in three to five fields, each with its benefit. `cards` or `columns`
5. What sets us apart, concretely. `bullets`, `verdict` or `columns`
6. References, grouped by industry or size. `logo_wall`
7. Case: task, solution, result. `reference`; customers' voices `testimonials` (one to three,
   with name, role and portrait or logo)
8. Team and contact persons. `team`; one person in depth `profile`
9. How working together goes. `process` or `steps`
10. The next step, not "thank you". `closing` with the step as its sentence

**Modular use.** Keep one master deck of 30 to 40 slides and cut it per occasion; for each offer
keep a block of three slides (occasion, approach, evidence). This fits the VibeUpSlides library:
propose the long deck once and build occasion decks from it by leaving slides out.

**Length, density, timing (live).** The research gives no timing for this kind. Derive the number
of slides from the slot and the audience; ten slides as above is the short form.

**Variants.** None contested in the sources. The one rule with the strongest consensus of the whole
research applies here: do not begin with your own company (size, history, "we" sentences) but with
the customer.

**Check the storyline against**
- Do slides 1 to 3 talk about the audience's problem or about the organisation's history?
- Are the figures few enough to grasp in seconds, and sourced?
- Is each service stated with its benefit, not only named?
- Is the difference concrete?
- Does the deck end with a next step?

---

## 5. Sales deck

**Right when** a seller sits with a prospective customer and wants a decision or a next meeting.
Three models stand behind the sequence:

- **Andy Raskin** (2016, on the Zuora deck): name a big change in the world; show that there will
  be winners and losers; tease the promised future; present features as the means to get there;
  give evidence. Explicitly do not begin with product, company or "the problem".
- **Challenger** (Dixon and Adamson; checked only through secondary sources): opening, reframing, rational deepening, emotional impact, a new way, your own solution last.
- **Gong**: change, pain, gain, proof.

**Ask the user**
- Who is the customer, who sits in the meeting, and what do you already know about their situation?
- Is there a real change in their world (market, regulation, technology) that makes acting urgent?
- What is at stake for them if nothing happens?
- Which evidence exists: named customers, numbers, a case?
- What is the next step you want from this meeting?

**Sequence (inference from the three models)**
1. A change or insight in the customer's world. `statement`, `fullbleed` or `kpis` with a sourced
   number
2. What is at stake: who wins, who loses. `columns` with two columns, or `verdict`
3. The customer's situation, confirmed with them in the room. `bullets`; say in the notes that
   this slide is a question to the customer
4. The target state. `statement` or `split`
5. Capabilities as the way there. `process`, `steps` or `cards`
6. Evidence. `kpis`, `big_number`; a case `reference`; customers' voices `testimonials`; whom
   you work for `logo_wall`
7. One short company slide. `kpis` or `bullets`
8. The next step. `closing`, or `steps` with dates

**Length, density, timing (live)**
- Keep the deck part short and leave the time to the conversation: in won first meetings the deck
  part lasted 9.1 minutes on average, in lost ones 11.4 (Gong's own data, one source, correlation
  only). Do not present this as a rule; use it to argue for fewer slides.
- About your own company two minutes at most.

**Where the sources disagree**
- *Opening.* Raskin opens with the change, German sources and Kawasaki with the problem. Default:
  the change, when the user can name a real one, because all three models open in the customer's
  world and not with the offer. If there is no real change, open with the problem; an invented
  trend is worse than none (inference). The user decides.

**Check the storyline against**
- Does it begin with the product, the company or its history?
- Is the customer's situation asserted, or confirmed with them?
- Are features shown as means to the target state, or as a list?
- Is the company part longer than one slide?
- Is there a concrete next step with a date or owner?

---

## 6. Proposal

**Right when** the deck is an offer: understanding of the task, approach, team, schedule, price. A
proposal is by nature a **reading version**; the presentation in the meeting selects from it
(inference). Set `"mode": "reading"` and build the live selection on request (`modes.md`).

**Ask the user**
- Is there a brief or tender? If so the proposal follows **its order and its headings**, and the
  sequence below only fills what the tender leaves open. Ask for the document.
- The customer's most important concerns, in their words and weighted.
- The guiding thought: the one sentence on how you solve it.
- Phases, activities, results, staffing per phase, and what the customer must contribute.
- Price basis: day rates, effort, fixed price, terms. Should the deck carry a signature block?
- Who reads it and who decides. Is there a meeting (30 to 60 minutes with discussion)?

**Sequence (default template).** The core order is consensus from three guides (opening,
understanding of the task, approach with a core thesis, results, references, team, schedule, price
and terms, next steps); the template adds what the analysis of one real consulting proposal of 46
slides showed to be worth taking over.

1. Cover, formal, naming both parties. `cover`
2. Contents: the sections of the proposal. `sections` (it carries no page numbers; the reading
   version builds its own contents page)
3. Summary: concern, solution, duration, price. After Shipley in four fields: guiding thought and
   the customer's goal; their main concerns in their words, weighted; per concern benefit,
   solution, difference, evidence; price and next step. `summary`: the concerns as `context`,
   the guiding thought as the title, benefit and evidence as `points`, duration, price and next
   step as `facts`
4. Understanding of the starting position. `bullets`, `columns`
5. Match with the brief: each requirement and where the proposal answers it. `requirements`
6. Approach at a glance. `phases`
7. Per phase: an overview, then numbered sub-sections with activities, staffing, results and the
   customer's contribution. `chapter`, then `columns` or `table`; `phases` again with only the
   steps of that phase works too
8. Governance and schedule. `governance` for who meets how often for what; `timeline` for the
   schedule as bars with milestones; a plain list of dates fits `table`
9. Team. `team`; a full page per person `profile`
10. Why us. `bullets` or `verdict`; references `reference`, `logo_wall` and `testimonials` (one
    quotation that is not a customer's: `quote`)
11. Offer: effort, price, terms, signature. `effort_table`, `price_table`, `terms`, `signature`
12. Next steps and contact. `steps` with dates, then `closing`
13. Appendix: references and profiles. `chapter`, then `reference` and `profile`

Worth taking over from the real proposal (one example): a double title (the subject in `topic`,
the claim as a sentence in the title); a matching of the brief (`requirements`); phase slides that
name the customer's contribution (`phases`); the contract part (`terms`, `signature`). Its section bar and project line in the footer need an engine
feature that does not exist yet (see the end).

**Length, density.** A proposal slide carries 100 to 250 words, the range for reading versions
(see `modes.md`); that is far more than a live slide, so check overflow and split rather than
shrink. For the meeting select the summary, the approach at a glance, team, price and next steps,
and leave time for discussion.

**Where the sources disagree**
- *Company profile first.* The real proposal put eight slides of company profile before the
  customer, had no summary at the front and no next step. The guides say the opposite on all
  three. Default: the template above (customer first, summary at the front, next step at the end),
  because it follows the cross-cutting rules. Offer "profile first" as a variant when the customer
  does not know the firm or the tender demands it. The user decides.
- *Tender order versus this template.* Not a disagreement: the tender wins.

**Check the storyline against**
- Does it follow the tender's order and headings where there is one?
- Does the summary stand alone, including price and duration?
- Are the customer's concerns stated in their words before the solution?
- Is every requirement of the brief matched?
- Is there a next step with a date?

---

## 7. Strategy or consulting deck

**Right when** an analysis leads to a recommendation for management, a board or a client. The
pyramid principle and MECE (blocks that do not overlap) come from Barbara
Minto (McKinsey, 1963 to 1973). The introduction follows SCQA: situation, complication, question,
answer.

**Ask the user**
- The answer or recommendation in one sentence. If they do not have it yet, the deck is not ready
  to be written; work on the sentence first.
- What is the meeting for: to inform, to decide, or to get feedback? (PwC: say it at the start.)
- Does the audience get the deck beforehand? Then that is the reading version and the meeting
  needs a short one.
- Which data backs each argument, and what is its source?

**Sequence**
1. Title. `cover`
2. Summary: one slide that stands alone and carries the whole argument; not an agenda. Situation
   and complication take about a fifth of it, the answer the rest. `summary`
3. Main part in three to five sections that do not overlap, one per supporting argument. `chapter`
   per section; within it one finding per slide: `figure` for a chart or diagram that exists as
   an image, otherwise `bars`, `line_chart`, `kpis`, `table`, `verdict`
4. Next steps: who does what by when. `steps`, `process`, `table` or `timeline`
5. Appendix: detail and sources. `chapter`, then `table` and charts

**How one slide is built (consensus):** the title is a claim as a full sentence; below it exactly
one insight with its evidence; a marker on the data point that matters; a small source line
(`source`).

**Length, density, timing (live)**
- In front of a board (PwC, one source): the reading version goes out beforehand. In the meeting
  use a short deck, repeat nothing that was sent, name the goal, leave time for discussion.
- The research gives no slide count. The count follows from the argument: one slide per claim.

**Variants.** The research could not establish differences between McKinsey, BCG and Bain; treat
the above as the common form. No contested points.

**Check the storyline against (consensus)**
- Topic titles instead of claims?
- Is the recommendation at the end instead of at the front?
- Was the look designed before the argument stood? (Run the method above first.)
- Data without a source?
- Do the sections overlap?

---

## 8. Workshop or training

**Right when** people work in the room and the deck guides them: it holds prompts, instructions and
timers, and the details go into the handout.

**Support is weakest here.** The models named are Gagné's nine events of instruction, Kolb's
learning cycle, Bowman's 4C (connect, concepts, practice, conclusion), Pike's
90/20/8, Liberating Structures with their minute counts, and the design sprint (Jake Knapp). Pike
cites no research; the attention limit of 10 to 15 minutes is not covered by the primary data
(Bradbury 2016); Kolb and 4MAT are considered empirically weak. Use every number below as a planning aid and
say so when the user asks why.

**Ask the user**
- What should participants be able to do afterwards? (One goal per block.)
- How many people, in which room, in which group forms; which material is there?
- The total time and the fixed points (start, breaks, end).
- Which exercises already exist, with their durations and the result each should produce?
- What do participants get afterwards: a handout, exercise sheets, the slides?

**Sequence of one block (inference from 4C, Gagné and Scott Berkun).** A workshop is an opening
(`cover`, the day as `agenda`), several such blocks, each opened by a `chapter`, and a close.
1. Goal or why. `statement` or `bullets`
2. Connecting to what participants already know. `quiz_choice`, `quiz_estimate` or a question as
   `statement`
3. Short input. `bullets`, `split`, `process`, `columns`
4. Exercise instruction. `exercise`
5. Timer. `timer`, directly after the exercise slide
6. Debrief: where did it get stuck, what was hard, what do you take away; show participants' work.
   `bullets` with the questions, or `gallery`
7. Summary and transfer. `bullets` or `statement`; a recap as `quiz_true_false`

**The exercise slide must contain:** the task as an instruction; the time; the group form; the
expected result and where it goes; what happens afterwards. It stays visible during the exercise,
which is why the timer repeats the steps.

**Length, density, timing (live)**
- A unit of about 45 minutes, split 15/15/15 into input, exercise and debrief; a break about every
  two hours (Berkun, one source). Put breaks in as `timer` slides without steps.
- Pike's 90/20/8: no block over 90 minutes, a change of pace every 20, participation every 8 (no
  research cited).
- Participants should have 60 to 70 percent of the speaking time (Bowman, known through a review).
  In practice: the input slides of a block are few.
- Write the schedule with times into the notes of each chapter slide.

**Variants.** The models differ in vocabulary more than in order; the block above is their common
part. If the user works with a named format (a design sprint, a Liberating Structure), follow that
format's steps and minute counts and use the block only for the slides around it.

**Handout.** Details, room for notes, exercise sheets, sources, next steps. The facilitation deck
holds only prompts, instructions and timers. Plan the handout as its own reading version.

**Check the storyline against**
- Does every exercise slide have task, time, group form, result and what follows?
- Is there a timer after each exercise and a debrief after each timer?
- Is the share of input slides small enough for the participants to do most of the talking?
- Are breaks planned?
- Is detail on the slides that belongs in the handout?

---

## Masters these structures need that do not exist yet

The masters for proposals and consulting decks (`summary`, `sections`, `phases`, `timeline`,
`governance`, `requirements`, `effort_table`, `price_table`, `terms`, `signature`), for people and
proof (`profile`, `reference`, `testimonials`, `logo_wall`) and for talks (`big_number`,
`statement_photo`, `figure`, `blank`) ship with the framework. A brand library made before they
existed gets them from the framework as they are; have vs-build adapt them when the brand's look
asks for it. Still missing:

| Missing | What it shows | Needed by | Until then |
|---|---|---|---|
| dates overview | milestones and meetings as a list of dates | proposal | `table`, or the milestone row of `timeline` |
| chart from data inside `figure` | `figure` shows an image; it draws nothing | conference, strategy | export the chart as SVG or PNG, or use `bars` and `line_chart` |
| price or effort table that adds up | the tables print the sums they are given | proposal | calculate the totals before writing the deck and check them |

Also missing in the engine, not as a master: a section bar and a project line in the footer of
reading decks.
