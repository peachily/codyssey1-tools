// Public configuration only. Never put API keys or email service secrets here.
export const config = {
  githubUser: 'peachily',
  formEndpoint: 'https://formspree.io/f/mnppayoo',
  youtubeUrl: 'https://www.youtube.com/@peachily_log',
  blogUrl: 'https://peachily.tistory.com/',
};
export const categories = { education: '교육용', school: '학교 업무용', development: '개발 프로젝트' };
// Editorial metadata: selection/title/category/description/verified technologies.
// API owns public existence, primary language, GitHub URL and creation-date ordering.
// Evidence is recorded in docs/content-sources.md. Array order is not display order.
export const featuredProjects = [
  { repo: 'school01-numbermonster', title: '숫자 몬스터 잡기', category: 'education', description: '학생별 수준에 맞춰 1부터 9까지의 수 읽기를 연습하는 게임.', technologies: ['JavaScript', 'HTML', 'CSS', 'Node.js'] },
  { repo: 'school02-countcake', title: '케이크 만들기', category: 'education', description: '교사와 학생의 화면을 연결해 1부터 9까지 개수 세기를 연습하는 게임.', technologies: ['JavaScript', 'HTML', 'CSS', 'Node.js'] },
  { repo: 'school04-pet-simulator', title: '반려동물 돌보기', category: 'education', description: '먹이 주기·놀아 주기·산책으로 반려동물의 요청을 해결하는 활동.', technologies: ['JavaScript', 'React', 'Vite'] },
  { repo: 'school05-animal-rescue', title: '동물 구조 게임', category: 'education', description: '두 수의 합을 10으로 맞춰 로켓에 탄 동물을 구출하는 덧셈 게임.', technologies: ['JavaScript', 'HTML', 'CSS'] },
  { repo: 'school06-snack-market', title: '얼마일까요?', category: 'education', description: '과자 가격에 맞춰 돈을 옮기며 네 자리 수와 자릿값을 익히는 활동.', technologies: ['TypeScript', 'React', 'Tailwind CSS'] },
  { repo: 'school03-lunch-menu-extractor', title: '급식 메뉴 추출 도구', category: 'school', description: 'HWPX 급식표에서 날짜별 메뉴를 추출해 텍스트로 정리하는 도구.', technologies: ['Python', 'Tkinter', 'XML'] },
  { repo: 'codyssey0-python', title: 'Codyssey · Python', category: 'development', description: 'CSV 재고 분석과 파일 저장 등 Python 기초를 구현한 학습 기록.', technologies: ['Python', 'CSV'] },
  { repo: 'codyssey0-devops', title: 'Codyssey · DevOps', category: 'development', description: 'Flask 메뉴판 웹 앱과 템플릿을 만들며 익힌 웹 개발 실습.', technologies: ['Python', 'Flask', 'HTML'] },
  { repo: 'codyssey1-selection', title: 'Codyssey · Selection', category: 'development', description: 'Python 퀴즈 게임과 Docker 개발 환경 구축을 담은 실습 기록.', technologies: ['Python', 'Docker', 'Git'] },
  { repo: 'codyssey1-tools', title: 'Codyssey · Tools', category: 'development', description: 'AI 커밋 초안 도구부터 자료구조 구현까지 개발 도구를 익힌 기록.', technologies: ['Python', 'Git', 'REST API'] },
  { repo: 'codyssey1-termproject', title: '까무룩 · KKAMURUK', category: 'development', description: '잠들기 어려운 밤, 대화와 마법약 처방으로 위로를 전하는 웹 서비스.', technologies: ['Python', 'FastAPI', 'React', 'SQLAlchemy'] },
];
