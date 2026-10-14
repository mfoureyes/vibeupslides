"""Read a brand from a website and save it as a VibeUpSlides brand profile.

    python3 extract_brand.py https://example.com --name example [--pages 4] [--no-fonts] [--out DIR]

Opens the site in headless Chromium, visits the home page and a few internal pages and collects:
colours (weighted by how much area and text they cover), fonts (families, weights, the font files
the site loads), logos (header, footer, favicon), large photos, headings and copy, and screenshots.
The result is a brand folder:

    <home>/brands/<name>/
        brand.json        draft profile from heuristics, to be reviewed and corrected
        logos/ fonts/ images/
        elements/         icons/, arrows/ and shapes/ the site uses, as standalone svg files
        raw/extract.json  everything that was measured
        raw/components.json  look and feel: buttons, cards, labels, headings, image treatment, sections, graphics
        raw/copy.md       headings, navigation, buttons and paragraphs, for the voice analysis
        raw/screens/      screenshots of the pages, components/ holds close-ups of single components
        raw/elements.png  contact sheet of the saved icons and arrows
        raw/motion.json   how the site moves: transitions, keyframe animations, scroll reveals, hover, marquees, video,
                          motion libraries; with the drafted motion profile (brand.json, motion) and the reason for it

Fonts are sorted by licence situation (brand.json, fonts.families): open fonts (Google Fonts, Bunny Fonts,
well-known open-source families) are embedded, self-hosted files of unknown origin wait in fonts/pending/
until the user confirms the licence, fonts of a commercial service (Adobe Fonts and the like) are not saved.

<home> is $VIBEUPSLIDES_HOME, else ~/.vibeupslides. The draft is a starting point: look at the
screenshots, correct brand.json, then write voice.md and imagery.md (see references/brand-extraction.md).

Only read sites you are allowed to take the brand from. Font files stay under the licence of
their foundry: embed them only if the brand owner may use them in documents, otherwise pass
--no-fonts and the decks fall back to system fonts.
"""
import colorsys, hashlib, json, os, re, sys
from urllib.parse import urljoin, urlparse

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(HERE), "engine"))
import build as B

# ---------------------------------------------------------------- in-page measurement

MEASURE_JS = r"""
() => {
  const vis = e => { const r = e.getBoundingClientRect(); const s = getComputedStyle(e);
    return r.width > 1 && r.height > 1 && s.visibility !== 'hidden' && s.display !== 'none' && parseFloat(s.opacity) > .05; };
  const rgb = c => { const m = (c || '').match(/rgba?\(([^)]+)\)/); if (!m) return null;
    const p = m[1].split(/[ ,\/]+/).map(parseFloat); if (p.length > 3 && p[3] < .5) return null;
    return '#' + p.slice(0, 3).map(v => Math.round(v).toString(16).padStart(2, '0')).join(''); };
  const add = (map, key, w) => { if (key) map[key] = (map[key] || 0) + w; };
  const bg = {}, text = {}, border = {};
  const all = Array.from(document.querySelectorAll('body, body *')).filter(e => !e.closest('[data-vs-consent]')).slice(0, 6000);
  for (const e of all) {
    if (!vis(e)) continue;
    const s = getComputedStyle(e), r = e.getBoundingClientRect();
    add(bg, rgb(s.backgroundColor), Math.min(r.width * r.height, 3e6));
    const own = Array.from(e.childNodes).filter(n => n.nodeType === 3).map(n => n.textContent.trim()).join(' ');
    if (own.length > 1) add(text, rgb(s.color), own.length * Math.max(parseFloat(s.fontSize) / 16, 1));
    if (parseFloat(s.borderTopWidth) > 0) add(border, rgb(s.borderTopColor), r.width);
  }
  const style = (sel, limit) => Array.from(document.querySelectorAll(sel)).filter(e => vis(e) && !e.closest('[data-vs-consent]')).slice(0, limit || 6).map(e => {
    const s = getComputedStyle(e), r = e.getBoundingClientRect();
    return { text: (e.innerText || e.value || '').trim().slice(0, 80), color: rgb(s.color), background: rgb(s.backgroundColor),
      fontFamily: s.fontFamily, fontWeight: s.fontWeight, fontSize: parseFloat(s.fontSize), letterSpacing: s.letterSpacing,
      textTransform: s.textTransform, borderRadius: s.borderTopLeftRadius, borderColor: parseFloat(s.borderTopWidth) > 0 ? rgb(s.borderTopColor) : null,
      width: Math.round(r.width), height: Math.round(r.height) }; });
  const styles = { body: style('body', 1), h1: style('h1', 3), h2: style('h2', 5), h3: style('h3', 5), p: style('p', 6), a: style('main a, p a, li a', 8),
    button: style('button, a[class*="btn" i], a[class*="button" i], [role="button"], input[type="submit"]', 12),
    nav: style('nav a, header a', 8), header: style('header', 1), footer: style('footer', 1),
    card: style('[class*="card" i], article', 8), img: style('main img, section img', 8) };
  const vars = {};
  for (const sheet of Array.from(document.styleSheets)) { let rules; try { rules = sheet.cssRules; } catch (e) { continue; }
    for (const rule of Array.from(rules || [])) if (rule.selectorText && /^(:root|html|body)$/.test(rule.selectorText.trim()))
      for (const name of Array.from(rule.style)) if (name.startsWith('--')) vars[name] = rule.style.getPropertyValue(name).trim().slice(0, 80); }
  const probe = document.createElement('i'); document.body.appendChild(probe);
  const palette = {};
  for (const [name, value] of Object.entries(vars)) { if (/admin|editor|synced|bound|shadow|gradient/i.test(name)) continue;
    if (!/^(#|rgb|hsl|oklch|color\()/i.test(value)) continue; probe.style.color = ''; probe.style.color = value; const c = rgb(getComputedStyle(probe).color); if (c) palette[name] = c; }
  probe.remove();
  const fonts = []; document.fonts.forEach(f => fonts.push({ family: f.family.replace(/["']/g, ''), weight: f.weight, style: f.style, status: f.status }));
  const fontFaces = Array.from(document.querySelectorAll('style')).map(s => s.textContent).join('\n').match(/@font-face\s*\{[^}]*\}/g) || [];
  const where = e => e.closest('footer') ? 'footer' : (e.closest('header, nav, [class*="header" i], [class*="navbar" i]') ? 'header' : 'body');
  const isLogo = e => /logo|brand/i.test([e.className && e.className.baseVal !== undefined ? e.className.baseVal : e.className, e.id, e.alt, e.getAttribute('aria-label'), e.currentSrc || e.src || ''].join(' '));
  const home = e => { const a = e.closest('a'); if (!a) return false; try { const u = new URL(a.href, location.href); return u.origin === location.origin && (u.pathname === '/' || u.pathname === location.pathname.split('/').slice(0, 2).join('/') + '/'); } catch (x) { return false; } };
  const logos = []; let k = 0;
  for (const e of Array.from(document.querySelectorAll('img, svg'))) {
    if (!vis(e) || e.closest('svg') !== (e.tagName.toLowerCase() === 'svg' ? e : null) && e.tagName.toLowerCase() === 'svg') continue;
    const r = e.getBoundingClientRect(); if (r.width < 24 || r.height < 12 || r.width > 700 || r.height > 320) continue;
    const loc = where(e), named = isLogo(e) || (e.parentElement && isLogo(e.parentElement)), linked = home(e);
    if (!(named || (linked && loc !== 'body'))) continue;
    e.setAttribute('data-vs-logo', String(k));
    let bgc = null; for (let p = e; p && !bgc; p = p.parentElement) bgc = rgb(getComputedStyle(p).backgroundColor);
    const svg = e.tagName.toLowerCase() === 'svg';
    const sibs = e.parentElement ? Array.from((e.closest('ul, [class*="grid" i], [class*="slider" i], [class*="carousel" i], [class*="logos" i], [class*="partner" i], [class*="client" i]') || e.parentElement.parentElement || e.parentElement).querySelectorAll('img, svg')).filter(x => { const q = x.getBoundingClientRect(); return q.width >= 24 && q.width <= 700; }).length : 0;
    logos.push({ k: k++, wall: sibs >= 4 && !linked, where: loc, named, linked, svg, src: svg ? null : (e.currentSrc || e.src), width: Math.round(r.width), height: Math.round(r.height), top: Math.round(r.top + scrollY),
      background: bgc || '#ffffff', color: rgb(getComputedStyle(e).color), alt: e.alt || e.getAttribute('aria-label') || '',
      markup: svg ? new XMLSerializer().serializeToString(e) : null });
    if (k > 16) break;
  }
  const images = [];
  for (const e of Array.from(document.images)) { if (!vis(e) || e.hasAttribute('data-vs-logo')) continue; const r = e.getBoundingClientRect();
    if (e.naturalWidth >= 700 && r.width >= 300 && r.height >= 200) images.push({ src: e.currentSrc || e.src, w: e.naturalWidth, h: e.naturalHeight, area: Math.round(r.width * r.height), alt: e.alt || '' }); }
  for (const e of all) { const s = getComputedStyle(e), m = s.backgroundImage && s.backgroundImage.match(/url\(["']?([^"')]+)["']?\)/); if (!m || !vis(e)) continue;
    const r = e.getBoundingClientRect(); if (r.width >= 600 && r.height >= 300 && !/\.svg(\?|$)/i.test(m[1])) images.push({ src: new URL(m[1], location.href).href, w: 0, h: 0, area: Math.round(r.width * r.height), alt: '', css: true }); }
  const meta = n => { const e = document.querySelector('meta[name="' + n + '"], meta[property="' + n + '"]'); return e ? e.content : ''; };
  const icons = Array.from(document.querySelectorAll('link[rel~="icon"], link[rel="apple-touch-icon"], link[rel="mask-icon"]')).map(l => ({ rel: l.rel, href: l.href, sizes: l.getAttribute('sizes') || '', type: l.type || '' }));
  const txt = (sel, n, min) => Array.from(document.querySelectorAll(sel)).filter(vis).map(e => (e.innerText || '').replace(/\s+/g, ' ').trim()).filter(t => t.length >= (min || 2)).slice(0, n);
  const copy = { title: document.title, description: meta('description'), siteName: meta('og:site_name'), ogImage: meta('og:image'), themeColor: meta('theme-color'), lang: document.documentElement.lang || '',
    h1: txt('h1', 5), h2: txt('h2', 14), h3: txt('h3', 14), nav: txt('nav a, header a', 20), buttons: [...new Set(styles.button.map(b => b.text).filter(Boolean))],
    paragraphs: txt('main p, section p, article p, p', 30, 60) };
  const links = Array.from(document.querySelectorAll('nav a[href], header a[href]')).map(a => { try { const u = new URL(a.href, location.href); return u.origin === location.origin ? u.origin + u.pathname : null; } catch (e) { return null; } }).filter(Boolean);
  return { url: location.href, bg, text, border, styles, vars, palette, fonts, fontFaces, logos, images, icons, copy, links: [...new Set(links)] };
}
"""

# Consent banners: the privacy-preserving choice is taken (decline), never "accept". Whatever is left
# of the banner is hidden so it neither covers the screenshots nor counts as brand colour.
CONSENT_JS = r"""
() => {
  const box = '[id*="cookie" i],[class*="cookie" i],[id*="consent" i],[class*="consent" i],[id*="gdpr" i],[class*="gdpr" i],[id*="onetrust" i],[id*="usercentrics" i],[class*="cmp" i],[id*="cmp" i],[aria-modal="true"]';
  const decline = /^(alle )?ablehnen|nur (notwendige|erforderliche|essenzielle)|weiter ohne|ohne einwilligung|reject( all)?$|decline|deny|refuse|only (necessary|essential|required)|necessary only|continue without|tout refuser|refuser|rechazar|rifiuta/i;
  let clicked = '';
  for (const b of document.querySelectorAll('button, a, [role="button"], input[type="button"], input[type="submit"]')) {
    const t = (b.innerText || b.value || '').trim();
    if (t && t.length < 60 && decline.test(t) && b.closest(box) && b.getBoundingClientRect().width > 0) { b.click(); clicked = t; break; }
  }
  return clicked;
}
"""
HIDE_CONSENT_JS = r"""
() => {
  const box = '[id*="cookie" i],[class*="cookie" i],[id*="consent" i],[class*="consent" i],[id*="gdpr" i],[class*="gdpr" i],[id*="onetrust" i],[id*="usercentrics" i],[aria-modal="true"]';
  let n = 0;
  for (const e of document.querySelectorAll(box)) {
    const s = getComputedStyle(e), r = e.getBoundingClientRect();
    if ((s.position === 'fixed' || s.position === 'sticky' || s.position === 'absolute' || e.getAttribute('aria-modal') === 'true') && r.width > 200 && r.height > 60) {
      e.setAttribute('data-vs-consent', '1'); e.style.setProperty('display', 'none', 'important'); n++; }
  }
  document.documentElement.style.overflow = 'auto'; document.body.style.overflow = 'auto';
  return n;
}
"""

# Look and feel: how the site builds its components (buttons, cards, labels, headings, image treatment,
# section rhythm, graphic elements, lists, links, arrows, icons). Runs after MEASURE_JS on every page that
# is open anyway. Each step is isolated: a failing step leaves null and a note. With mark=true (home page)
# the measured elements get data-vs-* attributes so that they can be screenshotted afterwards.
COMPONENTS_JS = r"""
(mark) => {
  const out = { url: location.href, notes: [] };
  const VW = document.documentElement.clientWidth;
  const cs = (e, p) => getComputedStyle(e, p || null);
  const skip = e => !!e.closest('[data-vs-consent]');
  const vis = e => { const r = e.getBoundingClientRect(), s = cs(e); return r.width > 1 && r.height > 1 && s.visibility !== 'hidden' && s.display !== 'none' && parseFloat(s.opacity) > .05; };
  const num = v => Math.round((parseFloat(v) || 0) * 10) / 10;
  const norm = (v, n) => (v || '').replace(/\s+/g, ' ').trim().slice(0, n || 200);
  const rgba = c => { const m = (c || '').match(/rgba?\(([^)]+)\)/); if (!m) return null; const p = m[1].split(/[ ,\/]+/).map(parseFloat); return [p[0], p[1], p[2], p.length > 3 && !isNaN(p[3]) ? p[3] : 1]; };
  const hex = p => '#' + p.slice(0, 3).map(v => Math.round(v).toString(16).padStart(2, '0')).join('');
  // colour as #rrggbb, or #rrggbbaa when it is translucent; null when there is none
  const col = c => { const p = rgba(c); if (!p) return /^(color|oklch|oklab|lab|lch)\(/.test(c || '') ? norm(c, 60) : null; if (p[3] < .03) return null; return p[3] > .97 ? hex(p) : hex(p) + Math.round(p[3] * 255).toString(16).padStart(2, '0'); };
  const txt = (e, n) => (e.innerText || e.value || '').replace(/\s+/g, ' ').trim().slice(0, n || 60);
  const cls = e => (e.className && e.className.baseVal !== undefined ? e.className.baseVal : (e.className || '')) + '';
  const tag = (e, k, v) => { if (mark) e.setAttribute('data-vs-' + k, String(v)); };
  const step = (name, fn) => { try { out[name] = fn(); } catch (x) { out[name] = null; out.notes.push(name + ': ' + String(x && x.message || x).slice(0, 120)); } };
  const where = e => e.closest('footer') ? 'footer' : (e.closest('header, nav, [class*="header" i], [class*="navbar" i]') ? 'header' : 'body');
  const on = e => { for (let p = e; p; p = p.parentElement) { const s = cs(p), c = col(s.backgroundColor); if (c && c.length === 7) return c; if (/gradient\(|url\(/.test(s.backgroundImage)) return 'image'; } return '#ffffff'; };
  const quad = (a, b, c, d) => { const v = [a, b, c, d].map(num); if (v.every(x => x === v[0])) return v[0] + 'px'; if (v[0] === v[2] && v[1] === v[3]) return v[0] + 'px ' + v[1] + 'px'; return v.map(x => x + 'px').join(' '); };
  const pad = s => quad(s.paddingTop, s.paddingRight, s.paddingBottom, s.paddingLeft);
  const rad = (s, r) => { const v = [s.borderTopLeftRadius, s.borderTopRightRadius, s.borderBottomRightRadius, s.borderBottomLeftRadius], n = v.map(x => parseFloat(x) || 0), same = n.every(x => x === n[0]);
    const round = v.some(x => /%/.test(x)) ? n[0] >= 50 : n[0] >= Math.min(r.width, r.height) / 2 - 1;
    if (same && n[0] > 0 && round) return Math.abs(r.width - r.height) < 3 ? 'circle' : 'pill';
    if (v.some(x => /%/.test(x))) return same ? v[0].split(' ')[0] : v.join(' '); return same ? num(n[0]) + 'px' : n.map(x => num(x) + 'px').join(' '); };
  const bord = s => { const sides = ['Top', 'Right', 'Bottom', 'Left'].map(k => { const w = parseFloat(s['border' + k + 'Width']) || 0, st = s['border' + k + 'Style'], c = col(s['border' + k + 'Color']); return (w > 0 && st !== 'none' && st !== 'hidden' && c) ? num(w) + 'px ' + st + ' ' + c : null; });
    if (sides.every(x => !x)) return null; if (sides.every(x => x === sides[0])) return sides[0]; const o = {}; ['top', 'right', 'bottom', 'left'].forEach((k, i) => { if (sides[i]) o[k] = sides[i]; }); return o; };
  const sh = v => (!v || v === 'none') ? null : norm(v, 170);
  const track = s => { const v = parseFloat(s.letterSpacing), f = parseFloat(s.fontSize) || 16; return (!v || isNaN(v)) ? null : Math.round(v / f * 1000) / 1000 + 'em'; };
  const tcase = s => s.textTransform === 'none' ? null : s.textTransform;
  const lh = s => { const v = parseFloat(s.lineHeight), f = parseFloat(s.fontSize); return isNaN(v) ? 'normal' : Math.round(v / f * 100) / 100; };
  const fam = s => (s.fontFamily || '').split(',')[0].trim().replace(/["']/g, '');
  const bgOf = s => { const g = s.backgroundImage; if (g && g !== 'none') return /gradient\(/.test(g) ? norm(g.replace(/url\([^)]*\)/g, 'url()'), 220) : 'image'; return col(s.backgroundColor); };
  const maskOf = s => { const m = s.maskImage && s.maskImage !== 'none' ? s.maskImage : (s.webkitMaskImage && s.webkitMaskImage !== 'none' ? s.webkitMaskImage : null); return m ? norm(m.replace(/url\(["']?data:[^)]*\)/g, 'url(data)'), 120) : null; };
  const pseudo = e => ['::before', '::after'].map(p => { const s = cs(e, p); if (!s || s.content === 'none' || s.content === 'normal' || s.display === 'none') return null;
    return { p: p.slice(2), s, text: s.content.replace(/^["']|["']$/g, ''), w: parseFloat(s.width) || 0, h: parseFloat(s.height) || 0, bg: col(s.backgroundColor), color: col(s.color), pos: s.position,
      img: s.backgroundImage !== 'none' || !!maskOf(s), radius: parseFloat(s.borderTopLeftRadius) || 0, border: Math.max(parseFloat(s.borderTopWidth) || 0, parseFloat(s.borderBottomWidth) || 0, parseFloat(s.borderLeftWidth) || 0), borderColor: col(s.borderTopColor) }; }).filter(Boolean);
  const ARW = /[←-⇿➔-➾⟵-⟿⬅-⬍⮕›‹»«▶▸►]/g, PUA = /[-]/;
  const NAMED = /arrow|chevron|caret|(^|[-_ ])angle|pfeil/i;
  const names = e => { const u = e.querySelector && e.querySelector('use'), p = e.parentElement, t = e.querySelector && e.querySelector('title');
    return [cls(e), e.id, e.getAttribute('aria-label'), e.getAttribute('data-icon'), e.getAttribute('src'), u && (u.getAttribute('href') || u.getAttribute('xlink:href')), p && cls(p), p && p.getAttribute('aria-label'), t && t.textContent].filter(Boolean).join(' '); };
  const BTN = 'button, a[class*="btn" i], a[class*="button" i], a[class*="cta" i], [role="button"], input[type="submit"], input[type="button"]';
  const all = Array.from(document.querySelectorAll('body *')).filter(e => (!(e instanceof SVGElement) || e.tagName === 'svg') && !/^(SCRIPT|STYLE|NOSCRIPT|TEMPLATE|BR|OPTION)$/.test(e.tagName) && !skip(e)).slice(0, 6000);
  // decoration of a small text: a pseudo element, a leading glyph, an empty child or a one-sided border
  const mark2 = (q) => q.text ? (PUA.test(q.text) ? { type: 'icon-font' } : { type: 'glyph', glyph: q.text.trim().slice(0, 3), color: q.color }) :
    (q.w > 0 && (q.bg || q.border || q.img)) ? { type: q.img && !q.bg ? 'icon' : (q.w >= Math.max(q.h, q.border, 1) * 3 ? 'line' : (Math.abs(q.w - q.h) <= 2 ? (q.radius >= q.w / 2 - 1 ? 'dot' : 'square') : 'bar')), width: num(q.w), height: num(q.h || q.border), color: q.bg || q.borderColor || q.color } : null;
  const decoration = (e, s) => { for (const q of pseudo(e)) { const m = mark2(q); if (m && (m.type !== 'glyph' || /^[—–\-•·\/#|●■→↗+*]+$/.test(m.glyph))) return Object.assign(m, { at: q.p }); }
    const t = txt(e, 4); if (/^[—–•·\/#|●■]\s?/.test(t)) return { type: 'glyph', glyph: t[0], at: 'text' };
    const c = e.firstElementChild; if (c && !txt(c)) { const r = c.getBoundingClientRect(), q = cs(c); if (/^(svg|IMG|I)$/.test(c.tagName) && r.width > 0) return { type: 'icon', width: num(r.width), at: 'before' };
      if (r.width > 0 && r.height > 0 && r.height <= 14 && col(q.backgroundColor)) return { type: r.width >= r.height * 3 ? 'line' : (parseFloat(q.borderTopLeftRadius) >= r.width / 2 - 1 ? 'dot' : 'square'), width: num(r.width), height: num(r.height), color: col(q.backgroundColor), at: 'before' }; }
    const b = bord(s); if (b && typeof b === 'object') { const k = Object.keys(b); if (k.length === 1) return { type: 'border-' + k[0], line: b[k[0]] }; }
    return null; };

  step('buttons', () => { const res = []; let i = 0;
    for (const e of document.querySelectorAll(BTN)) { if (res.length >= 48) break; if (skip(e) || !vis(e) || (e.parentElement && e.parentElement.closest(BTN))) continue;
      const r = e.getBoundingClientRect(), t = txt(e, 44); if (!t || txt(e, 80).length > 44 || r.height < 22 || r.height > 96 || r.width < 44 || r.width > 520) continue;
      let s = cs(e), g = bgOf(s), b = bord(s), box = r;
      if (!g && !b) { const c = Array.from(e.children).find(c => { const q = c.getBoundingClientRect(); return q.width >= r.width * .9 && q.height >= r.height * .8 && (bgOf(cs(c)) || bord(cs(c))); }); if (c) { s = cs(c); g = bgOf(s); b = bord(s); box = c.getBoundingClientRect(); } }
      const pon = e.parentElement ? on(e.parentElement) : '#ffffff'; if (g && g === pon) g = null;
      const kind = g ? 'filled' : (typeof b === 'string' ? 'outline' : 'text'), loc = where(e), fs = cs(e);
      let arrow = null, icon = null; const m = (e.innerText || e.value || '').match(ARW); if (m) arrow = m[0]; else if (/\s>$/.test(t)) arrow = '>';
      if (!arrow) for (const q of pseudo(e).concat(...Array.from(e.children).slice(0, 4).map(pseudo))) { const pm = q.text.match(ARW); if (pm) { arrow = pm[0]; break; } if (PUA.test(q.text)) { icon = 'icon-font'; } else if (!q.text && q.img && q.w > 0 && q.w <= 40) icon = 'css-image'; }
      const sv = e.querySelector('svg, img'); if (sv) { const q = sv.getBoundingClientRect(); if (q.width > 0 && q.width <= 48) { const side = q.left + q.width / 2 > r.left + r.width / 2 ? 'trailing' : 'leading'; if (!arrow && NAMED.test(names(sv))) arrow = 'svg'; icon = side + ' ' + sv.tagName.toLowerCase(); } }
      if (kind === 'text' && !(loc === 'body' && (arrow || icon || /underline/.test(fs.textDecorationLine) || (b && typeof b === 'object')))) continue;   // menu toggles and plain nav items are not buttons
      tag(e, 'b', i);
      res.push({ ref: mark ? i : null, kind, where: loc, text: t, background: g, color: col(fs.color), border: b, radius: rad(s, box), padding: pad(s), fontWeight: fs.fontWeight, fontSize: num(fs.fontSize), textTransform: tcase(fs), letterSpacing: track(fs),
        boxShadow: sh(s.boxShadow), arrow, icon, on: pon, height: Math.round(box.height), width: Math.round(box.width), family: fam(fs), underline: /underline/.test(fs.textDecorationLine) || null, transition: s.transitionDuration && s.transitionDuration !== '0s' ? norm(s.transitionProperty + ' ' + s.transitionDuration, 60) : null }); i++; }
    return res; });

  step('cards', () => { const res = [], taken = []; let i = 0;
    const named = new Set(document.querySelectorAll('[class*="card" i], article, [class*="tile" i], [class*="teaser" i], [class*="feature" i], [class*="box" i]'));
    for (const e of all) { if (res.length >= 40) break; if (!/^(DIV|LI|A|ARTICLE|SECTION|FIGURE)$/.test(e.tagName)) continue;
      const r = e.getBoundingClientRect(); if (r.width < 180 || r.width > Math.min(760, VW * .62) || r.height < 110 || r.height > 900) continue;
      if (taken.some(t => t.contains(e)) || !vis(e) || e.closest('header, nav, footer, form') || e.matches(BTN)) continue;
      const s = cs(e), b = bord(s), shd = sh(s.boxShadow), pon = e.parentElement ? on(e.parentElement) : '#ffffff'; let g = bgOf(s); if (g === pon) g = null;
      let frameless = false;
      if (!(g || typeof b === 'string' || shd || (named.has(e) && parseFloat(s.borderTopLeftRadius) > 0))) {      // no frame: still a card if it is an image with a heading below, repeated side by side
        const pic = e.querySelector('img, picture'), hd = e.querySelector('h2,h3,h4,h5'), sib = e.parentElement ? Array.from(e.parentElement.children).filter(x => x.tagName === e.tagName && cls(x) === cls(e)).length : 0;
        if (!pic || !hd || sib < 2 || e.querySelectorAll('h2,h3,h4,h5').length > 1) continue; const q = pic.getBoundingClientRect(); if (q.width < r.width * .9 || q.height < 80 || q.top - r.top > 4) continue; frameless = true; }
      const t = txt(e, 50); if (t.length < 8 || !e.querySelector('h1,h2,h3,h4,h5,h6,p,strong,span')) continue;
      let image = 'none', imageRadius = null; const bw = parseFloat(s.borderTopWidth) || 0, im = Array.from(e.querySelectorAll('img, picture, video')).find(x => x.getBoundingClientRect().width > 0), ic = e.querySelector('svg');
      if (/url\(/.test(s.backgroundImage)) image = 'background';
      else if (im) { const q = im.getBoundingClientRect(); if (q.width < 72 && q.height < 72) image = 'icon';
        else { const fullW = q.width >= r.width - 2 * bw - 3, top = q.top - r.top <= bw + 2, fullH = q.height >= r.height - 2 * bw - 3; image = fullW && fullH ? 'cover' : (fullW && top ? 'flush-top' : (fullH && q.left - r.left <= bw + 2 ? 'flush-left' : (fullH ? 'flush-right' : 'inset'))); imageRadius = rad(cs(im), q); } }
      else if (ic) image = 'icon';
      const h = e.querySelector('h1,h2,h3,h4,h5,h6'), p = e.querySelector('p'), first = h || p; let inset = null; if (first) inset = Math.max(0, Math.round(first.getBoundingClientRect().left - r.left));
      taken.push(e); tag(e, 'c', i);
      res.push({ ref: mark ? i : null, text: t, frameless, background: g, border: b, radius: rad(s, r), shadow: shd, padding: pad(s), image, imageRadius, textInset: inset, overflow: s.overflowX !== 'visible' ? s.overflowX : null,
        heading: h ? { size: num(cs(h).fontSize), weight: cs(h).fontWeight, color: col(cs(h).color) } : null, textColor: p ? col(cs(p).color) : col(s.color), textSize: p ? num(cs(p).fontSize) : null,
        on: pon, width: Math.round(r.width), height: Math.round(r.height), link: e.tagName === 'A' || !!e.querySelector('a') }); i++; }
    return res; });

  step('labels', () => { const res = [], seen = new Set(); let i = 0;
    const rec = (e, kind, h) => { if (seen.has(e) || res.length >= 40) return false; const t = txt(e, 48); if (t.length < 2) return false; seen.add(e);
      let st = e; while (st.children.length === 1 && txt(st.firstElementChild, 48) === t) st = st.firstElementChild;      // the style often sits on the innermost wrapper
      const s = cs(st), o = cs(e), r = e.getBoundingClientRect(); const g = bgOf(o) || bgOf(s), b = bord(o) || bord(s), framed = !!(g || typeof b === 'string');
      tag(e, 'l', i); res.push({ ref: mark ? i : null, kind: kind === 'eyebrow' ? 'eyebrow' : (framed ? 'badge' : 'label'), framed, text: t, above: h ? h.tagName.toLowerCase() : null, color: col(s.color), background: g, border: typeof b === 'string' ? b : null,
        radius: framed ? rad(g || b ? (bgOf(o) || bord(o) ? o : s) : o, r) : null, padding: framed ? pad(bgOf(o) || bord(o) ? o : s) : null, textTransform: tcase(s), letterSpacing: track(s), fontWeight: s.fontWeight, fontSize: num(s.fontSize), family: fam(s),
        decoration: decoration(e, o) || (st !== e ? decoration(st, s) : null), gap: h ? Math.round(h.getBoundingClientRect().top - r.bottom) : null }); i++; return true; };
    let n = 0;
    for (const h of document.querySelectorAll('h1, h2, h3')) { if (n >= 30) break; if (skip(h) || !vis(h) || h.closest('footer, nav')) continue; n++;
      const hs = parseFloat(cs(h).fontSize), hr = h.getBoundingClientRect(); let c = h.previousElementSibling; if (!c && h.parentElement && h.parentElement.children.length <= 2) c = h.parentElement.previousElementSibling;
      for (let d = 0; c && d < 3 && c.children.length > 1 && !txt(c, 60).length; d++) c = c.lastElementChild;
      if (!c || /^(H[1-6]|IMG|PICTURE|FIGURE|UL|OL|NAV|FORM)$/.test(c.tagName) || c.matches(BTN) || !vis(c)) continue;
      const t = txt(c, 60), cr = c.getBoundingClientRect(); let st = c; while (st.children.length === 1 && txt(st.firstElementChild, 60) === t) st = st.firstElementChild;
      const fs = parseFloat(cs(st).fontSize); if (t.length < 2 || t.length > 48 || c.querySelector('h1,h2,h3,h4,img,picture') || fs > Math.min(22, hs * .66) || cr.bottom > hr.top + 6 || hr.top - cr.bottom > 64) continue;
      if (rec(c, 'eyebrow', h)) tag(h, 'eh', res.length - 1); }
    for (const e of document.querySelectorAll('[class*="badge" i], [class*="tag" i], [class*="pill" i], [class*="chip" i], [class*="label" i], [class*="eyebrow" i], [class*="kicker" i], [class*="overline" i], [class*="subline" i], [class*="tagline" i], [class*="category" i]')) {
      if (res.length >= 40) break; if (skip(e) || seen.has(e) || /^(LABEL|INPUT|SELECT|TEXTAREA|H[1-6]|svg|IMG|BODY|HTML)$/.test(e.tagName) || e.closest('form, nav, header, footer') || e.matches(BTN) || !vis(e)) continue;
      const r = e.getBoundingClientRect(), s = cs(e), t = txt(e, 60); if (t.length < 2 || t.length > 32 || r.height > 44 || parseFloat(s.fontSize) > 18 || e.children.length > 3 || e.querySelector('h1,h2,h3,h4,p,ul,img,picture')) continue;
      const framed = bgOf(s) || typeof bord(s) === 'string'; if (!framed && !(s.textTransform === 'uppercase' || parseFloat(s.letterSpacing) > .3 || /eyebrow|kicker|overline|subline|tagline/i.test(cls(e)))) continue;
      rec(e, 'badge', null); }
    return res; });

  step('headings', () => { const res = [];
    for (const lvl of ['h1', 'h2', 'h3']) { let n = 0; for (const e of document.querySelectorAll(lvl)) { if (n >= 8) break; if (skip(e) || !vis(e) || e.closest('footer, nav')) continue; const t = txt(e, 400); if (!t) continue; n++;
      let st = e; while (st.children.length === 1 && txt(st.firstElementChild, 400) === t && !/^(A)$/.test(st.firstElementChild.tagName)) st = st.firstElementChild;
      const s = cs(st), hl = [], gradText = /text/.test(s.webkitBackgroundClip || s.backgroundClip || '') && /gradient\(/.test(s.backgroundImage);
      for (const c of st.querySelectorAll('span, em, mark, strong, b, i, u, a')) { if (hl.length >= 2) break; const ct = txt(c, 400); if (!ct || ct.length > t.length * .85 || !vis(c) || hl.some(x => x.el.contains(c))) continue; const q = cs(c), how = {};
        if (/text/.test(q.webkitBackgroundClip || q.backgroundClip || '') && /gradient\(/.test(q.backgroundImage)) how.gradient_text = norm(q.backgroundImage, 160);
        else { if (col(q.color) !== col(s.color)) how.color = col(q.color); if (bgOf(q)) how.background = bgOf(q); }
        if (/underline/.test(q.textDecorationLine) && !/underline/.test(s.textDecorationLine) && c.tagName !== 'A') how.underline = [q.textDecorationStyle, q.textDecorationThickness, col(q.textDecorationColor)].join(' ');
        if (q.fontStyle !== s.fontStyle) how.font_style = q.fontStyle; if (q.fontWeight !== s.fontWeight) how.weight = q.fontWeight; if (fam(q) !== fam(s)) how.family = fam(q);
        for (const p of pseudo(c)) if (!p.text && (p.bg || p.img) && p.pos === 'absolute') how.shape_behind = { background: p.bg || 'image', height: num(p.h) };
        if (how.background && bgOf(q) && how.background !== 'image') how.padding = pad(q), how.radius = rad(q, c.getBoundingClientRect());
        if (Object.keys(how).length) hl.push(Object.assign({ el: c, tag: c.tagName.toLowerCase(), text: ct.slice(0, 40) }, how)); }
      hl.forEach(x => delete x.el); const r = e.getBoundingClientRect();
      res.push({ level: lvl, text: t.slice(0, 60), size: num(s.fontSize), weight: s.fontWeight, lineHeight: lh(s), letterSpacing: track(s), textTransform: tcase(s), color: gradText ? 'gradient: ' + norm(s.backgroundImage, 160) : col(s.color), family: fam(s),
        align: /center|right/.test(s.textAlign) ? s.textAlign : null, fontStyle: s.fontStyle !== 'normal' ? s.fontStyle : null, width: Math.round(r.width), on: on(e), highlight: hl.length ? hl : null, decoration: decoration(e, cs(e)) }); } }
    return res; });

  step('images', () => { const res = [], css = []; let i = 0;
    const layer = (s, kind) => { const g = s.backgroundImage && /gradient\(/.test(s.backgroundImage) ? norm(s.backgroundImage, 200) : null, c = col(s.backgroundColor), op = parseFloat(s.opacity), bl = s.mixBlendMode !== 'normal' ? s.mixBlendMode : null;
      if (!g && !(c && (c.length === 9 || op < 1 || bl))) return null; const o = { layer: kind, background: g || c }; if (op < 1) o.opacity = op; if (bl) o.blend = bl; return o; };
    for (const e of document.querySelectorAll('img, video')) { if (res.length >= 40) break; if (skip(e) || !vis(e) || e.hasAttribute('data-vs-logo') || e.closest('header, nav, footer')) continue;
      const r = e.getBoundingClientRect(); if (r.width < 140 || r.height < 90 || /\.svg(\?|$)/i.test(e.currentSrc || e.src || '')) continue;
      const s = cs(e); let box = r, radius = rad(s, r), clip = s.clipPath !== 'none' ? norm(s.clipPath, 160) : null, mask = maskOf(s), filter = s.filter !== 'none' ? norm(s.filter, 120) : null, blend = s.mixBlendMode !== 'normal' ? s.mixBlendMode : null,
        shadow = sh(s.boxShadow), border = bord(s), tint = null; const overlays = [];
      for (let p = e.parentElement, d = 0; p && d < 3 && p !== document.body; p = p.parentElement, d++) { const q = p.getBoundingClientRect(), ps = cs(p);
        const tight = Math.abs(q.width - r.width) <= 8 && Math.abs(q.height - r.height) <= 8, crops = ps.overflowX !== 'visible' && q.width <= r.width + 8 && q.height <= r.height + 8 && q.width > 40 && q.height > 40;
        if (!tight && !crops) break; if (crops && (q.width < box.width - 8 || q.height < box.height - 8)) box = q;
        if ((radius === '0px') && (ps.overflowX !== 'visible' || tight)) { const pr = rad(ps, q); if (pr !== '0px' && ps.overflowX !== 'visible') radius = pr; }
        if (!clip && ps.clipPath !== 'none') clip = norm(ps.clipPath, 160); if (!mask) mask = maskOf(ps); if (!filter && ps.filter !== 'none') filter = norm(ps.filter, 120); if (!shadow) shadow = sh(ps.boxShadow); if (!border) border = bord(ps);
        if (!tint && (blend || parseFloat(s.opacity) < 1) && col(ps.backgroundColor)) tint = col(ps.backgroundColor);
        for (const k of ['::before', '::after']) { const o = cs(p, k); if (o.content !== 'none' && o.content !== 'normal' && o.position === 'absolute') { const l = layer(o, 'pseudo'); if (l) overlays.push(l); } }
        for (const c of p.children) { if (c.contains(e) || overlays.length >= 3) continue; const o = cs(c), cr = c.getBoundingClientRect(); if (o.position !== 'absolute' || o.display === 'none') continue;
          const iw = Math.min(cr.right, r.right) - Math.max(cr.left, r.left), ih = Math.min(cr.bottom, r.bottom) - Math.max(cr.top, r.top); if (iw <= 0 || ih <= 0 || iw * ih < r.width * r.height * .3) continue; const l = layer(o, txt(c) ? 'text panel' : 'element'); if (l) overlays.push(l); } }
      const gray = /grayscale|saturate\(0/.test(filter || ''), duo = /url\(/.test(filter || '') ? 'svg filter' : ((gray || /luminosity|multiply|screen|color|overlay/.test(blend || '')) && (tint || overlays.some(o => o.blend || o.opacity)) ? 'tinted greyscale' : null);
      tag(e, 'i', i); res.push({ ref: mark ? i : null, width: Math.round(box.width), height: Math.round(box.height), radius, objectFit: s.objectFit !== 'fill' ? s.objectFit : null, objectPosition: s.objectPosition !== '50% 50%' ? s.objectPosition : null,
        filter, blend, clip, mask, shadow, border, opacity: parseFloat(s.opacity) < 1 ? parseFloat(s.opacity) : null, tint, overlays: overlays.length ? overlays : null, duotone: duo, treated: !!(filter || blend || clip || mask || overlays.length || tint) }); i++; }
    for (const e of all) { if (css.length >= 10) break; const s = cs(e); if (!/url\(/.test(s.backgroundImage) || /\.svg/i.test(s.backgroundImage)) continue; const r = e.getBoundingClientRect(); if (r.width < 400 || r.height < 220 || !vis(e) || /repeat(?!-)|^repeat/.test(s.backgroundRepeat.replace('no-repeat', ''))) continue;
      const overlays = []; const own = /gradient\(/.test(s.backgroundImage) ? norm(s.backgroundImage.replace(/url\([^)]*\)/g, 'url()'), 200) : null; if (own) overlays.push({ layer: 'same background', background: own });
      for (const k of ['::before', '::after']) { const o = cs(e, k); if (o.content !== 'none' && o.content !== 'normal' && o.position === 'absolute') { const l = layer(o, 'pseudo'); if (l) overlays.push(l); } }
      for (const c of e.children) { const o = cs(c); if (o.position === 'absolute' && !txt(c) && overlays.length < 3) { const l = layer(o, 'element'); if (l) overlays.push(l); } }
      css.push({ width: Math.round(r.width), height: Math.round(r.height), radius: rad(s, r), size: s.backgroundSize, position: s.backgroundPosition, blend: s.backgroundBlendMode !== 'normal' ? s.backgroundBlendMode : null, filter: s.filter !== 'none' ? norm(s.filter, 120) : null,
        clip: s.clipPath !== 'none' ? norm(s.clipPath, 160) : null, attachment: s.backgroundAttachment !== 'scroll' ? s.backgroundAttachment : null, overlays: overlays.length ? overlays : null, hasText: !!txt(e) }); }
    return { img: res, css }; });

  step('sections', () => {
    const bodyBg = col(cs(document.body).backgroundColor) || col(cs(document.documentElement).backgroundColor) || '#ffffff';
    const DH = Math.max(document.documentElement.scrollHeight, document.body.scrollHeight), bands = [], widths = {};
    const desc = (e, s) => { if (/^(IMG|VIDEO)$/.test(e.tagName)) return 'image'; const g = s.backgroundImage; if (g && g !== 'none') { const u = /url\(/.test(g), gr = /gradient\(/.test(g); return u && gr ? 'image + ' + norm(g.replace(/url\([^)]*\)/g, 'url()'), 170) : (u ? 'image' : norm(g, 200)); } const c = col(s.backgroundColor); return c && c.length === 7 ? c : null; };
    for (const e of all) { const r = e.getBoundingClientRect(); if (r.width < 600) continue; const s = cs(e); const mw = parseFloat(s.maxWidth); if (mw >= 480 && mw <= 1920 && /px/.test(s.maxWidth) && r.width < VW - 20) widths[Math.round(mw)] = (widths[Math.round(mw)] || 0) + 1;
      if (bands.length >= 160 || r.width < VW * .9 || r.height < 80 || s.position === 'fixed' || s.position === 'sticky' || s.display === 'none' || s.visibility === 'hidden' || parseFloat(s.opacity) < .05) continue;
      const media = /^(IMG|VIDEO)$/.test(e.tagName); if (media && r.height < 240) continue; if (!media && s.position === 'absolute' && !txt(e)) continue; const d = desc(e, s); if (!d) continue;
      bands.push({ e, top: r.top + scrollY, bottom: r.bottom + scrollY, bg: d }); }
    const ys = [...new Set([0, DH].concat(...bands.map(b => [Math.round(b.top), Math.round(b.bottom)])))].filter(y => y >= 0 && y <= DH).sort((a, b) => a - b), seq = [];
    for (let i = 0; i + 1 < ys.length; i++) { const y0 = ys[i], y1 = ys[i + 1]; if (y1 - y0 < 24) continue; const mid = (y0 + y1) / 2; let best = null;
      for (const b of bands) if (b.top <= mid && b.bottom >= mid && (!best || b.bottom - b.top < best.bottom - best.top)) best = b;
      const bg = best ? best.bg : bodyBg, last = seq[seq.length - 1]; if (last && last.background === bg) { last.height = y1 - last.top; continue; } seq.push({ top: y0, height: y1 - y0, background: bg }); }
    const content = Array.from(document.querySelectorAll('h1,h2,h3,h4,h5,p,li,img,button,figure,input,a')).filter(e => !skip(e)).slice(0, 1500).map(e => { const r = e.getBoundingClientRect(); if (r.width < 2 || r.height < 2 || r.left < 0 || r.right > VW + 1) return null; const s = cs(e); if (s.visibility === 'hidden' || s.position === 'fixed' || e.closest('header')) return null;
      return { t: r.top + scrollY, b: r.bottom + scrollY, l: r.left, r: r.right, color: /^(H[1-5]|P)$/.test(e.tagName) && txt(e, 4) ? col(s.color) : null, head: /^H/.test(e.tagName) }; }).filter(Boolean);
    for (const q of seq) { if (q.height < 160) continue; const inside = content.filter(c => c.t >= q.top - 2 && c.b <= q.top + q.height + 2); if (!inside.length) continue;
      const t = Math.min(...inside.map(c => c.t)), b = Math.max(...inside.map(c => c.b)), l = Math.min(...inside.map(c => c.l)), r = Math.max(...inside.map(c => c.r));
      q.pad = [Math.max(0, Math.round(t - q.top)), Math.max(0, Math.round(q.top + q.height - b))]; q.contentWidth = Math.round(r - l); q.contentLeft = Math.round(l);
      const hc = inside.find(c => c.head && c.color), pc = inside.find(c => !c.head && c.color); if (hc) q.heading = hc.color; if (pc) q.text = pc.color; }
    const hd = Array.from(document.querySelectorAll('header, [class*="header" i], nav')).find(e => { const r = e.getBoundingClientRect(); return r.width >= VW * .9 && r.height > 30 && r.height < 260 && vis(e); }); let header = null;
    if (hd) { const s = cs(hd), r = hd.getBoundingClientRect(); header = { background: bgOf(s) || 'transparent', height: Math.round(r.height), position: s.position, shadow: sh(s.boxShadow), border: bord(s), blur: /blur/.test(s.backdropFilter || '') ? s.backdropFilter : null }; }
    if (mark) { const h = Array.from(document.querySelectorAll('h1')).find(e => vis(e) && !skip(e)); let hero = null;
      if (h) for (let p = h; p && p !== document.body; p = p.parentElement) { const r = p.getBoundingClientRect(); if (r.width >= VW * .9 && r.height >= 300) { hero = p; break; } }
      if (!hero) { const b = bands.find(b => b.top < 400 && b.bottom - b.top >= 300); hero = b && b.e; } if (hero) tag(hero, 'comp', 'hero');
      const f = Array.from(document.querySelectorAll('footer, [role="contentinfo"]')).filter(vis).pop(); if (f) tag(f, 'comp', 'footer'); }
    return { sequence: seq.slice(0, 24), truncated: seq.length > 24 ? seq.length : null, body: bodyBg, pageHeight: DH, viewport: VW, header, maxWidths: widths }; });

  step('graphics', () => { const g = { clip: [], transform: [], circles: [], patterns: [], gradients: [], dividers: [], borders: [], shadows: [], textShadows: [] };
    const cap = (a, v, n) => { if (a.length < (n || 60)) a.push(v); };
    for (const e of all) { const s = cs(e), tg = e.tagName; if (s.display === 'none' || s.visibility === 'hidden') continue; const r = e.getBoundingClientRect(); if (r.width < 1 || r.height < 1) continue;
      const kindOf = () => e.matches(BTN) ? 'button' : (/^(IMG|VIDEO|PICTURE|FIGURE)$/.test(tg) ? 'image' : (/^(INPUT|SELECT|TEXTAREA)$/.test(tg) ? 'input' : (e.closest('header') && r.width >= VW * .9 ? 'header' : (r.width >= VW * .9 ? 'section' : (r.width >= 180 && r.height >= 110 ? 'card' : 'small')))));
      const bgi = s.backgroundImage, t = (bgi !== 'none' || s.clipPath !== 'none' || s.transform !== 'none' || r.height <= 8 || r.width <= 8 || parseFloat(s.borderTopLeftRadius) > 40) ? txt(e, 8) : null;
      if (s.clipPath !== 'none' && r.width >= 60 && r.height >= 40) cap(g.clip, { value: norm(s.clipPath, 170), on: kindOf(), width: Math.round(r.width), height: Math.round(r.height) });
      const mk = maskOf(s); if (mk && tg !== 'svg' && r.width >= 80 && r.height >= 60) cap(g.clip, { value: 'mask: ' + mk, on: kindOf(), width: Math.round(r.width), height: Math.round(r.height) });
      if (s.transform !== 'none' && tg !== 'svg' && Math.max(r.width, r.height) >= 60) { const m = s.transform.match(/matrix\(([^)]+)\)/); if (m) { const [a, b, c, d] = m[1].split(',').map(parseFloat), rot = Math.round(Math.atan2(b, a) * 180 / Math.PI), skew = Math.round(Math.atan2(a * c + b * d, a * a + b * b) * 180 / Math.PI);
        if (Math.abs(rot) >= 2 || Math.abs(skew) >= 2) cap(g.transform, { rotate: rot, skew, on: t ? 'text' : kindOf(), background: bgOf(s), width: Math.round(r.width), height: Math.round(r.height) }); } }
      const blur = (s.filter.match(/blur\(([^)]+)\)/) || [])[1];
      if (!t && !/^(IMG|VIDEO|svg|INPUT|IFRAME|CANVAS)$/.test(tg) && r.width >= 100 && r.height >= 100 && !e.querySelector('img, video, svg, input, iframe') && (bgOf(s) || bord(s))) { const rr = rad(s, r);
        if (((rr === 'circle' || rr === 'pill') && Math.abs(r.width - r.height) / r.width < .25) || blur) cap(g.circles, { shape: blur ? 'blurred blob' : 'circle', size: Math.round(Math.max(r.width, r.height)), background: bgOf(s), border: bord(s), blur: blur || null, opacity: parseFloat(s.opacity) < 1 ? parseFloat(s.opacity) : null, blend: s.mixBlendMode !== 'normal' ? s.mixBlendMode : null, position: s.position }, 20); }
      if (bgi !== 'none') { const rep = /repeating-(linear|radial|conic)-gradient/.test(bgi), tile = /url\(/.test(bgi) && /(^|[\s,])repeat/.test(s.backgroundRepeat) && !/cover|contain|100%/.test(s.backgroundSize);
        if ((rep || tile) && r.width >= 200 && r.height >= 80) { const u = (bgi.match(/url\(["']?([^"')]+)/) || [])[1]; cap(g.patterns, { kind: rep ? 'repeating gradient' : 'tiled image', value: rep ? norm(bgi, 200) : (u || '').split('/').pop().split('?')[0].slice(0, 60), url: tile && u && !/^data:/.test(u) ? new URL(u, location.href).href : null, size: s.backgroundSize, on: kindOf() }, 20); }
        else if (/gradient\(/.test(bgi) && r.width * r.height >= 5000) cap(g.gradients, { value: norm(bgi.replace(/url\([^)]*\)/g, 'url()'), 220), on: /text/.test(s.webkitBackgroundClip || '') ? 'text' : (s.position === 'absolute' && !t ? 'overlay' : kindOf()) }, 80); }
      if (tg === 'HR') { if (vis(e)) cap(g.dividers, { type: 'hr', thickness: num(Math.max(parseFloat(s.borderTopWidth) || 0, parseFloat(s.height) || 0)), color: col(parseFloat(s.borderTopWidth) > 0 ? s.borderTopColor : s.backgroundColor), style: parseFloat(s.borderTopWidth) > 0 ? s.borderTopStyle : 'solid', width: Math.round(r.width), full: r.width >= VW * .9 || null }); }
      else if (!t && e.children.length === 0 && !/^(IMG|INPUT|svg|IFRAME|CANVAS|VIDEO)$/.test(tg) && !/progress|slider|swiper|scroll|range|track|thumb|dot|bullet|pagination|burger|toggle|menu/i.test(cls(e) + ' ' + cls(e.parentElement || e)) && !e.closest('button, nav')) { const c = col(s.backgroundColor) || (/gradient\(/.test(bgi) ? 'gradient' : null);
        if (c && r.height <= 8 && r.width >= 24 && parseFloat(s.opacity) > .05) cap(g.dividers, { type: 'bar', thickness: num(r.height), color: c, width: Math.round(r.width), full: r.width >= VW * .9 || null, radius: parseFloat(s.borderTopLeftRadius) > 0 ? rad(s, r) : null });
        else if (c && r.width <= 8 && r.height >= 24 && parseFloat(s.opacity) > .05) cap(g.dividers, { type: 'vertical bar', thickness: num(r.width), color: c, width: Math.round(r.height) }); }
      const b = bord(s); if (b && typeof b === 'object' && !/^(INPUT|SELECT|TEXTAREA|TD|TH|TR|TABLE|BUTTON)$/.test(tg) && r.width >= 60 && vis(e)) for (const k of Object.keys(b)) { const w = parseFloat(b[k]); if (Object.keys(b).length > 2) break; if ((k === 'left' || k === 'right') && w < 2) continue;
        cap(g.borders, { side: k, line: b[k], on: /^H[1-6]$/.test(tg) ? 'heading' : (tg === 'BLOCKQUOTE' ? 'quote' : (tg === 'A' ? 'link' : (tg === 'LI' ? 'list item' : kindOf()))) }, 120); }
      if (s.boxShadow !== 'none' && r.width >= 60 && vis(e)) cap(g.shadows, { value: sh(s.boxShadow), on: kindOf() }, 120);
      const ds = (s.filter.match(/drop-shadow\((?:[^()]|\([^()]*\))*\)/) || [])[0]; if (ds && r.width >= 40) cap(g.shadows, { value: norm(ds, 120), on: kindOf() }, 120);
      if (s.textShadow !== 'none' && e.children.length === 0 && txt(e, 4)) cap(g.textShadows, { value: norm(s.textShadow, 100) }, 30); }
    return g; });

  step('lists', () => { const res = [];
    for (const e of document.querySelectorAll('main ul > li, section ul > li, article ul > li, main ol > li, [class*="content" i] ul > li')) { if (res.length >= 40) break;
      if (skip(e) || !vis(e) || e.closest('nav, header, footer, [class*="menu" i], [class*="nav" i], [class*="slider" i], [class*="swiper" i], [class*="carousel" i], [class*="tab" i]') || e.querySelector('h2, h3, img, picture, ' + BTN)) continue; if (txt(e, 12).length < 3) continue;
      const s = cs(e), m = cs(e, '::marker'), p = pseudo(e)[0]; let marker;
      if (s.listStyleImage !== 'none') marker = { type: 'image' }; else if (s.listStyleType !== 'none' && s.display === 'list-item') marker = { type: s.listStyleType, color: col(m.color) };
      else if (p && mark2(p)) marker = mark2(p); else { const ic = e.querySelector(':scope > svg, :scope > img, :scope > i, :scope > span > svg, :scope > div > svg'); marker = ic ? { type: 'icon', width: num(ic.getBoundingClientRect().width), color: col(cs(ic).color) } : { type: 'none' }; }
      res.push({ ordered: e.parentElement.tagName === 'OL' || null, marker, color: col(s.color), fontSize: num(s.fontSize), gap: num(s.marginBottom) || num(cs(e.parentElement).rowGap) || null, indent: num(cs(e.parentElement).paddingLeft) + num(s.paddingLeft) }); }
    return res; });

  step('links', () => { const res = [], nav = [];
    for (const e of document.querySelectorAll('main p a, section p a, article p a, main li a, p a')) { if (res.length >= 40) break; if (skip(e) || !vis(e) || e.matches(BTN) || e.closest('nav, header, footer') || !txt(e, 4)) continue; const s = cs(e), ps = cs(e.parentElement), ul = /underline/.test(s.textDecorationLine), bb = parseFloat(s.borderBottomWidth) > 0;
      res.push({ text: txt(e, 30), color: col(s.color), ownColor: col(s.color) !== col(ps.color), underline: ul ? [s.textDecorationStyle, s.textDecorationThickness, col(s.textDecorationColor) !== col(s.color) ? col(s.textDecorationColor) : ''].join(' ').trim() : null,
        underlineOffset: ul && s.textUnderlineOffset !== 'auto' ? s.textUnderlineOffset : null, borderBottom: bb ? num(s.borderBottomWidth) + 'px ' + s.borderBottomStyle + ' ' + col(s.borderBottomColor) : null,
        background: /gradient\(/.test(s.backgroundImage) ? norm(s.backgroundImage, 120) : null, fontWeight: s.fontWeight !== ps.fontWeight ? s.fontWeight : null }); }
    for (const e of document.querySelectorAll('header nav a, nav a, header a')) { if (nav.length >= 8) break; if (skip(e) || !vis(e) || e.matches(BTN) || !txt(e, 4) || e.querySelector('img, svg')) continue; const s = cs(e);
      nav.push({ text: txt(e, 24), color: col(s.color), fontWeight: s.fontWeight, fontSize: num(s.fontSize), textTransform: tcase(s), letterSpacing: track(s), family: fam(s), underline: /underline/.test(s.textDecorationLine) || null }); }
    return { text: res, nav }; });

  step('arrowGlyphs', () => { const g = {}; const add = (ch, k) => { g[ch] = g[ch] || { links: 0, text: 0, pseudo: 0 }; g[ch][k]++; };
    for (const ch of ((document.body.innerText || '').match(ARW) || []).slice(0, 400)) add(ch, 'text');
    let n = 0; for (const e of document.querySelectorAll('a, button, [role="button"], summary')) { if (++n > 1500) break; if (skip(e)) continue; const t = e.innerText || ''; if (t.length > 120) continue;
      for (const ch of (t.match(ARW) || [])) add(ch, 'links'); if (/\S\s>$/.test(t.trim())) add('>', 'links');
      for (const q of pseudo(e).concat(...Array.from(e.children).slice(0, 3).map(pseudo))) for (const ch of (q.text.match(ARW) || [])) add(ch, 'pseudo'); }
    return g; });

  step('fontUse', () => { const use = {}; let n = 0;
    for (const e of all) { if (++n > 4000) break; const own = Array.from(e.childNodes).filter(x => x.nodeType === 3).map(x => x.textContent.trim()).join(' '); if (own.length < 2) continue; const s = cs(e); if (s.display === 'none' || s.visibility === 'hidden') continue;
      const f = fam(s), u = use[f] = use[f] || { chars: 0, size: 0, mono: /monospace/.test(s.fontFamily), stack: s.fontFamily.slice(0, 160), code: 0 }; u.chars += own.length; u.size += own.length * parseFloat(s.fontSize); if (e.closest('code, pre, kbd')) u.code += own.length; }
    for (const f of Object.keys(use)) use[f].size = Math.round(use[f].size / use[f].chars);
    return use; });

  // inline svgs as standalone files: computed paint is written onto the shapes, one-colour icons keep currentColor
  const standalone = svg => { if (svg.querySelector('script, foreignObject, image')) return null;
    const r = svg.getBoundingClientRect(), clone = svg.cloneNode(true), src = [svg].concat(Array.from(svg.querySelectorAll('*'))), dst = [clone].concat(Array.from(clone.querySelectorAll('*')));
    const keepClass = !!svg.querySelector('style'), cols = new Set(), drop = [], sws = []; let nStroke = 0, nFill = 0, n = 0; const oc = rgba(cs(svg).color), own = oc ? hex(oc) : null;
    src.forEach((o, i) => { const d = dst[i], tg = o.tagName.toLowerCase(); if (!keepClass) d.removeAttribute('class');
      for (const a of Array.from(d.attributes)) if (/^(data-|aria-|focusable$|role$|tabindex$)/.test(a.name)) d.removeAttribute(a.name);
      if (!/^(path|circle|rect|line|polyline|polygon|ellipse|use|text|tspan)$/.test(tg) || o.parentElement.closest('defs, clipPath, mask, pattern, symbol, marker')) return;
      const s = cs(o); if (s.display === 'none' || s.visibility === 'hidden') { drop.push(d); return; } n++;
      const sw = parseFloat(s.strokeWidth) || 0;
      for (const k of ['fill', 'stroke']) { const v = s[k] || 'none'; if (d.style) { d.style.removeProperty(k); d.style.removeProperty(k + '-opacity'); }
        if (/^url/.test(v)) { const id = (v.match(/#([^"')]+)/) || [])[1]; d.setAttribute(k, id ? 'url(#' + id + ')' : 'none'); if (k === 'fill') nFill++; else nStroke++; continue; }
        const p = rgba(v), op = parseFloat(k === 'fill' ? s.fillOpacity : s.strokeOpacity); if (!p || p[3] < .03 || op < .03 || (k === 'stroke' && sw <= 0)) { d.setAttribute(k, 'none'); continue; }
        d.setAttribute(k, hex(p)); const al = p[3] * (isNaN(op) ? 1 : op); if (al < .97) d.setAttribute(k + '-opacity', String(Math.round(al * 100) / 100)); else d.removeAttribute(k + '-opacity');
        if (k === 'fill' && tg === 'line') continue; cols.add(hex(p)); if (k === 'fill') nFill++; else { nStroke++; sws.push(sw); } }
      if (sw > 0 && s.stroke !== 'none') { d.setAttribute('stroke-width', String(Math.round(sw * 100) / 100)); if (s.strokeLinecap !== 'butt') d.setAttribute('stroke-linecap', s.strokeLinecap); if (s.strokeLinejoin !== 'miter') d.setAttribute('stroke-linejoin', s.strokeLinejoin);
        if (d.style) for (const k of ['stroke-width', 'stroke-linecap', 'stroke-linejoin']) d.style.removeProperty(k); }
      if (s.fillRule === 'evenodd') d.setAttribute('fill-rule', 'evenodd'); if (parseFloat(s.opacity) < 1) d.setAttribute('opacity', s.opacity);
      if (d.getAttribute('style') === '') d.removeAttribute('style'); });
    drop.forEach(d => d.remove());
    const mono = cols.size === 1 ? Array.from(cols)[0] : null;
    for (const d of dst) for (const k of ['fill', 'stroke']) { const v = d.getAttribute(k); if (v && (v === mono || (!mono && v === own))) d.setAttribute(k, 'currentColor'); }
    for (const u of Array.from(clone.querySelectorAll('use'))) { const h = u.getAttribute('href') || u.getAttribute('xlink:href') || ''; if (h[0] !== '#') return null; const id = h.slice(1);
      if (Array.from(clone.querySelectorAll('[id]')).some(x => x.id === id)) continue; const t = document.getElementById(id); if (!t || t.querySelector('script, foreignObject, image')) return null;
      const g = document.createElementNS('http://www.w3.org/2000/svg', 'g'); for (const k of ['fill', 'stroke', 'stroke-width', 'stroke-linecap', 'stroke-linejoin', 'fill-opacity', 'stroke-opacity', 'opacity', 'transform']) if (u.getAttribute(k)) g.setAttribute(k, u.getAttribute(k));
      const x = parseFloat(u.getAttribute('x')) || 0, y = parseFloat(u.getAttribute('y')) || 0; if (x || y) g.setAttribute('transform', ((g.getAttribute('transform') || '') + ' translate(' + x + ' ' + y + ')').trim());
      if (/^(symbol|svg)$/i.test(t.tagName)) { for (const c of Array.from(t.childNodes)) g.appendChild(c.cloneNode(true)); if (t.getAttribute('viewBox') && (!clone.getAttribute('viewBox') || clone.children.length === 1)) clone.setAttribute('viewBox', t.getAttribute('viewBox')); } else g.appendChild(t.cloneNode(true));
      for (const c of g.querySelectorAll('[class]')) c.removeAttribute('class'); u.replaceWith(g); }
    let vb = clone.getAttribute('viewBox'); if (!vb) { const w = parseFloat(svg.getAttribute('width')), h = parseFloat(svg.getAttribute('height')); vb = '0 0 ' + (w || num(r.width)) + ' ' + (h || num(r.height)); clone.setAttribute('viewBox', vb); }
    clone.removeAttribute('style'); clone.removeAttribute('id'); const key = vb + '|' + clone.innerHTML.replace(/\s+/g, ' ');
    clone.setAttribute('width', String(Math.round(r.width))); clone.setAttribute('height', String(Math.round(r.height)));
    let markup = new XMLSerializer().serializeToString(clone); if (markup.indexOf('xmlns="http://www.w3.org/2000/svg"') < 0) markup = markup.replace('<svg', '<svg xmlns="http://www.w3.org/2000/svg"');
    sws.sort((a, b) => a - b); return { markup, key, nStroke, nFill, n: n, sw: sws.length ? sws[Math.floor(sws.length / 2)] : null, grid: parseFloat(vb.split(/[ ,]+/)[2]) || null, mono: !!mono }; };

  // an arrow or chevron by its geometry: one symmetric two-segment head, plus at most two straight shafts
  const arrowShape = svg => { const subs = []; const dist = (a, b) => Math.hypot(a[0] - b[0], a[1] - b[1]);
    for (const e of svg.querySelectorAll('path, line, polyline, polygon, circle, rect, ellipse, text, use')) { const tg = e.tagName.toLowerCase(); if (e.closest('defs, clipPath, mask')) continue; const s = cs(e); if (s.display === 'none') continue;
      if (tg === 'line') subs.push([[+e.getAttribute('x1') || 0, +e.getAttribute('y1') || 0], [+e.getAttribute('x2') || 0, +e.getAttribute('y2') || 0]]);
      else if (tg === 'polyline') { const n = (e.getAttribute('points') || '').trim().split(/[\s,]+/).map(parseFloat), p = []; for (let i = 0; i + 1 < n.length; i += 2) p.push([n[i], n[i + 1]]); subs.push(p); }
      else if (tg === 'path') { const d = e.getAttribute('d') || ''; if (/[csqtaz]/i.test(d) || s.fill !== 'none' && (s.stroke === 'none' || !parseFloat(s.strokeWidth))) return null; let x = 0, y = 0, cur = null;
        for (const m of d.matchAll(/([MLHVmlhv])([^MLHVmlhv]*)/g)) { const c = m[1], n = (m[2].match(/-?(?:\d*\.\d+|\d+\.?)(?:e-?\d+)?/gi) || []).map(parseFloat), step = /[hv]/i.test(c) ? 1 : 2;
          for (let i = 0; i + step <= n.length; i += step) { const rel = c === c.toLowerCase(), k = c.toLowerCase(); if (k === 'h') x = rel ? x + n[i] : n[i]; else if (k === 'v') y = rel ? y + n[i] : n[i]; else { x = rel ? x + n[i] : n[i]; y = rel ? y + n[i + 1] : n[i + 1]; }
            if (k === 'm' && i === 0) { cur = []; subs.push(cur); } if (!cur) return null; cur.push([x, y]); } } }
      else return null; }
    const parts = subs.filter(p => p.length > 1); if (!parts.length || parts.length > 3) return null; const heads = parts.filter(p => p.length === 3), rest = parts.filter(p => p.length !== 3);
    if (heads.length !== 1 || rest.some(p => p.length !== 2)) return null; const [a, b, c] = heads[0], l1 = dist(a, b), l2 = dist(b, c); if (!l1 || !l2 || Math.abs(l1 - l2) / Math.max(l1, l2) > .12) return null;
    const ang = Math.acos(Math.max(-1, Math.min(1, ((a[0] - b[0]) * (c[0] - b[0]) + (a[1] - b[1]) * (c[1] - b[1])) / (l1 * l2)))) * 180 / Math.PI; if (ang < 35 || ang > 145) return null;
    return rest.length ? 'arrow' : 'chevron'; };

  step('icons', () => { const SOCIAL = /facebook|twitter|linkedin|instagram|youtube|tiktok|xing|github|mastodon|whatsapp|pinterest|vimeo|bluesky|threads|telegram|spotify|soundcloud|flickr|snapchat|reddit|discord|(^|[\/.])x\.com|social/i, LOGO = /logo|brand|wordmark|signet/i, STEP = /next|prev|weiter|zur(ü|ue)ck|forward|\bback\b|slide/i;
    const list = [], shapes = [], imgs = [], fonts = {}, els = []; let unresolved = 0, social = 0;
    const hint = (e, a) => { const u = e.querySelector && e.querySelector('use'), h = u && (u.getAttribute('href') || u.getAttribute('xlink:href') || '').split('#')[1], t = e.querySelector && e.querySelector('title'), c = (cls(e) + ' ' + (e.parentElement ? cls(e.parentElement) : '')).match(/(?:icon|ico|fa|bi|lucide|feather|tabler|svg)[-_]{1,2}([a-z][a-z0-9-]{1,30})/i), f = (e.getAttribute('src') || '').split('/').pop().split('?')[0].replace(/\.svg$/i, '');
      const short = v => v && v.trim().length <= 18 && v.trim().split(/\s+/).length <= 2 ? v : '';
      return (h || (c && c[1]) || f || short(e.getAttribute('aria-label')) || short(t && t.textContent) || e.getAttribute('data-icon') || short(a && a.getAttribute('aria-label')) || '').toLowerCase().trim().slice(0, 30); };
    const context = e => { const a = e.closest('a, button, [role="button"]'); return { a, label: a ? [a.getAttribute('href'), a.getAttribute('aria-label'), a.getAttribute('title'), cls(a)].filter(Boolean).join(' ') : '' }; };
    for (const e of document.querySelectorAll('svg')) { if ((e.parentElement && e.parentElement.closest('svg')) || skip(e)) continue; const r = e.getBoundingClientRect(); if (r.width < 1 || r.height < 1) continue; const s = cs(e); if (s.display === 'none' || s.visibility === 'hidden' || parseFloat(s.opacity) < .05) continue;
      const nm = names(e), { a, label } = context(e), big = Math.max(r.width, r.height), small = Math.min(r.width, r.height); if (e.closest('[data-vs-logo]') || LOGO.test(nm + ' ' + (a ? cls(a) : ''))) continue;
      if (big >= 12 && big <= 64 && small >= 8) { if (SOCIAL.test(nm + ' ' + label)) { social++; continue; } if (list.length >= 90) continue; const m = standalone(e); if (!m) { unresolved++; continue; } if (m.markup.length > 14000 || !m.n && !/<(path|g|circle|rect|line|poly)/.test(m.markup)) continue;
        const simple = (m.markup.match(/<(path|line|polyline|polygon)\b/g) || []).length <= 3 && !/<(circle|rect|ellipse|text)\b/.test(m.markup) && m.markup.length < 900, ar = a ? a.getBoundingClientRect() : null;
        let geo = null; try { geo = arrowShape(e); } catch (x) {}
        const arrow = geo ? 'shape' : (NAMED.test(nm + ' ' + label) ? 'name' : (a && !txt(a) && STEP.test(label + ' ' + nm) ? 'name' : (a && txt(a) && simple && r.left + r.width / 2 > ar.left + ar.width * .6 ? 'position' : null)));
        els.push(e); list.push(Object.assign(m, { width: Math.round(r.width), height: Math.round(r.height), arrow, hint: geo || hint(e, a), inButton: !!a, color: col(s.color), where: where(e), rotated: s.transform !== 'none' && /matrix\((?!1, 0, 0, 1)/.test(s.transform) ? s.transform : null })); }
      else if (big >= 160 && !a && shapes.length < 8 && !e.querySelector('text, image, foreignObject')) { const deco = e.getAttribute('aria-hidden') === 'true' || e.getAttribute('role') === 'presentation' || /shape|blob|deco|pattern|wave|divider|ornament|graphic|backdrop|background|curve/i.test(nm);
        const abs = /absolute|fixed/.test(s.position) || (e.parentElement && /absolute|fixed/.test(cs(e.parentElement).position)); if (!deco || !abs || e.querySelectorAll('path, circle, rect, polygon, ellipse, line, polyline').length > 30) continue;
        const m = standalone(e); if (m && m.markup.length <= 30000) shapes.push(Object.assign(m, { width: Math.round(r.width), height: Math.round(r.height), hint: hint(e, null), color: col(s.color) })); } }
    for (const e of document.querySelectorAll('img')) { if (imgs.length >= 30) break; const src = e.currentSrc || e.src || ''; if (!/\.svg(\?|$)/i.test(src) || /^data:/.test(src) || skip(e) || !vis(e) || e.closest('[data-vs-logo]') || e.hasAttribute('data-vs-logo')) continue; const r = e.getBoundingClientRect(), big = Math.max(r.width, r.height);
      if (big < 12 || big > 64 || Math.min(r.width, r.height) < 8) continue; const nm = names(e) + ' ' + (e.alt || ''), { a, label } = context(e); if (LOGO.test(nm + ' ' + (a ? cls(a) : ''))) continue; if (SOCIAL.test(nm + ' ' + label)) { social++; continue; }
      els.push(e); imgs.push({ src, width: Math.round(r.width), height: Math.round(r.height), arrow: NAMED.test(nm + ' ' + label) ? 'name' : null, hint: hint(e, a), where: where(e) }); }
    let k = 0; for (const e of document.querySelectorAll('i, span[class*="icon" i], span[class*="fa-" i], em[class*="icon" i]')) { if (++k > 400) break; const b = cs(e, '::before'); if (b.content && PUA.test(b.content)) { const f = fam(b); fonts[f] = (fonts[f] || 0) + 1; } }
    if (mark && els.length >= 3) { const rows = new Map(); for (const e of els) { if (e.closest('header, nav, footer')) continue; for (let p = e.parentElement, d = 0; p && d < 6; p = p.parentElement, d++) { const r = p.getBoundingClientRect(); if (r.width >= 420) { if (r.height <= 620 && !Array.from(p.querySelectorAll('img')).some(x => x.getBoundingClientRect().width > 160)) rows.set(p, (rows.get(p) || 0) + 1); break; } } }
      const best = Array.from(rows.entries()).filter(x => x[1] >= 3).sort((x, y) => y[1] - x[1])[0]; if (best) tag(best[0], 'comp', 'icon_row'); }
    return { list, shapes, imgs, fonts, unresolved, social }; });
  return out;
}
"""

# The icons of a site that keeps them in an svg sprite: symbols already in the page and the sprite files it points
# to (<use href="sprite.svg#id">, data-svg-href="…" loaded by script). Every symbol is drawn once inside the page so
# that the site's own css colours it, and comes back with those colours written into the file (currentColor where
# it takes the text colour).
SPRITE_JS = r"""
async (max) => {
  const out = { sources: [], symbols: [] }, urls = new Set(), abs = v => { try { return new URL(v, location.href).href; } catch (e) { return null; } };
  for (const u of document.querySelectorAll('use')) { const f = (u.getAttribute('href') || u.getAttribute('xlink:href') || '').split('#')[0]; if (f && abs(f)) urls.add(abs(f)); }
  for (const e of document.querySelectorAll('[data-svg-href],[data-sprite],[data-svg-sprite],[data-svg-src],[data-src]')) for (const a of ['data-svg-href', 'data-sprite', 'data-svg-sprite', 'data-svg-src', 'data-src']) {
    const v = e.getAttribute(a); if (v && /\.(svg|html?)(\?|#|$)/i.test(v) && (a !== 'data-src' || /sprite|icons?\b/i.test(v)) && abs(v)) urls.add(abs(v)); }
  const host = document.createElement('div'); host.style.cssText = 'position:absolute;left:-10000px;top:0;width:10px;height:10px;overflow:hidden'; document.body.appendChild(host);
  for (const u of Array.from(urls).slice(0, 4)) { try { const t = await (await fetch(u, { credentials: 'same-origin' })).text(); if (t.length < 4e6 && t.includes('<symbol')) { const d = document.createElement('div'); d.innerHTML = t.replace(/<script[\s\S]*?<\/script>/gi, ''); host.appendChild(d); out.sources.push(u); } } catch (e) {} }
  const seen = new Set(), SH = 'path,circle,rect,ellipse,polygon,polyline,line';
  for (const s of document.querySelectorAll('symbol[id]')) {
    if (out.symbols.length >= max) break; const vb = s.getAttribute('viewBox'); if (!vb || seen.has(s.id)) continue; seen.add(s.id);
    const svg = document.createElementNS('http://www.w3.org/2000/svg', 'svg'); svg.setAttribute('viewBox', vb); svg.setAttribute('style', 'width:48px;height:48px;color:rgb(1, 2, 3)');
    for (const c of s.childNodes) svg.appendChild(c.cloneNode(true)); host.appendChild(svg);
    const shapes = svg.querySelectorAll(SH); if (!shapes.length || shapes.length > 150 || svg.querySelector('image, foreignObject, text')) { svg.remove(); continue; }
    const colours = new Set(), paint = v => (!v || v === 'none') ? 'none' : (v === 'rgb(1, 2, 3)' || v === 'rgb(0, 0, 0)') ? 'currentColor' : (v.startsWith('url(') ? null : v);
    let ok = true;
    for (const e of svg.querySelectorAll(SH)) { const cs = getComputedStyle(e);
      for (const p of ['fill', 'stroke']) { const v = paint(cs.getPropertyValue(p)); if (v === null) { ok = false; break; } e.setAttribute(p, v); if (v !== 'none' && v !== 'currentColor') colours.add(v); }
      if (cs.stroke !== 'none') e.setAttribute('stroke-width', cs.strokeWidth); if (cs.opacity !== '1') e.setAttribute('opacity', cs.opacity); if (cs.fillRule === 'evenodd') e.setAttribute('fill-rule', 'evenodd'); }
    for (const e of svg.querySelectorAll('*')) { e.removeAttribute('class'); e.removeAttribute('style'); } for (const e of svg.querySelectorAll('style, title, desc, script')) e.remove();
    svg.removeAttribute('style'); svg.setAttribute('xmlns', 'http://www.w3.org/2000/svg');
    if (ok) { const markup = svg.outerHTML; if (markup.length <= 20000) out.symbols.push({ id: s.id, markup, mono: !colours.size, colours: Array.from(colours).slice(0, 4), n: shapes.length }); }
    svg.remove(); }
  host.remove(); return out; }
"""

# Scrolls the union of some elements into view and returns its viewport rectangle (plus a margin) to clip a screenshot to.
SHOOT_JS = r"""
async ([sels, m]) => { const els = sels.map(s => document.querySelector(s)).filter(Boolean); if (!els.length) return null;
  const u = () => { let a = [1e9, 1e9, -1e9, -1e9]; for (const e of els) { const r = e.getBoundingClientRect(); a = [Math.min(a[0], r.left), Math.min(a[1], r.top), Math.max(a[2], r.right), Math.max(a[3], r.bottom)]; } return a; };
  let b = u(); const h = b[3] - b[1] + 2 * m, W = document.documentElement.clientWidth;
  scrollTo({ top: Math.max(0, scrollY + b[1] - m - Math.max(0, (innerHeight - h) / 2)), behavior: 'instant' }); await new Promise(r => setTimeout(r, 450)); b = u();
  const x = Math.max(0, b[0] - m), y = Math.max(0, b[1] - m), x2 = Math.min(W, b[2] + m), y2 = Math.min(innerHeight, b[3] + m);
  return (x2 - x < 8 || y2 - y < 8) ? null : { x, y, width: x2 - x, height: y2 - y }; }
"""

# Run inside the contact sheet page: drops tiles whose svg does not render on its own and measures how much
# of its box each icon covers with ink (line icons cover little, filled ones a lot).
SHEET_JS = r"""
async () => { const res = {};
  await Promise.all(Array.from(document.images).map(i => i.decode().catch(() => 0)));
  for (const im of Array.from(document.images)) { const f = im.getAttribute('data-f'); if (!im.naturalWidth) { res[f] = { ok: false }; im.closest('.t').remove(); continue; }
    let cov = null; try { const c = document.createElement('canvas'), n = 64; c.width = c.height = n; const x = c.getContext('2d'), k = Math.min(n / im.naturalWidth, n / im.naturalHeight), w = im.naturalWidth * k, h = im.naturalHeight * k;
      x.drawImage(im, 0, 0, w, h); const d = x.getImageData(0, 0, n, n).data; let ink = 0; for (let i = 3; i < d.length; i += 4) if (d[i] > 60) ink++; cov = Math.round(ink / Math.max(1, w * h) * 100) / 100; } catch (e) {}
    res[f] = { ok: true, cov }; }
  return res; }
"""

# ---------------------------------------------------------------- colour helpers

def _rgb(h):
    h = h.lstrip("#"); return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))

def _hex(rgb):
    return "#" + "".join(f"{max(0, min(255, round(c))):02X}" for c in rgb)

def mix(a, b, t):
    """Blend colour a towards b by t (0..1)."""
    return _hex(tuple(x + (y - x) * t for x, y in zip(_rgb(a), _rgb(b))))

def saturation(h):
    r, g, b = (c / 255 for c in _rgb(h)); return colorsys.rgb_to_hls(r, g, b)[2]

def distance(a, b):
    return sum((x - y) ** 2 for x, y in zip(_rgb(a), _rgb(b))) ** .5

def _top(weights, n=8):
    return [c for c, _ in sorted(weights.items(), key=lambda kv: -kv[1])[:n]]

def choose_colors(pages):
    """Pick the palette from the measured pages. Returns (colors, notes)."""
    bg, text, accent_votes = {}, {}, {}
    for p in pages:
        for c, w in p["bg"].items(): bg[c] = bg.get(c, 0) + w
        for c, w in p["text"].items(): text[c] = text.get(c, 0) + w
        for b in p["styles"]["button"]:
            for key, w in (("background", 6), ("borderColor", 2), ("color", 1)):
                c = b.get(key)
                if c and saturation(c) > .25 and .04 < B.luminance(c) < .9:
                    accent_votes[c] = accent_votes.get(c, 0) + w
        for a in p["styles"]["a"] + p["styles"]["nav"]:
            c = a.get("color")
            if c and saturation(c) > .35 and .04 < B.luminance(c) < .9:
                accent_votes[c] = accent_votes.get(c, 0) + 1
        for name, c in (p.get("palette") or {}).items():      # colours the site declares as its palette
            if saturation(c) > .35 and .04 < B.luminance(c) < .9:
                boost = 4 if re.search(r"primary|brand|accent|main|key", name, re.I) else 1.5
                accent_votes[c] = accent_votes.get(c, 0) + boost
        tc = (p["copy"].get("themeColor") or "").strip()
        if re.fullmatch(r"#[0-9a-fA-F]{6}", tc) and saturation(tc) > .25:
            accent_votes[tc.lower()] = accent_votes.get(tc.lower(), 0) + 3
    notes = []
    paper = _top(bg, 1)[0] if bg else "#ffffff"
    on_paper = sorted(text.items(), key=lambda kv: -kv[1] * (1 if B.contrast(kv[0], paper) >= 4.5 else .05))
    ink = on_paper[0][0] if on_paper else B.readable_on(paper)
    if B.contrast(ink, paper) < 7:
        ink = mix(ink, B.readable_on(paper, "#FFFFFF", "#111111"), .5); notes.append("ink was darkened/lightened for contrast")
    if not accent_votes:     # no coloured buttons or links: take the most saturated colour that covers real area
        total = sum(bg.values()) or 1
        for c, w in list(bg.items()) + list(text.items()):
            if saturation(c) > .35 and .04 < B.luminance(c) < .9:
                accent_votes[c] = accent_votes.get(c, 0) + w / total
        notes.append("accent guessed from coloured areas, no coloured buttons or links found")
    accent = _top(accent_votes, 1)[0] if accent_votes else ink
    if not accent_votes: notes.append("no accent colour found, ink is used; pick one by hand")
    dark_bgs = [c for c in _top(bg, 12) if B.luminance(c) < .12 and distance(c, paper) > 60]
    light_paper = B.luminance(paper) > .5
    if light_paper:
        deep = dark_bgs[0] if dark_bgs else (ink if B.luminance(ink) < .12 else mix(ink, "#000000", .4))
    else:               # dark site: the contrast surface is a lighter or accent panel, keep it dark enough for light text
        lighter = [c for c in _top(bg, 12) if distance(c, paper) > 25 and B.luminance(c) < .2]
        deep = lighter[0] if lighter else mix(paper, "#FFFFFF", .08)
        notes.append("dark site: paper is dark, check soft/line/ghost by eye")
    muted_c = [c for c, _ in on_paper[1:8] if 3 <= B.contrast(c, paper) < 9 and saturation(c) < .35 and distance(c, ink) > 40]
    colors = {
        "accent": accent.upper(), "on_accent": B.readable_on(accent),
        "ink": ink.upper(), "deep": deep.upper(), "on_deep": B.readable_on(deep),
        "muted": (muted_c[0] if muted_c else mix(ink, paper, .42)).upper(),
        "line": mix(ink, paper, .76), "soft": mix(ink, paper, .94), "ghost": mix(ink, paper, .89),
        "paper": paper.upper(),
    }
    if B.contrast(colors["accent"], colors["paper"]) < 3 and saturation(colors["deep"]) > .25 and B.contrast(colors["deep"], colors["paper"]) >= 4.5:
        colors["accent_text"] = colors["deep"]; notes.append("the accent is too light for text on paper, accent words use the deep colour (colors.accent_text)")
    return colors, notes, {"background": _top(bg), "text": _top(text), "accent_candidates": _top(accent_votes)}

# ---------------------------------------------------------------- fonts

_GENERIC = {"serif", "sans-serif", "monospace", "system-ui", "ui-sans-serif", "ui-serif", "ui-monospace", "cursive", "fantasy",
            "-apple-system", "blinkmacsystemfont", "inherit", "initial", "emoji", "math"}

def first_family(stack):
    for f in (stack or "").split(","):
        f = f.strip().strip("\"'")
        if f and f.lower() not in _GENERIC:
            return f
    return None

def fallback_for(stack):
    s = (stack or "").lower()
    if "monospace" in s and "sans" not in s: return "Menlo, Consolas, monospace"
    if re.search(r"(?<!sans-)serif", s): return "Georgia, 'Times New Roman', serif"
    return "Arial, Helvetica, sans-serif"

def parse_font_faces(css, base):
    """@font-face blocks -> [{family, weight, style, urls}]"""
    out = []
    for block in re.findall(r"@font-face\s*\{([^}]*)\}", css or ""):
        fam = re.search(r"font-family\s*:\s*([^;]+)", block)
        if not fam: continue
        weight = re.search(r"font-weight\s*:\s*([^;]+)", block); style = re.search(r"font-style\s*:\s*([^;]+)", block)
        urls = [urljoin(base, u.strip("\"' ")) for u in re.findall(r"url\(([^)]+)\)", block) if not u.strip("\"' ").startswith("data:")]
        out.append({"family": fam.group(1).strip().strip("\"'"), "weight": (weight.group(1).strip() if weight else "400"),
                    "style": (style.group(1).strip() if style else "normal"), "urls": urls})
    return out

def _weight_num(w):
    w = str(w).strip().lower()
    w = {"normal": "400", "bold": "700"}.get(w, w)
    nums = [int(x) for x in re.findall(r"\d+", w)]
    return nums if nums else [400]

# ---------------------------------------------------------------- fonts by licence situation

def slugify(s):
    return re.sub(r"[^a-z0-9]+", "-", s.lower()).strip("-") or "brand"

def _fkey(name):
    return re.sub(r"[^a-z0-9]", "", (name or "").lower())

# Families published under an open licence (OFL, Apache, Ubuntu Font Licence): safe to embed even when self-hosted.
_OPEN_FAMILIES = {_fkey(n) for n in """Inter;Lato;Poppins;Montserrat;Raleway;Oswald;Mulish;Manrope;Urbanist;Lexend;Geist;Geist Mono;Sora;Karla;Rubik;Outfit;Figtree;
    Work Sans;Nunito;Nunito Sans;Quicksand;Ubuntu;Ubuntu Mono;Cabin;Bitter;Lora;Crimson Text;Crimson Pro;EB Garamond;Cormorant;Cormorant Garamond;Josefin Sans;Josefin Slab;
    Overpass;Titillium Web;Hind;Heebo;Assistant;Dosis;Exo;Exo 2;Kanit;Prompt;Sarabun;Mukta;Catamaran;Arimo;Tinos;Cousine;Zilla Slab;Bebas Neue;Anton;Abril Fatface;Fraunces;
    Syne;Epilogue;Albert Sans;Onest;Instrument Sans;Instrument Serif;Bricolage Grotesque;Hanken Grotesk;Schibsted Grotesk;Commissioner;Jost;Chivo;Spectral;Alegreya;
    Alegreya Sans;Vollkorn;Gelasio;Newsreader;Literata;Courier Prime;Inconsolata;Hack;Readex Pro;Unbounded;Familjen Grotesk;Darker Grotesque;Maven Pro;Asap;Signika;
    Varela Round;Questrial;Comfortaa;Yantramanav;Archivo;Archivo Narrow;Archivo Black;Barlow;Barlow Condensed;Barlow Semi Condensed;Space Grotesk;Space Mono;
    Plus Jakarta Sans;Be Vietnam Pro;Public Sans;Encode Sans;Atkinson Hyperlegible;Libre Baskerville;Libre Franklin;Libre Caslon Text;Red Hat Display;Red Hat Text;
    Red Hat Mono;JetBrains Mono;Fira Code;Fira Mono;Fira Sans;Fira Sans Condensed;Cascadia Code;Lexend Deca;Teko;Rajdhani;Saira;Sen;Tajawal;Cairo;Arvo;PT Sans;PT Serif;
    PT Mono;Open Sans;Open Sans Condensed;Playfair;Playfair Display;Merriweather;Merriweather Sans;DM Sans;DM Mono;DM Serif Display;DM Serif Text;Source Sans;Source Serif;
    Source Code;Roboto;Roboto Slab;Roboto Mono;Roboto Condensed;Roboto Flex;Roboto Serif;IBM Plex Sans;IBM Plex Serif;IBM Plex Mono;Noto Sans;Noto Serif;Wix Madefor Display;
    Wix Madefor Text;Bai Jamjuree;Golos Text;Martian Mono;Martian Grotesk;Gantari;Kumbh Sans;Outfit;Parkinsans;Funnel Display;Funnel Sans;Afacad;Reddit Sans;Young Serif""".split(";")}
_OPEN_SERIES = ("noto", "ibmplex", "sourcesans", "sourceserif", "sourcecode", "roboto", "opensans", "dmsans", "dmserif", "dmmono", "firasans", "firacode", "firamono", "ptsans", "ptserif",
                "playfair", "merriweather", "montserrat", "nunito", "redhat", "spacegrotesk", "jetbrainsmono", "plusjakarta", "worksans", "librebaskerville", "librefranklin", "barlow", "archivo")
_STYLE_WORD = re.compile(r"(variable|var|vf|web|pro|std|regular|italic|bold|semibold|demibold|extrabold|ultrabold|black|heavy|light|extralight|ultralight|thin|medium|book|roman|normal|"
                         r"display|text|tight|latin|subset|fallback|local|\d+)$")

def is_open_family(name):
    """True for a family name that is a well-known open-source font, with or without a style suffix (InterVariable, SourceSansProBold)."""
    n = _fkey(name)
    for _ in range(6):
        if n in _OPEN_FAMILIES or any(n.startswith(p) for p in _OPEN_SERIES): return True
        m = _STYLE_WORD.sub("", n)
        if m == n or not m: return False
        n = m
    return False

# (source, licence, label, hosts). Commercial services other than Adobe have no source value of their own: "unknown".
_FONT_SERVICES = (
    ("google", "open", "Google Fonts", ("fonts.gstatic.com", "fonts.googleapis.com")),
    ("bunny", "open", "Bunny Fonts", ("fonts.bunny.net",)),
    ("adobe", "ask", "Adobe Fonts", ("typekit.net", "typekit.com", "use.edgefonts.net")),
    ("unknown", "ask", "a commercial font service", ("fonts.com", "fonts.net", "typography.com", "monotype.com", "myfonts.net", "linotype.com", "webtype.com", "typotheque.com", "fontstand.com")),
)

def font_service(urls):
    for u in urls:
        host = urlparse(u or "").netloc.lower()
        for source, licence, label, hosts in _FONT_SERVICES:
            if any(host == h or host.endswith("." + h) for h in hosts) or (source == "unknown" and "monotype" in host):
                return source, licence, label if source != "unknown" else f"{label} ({host})"
    return None

def font_roles(body_family, head_family, body_stack, head_stack, use, faces, declared, heading_use=None):
    """Families to classify, most important first: {family: {"roles": [...], "stack": css stack}}. A third one only if it is clearly in use."""
    roles = {}
    def add(fam, role, stack):
        key = next((k for k in roles if (k or "").casefold() == (fam or "").casefold()), fam)
        r = roles.setdefault(key, {"roles": [], "stack": stack})
        if role not in r["roles"]: r["roles"].append(role)
    add(head_family or body_family, "head", head_stack if head_family else body_stack); add(body_family, "body", body_stack)
    web = {f["family"].casefold() for f in faces} | {f["family"].casefold() for f in declared}
    total = sum(u["chars"] for u in use.values()) or 1
    best = None
    for fam, u in use.items():
        if any((k or "").casefold() == fam.casefold() for k in roles) or fam.lower() in _GENERIC or re.search(r"icon|awesome|glyph|symbol|material", fam, re.I): continue
        is_web, share = fam.casefold() in web, u["chars"] / total
        in_heads = (heading_use or {}).get(fam, 0)          # a web font on several headings counts most, then a web font with real text share, then the code font
        if is_web and (in_heads >= 3 or share >= .08): cand = (2 + share + (1 if in_heads >= 3 else 0), fam, "mono" if u.get("mono") else ("display" if in_heads >= 3 or u["size"] >= 28 else "accent"), u["stack"])
        elif u.get("code", 0) > 60 and (is_web or u.get("mono")): cand = ((1 if is_web else 0) + share, fam, "mono", u["stack"])
        else: continue
        if not best or cand[0] > best[0]: best = cand
    if best: add(best[1], best[2], best[3])
    return roles

def classify_fonts(root, roles, faces, font_bodies, declared, save=True):
    """Sort the families by licence situation and save only what may be saved.
    Returns (families, files, pending, weights): files go to fonts/ (embedded by the build), pending to fonts/pending/."""
    families, files, pending, weights, seen_bodies = [], [], [], {}, set()
    for fam, info in roles.items():
        key = (fam or "").casefold()
        mine = [f for f in faces if f["family"].casefold() == key] if fam else []
        known = [f for f in declared if f["family"].casefold() == key] if fam else []
        used = sorted({w for f in known if f.get("status") == "loaded" for w in _weight_num(f["weight"])})
        label = fam or next((s.strip().strip("\"'") for s in (info.get("stack") or "").split(",") if s.strip()), "sans-serif")
        rec = {"family": label, "roles": info["roles"], "source": "system", "licence": "system", "status": "system", "files": 0, "weights": [], "note": ""}
        families.append(rec)
        if not mine and not known:
            rec["note"] = "System font, no web font is loaded; decks use the same font stack."; continue
        hits = []
        for f in mine:
            u = next((u for u in f["urls"] if u in font_bodies), None)
            if u: hits.append((f, u))
        urls = [u for f in mine for u in f["urls"]] + [f.get("css") for f in mine]
        service = font_service([u for _, u in hits]) or font_service(urls)
        where = ""
        if service: rec["source"], rec["licence"], where = service
        elif mine: rec["source"], rec["licence"] = "self-hosted", "open" if is_open_family(fam) else "ask"
        else: rec["source"], rec["licence"] = "unknown", "open" if is_open_family(fam) else "ask"
        target = None
        if save and hits: target = "fonts" if rec["licence"] == "open" else ("fonts/pending" if rec["source"] == "self-hosted" else None)
        saved = []
        if target:
            os.makedirs(os.path.join(root, target), exist_ok=True)
            for face, u in hits:
                ext = os.path.splitext(urlparse(u).path)[1].lower()
                if ext not in (".woff2", ".woff", ".ttf", ".otf"): ext = ".woff2"
                w = _weight_num(face["weight"])
                fn = f"{target}/{slugify(face['family'])}-{'-'.join(str(n) for n in w)}-{face['style']}-{hashlib.md5(u.encode()).hexdigest()[:6]}{ext}"
                digest = hashlib.md5(font_bodies[u]).hexdigest()
                if any(f["file"] == fn for f in saved) or digest in seen_bodies: continue
                seen_bodies.add(digest)
                try: open(os.path.join(root, fn), "wb").write(font_bodies[u])
                except Exception: continue
                saved.append({"family": fam, "weight": " ".join(str(n) for n in w), "style": face["style"], "file": fn})
                if target == "fonts": weights.setdefault(fam, set()).update(range(w[0], w[-1] + 1, 100) if len(w) > 1 else w)
        (files if target == "fonts" else pending).extend(saved)
        rec["files"] = len(saved)
        rec["status"] = "missing" if not saved else ("embedded" if target == "fonts" else "pending")
        ws = set(used)
        for f in ([face for face, _ in hits] or mine):
            w = _weight_num(f["weight"]); ws.update(range(w[0], w[-1] + 1, 100) if len(w) > 1 else w)
        rec["weights"] = sorted(ws)
        n = f"{len(saved)} file{'s' if len(saved) != 1 else ''}"
        if rec["source"] in ("google", "bunny"): origin = f"Served by {where} under an open licence"
        elif rec["licence"] == "open": origin = f"{'Self-hosted' if mine else 'Loaded by script'}, and {label} is a well-known open-source family"
        else: origin = ""
        if rec["licence"] == "open":
            rec["note"] = (f"{origin}; {n} embedded." if saved else f"{origin}, but font saving is switched off (--no-fonts); decks use the fallback font." if not save
                           else f"{origin}, but no font file could be fetched; add files to fonts/ or decks use the fallback font.")
        elif service:
            rec["note"] = f"Licensed through {where}: the licence is tied to that service, so no files were saved; supply your own files in fonts/ if your licence allows embedding in documents."
        elif saved:
            rec["note"] = f"Self-hosted files of unknown licence: {n} kept in fonts/pending/ and not embedded; move them to fonts/ and into fonts.files once the licence allows embedding in documents."
        else:
            rec["note"] = ("Self-hosted web font of unknown licence" if mine else "Web font of unknown origin") + (", not saved (--no-fonts)" if not save and hits else ", its files could not be fetched") + \
                          "; supply files in fonts/ if your licence allows embedding in documents."
    return families, files, pending, weights

# ---------------------------------------------------------------- look and feel

def _snake(k):
    return re.sub(r"([A-Z])", lambda m: "_" + m.group(1).lower(), k)

def _empty(v):
    return v is None or v is False or v == "" or v == [] or v == {}

def _clean(d):
    return {_snake(k): v for k, v in d.items() if not _empty(v) and not k.startswith("_")}

def _groups(items, keys):
    g = {}
    for it in items: g.setdefault(json.dumps([it.get(k) for k in keys], sort_keys=True, default=str), []).append(it)
    return sorted(g.values(), key=len, reverse=True)

def _count(values, n=5):
    vals = [json.dumps(v, sort_keys=True) for v in values if not _empty(v)]
    return [{"value": json.loads(v), "count": c} for v, c in sorted({v: vals.count(v) for v in dict.fromkeys(vals)}.items(), key=lambda kv: -kv[1])[:n]]

def _mode(values):
    c = _count(values, 1); return c[0]["value"] if c else None

def _median(values):
    v = sorted(x for x in values if isinstance(x, (int, float))); return v[len(v) // 2] if v else None

def _style(group, keys, extra=(), sets=(), medians=(), sample="text"):
    """One record for a group of identically styled elements: the shared values, how often, a few sample texts."""
    rec = _clean({k: group[0].get(k) for k in keys}); rec["count"] = len(group)
    for k in extra:
        m = _mode([it.get(k) for it in group])
        if not _empty(m): rec[_snake(k)] = m
    for k in sets:
        s = sorted({it.get(k) for it in group if isinstance(it.get(k), str)})
        if s: rec[_snake(k)] = s
    for k in medians:
        m = _median([it.get(k) for it in group])
        if m is not None: rec[_snake(k)] = m
    texts = list(dict.fromkeys(it.get(sample) for it in group if sample and it.get(sample)))
    if texts: rec["samples"] = texts[:3]
    ref = next((it["ref"] for it in group if it.get("ref") is not None), None)
    if ref is not None: rec["_ref"] = ref
    return rec

_ASPECTS = (("1:1", 1), ("5:4", 1.25), ("4:3", 1.333), ("3:2", 1.5), ("16:10", 1.6), ("16:9", 1.778), ("2:1", 2), ("21:9", 2.333), ("3:1", 3), ("4:5", .8), ("3:4", .75), ("2:3", .667), ("9:16", .5625))

def _aspect(w, h):
    r = w / max(h, 1); name, v = min(_ASPECTS, key=lambda a: abs(a[1] - r) / a[1])
    return name if abs(v - r) / v < .06 else f"{r:.2f}:1"

_BTN = ["kind", "background", "color", "border", "radius", "fontWeight", "textTransform", "letterSpacing", "boxShadow"]

def summarise_components(comps):
    """Condense what COMPONENTS_JS measured on the pages (home first) into few, counted, deduplicated styles.
    Keys starting with "_" are element references for the screenshots and are stripped before saving."""
    def rows(key, sub=None):
        out = []
        for c in comps:
            v = c.get(key)
            if sub and isinstance(v, dict): v = v.get(sub)
            if isinstance(v, list): out += [x for x in v if isinstance(x, dict)]
        return out
    def tally(items, keys, n, **kw):
        return [_style(g, keys, **kw) for g in _groups(items, keys)[:n]]
    s = {}
    # buttons: the most frequent filled style is the primary one, buttons in the page body count more than those in the header
    btns, out = [dict(b) for b in rows("buttons")], []
    for b in btns:                 # a border in the colour of the fill is no border
        if b["kind"] == "filled" and isinstance(b.get("border"), str) and isinstance(b.get("background"), str) and b["border"].endswith(b["background"]): b["border"] = None
    def score(g):                  # frequent, in the page body, and in a real colour
        bg = g[0].get("background") or ""
        return (len(g) + 2 * sum(b.get("where") == "body" for b in g)) * (2 if re.fullmatch(r"#[0-9a-f]{6}", bg) and saturation(bg) > .25 else 1)
    by_kind = {k: sorted([g for g in _groups(btns, _BTN) if g[0]["kind"] == k], key=score, reverse=True) for k in ("filled", "outline", "text")}
    for kind, n in (("filled", 3), ("outline", 2), ("text", 2)):
        for i, g in enumerate(by_kind[kind][:n]):
            lead = kind == "filled" or not by_kind["filled"]
            rec = {"role": "text" if kind == "text" else ("primary" if lead and i == 0 else "secondary")}
            rec.update(_style(g, _BTN, extra=("padding", "fontSize", "on", "family", "icon", "underline", "transition"), sets=("where",), medians=("height",)))
            sizes = _count([{"padding": b["padding"], "font_size": b["fontSize"], "height": b["height"]} for b in g], 3)
            if len(sizes) > 1: rec["sizes"] = [dict(x["value"], count=x["count"]) for x in sizes]
            arrows = [b["arrow"] for b in g if b.get("arrow")]
            rec["arrow"] = (_mode(arrows) if len(arrows) * 2 >= len(g) else "sometimes " + _mode(arrows)) if arrows else False
            out.append(rec)
    s["buttons"] = out
    s["cards"] = tally(rows("cards"), ["frameless", "background", "border", "radius", "shadow", "padding", "image"], 4,
                       extra=("imageRadius", "textInset", "overflow", "on", "heading", "textColor", "textSize", "link"), medians=("width", "height"))
    labels, out = rows("labels"), []
    lkeys = ["kind", "color", "background", "border", "radius", "padding", "textTransform", "letterSpacing", "fontWeight", "fontSize"]
    for kind, n in (("eyebrow", 4), ("badge", 3), ("label", 2)):
        out += tally([l for l in labels if l["kind"] == kind], lkeys, n, extra=("decoration", "family", "above", "gap"))
    s["labels"] = out
    heads, hs = rows("headings"), {}
    for lvl in ("h1", "h2", "h3"):
        mine = [h for h in heads if h["level"] == lvl]
        if not mine: continue
        hs[lvl] = tally(mine, ["size", "weight", "lineHeight", "letterSpacing", "textTransform", "color", "family"], 2, extra=("align", "fontStyle", "decoration", "on"), medians=("width",))
        hl = [x for h in mine for x in (h.get("highlight") or [])]
        marks = []
        for g in _groups(hl, ["color", "background", "gradient_text", "underline", "font_style", "weight", "family", "shape_behind"])[:2]:
            m = _clean({k: v for k, v in g[0].items() if k != "text"}); m["count"] = len(g); m["samples"] = list(dict.fromkeys(x["text"] for x in g))[:3]; marks.append(m)
        hs[lvl][0]["word_highlight"] = marks or False
    s["headings"] = hs
    imgs, css = rows("images", "img"), rows("images", "css")
    for c in css: c["aspect"] = _aspect(c["width"], c["height"])
    s["images"] = _clean({
        "measured": len(imgs), "radius": _count([i["radius"] for i in imgs], 4), "aspect_ratios": _count([_aspect(i["width"], i["height"]) for i in imgs], 5),
        "object_fit": _count([i.get("objectFit") for i in imgs], 3), "filter": _count([i.get("filter") for i in imgs], 3), "blend_mode": _count([i.get("blend") for i in imgs], 3),
        "clip_path": _count([i.get("clip") for i in imgs], 3), "mask": _count([i.get("mask") for i in imgs], 2), "shadow": _count([i.get("shadow") for i in imgs], 3),
        "border": _count([i.get("border") for i in imgs], 2), "opacity": _count([i.get("opacity") for i in imgs], 2), "tint_behind": _count([i.get("tint") for i in imgs], 2),
        "overlays": _count([o for i in imgs for o in (i.get("overlays") or [])], 4), "duotone_hint": _mode([i.get("duotone") for i in imgs]),
        "treated": sum(1 for i in imgs if i.get("treated")),
        "background_images": tally(css, ["radius", "size", "blend", "filter", "clip", "attachment", "overlays"], 3, extra=("aspect", "hasText"), sample=None)})
    home = (comps[0].get("sections") if comps else None) or {}
    seqs = [q for c in comps for q in ((c.get("sections") or {}).get("sequence") or [])]
    pads = [p for q in seqs for p in (q.get("pad") or []) if 8 <= p <= 400]
    cws = [round(q["contentWidth"] / 10) * 10 for q in seqs if 600 <= (q.get("contentWidth") or 0) <= (home.get("viewport") or 1440)]
    mws = {}
    for c in comps:
        for w, n in ((c.get("sections") or {}).get("maxWidths") or {}).items(): mws[w] = mws.get(w, 0) + n
    s["sections"] = _clean({
        "page": comps[0].get("url") if comps else None, "viewport": home.get("viewport"), "page_height": home.get("pageHeight"), "body_background": home.get("body"), "header": _clean(home.get("header") or {}),
        "sequence": [_clean(q) for q in (home.get("sequence") or [])], "sequence_truncated_from": home.get("truncated"),
        "padding_y": {"typical": _median(pads), "min": min(pads), "max": max(pads)} if pads else None,
        "content_width": _mode(cws), "content_widths": _count(cws, 3),
        "max_width_declared": [{"value": int(w), "count": n} for w, n in sorted(mws.items(), key=lambda kv: -kv[1])[:3]]})
    g = lambda k: rows("graphics", k)
    s["shapes"] = _clean({
        "clip_paths": tally(g("clip"), ["value"], 4, sets=("on",), medians=("width", "height"), sample=None),
        "transforms": tally(g("transform"), ["rotate", "skew", "on"], 5, extra=("background",), medians=("width", "height"), sample=None),
        "circles_and_blobs": tally(g("circles"), ["shape", "size", "background", "border", "blur", "opacity", "blend"], 5, extra=("position",), sample=None),
        "patterns": tally(g("patterns"), ["kind", "value", "size"], 4, sets=("on",), sample=None),
        "gradients": tally(g("gradients"), ["value"], 6, sets=("on",), sample=None),
        "dividers": tally(g("dividers"), ["type", "thickness", "color", "style", "radius"], 6, extra=("full",), medians=("width",), sample=None),
        "accent_borders": tally(g("borders"), ["side", "line"], 6, sets=("on",), sample=None),
        "shadows": tally(g("shadows"), ["value"], 6, sets=("on",), sample=None),
        "text_shadows": tally(g("textShadows"), ["value"], 2, sample=None)})
    s["lists"] = tally(rows("lists"), ["ordered", "marker", "color", "fontSize"], 3, extra=("gap", "indent"), sample=None)
    s["links"] = _clean({"in_text": tally(rows("links", "text"), ["color", "ownColor", "underline", "underlineOffset", "borderBottom", "background", "fontWeight"], 3),
                         "navigation": tally(rows("links", "nav"), ["color", "fontWeight", "fontSize", "textTransform", "letterSpacing", "family", "underline"], 2)})
    glyphs = {}
    for c in comps:
        for ch, n in (c.get("arrowGlyphs") or {}).items():
            t = glyphs.setdefault(ch, {"glyph": ch, "in_links": 0, "in_text": 0, "in_pseudo": 0})
            for k in ("links", "text", "pseudo"): t["in_" + k] += n.get(k, 0)
    s["arrows"] = {"glyphs": sorted(glyphs.values(), key=lambda t: -(t["in_links"] * 3 + t["in_pseudo"] * 3 + t["in_text"]))[:5]}
    return s

def _strip_refs(v):
    if isinstance(v, dict): return {k: _strip_refs(x) for k, x in v.items() if not k.startswith("_")}
    if isinstance(v, list): return [_strip_refs(x) for x in v]
    return v

def shoot_components(pg, root, comp, notes, shots, first=True):
    """Close-ups of representative components of the page that is open, added to shots as {file, shows}: at most ten in all.
    The home page (first) gives hero, buttons, heading and footer; later pages only fill in what the home page did not show."""
    folder = os.path.join(root, "raw/screens/components"); os.makedirs(folder, exist_ok=True)
    if first:
        for f in os.listdir(folder):
            if f.endswith(".png"): os.remove(os.path.join(folder, f))
    have = {os.path.basename(x["file"])[:-4] for x in shots}
    s = summarise_components([comp]); plan = []
    sample = lambda x: (x.get("samples") or [""])[0]
    if first:
        plan.append(("hero", ['[data-vs-comp="hero"]'], 0, "hero: the first screen with the main heading"))
        for role in ("primary", "secondary"):
            b = next((x for x in s["buttons"] if x["role"] == role and "_ref" in x), None)
            if b: plan.append((f"button_{role}", [f'[data-vs-b="{b["_ref"]}"]'], 28, f"{role} button ({b['kind']}): {sample(b)}"))
    for i, c in enumerate([c for c in s["cards"] if "_ref" in c][:2]):
        plan.append((f"card_{i + 1}", [f'[data-vs-c="{c["_ref"]}"]'], 18, f"card ({'no frame' if c.get('frameless') else 'framed'}, image {c.get('image', 'none')}): {sample(c)}"))
    ebs = [l for l in s["labels"] if l["kind"] == "eyebrow" and "_ref" in l]
    eb = next((l for l in ebs if l.get("above") == "h2"), ebs[0] if ebs else None)
    if eb: plan.append(("heading_eyebrow", [f'[data-vs-l="{eb["_ref"]}"]', f'[data-vs-eh="{eb["_ref"]}"]'], 26, f"section heading with its eyebrow: {sample(eb)}"))
    elif first: plan.append(("heading", ["main h2, section h2, h2"], 26, "section heading (no eyebrow found above the headings)"))
    imgs = sorted((comp.get("images") or {}).get("img") or [], key=lambda i: (not i.get("treated"), -i["width"] * i["height"]))
    if imgs and imgs[0].get("treated"): plan.append(("image_treated", [f'[data-vs-i="{imgs[0]["ref"]}"]'], 18, "image with its treatment (overlay, filter, blend or clip measured on it)"))
    elif imgs and first: plan.append(("image", [f'[data-vs-i="{imgs[0]["ref"]}"]'], 18, "image (no filter, overlay or clip measured on it)"))
    plan.append(("icon_row", ['[data-vs-comp="icon_row"]'], 12, "a group of icons in the page body"))
    badge = next((l for l in s["labels"] if l["kind"] == "badge" and "_ref" in l), None)
    if badge: plan.append(("badge", [f'[data-vs-l="{badge["_ref"]}"]'], 30, f"badge or pill: {sample(badge)}"))
    if first: plan.append(("footer", ['[data-vs-comp="footer"]'], 0, "footer"))
    for name, sels, margin, shows in plan:
        if name in have or len(shots) >= 10: continue
        try:
            box = pg.evaluate(SHOOT_JS, [sels, margin])
            if not box: continue
            path = os.path.join(folder, name + ".png"); pg.screenshot(path=path, clip=box)
            try:
                from PIL import Image
                im = Image.open(path)
                if im.width > 1440: im = im.resize((1440, round(im.height * 1440 / im.width)), Image.LANCZOS)
                if im.width * im.height > 500000: im.convert("RGB").quantize(256, method=Image.Quantize.MEDIANCUT).save(path, optimize=True)      # keeps the folder small
                else: im.save(path, optimize=True)
            except Exception: pass
            shots.append({"file": f"raw/screens/components/{name}.png", "shows": shows, "page": comp.get("url")})
        except Exception as e:
            notes.append(f"component screenshot {name} failed: {str(e)[:80]}")

def save_elements(ctx, root, comps, notes):
    """Write the site's inline svg icons, arrows and decorative shapes to elements/ and draw raw/elements.png.
    Returns (lists of saved files by kind, facts for components.json)."""
    import base64
    for d in ("icons", "arrows", "shapes"):
        p = os.path.join(root, "elements", d); os.makedirs(p, exist_ok=True)
        for f in os.listdir(p):
            if f.endswith(".svg"): os.remove(os.path.join(p, f))
    found, shapes, linked, icon_fonts, social, unresolved = {}, {}, {}, {}, 0, 0
    for c in comps:
        ic = c.get("icons") or {}
        social += ic.get("social") or 0; unresolved += ic.get("unresolved") or 0
        for it in ic.get("list") or []:
            g = found.setdefault(hashlib.md5(it["key"].encode()).hexdigest(), dict(it, count=0)); g["count"] += 1
            if it.get("arrow") and g.get("arrow") not in ("shape", "name"): g["arrow"] = it["arrow"]
        for it in ic.get("shapes") or []: shapes.setdefault(hashlib.md5(it["key"].encode()).hexdigest(), it)
        for it in ic.get("imgs") or []:
            g = linked.setdefault(it["src"], dict(it, count=0)); g["count"] += 1
        for f, n in (ic.get("fonts") or {}).items(): icon_fonts[f] = icon_fonts.get(f, 0) + n
    for src, it in sorted(linked.items(), key=lambda kv: -kv[1]["count"])[:16]:      # svg files used as <img>: taken as they are, with their own colours
        try:
            r = ctx.request.get(src, timeout=8000); body = r.body() if r.ok else b""
            if b"<svg" not in body or len(body) > 15000 or b"<script" in body.lower(): continue
            found.setdefault(hashlib.md5(body).hexdigest(), dict(it, markup=body.decode("utf-8", "replace"), linked=True))
        except Exception:
            continue
    ranked = sorted(found.values(), key=lambda i: -i["count"])
    sprite_src, sprite_n = [], 0                          # a sprite of the site: its symbols after the icons seen on the pages
    LOGO, SOCIAL = re.compile(r"logo|brand|wordmark|signet", re.I), re.compile(r"facebook|twitter|linkedin|instagram|youtube|tiktok|xing|github|mastodon|whatsapp|pinterest|vimeo|bluesky|threads|telegram|spotify|soundcloud|flickr|snapchat|reddit|discord|social", re.I)
    ARROW = re.compile(r"arrow|pfeil|chevron|caret|angle|next|prev|toplink", re.I)
    have = {re.sub(r"\s+", "", i.get("markup") or "") for i in ranked}
    for c in comps:
        sp = c.get("sprite") or {}
        sprite_src += [u for u in sp.get("sources") or [] if u not in sprite_src]
        for s in sp.get("symbols") or []:
            if LOGO.search(s["id"]) or SOCIAL.search(s["id"]) or re.sub(r"\s+", "", s["markup"]) in have: continue
            have.add(re.sub(r"\s+", "", s["markup"])); sprite_n += 1
            hint = re.sub(r"^(icon|ico|svg|sprite)[-_]+|[-_]+(icon|svg)$", "", re.sub(r"^[a-z0-9]+--", "", s["id"].lower()))
            ranked.append({"markup": s["markup"], "hint": hint, "arrow": "name" if ARROW.search(s["id"]) else None, "count": 0, "width": 48, "height": 48, "mono": s.get("mono"),
                           "color": (s.get("colours") or [None])[0], "sprite": True})
    def write(kind, items):
        for n, it in enumerate(items, 1):
            tail = re.sub(r"[^a-z0-9]+", "-", (it.get("hint") or "").lower()).strip("-")[:24]
            it["file"] = f"elements/{kind}s/{kind}_{n:02d}{'_' + tail if tail else ''}.svg"
            open(os.path.join(root, it["file"]), "w", encoding="utf-8").write(it["markup"])
        return items
    icons = [i for i in ranked if not i.get("arrow") and not i.get("sprite")][:40] + [i for i in ranked if not i.get("arrow") and i.get("sprite")][:160]
    sets = {"icon": write("icon", icons), "arrow": write("arrow", [i for i in ranked if i.get("arrow")][:12]), "shape": write("shape", list(shapes.values())[:6])}
    checked = {}
    try:                                      # contact sheet: the files are loaded as images, which also proves that they stand alone
        html = ("<meta charset='utf-8'><style>body{margin:0;padding:18px;background:#d6d6d6;font:11px/1.3 Menlo,Consolas,monospace;color:#111}h2{font:600 14px Arial,sans-serif;margin:16px 2px 8px}"
                ".g{display:flex;flex-wrap:wrap;gap:8px}.t{width:170px;background:#c4c4c4;padding:10px 6px 8px;text-align:center;box-sizing:border-box}"
                ".i{height:78px;display:flex;align-items:center;justify-content:center}.n{margin-top:8px;word-break:break-all}.m{color:#444}</style>")
        for kind, title, css in (("icon", "icons", "height:56px;max-width:150px"), ("arrow", "arrows", "height:56px;max-width:150px"), ("shape", "shapes", "max-height:76px;max-width:156px")):
            if not sets[kind]: continue
            html += f"<h2>elements/{title}/ ({len(sets[kind])})</h2><div class='g'>"
            for it in sets[kind]:
                b64 = base64.b64encode(it["markup"].encode("utf-8")).decode()
                meta = f"{it['width']}x{it['height']} px" + (f", {it['count']}x" if it.get("count", 1) > 1 else "") + (", by position" if it.get("arrow") == "position" else "") + (", img file" if it.get("linked") else "")
                html += f"<div class='t'><div class='i'><img data-f='{it['file']}' style='{css}' src='data:image/svg+xml;base64,{b64}'></div><div class='n'>{os.path.basename(it['file'])}</div><div class='m'>{meta}</div></div>"
            html += "</div>"
        if any(sets.values()):
            page = ctx.new_page(); page.set_viewport_size({"width": 1120, "height": 400}); page.set_content(html)
            checked = page.evaluate(SHEET_JS)
            broken = [f for f, v in checked.items() if not v.get("ok")]
            for f in broken:
                try: os.remove(os.path.join(root, f))
                except Exception: pass
            for kind in sets: sets[kind] = [i for i in sets[kind] if i["file"] not in broken]
            if broken: notes.append(f"{len(broken)} svg element(s) did not render as standalone files and were dropped")
            if any(sets.values()): page.screenshot(path=os.path.join(root, "raw/elements.png"), full_page=True)
            page.close()
    except Exception as e:
        notes.append("element contact sheet could not be drawn: " + str(e)[:80])
    line, filled, strokes = 0, 0, []
    for it in sets["icon"]:
        cov = (checked.get(it["file"]) or {}).get("cov")
        if (it.get("nStroke") or 0) > 0 and (it.get("nStroke") or 0) >= (it.get("nFill") or 0):
            line += 1
            if it.get("sw") and it.get("grid"): strokes.append(round(it["sw"] * 24 / it["grid"] * 4) / 4)
        elif cov is not None and cov < .2: line += 1         # an outline drawn as a filled path
        else: filled += 1
    style = None if not sets["icon"] else ("line" if line >= filled else "filled")
    facts = _clean({
        "saved": len(sets["icon"]), "style": style, "line": line, "filled": filled, "stroke_width_on_24_grid": _mode(strokes) if style == "line" else None,
        "sizes_px": _count([i["height"] for i in sets["icon"]], 4), "colors": _count([i.get("color") for i in sets["icon"]], 3), "one_colour": sum(1 for i in sets["icon"] if i.get("mono")),
        "from_img_files": sum(1 for i in sets["icon"] if i.get("linked")), "from_sprite": sum(1 for i in sets["icon"] if i.get("sprite")), "sprite_files": sprite_src[:4], "icon_font": [{"family": f, "count": n} for f, n in sorted(icon_fonts.items(), key=lambda kv: -kv[1])[:2]],
        "skipped_social": social, "skipped_unresolved": unresolved,
        "arrow_files": [{"file": i["file"], "found_by": i["arrow"], "in_button_or_link": i.get("inButton", False), "rotated_by_css": bool(i.get("rotated"))} for i in sets["arrow"]],
        "shape_files": [{"file": i["file"], "width": i["width"], "height": i["height"]} for i in sets["shape"]]})
    if icon_fonts: notes.append("the site draws icons with an icon font (" + ", ".join(list(icon_fonts)[:2]) + "): those are not saved as svg"
                                + (f"; its svg sprite gave {sum(1 for i in sets['icon'] if i.get('sprite'))} icon(s)" if sprite_n else ""))
    if unresolved: notes.append(f"{unresolved} svg icon(s) point to an external sprite or contain images and were not saved")
    files = {k: [i["file"] for i in v] for k, v in sets.items()}
    return files, facts, (_mode(strokes) if style == "line" else None), style

# ---------------------------------------------------------------- motion: how the site moves

MOTION_CENSUS_JS = r"""
() => {
  const out = {elements: 0, transitions: {}, transition_easings: {}, transition_properties: {}, animations: [], keyframes: {}, sheets_blocked: 0,
               libraries: [], videos: [], hints: {}, smooth_scroll: false, scroll_timeline: false};
  const add = (o, k, w) => { o[k] = (o[k] || 0) + (w || 1); };
  const secs = s => s.split(',').map(x => { x = x.trim(); return x.endsWith('ms') ? parseFloat(x) / 1000 : parseFloat(x) || 0; });
  const top = s => s.split(/,(?![^(]*\))/).map(x => x.trim());
  const seen = {}, vw = innerWidth, vh = innerHeight;
  for (const e of document.querySelectorAll('body *')) {
    out.elements++;
    const s = getComputedStyle(e);
    if (s.display === 'none') continue;
    const td = secs(s.transitionDuration);
    if (td.some(d => d > 0)) {
      const tp = top(s.transitionProperty), tf = top(s.transitionTimingFunction);
      td.forEach((d, i) => { if (d > 0) { add(out.transitions, d.toFixed(2)); add(out.transition_properties, tp[i % tp.length]); add(out.transition_easings, tf[i % tf.length]); } });
    }
    if (s.animationName && s.animationName !== 'none') {
      const names = top(s.animationName), du = secs(s.animationDuration), ea = top(s.animationTimingFunction), it = top(s.animationIterationCount), r = e.getBoundingClientRect();
      names.forEach((n, i) => {
        if (n === 'none') return;
        const key = n + '|' + du[i % du.length] + '|' + ea[i % ea.length] + '|' + it[i % it.length];
        if (!seen[key]) { seen[key] = {name: n, duration: du[i % du.length], easing: ea[i % ea.length], iterations: it[i % it.length], count: 0, width: Math.round(r.width), height: Math.round(r.height),
                                       on: (e.tagName.toLowerCase() + (typeof e.className === 'string' && e.className ? '.' + e.className.trim().split(/\s+/).slice(0, 2).join('.') : '')).slice(0, 80)};
                          out.animations.push(seen[key]); }
        seen[key].count++; seen[key].width = Math.max(seen[key].width, Math.round(r.width));
      });
    }
    if (s.animationTimeline && s.animationTimeline !== 'auto' && s.animationTimeline !== 'none') out.scroll_timeline = true;
  }
  out.smooth_scroll = getComputedStyle(document.documentElement).scrollBehavior === 'smooth';
  const walk = rules => { for (const r of rules) {
    if (r.type === 7 || (r.constructor && r.constructor.name === 'CSSKeyframesRule')) {
      if (Object.keys(out.keyframes).length >= 150) return;
      const props = {};
      for (const k of r.cssRules) for (let i = 0; i < k.style.length; i++) { const p = k.style[i]; (props[p] = props[p] || []).push(k.keyText + ' ' + k.style.getPropertyValue(p).slice(0, 80)); }
      out.keyframes[r.name] = props;
    } else if (r.cssRules) { try { walk(r.cssRules); } catch (e) {} }
  } };
  for (const sh of document.styleSheets) { try { walk(sh.cssRules); } catch (e) { out.sheets_blocked++; } }
  const w = window, has = sel => !!document.querySelector(sel), res = performance.getEntriesByType('resource').map(r => r.name.toLowerCase()).filter(n => /\.m?js(\?|$)/.test(n)).join(' ');
  const lib = (name, test) => { let ok = false; try { ok = !!test(); } catch (e) {} if (ok) out.libraries.push(name); };
  lib('GSAP', () => w.gsap || w.TweenMax || w.TweenLite || /gsap|tweenmax/.test(res));
  lib('GSAP ScrollTrigger', () => w.ScrollTrigger || /scrolltrigger/.test(res) || has('.pin-spacer'));
  lib('Lenis', () => w.Lenis || w.lenis || document.documentElement.classList.contains('lenis') || /lenis/.test(res));
  lib('Locomotive Scroll', () => w.LocomotiveScroll || has('[data-scroll-container]') || /locomotive/.test(res));
  lib('Framer Motion', () => has('[data-framer-appear-id],[data-projection-id],[data-framer-name]') || w.MotionGlobalConfig || /framer-motion|framer\.com\/m\//.test(res));
  lib('Motion One', () => w.Motion || /motion(\.min)?\.js|motion-one|@motionone/.test(res));
  lib('AOS', () => w.AOS || has('[data-aos]'));
  lib('ScrollReveal', () => w.ScrollReveal || has('[data-sr-id]'));
  lib('WOW.js', () => w.WOW || has('.wow'));
  lib('Swiper', () => w.Swiper || has('.swiper,.swiper-container'));
  lib('Splide', () => w.Splide || has('.splide'));
  lib('Slick', () => has('.slick-slider'));
  lib('Flickity', () => w.Flickity || has('.flickity-enabled'));
  lib('Embla', () => has('.embla') || /embla/.test(res));
  lib('Lottie', () => w.lottie || w.bodymovin || has('lottie-player,dotlottie-player,dotlottie-wc,[data-animation-type="lottie"]') || /lottie/.test(res));
  lib('Rive', () => w.rive || /rive/.test(res));
  lib('Three.js', () => w.THREE || w.__THREE__ || /three(\.module)?(\.min)?\.js/.test(res));
  lib('anime.js', () => w.anime || /anime(\.min)?\.js/.test(res));
  lib('Barba', () => w.barba || has('[data-barba]'));
  lib('Swup', () => w.swup || has('#swup'));
  lib('SplitType or SplitText', () => w.SplitType || w.SplitText || w.Splitting || has('.split-line,.splitting,.word > .char,[data-splitting]'));
  lib('Webflow interactions', () => w.Webflow && has('[data-w-id]'));
  lib('Alpine transitions', () => has('[x-transition]'));
  out.hints = {canvas: document.querySelectorAll('canvas').length, marquee_tags: document.querySelectorAll('marquee').length,
               marquee_classes: document.querySelectorAll('[class*="marquee" i],[class*="ticker" i]').length,
               view_transitions: !!document.querySelector('meta[name="view-transition"]'), sticky: [...document.querySelectorAll('body *')].slice(0, 4000).filter(e => getComputedStyle(e).position === 'sticky').length};
  for (const v of document.querySelectorAll('video')) { const r = v.getBoundingClientRect();
    out.videos.push({autoplay: v.autoplay, muted: v.muted, loop: v.loop, controls: v.controls, share_of_viewport: +(Math.max(0, r.width) * Math.max(0, r.height) / (vw * vh)).toFixed(2),
                     top: Math.round(r.top + scrollY), behind_content: getComputedStyle(v).position === 'absolute' || getComputedStyle(v).position === 'fixed' || getComputedStyle(v).objectFit === 'cover'}); }
  return out;
}
"""

# States of elements that wait for the visitor to scroll: taken before and after scrolling them into view.
REVEAL_JS = r"""
async (phase) => {
  const state = e => { const s = getComputedStyle(e); let op = 1; for (let a = e; a && a !== document.documentElement; a = a.parentElement) op *= parseFloat(getComputedStyle(a).opacity);
    const m = s.transform !== 'none' ? new DOMMatrixReadOnly(s.transform) : null, r = e.getBoundingClientRect();
    const blur = (s.filter.match(/blur\(([\d.]+)px\)/) || [])[1];
    return {opacity: +op.toFixed(2), tx: m ? Math.round(m.m41) : 0, ty: m ? Math.round(m.m42) : 0, scale: m ? +Math.hypot(m.m11, m.m12).toFixed(3) : 1,
            rotate: m ? Math.round(Math.atan2(m.m12, m.m11) * 57.3) : 0, clip: s.clipPath !== 'none' ? s.clipPath.slice(0, 60) : null, blur: blur ? +blur : 0,
            hidden: s.visibility === 'hidden', h: Math.round(r.height), w: Math.round(r.width)}; };
  const waiting = st => st.opacity < .15 || Math.abs(st.ty) > 3 || Math.abs(st.tx) > 3 || Math.abs(st.scale - 1) > .015 || st.blur > 0 || st.hidden || (st.clip && !/^inset\(0(px|%)?( 0(px|%)?)*\)$/.test(st.clip));
  const sleep = ms => new Promise(r => setTimeout(r, ms));
  if (phase === 'before') {
    const list = [], vh = innerHeight; let below = 0;
    for (const e of document.querySelectorAll('main *, section *, article *, body > div *')) {
      if (list.length >= 90) break;
      const r = e.getBoundingClientRect(); if (r.top < vh * 1.05 || r.width < 40 || r.height < 12) continue;
      if (e.closest('[data-vs-m],nav,header,footer,[aria-hidden="true"],dialog,[role="dialog"],[hidden]')) continue;
      const s = getComputedStyle(e); if (s.display === 'none' || s.position === 'fixed') continue;
      below++;
      const st = state(e); if (!waiting(st)) continue;
      const mask = Math.abs(st.ty) >= st.h * .7 && e.parentElement && /hidden|clip/.test(getComputedStyle(e.parentElement).overflow);
      const tp = s.transitionDuration.split(',').map(x => x.trim().endsWith('ms') ? parseFloat(x) / 1000 : parseFloat(x) || 0), dl = s.transitionDelay.split(',').map(x => x.trim().endsWith('ms') ? parseFloat(x) / 1000 : parseFloat(x) || 0);
      e.setAttribute('data-vs-m', list.length);
      list.push({i: list.length, tag: e.tagName.toLowerCase(), cls: (typeof e.className === 'string' ? e.className : '').trim().split(/\s+/).slice(0, 3).join(' ').slice(0, 70), y: Math.round(r.top + scrollY),
                 parent: [...document.querySelectorAll('*')].indexOf(e.parentElement), before: st, mask_parent: !!mask,
                 transition: Math.max(...tp), transition_delay: Math.max(...dl), easing: s.transitionTimingFunction.split(/,(?![^(]*\))/)[0].trim(), text: (e.innerText || '').trim().slice(0, 40)});
    }
    // time the first few: scroll each into view and watch how long it takes to come to rest
    const timed = [];
    for (const it of list.filter(x => !x.before.hidden).slice(0, 4)) {
      const e = document.querySelector('[data-vs-m="' + it.i + '"]'); if (!e) continue;
      e.scrollIntoView({block: 'center', behavior: 'instant'});
      const t0 = performance.now(); let first = null, last = null, prev = JSON.stringify(state(e));
      while (performance.now() - t0 < 2600) { await sleep(40); const now = JSON.stringify(state(e));
        if (now !== prev) { if (first === null) first = performance.now() - t0 - 40; last = performance.now() - t0; prev = now; }
        else if (last !== null && performance.now() - t0 - last > 400) break; }
      if (first !== null) timed.push({i: it.i, starts_after: +(Math.max(0, first) / 1000).toFixed(2), takes: +((last - Math.max(0, first)) / 1000).toFixed(2)});
    }
    return {below_the_fold: below, waiting: list, timed};
  }
  const after = {};
  for (const e of document.querySelectorAll('[data-vs-m]')) { const st = state(e), s = getComputedStyle(e);
    after[e.getAttribute('data-vs-m')] = Object.assign(st, {rest: !waiting(st), animation: s.animationName !== 'none' ? s.animationName.split(',')[0].trim() : null}); }
  return after;
}
"""

HOVER_PICK_JS = r"""
() => {
  const vis = e => { const r = e.getBoundingClientRect(); return r.width > 30 && r.height > 18 && r.top > 60 && r.bottom < innerHeight - 10 && r.left >= 0 && r.right <= innerWidth; };
  const bg = e => { const c = getComputedStyle(e).backgroundColor; return c && !/rgba\(.*, 0\)$|transparent/.test(c); };
  const picks = [], seen = new Set();
  const take = (e, kind) => { if (seen.has(e) || [...seen].some(o => o.contains(e) || e.contains(o))) return; seen.add(e); e.setAttribute('data-vs-h', picks.length); picks.push({i: picks.length, kind, text: (e.innerText || '').trim().slice(0, 30)}); };
  for (const e of document.querySelectorAll('main a, main button, section a, section button, a[class*="btn" i], a[class*="button" i], button')) {
    if (picks.filter(p => p.kind === 'button').length >= 3) break;
    const s = getComputedStyle(e), r = e.getBoundingClientRect();
    if (vis(e) && r.height < 90 && r.width < 420 && (bg(e) || parseFloat(s.borderTopWidth) > 0) && !e.closest('nav,header,[role="dialog"]')) take(e, 'button');
  }
  for (const e of document.querySelectorAll('a[class*="card" i], [class*="card" i], article, li > a, a')) {
    if (picks.filter(p => p.kind === 'card').length >= 3) break;
    const r = e.getBoundingClientRect();
    if (vis(e) && r.width > 180 && r.height > 120 && r.width < innerWidth * .7 && e.querySelector('img,picture,h2,h3,h4,svg') && !e.closest('nav,header,[role="dialog"]')) take(e, 'card');
  }
  return picks;
}
"""

HOVER_STATE_JS = r"""
(i) => { const e = document.querySelector('[data-vs-h="' + i + '"]'); if (!e) return null;
  const pick = x => { const s = getComputedStyle(x); return {transform: s.transform, 'background-color': s.backgroundColor, color: s.color, 'box-shadow': s.boxShadow, opacity: s.opacity,
    'border-color': s.borderTopColor, 'text-decoration': s.textDecorationLine, filter: s.filter, translate: s.translate, scale: s.scale}; };
  const s = getComputedStyle(e), img = e.querySelector('img,picture,video'), arrow = e.querySelector('svg,[class*="arrow" i],[class*="icon" i]');
  const d = s.transitionDuration.split(',').map(x => x.trim().endsWith('ms') ? parseFloat(x) / 1000 : parseFloat(x) || 0);
  return {self: pick(e), image: img ? pick(img) : null, arrow: arrow ? pick(arrow) : null, duration: Math.max(...d), easing: s.transitionTimingFunction.split(/,(?![^(]*\))/)[0].trim()}; }
"""

def _kf_from_css(css_texts, have):
    """Keyframes from the stylesheets the browser would not let the page read (other origins)."""
    out = {}
    for text in css_texts.values():
        for m in re.finditer(r"@(?:-webkit-)?keyframes\s+([\w-]+)\s*\{", text):
            name = m.group(1)
            if name in have or name in out or len(out) >= 150: continue
            depth, i = 1, m.end()
            while i < len(text) and depth:
                depth += {"{": 1, "}": -1}.get(text[i], 0); i += 1
            props = {}
            for key, block in re.findall(r"([\w%.,\s]+)\{([^{}]*)\}", text[m.end():i - 1]):
                for decl in block.split(";"):
                    if ":" in decl:
                        p, v = decl.split(":", 1); props.setdefault(p.strip().lower(), []).append(key.strip() + " " + v.strip()[:80])
            out[name] = props
    return out

def _does(props):
    """What a keyframe animation does, in plain words, from the properties it changes."""
    does, values = [], " ".join(" ".join(v) for v in props.values()).lower()
    if "opacity" in props: does.append("fade")
    if any(p in props for p in ("transform", "translate")):
        if re.search(r"translatey\(|translate3d\(\s*0(px|%)?\s*,\s*-?[1-9.]|translate\(\s*0(px|%)?\s*,\s*-?[1-9.]", values) or ("translate" in props and re.search(r"\s0(px|%)?\s+-?[1-9.]", " ".join(props.get("translate", [])))): does.append("rise")
        if re.search(r"translatex\(|translate3d\(\s*-?[1-9.]|translate\(\s*-?[1-9.]", values): does.append("slide")
    if "scale" in props or re.search(r"scale(3d|x|y)?\(", values): does.append("scale")
    if "rotate" in props or re.search(r"rotate(3d|x|y|z)?\(", values): does.append("rotate")
    if "clip-path" in props or any(p.startswith("mask") or p.startswith("-webkit-mask") for p in props): does.append("mask")
    if any(p in props for p in ("width", "height", "max-height", "max-width", "inset", "left", "right", "top", "bottom")): does.append("grow or move a box")
    if "stroke-dashoffset" in props or "stroke-dasharray" in props: does.append("draw a line")
    if "blur(" in values: does.append("blur")
    if "background-position" in props or "background-position-x" in props: does.append("shift a background")
    if any(p in props for p in ("color", "background-color", "border-color", "fill", "stroke", "box-shadow")): does.append("change colour")
    return does or ["other"]

def _weighted(counts, n=6, skip=()):
    items = sorted(((k, v) for k, v in counts.items() if k not in skip), key=lambda kv: -kv[1])[:n]
    return [{"value": (float(k) if re.fullmatch(r"[\d.]+", str(k)) else k), "weight": v} for k, v in items]

def _wmedian(counts):
    pairs = sorted((float(k), v) for k, v in counts.items()); total = sum(v for _, v in pairs); run = 0
    for k, v in pairs:
        run += v
        if run * 2 >= total: return k
    return None

def _clean_ease(e):
    e = re.sub(r"\s+", "", str(e or ""))
    e = re.sub(r"(?<![\d.])0\.", ".", e)
    return {"cubic-bezier(.25,.1,.25,1)": "ease", "cubic-bezier(0,0,1,1)": "linear", "cubic-bezier(.42,0,1,1)": "ease-in", "cubic-bezier(0,0,.58,1)": "ease-out", "cubic-bezier(.42,0,.58,1)": "ease-in-out"}.get(e, e)

def read_motion(ctx, url, census, css_texts, shape=None):
    """How the site moves: measured facts (raw/motion.json) and a drafted motion profile for brand.json.
    census: results of MOTION_CENSUS_JS per page read. The reveal and hover sampling opens the home page once more,
    because the first visit has already scrolled through it."""
    import motion as M
    notes = []
    t, te, tp, anims, kf, libs, videos, hints, blocked = {}, {}, {}, {}, {}, [], [], {}, 0
    for c in census:
        for k, v in c.get("transitions", {}).items(): t[k] = t.get(k, 0) + v
        for k, v in c.get("transition_easings", {}).items(): te[_clean_ease(k)] = te.get(_clean_ease(k), 0) + v
        for k, v in c.get("transition_properties", {}).items(): tp[k] = tp.get(k, 0) + v
        for a in c.get("animations", []):
            key = (a["name"], a["duration"], a["easing"], a["iterations"])
            if key in anims: anims[key]["count"] += a["count"]; anims[key]["width"] = max(anims[key]["width"], a["width"])
            else: anims[key] = dict(a)
        kf.update(c.get("keyframes", {})); blocked += c.get("sheets_blocked", 0)
        libs += [l for l in c.get("libraries", []) if l not in libs]; videos += c.get("videos", [])
        for k, v in c.get("hints", {}).items(): hints[k] = max(hints.get(k, 0), int(v))
    kf.update(_kf_from_css(css_texts, kf))
    in_use = []
    for a in sorted(anims.values(), key=lambda a: -a["count"]):
        a = dict(a, easing=_clean_ease(a["easing"]), does=_does(kf.get(a["name"], {})))
        a["kind"] = ("marquee" if a["iterations"] == "infinite" and "slide" in a["does"] and a["duration"] >= 4 and a["width"] >= 300 else
                     "spinner or loader" if a["iterations"] == "infinite" and a["width"] <= 80 else
                     "loop" if a["iterations"] == "infinite" else "entrance")
        in_use.append(a)
    marquees = [a for a in in_use if a["kind"] == "marquee"]
    used = {a["name"] for a in in_use}

    reveal, hover = {"sampled": 0, "waiting": 0, "revealed": 0, "found": False}, {"buttons": [], "cards": []}
    try:
        pg = ctx.new_page()
        pg.goto(url, wait_until="domcontentloaded", timeout=45000)
        try: pg.wait_for_load_state("networkidle", timeout=10000)
        except Exception: pass
        try: pg.evaluate(CONSENT_JS); pg.wait_for_timeout(600); pg.evaluate(HIDE_CONSENT_JS)
        except Exception: pass
        pg.wait_for_timeout(900)
        # hover first, at the top of the page, before anything has been scrolled
        try:
            for pick in pg.evaluate(HOVER_PICK_JS):
                before = pg.evaluate(HOVER_STATE_JS, pick["i"])
                try: pg.locator(f'[data-vs-h="{pick["i"]}"]').first.hover(timeout=1500, force=True)
                except Exception: continue
                pg.wait_for_timeout(520)
                after = pg.evaluate(HOVER_STATE_JS, pick["i"])
                if not before or not after: continue
                changes = [f"{part if part != 'self' else ''} {k}".strip() for part in ("self", "image", "arrow") if before.get(part) and after.get(part)
                           for k in before[part] if before[part][k] != after[part][k]]
                moves = [c for c in changes if any(w in c for w in ("transform", "translate", "scale"))]
                hover["buttons" if pick["kind"] == "button" else "cards"].append(
                    {"text": pick["text"], "changes": changes, "moves": bool(moves), "duration": before["duration"], "easing": _clean_ease(before["easing"])})
            pg.mouse.move(2, 2)
        except Exception as e:
            notes.append("hover could not be sampled: " + str(e)[:80])
        b = pg.evaluate(REVEAL_JS, "before")
        pg.evaluate("async()=>{for(let y=0;y<document.documentElement.scrollHeight;y+=450){scrollTo(0,y);await new Promise(r=>setTimeout(r,260));}}")
        pg.wait_for_timeout(1300)
        a = pg.evaluate(REVEAL_JS, "after")
        pg.close()
        kinds, dist, durs, eases, rows, by_parent, driven = {}, [], [], {}, [], {}, {}
        for w in b["waiting"]:
            st = a.get(str(w["i"]))
            if not st or not st["rest"]: continue
            bf, k = w["before"], []
            if w["mask_parent"] or bf["clip"]: k.append("mask")
            else:
                if bf["ty"] > 3: k.append("rise"); dist.append(abs(bf["ty"]))
                elif bf["ty"] < -3: k.append("drop"); dist.append(abs(bf["ty"]))
                if abs(bf["tx"]) > 3: k.append("slide"); dist.append(abs(bf["tx"]))
            if abs(bf["scale"] - 1) > .015: k.append("scale")
            if bf["blur"]: k.append("blur")
            if bf["opacity"] < .15 or bf["hidden"]: k.append("fade")
            if not k: continue
            for x in k: kinds[x] = kinds.get(x, 0) + 1
            how = "css transition" if w["transition"] > 0 else ("css animation" if st.get("animation") else "script")
            driven[how] = driven.get(how, 0) + 1
            if w["transition"] > 0: durs.append(w["transition"]); eases[_clean_ease(w["easing"])] = eases.get(_clean_ease(w["easing"]), 0) + 1
            elif st.get("animation"):
                for an in in_use:
                    if an["name"] == st["animation"]: durs.append(an["duration"]); eases[an["easing"]] = eases.get(an["easing"], 0) + 1; break
            by_parent.setdefault(w["parent"], []).append(w["transition_delay"])
            if len(rows) < 14: rows.append({"element": (w["tag"] + "." + w["cls"].replace(" ", ".")).rstrip("."), "text": w["text"], "kinds": k, "before": {x: y for x, y in bf.items() if x not in ("h", "w")},
                                            "driven_by": how, "transition": w["transition"], "delay": w["transition_delay"], "easing": _clean_ease(w["easing"])})
        steps = []
        for delays in by_parent.values():
            d = sorted(set(round(x, 3) for x in delays))
            if len(d) >= 2: steps += [round(y - x, 3) for x, y in zip(d, d[1:]) if 0 < y - x < .6]
        timed = [x["takes"] for x in b.get("timed", []) if x["takes"] > .05]
        revealed = sum(1 for w in b["waiting"] if a.get(str(w["i"]), {}).get("rest"))
        reveal = {"found": revealed >= 3, "below_the_fold": b["below_the_fold"], "waiting": len(b["waiting"]), "revealed": revealed,
                  "kinds": dict(sorted(kinds.items(), key=lambda kv: -kv[1])), "distance_px": _median(dist) if dist else None,
                  "duration_s": round(_median(durs), 2) if durs else (round(_median(timed), 2) if timed else None), "measured_by_watching_s": timed,
                  "easing": max(eases, key=eases.get) if eases else None, "stagger_s": round(_median(steps), 3) if steps else None,
                  "siblings_revealed_together": max((len(v) for v in by_parent.values()), default=0), "driven_by": driven, "samples": rows}
    except Exception as e:
        notes.append("scroll reveal could not be sampled: " + str(e)[:100])

    bg_video = [v for v in videos if v.get("autoplay") and v.get("muted") and v.get("share_of_viewport", 0) >= .3]
    entrances = [a for a in in_use if a["kind"] in ("entrance", "loop") and a["width"] > 80 and a["duration"] > 0]
    hover_moves = sum(1 for h in hover["buttons"] + hover["cards"] if h["moves"])
    heavy = [l for l in libs if l in ("GSAP", "GSAP ScrollTrigger", "Three.js", "Lottie", "Rive", "Framer Motion", "Locomotive Scroll", "Lenis", "anime.js", "Barba", "Swup", "SplitType or SplitText", "Webflow interactions")]
    score = (2 if reveal.get("found") else 0) + (1 if entrances else 0) + (1 if marquees or hints.get("marquee_tags") else 0) + (1 if bg_video else 0) + min(2, len(heavy)) + (1 if len(reveal.get("kinds", {})) >= 3 else 0)
    amount = "none" if score == 0 and not t else "hover only" if score == 0 else "little" if score <= 1 else "some" if score <= 3 else "much"

    # ---- the drafted profile: a set that matches what was seen, tokens from what was measured
    kinds = reveal.get("kinds") or {}
    all_does = [d for a in entrances for d in a["does"]]
    ease_pool = {k: v for k, v in te.items() if k not in ("ease", "linear", "ease-in-out", "ease-out", "ease-in") and not k.startswith("steps")}
    site_ease = reveal.get("easing") if reveal.get("easing") not in (None, "ease", "linear") else (max(ease_pool, key=ease_pool.get) if ease_pool and max(ease_pool.values()) >= max(3, sum(te.values()) * .05) else None)
    overshoot = bool(site_ease and (m := re.match(r"cubic-bezier\(([-\d.]+),([-\d.]+),([-\d.]+),([-\d.]+)\)", site_ease)) and (float(m.group(2)) > 1.05 or float(m.group(4)) > 1.05))
    stepped = sum(v for k, v in te.items() if k.startswith("steps")) > sum(te.values()) * .3 if te else False
    radius = (shape or {}).get("radius") or 0
    if amount in ("none", "hover only"):
        name, why = "rise", f"the site shows no movement of its own ({'only hover states' if amount == 'hover only' else 'no transitions, no animations'}), so the deck gets the calm default: short fades and rises, slides change with a fade"
    elif stepped:
        name, why = "cut", "most transitions on the site use stepped timing: things switch instead of easing"
    elif kinds.get("mask", 0) >= max(2, sum(kinds.values()) * .25) or all_does.count("mask") >= 2:
        name, why = "mask", f"elements on the site are uncovered by masks ({kinds.get('mask', 0)} of the scroll reveals, {all_does.count('mask')} keyframe animations clip or mask)"
    elif (kinds.get("scale", 0) + kinds.get("blur", 0)) >= max(2, sum(kinds.values()) * .3):
        name, why = "soft", f"scroll reveals on the site scale or come into focus ({kinds.get('scale', 0)} scale, {kinds.get('blur', 0)} blur)"
    elif all_does.count("draw a line") >= 2 and not kinds:
        name, why = "draw", "the site draws lines (stroke animations) and reveals little else"
    elif reveal.get("found") and (overshoot or ((reveal.get("distance_px") or 0) >= 60 and (reveal.get("stagger_s") or 0) > 0) or (amount == "much" and marquees and (reveal.get("distance_px") or 0) >= 40)):
        name, why = "cascade", ("the site's reveals overshoot (" + site_ease + ")" if overshoot else f"reveals travel far ({reveal.get('distance_px')} px) and the site is busy (marquee, staggered groups)")
    elif reveal.get("found") and (kinds.get("rise", 0) or kinds.get("fade", 0)):
        soft = radius >= 14 and not kinds.get("rise")
        name = "soft" if soft else "rise"
        why = (f"the site fades elements in while scrolling ({kinds.get('fade', 0)} of {reveal['revealed']}) and its shapes are round (radius {radius} px)" if soft else
               f"elements on the site fade in and rise while scrolling ({kinds.get('rise', 0)} rise, {kinds.get('fade', 0)} fade of {reveal['revealed']} sampled" +
               (f", about {reveal['distance_px']:g} px" if reveal.get("distance_px") else "") + ")" if kinds.get("rise") else
               f"elements on the site fade in while scrolling without travelling ({kinds.get('fade', 0)} of {reveal['revealed']} sampled), so the rise is kept very short")
    elif kinds.get("slide"):
        name, why = "rise", f"the site slides elements in sideways ({kinds['slide']} sampled); rise is the closest quiet set, consider cascade if the brand is lively"
    else:
        name, why = "rise", f"the site moves ({amount}: " + ", ".join(filter(None, [f"{len(entrances)} keyframe animations in use" if entrances else "", "marquee" if marquees else "", "background video" if bg_video else "", ", ".join(heavy)])) + ") but no scroll reveal could be sampled, so the quiet set is the safe draft; look at the site and at the film strips"
    if name == "rise" and amount == "much" and heavy:
        why += f"; the site is busier than this sample shows ({', '.join(heavy)}), so also compare cascade, mask and sweep in the film strips"
    base = M.sets().get(name, {}).get("tokens", dict(M.TOKENS))
    tokens, measured = dict(base), []
    if site_ease and re.match(r"cubic-bezier", site_ease) and name not in ("cut",) and (name == "cascade" or not overshoot):
        tokens["ease"] = site_ease; measured.append("ease")
    d = reveal.get("duration_s")
    if d and .2 <= d <= 2: tokens["duration"] = round(min(1.2, max(.35, d)), 2); measured.append("duration")
    elif t and amount not in ("none", "hover only"):
        ui = _wmedian(t)                                    # interface transitions are short; an entrance on a slide takes about twice as long
        if ui: tokens["duration"] = round(min(1.0, max(.4, ui * 2.2)), 2); measured.append("duration (from interface transitions)")
    if reveal.get("stagger_s"): tokens["stagger"] = round(min(.25, max(.04, reveal["stagger_s"])), 3); measured.append("stagger")
    if reveal.get("distance_px") and name in ("rise", "cascade", "sweep"): tokens["travel"] = int(min(80, max(8, reveal["distance_px"]))); measured.append("travel")
    elif name == "rise" and reveal.get("found") and not kinds.get("rise"): tokens["travel"] = 10
    if any(l in libs for l in ("Swiper", "Splide", "Slick", "Flickity", "Embla")) and name in ("rise", "cascade") and amount in ("some", "much"): tokens["change"] = "slide"
    profile = dict(set=name, **tokens)
    facts = {"_about": "How the website moves, measured at 1440 px width. transitions and their easings are counted once per element that carries them (the weight). "
                       "animations.in_use are keyframe animations running on elements, with what their keyframes change (frames: the keyframes themselves, for entrances). scroll_reveal compares elements below the fold before and after "
                       "they were scrolled into view. hover lists what changed on up to three buttons and three cards. suggestion is the drafted motion profile, with the reason.",
             "pages": [c.get("url") for c in census if c.get("url")], "amount": amount,
             "transitions": {"elements_with_transition": sum(t.values()), "durations_s": _weighted(t), "easings": _weighted(te), "properties": _weighted(tp, 8)},
             "animations": {"in_use": [dict({k: a[k] for k in ("name", "kind", "does", "duration", "easing", "iterations", "count", "on")},
                                              **({"frames": kf[a["name"]]} if a["kind"] == "entrance" and kf.get(a["name"]) else {})) for a in in_use[:24]],
                            "keyframes_defined": len(kf), "keyframes_unused_sample": [{"name": n, "does": _does(p)} for n, p in list(kf.items()) if n not in used][:20],
                            "stylesheets_not_readable_in_page": blocked},
             "scroll_reveal": reveal, "hover": hover,
             "marquees": [{"name": a["name"], "duration": a["duration"], "on": a["on"]} for a in marquees] + ([{"name": "<marquee> element"}] if hints.get("marquee_tags") else []),
             "marquee_like_class_names": hints.get("marquee_classes", 0),
             "background_video": [{k: v[k] for k in ("share_of_viewport", "loop", "top")} for v in bg_video], "videos_on_page": len(videos),
             "libraries": libs, "canvas_elements": hints.get("canvas", 0), "sticky_elements": hints.get("sticky", 0),
             "smooth_scroll": any(c.get("smooth_scroll") for c in census) or "Lenis" in libs or "Locomotive Scroll" in libs,
             "css_scroll_timeline": any(c.get("scroll_timeline") for c in census),
             "suggestion": {"set": name, "tokens": tokens, "measured": measured, "why": why}, "notes": notes}
    rv = (f"reveal {'+'.join(list(kinds)[:3])} ({reveal.get('revealed')} of {reveal.get('waiting')} waiting"
          + (f", {reveal['distance_px']:g} px" if reveal.get("distance_px") else "") + (f", {reveal['duration_s']:g} s" if reveal.get("duration_s") else "") + ")") if reveal.get("found") else "no scroll reveal"
    top_t = _weighted(t, 1); top_e = _weighted(te, 1)
    summary = (f"motion: {amount} | {rv} | transitions {str(top_t[0]['value']) + ' s ' + str(top_e[0]['value']) if top_t and top_e else 'none'} on {sum(t.values())} elements"
               f" | keyframe animations in use {len(entrances)} | hover moves {hover_moves} of {len(hover['buttons']) + len(hover['cards'])}"
               f" | marquee {len(facts['marquees'])} | background video {len(bg_video)} | libraries {', '.join(libs) or 'none'}")
    return facts, profile, summary


# ---------------------------------------------------------------- main

VIDEOS_JS = """() => [...document.querySelectorAll('video')].map((v, i) => { const r = v.getBoundingClientRect();
  const srcs = [v.currentSrc, v.src, ...[...v.querySelectorAll('source')].map(s => s.src)].filter(Boolean);
  return {i, srcs: [...new Set(srcs)], poster: v.poster || '', w: v.videoWidth, h: v.videoHeight, seconds: isFinite(v.duration) ? Math.round(v.duration) : null,
          autoplay: v.autoplay, muted: v.muted, loop: v.loop, share: Math.min(1, (r.width * r.height) / (innerWidth * innerHeight))}; })"""

def fetch_videos(url, root, limit=3, max_mb=60):
    """Save the website's own video files into videos/ and list them in brand.json under "videos".
    Only plain files the page itself plays (mp4, webm, mov) are taken, up to max_mb each; streams, players
    (YouTube, Vimeo) and blob sources are left alone. A video that runs silently in a loop behind a large part
    of the page is marked "background": that is the one for chapter and photo slides. Returns the list."""
    from playwright.sync_api import sync_playwright
    if not re.match(r"https?://", url): url = "https://" + url
    os.makedirs(os.path.join(root, "videos"), exist_ok=True)
    out, seen = [], set()
    with sync_playwright() as p:
        br = p.chromium.launch()
        ctx = br.new_context(viewport={"width": 1440, "height": 900},
                             user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0 Safari/537.36 vibeupslides-brand-reader")
        pg = ctx.new_page()
        try:
            pg.goto(url, wait_until="domcontentloaded", timeout=45000)
            try: pg.wait_for_load_state("networkidle", timeout=12000)
            except Exception: pass
            try:
                if pg.evaluate(CONSENT_JS): pg.wait_for_timeout(900)
                pg.evaluate(HIDE_CONSENT_JS)
            except Exception: pass
            pg.evaluate("async()=>{for(let y=0;y<document.body.scrollHeight;y+=700){scrollTo(0,y);await new Promise(r=>setTimeout(r,150));}scrollTo(0,0);}")
            pg.wait_for_timeout(1200)
            found = pg.evaluate(VIDEOS_JS)
        except Exception as e:
            print("  could not read", url, "-", str(e)[:120]); found = []
        for v in sorted(found, key=lambda v: -v.get("share", 0)):
            if len(out) >= limit: break
            src = next((s for s in v["srcs"] if re.match(r"https?://", s) and os.path.splitext(urlparse(s).path)[1].lower() in (".mp4", ".webm", ".mov", ".m4v")), None)
            if not src or src in seen: continue
            seen.add(src)
            try:
                size = 0
                try: size = int(ctx.request.head(src, timeout=20000).headers.get("content-length") or 0)
                except Exception: pass
                if size > max_mb * 1024 * 1024:
                    print(f"  video left out, {size / 1048576:.0f} MB is over the limit of {max_mb} MB: {src}"); continue
                r = ctx.request.get(src, timeout=180000)
                body = r.body() if r.ok else b""
                if len(body) < 20000 or len(body) > max_mb * 1024 * 1024: continue
                ext = os.path.splitext(urlparse(src).path)[1].lower()
                fn = f"videos/video_{len(out) + 1:02d}{ext}"
                open(os.path.join(root, fn), "wb").write(body)
                item = {"file": fn, "width": v.get("w") or None, "height": v.get("h") or None, "seconds": v.get("seconds"),
                        "background": bool(v.get("autoplay") and v.get("muted") and v.get("share", 0) >= .3), "source": src}
                poster = None
                if v.get("poster") and re.match(r"https?://", v["poster"]):
                    try:
                        pr = ctx.request.get(v["poster"], timeout=30000)
                        if pr.ok and len(pr.body()) > 4000:
                            pe = os.path.splitext(urlparse(v["poster"]).path)[1].lower()
                            poster = fn[:-len(ext)] + (pe if pe in (".jpg", ".jpeg", ".png") else ".jpg")
                            open(os.path.join(root, poster), "wb").write(pr.body())
                    except Exception: pass
                if not poster:                              # no poster on the site: a frame of the video as it stands on the page
                    try:
                        el = pg.locator("video").nth(v["i"]); el.scroll_into_view_if_needed(timeout=3000); pg.wait_for_timeout(600)
                        poster = fn[:-len(ext)] + ".jpg"
                        el.screenshot(path=os.path.join(root, poster), type="jpeg", quality=86, timeout=8000)
                    except Exception:
                        poster = None
                if poster: item["poster"] = poster
                out.append(item)
                print(f"  video saved: {fn} ({len(body) / 1048576:.1f} MB" + (", background loop" if item["background"] else "") + ")")
            except Exception as e:
                print("  video could not be saved:", src, "-", str(e)[:100])
        br.close()
    bj = os.path.join(root, "brand.json")
    if os.path.exists(bj):
        data = json.load(open(bj, encoding="utf-8")); data["videos"] = out
        json.dump(data, open(bj, "w", encoding="utf-8"), indent=2, ensure_ascii=False)
    print("videos:", len(out), "of", len(found), "on the page" + ("" if out or not found else " (none is a plain file that can be saved)"))
    return out


def extract(url, name=None, pages=4, fonts=True, out=None, max_images=12):
    from playwright.sync_api import sync_playwright
    if not re.match(r"https?://", url): url = "https://" + url
    host = urlparse(url).netloc.replace("www.", "")
    slug = slugify(name or host.split(".")[0])
    root = out or os.path.join(B.home(), "brands", slug)
    for d in ("logos", "fonts", "images", "raw/screens"):
        os.makedirs(os.path.join(root, d), exist_ok=True)
    font_bodies, css_texts, measured = {}, {}, []
    comps, look_notes, shots = [], [], []                 # look and feel: one measurement per page, home first
    motion_census, motion_facts, motion_profile, motion_line = [], None, None, ""      # how the site moves
    el_files, el_facts, icon_stroke, icon_style = {"icon": [], "arrow": [], "shape": []}, {}, None, None

    def on_response(resp):
        try:
            rt = resp.request.resource_type
            if rt == "font" and resp.ok: font_bodies[resp.url] = resp.body()
            elif rt == "stylesheet" and resp.ok: css_texts[resp.url] = resp.text()
        except Exception:
            pass

    with sync_playwright() as p:
        br = p.chromium.launch()
        ctx = br.new_context(viewport={"width": 1440, "height": 900}, device_scale_factor=2,
                             user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0 Safari/537.36 vibeupslides-brand-reader")
        pg = ctx.new_page(); pg.on("response", on_response)

        def visit(u, tag):
            try:
                pg.goto(u, wait_until="domcontentloaded", timeout=45000)
                try: pg.wait_for_load_state("networkidle", timeout=12000)
                except Exception: pass
                try:
                    said = pg.evaluate(CONSENT_JS)
                    if said: pg.wait_for_timeout(900)
                    hidden = pg.evaluate(HIDE_CONSENT_JS)
                    if tag == "home" and (said or hidden): print(f"  consent banner: {'declined (' + said + ')' if said else 'not answered'}, {hidden} overlay(s) hidden")
                except Exception: pass
                pg.evaluate("async()=>{for(let y=0;y<document.body.scrollHeight;y+=700){scrollTo(0,y);await new Promise(r=>setTimeout(r,120));}scrollTo(0,0);}")
                pg.wait_for_timeout(700)
                data = pg.evaluate(MEASURE_JS)
            except Exception as e:
                print("  could not read", u, "-", str(e)[:120]); return None
            data["tag"] = tag
            try: motion_census.append(dict(pg.evaluate(MOTION_CENSUS_JS), url=data.get("url")))
            except Exception as e: look_notes.append(f"{tag}: motion could not be measured: " + str(e)[:100])
            try: comp = pg.evaluate(COMPONENTS_JS, True)
            except Exception as e: comp = {"url": data.get("url"), "notes": ["component capture failed: " + str(e)[:120]]}
            if tag == "home":                            # icons kept in an svg sprite, also one the page loads by script
                try: comp["sprite"] = pg.evaluate(SPRITE_JS, 400)
                except Exception as e: look_notes.append("svg sprite could not be read: " + str(e)[:100])
            look_notes.extend(f"{tag}: {n}" for n in comp.get("notes") or [])
            comps.append(comp)
            pg.screenshot(path=os.path.join(root, "raw/screens", f"{tag}.png"))
            if tag == "home":
                try: pg.screenshot(path=os.path.join(root, "raw/screens", "home_full.png"), full_page=True, clip=None)
                except Exception: pass
            return data

        print("reading", url)
        home = visit(url, "home")
        if not home:
            br.close(); raise SystemExit("The site could not be read.")
        measured.append(home)

        # logos are taken from the home page while it is still open
        logos = []
        for lg in home["logos"]:
            base = f"logo_{lg['where']}_{lg['k']}"
            rec = dict(lg); rec.pop("markup", None)
            try:
                if lg["svg"]:
                    markup = lg["markup"]
                    if "currentColor" in markup and lg.get("color"): markup = markup.replace("currentColor", lg["color"])
                    if 'xmlns="http://www.w3.org/2000/svg"' not in markup: markup = markup.replace("<svg", '<svg xmlns="http://www.w3.org/2000/svg"', 1)
                    open(os.path.join(root, "logos", base + ".svg"), "w", encoding="utf-8").write(markup); rec["file"] = f"logos/{base}.svg"
                else:
                    r = ctx.request.get(lg["src"])
                    ext = os.path.splitext(urlparse(lg["src"]).path)[1].lower() or ".png"
                    if ext not in (".png", ".svg", ".jpg", ".jpeg", ".webp", ".gif"): ext = ".png"
                    if r.ok:
                        open(os.path.join(root, "logos", base + ext), "wb").write(r.body()); rec["file"] = f"logos/{base}{ext}"
                el = pg.locator(f'[data-vs-logo="{lg["k"]}"]').first
                el.screenshot(path=os.path.join(root, "logos", base + "_shot.png"), omit_background=True); rec["shot"] = f"logos/{base}_shot.png"
            except Exception as e:
                rec["error"] = str(e)[:100]
            logos.append(rec)

        # favicon and social image
        icon_file = None
        icons = sorted(home["icons"], key=lambda i: (("apple" in i["rel"]) * 2 + ("svg" in i["type"]) * 1 + (("192" in i["sizes"]) or ("180" in i["sizes"])) * 3), reverse=True)
        for ic in icons + [{"href": urljoin(url, "/favicon.ico")}]:
            try:
                r = ctx.request.get(ic["href"])
                if r.ok and len(r.body()) > 100:
                    ext = os.path.splitext(urlparse(ic["href"]).path)[1].lower() or ".png"
                    path = os.path.join(root, "logos", "icon" + ext); open(path, "wb").write(r.body())
                    if ext == ".ico":
                        from PIL import Image
                        im = Image.open(path); im.save(os.path.join(root, "logos", "icon.png")); ext = ".png"
                    icon_file = "logos/icon" + ext; break
            except Exception:
                continue

        # close-ups of single components, while the home page is still open
        try: shoot_components(pg, root, comps[0], look_notes, shots, first=True)
        except Exception as e: look_notes.append("component screenshots failed: " + str(e)[:100])

        # a few more pages from the navigation, for a broader sample of colours, copy and photos
        seen = {home["url"].rstrip("/"), url.rstrip("/")}
        prefer = re.compile(r"about|ueber|über|company|unternehmen|product|produkt|service|leistung|team|story|mission|program|angebot", re.I)
        links = sorted([l for l in home["links"] if l.rstrip("/") not in seen], key=lambda l: (not prefer.search(l), len(l)))
        for i, link in enumerate(links[:max(0, pages - 1)]):
            before = len(comps)
            d = visit(link, f"page{i + 1}")
            if d: measured.append(d); seen.add(link.rstrip("/"))
            if d and len(comps) > before and len(shots) < 10:       # components the home page did not show
                try: shoot_components(pg, root, comps[-1], look_notes, shots, first=False)
                except Exception as e: look_notes.append("component screenshots failed: " + str(e)[:100])

        # photos
        imgs, picked = {}, []
        for d in measured:
            for im in d["images"]:
                if im["src"].startswith("data:"): continue
                imgs[im["src"]] = max(imgs.get(im["src"], 0), im["area"])
        for src, _ in sorted(imgs.items(), key=lambda kv: -kv[1])[:max_images]:
            try:
                r = ctx.request.get(src)
                if not r.ok or len(r.body()) < 8000: continue
                ext = os.path.splitext(urlparse(src).path)[1].lower()
                if ext not in (".jpg", ".jpeg", ".png", ".webp", ".avif"): ext = ".jpg"
                fn = f"images/photo_{len(picked) + 1:02d}{ext}"
                open(os.path.join(root, fn), "wb").write(r.body())
                if ext in (".webp", ".avif"):          # convert for the build step
                    try:
                        from PIL import Image
                        Image.open(os.path.join(root, fn)).convert("RGB").save(os.path.join(root, fn[:-len(ext)] + ".jpg"), quality=88)
                        os.remove(os.path.join(root, fn)); fn = fn[:-len(ext)] + ".jpg"
                    except Exception: pass
                picked.append({"file": fn, "source": src})
            except Exception:
                continue

        # icons, arrows and shapes the site draws as svg, with a contact sheet
        try: el_files, el_facts, icon_stroke, icon_style = save_elements(ctx, root, comps, look_notes)
        except Exception as e: look_notes.append("svg elements could not be saved: " + str(e)[:100])
        try:                                             # motion: transitions and animations in use, scroll reveals, hover, libraries
            card_radii = sorted(float(m.group(1)) for d in measured for c in d["styles"]["card"] + d["styles"]["img"] if (m := re.match(r"([\d.]+)px", c.get("borderRadius") or ""))) or [0]
            motion_facts, motion_profile, motion_line = read_motion(ctx, url, motion_census, css_texts, {"radius": card_radii[len(card_radii) // 2]})
        except Exception as e: look_notes.append("motion could not be read: " + str(e)[:120])
        br.close()

    # ---------------- fonts: classified by licence situation, only open ones are embedded
    faces = []
    for css_url, css in css_texts.items(): faces += [dict(f, css=css_url) for f in parse_font_faces(css, css_url)]
    for d in measured:
        for block in d["fontFaces"]: faces += [dict(f, css=d["url"]) for f in parse_font_faces(block, d["url"])]
    st = home["styles"]
    body_stack = (st["p"] or st["body"] or [{}])[0].get("fontFamily", "")
    head_el = (st["h1"] or st["h2"] or st["h3"] or [{}])[0]
    head_stack = head_el.get("fontFamily", body_stack)
    body_family, head_family = first_family(body_stack), first_family(head_stack)
    wanted = {f for f in (body_family, head_family) if f}
    font_use = {}
    for c in comps:
        for fam, u in (c.get("fontUse") or {}).items():
            t = font_use.setdefault(fam, {"chars": 0, "size": 0, "code": 0, "mono": u.get("mono"), "stack": u.get("stack", "")})
            t["size"] = round((t["size"] * t["chars"] + u["size"] * u["chars"]) / max(t["chars"] + u["chars"], 1)); t["chars"] += u["chars"]; t["code"] += u.get("code", 0)
    declared = [f for d in measured for f in d["fonts"]]
    try:
        heading_use = {}
        for c in comps:
            for h in c.get("headings") or []: heading_use[h.get("family")] = heading_use.get(h.get("family"), 0) + 1
        roles = font_roles(body_family, head_family, body_stack, head_stack, font_use, faces, declared, heading_use)
        font_families, font_files, font_pending, weights = classify_fonts(root, roles, faces, font_bodies, declared, save=fonts)
    except Exception as e:
        font_families, font_files, font_pending, weights = [], [], [], {}
        look_notes.append("fonts could not be classified: " + str(e)[:100])
    for f in home["fonts"]:            # weights the page actually used, also for fonts we could not download
        if f["family"] in wanted and f["status"] == "loaded":
            weights.setdefault("_used_" + f["family"], set()).update(_weight_num(f["weight"]))

    def nearest(family, target):
        have = sorted(weights.get(family) or weights.get("_used_" + (family or ""), []) or [400, 700])
        return min(have, key=lambda w: (abs(w - target), -w))
    hf = head_family or body_family
    h1_weight = int(float(head_el.get("fontWeight") or 700))
    h2_weight = int(float(((st["h2"] or [head_el])[0]).get("fontWeight") or h1_weight))
    display_weight = nearest(hf, max(h1_weight, 700))
    head_weight = nearest(hf, min(max(h2_weight, 500), display_weight))

    # ---------------- shape
    def px(v):
        m = re.match(r"([\d.]+)px", v or ""); return float(m.group(1)) if m else 0.0
    btn = [b for d in measured for b in d["styles"]["button"] if b.get("background") or b.get("borderColor")]
    radii = sorted(min(px(b["borderRadius"]), b["height"] / 2 if b.get("height") else 999) for b in btn) or [0]
    card_r = sorted(px(c["borderRadius"]) for d in measured for c in d["styles"]["card"] + d["styles"]["img"]) or [0]
    radius = round(min(card_r[len(card_r) // 2] or radii[len(radii) // 2], 28))
    ls = head_el.get("letterSpacing", "normal"); fs = head_el.get("fontSize") or 48
    tracking = None if ls in ("normal", "", None) else f"{px(ls) / fs if 'px' in ls else 0:.3f}em"
    if tracking and re.match(r"-?0\.000em", tracking): tracking = None
    head_case = head_el.get("textTransform") if head_el.get("textTransform") in ("uppercase", "lowercase") else "none"
    motif = "wedge" if radius <= 4 else "block"

    copy_site = (home["copy"].get("siteName") or "")
    # ---------------- logos: best header logo, an inverse if the site shows one on a dark ground
    site_words = {w for w in re.split(r"[^a-z0-9]+", (copy_site + " " + host.split(".")[0]).lower()) if len(w) > 2}
    def score(l):
        alt = (l.get("alt") or "").lower() + " " + (l.get("src") or "").lower()
        same_name = any(w in alt for w in site_words)
        return ((l["where"] == "header") * 4 + l["named"] * 2 + l["linked"] * 4 + same_name * 3 - l.get("wall", False) * 6
                - (l["top"] > 700 and l["where"] != "footer") * 2 - (l["where"] == "footer") * 1)
    usable = [l for l in logos if l.get("file") or l.get("shot")]
    usable.sort(key=score, reverse=True)
    primary = usable[0] if usable else None
    def logo_file(l): return l.get("file") or l.get("shot")
    inverse = None
    if primary:
        p_dark = B.luminance(primary["background"]) < .3
        ratio = primary["width"] / max(primary["height"], 1)
        for l in usable[1:]:          # the same mark on the opposite kind of ground: similar proportions, not part of a logo wall
            similar = abs(l["width"] / max(l["height"], 1) - ratio) / ratio < .3
            if (B.luminance(l["background"]) < .3) != p_dark and similar and not l.get("wall") and logo_file(l) != logo_file(primary):
                inverse = l; break
        if p_dark and inverse:        # the header itself is dark: the header logo is the inverse one
            primary, inverse = inverse, primary

    colors, notes, census = choose_colors(measured)
    copy0 = home["copy"]
    brand_name = copy0.get("siteName") or re.split(r"\s[|–—-]\s", copy0.get("title") or host)[0].strip() or host
    lang = (copy0.get("lang") or "en").split("-")[0].lower() or "en"
    brand = {
        "name": brand_name, "url": url, "lang": lang,
        "colors": colors,
        "fonts": {"body": {"family": body_family, "fallback": fallback_for(body_stack)},
                  "head": {"family": head_family if head_family != body_family else None, "fallback": fallback_for(head_stack)},
                  "files": font_files, "display_weight": display_weight, "head_weight": head_weight,
                  "pending": font_pending, "families": font_families},
        "shape": {"radius": radius, "motif": motif, "head_case": head_case, "head_tracking": tracking, "logo_position": "right"},
        "logo_candidates": [{"file": logo_file(l), "where": l["where"], "on": l["background"], "alt": l.get("alt", ""), "wall": l.get("wall", False)} for l in usable[:8]],
        "logos": {"primary": logo_file(primary) if primary else None, "primary_inverse": logo_file(inverse) if inverse else None,
                  "partner": None, "partner_inverse": None, "icon": icon_file, "inverse_mode": "file" if inverse else "plate"},
        "footer": {"left": "", "right": host},
        "images": picked,
        "elements": {"icons": el_files["icon"], "arrows": el_files["arrow"], "shapes": el_files["shape"], "arrow_glyph": None, "icon_style": icon_style, "icon_stroke_width": icon_stroke},
    }
    # ---------------- look and feel: raw/components.json
    try:
        look = summarise_components(comps)
        top = next((g for g in look["arrows"]["glyphs"] if g["in_links"] + g["in_pseudo"] > 0), None) or next(iter(look["arrows"]["glyphs"]), None)
        brand["elements"]["arrow_glyph"] = top["glyph"] if top else None
        look["arrows"].update({"most_used_glyph": brand["elements"]["arrow_glyph"], "svg_files": el_files["arrow"]})
        look["icons"] = dict(el_facts, files=el_files["icon"])
        look = _strip_refs(look)
    except Exception as e:
        look = {}; look_notes.append("components could not be summarised: " + str(e)[:100])
    look = dict({"_about": "Look and feel measured at 1440 px width on the pages listed. Styles are grouped and counted, the most frequent first; a key that is absent means none or default. "
                           "Colours are #rrggbb, or #rrggbbaa when translucent. See raw/screens/components/ and raw/elements.png for the pictures.",
                 "pages": [c.get("url") for c in comps]}, **look, screens=shots, notes=look_notes)
    json.dump(look, open(os.path.join(root, "raw/components.json"), "w", encoding="utf-8"), indent=1, ensure_ascii=False)
    if os.environ.get("VIBEUPSLIDES_DEBUG"): json.dump(comps, open(os.path.join(root, "raw/components_raw.json"), "w", encoding="utf-8"), indent=1, ensure_ascii=False)
    for f in font_families:
        if f["status"] == "pending": notes.append(f"font {f['family']}: self-hosted files of unknown licence are in fonts/pending/, not embedded; move them to fonts/ and into fonts.files once the licence allows it")
        elif f["licence"] == "ask": notes.append(f"font {f['family']}: commercial or unknown licence, no files saved; decks use the fallback font until you supply files")
    if primary and not inverse: notes.append("no logo for dark backgrounds found: run `brand.py inverse` for a white version or keep inverse_mode 'plate'")
    if not primary: notes.append("no logo found: add one to logos/ and set logos.primary")
    if fonts and any(f["licence"] == "open" and f["status"] == "missing" for f in font_families): notes.append("font files could not be downloaded: decks use the fallback fonts until files are added to fonts/")
    if B.luminance(colors["paper"]) > .5 and primary and B.luminance(primary["background"]) < .3 and not inverse:
        notes.append("the only logo found sits on a dark header: it is probably the light version, check logos.primary")
    notes += B.brand_warnings(B._merge(B.DEFAULT_BRAND, brand))

    try:
        from PIL import Image, ImageDraw
        tiles = []
        for i, l in enumerate(usable[:8]):
            shot = l.get("shot")
            if not shot: continue
            im = Image.open(os.path.join(root, shot)).convert("RGBA"); im.thumbnail((360, 150))
            tile = Image.new("RGBA", (400, 220), l["background"]); tile.alpha_composite(im, ((400 - im.width) // 2, 20 + (150 - im.height) // 2))
            d = ImageDraw.Draw(tile); d.rectangle((0, 190, 400, 220), fill="#000000")
            d.text((8, 198), f"{i + 1}: {os.path.basename(logo_file(l))}  [{l['where']}]" + ("  wall" if l.get("wall") else ""), fill="#ffffff")
            tiles.append(tile)
        if tiles:
            sheet = Image.new("RGB", (800, 220 * ((len(tiles) + 1) // 2)), "#888888")
            for i, tl in enumerate(tiles): sheet.paste(tl.convert("RGB"), ((i % 2) * 400, (i // 2) * 220))
            sheet.save(os.path.join(root, "raw/logo_candidates.png"))
    except Exception as e:
        notes.append("logo contact sheet could not be drawn: " + str(e)[:80])
    if motion_profile:
        brand["motion"] = motion_profile
        json.dump(motion_facts, open(os.path.join(root, "raw/motion.json"), "w", encoding="utf-8"), indent=1, ensure_ascii=False)
        import motion as _M
        site_motion = _M.write_site_set(root, motion_facts, url)
    json.dump(brand, open(os.path.join(root, "brand.json"), "w", encoding="utf-8"), indent=2, ensure_ascii=False)
    raw = {"pages": measured, "logos": logos, "font_faces": faces, "font_urls": sorted(font_bodies), "census": census, "notes": notes}
    json.dump(raw, open(os.path.join(root, "raw/extract.json"), "w", encoding="utf-8"), indent=1, ensure_ascii=False)
    with open(os.path.join(root, "raw/copy.md"), "w", encoding="utf-8") as f:
        for d in measured:
            c = d["copy"]
            f.write(f"# {c['title']}\n{d['url']}\n\n{c['description']}\n\n")
            for key in ("h1", "h2", "h3", "nav", "buttons", "paragraphs"):
                if c.get(key):
                    f.write(f"## {key}\n" + "\n".join("- " + t for t in c[key]) + "\n\n")
    print("\nbrand folder:", root)
    print("name:", brand_name, "| language:", lang)
    print("colours:", ", ".join(f"{k} {v}" for k, v in colors.items()))
    print("fonts: body", body_family, "| headings", head_family, "| files", len(font_files), "| weights", display_weight, head_weight)
    print("shape: radius", radius, "| motif", motif, "| case", head_case, "| tracking", tracking)
    print("logos: primary", brand["logos"]["primary"], "| inverse", brand["logos"]["primary_inverse"], "| icon", icon_file, "| candidates", len(logos))
    print("photos:", len(picked), "| pages read:", len(measured))
    if look:
        print("look and feel:", len(look.get("buttons") or []), "button styles |", len(look.get("cards") or []), "card styles |", len(look.get("labels") or []), "label styles |",
              len((look.get("sections") or {}).get("sequence") or []), "sections | screenshots", len(shots))
    print("elements: icons", len(el_files["icon"]), "| arrows", len(el_files["arrow"]), "| shapes", len(el_files["shape"]), "| arrow glyph", brand["elements"]["arrow_glyph"],
          "| icon style", icon_style, f"(stroke {icon_stroke})" if icon_stroke else "")
    if motion_profile:
        print(motion_line)
        sug = motion_facts["suggestion"]
        print("NOTE (motion): suggested set " + motion_profile["set"] + " because " + sug["why"] + ". Tokens: " + ", ".join(f"{k} {v}" for k, v in sug["tokens"].items())
              + " (measured on the site: " + (", ".join(sug["measured"]) or "nothing, these are the set's own values") + "). See raw/motion.json and `vs.py motion <brand> --strip all`.")
        if site_motion:
            print("NOTE (motion): the way the website's own elements arrive was copied into a set of this brand, `site` (" + _M.sets(root)["site"]["character"] + "). "
                  "The user chooses between it and the framework's sets: `vs.py motion <brand> --compare` plays them side by side, `vs.py motion <brand> --set site` takes it.")
        else:
            print("NOTE (motion): the website shows no entrance that could be copied, so there is no `site` set; the user chooses among the framework's sets.")
    for n in notes: print("NOTE:", n)
    for n in look_notes: print("NOTE (look and feel):", n)
    print("FONTS")
    for f in font_families:
        print(f"  {f['family']} [{', '.join(f['roles'])}]: {f['status']} ({f['source']}, licence {f['licence']}, {f['files']} files) - {f['note']}")
    return root


if __name__ == "__main__":
    args = sys.argv[1:]
    if not args or args[0].startswith("-"):
        print(__doc__); sys.exit(1)
    opt = {"name": None, "pages": 4, "out": None}
    for i, a in enumerate(args):
        if a in ("--name", "--out"): opt[a[2:]] = args[i + 1]
        if a == "--pages": opt["pages"] = int(args[i + 1])
    extract(args[0], name=opt["name"], pages=opt["pages"], fonts="--no-fonts" not in args, out=opt["out"])
