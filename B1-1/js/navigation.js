export function initNavigation() {
  const header = document.querySelector('.site-header');
  const menu = document.querySelector('#navigation');
  const toggle = document.querySelector('#menu-toggle');
  const top = document.querySelector('#back-to-top');
  const links = [...menu.querySelectorAll('a')];
  const sections = links.map(link => document.querySelector(link.hash));
  const desktop = window.matchMedia('(min-width: 768px)');
  const state = { menuOpen: false, scrolled: false, showTop: false, section: '' };
  function render() {
    menu.classList.toggle('active', state.menuOpen);
    toggle.setAttribute('aria-expanded', String(state.menuOpen));
    toggle.setAttribute('aria-label', state.menuOpen ? '메뉴 닫기' : '메뉴 열기');
    header.classList.toggle('scrolled', state.scrolled);
    top.hidden = !state.showTop;
    links.forEach(link => {
      if (link.hash === `#${state.section}`) link.setAttribute('aria-current', 'location');
      else link.removeAttribute('aria-current');
    });
  }
  function closeMenu(returnFocus = false) {
    state.menuOpen = false;
    render();
    if (returnFocus) toggle.focus();
  }
  toggle.addEventListener('click', () => { state.menuOpen = !state.menuOpen; render(); });
  document.addEventListener('keydown', event => {
    if (event.key === 'Escape' && state.menuOpen) closeMenu(true);
  });
  document.addEventListener('click', event => {
    if (state.menuOpen && !header.contains(event.target)) closeMenu();
  });
  header.addEventListener('focusout', event => {
    if (state.menuOpen && !header.contains(event.relatedTarget)) closeMenu();
  });
  desktop.addEventListener('change', () => {
    if (!desktop.matches && menu.contains(document.activeElement)) toggle.focus();
    closeMenu();
  });
  document.querySelectorAll('a[href^="#"]').forEach(link => {
    link.addEventListener('click', event => {
      const target = document.querySelector(link.hash);
      if (!target) return;
      event.preventDefault();
      closeMenu();
      target.setAttribute('tabindex', '-1');
      target.focus({ preventScroll: true });
      target.scrollIntoView({ behavior: matchMedia('(prefers-reduced-motion: reduce)').matches ? 'instant' : 'smooth' });
      history.replaceState(null, '', link.hash);
    });
  });
  let scheduled = false;
  function updateScroll() {
    state.scrolled = window.scrollY > 60;
    state.showTop = window.scrollY > 300;
    state.section = sections.filter(section => section.getBoundingClientRect().top <= 180).at(-1)?.id || '';
    render();
    scheduled = false;
  }
  window.addEventListener('scroll', () => {
    if (!scheduled) { scheduled = true; requestAnimationFrame(updateScroll); }
  }, { passive: true });
  updateScroll();
}
