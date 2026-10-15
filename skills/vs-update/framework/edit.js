/* Editing mode (vs.py edit). The edit button in the button bar opens and closes it. Served by the local server,
   every change is sent there and written into deck.json; this page never keeps a change of its own. Opened as a
   file, changes show on the page at once, are kept in a journal and saved for `vs.py apply`.
   Texts: click, type, Enter or click away saves, Escape discards. A text changed in one language is translated
   into the deck's other languages after the editing: the deck file notes what waits, the agent does it. */
(function(){
  var FILE=location.protocol.indexOf('http')!==0;            /* opened as a file: no server, see `local` below */
  var root=document.documentElement, DE=(root.lang||'en').slice(0,2)==='de';
  function reading(){ return root.getAttribute('data-mode')==='reading'; }      /* asked when needed: the engine sets the version after this script has run */
  function toLive(){ try{ sessionStorage.setItem('vs-edit','1'); }catch(e){} if(window.vsSwitchMode) window.vsSwitchMode('live'); }
  var T=DE?{edit:'Bearbeiten (E)',toLive:'Bearbeiten (E): öffnet die Vortragsfassung zum Bearbeiten',earlier:'← nach vorn',later:'nach hinten →',dup:'Duplizieren',del:'Löschen',undo:'Rückgängig',redo:'Wiederholen',notes:'Notizen, Lesetext',
           saved:'Gespeichert',saving:'Speichere …',over:'Der Text läuft über die Folie hinaus: kürzen oder die Folie teilen',up:'↑',down:'↓',idup:'Duplizieren',idel:'Entfernen',
           sure:'Diese Folie löschen? (Rückgängig holt sie zurück)',hint:'Text anklicken und tippen. Enter speichert, Esc verwirft.',voice:'Sprache der Marke: ',
           typing:'Im Textfeld: Enter speichert, Esc verwirft. Danach blättern die Pfeiltasten wieder; Bild↑/Bild↓ blättern immer.',
           waiting:'Gespeichert. Nach „Fertig“ wird der Text korrigiert und nach {l} übersetzt.',saved2:'Gespeichert. Nach „Fertig“ wird die Rechtschreibung geprüft.',notesFor:'Notizen zu dieser Folie (für die Moderation)',notesSave:'Speichern',done:'Fertig',readFor:'Lesetext zu dieser Folie (steht in der Lesefassung neben der Folie)',
           tEarlier:'Die gezeigte Folie tauscht den Platz mit der Folie davor',tLater:'Die gezeigte Folie tauscht den Platz mit der Folie danach',tDup:'Eine Kopie der gezeigten Folie direkt dahinter einfügen',tDel:'Die gezeigte Folie aus dem Deck entfernen',
           gMove:'Reihenfolge: diese Folie',gSlide:'Diese Folie',gAdd:'Einfügen',gText:'Zur Folie',gSteps:'Verlauf',
           tAdd:'Eine neue Folie nach der gezeigten einfügen',tField:'Der gezeigten Folie ein Textfeld hinzufügen, das sie noch nicht nutzt',tNotes:'Notizen für die Moderation und Lesetext dieser Folie schreiben',
           tDone:'Bearbeitung abschließen: geänderte Texte werden korrigiert und übersetzt',
           add:'Neue Folie',field:'Textfeld',addHead:'Neue Folie nach dieser einfügen',fieldHead:'Feld auf dieser Folie ergänzen',noField:'Diese Folie nutzt schon alle Textfelder ihres Masters.',
           overAt:'Die orange markierten Teile reichen über die gestrichelte Linie hinaus.',
           open:'{n} geänderte Text(e) werden nach „Fertig“ korrigiert und übersetzt',end1:'Deine Änderungen sind übernommen',
           end2:'Rechtschreibung und Grammatik der geänderten Texte werden jetzt geprüft und die Texte in die andere Sprache übersetzt. Diese Seite öffnet sich danach von selbst wieder, du musst nichts tun.',back:'Die Seite ist wieder da …',
           gAnim:'Animation',aStep:'Auf Klick',tStep:'Die Teile dieser Folie erscheinen nacheinander per Klick, der erste steht mit der Folie. Noch einmal drücken: alles kommt zusammen',aMove:{'':'Bewegung: wie Deck',calm:'Bewegung: ruhiger',expressive:'Bewegung: kräftiger',off:'Bewegung: keine'},tMove:'Wie viel sich auf dieser einen Folie bewegt: wie in der ganzen Präsentation, ruhiger, kräftiger oder gar nicht',aPlay:'▶ Abspielen',aOrder:'Reihenfolge',aOrderOk:'Reihenfolge speichern',tOrder:'Die Klickschritte dieser Folie in eine eigene Reihenfolge bringen und Teile zusammenfassen',oHint:'Klicken Sie die Teile in der Reihenfolge an, in der sie kommen sollen. Mit gedrückter Umschalttaste kommt ein Teil zusammen mit dem davor. Esc bricht ab.',oNone:'Diese Folie hat keine Klickschritte. Erst „Auf Klick“ wählen.',oSaved:'Reihenfolge gespeichert.',tPlay:'Die Animation dieser Folie ansehen, mit ihren Klickschritten',shared:'Diese Folie teilen sich mehrere Präsentationen („{s}“). Was du hier änderst, gilt nur für diese, außer du drückst „Für alle Präsentationen“.',sharedAll:'Deine Änderungen an dieser Folie („{s}“) gelten für alle Präsentationen: Claude übernimmt sie in die Bibliothek und fragt, ob die anderen Präsentationen aktualisiert werden sollen.',forAll:'Für alle Präsentationen',tForAll:'Was du an dieser geteilten Folie änderst, soll für alle Präsentationen gelten, die sie verwenden. Noch einmal drücken: nur für diese',edge:'Weiter geht es in dieser Richtung nicht.',lastOne:'Die letzte Folie bleibt.',lastItem:'Der letzte Punkt einer Liste bleibt: die Folie löschen oder Claude um einen anderen Aufbau bitten.',noItem:'Diese Liste lässt sich hier nicht umbauen. Sag Claude, was sich ändern soll.',fClose:'Weiter bearbeiten',fEnd1:'Änderungen gesichert',fEnd2:'Die Datei „{f}“ ist gespeichert. Sie gehört in den Ordner, in dem diese Präsentation liegt.',fEnd2d:'Die Datei „{f}“ liegt jetzt in deinem Download-Ordner. Lege sie in den Ordner, in dem diese Präsentation liegt, oder lade sie im Chat hoch.',fEnd3:'Für Korrektur, Übersetzung in die anderen Sprachen und PDF sag Claude: „Übernimm meine Änderungen an {d}“.',fHint:'Text anklicken und tippen. Enter speichert, Esc verwirft.',gSave:'Speichern',fDir:'Ordner wählen …',fDirOk:'Speichert in Datei ✓',tDir:'Einmal den Ordner wählen, in dem deine Präsentationen liegen (oder den dieser Präsentation): danach wird jede Änderung sofort in der Präsentation gespeichert, auch bei künftigen Präsentationen in diesem Ordner',tDirOk:'Jede Änderung wird sofort in „{f}“ gespeichert',fWrong:'„{f}“ liegt weder in diesem Ordner noch darunter. Bitte den Ordner wählen, in dem diese Präsentation liegt.',fSaved:'Gespeichert in „{f}“',fFail:'Speichern nicht möglich: ',fNeed:'Noch nicht in der Datei gespeichert: „Ordner wählen …“ drücken und den Ordner angeben, in dem deine Präsentationen liegen.',fOk:'Schließen',fEndDir:'Deine Änderungen stehen in „{f}“. Du kannst die Datei so zeigen und weitergeben.',fPending:' · {n} Text(e) ungeprüft: Claude korrigiert sie, sobald du ihm schreibst. Bis dahin sind sie gelb markiert.',gCheck:'Prüfung',uKeep:'Text so lassen',tKeep:'Der zuletzt geänderte Text dieser Folie soll genau so bleiben: Er wird nicht korrigiert, nur übersetzt, und gilt als geprüft',uTip:'Ungeprüft: von dir getippt, noch nicht korrigiert',uFlag:'{n} ungeprüft',uTitle:'Texte, die du getippt hast und die noch nicht korrigiert sind. Schreib Claude „Übernimm meine Änderungen“, oder gib sie mit „Text so lassen“ selbst frei.',uKept:'Bleibt genau so und gilt als geprüft.',rHead:'Seit deiner letzten Bearbeitung übernommen',rSlide:'Folie {n}',rFixed:'korrigiert',rSame:'unverändert übernommen',rPending:'Korrektur steht noch aus',rLangs:'übersetzt: {l}'}
         :{edit:'Edit (E)',toLive:'Edit (E): opens the version to present for editing',earlier:'← forward',later:'back →',dup:'Duplicate',del:'Delete',undo:'Undo',redo:'Redo',notes:'Notes, reader text',
           saved:'Saved',saving:'Saving …',over:'The text runs off the slide: shorten it or split the slide',up:'↑',down:'↓',idup:'Duplicate',idel:'Remove',
           sure:'Delete this slide? (Undo brings it back)',hint:'Click a text and type. Enter saves, Esc discards.',voice:'Brand voice: ',
           typing:'In the text: Enter saves, Esc discards. After that the arrow keys turn the slides again; Page Up and Page Down always do.',
           waiting:'Saved. After “Done” the text is corrected and translated into {l}.',saved2:'Saved. After “Done” the spelling is checked.',notesFor:'Notes for this slide (for the presenter)',notesSave:'Save',done:'Done',readFor:'Reader text for this slide (stands beside the slide in the reading version)',
           tEarlier:'The slide shown swaps places with the one before it',tLater:'The slide shown swaps places with the one after it',tDup:'Insert a copy of the slide shown right after it',tDel:'Remove the slide shown from the deck',
           gMove:'Order: this slide',gSlide:'This slide',gAdd:'Insert',gText:'For the slide',gSteps:'History',
           tAdd:'Insert a new slide after the one shown',tField:'Add a text field to the slide shown that it does not use yet',tNotes:'Write presenter notes and the reader text of this slide',
           tDone:'Finish editing: changed texts are corrected and translated',
           add:'New slide',field:'Text field',addHead:'Insert a new slide after this one',fieldHead:'Add a field to this slide',noField:'This slide already uses every text field of its master.',
           overAt:'The parts marked in orange reach beyond the dashed line.',
           open:'{n} changed text(s) are corrected and translated after “Done”',end1:'Your changes are taken over',
           end2:'Spelling and grammar of the changed texts are checked now and the texts are translated into the other language. This page opens again by itself afterwards, there is nothing you need to do.',back:'The page is back …',
           gAnim:'Animation',aStep:'On click',tStep:'The parts of this slide appear one after the other on click, the first stands with the slide. Press again: everything comes together',aMove:{'':'Movement: as the deck',calm:'Movement: calmer',expressive:'Movement: stronger',off:'Movement: none'},tMove:'How much moves on this one slide: as in the whole presentation, calmer, stronger or not at all',aPlay:'▶ Play',aOrder:'Order',aOrderOk:'Save order',tOrder:'Put the click steps of this slide in an order of your own and join parts into one step',oHint:'Click the parts in the order they should come. Hold Shift to have a part come together with the one before. Esc cancels.',oNone:'This slide has no click steps. Choose “On click” first.',oSaved:'Order saved.',tPlay:'Watch the animation of this slide, with its click steps',shared:'Several presentations share this slide (“{s}”). What you change here holds for this one only, unless you press “For all presentations”.',sharedAll:'Your changes to this slide (“{s}”) hold for all presentations: Claude takes them into the library and asks whether the other presentations should be updated.',forAll:'For all presentations',tForAll:'What you change on this shared slide should hold for every presentation that uses it. Press again: for this one only',edge:'It does not go further in this direction.',lastOne:'The last slide stays.',lastItem:'The last item of a list stays: delete the slide or ask Claude for another layout.',noItem:'This list cannot be rearranged here. Tell Claude what should change.',fClose:'Go on editing',fEnd1:'Changes saved',fEnd2:'The file “{f}” is saved. It belongs into the folder this presentation is in.',fEnd2d:'The file “{f}” is in your downloads folder now. Put it into the folder this presentation is in, or upload it in the chat.',fEnd3:'For correction, translation into the other languages and PDF tell Claude: “Apply my changes to {d}”.',fHint:'Click a text and type. Enter saves, Esc discards.',gSave:'Saving',fDir:'Choose folder …',fDirOk:'Saves into the file ✓',tDir:'Choose the folder your presentations are in (or the one of this presentation), once: from then on every change is saved in the presentation at once, for later presentations in that folder too',tDirOk:'Every change is saved in “{f}” at once',fWrong:'“{f}” is neither in this folder nor below it. Please choose the folder this presentation is in.',fSaved:'Saved in “{f}”',fFail:'Could not save: ',fNeed:'Not saved in the file yet: press “Choose folder …” and name the folder of this presentation.',fOk:'Close',fEndDir:'Your changes are in “{f}”. You can show it and pass it on as it is.',fPending:' · {n} text(s) unchecked: Claude corrects them as soon as you write to it. Until then they are marked in yellow.',gCheck:'Checking',uKeep:'Keep text as it is',tKeep:'The text of this slide you changed last stays exactly as it is: it is not corrected, only translated, and counts as checked',uTip:'Unchecked: typed by you, not corrected yet',uFlag:'{n} unchecked',uTitle:'Texts you typed that are not corrected yet. Tell Claude “Apply my changes”, or release them yourself with “Keep text as it is”.',uKept:'Stays exactly as it is and counts as checked.',rHead:'Taken over since you last edited',rSlide:'Slide {n}',rFixed:'corrected',rSame:'taken over as it was',rPending:'not corrected yet',rLangs:'translated: {l}'};
  function el(tag,attrs,html){ var e=document.createElement(tag); for(var k in attrs||{}) e.setAttribute(k,attrs[k]); if(html!==undefined) e.innerHTML=html; return e; }
  var panel=el('div',{id:'vse'}), items=el('div',{id:'vsi'}), note=el('div',{id:'vsn'}), notesBox=el('div',{id:'vse-notes'}), pick=el('div',{id:'vse-pick'}), line=el('div',{id:'vsl'}),
      msg, btn, bUndo, bRedo, bNotes, bDone, bAdd, bField, bDir, bKeep, flag, area, area2, on=false;
  function button(parent,label,fn,cls){ var b=el('button',cls?{'class':cls,type:'button'}:{type:'button'},label);
    b.addEventListener('mousedown',function(e){ e.preventDefault(); }); b.addEventListener('click',function(e){ e.stopPropagation(); fn(); }); parent.appendChild(b); return b; }

  function active(){ return document.querySelector('#deck > .slide.active'); }
  function slideOf(e){ return e.closest('#deck > .slide'); }
  function num(s){ return parseInt(s.getAttribute('data-n'),10)||0; }
  function langOf(s){ return s.getAttribute('lang')||root.lang||'en'; }
  function say(text,cls){ if(!text&&on){ var s=active(), k=s&&s.getAttribute('data-shared'); if(k) text=(s.getAttribute('data-forall')?T.sharedAll:T.shared).replace('{s}',k); }      /* nothing else to say: what holds for this slide */
    msg.textContent=text||''; msg.className=cls||''; }
  function names(l){ return (l||[]).map(function(x){ return x.toUpperCase(); }).join(', '); }

  var queue=Promise.resolve();
  function send(action,body,quiet){                         /* one request after the other, in the order of the changes */
    queue=queue.catch(function(){}).then(function(){ if(!quiet) say(T.saving);
      if(FILE){ var d=local(action,body||{}); state(d); return d; }
      return fetch('/__vs/'+action,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(Object.assign({ui:DE?'de':'en'},body||{}))})
        .then(function(r){ return r.json(); })
        .then(function(d){ if(!d.ok) throw new Error(d.error||'error'); state(d); return d; });
    });
    return queue;
  }
  /* what the server reports with every answer: undo depth, texts that wait for translation */
  /* the slides by their number in the deck file, one per language; copies made in a file get numbers above those */
  var EL={}, BASE=[];
  function scan(){ EL={}; BASE=[]; document.querySelectorAll('#deck > .slide[data-n]').forEach(function(s){ var k=num(s); if(!EL[k]){ EL[k]=[]; BASE.push(k); } EL[k].push(s); }); }
  function els(n){ return EL[n]||[]; }
  function put(n,lang,path,text){ els(n).forEach(function(s){
    if(langOf(s)!==lang) return;
    if(path==='notes'){ var a=s.querySelector(':scope > .notes'); if(a) a.innerHTML=text; return; }
    s.querySelectorAll('[data-s="'+path+'"]').forEach(function(e){ if(e!==document.activeElement){ e.innerHTML=text; if(e.vsRaw!==undefined){ e.vsRaw=text; if(!on&&window.vsSplit) window.vsSplit(e); } if(e.vsCount) e.vsCount.text=e.textContent; } }); }); }
  var boot=null;
  function state(d){
    if(d.boot&&!boot) boot=d.boot;
    if(bUndo){ bUndo.disabled=!d.undo; bRedo.disabled=!d.redo; }
    if(bDone) bDone.title=d.open?T.open.replace('{n}',d.open):'';
  }
  function fail(e){ say(String(e.message||e),'bad'); }
  function reload(n){ if(FILE){ say(T.saved,'good'); return; } var s=active(); location.href=location.pathname+'?lang='+encodeURIComponent(s?langOf(s):'')+'&n='+n+'&t='+Date.now(); }

  /* overflow: the same measure the build uses (content below 930 or right of 1800 slide pixels) */
  function overflow(s){
    document.querySelectorAll('#deck .vs-over').forEach(function(e){ e.classList.remove('vs-over'); }); line.classList.remove('on');
    if(!on||!s||s.classList.contains('no-footer')||s.classList.contains('tslide')) return false;
    var sr=s.getBoundingClientRect(), sc=sr.width/1920, b=0, r=0, lim=s.classList.contains('fullbleed')?980:930, R=1800, tol=4, bad=[];      /* tol: a window that scales the slide by an odd factor measures a few tenths off */
    var sel=':scope > *:not(.header):not(.footer):not(.rbar):not(.vs-credit):not(.wedge):not(.ghost):not(.image):not(.photo):not(.biglogo):not(.notes):not(.read):not(.badge):not(canvas)';
    var t=s.querySelector('.text'); (t?t.querySelectorAll(':scope > *'):s.querySelectorAll(sel)).forEach(function(e){
      var q=e.getBoundingClientRect(); if(!q.width&&!q.height) return; var eb=(q.bottom-sr.top)/sc, er=(q.right-sr.left)/sc;
      if(eb>lim+tol||er>R+tol) bad.push(e); b=Math.max(b,eb); r=Math.max(r,er); });
    if(!bad.length) return false;
    /* show where: the texts inside the parts that reach too far (those texts themselves where they do), and the line they cross */
    bad.forEach(function(e){
      var inner=[]; e.querySelectorAll('[data-s]').forEach(function(x){ var q=x.getBoundingClientRect(); if((q.bottom-sr.top)/sc>lim+tol||(q.right-sr.left)/sc>R+tol) inner.push(x); });
      (inner.length?inner:[e]).forEach(function(x){ x.classList.add('vs-over'); });
    });
    if(b>lim+tol){ line.style.top=(sr.top+lim*sc)+'px'; line.style.left=sr.left+'px'; line.style.width=sr.width+'px'; line.classList.add('on'); }
    return true;
  }
  function unmark(){ document.querySelectorAll('#deck .vs-over').forEach(function(e){ e.classList.remove('vs-over'); }); line.classList.remove('on'); if(msg.className==='warn') say(''); }
  var seen=0;                                               /* looks in a row that found text off the slide */
  function checkOverflow(now){
    if(!on){ seen=0; unmark(); return false; }
    var over=overflow(active());
    seen=over?seen+1:0;
    if(over&&(now||seen>=2)) say(T.over+' '+T.overAt,'warn');      /* typing shows it at once; otherwise only when it holds */
    else unmark();
    return over&&(now||seen>=2);
  }
  function afterSave(d){
    var v=d.voice||[];
    note.innerHTML=''; v.forEach(function(x){ var r=el('div'); r.textContent=T.voice+x; note.appendChild(r); }); note.classList.toggle('on',!!v.length);
    document.querySelectorAll('#deck .vs-voice').forEach(function(e){ e.classList.remove('vs-voice'); });      /* show which text the findings are about */
    if(v.length&&d.path) document.querySelectorAll('#deck > .slide.active [data-s="'+d.path+'"]').forEach(function(e){ e.classList.add('vs-voice'); });
    if(window.vsFit) window.vsFit(active());                /* the body fills the slide again after a change */
    if(checkOverflow(true)) return;
    var l=names(d.waiting);
    if(FILE){ var u=unchecked().length; say(T.saved+(u?T.fPending.replace('{n}',u):''),u?'warn':'good'); return; }
    say(l?T.waiting.replace('{l}',l):(d.review?T.saved2:T.saved),'good');
  }

  /* texts */
  var before=null;
  function commit(e){
    if(before===null) return Promise.resolve(); var was=before; before=null;
    if(e.innerHTML===was) return Promise.resolve();
    var s=slideOf(e);
    return send('text',{n:num(s),lang:langOf(s),path:e.getAttribute('data-s'),html:e.innerHTML,was:was}).then(function(d){
      e.innerHTML=d.text; if(e.vsRaw!==undefined) e.vsRaw=d.text; if(e.vsCount) e.vsCount.text=e.textContent; afterSave(d);
    }).catch(function(err){ e.innerHTML=was; fail(err); });
  }
  function prepare(){
    document.querySelectorAll('#deck [data-s]').forEach(function(e){
      if(!e.vsEdit){ e.vsEdit=true;
        e.addEventListener('focus',function(){ before=e.innerHTML; showItems(e); if(msg.className!=='warn') say(T.typing); });
        e.addEventListener('blur',function(){ hideItems(); if(msg.textContent===T.typing) say(''); commit(e); });
        e.addEventListener('input',function(){ checkOverflow(true); placeItems(e); });
        e.addEventListener('paste',function(ev){ ev.preventDefault(); var t=(ev.clipboardData||window.clipboardData).getData('text/plain').replace(/\s*\n\s*/g,' '); document.execCommand('insertText',false,t); });
        e.addEventListener('click',function(ev){ if(on) ev.stopPropagation(); });
      }
      if(on&&window.vsUnsplit) window.vsUnsplit(e);         /* a heading animated word by word is one text again while it can be typed into */
      if(!on&&window.vsSplit&&e.vsRaw!==undefined&&!e.querySelector('.mw')) window.vsSplit(e);
      if(on){ e.setAttribute('contenteditable','plaintext-only'); if(e.contentEditable!=='plaintext-only') e.setAttribute('contenteditable','true'); e.setAttribute('spellcheck','true'); }
      else e.removeAttribute('contenteditable');
    });
  }
  /* keys typed into a text never reach the deck's own keys */
  ['keydown','keyup','keypress'].forEach(function(type){
    window.addEventListener(type,function(e){
      var t=e.target, typing=t&&(t.isContentEditable||t===area||t===area2);
      if(typing){
        e.stopPropagation();
        if(t===area||t===area2){ if(type==='keydown'&&e.key==='Escape'){ openNotes(false); } return; }
        var dir=type==='keydown'?turn(e,t):0;               /* leaving the text at its end or its start turns the slide */
        if(dir){ e.preventDefault(); t.blur(); move(dir); }
        else if(type==='keydown'&&e.key==='Enter'&&!e.shiftKey){ e.preventDefault(); t.blur(); }
        else if(type==='keydown'&&e.key==='Escape'){ if(before!==null){ t.innerHTML=before; before=null; } t.blur(); checkOverflow(); }
        return;
      }
      if(type!=='keydown') return;
      if((e.key==='e'||e.key==='E')&&!e.metaKey&&!e.ctrlKey&&!e.altKey){ e.preventDefault(); e.stopPropagation(); toggle(); }
      else if(on&&(e.metaKey||e.ctrlKey)&&(e.key==='z'||e.key==='Z')){ e.preventDefault(); e.stopPropagation(); step(e.shiftKey?'redo':'undo'); }
    },true);
  });

  /* turning the slide out of a text: Page Up and Page Down always; an arrow key when the cursor already stands at
     the end (forward) or at the start (back) of the text */
  function caret(t){ var s=window.getSelection(); if(!s.rangeCount||!s.isCollapsed) return null;
    var r=document.createRange(); r.selectNodeContents(t); r.setEnd(s.focusNode,s.focusOffset); var at=r.toString().length, all=t.textContent.length;
    return at>=all?'end':(at===0?'start':'in'); }
  function turn(e,t){
    if(e.metaKey||e.ctrlKey||e.altKey||e.shiftKey) return 0;
    if(e.key==='PageDown') return 1; if(e.key==='PageUp') return -1;
    var c=caret(t);
    if((e.key==='ArrowRight'||e.key==='ArrowDown')&&c==='end') return 1;
    if((e.key==='ArrowLeft'||e.key==='ArrowUp')&&c==='start') return -1;
    return 0; }
  function move(dir){ var k=parseInt((location.hash.match(/\d+/)||[1])[0],10)+dir; if(window.vsGo) window.vsGo(k); }

  /* list items: the small bar beside the text that has the focus */
  var cur=null;
  function inList(e){ return /(^|\.)\d+(\.|$)/.test(e.getAttribute('data-s')); }
  function placeItems(e){ if(!items.classList.contains('on')) return; var r=e.getBoundingClientRect(), w=items.offsetWidth||200;      /* at the right end, where it covers least */
    items.style.left=Math.max(8,Math.min(window.innerWidth-w-8,r.right-w))+'px'; items.style.top=(r.top>52?r.top-40:r.bottom+8)+'px'; }
  function showItems(e){ cur=e; if(!inList(e)){ items.classList.remove('on'); return; } items.classList.add('on'); placeItems(e); }
  function hideItems(){ setTimeout(function(){ if(!document.activeElement||!document.activeElement.isContentEditable) items.classList.remove('on'); },0); }
  function itemOp(op){ var e=cur; if(!e) return; var s=slideOf(e), body={n:num(s),lang:langOf(s),path:e.getAttribute('data-s'),op:op};
    commit(e).then(function(){ return send('item',body); }).then(function(d){ reload(d.reload); if(FILE&&e.isConnected) e.focus(); }).catch(fail); }
  function pending(){ var a=document.activeElement; return a&&a.isContentEditable?commit(a):Promise.resolve(); }
  function slideOp(op){ var s=active(); if(!s) return; if(op==='delete'&&!confirm(T.sure)) return;
    pending().then(function(){ return send('slide',{n:num(s),op:op}); }).then(function(d){ reload(d.reload); }).catch(fail); }
  function step(what){ var s=active(); pending().then(function(){ return send(what,{n:s?num(s):1}); }).then(function(d){ reload(d.reload); }).catch(fail); }

  /* how the slide shown moves: its click steps, how much moves on it, and a look at it */
  var bStep, bMove, bOrder, bAll, playing=null;
  function stepOf(s){ var a=s.getAttribute('data-step'); return a==='1'||(a===null&&!!s.querySelector('.f')); }
  function animState(){ var s=active(); if(!s||!bStep) return; bStep.classList.toggle('on',stepOf(s));
    if(bAll){ var sh=s.getAttribute('data-shared'); bAll.style.display=sh?'':'none'; bAll.classList.toggle('on',!!s.getAttribute('data-forall')); } bMove.textContent=T.aMove[s.getAttribute('data-move')||'']||T.aMove['']; }
  function animAttr(key){ return key==='step'?'data-step':key==='order'?'data-order':key==='all'?'data-forall':'data-move'; }
  function setAnim(n,key,value){ els(n).forEach(function(s){ var attr=animAttr(key);
      if(value===null||value===undefined||value===''||(key==='all'&&!value)) s.removeAttribute(attr); else s.setAttribute(attr,key==='step'?(value?'1':'0'):key==='all'?'1':value);
      if(key!=='move'&&window.vsStep) window.vsStep(s); }); steps(); animState(); }
  function anim(key,value){ var s=active(); if(!s) return;
    pending().then(function(){ return send('anim',{n:num(s),key:key,value:value}); }).then(function(d){ reload(d.reload); }).catch(fail); }
  function play(){ var s=active(); if(!s||playing) return; pending();
    root.setAttribute('data-motion',motionWas&&motionWas!=='off'?motionWas:'standard'); if(window.vsReplay) window.vsReplay();
    function end(){ clearInterval(playing); playing=null; if(on){ root.setAttribute('data-motion','off'); steps(); } }
    var wait=2; playing=setInterval(function(){ if(active()!==s||!on) return end(); if(wait-->0) return; if(!(window.vsStepOpen&&window.vsStepOpen())){ clearInterval(playing); playing=setTimeout(end,1600); } },800); }

  /* the order of the click steps by hand: every step of the slide shown gets its number; the parts are clicked in
     the new order (with Shift: together with the one before); the result goes to the deck as "order" */
  var ordering=null, badges=[];
  function unbadge(){ badges.forEach(function(b){ b.remove(); }); badges=[]; }
  function badge(){ unbadge(); if(!ordering) return;
    ordering.plan.groups.forEach(function(els,i){ var at=-1; ordering.pick.forEach(function(p,k){ if(p.indexOf(i)>=0) at=k; });
      var r=els[0].getBoundingClientRect(), b=el('div',{'class':'vse-badge'+(at<0?'':' set')},String(at<0?i+1:at+1));
      b.style.left=Math.max(4,r.left-14)+'px'; b.style.top=Math.max(4,r.top-14)+'px'; document.body.appendChild(b); badges.push(b);
      els.forEach(function(x){ x.classList.add('vse-part'); }); }); }
  function stopOrder(save){ var o=ordering; if(!o) return; ordering=null; unbadge(); bOrder.textContent=T.aOrder; bOrder.classList.remove('on');
    document.querySelectorAll('#deck .vse-part').forEach(function(x){ x.classList.remove('vse-part'); });
    if(!save||!o.pick.length) return say('');
    var seq=o.pick.slice(), used={}; seq.forEach(function(p){ p.forEach(function(i){ used[i]=1; }); });
    o.plan.groups.forEach(function(g,i){ if(!used[i]) seq.push([i]); });
    var out=seq.map(function(p){ var m=[]; p.forEach(function(i){ m=m.concat(o.plan.steps[i]); }); return m; }),
        same=!o.plan.zero.length&&out.every(function(m,i){ return m.length===1&&m[0]===i+1; });
    if(o.plan.zero.length) out.unshift([0].concat(o.plan.zero));
    say(T.oSaved,'good'); anim('order',same?'':out.map(function(m){ return m.join('+'); }).join(','));
  }
  function startOrder(){ var s=active(); if(!s) return; if(ordering) return stopOrder(true);
    var plan=window.vsStepPlan&&window.vsStepPlan(s); steps();
    if(!plan||!plan.groups.length) return say(T.oNone,'warn');
    pending(); ordering={s:s,plan:plan,pick:[]}; bOrder.textContent=T.aOrderOk; bOrder.classList.add('on'); say(T.oHint); badge(); }
  function orderClick(e){ if(!ordering) return; var t=e.target;
    if(t.closest&&t.closest('#ctl')) return;
    e.preventDefault(); e.stopPropagation(); if(e.type!=='click') return;
    var i=-1; ordering.plan.groups.forEach(function(els,k){ if(i<0&&els.some(function(x){ return x===t||x.contains(t); })) i=k; });
    if(i<0) return;
    ordering.pick.forEach(function(p){ var at=p.indexOf(i); if(at>=0) p.splice(at,1); }); ordering.pick=ordering.pick.filter(function(p){ return p.length; });
    if(e.shiftKey&&ordering.pick.length) ordering.pick[ordering.pick.length-1].push(i); else ordering.pick.push([i]);
    badge(); }
  ['mousedown','click'].forEach(function(k){ document.addEventListener(k,orderClick,true); });
  document.addEventListener('keydown',function(e){ if(ordering&&e.key==='Escape'){ e.preventDefault(); e.stopPropagation(); stopOrder(false); } },true);

  /* speaker notes of the slide that is shown */
  function notesText(s){ var a=s&&s.querySelector(':scope > .notes'); if(!a) return '';
    return a.innerHTML.replace(/<\/p>\s*<p[^>]*>/gi,'\n\n').replace(/<br\s*\/?>/gi,'\n').replace(/<[^>]+>/g,'').replace(/&amp;/g,'&').replace(/&lt;/g,'<').replace(/&gt;/g,'>').replace(/&nbsp;/g,' ').trim(); }
  function plainOf(a){ return !a?'':a.innerHTML.replace(/<\/p>\s*<p[^>]*>/gi,'\n\n').replace(/<br\s*\/?>/gi,'\n').replace(/<[^>]+>/g,'').replace(/&amp;/g,'&').replace(/&lt;/g,'<').replace(/&gt;/g,'>').replace(/&nbsp;/g,' ').trim(); }
  function readText(s){ return plainOf(s&&s.querySelector(':scope > .read:not([data-from])')); }
  var notesWas='', readWas='';
  function fillNotes(){ var s=active(); area.value=notesWas=notesText(s); area2.value=readWas=readText(s); }
  function openNotes(show){ notesBox.classList.toggle('on',show); bNotes.classList.toggle('on',show); if(show){ openPick(null); fillNotes(); area.focus(); } }
  function saveNotes(){ var s=active(); if(!s) return; var jobs=[];
    if(area.value.trim()!==notesWas) jobs.push(send('notes',{n:num(s),lang:langOf(s),text:area.value}).then(function(d){
      var a=s.querySelector(':scope > .notes'); if(!a&&d.text){ a=el('aside',{'class':'notes'}); s.appendChild(a); } if(a) a.innerHTML=d.text; notesWas=area.value.trim(); return d; }));
    if(area2.value.trim()!==readWas) jobs.push(send('read',{n:num(s),lang:langOf(s),text:area2.value}).then(function(d){
      var a=s.querySelector(':scope > .read'); if(!a&&d.text){ a=el('aside',{'class':'read'}); s.appendChild(a); } if(a){ a.removeAttribute('data-from'); a.innerHTML=d.text; } readWas=area2.value.trim(); return d; }));
    Promise.all(jobs).then(function(r){ if(r.length) afterSave(r[r.length-1]); else say(T.saved,'good'); }).catch(fail); }

  /* a new slide from a master, a field this slide does not use yet */
  function openPick(what){
    var same=pick.getAttribute('data-what')===what&&pick.classList.contains('on');
    pick.classList.remove('on'); pick.innerHTML=''; bAdd.classList.remove('on'); bField.classList.remove('on'); pick.removeAttribute('data-what');
    if(!what||same) return;
    notesBox.classList.remove('on'); bNotes.classList.remove('on');
    var s=active(); if(!s) return;
    send('library',{n:num(s)},true).then(function(d){
      pick.setAttribute('data-what',what); pick.classList.add('on'); (what==='add'?bAdd:bField).classList.add('on');
      pick.appendChild(el('label',{},what==='add'?T.addHead:T.fieldHead));
      var list=el('div',{'class':'list'}); pick.appendChild(list);
      if(what==='add') d.masters.forEach(function(m){ var b=button(list,'',function(){ send('add',{n:num(s),master:m.name}).then(function(x){ reload(x.reload); }).catch(fail); });
        b.appendChild(el('b',{},m.title)); var u=el('small'); u.textContent=m.use; b.appendChild(u); });
      else if(!d.fields.length){ var p=el('p'); p.textContent=T.noField; pick.appendChild(p); }
      else d.fields.forEach(function(f){ var b=button(list,'',function(){ send('fill',{n:num(s),slot:f.slot}).then(function(x){ reload(x.reload); }).catch(fail); });
        b.appendChild(el('b',{},f.slot)); var u=el('small'); u.textContent=f.about; b.appendChild(u); });
    }).catch(fail);
  }
  function finish(){ if(FILE) return finishFile(); pending().then(function(){ return send('done',{}); }).then(function(d){
      var s=active(), back=location.pathname+'?lang='+encodeURIComponent(s?langOf(s):'')+'&n='+(s?num(s):1)+'&t='+Date.now();
      toggle(false);
      if(!d.stop) return;                                   /* nothing to correct or translate: simply back to the deck, the pencil opens the editing again */
      try{ sessionStorage.setItem('vs-edit','1'); }catch(e){}      /* open again when the page comes back */
      var o=el('div',{id:'vsend'}), h=el('b'), p=el('p'); h.textContent=T.end1; p.textContent=T.end2;
      o.appendChild(el('i',{'class':'spin'})); o.appendChild(h); o.appendChild(p); document.body.appendChild(o);
      btn.style.display='none';
      /* the server is gone while the texts are corrected and translated; when it answers again, show the deck again */
      var t=setInterval(function(){                         /* a new run of the server answers with another boot number */
        var c=window.AbortController?new AbortController():null, k=setTimeout(function(){ if(c) c.abort(); },1200);
        fetch('/__vs/state',{method:'POST',headers:{'Content-Type':'application/json'},body:'{}',cache:'no-store',signal:c?c.signal:undefined}).then(function(r){ return r.json(); })
          .then(function(x){ clearTimeout(k); if(x&&x.ok&&x.boot&&x.boot!==boot){ clearInterval(t); h.textContent=T.back; location.href=back; } })
          .catch(function(){ clearTimeout(k); });
      },1500);
    }).catch(fail); }

  /* ---- opened as a file: no server. Changes are kept in a journal (in this browser, so a reload loses nothing) and
     written into one file when the user is done; `vs.py apply` brings that file into deck.json. Everything shows
     on the page at once: texts, notes and reader text, slides and list items moved, copied and deleted. */
  var INFO=window.VS_EDIT||{deck:'deck',base:''}, KEY='vs-edits:'+INFO.deck, J={base:INFO.base,ops:[],redo:[]};
  function keep(){ J.t=Date.now(); try{ localStorage.setItem(KEY,JSON.stringify(J)); }catch(e){} saveSoon(); }

  /* Saving without a server (Chrome, Edge): the user names the folder of the presentation once. From then on every
     change is written at once into the presentation file itself (as a block of changes it applies when it is
     opened, wherever that is) and into <deck>.edits.json beside it, for `vs.py apply`. */
  var DIR=null, ROOT=null, saveTimer=null, saving=Promise.resolve(), FSA=!!window.showDirectoryPicker&&!!window.indexedDB;
  var FILE_NAME=decodeURIComponent((location.pathname.split('/').pop()||''));
  function idb(mode,fn){ return new Promise(function(res,rej){ var r=indexedDB.open('vibeupslides',1);
    r.onupgradeneeded=function(){ r.result.createObjectStore('dirs'); }; r.onerror=function(){ rej(r.error); };
    r.onsuccess=function(){ var tx=r.result.transaction('dirs',mode), q=fn(tx.objectStore('dirs')); tx.oncomplete=function(){ res(q&&q.result); }; tx.onerror=function(){ rej(tx.error); }; }; }); }
  function may(h,ask){ if(!h) return Promise.resolve(false); var o={mode:'readwrite'};
    return h.queryPermission(o).then(function(p){ return p==='granted'||(ask?h.requestPermission(o).then(function(q){ return q==='granted'; }):false); }).catch(function(){ return false; }); }
  function allowed(ask){ return may(DIR,ask); }
  /* The folder of this presentation inside a folder the user named: the folder itself, or one below it (three
     levels). The file is known by its name and by the mark of the deck file it was built from. */
  async function locate(h,depth){
    try{ var f=await h.getFileHandle(FILE_NAME), t=await (await f.getFile()).text(); if(!INFO.base||t.indexOf('"base": "'+INFO.base+'"')>=0) return h; }catch(e){}
    if(depth<=0) return null;
    for await (var c of h.values()){
      if(c.kind!=='directory'||/^(\.|assets$|images$|shots|sources$|research$|node_modules$)/.test(c.name)) continue;
      var r=await locate(c,depth-1); if(r) return r;
    }
    return null;
  }
  function fromRoot(ask){                                    /* a folder named for an earlier presentation: this one may lie in it too */
    if(DIR||!ROOT) return Promise.resolve(!!DIR);
    return may(ROOT,ask).then(function(ok){ return ok?locate(ROOT,3):null; }).then(function(d){ if(d){ DIR=d; idb('readwrite',function(s){ return s.put(d,INFO.deck); }); fileState(); } return !!d; }).catch(function(){ return false; });
  }
  function fileState(){ if(!bDir) return; allowed(false).then(function(ok){
      bDir.style.display=FSA?'':'none'; bDir.textContent=ok?T.fDirOk:T.fDir; bDir.title=ok?T.tDirOk.replace('{f}',FILE_NAME):T.tDir; bDir.classList.toggle('good',ok); }); }
  function connect(pick){                                    /* a user's click: ask for the folder, or for the permission of the one from last time */
    if(!FSA) return Promise.resolve(false);
    var got=(DIR&&!pick)?Promise.resolve(null):((!pick&&ROOT)?fromRoot(true).then(function(ok){ return ok?null:window.showDirectoryPicker({id:'vibeupslides',mode:'readwrite'}); }):window.showDirectoryPicker({id:'vibeupslides',mode:'readwrite'}));
    return got.then(function(h){ if(!h) return;              /* h: a folder just chosen. It is kept for the presentations to come as well. */
        return locate(h,3).then(function(d){ if(!d) throw new Error(T.fWrong.replace('{f}',FILE_NAME));
          DIR=d; ROOT=h; return idb('readwrite',function(s){ s.put(h,'*root'); return s.put(d,INFO.deck); }); }); })
      .then(function(){ return allowed(true); }).then(function(ok){ fileState(); if(ok) return write().then(function(){ return true; }); return false; });
  }
  function write(){                                          /* one writing after the other */
    saving=saving.catch(function(){}).then(function(){ return allowed(false); }).then(function(ok){ if(!ok) return false;
      var data=JSON.stringify({vibeupslides_edits:1,deck:INFO.deck,base:INFO.base,t:J.t,ops:J.ops},null,1);
      function put(name,text){ return DIR.getFileHandle(name,{create:true}).then(function(h){ return h.createWritable(); }).then(function(w){ return w.write(text).then(function(){ return w.close(); }); }); }
      return DIR.getFileHandle(FILE_NAME).then(function(h){ return h.getFile(); }).then(function(f){ return f.text(); }).then(function(html){
        var open='<scr'+'ipt type="application/json" id="vs-'+'journal">', close='</scr'+'ipt>';      /* never written out whole: this script stands in the file it searches */
        var block=open+JSON.stringify(J).replace(/</g,'\\u003c')+close;
        var re=new RegExp(open.replace(/[\/"]/g,'\\$&')+'[\\s\\S]*?'+close.replace(/\//g,'\\/')+'\\n?');
        html=re.test(html)?html.replace(re,function(){ return J.ops.length?block+'\n':''; }):(J.ops.length?html.replace(/<\/body>(?![\s\S]*<\/body>)/,function(){ return block+'\n</body>'; }):html);
        return put(FILE_NAME,html); }).then(function(){ return put(INFO.deck+'.edits.json',data); }).then(function(){ if(on){ var u=unchecked().length; say(T.fSaved.replace('{f}',FILE_NAME)+(u?T.fPending.replace('{n}',u):''),u?'warn':'good'); } return true; });
    }).catch(function(e){ say(T.fFail+String(e&&e.message||e),'bad'); return false; });
    return saving;
  }
  function saveSoon(){ if(!FILE||!DIR) return; clearTimeout(saveTimer); saveTimer=setTimeout(write,500); }
  function esc(t){ return String(t).replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;'); }
  function setWhole(n,lang,key,html){ els(n).forEach(function(s){ if(langOf(s)!==lang) return;
    var a=s.querySelector(':scope > .'+key); if(!a&&html){ a=el('aside',{'class':key}); s.appendChild(a); } if(a){ a.removeAttribute('data-from'); a.innerHTML=html; } }); }
  function show(o,back){                                     /* put one change on the page, or take it back */
    if(o.a==='text') put(o.n,o.lang,o.path,back?o.was:o.html);
    else if(o.a==='notes'||o.a==='read') setWhole(o.n,o.lang,o.a,back?o.wasHtml:o.html);
    else if(o.a==='anim') setAnim(o.n,o.key,back?o.was:o.value);
  }
  /* Where a text of a list stands after one change of that list (as edit._remark does it for the deck file) */
  function itemOf(path){ var p=String(path||'').split('.'); for(var i=p.length-1;i>0;i--) if(/^\d+$/.test(p[i])) return {b:p.slice(0,i).join('.'),i:parseInt(p[i],10)}; return null; }
  function remap(path,x){ var it=itemOf(x.path); if(!it||!path||path.indexOf(it.b+'.')!==0) return path;
    var rest=path.slice(it.b.length+1).split('.'), k=parseInt(rest[0],10), i=it.i; if(isNaN(k)) return path;
    if(x.op==='up'){ if(i>1) k=k===i?i-1:(k===i-1?i:k); }
    else if(x.op==='down') k=k===i?i+1:(k===i+1?i:k);
    else if(x.op==='duplicate'){ if(k>i) k++; }
    else if(x.op==='delete'){ if(k===i) return null; if(k>i) k--; }
    rest[0]=k; return it.b+'.'+rest.join('.'); }
  function unchecked(){                                      /* texts the user typed that nobody corrected yet and that they did not release: the last change of each place counts. [{o: the change, n, lang, path: where it stands now}] */
    var last={};
    J.ops.forEach(function(o){
      if(o.a==='text'||o.a==='notes'||o.a==='read') last[o.n+'|'+o.lang+'|'+(o.path||o.a)]={o:o,n:o.n,lang:o.lang,path:o.path||o.a};
      else if(o.a==='item'||(o.a==='slide'&&o.op==='duplicate')){ var next={};
        Object.keys(last).forEach(function(k){ var u=last[k];
          if(u.n!==o.n){ next[k]=u; return; }
          if(o.a==='slide'){ next[k]=u; next[o.id+'|'+u.lang+'|'+u.path]={o:u.o,n:o.id,lang:u.lang,path:u.path}; return; }
          var p=remap(u.path,o); if(p) next[u.n+'|'+u.lang+'|'+p]={o:u.o,n:u.n,lang:u.lang,path:p}; });
        last=next; } });
    var there=order();
    return Object.keys(last).map(function(k){ return last[k]; }).filter(function(u){ return !u.o.ok&&there.indexOf(u.n)>=0; });
  }
  function flags(){
    document.querySelectorAll('#deck .vs-raw').forEach(function(e){ e.classList.remove('vs-raw'); e.removeAttribute('title'); });
    var u=unchecked();
    u.forEach(function(o){ if(o.o.a!=='text') return; els(o.n).forEach(function(s){ if(langOf(s)!==o.lang) return;
      s.querySelectorAll('[data-s="'+o.path+'"]').forEach(function(e){ e.classList.add('vs-raw'); e.title=T.uTip; }); }); });
    if(flag){ flag.textContent=u.length?T.uFlag.replace('{n}',u.length):''; flag.title=T.uTitle; flag.style.display=u.length?'':'none'; }
    if(bKeep) bKeep.disabled=!lastRaw();
    return u.length;
  }
  function lastRaw(){ var u=unchecked(), a=document.activeElement, s=active(); if(!s) return null;
    var here=u.filter(function(o){ return o.n===num(s)&&o.lang===langOf(s); }); if(!here.length) return null;
    if(a&&a.getAttribute&&a.getAttribute('data-s')){ var m=here.filter(function(o){ return o.path===a.getAttribute('data-s'); }); if(m.length) return m[0]; }
    return here[here.length-1]; }
  function release(){ var u=lastRaw(); if(!u) return; u.o.ok=true; keep(); flags(); say(T.uKept,'good'); }

  /* Slides moved, copied and deleted in a file: the page shows the new order at once. The order is worked out from
     the changes each time (as `vs.py apply` will do it in the deck file), so undoing is leaving a change out. */
  function shift(o,x){ var i=o.indexOf(x.n); if(i<0) return false;
    if(x.op==='earlier'){ if(i<1) return false; o.splice(i-1,2,o[i],o[i-1]); }
    else if(x.op==='later'){ if(i>o.length-2) return false; o.splice(i,2,o[i+1],o[i]); }
    else if(x.a==='add'||x.op==='duplicate') o.splice(i+1,0,x.id);
    else if(x.op==='delete'){ if(o.length<2) return false; o.splice(i,1); }
    else return false;
    return true; }
  function order(){ var o=BASE.slice(); J.ops.forEach(function(x){ if(x.a==='slide'||x.a==='add') shift(o,x); }); return o; }
  function newId(){ var m=0; BASE.forEach(function(k){ m=Math.max(m,k); }); J.ops.concat(J.redo||[]).forEach(function(x){ if(x.id) m=Math.max(m,x.id); }); return m+1; }
  function copy(x){                                          /* the copy of a slide as it stands at this moment, in every language */
    if(EL[x.id]) return;
    EL[x.id]=els(x.n).map(function(s){ var c=s.cloneNode(true); c.setAttribute('data-n',x.id); c.classList.remove('active','leave','back');
      c.querySelectorAll('iframe.mlive').forEach(function(f){ f.remove(); });
      var a=s.querySelectorAll('[data-s],.mcountup'), b=c.querySelectorAll('[data-s],.mcountup');
      for(var i=0;i<a.length&&i<b.length;i++){ if(a[i].vsRaw!==undefined) b[i].vsRaw=a[i].vsRaw; if(a[i].vsCount) b[i].vsCount={n:a[i].vsCount.n,sep:a[i].vsCount.sep,text:a[i].vsCount.text,ms:a[i].vsCount.ms}; b[i].classList.remove('vs-over','vs-voice'); }
      if(c.classList.contains('qslide')&&window.vsQuizInit){ window.vsQuizInit(c); if(window.vsQuizWatch) window.vsQuizWatch(c); }      /* a copied quiz or timer works at once */
      if(c.classList.contains('tslide')&&window.vsTimerInit) window.vsTimerInit(c);
      return c; });
  }
  function make(x){                                          /* a new slide from a master: the build left one per language in the page */
    if(EL[x.id]) return true;
    var m=(INFO.masters||[]).filter(function(k){ return k.name===x.master; })[0]; if(!m) return false;
    EL[x.id]=Object.keys(m.html).map(function(l){ var t=document.createElement('template'); t.innerHTML=m.html[l]; var s=t.content.querySelector('.slide'); if(!s) return null;
      s.setAttribute('data-n',x.id); s.querySelectorAll('.mtext[data-s]').forEach(function(e){ e.vsRaw=e.innerHTML; }); return s; }).filter(function(s){ return s; });
    return EL[x.id].length>0; }
  /* A text field the slide did not use yet, in a file: the build left the slide once more with that field filled.
     It takes the slide's place; what was typed into the slide before is put into it again. One field per slide. */
  var WAS=window.WeakMap?new WeakMap():null;
  function fieldsFor(n){ var l=(INFO.fields||{})[n]||[]; if(BASE.indexOf(n)<0||J.ops.some(function(x){ return x.n===n&&(x.a==='fill'||x.a==='item'); })) return []; return l; }
  function swapIn(x){
    var f=((INFO.fields||{})[x.n]||[]).filter(function(k){ return k.slot===x.slot; })[0], old=els(x.n); if(!f||!old.length||!WAS) return false;
    var fresh=old.map(function(s){ var h=f.html[langOf(s)]; if(!h) return s; var t=document.createElement('template'); t.innerHTML=h; var c=t.content.querySelector('.slide'); if(!c) return s;
      ['active','off','vs-dk'].forEach(function(k){ if(s.classList.contains(k)) c.classList.add(k); });
      c.querySelectorAll('.mtext[data-s]').forEach(function(e){ e.vsRaw=e.innerHTML; });
      var cr=s.querySelector(':scope > .vs-credit'); if(cr) c.appendChild(cr);
      if(s.parentNode) s.parentNode.replaceChild(c,s); return c; });
    WAS.set(x,old); EL[x.n]=fresh;
    J.ops.forEach(function(o){ if(o!==x&&o.n===x.n&&(o.a==='text'||o.a==='notes'||o.a==='read'||o.a==='anim')) show(o,false); });
    if(window.vsRescan) window.vsRescan(inLang(x.n)); prepare(); steps(); return true; }
  function swapOut(x){ var old=WAS&&WAS.get(x), now=els(x.n); if(!old) return;
    now.forEach(function(c,i){ var s=old[i]; if(!s||s===c) return; ['active','off'].forEach(function(k){ s.classList.toggle(k,c.classList.contains(k)); });
      var cr=c.querySelector(':scope > .vs-credit'); if(cr) s.appendChild(cr); if(c.parentNode) c.parentNode.replaceChild(s,c); });
    EL[x.n]=old; if(window.vsRescan) window.vsRescan(inLang(x.n)); prepare(); steps(); }
  var END=null, LOOSE=null;
  function lay(showing){
    var deck=document.getElementById('deck'), o=order(), list=[];
    if(!END){ var n=document.querySelectorAll('#deck > .slide[data-n]'); if(!n.length) return; END=document.createComment('slides'); deck.insertBefore(END,n[n.length-1].nextSibling);
      LOOSE=[]; document.querySelectorAll('#deck > .slide:not([data-n])').forEach(function(s){ var p=s.previousElementSibling; while(p&&!(p.classList.contains('slide')&&p.hasAttribute('data-n'))) p=p.previousElementSibling; if(p) LOOSE.push({s:s,after:num(p)}); }); }
    o.forEach(function(k){ list=list.concat(els(k)); });
    Object.keys(EL).forEach(function(k){ if(o.indexOf(parseInt(k,10))<0) EL[k].forEach(function(s){ if(s.parentNode) s.parentNode.removeChild(s); }); });
    for(var i=list.length-1, ref=END;i>=0;i--){ if(list[i].nextSibling!==ref||list[i].parentNode!==deck) deck.insertBefore(list[i],ref); ref=list[i]; }
    LOOSE.forEach(function(l){ var e=els(o.indexOf(l.after)>=0?l.after:o[0]), last=e[e.length-1]; if(last&&l.s.previousSibling!==last) deck.insertBefore(l.s,last.nextSibling); });      /* the contents page stays behind its slide */
    var credit={}; Object.keys(EL).forEach(function(k){ EL[k].forEach(function(s){ var c=s.querySelector(':scope > .vs-credit'); if(!c) return; var l=langOf(s); if(credit[l]) c.parentNode.removeChild(c); else credit[l]=c; }); });
    list.forEach(function(s){ var l=langOf(s); if(credit[l]) credit[l].last=s; });      /* who made the deck stays on the last slide */
    Object.keys(credit).forEach(function(l){ var c=credit[l]; if(c.last&&c.parentNode!==c.last) c.last.insertBefore(c,c.last.querySelector(':scope > .header, :scope > .footer')); });
    if(window.vsRescan) window.vsRescan(showing);
    prepare(); steps(); seen=0; checkOverflow();
  }
  function inLang(n){ var s=active(), l=s?langOf(s):'', hit=null; els(n).forEach(function(e){ if(!hit&&langOf(e)===l) hit=e; }); return hit; }

  /* List items moved, copied and removed in a file. The element of an item is found from the texts marked in it:
     the part of the list that holds the texts of this item and none of its neighbour's. */
  var GONE=window.WeakMap?new WeakMap():null;
  function itemTexts(s,base,i){ var pre=base+'.'+i; return Array.prototype.filter.call(s.querySelectorAll('[data-s]'),function(e){ var p=e.getAttribute('data-s'); return p===pre||p.indexOf(pre+'.')===0; }); }
  function itemCount(s,base){ var m=0; s.querySelectorAll('[data-s]').forEach(function(e){ var p=e.getAttribute('data-s'); if(p.indexOf(base+'.')===0){ var k=parseInt(p.slice(base.length+1),10); if(k>m) m=k; } }); return m; }
  function itemPair(s,base,i,j){                             /* [element of item i, element of item j], side by side in one parent; null where the master builds the list another way */
    var a=itemTexts(s,base,i), b=itemTexts(s,base,j); if(!a.length||!b.length) return null;
    var p=a[0]; while(p&&p!==s&&!a.concat(b).every(function(x){ return p.contains(x); })) p=p.parentNode;
    if(!p) return null;
    function child(set,other){ var c=set[0]; if(c===p) return null; while(c.parentNode!==p) c=c.parentNode;
      return set.every(function(x){ return c.contains(x); })&&!other.some(function(x){ return c.contains(x); })?c:null; }
    var ea=child(a,b), eb=child(b,a); return ea&&eb?[ea,eb]:null; }
  function renumber(root,base,fn){ var l=Array.prototype.slice.call(root.querySelectorAll('[data-s]')); if(root.hasAttribute&&root.hasAttribute('data-s')) l.push(root);
    l.forEach(function(e){ var p=e.getAttribute('data-s'); if(p.indexOf(base+'.')!==0) return; var rest=p.slice(base.length+1).split('.'), k=parseInt(rest[0],10); if(isNaN(k)) return;
      rest[0]=fn(k); e.setAttribute('data-s',base+'.'+rest.join('.')); }); }
  function itemPlan(s,x){                                    /* what one change of a list does on one slide: null if the list is shorter here, false if it cannot be shown */
    var it=itemOf(x.path), i=it.i, n=itemCount(s,it.b), pair;
    if(i>n) return null;
    if(x.op==='up'){ if(i<2) throw new Error(T.edge); pair=itemPair(s,it.b,i,i-1); return pair?function(){ pair[0].parentNode.insertBefore(pair[0],pair[1]); renumber(s,it.b,function(k){ return k===i?i-1:(k===i-1?i:k); }); }:false; }
    if(x.op==='down'){ if(i>=n) throw new Error(T.edge); pair=itemPair(s,it.b,i,i+1); return pair?function(){ pair[0].parentNode.insertBefore(pair[1],pair[0]); renumber(s,it.b,function(k){ return k===i?i+1:(k===i+1?i:k); }); }:false; }
    if(n<2){ if(x.op==='delete') throw new Error(T.lastItem); return false; }
    pair=itemPair(s,it.b,i,i>1?i-1:i+1); if(!pair) return false;
    if(x.op==='duplicate') return function(){ var c=pair[0].cloneNode(true); c.querySelectorAll('.vs-raw,.vs-over,.vs-voice').forEach(function(e){ e.classList.remove('vs-raw','vs-over','vs-voice'); });
      renumber(s,it.b,function(k){ return k>i?k+1:k; }); renumber(c,it.b,function(){ return i+1; }); pair[0].parentNode.insertBefore(c,pair[0].nextSibling); };
    if(x.op==='delete') return function(){ var next=pair[0].nextSibling, par=pair[0].parentNode; par.removeChild(pair[0]); renumber(s,it.b,function(k){ return k>i?k-1:k; });
      return function(){ renumber(s,it.b,function(k){ return k>=i?k+1:k; }); par.insertBefore(pair[0],next&&next.parentNode===par?next:null); }; };
    return false; }
  function doItem(x){
    var plans=[]; els(x.n).forEach(function(s){ var p=itemPlan(s,x); if(p===false) throw new Error(T.noItem); if(p) plans.push(p); });
    if(!plans.length) throw new Error(T.noItem);
    var back=plans.map(function(p){ return p(); }); if(GONE) GONE.set(x,back);
    prepare(); steps(); }
  function undoItem(x){ var it=itemOf(x.path), back=GONE&&GONE.get(x);
    if(x.op==='up') doItem({n:x.n,path:it.b+'.'+(it.i-1),op:'down'});
    else if(x.op==='down') doItem({n:x.n,path:it.b+'.'+(it.i+1),op:'up'});
    else if(x.op==='duplicate') doItem({n:x.n,path:it.b+'.'+(it.i+1),op:'delete'});
    else if(back){ back.forEach(function(f){ if(f) f(); }); prepare(); steps(); } }

  function local(action,b){
    var out={ok:true}, o;
    if(action==='text'){ var t=String(b.html||'').replace(/<(?!\/?(em|strong|b|i|u|sup|sub|br|mark|small)\b)[^>]*>/gi,'').trim();
      if(!t.replace(/<[^>]+>/g,'').trim()) throw new Error(DE?'Ein leerer Text würde das Element entfernen: die Folie löschen oder den Text kürzen.':'an empty text would remove the element');
      o={a:'text',n:b.n,lang:b.lang,path:b.path,html:t,was:b.was}; J.ops.push(o); J.redo=[]; out.text=t; out.path=b.path; out.review=true; }
    else if(action==='notes'||action==='read'){ var h=esc(String(b.text||'').trim()).replace(/\n\s*\n/g,'<br><br>');
      var a=document.querySelector('#deck > .slide.active > .'+action);
      o={a:action,n:b.n,lang:b.lang,html:h,wasHtml:a&&!a.hasAttribute('data-from')?a.innerHTML:''}; J.ops.push(o); J.redo=[]; out.text=h; out.review=true; }
    else if(action==='slide'){ o={a:'slide',n:b.n,op:b.op}; if(b.op==='duplicate') o.id=newId();
      if(!shift(order(),o)) throw new Error(b.op==='delete'?T.lastOne:T.edge);
      if(o.id) copy(o); J.ops.push(o); J.redo=[]; lay(o.id?inLang(o.id):null); out.reload=b.n; }
    else if(action==='anim'){ var sa=els(b.n)[0], at=sa&&sa.getAttribute(animAttr(b.key));
      o={a:'anim',n:b.n,key:b.key,value:b.value,was:b.key==='step'?(at===null||at===undefined?null:at==='1'):(at||'')}; J.ops.push(o); J.redo=[]; show(o,false); out.reload=b.n; }
    else if(action==='library'){ out.masters=INFO.masters||[]; out.fields=fieldsFor(b.n); return out; }
    else if(action==='fill'){ o={a:'fill',n:b.n,slot:b.slot}; if(!swapIn(o)) throw new Error('not available in a deck opened as a file'); J.ops.push(o); J.redo=[]; out.reload=b.n; }
    else if(action==='add'){ o={a:'add',n:b.n,master:b.master,id:newId()}; if(!make(o)) throw new Error('not available in a deck opened as a file');
      J.ops.push(o); J.redo=[]; lay(inLang(o.id)); out.reload=o.id; }
    else if(action==='item'){ o={a:'item',n:b.n,path:b.path,op:b.op}; doItem(o); J.ops.push(o); J.redo=[]; out.reload=b.n; }
    else if(action==='undo'){ o=J.ops[J.ops.length-1]; if(!o) throw new Error('nothing to undo');
      if(o.a==='item') undoItem(o); if(o.a==='fill') swapOut(o); J.ops.pop(); J.redo.push(o); if(o.a==='slide'||o.a==='add') lay(inLang(o.n)); else if(o.a!=='item'&&o.a!=='fill') show(o,true); out.reload=b.n; }
    else if(action==='redo'){ o=J.redo[J.redo.length-1]; if(!o) throw new Error('nothing to redo');
      if(o.a==='item') doItem(o); if(o.a==='fill') swapIn(o); J.redo.pop(); J.ops.push(o); if(o.a==='slide'||o.a==='add') lay(inLang(o.id||o.n)); else if(o.a!=='item'&&o.a!=='fill') show(o,false); out.reload=b.n; }
    else if(action!=='state') throw new Error('not available in a deck opened as a file');
    keep(); flags();
    out.undo=J.ops.length; out.redo=J.redo.length; out.open=J.ops.length;
    return out;
  }
  function restore(){                                        /* the changes made to this build: the block inside the file, or what this browser kept, whichever is newer */
    var best=null;
    [function(){ return (document.getElementById('vs-journal')||{}).textContent; },function(){ return localStorage.getItem(KEY); }].forEach(function(get){
      try{ var j=JSON.parse(get()||'null'); if(j&&j.base===INFO.base&&j.ops&&(!best||(j.t||0)>(best.t||0))) best=j; }catch(e){} });
    if(best){ J=best; J.redo=[]; var done=[], moved=false;      /* in their order: a copy takes the texts its slide had at that moment */
      J.ops.forEach(function(o){ try{
          if(o.a==='slide'){ if(o.op==='duplicate'){ if(!o.id) o.id=newId(); copy(o); } moved=true; }
          else if(o.a==='add'){ if(!make(o)) return; moved=true; }
          else if(o.a==='fill'){ var jo=J.ops; J.ops=done; var okf=swapIn(o); J.ops=jo; if(!okf) return; }
          else if(o.a==='item') doItem(o); else show(o,false);
          done.push(o); }catch(e){} });
      J.ops=done; if(moved) lay(parseInt((location.hash.match(/\d+/)||[1])[0],10)-1); }
    flags();
    if(FSA) idb('readonly',function(s){ return s.get(INFO.deck); }).then(function(h){ if(h) DIR=h; return idb('readonly',function(s){ return s.get('*root'); }); })
      .then(function(r){ ROOT=r||null; return DIR?may(DIR,false).then(function(ok){ if(ok) return locate(DIR,0).then(function(d){ if(!d) DIR=null; }); }):null; })
      .then(function(){ return fromRoot(false); }).then(fileState).catch(function(){});
  }
  function writeFile(name,text){
    function download(){ var a=el('a',{href:URL.createObjectURL(new Blob([text],{type:'application/json'})),download:name}); document.body.appendChild(a); a.click(); a.remove(); return 'download'; }
    if(!window.showSaveFilePicker) return Promise.resolve(download());
    return window.showSaveFilePicker({id:'vibeupslides',suggestedName:name,types:[{description:'vibeupslides',accept:{'application/json':['.json']}}]})
      .then(function(h){ return h.createWritable().then(function(w){ return w.write(text).then(function(){ return w.close(); }); }).then(function(){ return h.name; }); },
            function(e){ if(e&&e.name==='AbortError') throw e; return download(); });
  }
  function finishFile(){ pending().then(function(){
      if(!J.ops.length){ toggle(false); return; }
      var name=INFO.deck+'.edits.json';
      function told(){ var o=el('div',{id:'vsend'}), h=el('b'), p=el('p'), q=el('p'); h.textContent=T.fEnd1; p.textContent=T.fEndDir.replace('{f}',FILE_NAME); q.textContent=T.fEnd3.replace('{d}',INFO.deck);
        o.appendChild(h); o.appendChild(p); o.appendChild(q); var c=el('button',{type:'button'},T.fOk); c.addEventListener('click',function(){ o.remove(); }); o.appendChild(c); document.body.appendChild(o); toggle(false); }
      if(FSA) return connect(false).then(function(ok){ if(ok) told(); else say(T.fNeed,'warn'); });
      return writeFile(name,JSON.stringify({vibeupslides_edits:1,deck:INFO.deck,base:INFO.base,ops:J.ops},null,1)).then(function(how){
        var o=el('div',{id:'vsend'}), h=el('b'), p=el('p'), q=el('p'); h.textContent=T.fEnd1; p.textContent=(how==='download'?T.fEnd2d:T.fEnd2).replace('{f}',name); q.textContent=T.fEnd3.replace('{d}',INFO.deck);
        o.appendChild(h); o.appendChild(p); o.appendChild(q); var c=el('button',{type:'button'},T.fClose); c.addEventListener('click',function(){ o.remove(); }); o.appendChild(c);
        document.body.appendChild(o);
      });
    }).catch(function(e){ if(!e||e.name!=='AbortError') fail(e); }); }

  /* What became of the texts the user typed last time: shown once when the editing is opened in the deck built since */
  var report=el('div',{id:'vse-report'});
  function news(){ var r=INFO.report||[]; if(!r.length) return false; try{ return localStorage.getItem('vs-seen:'+INFO.deck)!==INFO.base; }catch(e){ return true; } }
  function showReport(){
    var r=INFO.report||[]; if(!r.length) return;
    report.innerHTML=''; report.appendChild(el('label',{},T.rHead));
    r.forEach(function(x){ var row=el('div',{'class':'r'}), a=el('small'), b=el('span');
      a.textContent=T.rSlide.replace('{n}',x.slide)+' · '+(x.pending?T.rPending:(x.changed?T.rFixed:T.rSame))+(x.langs&&x.langs.length?' · '+T.rLangs.replace('{l}',names(x.langs)):'');
      if(x.changed&&!x.pending){ var d=el('s'); d.textContent=x.typed; b.appendChild(d); b.appendChild(document.createTextNode(' → ')); }
      var n=el('b'); n.textContent=x.now; b.appendChild(n); row.appendChild(a); row.appendChild(b); report.appendChild(row); });
    var c=el('button',{type:'button'},T.fOk); c.addEventListener('click',function(e){ e.stopPropagation(); report.classList.remove('on'); }); report.appendChild(c);
    report.classList.add('on'); try{ localStorage.setItem('vs-seen:'+INFO.deck,INFO.base); }catch(e){} if(btn) btn.classList.remove('news');
  }

  /* open and close */
  var motionWas=null;
  function steps(){ var s=active(); if(on&&s) s.querySelectorAll('.f').forEach(function(f){ f.classList.add('on'); }); }
  function toggle(to){
    if(reading()) return toLive();
    on=(to===undefined)?!on:to; try{ sessionStorage.setItem('vs-edit',on?'1':'0'); }catch(e){}
    if(on){ motionWas=root.getAttribute('data-motion'); root.setAttribute('data-motion','off'); }
    else { stopOrder(false); pending(); if(motionWas!==null) root.setAttribute('data-motion',motionWas); items.classList.remove('on'); openNotes(false); openPick(null); overflow(null);
      document.querySelectorAll('#deck .vs-voice').forEach(function(e){ e.classList.remove('vs-voice'); }); }
    root.classList.toggle('vs-editing',on); btn.classList.toggle('on',on); prepare(); steps(); animState();
    if(on&&news()) showReport(); if(!on) report.classList.remove('on');
    if(on){ say(FILE?T.fHint+(unchecked().length?T.fPending.replace('{n}',unchecked().length):''):T.hint); checkOverflow(); if(FILE&&(DIR||ROOT)) (DIR?allowed(true):fromRoot(true)).then(fileState); }
  }

  function start(){
    if(FILE) return build();
    fetch('/__vs/state',{method:'POST',headers:{'Content-Type':'application/json'},body:'{}'}).then(function(r){ return r.json(); })
      .then(function(d){ if(!d||!d.ok||(d.actions||[]).indexOf('all')<0) FILE=true; },function(){ FILE=true; }).then(build);      /* shown by a server that takes no changes: as from a file */
  }
  function build(){
    var ctl=document.getElementById('ctl'); if(!ctl) return;
    var fs=ctl.querySelector('[data-act="fs"]');
    btn=el('button',{id:'vse-btn',type:'button',title:T.edit},'<svg viewBox="0 0 24 24"><path d="M4 20h4L19 9l-4-4L4 16z"/><path d="M13.5 6.5l4 4"/></svg>');
    btn.addEventListener('click',function(e){ e.stopPropagation(); toggle(); });
    ctl.insertBefore(btn,fs); ctl.insertBefore(el('span',{'class':'sep'}),fs);
    if(reading()){ btn.title=T.toLive; return; }   /* the reading version rearranges the slides into pages: the pencil opens the editing in the version to present */
    var area_label=el('label',{},T.notesFor); area=el('textarea',{spellcheck:'true'}); notesBox.appendChild(area_label); notesBox.appendChild(area);
    area2=el('textarea',{spellcheck:'true'}); notesBox.appendChild(el('label',{},T.readFor)); notesBox.appendChild(area2);
    var nrow=el('div',{'class':'row'}); notesBox.appendChild(nrow); button(nrow,T.notesSave,saveNotes);
    var row=el('div',{'class':'row'});
    scan();
    function group(label){ var g=el('div',{'class':'grp'}); g.appendChild(el('small',{},label)); var r=el('div'); g.appendChild(r); row.appendChild(g); return r; }
    function named(b,tip){ b.title=tip; return b; }
    var g=group(T.gMove); named(button(g,T.earlier,function(){ slideOp('earlier'); }),T.tEarlier); named(button(g,T.later,function(){ slideOp('later'); }),T.tLater);
    g=group(T.gSlide); named(button(g,T.dup,function(){ slideOp('duplicate'); }),T.tDup); named(button(g,T.del,function(){ slideOp('delete'); },'danger'),T.tDel);
    g=group(T.gAdd); bAdd=named(button(g,T.add,function(){ openPick('add'); }),T.tAdd); bField=named(button(g,T.field,function(){ openPick('field'); }),T.tField);
    g=group(T.gText); bNotes=named(button(g,T.notes,function(){ openNotes(!notesBox.classList.contains('on')); }),T.tNotes);
    bAll=named(button(g,T.forAll,function(){ var s=active(); if(s&&s.getAttribute('data-shared')) anim('all',!s.getAttribute('data-forall')); }),T.tForAll); bAll.style.display='none';
    g=group(T.gAnim); bStep=named(button(g,T.aStep,function(){ var s=active(); if(s) anim('step',!stepOf(s)); }),T.tStep);
    bMove=named(button(g,T.aMove[''],function(){ var s=active(), l=['','calm','expressive','off']; if(s) anim('move',l[(l.indexOf(s.getAttribute('data-move')||'')+1)%4]); }),T.tMove);
    bOrder=named(button(g,T.aOrder,startOrder),T.tOrder);
    named(button(g,T.aPlay,play),T.tPlay);
    g=group(T.gSteps); bUndo=button(g,T.undo,function(){ step('undo'); }); bRedo=button(g,T.redo,function(){ step('redo'); });
    if(FILE){ g=group(T.gCheck); bKeep=named(button(g,T.uKeep,release),T.tKeep); bKeep.disabled=true;
      flag=el('span',{id:'vse-flag'}); flag.style.display='none'; ctl.insertBefore(flag,btn); }
    if(FILE){ g=group(T.gSave); bDir=button(g,T.fDir,function(){ connect(true).catch(function(e){ if(!e||e.name!=='AbortError') fail(e); }); }); }
    g=group('\u00a0'); bDone=named(button(g,T.done,finish,'go'),T.tDone);
    msg=el('div',{id:'vse-msg'});
    panel.appendChild(report); if(news()) btn.classList.add('news');
    panel.appendChild(pick); panel.appendChild(notesBox); panel.appendChild(note); document.body.appendChild(line); panel.appendChild(msg); panel.appendChild(row);
    panel.addEventListener('click',function(e){ e.stopPropagation(); });
    ctl.appendChild(panel); document.body.appendChild(items);
    button(items,T.up,function(){ itemOp('up'); }); button(items,T.down,function(){ itemOp('down'); });
    button(items,T.idup,function(){ itemOp('duplicate'); }); button(items,T.idel,function(){ itemOp('delete'); },'danger');
    var open=/_edit\.html$/.test(location.pathname)?'1':'0'; try{ open=sessionStorage.getItem('vs-edit')||open; }catch(e){}
    if(FILE){ if(!Object.keys(INFO.fields||{}).length) bField.style.display='none'; if(!(INFO.masters||[]).length) bAdd.style.display='none'; restore(); }      /* new slides and fields come from what the build left in the page */
    toggle(open==='1');
    send('state',{},true).catch(fail);
    var shown=active(); setInterval(function(){ var s=active(); if(s!==shown){ shown=s; seen=0; stopOrder(false); unmark(); note.classList.remove('on'); if(on) say(''); if(notesBox.classList.contains('on')) fillNotes(); openPick(null); steps(); animState(); }
      else if(on&&!(document.activeElement&&document.activeElement.isContentEditable)) checkOverflow(); },350);
  }
  if(document.readyState==='complete') setTimeout(start,50); else window.addEventListener('load',function(){ setTimeout(start,50); });
})();
