# The voice profile

A deck in the brand's colours that reads like any other deck is half a brand. The voice profile
records how the company writes, so that every title, bullet and reader text of a later deck could
stand on its own website. It has two parts, and they do different work:

| Part | Where | For whom |
|---|---|---|
| the profile | `library/<brand>/voice.md` | the writer: vs-create reads it before it writes a word |
| the rules | `brand.json` under `voice` | the build: it checks every slide and names what breaks a rule |

The profile carries what cannot be checked (tone, rhythm, which word is the brand's). The rules
carry what can (address, sentence length, words to avoid, fixed terms). Do not try to turn tone into
rules, and do not leave a checkable thing in prose only.

## 1. Gather texts the company wrote itself

```bash
vs voice example                         # measure what the library holds
vs voice example ~/Downloads/about.txt   # add sample texts first, then measure
```

Three sources, in this order of weight:

1. **Sample texts the user names** (`voice/samples/`, `.txt` or `.md`). Ask for two or three texts
   they consider typical and well written: a newsletter, a text about the company, a customer
   letter, the script of a talk. These say most, because someone chose them.
2. **Documents that were read in** (`vs ingest`): a style guide's chapter on language is a decision
   and outranks everything measured; a good deck shows how the company writes on slides.
3. **The website** (`raw/copy.md`). Often written by an agency, often translated: good for terms
   and claims, weaker for tone.

PDF, Word and PowerPoint files go through `vs ingest`, their text is then measured as well.
Only texts by the company count. Press articles about it, customer quotes and legal pages do not.

## 2. Read the measurement, then the texts

The command prints per language: how the reader is addressed, how often "we" speaks, sentence
length (the usual and the long one), questions and exclamation marks, headline length, frequent
words and pairs, and names written with capitals more than once. The numbers are in
`raw/voice.json`. With under 250 words in a language the command says so: treat the numbers as a
hint and ask the user for a sample text in that language.

Numbers show the frame, not the voice. Read the texts themselves and note what a number cannot
see: who is the subject of the sentences (the company, the customer, the matter), whether they
promise or describe, what is concrete and what is abstract, how a paragraph opens, what the
company never says about itself.

## 3. Write `voice.md`

The command drafts the file with the measured facts in place and a `TODO` wherever a judgement is
needed. Fill every section, in the language the brand's first language is written in:

- **In one paragraph.** Who speaks to whom, in which manner. A new colleague must be able to
  write from these four sentences alone.
- **Address and perspective.** Formal or informal, who "we" is, how customers, members or partners
  are named, how the company refers to itself.
- **Tone.** Three or four adjectives, each with a phrase from the texts as evidence and with the
  thing next to it that the company is not ("confident, not loud"). An adjective without evidence
  is your opinion: leave it out.
- **Sentences.** Rhythm, verbs or nouns, active or passive, questions, imperatives.
- **Words.** The brand's words for itself, its customers and its offer. Words it avoids, each with
  what it says instead; a word is "avoided" only if the texts show the alternative or the user
  says so.
- **Fixed terms.** Product, programme, event and role names exactly as written, with the forms
  that are wrong. The candidates the command lists are candidates: strike place names and
  coincidences.
- **Ten real sentences** and **eight real headlines**, word for word, with their source. Choose
  them for range, not for beauty. They are the material samples and decks are written from.
- **Before and after.** Five pairs: a sentence as a generic deck would put it, and the same
  content in this voice. This section does more for later decks than any description: write it
  with care, from what the company really offers.
- **On slides.** What follows for titles, labels, bullets, numbers, calls to action and the reader
  text of a reading version.
- **Per language**, if the brand presents in more than one: what differs (address, tone, terms
  that stay untranslated).

Nothing is invented. What the texts do not show is recorded as "not defined" and goes to the open
points, where the user decides.

## 4. Set the rules

The command drafts them from the measurement when the brand has none. Correct them, then confirm
them with the user in the same message as the rest of the library (they are short enough to show):

```json
"voice": {
  "sentence_max": 20,
  "exclamation": false,
  "terms": ["Example Forum", "Example Hub e.V."],
  "avoid": ["leverage => use", "world-class"],
  "de": {"address": "Sie", "gender": ":innen", "avoid": ["Lösungsanbieter"]},
  "en": {"sentence_max": 22}
}
```

| Rule | Meaning | How to set it |
|---|---|---|
| `sentence_max` | most words a sentence on a slide may have | from the measured sentence length, lower for a brand that writes short; slides are tighter than web pages, so stay under the long sentences of the website |
| `sentence_max_read` | the same for reader texts of a reading version | only if the user wants it checked; left out, reader texts are not measured |
| `address` | how the reader is addressed: `Sie` or `du` (de), `vous` or `tu` (fr), `usted` or `tú` (es), `Lei` or `tu` (it), `u` or `je` (nl) | under the language code; only when the texts are consistent or the user decides |
| `gender` | the gender-inclusive form in German: `:innen`, `*innen`, `_innen`, `Innen`, `/innen` | under `de`; only if the brand uses one consistently |
| `exclamation` | `false`: no exclamation marks on slides | `false` unless the brand clearly uses them |
| `terms` | names that are always written exactly like this | from the confirmed fixed terms; a different case or a missing hyphen is reported, capitals in a label are not |
| `avoid` | words and phrases the brand does not use, `"word => what it says instead"` | from the profile; few and certain, every entry costs a false alarm somewhere |

Rules directly under `voice` hold for every language. Rules under a language code hold for that
language, win over the common ones, and their `terms` and `avoid` are added to the common lists.

```bash
vs set example voice.sentence_max=20 voice.de.address=Sie 'voice.avoid=["leverage => use"]'
vs voice example --check "Wir zeigen dir, wie es geht!" --lang de      # try a sentence against the rules
```

## 5. Write the masters' samples in this voice

Every master's `sample` is written from the ten sentences and the headlines, in each of the
brand's languages. `vs preview` checks the samples against the rules and lists what breaks them
(`VOICE master bullets, title: ...`). The preview is what the user judges the voice by: when the
samples sound like a template, the profile is not finished.

A master whose sample is not the brand's own words (contract terms, a customer quote) carries
`"voice": false` in its sample and is not checked.

## 6. Ask the user

In the confirmation at the end of the onboarding, ask about the voice with material to react to:
show the paragraph, the rules, and three of the before-and-after pairs, and ask whether this is
how they write, which words are missing from the avoid list, and whether the address is right in
every language. People correct a sentence far more readily than they describe a tone.

## Later

- New texts: `vs voice example <files>` measures again. `voice.md` is never overwritten, the rules
  only with `--again`. Revise the profile by hand from the new numbers.
- A finding that is wrong more often than right means the rule is wrong: change the rule, do not
  teach the writer to work around it.
- The style guide's Voice section points to this profile. A library made before 0.5.0 has its
  voice in `styleguide.md`: run `vs voice <brand>`, move that content into `voice.md`, complete
  the sections that are new, set the rules.
