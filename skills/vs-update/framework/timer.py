# -*- coding: utf-8 -*-
"""Timer slides: a countdown for exercises and breaks.

A timer slide sits directly after an exercise slide, carries the essential facts of the
task and shows a large clock in the style of a Time Timer: an accent-coloured disc on a
dial with sixty minutes that disappears clockwise. The time can be adjusted by one and by
fifteen minutes at any moment. "End now" closes the exercise early. When the time is up a
gong sounds and the slide fills with the accent colour.

The duration in the heading (and in the facts) follows the buttons: "20 minutes for X"
becomes "18 minutes for X" after pressing -1 twice. It is set with the placeholder {duration}
("{duration} for X"), but a figure that matches the preset is recognised as well, as digits
or, for German and English, as a word ("20 Minuten", "zwanzig Minuten", "20 minutes",
"twenty minutes"). For every other language only digits are recognised.

While the presenter view of the master is open, the buttons disappear from the slide and the
clock is operated from the presenter window (that is what the vsTimer object attached to
every timer slide is for).
"""
import re

_NUMBER_WORDS = {
    "de": {1: "eine", 2: "zwei", 3: "drei", 4: "vier", 5: "fünf", 6: "sechs", 7: "sieben", 8: "acht",
           9: "neun", 10: "zehn", 12: "zwölf", 15: "fünfzehn", 20: "zwanzig", 25: "fünfundzwanzig",
           30: "dreißig", 40: "vierzig", 45: "fünfundvierzig", 60: "sechzig"},
    "en": {1: "one", 2: "two", 3: "three", 4: "four", 5: "five", 6: "six", 7: "seven", 8: "eight",
           9: "nine", 10: "ten", 12: "twelve", 15: "fifteen", 20: "twenty", 25: "twenty-five",
           30: "thirty", 40: "forty", 45: "forty-five", 60: "sixty"},
}


def _duration_text(lang, minutes):
    if lang == "de":
        return f"{minutes} Minute" if minutes == 1 else f"{minutes} Minuten"
    return f"{minutes} minute" if minutes == 1 else f"{minutes} minutes"


def _mark_duration(text, lang, minutes):
    """Wraps the duration in a <span class="tduration"> so the script can keep it up to date."""
    span = '<span class="tduration">{}</span>'
    if "{duration}" in text:
        return text.replace("{duration}", span.format(_duration_text(lang, minutes)))
    candidates = [str(minutes)]
    word = _NUMBER_WORDS.get(lang, {}).get(minutes)
    if word:
        candidates.append(word)
    unit = r"(?:Minuten|Minute|Min\.|minutes|minute|mins|min)"
    pattern = re.compile(
        r"(?<![\w-])(" + "|".join(re.escape(c) for c in candidates) + r")\s+" + unit + r"(?!\w)",
        re.IGNORECASE)
    return pattern.sub(lambda m: span.format(m.group(0)), text, count=1)


def timer_slide(lang, title, kicker, minutes, heading, bullets, facts):
    """bullets: list of (number, title, sentence). facts: list of (label, value).
    If bullets is empty the clock stands alone and centred, which is what a break uses.
    The duration is marked in heading and in the fact values ({duration} or recognised)."""
    german = lang == "de"
    heading = _mark_duration(heading, lang, minutes)
    facts = [(label, _mark_duration(value, lang, minutes)) for label, value in facts]
    steps_html = "".join(
        f'<div class="tp"><div class="tpn">{number}</div>'
        f'<div><h3>{step_title}</h3><p>{sentence}</p></div></div>'
        for number, step_title, sentence in bullets)
    facts_html = "".join(
        f'<div class="td"><small>{label}</small><span>{value}</span></div>' for label, value in facts)
    start_label = "Start"
    pause_label = "Pause"
    reset_label = "Zurücksetzen" if german else "Reset"
    end_now_label = "Sofort beenden" if german else "End now"
    time_up_text = "Die Zeit ist um" if german else "Time is up"
    reset_hint = "Klicken, um den Timer zurückzusetzen" if german else "Click to reset the timer"
    minute_singular = "Minute" if german else "minute"
    minute_plural = "Minuten" if german else "minutes"
    alone_class = " tallein" if not bullets else ""
    return f'''
<section class="slide dark tslide{alone_class}" lang="{lang}" data-title="{title}" data-timer="{minutes}">
  <div class="kicker">{kicker}</div>
  <h2 class="ttitle">{heading}</h2>
  <div class="tgrid">
    <div class="tclock">
      <svg viewBox="0 0 400 400" class="tsvg" aria-hidden="true">
        <g class="tdigits"></g>
        <circle cx="200" cy="200" r="150" fill="none" style="stroke:color-mix(in srgb,var(--on-deep) 16%,transparent)" stroke-width="2"/>
        <path class="tsector" d="" style="fill:var(--accent)"/>
        <circle class="tring" cx="200" cy="200" r="150" fill="none" style="stroke:color-mix(in srgb,var(--on-deep) 50%,transparent)" stroke-width="3"/>
        <circle cx="200" cy="200" r="7" style="fill:var(--on-deep)"/>
      </svg>
      <div class="ttime"><span class="tmin">00</span><span class="tsep">:</span><span class="tsek">00</span></div>
      <div class="tbuttons">
        <button class="tb" data-delta="-15">&minus;15</button>
        <button class="tb" data-delta="-1">&minus;1</button>
        <button class="tb tstart">{start_label}</button>
        <button class="tb" data-delta="1">+1</button>
        <button class="tb" data-delta="15">+15</button>
      </div>
      <div class="tsmall-row">
        <button class="tb tsmall treset">{reset_label}</button>
        <button class="tb tsmall tnow">{end_now_label}</button>
      </div>
    </div>
    <div class="tbody">
      <div class="tsteps">{steps_html}</div>
      <div class="tfacts">{facts_html}</div>
    </div>
  </div>
  <div class="tend" role="button" tabindex="-1">
    <div><div class="tendtext">{time_up_text}</div>
    <div class="tendhint">{reset_hint}</div></div>
  </div>
  <span class="tword" data-one="{minute_singular}" data-many="{minute_plural}" data-pause="{pause_label}" data-start="{start_label}"></span>
</section>'''


TIMER_ASSETS = r'''
<style>
.tslide .ttitle{font-size:52px;line-height:1.1;max-width:1500px}
.tslide .tgrid{margin-top:26px;display:grid;grid-template-columns:430px 1fr;gap:72px;align-items:start}
.tslide .tsvg{width:360px;height:360px;display:block;margin:0 auto}
.tslide .tdigits text{fill:color-mix(in srgb,var(--on-deep) 55%,transparent);font-size:19px;font-weight:700;text-anchor:middle;dominant-baseline:middle}
.tslide .tdigits line{stroke:color-mix(in srgb,var(--on-deep) 28%,transparent)}
.tslide .ttime{margin-top:10px;text-align:center;font-weight:var(--w-display);font-size:78px;line-height:1;letter-spacing:-.02em;color:var(--on-deep);font-variant-numeric:tabular-nums}
.tslide .tsep{opacity:.45;margin:0 2px}
.tslide .tbuttons{margin-top:18px;display:flex;gap:10px;justify-content:center;align-items:stretch}
.tslide .tb{font:inherit;font-weight:700;font-size:20px;letter-spacing:.02em;color:var(--on-deep);background:transparent;
  border:2px solid color-mix(in srgb,var(--on-deep) 45%,transparent);border-radius:var(--radius);padding:11px 16px;cursor:pointer;line-height:1;transition:background .15s,border-color .15s}
.tslide .tb:hover{background:color-mix(in srgb,var(--on-deep) 14%,transparent);border-color:var(--on-deep)}
.tslide .tstart{background:var(--accent);border-color:var(--accent);color:var(--on-accent);min-width:132px;font-size:21px}
.tslide .tstart:hover{background:color-mix(in srgb,var(--accent) 84%,#000);border-color:color-mix(in srgb,var(--accent) 84%,#000)}
.tslide .tsmall-row{margin-top:12px;display:flex;gap:10px;justify-content:center}
.tslide .tsmall{font-size:18px;padding:7px 14px;border-color:color-mix(in srgb,var(--on-deep) 28%,transparent);color:color-mix(in srgb,var(--on-deep) 75%,transparent)}
.tslide .tsteps{display:grid;gap:22px}
.tslide .tp{display:grid;grid-template-columns:52px 1fr;gap:20px;align-items:start}
.tslide .tpn{width:52px;height:52px;border:2px solid var(--accent);border-radius:var(--radius);color:var(--on-deep);font-weight:var(--w-display);font-size:24px;
  display:grid;place-items:center;line-height:1}
.tslide .tp h3{font-weight:700;font-size:28px;line-height:1.15;color:var(--on-deep);margin-bottom:6px}
.tslide .tp p{font-size:22px;line-height:1.4;color:color-mix(in srgb,var(--on-deep) 82%,transparent)}
.tslide .tfacts{margin-top:28px;padding-top:22px;border-top:1px solid color-mix(in srgb,var(--on-deep) 22%,transparent);
  display:grid;grid-template-columns:repeat(3,1fr);gap:22px}
.tslide .td small{display:block;font-weight:700;font-size:18px;letter-spacing:.14em;text-transform:uppercase;color:var(--accent-text);margin-bottom:6px}
.tslide .td span{display:block;font-size:19px;line-height:1.35;color:color-mix(in srgb,var(--on-deep) 85%,transparent)}
.tslide .tend{position:absolute;inset:0;z-index:9;display:none;place-items:center;background:var(--accent);cursor:pointer}
.tslide .tendtext{font-weight:var(--w-display);font-size:120px;line-height:1;color:var(--on-accent);letter-spacing:-.02em;text-align:center;padding:0 80px}
.tslide .tendhint{margin-top:36px;text-align:center;font-size:22px;letter-spacing:.04em;color:color-mix(in srgb,var(--on-accent) 80%,transparent)}
.tslide.ttimeup .tend{display:grid;animation:tfadein .5s cubic-bezier(.2,.7,.3,1) both}
.tslide.ttimeup .tendtext{animation:tpulse 1.1s ease-in-out infinite}
.tslide.ttimeup .tend{animation:tfadein .5s cubic-bezier(.2,.7,.3,1) both,tflash 1.1s ease-in-out 3}
@keyframes tflash{0%,100%{background:var(--accent)}50%{background:color-mix(in srgb,var(--accent) 79%,#000)}}
.tslide .tword{display:none}
.tslide.tallein .tgrid{grid-template-columns:1fr;justify-items:center}
.tslide.tallein .tbody{display:none}
.tslide.tallein .tsvg{width:376px;height:376px}
.tslide.tallein .ttime{font-size:96px}
.tslide.tallein .ttitle{text-align:center;margin-left:auto;margin-right:auto}
.tslide.tallein .kicker{text-align:center}
@keyframes tfadein{from{opacity:0;transform:scale(1.06)}to{opacity:1;transform:none}}
@keyframes tpulse{0%,100%{transform:scale(1)}50%{transform:scale(1.05)}}
.tslide.trunning .tring{animation:tbreathe 2s ease-in-out infinite}
@keyframes tbreathe{0%,100%{opacity:.5}50%{opacity:.95}}
</style>
<script>
(function(){
  var SCALE = 60;                                  /* dial with sixty minutes */
  function sectorPath(min){
    var R = 150, cx = 200, cy = 200;
    if (min <= 0) return "";
    if (min >= SCALE) return "M "+cx+" "+(cy-R)+" A "+R+" "+R+" 0 1 1 "+(cx-0.01)+" "+(cy-R)+" Z";
    var a = min / SCALE * 2 * Math.PI;
    var x = cx + R*Math.sin(a), y = cy - R*Math.cos(a);
    return "M "+cx+" "+cy+" L "+cx+" "+(cy-R)+" A "+R+" "+R+" 0 "+(a>Math.PI?1:0)+" 1 "+x.toFixed(2)+" "+y.toFixed(2)+" Z";
  }
  function drawDial(g){
    var parts = "";
    for (var i = 0; i < SCALE; i++){
      var a = i/SCALE*2*Math.PI, longTick = (i % 5 === 0);
      var r1 = longTick ? 132 : 142, r2 = 150;
      parts += '<line x1="'+(200+r1*Math.sin(a)).toFixed(1)+'" y1="'+(200-r1*Math.cos(a)).toFixed(1)+
               '" x2="'+(200+r2*Math.sin(a)).toFixed(1)+'" y2="'+(200-r2*Math.cos(a)).toFixed(1)+
               '" stroke-width="'+(longTick?2.5:1)+'"/>';
      if (longTick) parts += '<text x="'+(200+176*Math.sin(a)).toFixed(1)+'" y="'+(200-176*Math.cos(a)).toFixed(1)+'">'+i+'</text>';
    }
    g.innerHTML = parts;
  }
  var ac = null;
  function gong(){
    try{
      ac = ac || new (window.AudioContext || window.webkitAudioContext)();
      if (ac.state === "suspended") ac.resume();
      [0, 0.62, 1.24].forEach(function(t){
        [880, 1318.5, 2637].forEach(function(f, k){
          var o = ac.createOscillator(), g = ac.createGain();
          o.type = "sine"; o.frequency.value = f;
          var t0 = ac.currentTime + t, peak = 0.34 / (k + 1.6);
          g.gain.setValueAtTime(0.0001, t0);
          g.gain.exponentialRampToValueAtTime(peak, t0 + 0.012);
          g.gain.exponentialRampToValueAtTime(0.0001, t0 + 2.2);
          o.connect(g); g.connect(ac.destination);
          o.start(t0); o.stop(t0 + 2.3);
        });
      });
    }catch(e){}
  }
  function init(s){
    if(s.vsTimer) return;
    var preset = Math.max(1, parseInt(s.getAttribute("data-timer"), 10) || 20);
    var words  = s.querySelector(".tword");
    var seconds = preset * 60, running = false, endsAt = 0, done = false, duration = preset;
    var durationFields = Array.prototype.slice.call(s.querySelectorAll(".tduration"));
    var original = durationFields.map(function(f){ return f.textContent; });
    function showDuration(){
      durationFields.forEach(function(f, i){
        f.textContent = (duration === preset) ? original[i]
          : duration + " " + (duration === 1 ? words.dataset.one : words.dataset.many);
      });
    }
    var sector = s.querySelector(".tsector"), minEl = s.querySelector(".tmin"), secEl = s.querySelector(".tsek");
    var startButton = s.querySelector(".tstart");
    drawDial(s.querySelector(".tdigits"));

    function remaining(){ return running ? Math.max(0, (endsAt - Date.now()) / 1000) : seconds; }
    function draw(){
      var r = remaining();
      sector.setAttribute("d", sectorPath(r / 60));
      minEl.textContent = String(Math.floor(r / 60)).padStart(2, "0");
      secEl.textContent = String(Math.floor(r % 60)).padStart(2, "0");
      startButton.textContent = running ? words.dataset.pause : words.dataset.start;
      s.classList.toggle("trunning", running);
    }
    function pause(){ if (running){ seconds = remaining(); running = false; } draw(); }
    function start(){
      if (done){ done = false; s.classList.remove("ttimeup"); seconds = duration * 60; }
      if (seconds <= 0) seconds = duration * 60;
      endsAt = Date.now() + seconds * 1000; running = true; unlockAudio(); draw();
    }
    /* Browsers only allow sound after a user gesture, so the audio context is woken on click */
    function unlockAudio(){ try{ ac = ac || new (window.AudioContext || window.webkitAudioContext)();
                                 if (ac.state === "suspended") ac.resume(); }catch(e){} }
    function toggle(){ running ? pause() : start(); }
    startButton.addEventListener("click", toggle);
    function reset(){
      running = false; done = false; s.classList.remove("ttimeup"); seconds = duration * 60; draw();
    }
    function timeUp(){
      running = false; seconds = 0; done = true;
      s.classList.add("ttimeup"); gong(); draw();
    }
    function finish(){ if (!done){ unlockAudio(); timeUp(); } }
    function shift(min){
      var d = min * 60;
      var base = done ? 0 : remaining();
      var next = Math.min(SCALE * 60, Math.max(60, base + d));
      if (done){ done = false; s.classList.remove("ttimeup"); }
      /* Before the start the duration is exactly the time that is set, afterwards it moves by the step */
      if (running){ endsAt = Date.now() + next * 1000; duration = Math.min(SCALE, Math.max(1, duration + min)); }
      else { seconds = next; duration = Math.min(SCALE, Math.max(1, Math.round(next / 60))); }
      showDuration(); draw();
    }
    s.querySelector(".treset").addEventListener("click", reset);
    s.querySelector(".tnow").addEventListener("click", finish);
    s.querySelector(".tend").addEventListener("click", reset);
    Array.prototype.forEach.call(s.querySelectorAll(".tb[data-delta]"), function(b){
      b.addEventListener("click", function(){ shift(parseInt(b.getAttribute("data-delta"), 10)); });
    });
    /* Interface for the presenter view of the master */
    s.vsTimer = {
      toggle: toggle, delta: shift, reset: reset, finish: finish,
      status: function(){ return { remaining: done ? 0 : remaining(), running: running, done: done, duration: duration }; }
    };
    setInterval(function(){
      if (running && remaining() <= 0 && !done) timeUp();
      draw();
    }, 200);
    draw();
  }
  Array.prototype.forEach.call(document.querySelectorAll(".tslide"), init);
  window.vsTimerInit=init;                                  /* for a timer slide that is copied while editing */
})();
</script>
'''
