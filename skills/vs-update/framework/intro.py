# -*- coding: utf-8 -*-
"""The master preview introduces itself: a few slides at its start, built from the brand's own masters, say what
the file is, how to move in it, what comes next and what the decks can do. And every master slide carries one
line for the user that says what it is for (shown above the button bar, never on the slide).

Texts are kept free of an address (no "you", "du" or "Sie"), so they fit every brand's voice; German and English
are written, other languages read the English.
"""

def _l(en, de):
    return {"en": en, "de": de, "*": en}

def slides(brand_name, count, masters):
    """The introduction as deck slides. count: the master slides that follow. masters: the brand's masters; a
    slide whose master the brand does not have is left out."""
    name = str(brand_name or "").strip()
    out = [
        {"master": "bullets", "name": _l("Introduction", "Einführung"), "kicker": "vibeupslides",
         "title": _l(f"The slide library of <em>{name}</em>" if name else "This is the <em>slide library</em>",
                     f"Die Folienbibliothek von <em>{name}</em>" if name else "Das ist die <em>Folienbibliothek</em>"),
         "lead": _l(f"The {count} slides after this introduction are the master slides, filled with sample text. Every presentation is built from them.",
                    f"Die {count} Folien nach dieser Einführung sind die Masterfolien, gefüllt mit Mustertext. Aus ihnen entsteht jede Präsentation."),
         "bullets": [_l("<strong>← →</strong> turn the slides, <strong>O</strong> shows all of them at once, <strong>G</strong> the outline.",
                        "<strong>← →</strong> blättern, <strong>O</strong> zeigt alle Folien auf einmal, <strong>G</strong> die Gliederung."),
                     _l("<strong>L</strong> changes the language, <strong>D</strong> switches between light and dark slides.",
                        "<strong>L</strong> wechselt die Sprache, <strong>D</strong> schaltet zwischen hellen und dunklen Folien."),
                     _l("<strong>A</strong> turns the animations on and off, <strong>R</strong> plays a slide again.",
                        "<strong>A</strong> schaltet die Animationen ein und aus, <strong>R</strong> spielt eine Folie noch einmal ab."),
                     _l("<strong>M</strong> opens the presenter view with notes and clock, <strong>P</strong> makes a PDF.",
                        "<strong>M</strong> öffnet die Moderationsansicht mit Notizen und Uhr, <strong>P</strong> erzeugt ein PDF.")]},
        {"master": "steps", "name": _l("What comes next", "Wie es weitergeht"), "kicker": _l("Next", "Als Nächstes"),
         "title": _l("From this library to the <em>first presentation</em>", "Von dieser Bibliothek zur <em>ersten Präsentation</em>"),
         "items": [{"title": _l("Look through", "Durchsehen"), "current": True,
                    "text": _l("Go through the master slides and tell Claude what is off: colours, type, logo, pictures, spacing.",
                               "Die Masterfolien durchgehen und Claude sagen, was nicht passt: Farben, Schrift, Logo, Bilder, Abstände.")},
                   {"title": _l("Confirm", "Bestätigen"),
                    "text": _l("Once the look is right, the library is confirmed. It can be changed at any time later.",
                               "Stimmt das Aussehen, wird die Bibliothek bestätigt. Sie lässt sich später jederzeit ändern.")},
                   {"title": _l("Present", "Präsentieren"),
                    "text": _l("Tell Claude what the presentation is for and who it is for. The slides are there in seconds.",
                               "Claude sagen, wofür und für wen die Präsentation ist. Die Folien stehen in Sekunden.")},
                   {"title": _l("Edit", "Bearbeiten"),
                    "text": _l("The pencil in every presentation opens it for typing. Claude corrects and translates afterwards.",
                               "Der Stift in jeder Präsentation öffnet sie zum Tippen. Claude korrigiert und übersetzt danach.")}]},
        {"master": "cards", "name": _l("What a presentation can do", "Was eine Präsentation kann"), "kicker": _l("Built in", "Eingebaut"),
         "title": _l("More than a slide program <em>can do</em>", "Mehr, als ein Folienprogramm <em>kann</em>"), "cols": 4,
         "items": [{"n": "01", "title": _l("Two versions", "Zwei Fassungen"),
                    "text": _l("One file to present and to read, in one or several languages.", "Eine Datei zum Vortragen und zum Lesen, in einer oder mehreren Sprachen.")},
                   {"n": "02", "title": _l("Movement", "Bewegung"),
                    "text": _l("Animations in the manner of the website, and video as large as the slide.", "Animationen in der Art der Website und Video, so groß wie die Folie.")},
                   {"n": "03", "title": _l("In the room", "Im Raum"),
                    "text": _l("Presenter view with notes, timer and quiz slides.", "Moderationsansicht mit Notizen, Timer- und Quizfolien.")},
                   {"n": "04", "title": _l("The brand's voice", "Sprache der Marke"),
                    "text": _l("Every text is written the way the company writes, and checked against its rules.", "Jeder Text ist geschrieben, wie das Unternehmen schreibt, und gegen seine Regeln geprüft.")}]},
    ]
    return [dict(s, voice=False, intro=True) for s in out if s["master"] in masters]

ABOUT = {
    "cover": ("The opening slide: title, subtitle, date or occasion.", "Die Titelfolie: Titel, Untertitel, Datum oder Anlass."),
    "cover_photo": ("The opening slide over a photo or a film.", "Die Titelfolie über einem Foto oder Film."),
    "chapter": ("Opens a chapter and gives the footer its chapter name.", "Eröffnet ein Kapitel und gibt der Fußzeile den Kapitelnamen."),
    "agenda": ("The schedule of a day or a session.", "Der Zeitplan eines Tages oder Termins."),
    "sections": ("The parts of the presentation as a numbered list.", "Die Teile der Präsentation als nummerierte Liste."),
    "statement": ("One sentence that stands alone.", "Ein Satz, der allein steht."),
    "statement_photo": ("One sentence over a photo.", "Ein Satz über einem Foto."),
    "bullets": ("A message and three to five points, one by one on click if wanted.", "Eine Aussage und drei bis fünf Punkte, auf Wunsch einzeln per Klick."),
    "cards": ("Two to four similar things side by side.", "Zwei bis vier gleichartige Dinge nebeneinander."),
    "columns": ("Two or three topics side by side.", "Zwei oder drei Themen nebeneinander."),
    "cycle": ("Something that repeats: a loop of three to five stations.", "Etwas, das sich wiederholt: ein Kreislauf aus drei bis fünf Stationen."),
    "flow": ("How things hang together: boxes joined by arrows.", "Wie Dinge zusammenhängen: Kästen, durch Pfeile verbunden."),
    "stairs": ("Stages that build on each other, each higher than the last.", "Stufen, die aufeinander aufbauen, jede höher als die davor."),
    "compare": ("One figure and what it is measured against, as bars.", "Eine Zahl und woran sie gemessen wird, als Balken."),
    "tiles": ("Four to eight things that each have a picture.", "Vier bis acht Dinge, die jeweils ein Bild haben."),
    "matrix": ("Four fields along two questions, one of them marked.", "Vier Felder entlang zweier Fragen, eines ist hervorgehoben."),
    "funnel": ("Many become few: stages that narrow, each with its number.", "Aus vielen werden wenige: Stufen, die schmaler werden, jede mit ihrer Zahl."),
    "pyramid": ("What rests on what: three or four levels.", "Was worauf aufbaut: drei oder vier Ebenen."),
    "before_after": ("Two states set against each other.", "Zwei Zustände im Vergleich."),
    "hub": ("One thing in the middle and what belongs to it around it.", "Eine Sache in der Mitte und was dazugehört drum herum."),
    "venn": ("Two or three fields and what they share in the middle.", "Zwei oder drei Felder und was sie in der Mitte gemeinsam haben."),
    "spectrum": ("Where things stand on a scale between two poles.", "Wo Dinge auf einer Skala zwischen zwei Polen stehen."),
    "waterfall": ("How one figure becomes another, step by step.", "Wie aus einer Zahl Schritt für Schritt eine andere wird."),
    "share": ("Parts of a whole as a ring, the one that counts in the middle.", "Teile eines Ganzen als Ring, der wichtigste in der Mitte."),
    "steps": ("A procedure in three or four steps.", "Ein Vorgehen in drei oder vier Schritten."),
    "process": ("A path in three to six stages; every click fills the next one.", "Ein Weg in drei bis sechs Etappen; jeder Klick füllt die nächste."),
    "phases": ("Phases of a project, each with its content.", "Phasen eines Projekts mit ihrem Inhalt."),
    "timeline": ("What happens when: bars and milestones along the time.", "Was wann geschieht: Balken und Meilensteine entlang der Zeit."),
    "big_number": ("One figure, large, counting up.", "Eine Zahl, groß, sie zählt hoch."),
    "kpis": ("Three or four key figures side by side.", "Drei oder vier Kennzahlen nebeneinander."),
    "bars": ("Values compared as growing bars.", "Werte im Vergleich als wachsende Balken."),
    "figure": ("A column chart drawn from numbers, one value marked.", "Ein Säulendiagramm aus Zahlen, ein Wert ist markiert."),
    "line_chart": ("A development over time as a line.", "Eine Entwicklung über die Zeit als Linie."),
    "table": ("A table for what really needs rows and columns.", "Eine Tabelle für das, was wirklich Zeilen und Spalten braucht."),
    "split": ("Text on one side, a picture on the other.", "Text auf der einen Seite, ein Bild auf der anderen."),
    "fullbleed": ("A picture or film over the whole slide with a short text.", "Ein Bild oder Film über die ganze Folie mit kurzem Text."),
    "gallery": ("Several pictures together.", "Mehrere Bilder zusammen."),
    "quote": ("A quotation with the person who said it.", "Ein Zitat mit der Person, die es gesagt hat."),
    "testimonials": ("Several voices of customers or partners.", "Mehrere Stimmen von Kunden oder Partnern."),
    "reference": ("A project or customer as an example.", "Ein Projekt oder Kunde als Beispiel."),
    "logo_wall": ("Logos of customers or partners.", "Logos von Kunden oder Partnern."),
    "team": ("The people, with photo, name and role.", "Die Menschen, mit Foto, Name und Rolle."),
    "profile": ("One person in more detail.", "Eine Person ausführlicher."),
    "video": ("A video alone on the slide, as large as it goes.", "Ein Video allein auf der Folie, so groß wie möglich."),
    "video_title": ("A video with one line of title above it.", "Ein Video mit einer Zeile Titel darüber."),
    "embed": ("A live web page or an embedded player.", "Eine Webseite oder ein eingebetteter Player."),
    "exercise": ("A task for the audience, for workshops.", "Eine Aufgabe für das Publikum, für Workshops."),
    "summary": ("The whole argument on one slide, for readers of no other slide.", "Die ganze Argumentation auf einer Folie, für alle, die keine andere lesen."),
    "verdict": ("Criteria in three columns: fits, clarify first, does not fit.", "Kriterien in drei Spalten: passt, erst klären, passt nicht."),
    "requirements": ("The client's requirements and the answer to each, row by row.", "Die Anforderungen des Kunden und die Antwort darauf, Zeile für Zeile."),
    "governance": ("Who meets how often for what in a project.", "Wer sich im Projekt wie oft wozu trifft."),
    "effort_table": ("Effort by position, for proposals.", "Aufwand je Position, für Angebote."),
    "price_table": ("Prices or packages compared.", "Preise oder Pakete im Vergleich."),
    "terms": ("Conditions of a proposal.", "Konditionen eines Angebots."),
    "signature": ("The closing of a proposal with the signatures.", "Der Abschluss eines Angebots mit den Unterschriften."),
    "closing": ("The last slide: thanks, contact, the next step.", "Die letzte Folie: Dank, Kontakt, der nächste Schritt."),
    "blank": ("An empty slide with the brand's frame.", "Eine leere Folie im Rahmen der Marke."),
    "free": ("Free content for the one slide no master fits.", "Freier Inhalt für die eine Folie, zu der kein Master passt."),
    "brand_colours": ("The colours of the brand, to check them.", "Die Farben der Marke, zum Prüfen."),
    "brand_type": ("The typefaces of the brand, to check them.", "Die Schriften der Marke, zum Prüfen."),
    "timer": ("A countdown for breaks and exercises.", "Ein Countdown für Pausen und Übungen."),
    "quiz_true_false": ("A statement to judge: true or false.", "Eine Aussage zum Einschätzen: richtig oder falsch."),
    "logo_intro": ("The logo alone, as an opening.", "Das Logo allein, als Auftakt."),
    "quiz_choice": ("A question with answers to choose from.", "Eine Frage mit Antworten zur Auswahl."),
    "quiz_estimate": ("A question whose answer is a number to guess.", "Eine Frage, deren Antwort eine Zahl zum Schätzen ist."),
}

def about(master, meta=None):
    """One line for the user about a master slide, per language; for a master of the brand's own, what its file says."""
    if master in ABOUT: return _l(*ABOUT[master])
    use = str((meta or {}).get("use") or "").strip()
    return use or None
