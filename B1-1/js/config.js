// Public configuration only. Never put API keys or email service secrets here.
export const config = {
  githubUser: 'peachily',
  formEndpoint: '', // https://formspree.io/f/<your verified public form ID>
  youtubeUrl: '',
  blogUrl: '',
};
export const categories = { education: '교육용', school: '학교 업무용', development: '개발 프로젝트' };
// Editorial metadata: selection/order/title/category/description and verified demo URL.
// API owns repository existence, primary language, GitHub URL and API description fallback.
// Evidence and verification dates are recorded in docs/content-sources.md.
export const featuredProjects = [
  { repo: 'school01-numbermonster', title: '숫자 몬스터 잡기', category: 'education', description: '학생별 학습 수준에 맞춰 1부터 9까지의 수 읽기를 연습하는 교육용 게임.', demo: '' },
  { repo: 'school02-countcake', title: '케이크 만들기', category: 'education', description: '교사와 학생의 화면을 연결해 1부터 9까지의 개수 세기를 연습하는 학습 도구.', demo: '' },
  { repo: 'school03-lunch-menu-extractor', title: '급식 메뉴 추출 도구', category: 'school', description: 'HWPX 급식표에서 날짜별 메뉴를 추출하고 텍스트 파일로 정리하는 Python 도구.', demo: '' },
  { repo: 'codyssey1-tools', title: '배움의 기록, Codyssey', category: 'development', description: '개발 도구를 익히고 직접 구현한 과제들을 모은 저장소. 이 포트폴리오도 함께 만들어 갑니다.', demo: '' },
];
