import { initTheme } from './theme.js';
import { initNavigation } from './navigation.js';
import { initProjects } from './projects.js';
import { initAnimations } from './animations.js';
import { initContact } from './contact.js';
import { initSkills } from './technologies.js';

document.documentElement.classList.remove('no-js');

// Text fields can match :focus-visible even after a pointer click.
document.addEventListener('pointerdown', () => {
  document.documentElement.setAttribute('data-pointer-focus', '');
}, { capture: true });
document.addEventListener('keydown', event => {
  if (event.key === 'Tab') document.documentElement.removeAttribute('data-pointer-focus');
}, { capture: true });

initTheme();
initNavigation();
initSkills();
const observeReveals = initAnimations();
initProjects({ onCardsRendered: observeReveals });
initContact();

document.querySelector('#copyright-year').textContent = new Date().getFullYear();
