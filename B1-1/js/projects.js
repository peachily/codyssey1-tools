import { config, categories, featuredProjects } from './config.js';
import { createTechnologyBadge } from './technologies.js';
export function safeUrl(value) {
  try { const url = new URL(value); return url.protocol === 'https:' ? url.href : null; }
  catch { return null; }
}
export function selectProjects(repos) {
  // map으로 대표 프로젝트 정보를 API 응답과 합치고, 없는 저장소는 filter로 제외함.
  // 마지막 sort는 API 반환 순서와 관계없이 최초 생성일(created_at) 최신순으로 정렬함.
  return featuredProjects.map(meta => {
    const owner = meta.owner || config.githubUser;
    const repo = repos.find(item => item.name === meta.repo && !item.private && item.owner?.login?.toLowerCase() === owner.toLowerCase());
    const repositoryUrl = safeUrl(repo?.html_url);
    const github = safeUrl(meta.link || repositoryUrl);
    return repositoryUrl && github ? { ...meta, owner, language: repo.language || '기타', description: meta.description || repo.description || '설명을 준비하고 있습니다.', github, createdAt: repo.created_at } : null;
  }).filter(Boolean).sort((a, b) => {
    const dateDifference = (Date.parse(b.createdAt) || 0) - (Date.parse(a.createdAt) || 0);
    return dateDifference || `${a.owner}/${a.repo}`.localeCompare(`${b.owner}/${b.repo}`);
  });
}
export function filterProjects(projects, category, language) {
  // 카테고리와 주 언어 조건을 모두 만족하는 카드만 남김.
  return projects.filter(project => (category === 'all' || project.category === category) && (language === 'all' || project.language === language));
}
function element(tag, className, text) {
  // API 데이터로 카드를 만들기 위해 필요한 HTML 요소를 DOM에 새로 생성함.
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
  const headingId = `project-${project.owner}-${project.repo}`;
  link.setAttribute('aria-labelledby', headingId);
  const top = element('div', 'project-card-top');
  const arrow = document.createElementNS('http://www.w3.org/2000/svg', 'svg');
  arrow.setAttribute('class', 'icon project-arrow');
  arrow.setAttribute('aria-hidden', 'true');
  const use = document.createElementNS('http://www.w3.org/2000/svg', 'use');
  use.setAttribute('href', 'assets/icons/ui.svg#arrow');
  arrow.append(use);
  const labels = element('div', 'project-labels');
  labels.append(element('span', 'project-category', categories[project.category]));
  if (project.team) {
    const separator = element('span', 'project-separator', '/');
    separator.setAttribute('aria-hidden', 'true');
    labels.append(separator, element('span', 'project-team', 'Team Project'));
  }
  top.append(labels, arrow);
  const heading = element('h3', '', project.title);
  heading.id = headingId;
  heading.append(element('span', 'sr-only', project.link ? ' GitHub 조직 페이지 (새 탭)' : ' GitHub 저장소 (새 탭)'));
  const badges = element('div', 'badges');
  badges.append(...project.technologies.map(technology => createTechnologyBadge(technology, { compact: true })));
  link.append(top, heading, element('p', '', project.description), badges);
  article.append(link);
  article.dataset.reveal = '';
  return article;
}
function errorMessage(error) {
  return error.name === 'AbortError' ? '응답 시간이 초과되었습니다.'
    : error instanceof TypeError ? '네트워크 연결을 확인해 주세요.' : error.message;
}
async function requestGitHub(url, fetcher) {
  // fetch는 응답을 기다리는 동안 페이지를 멈추지 않음. await로 응답과 JSON을 차례로 받음.
  const controller = new AbortController();
  const timeout = setTimeout(() => controller.abort(), 12000);
  try {
    const response = await fetcher(url, {
      signal: controller.signal, headers: { Accept: 'application/vnd.github+json' },
    });
    // 요청 제한 시 GitHub가 제공한 재시도 가능 시간을 안내함.
    if (response.status === 403 || response.status === 429) {
      const reset = Number(response.headers.get('x-ratelimit-reset'));
      const when = reset > Date.now() / 1000 ? ` ${new Date(reset * 1000).toLocaleTimeString('ko-KR')} 이후 다시 시도해 주세요.` : ' 잠시 후 다시 시도해 주세요.';
      throw new Error(`GitHub 요청이 제한되었습니다.${when}`);
    }
    if (!response.ok) throw new Error(`GitHub에서 정보를 가져오지 못했습니다. (HTTP ${response.status})`);
    return await response.json();
  } finally { clearTimeout(timeout); }
}
export async function fetchRepositories(fetcher = fetch) {
  const repos = [];
  // 개인 저장소는 한 페이지에 최대 100개씩 받아 누락된 프로젝트가 없도록 끝까지 조회함.
  for (let page = 1; ; page += 1) {
    const data = await requestGitHub(`https://api.github.com/users/${config.githubUser}/repos?per_page=100&page=${page}&sort=created&direction=desc`, fetcher);
    if (!Array.isArray(data)) throw new Error('GitHub 응답 형식을 확인할 수 없습니다.');
    repos.push(...data);
    if (data.length < 100) break;
  }
  return repos;
}
export async function fetchProjectSources(fetcher = fetch) {
  // 팀 프로젝트는 각 소유자 저장소에서 조회함. 팀 여부는 소유자가 아니라 설정 데이터에 기록됨.
  const teams = featuredProjects.filter(project => project.owner && project.owner.toLowerCase() !== config.githubUser.toLowerCase());
  const sources = [
    { label: '개인 저장소', load: () => fetchRepositories(fetcher) },
    ...teams.map(project => ({
      label: project.title,
      load: async () => {
        const data = await requestGitHub(`https://api.github.com/repos/${project.owner}/${project.repo}`, fetcher);
        if (!data || Array.isArray(data) || typeof data.name !== 'string' || typeof data.owner?.login !== 'string') {
          throw new Error('GitHub 응답 형식을 확인할 수 없습니다.');
        }
        return [data];
      },
    })),
  ];
  // Promise.allSettled로 각 요청의 성공/실패를 따로 받아 일부 실패해도 성공한 카드는 유지함.
  const results = await Promise.allSettled(sources.map(source => source.load()));
  const repos = [];
  const failures = [];
  results.forEach((result, index) => {
    if (result.status === 'fulfilled') repos.push(...result.value);
    else failures.push({ source: sources[index].label, message: errorMessage(result.reason) });
  });
  if (failures.length === sources.length) {
    throw new Error(`프로젝트를 불러오지 못했습니다. ${failures[0].message}`);
  }
  return { repos, failures };
}
export function initProjects({ onCardsRendered } = {}) {
  const list = document.querySelector('#project-list');
  const status = document.querySelector('#project-status');
  const retry = document.querySelector('#project-retry');
  const language = document.querySelector('#language-filter');
  const categoryButtons = [...document.querySelectorAll('[data-category]')];
  const state = { phase: 'loading', projects: [], error: '', category: 'all', language: 'all', failures: [] };
  const preview = new URLSearchParams(document.location.search).get('preview') === 'projects';
  // 로딩·성공·오류·빈 결과 및 필터 상태를 DOM 목록과 안내 문구에 반영함.
  function render() {
    list.setAttribute('aria-busy', String(state.phase === 'loading'));
    retry.hidden = !['error', 'partial'].includes(state.phase);
    status.dataset.state = state.phase;
    list.replaceChildren();
    if (state.phase === 'loading' || state.phase === 'error') onCardsRendered?.([]);
    categoryButtons.forEach(button => button.setAttribute('aria-pressed', String(button.dataset.category === state.category)));
    language.value = state.language;
    if (state.phase === 'loading') status.textContent = 'GitHub에서 프로젝트를 불러오고 있습니다…';
    else if (state.phase === 'error') status.textContent = state.error;
    else {
      const visible = filterProjects(state.projects, state.category, state.language);
      status.textContent = visible.length ? `${visible.length}개의 프로젝트` : '조건에 맞는 프로젝트가 없습니다. 다른 카테고리나 언어를 선택해 주세요.';
      if (preview) status.textContent += ' · 카드 디자인 미리보기';
      if (state.failures.length) status.textContent += ` · 일부 저장소를 불러오지 못했습니다: ${state.failures.map(failure => `${failure.source} (${failure.message})`).join(', ')}`;
      // filter로 고른 데이터를 map으로 article 카드 DOM으로 변환함.
      const cards = visible.map(card);
      list.append(...cards);
      onCardsRendered?.(cards);
    }
  }
  async function load() {
    // 요청 시작 → 상태 변경 → API 대기 → 성공/오류 상태 변경 → render() 순서로 동작함.
    if (retry.disabled) return;
    state.phase = 'loading'; retry.disabled = true; render();
    try {
      if (preview) {
        state.projects = featuredProjects.map(project => ({
          ...project,
          owner: project.owner || config.githubUser,
          github: project.link || `https://github.com/${project.owner || config.githubUser}/${project.repo}`,
          language: project.technologies[0],
        }));
        state.failures = [];
        state.phase = 'success';
      } else {
        // 구조분해 할당으로 조회 결과에서 저장소와 실패 목록을 각각 꺼냄.
        const { repos, failures } = await fetchProjectSources();
        state.projects = selectProjects(repos); state.failures = failures;
        state.phase = failures.length ? 'partial' : 'success';
      }
      const languages = [...new Set(state.projects.map(project => project.language))].sort();
      language.replaceChildren(new Option('모든 언어', 'all'), ...languages.map(value => new Option(value, value)));
      if (!languages.includes(state.language)) state.language = 'all';
    }
    catch (error) { state.phase = 'error'; state.error = errorMessage(error); }
    finally { retry.disabled = false; render(); }
  }
  // 화살표 함수를 클릭 처리기로 전달함. 필터 이벤트가 상태를 바꾸면 render()가 목록을 다시 만듦.
  categoryButtons.forEach(button => button.addEventListener('click', () => {
    state.category = button.dataset.category; render();
  }));
  language.addEventListener('change', () => { state.language = language.value; render(); });
  retry.addEventListener('click', load);
  load();
}
