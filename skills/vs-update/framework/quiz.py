# -*- coding: utf-8 -*-
"""Quiz slides for the VibeUpSlides engine.

Three question types, all with the same reveal: the correct answer turns into an accent fill and
gets a check mark, there is confetti in the brand colours and a short bright chord.

- quiz_choice(...)      multiple choice with two to four answers (A to D)
- quiz_true_false(...)  one statement, two large fields for true and false
- quiz_estimate(...)    guess a number; on reveal it counts up in large digits

Operation in the room: click an answer (or press A to D, or 1 to 4). If it is the correct one, the
reveal runs. If it is a wrong one, the card shakes briefly and is dimmed; that way you can first go
through the guesses from the audience and then show the correct answer. Key 0 resets the question.
The presenter view has its own buttons for this, and the correct answer is marked there.

For the handout version build with revealed=True: the slide then shows the solution right away.
With advance=True the next forward click (arrow, space bar, presenter remote) reveals the question,
and only the click after that moves on to the next slide. Going back resets the question.
Call add(QUIZ_ASSETS) once at the end of the deck file.
"""

LETTERS = "ABCD"


def _texts(lang):
    """Default kickers and the true/false labels: German for "de", English for every other language."""
    if lang == "de":
        return dict(quiz="Quizfrage", estimate="Schätzfrage", tf="Richtig oder falsch?",
                    true="Richtig", false="Falsch", reveal="Auflösen")
    return dict(quiz="Quiz", estimate="Estimate", tf="True or false?",
                true="True", false="False", reveal="Reveal")


def _head(lang, title, kind, kicker, extra_class, revealed, data="", source=""):
    k = kicker or _texts(lang)[kind]
    open_class = " qopen" if revealed else ""
    if source:
        data += f' data-source="{source}"'
    return (f'<section class="slide qslide {extra_class}{open_class}" lang="{lang}" data-title="{title}" '
            f'data-quiz="{kind}"{data}>\n  <div class="kicker">{k}</div>\n')


def _explain(explanation):
    return f'\n  <p class="qexplain">{explanation}</p>' if explanation else ""


def _note(note):
    return f'\n  <aside class="notes">{note}</aside>' if note else ""


def _advance(advance):
    """Invisible click step: when a forward click switches it on, the question is revealed (script in QUIZ_ASSETS)."""
    return '\n  <span class="f qadvance" style="display:none" aria-hidden="true"></span>' if advance else ""


def quiz_choice(lang, title, question, answers, correct, explanation="", kicker=None,
              note="", revealed=False, source="", advance=False):
    """answers: list of 2 to 4 texts. correct: index of the correct answer (0 = A),
    or None, in which case whichever answer is clicked counts as correct."""
    assert 2 <= len(answers) <= 4, "two to four answers"
    cards = []
    for i, a in enumerate(answers):
        mark = ' data-correct="1"' if correct == i else ""
        state = " qright" if revealed and correct == i else (" qdim" if revealed else "")
        cards.append(f'<button class="qopt{state}" data-i="{i}"{mark}><span class="qletter">{LETTERS[i]}</span>'
                      f'<span class="qtx">{a}</span><span class="qcheck" aria-hidden="true"></span></button>')
    grid = "q2" if len(answers) in (2, 4) else "q3"
    return (_head(lang, title, "quiz", kicker, "qmc", revealed, source=source)
            + f'  <h2 class="qquestion">{question}</h2>\n'
            + f'  <div class="qopts {grid}">' + "".join(cards) + '</div>'
            + _explain(explanation) + _note(note) + _advance(advance and not revealed) + '\n</section>')


def quiz_true_false(lang, title, statement, is_true, explanation="", kicker=None, note="",
                  revealed=False, source="", advance=False):
    t = _texts(lang)
    cards = []
    for i, (word, value) in enumerate(((t["true"], True), (t["false"], False))):
        hit = (value == bool(is_true))
        mark = ' data-correct="1"' if hit else ""
        state = (" qright" if hit else " qdim") if revealed else ""
        symbol = "✓" if value else "✗"
        cards.append(f'<button class="qopt qtf{state}" data-i="{i}"{mark}><span class="qletter">{symbol}</span>'
                      f'<span class="qtx">{word}</span><span class="qcheck" aria-hidden="true"></span></button>')
    return (_head(lang, title, "tf", kicker, "qmc qtfslide", revealed, source=source)
            + f'  <h2 class="qquestion">{statement}</h2>\n'
            + '  <div class="qopts q2">' + "".join(cards) + '</div>'
            + _explain(explanation) + _note(note) + _advance(advance and not revealed) + '\n</section>')


def quiz_estimate(lang, title, question, number, unit="", explanation="", kicker=None, note="",
                 decimals=0, revealed=False, source="", advance=False):
    """number: the correct number. unit: short, e.g. "percent", "million euros", "teams".
    With revealed=True the number is written with German separators for lang "de" and English ones
    for every other language; the live count-up in the browser formats it for the slide language."""
    value = f"{number:,.{decimals}f}"
    if lang == "de":
        value = value.replace(",", "X").replace(".", ",").replace("X", ".")
    shown = value if revealed else "?"
    data = f' data-number="{number}" data-decimals="{decimals}"'
    return (_head(lang, title, "estimate", kicker, "qestimate", revealed, data, source=source)
            + f'  <h2 class="qquestion">{question}</h2>\n'
            + f'  <button class="qnumberbox"><span class="qnumber">{shown}</span>'
            + (f'<span class="qunit">{unit}</span>' if unit else "") + '</button>'
            + _explain(explanation) + _note(note) + _advance(advance and not revealed) + '\n</section>')


QUIZ_ASSETS = r'''
<style>
.qslide .qquestion{max-width:1600px;font-size:60px;line-height:1.12}
.qslide .qopts{margin-top:54px;display:grid;gap:26px}
.qslide .qopts.q2{grid-template-columns:repeat(2,minmax(0,1fr))}
.qslide .qopts.q3{grid-template-columns:repeat(3,minmax(0,1fr))}
.qslide .qopt{font:inherit;text-align:left;display:grid;grid-template-columns:76px 1fr 56px;align-items:center;gap:24px;
  min-height:128px;padding:22px 28px;background:var(--paper);border:3px solid var(--line);border-radius:var(--radius);color:var(--ink);
  cursor:pointer;position:relative;transition:background .35s,border-color .35s,color .35s,opacity .45s,transform .35s}
.qslide .qopt:hover{border-color:var(--ink)}
.qslide .qletter{width:76px;height:76px;display:grid;place-items:center;background:var(--ink);color:var(--paper);border-radius:var(--radius);
  font-weight:var(--w-display);font-size:38px;line-height:1;transition:background .35s,color .35s}
.qslide .qtx{font-size:32px;line-height:1.25;font-weight:500}
.qslide .qcheck{position:relative;width:56px;height:56px;border-radius:50%;opacity:0;transform:scale(.4);transition:opacity .3s,transform .45s cubic-bezier(.2,1.6,.4,1)}
.qslide .qtf{grid-template-columns:96px 1fr 56px;min-height:170px}
.qslide .qtf .qletter{width:96px;height:96px;font-size:54px}
.qslide .qtf .qtx{font-size:46px;font-weight:700}
/* wrong guess */
.qslide .qopt.qwrong{opacity:.38;border-color:var(--line);animation:qshake .5s ease both}
.qslide .qopt.qwrong .qletter{background:var(--muted)}
.qslide .qopt.qwrong .qtx{text-decoration:line-through;text-decoration-thickness:3px}
@keyframes qshake{0%,100%{transform:none}20%{transform:translateX(-14px)}40%{transform:translateX(12px)}60%{transform:translateX(-8px)}80%{transform:translateX(5px)}}
/* revealed */
.qslide .qopt.qdim{opacity:.3}
.qslide .qopt.qright{background:var(--accent);border-color:var(--accent);color:var(--on-accent);opacity:1;animation:qpulse .9s cubic-bezier(.2,.9,.3,1) both}
.qslide .qopt.qright .qletter{background:var(--on-accent);color:var(--accent-text)}
.qslide .qopt.qright .qcheck{opacity:1;transform:none;background:var(--on-accent)}
/* the check mark is a mask, so it can take the accent colour */
.qslide .qopt.qright .qcheck::after{content:"";position:absolute;inset:0;background:var(--accent);
  -webkit-mask:url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24'%3E%3Cpath d='M5 12.5l4.2 4.2L19 7' fill='none' stroke='%23000' stroke-width='3' stroke-linecap='round' stroke-linejoin='round'/%3E%3C/svg%3E") center/70% no-repeat;
  mask:url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24'%3E%3Cpath d='M5 12.5l4.2 4.2L19 7' fill='none' stroke='%23000' stroke-width='3' stroke-linecap='round' stroke-linejoin='round'/%3E%3C/svg%3E") center/70% no-repeat}
@keyframes qpulse{0%{transform:scale(1)}35%{transform:scale(1.06)}60%{transform:scale(.98)}100%{transform:scale(1)}}
.qslide.qopen .qopt{cursor:default}
.qslide.qopen .qopt.qright{animation:none}
/* explanation */
.qslide .qexplain{margin-top:36px;max-width:1500px;font-size:30px;line-height:1.4;color:var(--ink);
  opacity:0;transform:translateY(16px);transition:opacity .5s .5s,transform .5s .5s}
.qslide.qsolved .qexplain,.qslide.qopen .qexplain{opacity:1;transform:none}
/* estimate question */
.qslide .qnumberbox{font:inherit;margin-top:56px;display:flex;align-items:baseline;gap:28px;background:transparent;border:0;padding:0;cursor:pointer;color:var(--ink)}
.qslide .qnumber{font-weight:var(--w-display);font-size:220px;line-height:.9;letter-spacing:-.03em;font-variant-numeric:tabular-nums;
  min-width:260px;border-bottom:8px solid var(--line);padding-bottom:10px;transition:color .4s,border-color .4s}
.qslide .qunit{font-weight:700;font-size:54px;color:var(--muted)}
.qslide.qsolved .qnumber,.qslide.qopen .qnumber{color:var(--accent-text);border-color:var(--accent)}
.qslide.qsolved .qnumberbox,.qslide.qopen .qnumberbox{cursor:default}
/* confetti lies on top of the slide and does not catch clicks */
.qslide .qconfetti{position:absolute;inset:0;width:1920px;height:1080px;pointer-events:none;z-index:8}
/* entrance */
.active.qslide .qopt,.active.qslide .qnumberbox{animation:qenter .6s cubic-bezier(.2,.7,.3,1) both}
.active.qslide .qopt:nth-child(2){animation-delay:.08s}.active.qslide .qopt:nth-child(3){animation-delay:.16s}.active.qslide .qopt:nth-child(4){animation-delay:.24s}
.active.qslide .qopt.qwrong{animation:qshake .5s ease both}
.active.qslide .qopt.qright{animation:qpulse .9s cubic-bezier(.2,.9,.3,1) both}
.active.qslide.qopen .qopt{animation:none}
.active.qslide .qopt.qdim{animation:none;opacity:.3}
@keyframes qenter{from{opacity:0;transform:translateY(24px)}to{opacity:1;transform:none}}
@media print{.qslide .qconfetti{display:none}}
</style>
<script>
(function(){
  /* confetti colours come from the brand at runtime: accent weighted most, plus ink, line and muted */
  function brandColours(){
    var cs=getComputedStyle(document.documentElement);
    function v(name){ return (cs.getPropertyValue(name)||"").trim()||"#000"; }
    var accent=v("--accent");
    return [accent,accent,v("--ink"),v("--line"),v("--muted"),accent];
  }
  var reducedMotion=window.matchMedia&&window.matchMedia("(prefers-reduced-motion: reduce)").matches;
  var ac=null;
  function audio(){ try{ ac=ac||new (window.AudioContext||window.webkitAudioContext)(); if(ac.state==="suspended") ac.resume(); }catch(e){} return ac; }
  function tone(f,t0,duration,volume,type){
    var a=audio(); if(!a) return;
    var o=a.createOscillator(), g=a.createGain(); o.type=type||"triangle"; o.frequency.value=f;
    var s=a.currentTime+t0; g.gain.setValueAtTime(0.0001,s); g.gain.exponentialRampToValueAtTime(volume,s+0.015);
    g.gain.exponentialRampToValueAtTime(0.0001,s+duration); o.connect(g); g.connect(a.destination); o.start(s); o.stop(s+duration+0.05);
  }
  function chord(){ /* bright major chord, briefly arpeggiated: C6, E6, G6, C7 */
    [1046.5,1318.5,1568,2093].forEach(function(f,i){ tone(f,i*0.07,1.1,0.16,"triangle"); tone(f*2,i*0.07,0.5,0.03,"sine"); });
  }
  function missSound(){ tone(311,0,0.18,0.12,"sine"); tone(233,0.13,0.28,0.12,"sine"); }

  function confetti(s){
    if(reducedMotion) return;
    var c=s.querySelector(".qconfetti");
    if(!c){ c=document.createElement("canvas"); c.className="qconfetti"; s.appendChild(c); }
    c.width=1920; c.height=1080; var x=c.getContext("2d"), parts=[], colours=brandColours();
    var origin=s.querySelector(".qright,.qnumberbox"), sr=s.getBoundingClientRect(), scale=sr.width/1920;
    var ox=960, oy=540;
    if(origin){ var r=origin.getBoundingClientRect(); ox=(r.left+r.width/2-sr.left)/scale; oy=(r.top+r.height/2-sr.top)/scale; }
    for(var i=0;i<170;i++){
      var w=Math.random()*Math.PI*2, v=9+Math.random()*17;
      parts.push({x:ox,y:oy,vx:Math.cos(w)*v,vy:Math.sin(w)*v-9,b:8+Math.random()*12,h:5+Math.random()*7,
                  r:Math.random()*6,vr:(Math.random()-.5)*.35,f:colours[i%colours.length]});
    }
    var start=performance.now();
    (function frame(t){
      var age=(t-start)/1000; x.clearRect(0,0,1920,1080);
      parts.forEach(function(p){ p.vy+=0.55; p.vx*=0.985; p.vy*=0.985; p.x+=p.vx; p.y+=p.vy; p.r+=p.vr;
        x.save(); x.globalAlpha=Math.max(0,1-Math.max(0,age-1.6)/0.8); x.translate(p.x,p.y); x.rotate(p.r);
        x.fillStyle=p.f; x.fillRect(-p.b/2,-p.h/2,p.b,p.h*Math.abs(Math.cos(p.r*1.7))+1); x.restore(); });
      if(age<2.4) requestAnimationFrame(frame); else if(c.parentNode) c.parentNode.removeChild(c);
    })(start);
  }
  function notify(){ try{ document.dispatchEvent(new CustomEvent("vs-change")); }catch(e){} }

  /* thousands and decimal separators follow the slide language; an unknown language tag falls back to English */
  function formatNumber(n,decimals,lang){
    var o={minimumFractionDigits:decimals,maximumFractionDigits:decimals};
    try{ return Number(n).toLocaleString(lang||"en",o); }catch(e){ return Number(n).toLocaleString("en",o); }
  }

  function init(s){
    if(s.vsQuiz) return;
    var kind=s.getAttribute("data-quiz"), lang=s.getAttribute("lang")||"en";
    var opts=Array.prototype.slice.call(s.querySelectorAll(".qopt"));
    var solved=s.classList.contains("qopen");

    function solve(opt){
      if(solved) return; solved=true;
      s.classList.add("qsolved");
      opts.forEach(function(o){ o.classList.remove("qwrong"); o.classList.add(o===opt?"qright":"qdim"); });
      chord(); setTimeout(function(){ confetti(s); },120); notify();
    }
    function choose(i){
      if(kind==="estimate"){ revealNumber(); return; }
      var o=opts[i]; if(!o||solved||o.classList.contains("qwrong")) return;
      var hasCorrect=opts.some(function(x){ return x.hasAttribute("data-correct"); });
      if(!hasCorrect||o.hasAttribute("data-correct")) solve(o);
      else { o.classList.remove("qwrong"); void o.offsetWidth; o.classList.add("qwrong"); audio(); missSound(); notify(); }
    }
    function reveal(){
      if(kind==="estimate"){ revealNumber(); return; }
      var r=opts.filter(function(x){ return x.hasAttribute("data-correct"); })[0]; if(r) solve(r);
    }
    function revealNumber(){
      if(solved) return; solved=true; s.classList.add("qsolved");
      var target=parseFloat(s.getAttribute("data-number"))||0, decimals=parseInt(s.getAttribute("data-decimals"),10)||0;
      var el=s.querySelector(".qnumber"), t0=performance.now(), duration=reducedMotion?1:1700;
      audio();
      (function step(t){
        var p=Math.min(1,(t-t0)/duration), e=1-Math.pow(1-p,3);
        el.textContent=formatNumber(target*e,decimals,lang);
        if(p<1) requestAnimationFrame(step); else { chord(); confetti(s); notify(); }
      })(t0);
    }
    function reset(){
      solved=false; s.classList.remove("qsolved","qopen");
      opts.forEach(function(o){ o.classList.remove("qwrong","qright","qdim"); });
      var num=s.querySelector(".qnumber"); if(num) num.textContent="?";
      var c=s.querySelector(".qconfetti"); if(c&&c.parentNode) c.parentNode.removeChild(c);
      notify();
    }
    opts.forEach(function(o,i){ o.addEventListener("click",function(e){ e.stopPropagation(); choose(i); }); });
    var box=s.querySelector(".qnumberbox"); if(box) box.addEventListener("click",function(e){ e.stopPropagation(); revealNumber(); });

    /* interface for the keyboard handling and the presenter view of the engine */
    s.vsQuiz={
      kind:kind,
      options:function(){ return opts.map(function(o,i){ return {
        letter:o.querySelector(".qletter").textContent, text:o.querySelector(".qtx").textContent,
        correct:o.hasAttribute("data-correct"), wrong:o.classList.contains("qwrong"), i:i }; }); },
      choose:choose, reveal:reveal, reset:reset,
      solved:function(){ return solved; },
      number:function(){ var n=s.getAttribute("data-number"); return n===null?null:n; }
    };
  }
  Array.prototype.forEach.call(document.querySelectorAll(".qslide"), init);
  window.vsQuizInit=init;                                   /* for a quiz slide that is copied while editing */
})();
</script>
<script>
/* advance=True: the hidden click step .qadvance reveals the question, going back resets it */
(function(){
  function watch(f){
    var s = f.closest(".qslide");
    new MutationObserver(function(){
      if(!s.vsQuiz) return;
      if(f.classList.contains("on")){
        if(!s.vsQuiz.solved()){ var box = s.querySelector(".qnumberbox"); if(box) box.click(); else s.vsQuiz.reveal(); }
      } else if(s.vsQuiz.solved()){ s.vsQuiz.reset(); }
    }).observe(f, {attributes:true, attributeFilter:["class"]});
  }
  document.querySelectorAll(".qslide .qadvance").forEach(watch);
  window.vsQuizWatch=function(s){ s.querySelectorAll(".qadvance").forEach(watch); };
})();
</script>
'''
