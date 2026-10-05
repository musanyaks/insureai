/* =====================================================
   data.js — ALL page content. Add a project or skill by
   adding an object here; the DOM updates automatically.
===================================================== */

const NAV_LINKS = [
  { id: 'home',     label: 'Home' },
  { id: 'about',    label: 'About' },
  { id: 'projects', label: 'Projects' },
  { id: 'skills',   label: 'Skills' },
  { id: 'contact',  label: 'Contact' }
];

/* icon names refer to the set in js/render.js */
const HERO_CONTACT = [
  { icon: 'mail',  value: CONFIG.email,    label: 'Email',    href: 'mailto:' + CONFIG.email },
  { icon: 'phone', value: CONFIG.phone,    label: 'Phone',    href: 'tel:' + CONFIG.phone },
  { icon: 'pin',   value: CONFIG.location, label: 'Location' }
];

const CONTACT_ITEMS = [
  { icon: 'mail',  value: CONFIG.email,    href: 'mailto:' + CONFIG.email },
  { icon: 'phone', value: CONFIG.phone,    href: 'tel:' + CONFIG.phone },
  { icon: 'pin',   value: CONFIG.location }
];

const FEATURES = [
  { icon: 'code',  label: 'Software<br>Development' },
  { icon: 'chart', label: 'Data Analysis' },
  { icon: 'brain', label: 'Machine<br>Learning' },
  { icon: 'cloud', label: 'Cloud &amp; DevOps' }
];

const SKILL_GROUPS = [
  { title: 'Languages',              items: ['Python', 'Java', 'R', 'SQL'] },
  { title: 'Frameworks & Libraries', items: ['Spring Boot', 'Streamlit', 'Django', 'Flask'] },
  { title: 'Data & Analytics',       items: ['Pandas', 'NumPy', 'Matplotlib', 'Scikit-learn'] }
];

const FLOW = ['Learn', 'Build', 'Test', 'Improve', 'Deploy'];

/* PROJECTS — demo field:
   'https://…'  → live link     |   ''  → visible placeholder (toast)   |   omit key → no demo link  */
const PROJECTS = [
  {
    name: 'FleetPulse',
    desc: 'Real-time IoT fleet analytics platform with geofencing, driver scoring and live dashboards.',
    tags: ['Java', 'Spring Boot', 'Kafka', 'TimescaleDB', 'Docker'],
    github: 'https://github.com/musanyaks/fleetpulse',
    image: 'assets/project-fleetpulse.jpg',
    mock: 'fleetpulse'
  },
  {
    name: 'Loss Reserving Workbench',
    desc: 'Actuarial analysis platform with Chain Ladder, Mack and bootstrap methods, approval workflows and audit trails.',
    tags: ['Python', 'Streamlit', 'SQLAlchemy', 'Pandas'],
    github: 'https://github.com/musanyaks/loss-reserving-workbench',
    demo: '',   /* ← paste your Streamlit demo URL here */
    image: 'assets/project-lrw.jpg',
    mock: 'lrw'
  },
  {
    name: 'sacensus',
    desc: 'R package for accessing, analysing and visualising South African census data (1996, 2001, 2011 and 2022).',
    tags: ['R', 'Tidyverse', 'ggplot2', 'dplyr'],
    github: 'https://github.com/musanyaks/sacensus',
    image: 'assets/project-sacensus.jpg',
    mock: 'sacensus'
  }
];

/* SKILLS — devicon URL loads from CDN; if it fails, the coloured abbr tile shows */
const SKILLS = [
  { name: 'Python',      devicon: 'https://cdn.jsdelivr.net/gh/devicons/devicon/icons/python/python-original.svg',   abbr: 'Py', color: '#3776AB' },
  { name: 'Java',        devicon: 'https://cdn.jsdelivr.net/gh/devicons/devicon/icons/java/java-original.svg',       abbr: 'Jv', color: '#E76F00' },
  { name: 'R',           devicon: 'https://cdn.jsdelivr.net/gh/devicons/devicon/icons/r/r-original.svg',             abbr: 'R',  color: '#276DC3' },
  { name: 'SQL',         inline: '<ellipse cx="12" cy="5.5" rx="7.5" ry="3" fill="#8FC4F2"/><path d="M4.5 5.5v6.5c0 1.66 3.36 3 7.5 3s7.5-1.34 7.5-3V5.5" fill="none" stroke="#5EA9EC" stroke-width="2"/><path d="M4.5 12v6.5c0 1.66 3.36 3 7.5 3s7.5-1.34 7.5-3V12" fill="none" stroke="#5EA9EC" stroke-width="2"/>', abbr: 'SQL', color: '#5EA9EC' },
  { name: 'Spring Boot', devicon: 'https://cdn.jsdelivr.net/gh/devicons/devicon/icons/spring/spring-original.svg',   abbr: 'Sb', color: '#6DB33F' },
  { name: 'Kafka',       devicon: 'https://cdn.jsdelivr.net/gh/devicons/devicon/icons/kafka/kafka-original.svg',     abbr: 'Kk', color: '#231F20' },
  { name: 'Docker',      devicon: 'https://cdn.jsdelivr.net/gh/devicons/devicon/icons/docker/docker-original.svg',   abbr: 'Dk', color: '#2496ED' },
  { name: 'Streamlit',   devicon: 'https://cdn.jsdelivr.net/gh/devicons/devicon/icons/streamlit/streamlit-original.svg', abbr: 'St', color: '#FF4B4B' },
  { name: 'Pandas',      devicon: 'https://cdn.jsdelivr.net/gh/devicons/devicon/icons/pandas/pandas-original.svg',   abbr: 'Pd', color: '#150458' },
  { name: 'NumPy',       devicon: 'https://cdn.jsdelivr.net/gh/devicons/devicon/icons/numpy/numpy-original.svg',     abbr: 'Np', color: '#4DABCF' },
  { name: 'Git',         devicon: 'https://cdn.jsdelivr.net/gh/devicons/devicon/icons/git/git-original.svg',         abbr: 'Gt', color: '#F05033' },
  { name: 'Linux',       devicon: 'https://cdn.jsdelivr.net/gh/devicons/devicon/icons/linux/linux-original.svg',     abbr: 'Lx', color: '#111111' }
];

/* Card artwork — drawn stand-ins shown until your real screenshots
   exist at the image paths above. Replace freely or delete. */
const MOCKS = {
  fleetpulse: '<rect width="400" height="230" fill="#0B1626"/><rect width="64" height="230" fill="#0E1D33"/><circle cx="20" cy="18" r="6" fill="#2196F3"/><rect x="12" y="42" width="40" height="6" rx="3" fill="#2196F3"/><g fill="#223C5E"><rect x="12" y="60" width="34" height="6" rx="3"/><rect x="12" y="78" width="40" height="6" rx="3"/><rect x="12" y="96" width="30" height="6" rx="3"/><rect x="12" y="114" width="38" height="6" rx="3"/><rect x="12" y="132" width="28" height="6" rx="3"/><rect x="12" y="150" width="36" height="6" rx="3"/></g><text x="76" y="22" fill="#9FB3CE" font-family="monospace" font-size="9">FLEETPULSE · LIVE OVERVIEW</text><rect x="72" y="30" width="152" height="92" rx="6" fill="#0E1D33"/><g transform="translate(104,76)"><circle r="26" fill="none" stroke="#1B3355" stroke-width="10"/><circle r="26" fill="none" stroke="#22C55E" stroke-width="10" stroke-dasharray="49 163" transform="rotate(-90)"/><circle r="26" fill="none" stroke="#3B82F6" stroke-width="10" stroke-dasharray="38 163" transform="rotate(45)"/><circle r="26" fill="none" stroke="#F59E0B" stroke-width="10" stroke-dasharray="24 163" transform="rotate(128)"/></g><g font-family="monospace" font-size="7" fill="#7C93B4"><rect x="152" y="52" width="6" height="6" rx="1" fill="#22C55E"/><text x="162" y="58">EN ROUTE</text><rect x="152" y="68" width="6" height="6" rx="1" fill="#3B82F6"/><text x="162" y="74">IDLE</text><rect x="152" y="84" width="6" height="6" rx="1" fill="#F59E0B"/><text x="162" y="90">ALERT</text></g><rect x="232" y="30" width="152" height="92" rx="6" fill="#0E1D33"/><g><rect x="248" y="96" width="10" height="18" rx="2" fill="#22C55E"/><rect x="264" y="86" width="10" height="28" rx="2" fill="#22C55E"/><rect x="280" y="92" width="10" height="22" rx="2" fill="#22C55E"/><rect x="298" y="78" width="10" height="36" rx="2" fill="#38BDF8"/><rect x="314" y="70" width="10" height="44" rx="2" fill="#38BDF8"/><rect x="330" y="84" width="10" height="30" rx="2" fill="#38BDF8"/><rect x="346" y="64" width="10" height="50" rx="2" fill="#38BDF8"/></g><rect x="72" y="130" width="152" height="86" rx="6" fill="#0E1D33"/><path d="M80 200 100 186 118 192 138 168 156 176 176 158 196 166 214 150 214 210 80 210Z" fill="rgba(56,189,248,.12)"/><polyline points="80,200 100,186 118,192 138,168 156,176 176,158 196,166 214,150" fill="none" stroke="#38BDF8" stroke-width="2"/><rect x="232" y="130" width="152" height="86" rx="6" fill="#0E1D33"/><g stroke="#16283F"><path d="M240 150h136M240 170h136M240 190h136M260 138v70M290 138v70M320 138v70M350 138v70"/></g><polyline points="248,196 268,182 288,188 308,164 332,170 356,150" fill="none" stroke="#F59E0B" stroke-width="2" stroke-dasharray="4 3"/><circle cx="248" cy="196" r="3" fill="#22C55E"/><circle cx="356" cy="150" r="3" fill="#F59E0B"/><circle cx="308" cy="164" r="2.4" fill="#38BDF8"/><circle cx="288" cy="188" r="2.4" fill="#38BDF8"/>',

  lrw: '<rect width="400" height="230" fill="#E7EDF5"/><rect width="64" height="230" fill="#FFFFFF"/><circle cx="20" cy="18" r="6" fill="#3B82F6"/><rect x="12" y="42" width="40" height="6" rx="3" fill="#3B82F6"/><g fill="#D7E0EC"><rect x="12" y="60" width="34" height="6" rx="3"/><rect x="12" y="78" width="40" height="6" rx="3"/><rect x="12" y="96" width="30" height="6" rx="3"/><rect x="12" y="114" width="38" height="6" rx="3"/><rect x="12" y="132" width="28" height="6" rx="3"/></g><text x="74" y="22" fill="#64748B" font-family="monospace" font-size="9">RESERVING WORKBENCH</text><rect x="72" y="32" width="150" height="108" rx="6" fill="#FFFFFF"/><g stroke="#EEF2F8"><path d="M84 56h126M84 80h126M84 104h126M84 126h126"/></g><polyline points="84,118 106,110 128,96 150,88 172,70 194,62 212,54" fill="none" stroke="#3B82F6" stroke-width="2.4"/><g fill="#3B82F6"><circle cx="106" cy="110" r="2.6"/><circle cx="128" cy="96" r="2.6"/><circle cx="150" cy="88" r="2.6"/><circle cx="172" cy="70" r="2.6"/><circle cx="194" cy="62" r="2.6"/></g><rect x="230" y="32" width="154" height="108" rx="6" fill="#FFFFFF"/><g fill="#93C5FD"><rect x="244" y="98" width="14" height="32" rx="2"/><rect x="264" y="86" width="14" height="44" rx="2"/><rect x="284" y="104" width="14" height="26" rx="2"/></g><g fill="#2563EB"><rect x="306" y="72" width="14" height="58" rx="2"/><rect x="326" y="80" width="14" height="50" rx="2"/><rect x="346" y="92" width="14" height="38" rx="2"/></g><rect x="72" y="148" width="312" height="68" rx="6" fill="#FFFFFF"/><g fill="#334155" font-family="monospace" font-size="8"><text x="84" y="164">ACCIDENT YEAR</text><text x="196" y="164">ULTIMATE</text><text x="288" y="164">IBNR</text></g><g fill="#C9D4E2"><rect x="84" y="172" width="60" height="5" rx="2"/><rect x="196" y="172" width="40" height="5" rx="2"/><rect x="288" y="172" width="36" height="5" rx="2"/><rect x="84" y="186" width="52" height="5" rx="2"/><rect x="196" y="186" width="44" height="5" rx="2"/><rect x="288" y="186" width="30" height="5" rx="2"/><rect x="84" y="200" width="56" height="5" rx="2"/><rect x="196" y="200" width="38" height="5" rx="2"/><rect x="288" y="200" width="42" height="5" rx="2"/></g>',

  sacensus: '<rect width="400" height="230" fill="#EEF3F9"/><rect width="228" height="230" fill="#F7FAFD"/><text x="16" y="22" fill="#64748B" font-family="monospace" font-size="9">SA CENSUS · GEO EXPLORER</text><path d="M36 78 74 60 120 64 150 52 176 66 198 96 186 128 196 158 164 186 120 178 84 192 52 164 40 128Z" fill="#BFDBF2" stroke="#6FA8DC" stroke-width="1.5"/><g stroke="#8FB9E2" fill="none"><path d="M84 60 96 120 64 160M120 64 112 124M150 54 140 116 172 150M96 120 140 116"/></g><circle cx="112" cy="120" r="4" fill="#2563EB"/><circle cx="140" cy="112" r="3" fill="#2563EB" opacity=".75"/><circle cx="90" cy="150" r="3" fill="#2563EB" opacity=".6"/><g font-family="monospace" font-size="7" fill="#64748B"><rect x="16" y="204" width="8" height="8" rx="2" fill="#2563EB"/><text x="28" y="211">1996</text><rect x="60" y="204" width="8" height="8" rx="2" fill="#60A5FA"/><text x="72" y="211">2011</text><rect x="104" y="204" width="8" height="8" rx="2" fill="#BFDBF2"/><text x="116" y="211">2022</text></g><rect x="228" width="172" height="230" fill="#0F172A"/><circle cx="240" cy="14" r="3" fill="#F87171"/><circle cx="252" cy="14" r="3" fill="#FBBF24"/><circle cx="264" cy="14" r="3" fill="#34D399"/><g><rect x="240" y="30" width="70" height="5" rx="2" fill="#7DD3FC"/><rect x="316" y="30" width="40" height="5" rx="2" fill="#475569"/><rect x="252" y="44" width="56" height="5" rx="2" fill="#A5B4FC"/><rect x="314" y="44" width="52" height="5" rx="2" fill="#475569"/><rect x="252" y="58" width="84" height="5" rx="2" fill="#86EFAC"/><rect x="252" y="72" width="60" height="5" rx="2" fill="#FCD34D"/><rect x="318" y="72" width="30" height="5" rx="2" fill="#475569"/><rect x="240" y="86" width="100" height="5" rx="2" fill="#7DD3FC"/><rect x="252" y="100" width="72" height="5" rx="2" fill="#F9A8D4"/><rect x="330" y="100" width="36" height="5" rx="2" fill="#475569"/><rect x="252" y="114" width="52" height="5" rx="2" fill="#86EFAC"/><rect x="310" y="114" width="58" height="5" rx="2" fill="#475569"/><rect x="240" y="128" width="88" height="5" rx="2" fill="#A5B4FC"/><rect x="252" y="142" width="64" height="5" rx="2" fill="#FCD34D"/><rect x="240" y="156" width="44" height="5" rx="2" fill="#64748B"/><rect x="290" y="156" width="70" height="5" rx="2" fill="#475569"/><rect x="240" y="170" width="58" height="5" rx="2" fill="#7DD3FC"/><rect x="240" y="184" width="30" height="5" rx="2" fill="#64748B"/></g>'
};