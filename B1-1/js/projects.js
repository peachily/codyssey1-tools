import { config, categories, featuredProjects } from './config.js';
export function safeUrl(value) {
  try { const url = new URL(value); return url.protocol === 'https:' ? url.href : null; }
  catch { return null; }
}
export function selectProjects(repos) {
  return featuredProjects.map(meta => {
    const repo = repos.find(item => item.name === meta.repo && !item.private && item.owner?.login === config.githubUser);
    return repo && safeUrl(repo.html_url) ? { ...meta, language: repo.language || '기타', description: meta.description || repo.description || '설명을 준비하고 있습니다.', github: safeUrl(repo.html_url), createdAt: repo.created_at } : null;
  }).filter(Boolean).sort((a, b) => {
    const dateDifference = (Date.parse(b.createdAt) || 0) - (Date.parse(a.createdAt) || 0);
    return dateDifference || a.repo.localeCompare(b.repo);
  });
}
export function filterProjects(projects, category, language) {
  return projects.filter(project => (category === 'all' || project.category === category) && (language === 'all' || project.language === language));
}
function element(tag, className, text) {
  const node = document.createElement(tag);
  node.className = className;
  if (text) node.textContent = text;
  return node;
}
function card(project) {
  const article = element('article', 'project-card');
  article.dataset.category = project.category;
  const link = element('a', 'project-card-link');
  link.href = project.github;
  link.target = '_blank';
  link.rel = 'noopener noreferrer';
  link.setAttribute('aria-labelledby', `project-${project.repo}`);
  const top = element('div', 'project-card-top');
  const arrow = document.createElementNS('http://www.w3.org/2000/svg', 'svg');
  arrow.setAttribute('class', 'icon project-arrow');
  arrow.setAttribute('aria-hidden', 'true');
  const use = document.createElementNS('http://www.w3.org/2000/svg', 'use');
  use.setAttribute('href', 'images/icons.svg#arrow');
  arrow.append(use);
  top.append(element('span', 'project-category', categories[project.category]), arrow);
  const heading = element('h3', '', project.title);
  heading.id = `project-${project.repo}`;
  heading.append(element('span', 'sr-only', ' GitHub 저장소 (새 탭)'));
  const badges = element('div', 'badges');
  badges.append(...project.technologies.map(technology => element('span', 'badge', technology)));
  link.append(top, heading, element('p', '', project.description), badges);
  article.append(link);
  return article;
}
export async function fetchRepositories(fetcher = fetch) {
  const repos = [];
  // Follow pagination, so curated older repositories do not disappear after 100 repos.
  for (let page = 1; ; page += 1) {
    const controller = new AbortController();
    const timeout = setTimeout(() => controller.abort(), 12000);
    try {
      const response = await fetcher(`https://api.github.com/users/${config.githubUser}/repos?per_page=100&page=${page}&sort=created&direction=desc`, {
        signal: controller.signal, headers: { Accept: 'application/vnd.github+json' },
      });
      if (response.status === 403 || response.status === 429) {
        const reset = Number(response.headers.get('x-ratelimit-reset'));
        const when = reset > Date.now() / 1000 ? ` ${new Date(reset * 1000).toLocaleTimeString('ko-KR')} 이후 다시 시도해 주세요.` : ' 잠시 후 다시 시도해 주세요.';
        throw new Error(`GitHub 요청이 제한되었습니다.${when}`);
      }
      if (!response.ok) throw new Error(`GitHub에서 정보를 가져오지 못했습니다. (HTTP ${response.status})`);
      const data = await response.json();
      if (!Array.isArray(data)) throw new Error('GitHub 응답 형식을 확인할 수 없습니다.');
      repos.push(...data);
      if (data.length < 100) break;
    } finally { clearTimeout(timeout); }
  }
  return repos;
}
export function initProjects() {
  const list = document.querySelector('#project-list');
  const status = document.querySelector('#project-status');
  const retry = document.querySelector('#project-retry');
  const language = document.querySelector('#language-filter');
  const categoryButtons = [...document.querySelectorAll('[data-category]')];
  const state = { phase: 'loading', projects: [], error: '', category: 'all', language: 'all' };
  function render() {
    list.setAttribute('aria-busy', String(state.phase === 'loading'));
    retry.hidden = state.phase !== 'error';
    status.dataset.state = state.phase;
    list.replaceChildren();
    categoryButtons.forEach(button => button.setAttribute('aria-pressed', String(button.dataset.category === state.category)));
    language.value = state.language;
    if (state.phase === 'loading') status.textContent = 'GitHub에서 프로젝트를 불러오고 있습니다…';
    else if (state.phase === 'error') status.textContent = state.error;
    else {
      const visible = filterProjects(state.projects, state.category, state.language);
      status.textContent = visible.length ? `${visible.length}개의 프로젝트` : '조건에 맞는 프로젝트가 없습니다. 다른 카테고리나 언어를 선택해 주세요.';
      list.append(...visible.map(card));
    }
  }
  async function load() {
    if (retry.disabled) return;
    state.phase = 'loading'; retry.disabled = true; render();
    try {
      state.projects = selectProjects(await fetchRepositories()); state.phase = 'success';
      const languages = [...new Set(state.projects.map(project => project.language))].sort();
      language.replaceChildren(new Option('모든 언어', 'all'), ...languages.map(value => new Option(value, value)));
      if (!languages.includes(state.language)) state.language = 'all';
    }
    catch (error) { state.phase = 'error'; state.error = error.name === 'AbortError' ? '응답 시간이 초과되었습니다. 다시 시도해 주세요.' : error instanceof TypeError ? '네트워크 연결을 확인하고 다시 시도해 주세요.' : error.message; }
    finally { retry.disabled = false; render(); }
  }
  categoryButtons.forEach(button => button.addEventListener('click', () => {
    state.category = button.dataset.category; render();
  }));
  language.addEventListener('change', () => { state.language = language.value; render(); });
  retry.addEventListener('click', load);
  load();
}
