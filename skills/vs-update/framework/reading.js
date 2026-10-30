/* Reading version (mode "reading"), runs after the engine has set up the deck.
   1. Keeps the deck at rest: the engine's export state (no motion, all click steps shown, posters instead
      of players) stays on, also after the PDF export inside the deck has switched it off again.
   2. Every slide stays a whole slide in its master: render.py gives the reading version its own copy of a slide
      with texts for readers (data-only="reading", the paragraph under the title in .vs-explain); the engine sets
      the body smaller where that text needs the room (fitSlide). Speaker notes are taken out. */
(function(){
  var root=document.documentElement, deck=document.getElementById('deck');
  if(!deck||root.getAttribute('data-mode')!=='reading') return;      /* both versions are in the file, this one only runs when it is shown */
  var pages=Array.prototype.filter.call(deck.children,function(e){ return e.classList&&e.classList.contains('slide'); });

  function still(){
    root.classList.add('export');
    deck.querySelectorAll('.mbox').forEach(function(b){
      b.querySelectorAll('iframe.mlive').forEach(function(f){ f.remove(); });
      b.querySelectorAll('video.mlive').forEach(function(v){ try{ v.pause(); }catch(e){} });
      b.removeAttribute('data-state');
    });
  }
  still();
  new MutationObserver(function(){ if(!root.classList.contains('export')) still(); }).observe(root,{attributes:true,attributeFilter:['class']});

  /* video, embed and scene slides show their still; the address printed on it becomes a link */
  deck.querySelectorAll('.mbox').forEach(function(b){
    var url=['data-url','data-embed','data-src'].map(function(a){ return b.getAttribute(a)||''; }).filter(function(u){ return /^https?:\/\//.test(u); })[0];
    var line=b.querySelector('.murl, .mph span');
    if(!url||!line||line.querySelector('a')) return;
    var a=document.createElement('a'); a.href=url; a.target='_blank'; a.rel='noopener'; a.textContent=line.textContent;
    line.textContent=''; line.appendChild(a);
  });

  pages.forEach(function(s){
    try{ delete s.vsQuiz; }catch(e){}                        /* answers are shown, nothing to choose */
    Array.prototype.slice.call(s.children).forEach(function(c){ if(c.classList&&(c.classList.contains('notes')||c.classList.contains('cues')||c.classList.contains('read'))) c.remove(); });   /* speaker notes are not part of the reading version */
  });
  if(window.vsScheme) window.vsScheme();                    /* dark or light: the pages and the reduced slides take the scheme */
  window.vsReading=true;
})();
