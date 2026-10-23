// Test-only dependency: JSDOM_PATH=/absolute/path/to/jsdom/lib/api.js node --test B1-1/tests/*.mjs
import test from 'node:test';
import assert from 'node:assert/strict';
import { createHash } from 'node:crypto';
import { readFile, access } from 'node:fs/promises';
import { pathToFileURL } from 'node:url';
import { selectProjects, filterProjects, fetchRepositories, initProjects, safeUrl } from '../js/projects.js';
import { validateField, isFormEndpoint, initContact } from '../js/contact.js';
import { config } from '../js/config.js';
import { initSkills, createTechnologyBadge } from '../js/technologies.js';
import { initNavigation } from '../js/navigation.js';
import { initAnimations } from '../js/animations.js';
const { JSDOM } = await import(pathToFileURL(process.env.JSDOM_PATH).href);
const html = await readFile(new URL('../index.html', import.meta.url), 'utf8');
const fixture = [
  ['school01-numbermonster', 'JavaScript', '2026-03-17T02:27:42Z'],
  ['school02-countcake', 'JavaScript', '2026-03-17T11:01:39Z'],
  ['school04-pet-simulator', 'JavaScript', '2026-07-28T11:36:28Z'],
  ['school05-animal-rescue', 'JavaScript', '2026-10-17T06:43:09Z'],
  ['school06-snack-market', 'TypeScript', '2026-10-17T06:49:29Z'],
  ['school03-lunch-menu-extractor', 'Python', '2026-04-20T04:48:14Z'],
  ['codyssey0-python', 'Python', '2025-09-18T09:21:48Z'],
  ['codyssey0-devops', 'HTML', '2025-07-14T08:54:30Z'],
  ['codyssey1-selection', 'Python', '2026-03-30T08:56:04Z'],
  ['codyssey1-tools', 'Python', '2026-09-07T06:33:42Z'],
  ['codyssey1-termproject', 'Python', '2026-10-01T07:23:11Z'],
].map(([name, language, created_at], index) => ({
  name, language, created_at,
  // Deliberately disagree with creation order: display must ignore these fields.
  updated_at: `2026-10-${String(index + 1).padStart(2, '0')}T00:00:00Z`,
  pushed_at: `2026-09-${String(index + 1).padStart(2, '0')}T00:00:00Z`,
  private: false, owner: { login: 'peachily' }, html_url: `https://github.com/peachily/${name}`,
}));
const originalFormEndpoint = config.formEndpoint;
const flush = () => new Promise(resolve => setImmediate(resolve));
function setup() {
  const dom = new JSDOM(html, { url: 'http://localhost:8000/B1-1/', pretendToBeVisual: true });
  const media = new Map();
  dom.window.matchMedia = query => {
    if (!media.has(query)) media.set(query, { matches: false, listeners: [], addEventListener(_, callback) { this.listeners.push(callback); }, change(value) { this.matches = value; this.listeners.forEach(fn => fn({ matches: value })); } });
    return media.get(query);
  };
  for (const key of ['window', 'document', 'localStorage', 'history', 'Option']) globalThis[key] = key === 'window' ? dom.window : dom.window[key];
  globalThis.matchMedia = dom.window.matchMedia;
  globalThis.requestAnimationFrame = callback => { setImmediate(callback); return 1; };
  dom.window.HTMLElement.prototype.scrollIntoView = function () {};
  return { dom, media, $: selector => dom.window.document.querySelector(selector), event: type => new dom.window.Event(type, { bubbles: true, cancelable: true }) };
}
test('HTML: IDs, labels, semantic landmarks, internal anchors and local assets', async () => {
  const { $, dom } = setup();
  const ids = [...dom.window.document.querySelectorAll('[id]')].map(node => node.id);
  assert.equal(new Set(ids).size, ids.length);
  for (const tag of ['header', 'nav', 'main', 'section', 'article', 'footer']) assert.ok($(tag));
  assert.equal(dom.window.document.querySelectorAll('h1').length, 1);
  for (const field of dom.window.document.querySelectorAll('input, textarea, select')) assert.ok($(`label[for="${field.id}"]`));
  for (const a of dom.window.document.querySelectorAll('a[href^="#"]')) assert.ok($(a.hash));
  for (const node of dom.window.document.querySelectorAll('[src],link[href],use[href]')) {
    const value = node.getAttribute('src') || node.getAttribute('href');
    if (!value.startsWith('https:')) await access(new URL(`../${value.split('#')[0]}`, import.meta.url));
  }
  assert.equal(dom.window.document.querySelectorAll('[style],[onclick],[onsubmit]').length, 0);
  dom.window.close();
});
test('Skills: three groups, 24 technologies, local logos and text survives image errors', () => {
  const { $, dom, event } = setup();
  initSkills();
  const expected = [
    ['Frontend', ['HTML5', 'CSS3', 'JavaScript', 'TypeScript', 'React', 'Vite', 'Tailwind CSS']],
    ['Backend, Data & AI', ['Python', 'Node.js', 'FastAPI', 'SQLite', 'PostgreSQL', 'Supabase', 'PocketBase', 'OpenAI API']],
    ['Tools & Deployment', ['Git', 'GitHub', 'Linux', 'Amazon Web Services', 'Docker', 'Railway', 'Cloudflare', 'Netlify', 'Figma']],
  ];
  const cards = [...dom.window.document.querySelectorAll('#skills .skill-card')];
  assert.equal(cards.length, 3);
  cards.forEach((card, index) => {
    assert.equal(card.querySelector('h3').textContent, expected[index][0]);
    const badges = [...card.querySelectorAll('.technology-badge')];
    assert.deepEqual(badges.map(badge => badge.textContent), expected[index][1]);
    badges.forEach(badge => {
      const logo = badge.querySelector('img');
      assert.ok(logo.getAttribute('src').startsWith('assets/icons/technologies/'));
      assert.equal(logo.alt, '');
      assert.equal(logo.width, 18); assert.equal(logo.height, 18);
      const name = badge.textContent;
      logo.dispatchEvent(event('error'));
      assert.equal(badge.textContent, name);
    });
  });
  dom.window.close();
});
test('Brand assets retain upstream bytes and provenance, with the official OpenAI asset', async () => {
  const manifest = JSON.parse(await readFile(new URL('../assets/licenses/sources.json', import.meta.url), 'utf8'));
  assert.equal(manifest.assets.length, 24);
  assert.equal(new Set(manifest.assets.map(asset => asset.file)).size, 24);
  for (const asset of manifest.assets) {
    const data = await readFile(new URL(`../assets/${asset.file}`, import.meta.url));
    assert.equal(createHash('sha256').update(data).digest('hex'), asset.sha256);
    assert.match(data.toString(), /<svg/);
    assert.doesNotMatch(data.toString(), /<script|<foreignObject/i);
  }
  const openai = manifest.assets.find(asset => asset.file.endsWith('/openai.svg'));
  assert.equal(new URL(openai.source).hostname, 'cdn.openai.com');
  assert.match(openai.archivePath, /OpenAI-black-monoblossom/);
  await access(new URL('../assets/licenses/devicon-MIT.txt', import.meta.url));
});
test('Projects include the 11 selected public repos only and explicitly sort by created_at descending', () => {
  const projects = selectProjects([...fixture.toReversed(), { ...fixture[0], name: 'unselected-project' }]);
  assert.equal(projects.length, 11);
  assert.equal(new Set(projects.map(project => project.repo)).size, 11);
  assert.equal(selectProjects([{ ...fixture[0], private: true }]).length, 0);
  assert.equal(selectProjects([{ ...fixture[0], owner: { login: 'other' } }]).length, 0);
  assert.equal(selectProjects([{ ...fixture[0], html_url: 'javascript:alert(1)' }]).length, 0);
  assert.equal(selectProjects(fixture.slice(1)).length, 10);
  assert.equal(projects[0].repo, 'school06-snack-market');
  assert.equal(projects.at(-1).repo, 'codyssey0-devops');
  assert.deepEqual(projects.map(project => project.repo), selectProjects(fixture).map(project => project.repo));
  for (let i = 1; i < projects.length; i++) assert.ok(Date.parse(projects[i - 1].createdAt) >= Date.parse(projects[i].createdAt));
});
test('Category AND primary-language filters preserve creation-date order and handle empty results', () => {
  const projects = selectProjects(fixture);
  assert.equal(filterProjects(projects, 'all', 'all').length, 11);
  assert.equal(filterProjects(projects, 'education', 'all').length, 5);
  assert.equal(filterProjects(projects, 'school', 'Python').length, 1);
  assert.equal(filterProjects(projects, 'education', 'Python').length, 0);
  const filtered = filterProjects(projects, 'development', 'Python');
  assert.deepEqual(filtered.map(project => project.repo), ['codyssey1-termproject', 'codyssey1-tools', 'codyssey1-selection', 'codyssey0-python']);
});
test('Only HTTPS links and the intended Formspree endpoint are accepted', () => {
  for (const url of ['', 'javascript:alert(1)', 'http://example.com']) assert.equal(safeUrl(url), null);
  assert.ok(isFormEndpoint('https://formspree.io/f/abc123'));
  for (const url of ['', 'https://evil.test/f/abc', 'https://formspree.io.evil.test/f/abc', 'https://formspree.io/f/abc?x=1']) assert.equal(isFormEndpoint(url), false);
});
test('GitHub fetch follows pagination without dropping older repositories', async () => {
  const urls = [];
  const data = await fetchRepositories(async url => { urls.push(url); return new Response(JSON.stringify(urls.length === 1 ? Array(100).fill(fixture[0]) : [fixture[1]])); });
  assert.equal(data.length, 101); assert.match(urls[1], /page=2/);
  assert.match(urls[0], /sort=created&direction=desc/);
});
test('GitHub 403, 429, server errors, invalid payloads and network failures reject', async () => {
  for (const status of [403, 429]) await assert.rejects(fetchRepositories(async () => new Response('{}', { status })), /요청이 제한/);
  await assert.rejects(fetchRepositories(async () => new Response('{}', { status: 500 })), /HTTP 500/);
  await assert.rejects(fetchRepositories(async () => new Response('{}')), /응답 형식/);
  await assert.rejects(fetchRepositories(async () => { throw new TypeError('offline'); }), /offline/);
});
test('Projects DOM: loading → error → retry → success → combined filter empty', async () => {
  const { $, dom, event } = setup();
  globalThis.fetch = async () => new Response('{}', { status: 403 });
  initProjects();
  assert.equal($('#project-list').getAttribute('aria-busy'), 'true');
  await flush(); assert.equal($('#project-retry').hidden, false); assert.match($('#project-status').textContent, /제한/);
  globalThis.fetch = async () => new Response(JSON.stringify(fixture));
  $('#project-retry').click(); await flush();
  assert.equal(dom.window.document.querySelectorAll('.project-card').length, 11);
  $('[data-category="education"]').click();
  $('#language-filter').value = 'Python'; $('#language-filter').dispatchEvent(event('change'));
  assert.equal(dom.window.document.querySelectorAll('.project-card').length, 0);
  assert.match($('#project-status').textContent, /조건에 맞는/);
  $('[data-category="school"]').click(); assert.equal(dom.window.document.querySelectorAll('.project-card').length, 1);
  dom.window.close();
});
test('Project cards provide one full-card keyboard link, a top arrow and verified technology tags', async () => {
  const { $, dom } = setup();
  globalThis.fetch = async () => new Response(JSON.stringify(fixture));
  initProjects(); await flush();
  for (const card of dom.window.document.querySelectorAll('.project-card')) {
    const links = card.querySelectorAll('a');
    assert.equal(links.length, 1);
    const link = links[0];
    assert.ok(link.href.startsWith('https://github.com/peachily/'));
    assert.equal(link.tabIndex, 0);
    assert.ok(card.querySelector('.project-arrow use'));
    assert.equal(link.getAttribute('aria-labelledby'), card.querySelector('h3').id);
    assert.ok(card.querySelector('.badge').textContent);
    assert.equal(card.querySelector('img'), null);
  }
  const pet = $('[href="https://github.com/peachily/school04-pet-simulator"]');
  assert.ok([...pet.querySelectorAll('.badge')].some(badge => badge.textContent === 'React'));
  const market = $('[href="https://github.com/peachily/school06-snack-market"]');
  assert.ok([...market.querySelectorAll('.badge')].some(badge => badge.textContent === 'TypeScript'));
  dom.window.close();
});
test('Contact validation: whitespace, malformed email and message boundaries', () => {
  assert.ok(validateField('name', '  ')); assert.ok(validateField('email', 'a@b'));
  assert.ok(validateField('message', 'short')); assert.ok(validateField('message', 'a'.repeat(5001)));
  assert.equal(validateField('name', '김수정'), ''); assert.equal(validateField('email', 'a@example.com'), '');
  assert.equal(validateField('message', '안녕하세요. 함께 이야기해요.'), '');
});
test('Contact DOM: validation errors, input correction and no fabricated success without config', async () => {
  const { $, dom, event } = setup(); let requests = 0;
  globalThis.fetch = async () => { requests++; return new Response('{}'); };
  config.formEndpoint = ''; initContact();
  assert.equal($('#contact-status').textContent, '');
  $('#contact-form').dispatchEvent(event('submit'));
  assert.equal($('#name').getAttribute('aria-invalid'), 'true');
  assert.equal(dom.window.document.activeElement.id, 'name');
  for (const [id, value] of [['name', '수정'], ['email', 'test@example.com'], ['message', '안녕하세요. 프로젝트에 관해 이야기하고 싶습니다.']]) {
    $(`#${id}`).value = value; $(`#${id}`).dispatchEvent(event('input'));
  }
  $('#contact-form').dispatchEvent(event('submit')); await flush();
  assert.equal(requests, 0); assert.match($('#contact-status').textContent, /전송되지 않았습니다/);
  config.formEndpoint = originalFormEndpoint; dom.window.close();
});
test('Contact DOM: configured service sending, failure retention, retry success and duplicate guard', async () => {
  const { $, dom, event } = setup(); config.formEndpoint = 'https://formspree.io/f/testonly';
  initContact();
  for (const [id, value] of [['name', '수정'], ['email', 'test@example.com'], ['message', '테스트 메시지입니다. 실제 전송하지 않습니다.']]) $(`#${id}`).value = value;
  let settle; let requests = 0;
  globalThis.fetch = async () => { requests++; return new Promise(resolve => { settle = resolve; }); };
  $('#contact-form').dispatchEvent(event('submit')); $('#contact-form').dispatchEvent(event('submit'));
  assert.equal(requests, 1); assert.equal($('#name').disabled, true);
  settle(new Response('{}', { status: 422 })); await flush();
  assert.match($('#contact-status').textContent, /전송하지 못했습니다/); assert.equal($('#name').value, '수정');
  globalThis.fetch = async (_url, options) => { assert.equal(JSON.parse(options.body).name, '수정'); return new Response('{}'); };
  $('#contact-form').dispatchEvent(event('submit')); await flush();
  assert.match($('#contact-status').textContent, /전송되었습니다/); assert.equal($('#name').value, '');
  config.formEndpoint = originalFormEndpoint; dom.window.close();
});
test('Navigation: mobile menu state, Escape, section anchor, 60px and 300px scroll boundaries', async () => {
  const { $, dom, event } = setup(); initNavigation();
  $('#menu-toggle').click(); assert.ok($('#navigation').classList.contains('active'));
  dom.window.document.dispatchEvent(new dom.window.KeyboardEvent('keydown', { key: 'Escape', bubbles: true }));
  assert.equal($('#menu-toggle').getAttribute('aria-expanded'), 'false');
  assert.equal(dom.window.document.activeElement.id, 'menu-toggle');
  $('#menu-toggle').click(); $('#navigation a').click();
  assert.equal($('#menu-toggle').getAttribute('aria-expanded'), 'false'); assert.equal(dom.window.document.activeElement.id, 'about');
  for (const [position, scrolled, visible] of [[60, false, false], [61, true, false], [300, true, false], [301, true, true]]) {
    dom.window.scrollY = position; dom.window.dispatchEvent(event('scroll')); await flush();
    assert.equal($('.site-header').classList.contains('scrolled'), scrolled); assert.equal($('#back-to-top').hidden, !visible);
  }
  dom.window.close();
});
test('Theme: OS default, saved manual priority, persistence and OS changes', async () => {
  const { $, dom, media } = setup(); matchMedia('(prefers-color-scheme: dark)').matches = true;
  const { initTheme } = await import('../js/theme.js?test=os'); initTheme();
  assert.equal(dom.window.document.documentElement.dataset.theme, 'dark');
  assert.equal($('#theme-toggle use').getAttribute('href'), 'assets/icons/ui.svg#sun');
  $('#theme-toggle').click();
  assert.equal($('#theme-toggle use').getAttribute('href'), 'assets/icons/ui.svg#moon'); assert.equal(localStorage.getItem('peachily-theme'), 'light');
  media.get('(prefers-color-scheme: dark)').change(true); assert.equal(dom.window.document.documentElement.dataset.theme, 'light');
  localStorage.setItem('peachily-theme', 'dark'); await import('../js/theme.js?test=saved');
  assert.equal(dom.window.document.documentElement.dataset.theme, 'dark'); dom.window.close();
});
test('Animations: IntersectionObserver threshold 0.2 and reduced motion stops pending effects', () => {
  const { $, dom, media } = setup(); let options;
  globalThis.IntersectionObserver = class { constructor(_cb, opts) { options = opts; } observe() {} unobserve() {} disconnect() {} };
  dom.window.IntersectionObserver = globalThis.IntersectionObserver;
  initAnimations(); assert.equal(options.threshold, 0.2); assert.ok($('.reveal-pending'));
  media.get('(prefers-reduced-motion: reduce)').change(true);
  assert.equal($('.reveal-pending'), null); assert.equal($('#typing-text').textContent, '교육의 경험을기술로 이어갑니다.');
  assert.equal($('.hero-description').classList.contains('hero-description-pending'), false);
  dom.window.close();
});
test('Hero types the heading before revealing its description, with an intact accessible heading', t => {
  t.mock.timers.enable({ apis: ['setTimeout'] });
  const { $, dom } = setup();
  initAnimations();
  assert.equal($('#typing-text').textContent, '');
  assert.ok($('.hero-description-pending'));
  assert.equal($('#hero-heading .sr-only').textContent, '교육의 경험을 기술로 이어갑니다.');
  t.mock.timers.tick(300);
  assert.equal($('#typing-text').textContent, '교');
  assert.ok($('.hero-description-pending'));
  for (let step = 0; step < 40; step += 1) t.mock.timers.tick(100);
  assert.equal($('#typing-text').textContent, '교육의 경험을기술로 이어갑니다.');
  assert.equal($('.hero-description-pending'), null);
  assert.equal($('.typing'), null);
  dom.window.close();
});
test('Styles: responsive breakpoints, grid pattern, theme and text contrast', async () => {
  const responsive = await readFile(new URL('../css/responsive.css', import.meta.url), 'utf8');
  const layout = await readFile(new URL('../css/layout.css', import.meta.url), 'utf8');
  assert.match(responsive, /min-width: 768px/); assert.match(responsive, /min-width: 1024px/);
  assert.match(layout, /repeat\(auto-fit, minmax/);
  function luminance(hex) { return hex.match(/\w\w/g).map(x => parseInt(x,16)/255).map(x => x<=.04045 ? x/12.92 : ((x+.055)/1.055)**2.4).reduce((sum,x,i) => sum+x*[.2126,.7152,.0722][i],0); }
  for (const [fg,bg] of [['403c43','fffdfc'],['716b73','fffdfc'],['c0b7c2','2b2830'],['f6c5cf','211f25'],['a12b43','ffffff']]) {
    const values = [luminance(fg),luminance(bg)].sort((a,b)=>a-b); assert.ok((values[1]+.05)/(values[0]+.05)>=4.5, `${fg}/${bg}`);
  }
});
