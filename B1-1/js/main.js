import { initTheme } from './theme.js';
import { initNavigation } from './navigation.js';
initTheme();
initNavigation();
document.querySelector('#copyright-year').textContent = new Date().getFullYear();
