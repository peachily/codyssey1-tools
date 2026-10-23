import { initTheme } from './theme.js';
import { initNavigation } from './navigation.js';
initTheme();
initNavigation();
document.querySelector('#copyright-year').textContent = new Date().getFullYear();
import { initProjects } from './projects.js';
initProjects();
import { initAnimations } from './animations.js';
initAnimations();
