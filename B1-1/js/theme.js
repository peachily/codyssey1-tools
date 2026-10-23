const key = 'peachily-theme';
const system = window.matchMedia('(prefers-color-scheme: dark)');
let preference = null;
try {
  const saved = localStorage.getItem(key);
  if (saved === 'light' || saved === 'dark') preference = saved;
} catch { /* Storage may be blocked; the in-memory choice still works. */ }
function render() {
  const theme = preference || (system.matches ? 'dark' : 'light');
  document.documentElement.dataset.theme = theme;
  const button = document.querySelector('#theme-toggle');
  if (!button) return;
  button.setAttribute('aria-pressed', String(theme === 'dark'));
  button.querySelector('use').setAttribute('href', `assets/icons/ui.svg#${theme === 'dark' ? 'sun' : 'moon'}`);
  button.setAttribute('aria-label', theme === 'dark' ? '라이트 모드 켜기' : '다크 모드 켜기');
  document.querySelector('meta[name="theme-color"]').content = theme === 'dark' ? '#211f25' : '#FFFDFC';
}
render();
export function initTheme() {
  document.querySelector('#theme-toggle').addEventListener('click', () => {
    preference = document.documentElement.dataset.theme === 'dark' ? 'light' : 'dark';
    try { localStorage.setItem(key, preference); } catch { /* Keep working without persistence. */ }
    render();
  });
  system.addEventListener('change', render);
  window.addEventListener('storage', event => {
    if (event.key !== key && event.key !== null) return;
    preference = ['light', 'dark'].includes(event.newValue) ? event.newValue : null;
    render();
  });
}
