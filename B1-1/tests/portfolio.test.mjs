// Test-only dependency: JSDOM_PATH=/absolute/path/to/jsdom/lib/api.js node --test B1-1/tests/*.mjs
import test from 'node:test';
import assert from 'node:assert/strict';
import { readFile, access } from 'node:fs/promises';
import { pathToFileURL } from 'node:url';
import { selectProjects, filterProjects, fetchRepositories, initProjects, safeUrl } from '../js/projects.js';
import { validateField, isFormEndpoint, initContact } from '../js/contact.js';
import { config } from '../js/config.js';
import { initNavigation } from '../js/navigation.js';
import { initAnimations } from '../js/animations.js';
const { JSDOM } = await import(pathToFileURL(process.env.JSDOM_PATH).href);
const html = await readFile(new URL('../index.html', import.meta.url), 'utf8');
const fixture = [
  ['school01-numbermonster', 'JavaScript'], ['school02-countcake', 'HTML'],
  ['school03-lunch-menu-extractor', 'Python'], ['codyssey1-tools', 'Python'],
].map(([name, language]) => ({ name, language, private: false, owner: { login: 'peachily' }, html_url: `https://github.com/peachily/${name}` }));
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
test('Project selection excludes missing, private and foreign owner repos; preserves editorial order', () => {
  assert.equal(selectProjects(fixture).length, 4);
  assert.equal(selectProjects([{ ...fixture[0], private: true }]).length, 0);
  assert.equal(selectProjects([{ ...fixture[0], owner: { login: 'other' } }]).length, 0);
  assert.equal(selectProjects(fixture.toReversed())[0].repo, fixture[0].name);
});
test('Category AND language filters produce success and empty results', () => {
  const projects = selectProjects(fixture);
  assert.equal(filterProjects(projects, 'all', 'all').length, 4);
  assert.equal(filterProjects(projects, 'education', 'all').length, 2);
  assert.equal(filterProjects(projects, 'school', 'Python').length, 1);
  assert.equal(filterProjects(projects, 'education', 'Python').length, 0);
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
  assert.equal(dom.window.document.querySelectorAll('.project-card').length, 4);
  $('[data-category="education"]').click();
  $('#language-filter').value = 'Python'; $('#language-filter').dispatchEvent(event('change'));
  assert.equal(dom.window.document.querySelectorAll('.project-card').length, 0);
  assert.match($('#project-status').textContent, /조건에 맞는/);
  $('[data-category="school"]').click(); assert.equal(dom.window.document.querySelectorAll('.project-card').length, 1);
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
  $('#contact-form').dispatchEvent(event('submit'));
  assert.equal($('#name').getAttribute('aria-invalid'), 'true');
  assert.equal(dom.window.document.activeElement.id, 'name');
  for (const [id, value] of [['name', '수정'], ['email', 'test@example.com'], ['message', '안녕하세요. 프로젝트에 관해 이야기하고 싶습니다.']]) {
    $(`#${id}`).value = value; $(`#${id}`).dispatchEvent(event('input'));
  }
  $('#contact-form').dispatchEvent(event('submit')); await flush();
  assert.equal(requests, 0); assert.match($('#contact-status').textContent, /전송되지 않았습니다/);
  dom.window.close();
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
  config.formEndpoint = ''; dom.window.close();
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
  $('#theme-toggle').click(); assert.equal(localStorage.getItem('peachily-theme'), 'light');
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
  assert.equal($('.reveal-pending'), null); assert.equal($('#typing-text').textContent, '작은 필요에서 시작되는 변화');
  dom.window.close();
});
test('Styles: responsive breakpoints, grid pattern, theme and text contrast', async () => {
  const responsive = await readFile(new URL('../css/responsive.css', import.meta.url), 'utf8');
  const layout = await readFile(new URL('../css/layout.css', import.meta.url), 'utf8');
  assert.match(responsive, /min-width: 768px/); assert.match(responsive, /min-width: 1024px/);
  assert.match(layout, /repeat\(auto-fit, minmax/);
  function luminance(hex) { return hex.match(/\w\w/g).map(x => parseInt(x,16)/255).map(x => x<=.04045 ? x/12.92 : ((x+.055)/1.055)**2.4).reduce((sum,x,i) => sum+x*[.2126,.7152,.0722][i],0); }
  for (const [fg,bg] of [['403c43','fffdfc'],['716b73','fffdfc'],['925267','fffdfc'],['c0b7c2','2b2830'],['f6c5cf','211f25'],['a12b43','ffffff']]) {
    const values = [luminance(fg),luminance(bg)].sort((a,b)=>a-b); assert.ok((values[1]+.05)/(values[0]+.05)>=4.5, `${fg}/${bg}`);
  }
});
