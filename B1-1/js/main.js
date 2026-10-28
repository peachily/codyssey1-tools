// HTML에서 불러오는 시작점: 기능별 모듈을 가져와 각각 초기화함.
import { initTheme } from './theme.js';
import { initNavigation } from './navigation.js';
import { initProjects } from './projects.js';
import { initAnimations } from './animations.js';
import { initContact } from './contact.js';
import { initSkills } from './technologies.js';

document.documentElement.classList.remove('no-js');

// 입력 필드는 마우스로 눌러도 :focus-visible이 잡힐 수 있어 포인터/키보드 입력을 구분함.
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
// API로 뒤늦게 생성된 프로젝트 카드도 스크롤 등장 효과의 관찰 대상에 추가함.
initProjects({ onCardsRendered: observeReveals });
initContact();

document.querySelector('#copyright-year').textContent = new Date().getFullYear();
