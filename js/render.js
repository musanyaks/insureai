/* =====================================================
   render.js — builds the DOM from config.js + data.js
   (icons, then one render function per section)
===================================================== */

/* ---- inline icon set ---- */
const ICONS = {
  mail:   '<rect x="2" y="4" width="20" height="16" rx="2"/><path d="m22 6-10 7L2 6"/>',
  phone:  '<path d="M22 16.9v3a2 2 0 0 1-2.2 2 19.8 19.8 0 0 1-8.6-3.1 19.5 19.5 0 0 1-6-6A19.8 19.8 0 0 1 2.1 4.2 2 2 0 0 1 4.1 2h3a2 2 0 0 1 2 1.7c.1.9.3 1.8.6 2.6a2 2 0 0 1-.5 2.1L8 9.6a16 16 0 0 0 6 6l1.2-1.2a2 2 0 0 1 2.1-.5c.8.3 1.7.5 2.6.6a2 2 0 0 1 1.7 2z"/>',
  pin:    '<path d="M21 10c0 7-9 13-9 13s-9-6-9-13a9 9 0 0 1 18 0z"/><circle cx="12" cy="10" r="3"/>',
  code:   '<path d="M16 18l6-6-6-6M8 6l-6 6 6 6"/>',
  chart:  '<path d="M4 20V10M10 20V4M16 20v-8M22 20H2"/>',
  brain:  '<circle cx="5" cy="6" r="1.8" fill="currentColor" stroke="none"/><circle cx="5" cy="12" r="1.8" fill="currentColor" stroke="none"/><circle cx="5" cy="18" r="1.8" fill="currentColor" stroke="none"/><circle cx="12" cy="9" r="1.8" fill="currentColor" stroke="none"/><circle cx="12" cy="15" r="1.8" fill="currentColor" stroke="none"/><circle cx="19" cy="12" r="1.8" fill="currentColor" stroke="none"/><g stroke="currentColor" stroke-linecap="round"><path d="M6.5 6.8 10.4 8.4M6.5 11.6l3.8-1.8M6.5 12.6l3.8 1.8M6.5 17.2l3.8-1.6M13.7 9.7l3.6 1.7M13.7 14.3l3.6-1.7"/></g>',
  cloud:  '<path d="M17.5 19H9a7 7 0 1 1 6.7-9h1.8a4.5 4.5 0 1 1 0 9Z"/>',
  arrow:  '<path d="M4 12h14M13 6l6 6-6 6"/>',
  globe:  '<circle cx="12" cy="12" r="9"/><path d="M3 12h18M12 3a13.5 13.5 0 0 1 0 18M12 3a13.5 13.5 0 0 0 0 18"/>',
  github: '<path d="M12 .5C5.65.5.5 5.65.5 12c0 5.08 3.29 9.39 7.86 10.91.58.1.79-.25.79-.55v-2.17c-3.2.7-3.87-1.37-3.87-1.37-.52-1.33-1.28-1.69-1.28-1.69-1.05-.72.08-.7.08-.7 1.16.08 1.77 1.19 1.77 1.19 1.03 1.77 2.7 1.26 3.36.96.1-.75.4-1.26.72-1.55-2.55-.29-5.23-1.28-5.23-5.68 0-1.26.45-2.28 1.19-3.09-.12-.29-.52-1.46.11-3.05 0 0 .97-.31 3.18 1.18a11 11 0 0 1 5.8 0c2.2-1.49 3.17-1.18 3.17-1.18.63 1.59.23 2.76.11 3.05.74.81 1.19 1.83 1.19 3.09 0 4.41-2.69 5.38-5.25 5.66.41.36.77 1.05.77 2.13v3.16c0 .3.21.66.8.55A11.5 11.5 0 0 0 23.5 12C23.5 5.65 18.35.5 12 .5z"/>',
  linkedin:'<path d="M4.98 3.5A2.49 2.49 0 1 1 5 8.48a2.49 2.49 0 0 1-.02-4.98zM3 9.75h4v11.25H3zM9.5 9.75h3.8v1.54h.05c.53-1 1.83-2.06 3.77-2.06 4.03 0 4.78 2.65 4.78 6.1V21h-4v-5.13c0-1.22-.02-2.8-1.7-2.8-1.71 0-1.97 1.33-1.97 2.71V21h-3.98z"/>',
  twitter:'<path d="M23 4.9c-.8.4-1.7.7-2.6.8a4.5 4.5 0 0 0 2-2.5c-.9.5-1.9.9-2.9 1.1a4.5 4.5 0 0 0-7.7 4.1A12.8 12.8 0 0 1 2.5 3.6a4.5 4.5 0 0 0 1.4 6 4.4 4.4 0 0 1-2-.6v.1a4.5 4.5 0 0 0 3.6 4.4 4.6 4.6 0 0 1-2 .1 4.5 4.5 0 0 0 4.2 3.1A9 9 0 0 1 1 18.6a12.7 12.7 0 0 0 6.9 2c8.3 0 12.8-6.9 12.8-12.8v-.6c.9-.6 1.6-1.4 2.3-2.3z"/>'
};
const FILLED = ['github', 'linkedin', 'twitter'];
const icon = n => FILLED.includes(n)
  ? `<svg viewBox="0 0 24 24" fill="currentColor" aria-hidden="true">${ICONS[n]}</svg>`
  : `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">${ICONS[n]}</svg>`;

const esc = s => String(s).replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));

/* ---- nav (desktop, mobile, footer) ---- */
function renderNav(){
  const link = l => `<a href="#${l.id}">${l.label}</a>`;
  $('#navLinks').innerHTML = NAV_LINKS.map(link).join('');
  $('#footNav').innerHTML  = NAV_LINKS.map(link).join('');
  $('#mnav').innerHTML =
    NAV_LINKS.map(link).join('') +
    `<div class="m-meta">
       <a href="mailto:${CONFIG.email}">${esc(CONFIG.email)}</a>
       <a href="tel:${CONFIG.phone}">${esc(CONFIG.phone)}</a>
       <span>${esc(CONFIG.location)}</span>
     </div>`;
}

/* ---- hero contact chips ---- */
function renderHeroContact(){
  $('#heroContact').innerHTML = HERO_CONTACT.map(c => {
    const ic = `<span class="hc-ic">${icon(c.icon)}</span>`;
    const tx = `<span class="hc-tx"><b>${esc(c.value)}</b><i>${esc(c.label)}</i></span>`;
    return `<li>${c.href ? `<a href="${c.href}">${ic}${tx}</a>` : `<span class="hc-item">${ic}${tx}</span>`}</li>`;
  }).join('');
}

/* ---- about: features, pill groups, workflow ---- */
function renderAbout(){
  $('#features').innerHTML = FEATURES.map(f =>
    `<div class="feature">${icon(f.icon)}<span>${f.label}</span></div>`).join('');
  $('#skillGroups').innerHTML = SKILL_GROUPS.map(g =>
    `<div class="grp"><h3>${esc(g.title)}</h3><ul class="pills">${g.items.map(i => `<li>${esc(i)}</li>`).join('')}</ul></div>`).join('');
  $('#flow').innerHTML = FLOW.map((s, i) =>
    `<span>${esc(s)}</span>${i < FLOW.length - 1 ? icon('arrow') : ''}`).join('');
}

/* ---- project cards ---- */
function renderProjects(){
  $('#projectGrid').innerHTML = PROJECTS.map((p, i) => {
    const demoLink = p.demo === undefined ? '' :
      p.demo
        ? `<a href="${p.demo}" target="_blank" rel="noopener">${icon('globe')} Live Demo ${icon('arrow')}</a>`
        : `<a href="#" data-placeholder="demo" data-name="${esc(p.name)}">${icon('globe')} Live Demo ${icon('arrow')}</a>`;
    return `
    <article class="proj-card reveal" style="--d:${(i * .1).toFixed(1)}s">
      <div class="shot">
        <svg class="mock" viewBox="0 0 400 230" preserveAspectRatio="xMidYMid slice" role="img" aria-label="${esc(p.name)} preview">${MOCKS[p.mock] || ''}</svg>
        <img src="${p.image}" alt="${esc(p.name)} screenshot" loading="lazy" data-fb="remove">
      </div>
      <h3>${esc(p.name)}</h3>
      <p>${esc(p.desc)}</p>
      <ul class="tags">${p.tags.map(t => `<li>${esc(t)}</li>`).join('')}</ul>
      <div class="proj-links">
        ${demoLink}
        <a href="${p.github}" target="_blank" rel="noopener">${icon('github')} View on GitHub ${icon('arrow')}</a>
      </div>
    </article>`;
  }).join('');
}

/* ---- skills grid ---- */
function renderSkills(){
  $('#skillGrid').innerHTML = SKILLS.map(s => {
    const ic = s.inline
      ? `<svg viewBox="0 0 24 24" aria-hidden="true">${s.inline}</svg>`
      : `<img src="${s.devicon}" alt="" loading="lazy" data-fb="letter" data-abbr="${s.abbr}" data-color="${s.color}">`;
    return `<li class="skill-tile"><span class="tile-icon">${ic}</span><span>${esc(s.name)}</span></li>`;
  }).join('');
}

/* ---- contact list + socials ---- */
function renderContact(){
  $('#contactList').innerHTML = CONTACT_ITEMS.map(c =>
    `<li><span class="hc-ic">${icon(c.icon)}</span>${c.href
      ? `<a href="${c.href}">${esc(c.value)}</a>` : `<span>${esc(c.value)}</span>`}</li>`).join('');

  const socials = [
    { cls: 'so-li', label: 'LinkedIn', icon: 'linkedin', url: CONFIG.socials.linkedin },
    { cls: 'so-tw', label: 'Twitter',  icon: 'twitter',  url: CONFIG.socials.twitter },
    { cls: 'so-em', label: 'Email',    icon: 'mail',     url: 'mailto:' + CONFIG.email }
  ];
  $('#socialRow').innerHTML = socials.map(s =>
    s.url
      ? `<a class="${s.cls}" href="${s.url}" aria-label="${s.label}"${s.url.startsWith('http') ? ' target="_blank" rel="noopener"' : ''}>${icon(s.icon)}</a>`
      : `<a class="${s.cls}" href="#" aria-label="${s.label}" data-placeholder="social" data-name="${s.label}">${icon(s.icon)}</a>`
  ).join('');
}

/* ---- boot ---- */
renderNav();
renderHeroContact();
renderAbout();
renderProjects();
renderSkills();
renderContact();