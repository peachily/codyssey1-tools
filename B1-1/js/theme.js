const key = 'peachily-theme';
const system = window.matchMedia('(prefers-color-scheme: dark)');
let preference = null;
// 저장한 사용자 선택이 있으면 시스템 테마보다 우선 적용함.
try {
  const saved = localStorage.getItem(key);
  if (saved === 'light' || saved === 'dark') preference = saved;
} catch { /* 저장소를 사용할 수 없어도 현재 페이지에서는 테마 선택을 유지함. */ }
function render() {
  const theme = preference || (system.matches ? 'dark' : 'light');
  // data-theme 속성이 바뀌면 CSS의 다크 모드 변수가 적용됨.
  document.documentElement.dataset.theme = theme;
  const button = document.querySelector('#theme-toggle');
  if (!button) return;
  button.querySelector('use').setAttribute('href', `assets/icons/ui.svg#${theme === 'dark' ? 'sun' : 'moon'}`);
  button.setAttribute('aria-label', theme === 'dark' ? '라이트 모드 켜기' : '다크 모드 켜기');
  document.querySelector('meta[name="theme-color"]').content = theme === 'dark' ? '#211f25' : '#FFFDFC';
}
render();
export function initTheme() {
  // 버튼 클릭 → 선택한 테마 저장 → render()가 DOM 속성과 아이콘을 갱신함.
  document.querySelector('#theme-toggle').addEventListener('click', () => {
    preference = document.documentElement.dataset.theme === 'dark' ? 'light' : 'dark';
    try { localStorage.setItem(key, preference); } catch { /* 저장에 실패해도 현재 테마 전환은 동작함. */ }
    render();
  });
  system.addEventListener('change', render);
  window.addEventListener('storage', event => {
    if (event.key !== key && event.key !== null) return;
    preference = ['light', 'dark'].includes(event.newValue) ? event.newValue : null;
    render();
  });
}
