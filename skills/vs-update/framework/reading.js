/* Reading version (mode "reading"), runs after the engine has set up the deck.
   1. Keeps the deck at rest: the engine's export state (no motion, all click steps shown, posters instead
      of players) stays on, also after the PDF export inside the deck has switched it off again.
   2. A slide with reader text (<aside class="read">, written by render.py) becomes a page: the section the
      engine pages through stays the page, its content moves into a reduced copy of itself beside the text.
   3. Section bar on every page: the chapter names of the language in a row, the current one marked. */
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
    Array.prototype.slice.call(s.children).forEach(function(c){ if(c.classList&&c.classList.contains('notes')) c.remove(); });   /* speaker notes are not part of the reading version */
    s._plain=s.classList.contains('cover')||s.classList.contains('no-footer');
    var read=null;
    Array.prototype.forEach.call(s.children,function(c){ if(c.classList.contains('read')) read=c; });
    if(!read) return;
    if(!read.textContent.trim()){ read.remove(); return; }
    var inner=document.createElement('div'), state=['off','active'].filter(function(c){ return s.classList.contains(c); });
    Array.prototype.forEach.call(s.attributes,function(a){ if(a.name!=='id'&&a.name!=='class') inner.setAttribute(a.name,a.value); });
    inner.className=s.className.split(/\s+/).filter(function(c){ return c&&['off','active','leave','back'].indexOf(c)<0; }).join(' ')+' active';
    Array.prototype.slice.call(s.childNodes).forEach(function(n){
      if(n===read||(n.nodeType===1&&n.classList.contains('footer'))) return;   /* page number and source stay on the page */
      inner.appendChild(n);
    });
    s.className='slide rpage'+(state.length?' '+state.join(' '):''); s.removeAttribute('style');
    var rs=document.createElement('div'); rs.className='rs'; rs.appendChild(inner);
    var rt=document.createElement('div'); rt.className='rt';
    var rti=document.createElement('div'); rti.className='rti'; rti.innerHTML=read.innerHTML; rt.appendChild(rti);
    if(read.hasAttribute('data-from')) rt.setAttribute('data-from',read.getAttribute('data-from'));
    read.remove();
    s.insertBefore(rt,s.firstChild); s.insertBefore(rs,rt);
  });

  var langs=[];
  pages.forEach(function(s){ var l=s.getAttribute('lang')||''; if(langs.indexOf(l)<0) langs.push(l); });
  langs.forEach(function(l){
    var list=pages.filter(function(s){ var x=s.getAttribute('lang'); return !x||x===l; }), chapters=[];
    list.forEach(function(s,i){
      var c=s.dataset.chapterName||'';
      if(c&&!chapters.some(function(k){ return k.name===c; })) chapters.push({name:c,page:i+1});
    });
    if(chapters.length<2) return;
    list.forEach(function(s){
      if(s._plain||(s.getAttribute('lang')||'')!==l||s.querySelector(':scope > .rbar')) return;
      var bar=document.createElement('nav'); bar.className='rbar';
      chapters.forEach(function(k){
        var a=document.createElement('a'); a.href='#/'+k.page; if(k.name===(s.dataset.chapterName||'')) a.className='cur';
        var t=document.createElement('span'); t.textContent=k.name; a.appendChild(t); bar.appendChild(a);
      });
      s.appendChild(bar); s.classList.add('hasbar');
    });
  });
  if(window.vsScheme) window.vsScheme();                    /* dark or light: the pages and the reduced slides take the scheme */
  window.vsReading=true;
})();
