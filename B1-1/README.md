# peachily.

**교육의 경험을 기술로 이어갑니다.**

초등 특수교사 김수정의 개인 개발 포트폴리오입니다. 교육 현장에서 만든 학습 도구와 학교 업무 도구, 개발 과정을 소개하는 단일 페이지 웹사이트입니다.

- 저장소: https://github.com/peachily/codyssey1-tools (소스 `B1-1/`)
- 목표 배포 주소: https://peachily.dev — **아직 배포·DNS·HTTPS 확인 전**
- 상태: 로컬 구현 및 9단계 커밋. 사용자 지시에 따라 **push하지 않았습니다**.

## 기술과 구조

HTML5 / CSS3 / Vanilla JavaScript (ES Modules). 프레임워크, 빌드 도구, 런타임 패키지, CDN 없이 실행합니다. GitHub REST API와 Formspree를 호출합니다. 시스템 폰트와 공통 UI SVG Sprite, 로컬 브랜드 SVG를 사용합니다.

```text
B1-1/
├── index.html
├── css/                 # 토큰, 기본, 공통 UI, 레이아웃, 반응형
├── js/                  # 기능별 모듈과 공통 기술 배지 매핑
├── assets/              # 이미지, UI·브랜드 아이콘, 출처 및 라이선스
├── tests/               # DOM/로직 자동 검증 (실행에 불필요)
├── docs/                # 배포, 콘텐츠 근거, 체크리스트, 캡처 안내
├── CNAME
└── .nojekyll
```

## 로컬 실행

VS Code에서 `B1-1/index.html`을 Live Server로 열거나, 저장소 루트에서:

```sh
python3 -m http.server 8000
```

http://localhost:8000/B1-1/ 접속. ES Modules 사용으로 `file://` 직접 열기는 지원하지 않습니다. GitHub API를 보려면 인터넷 연결이 필요합니다.

## 주요 기능

- Hero / About / Skills / Projects / Contact / Footer와 반응형 모바일 메뉴
- Skills 3개 그룹·24개 기술 배지, Devicon·Simple Icons 및 공식 OpenAI 로고, 데스크톱 2열·모바일 1열
- Sticky Header(60px), 현재 섹션 표시, 부드러운 앵커 이동, Back-to-top(300px)
- Light/Dark 전환·localStorage 저장·OS 테마 감지·사용자 선택 우선
- IntersectionObserver(threshold 0.2) 스크롤 등장, Hero 제목 타이핑 후 소개 문장 등장, 모션 감소 지원
- Skills·Projects 공유 로고 매핑과 기술 배지, Projects 14px 로고
- 공개 GitHub 저장소 비동기 조회, 선정한 공개 프로젝트 14개(개인 계정 11·조직 3), 생성일 최신순 정렬, 카테고리+주 언어 복합 필터
- API 로딩/오류/빈 결과/재시도, 403·429 제한·타임아웃 처리, 조직 API 부분 실패 시 성공 카드 유지
- Contact 필드별 검증·전송 상태·중복 제출 방지, 사용자 제공 Formspree endpoint로 POST
- 키보드 포커스, ARIA 상태, skip link, SVG 재사용, 외부 링크 보호

## 설정과 제출

`js/config.js`에서 대표 저장소와 연락 서비스·소셜 URL을 관리합니다. **Formspree endpoint는 연결했으며 실제 이메일 수신 확인은 남아 있습니다.** YouTube·Blog와 복숭아 이미지는 사용자 제공 정보로 연결했습니다. MADI 미확인 링크는 만들지 않았습니다.

- [배포 및 사용자 설정](docs/deployment.md): GitHub Pages 수동 배포, Cloudflare, Formspree 연결
- [요구사항별 전체 체크리스트](docs/checklist.md): 완료·미완료 구분, 이벤트→상태→렌더링 7개 사례
- [콘텐츠·기술의 근거](docs/content-sources.md)
- [이미지 관리](assets/README.md)
- [Formspree 처음 연결하기](docs/formspree.md)

## 스크린샷

**현재 미첨부:** 연결 가능한 브라우저가 없어 실제 화면 캡처를 생성하지 못했습니다. [캡처 규격과 파일명](docs/screenshots.md)에 따라 데스크톱·모바일·다크 모드 이미지를 추가해야 제출 자료가 완성됩니다. 가짜 이미지나 깨진 이미지 링크는 사용하지 않았습니다.

## 자동 검증

모든 JS 문법 검사, DOM/로직 **23개 테스트 통과**. 실제 GitHub API 14개 프로젝트 매칭·생성일 정렬과 로컬 HTTP 200 확인. 실제 레이아웃과 이메일 수신은 미검증입니다.

사이트 실행에는 테스트 도구가 필요 없습니다. 재검증 시 Node.js 22.13 이상과 별도 임시 경로의 jsdom이 필요합니다:

```sh
npm install --prefix /tmp/peachily-qa jsdom@29.1.1 --no-audit --no-fund
JSDOM_PATH=/tmp/peachily-qa/node_modules/jsdom/lib/api.js node --test B1-1/tests/portfolio.test.mjs
```

Formspree 요청은 테스트에서 모의 응답을 사용하며 실제 전송하지 않습니다. 테스트는 실제 브라우저와 스크린리더 검증을 대신하지 않습니다.
