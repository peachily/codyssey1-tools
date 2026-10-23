import { initTheme } from './theme.js';
import { initNavigation } from './navigation.js';
import { initProjects, safeUrl } from './projects.js';
import { initAnimations } from './animations.js';
import { initContact } from './contact.js';
import { config } from './config.js';
import { initSkills } from './technologies.js';

initTheme();
initNavigation();
initSkills();
initProjects();
initAnimations();
initContact();

document.querySelector('#copyright-year').textContent = new Date().getFullYear();
[['#youtube-link', config.youtubeUrl], ['#blog-link', config.blogUrl]].forEach(([selector, value]) => {
  const url = safeUrl(value);
  if (url) {
    const link = document.querySelector(selector);
    link.href = url;
    link.hidden = false;
  }
});
