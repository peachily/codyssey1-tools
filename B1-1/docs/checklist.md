# 요구사항별 검증 체크리스트

기준: 사용자가 제공한 상세 요청 + 후속 B1-1 구현용 요약. 별도의 과제 원문 파일은 전달되지 않았으므로 원문과의 추가 대조는 수행하지 않았습니다.
최종 수정 확인일: 2026-10-23. `[x]`는 구현·해당 수준의 검증 완료, `[ ]`는 남은 외부 설정 또는 실제 화면 검증입니다.

## 구성·콘텐츠

- [x] peachily 워드마크, 한국어 중심 단일 스크롤 페이지, 확정된 Hero 문구 및 2개 CTA
- [x] Header / Hero / About / Skills / Projects / Contact / Footer, 섹션 내비게이션
- [x] About 자기소개 의미 유지, 학교·출신 대학명 제외, 제공된 복숭아 이미지
- [x] 사용자 확정 기술 24개·3개 그룹, 기술 숙련도 과장 없음
- [x] 크림색 카드·흰색 배지, 로컬 브랜드 로고 24개·Skills에서 REST API 제외, 18px·2열/1열
- [x] 에셋을 assets/images·icons·licenses로 관리, 원본 로고 출처·라이선스 기록
- [x] 지정 공개 저장소 11개, 교육용·학교 업무용·개발 프로젝트 분류
- [x] MADI 미확인 조직 링크 및 프로젝트 카드 생성 안 함
- [x] 이름·이메일·메시지, 사용자 이메일, Footer GitHub·Instagram·저작권
- [x] YouTube·Blog 사용자 제공 URL 연결, Footer 아이콘으로 표시
- [x] 제공된 assets/images/peachily.jpg 연결 — Hero·About, 원본 보존

## HTML·CSS·접근성

- [x] header/nav/main/section/article/footer, 단일 h1과 h2/h3 계층
- [x] 모든 폼 label 연결, 실제 이미지 alt, 장식 SVG aria-hidden
- [x] 외부 CSS·JS, 프레임워크·빌드 도구·런타임 외부 라이브러리 없음
- [x] :root 토큰: 팔레트·시맨틱 색상·타이포·간격·폭·radius·shadow·transition
- [x] [data-theme="dark"], Mobile First, 768px/1024px 미디어 쿼리
- [x] Flexbox 헤더, Grid repeat(auto-fit, minmax(...)) 프로젝트 카드
- [x] hover/focus-visible/transition, 44px 이상 주요 터치 컨트롤
- [x] aria-expanded/aria-pressed/aria-current, skip link, Escape로 메뉴 닫기·포커스 복귀
- [x] 폼 오류 aria-describedby/aria-invalid, status live region, 로딩 aria-busy
- [x] prefers-reduced-motion, 재사용 SVG Sprite, 외부 링크 rel 보호
- [x] 대표 본문 텍스트 색상 조합 5개의 대비 4.5:1 이상 계산 검사
- [ ] 320/390/768/1024/1440px 실제 레이아웃·잘림·가로 스크롤 점검
- [ ] 실제 브라우저 키보드·스크린리더·200% 확대·전체 색상 조합 점검

## JavaScript 필수

- [x] const/let, map/forEach/filter, DOM 조회·생성·수정, 이벤트 리스너
- [x] click/input/submit/scroll 처리, 제출 preventDefault, 인라인 이벤트·스타일 없음
- [x] 메뉴 .active 전환, Escape/링크 클릭/외부 클릭/포커스 이탈 시 닫기
- [x] CSS smooth와 JS anchor 이동, 모션 감소 시 즉시 이동, 이동 후 목표 포커스
- [x] scrollY > 60 Header 변화, scrollY > 300 Back-to-top (경계 자동 테스트)
- [x] 테마 localStorage, 접근 제한 시 메모리 선택 유지, OS 감지, 저장 선택 우선, 태양·달 아이콘 전환
- [x] IntersectionObserver threshold **0.2**, 등장 후 unobserve, 모션 감소 대응
- [x] async/await·fetch로 개인 GitHub `/users/peachily/repos` 조회, 페이지네이션
- [x] API Loading / Success / Empty / Error / Retry DOM 상태
- [x] 403·429 요청 제한, 500·네트워크·잘못된 응답·타임아웃 처리
- [x] 설정 데이터와 API 책임 분리, 유효 공개 저장소만 표시, HTTPS 링크 검증
- [x] 카테고리와 언어 조건 AND 적용 및 빈 결과 메시지, 필터 후 생성일 정렬 유지
- [x] 텍스트 중심 카테고리별 파스텔 카드, 전체 링크·키보드 접근·화살표 hover, 검증된 기술 태그
- [x] 폼 공백·이메일·메시지 길이 검증, 필드 오류·포커스, 입력 수정 시 갱신
- [x] 전송 중 재제출 차단·상태, 오류 시 내용 보존, 성공 시 초기화 (모의 응답 테스트)

## 이벤트 → 상태 → DOM 사례 (요구 3개 이상, 구현 7개)

| 이벤트 | 상태 | 렌더링 |
| --- | --- | --- |
| 메뉴 버튼 click | menuOpen | .active, aria-expanded, 버튼 이름 |
| scroll | scrolled/showTop/section | Header 클래스, Back-to-top hidden, aria-current |
| 테마 click/OS change | preference/시스템 테마 | data-theme, aria-pressed, meta theme-color |
| 카테고리 click | category | 버튼 선택·필터 결과·개수 |
| 언어 change | language | 복합 필터 카드·empty 안내 |
| 다시 불러오기 click → fetch 완료/실패 | phase/projects/error | loading/busy/error/retry/cards |
| 폼 input/submit → fetch 완료/실패 | errors/phase/message | 필드 오류·disabled·성공/실패 메시지 |

## 보너스 4개

- [x] ① 프로젝트 언어 필터 — filter() 및 카테고리 복합 적용
- [x] ② JavaScript Hero 타이핑 — 큰 제목에서 1회, 완료 후 소개 문장 등장, reduced motion 대응
- [x] ③ Formspree 연동 코드 — 설정 전 성공 가장 없음, 설정 방법 안내
- [ ] ③ **실제 이메일 수신 검증** — endpoint 연결 완료, 실제 전송·수신 테스트는 아직 수행하지 않음
- [x] ④ 시스템 테마 — prefers-color-scheme, 사용자 저장 선택 우선

## 배포·제출

- [x] GitHub Pages 수동 워크플로, B1-1 정적 파일만 업로드, CNAME/.nojekyll
- [x] Cloudflare 공식 GitHub DNS 값·도메인 검증·HTTPS 안내
- [x] README: 소개·기술·실행·기능·목표 URL·구조·설정·검증
- [x] 저장소 URL 기록, 로컬 9단계 커밋
- [ ] 원격 push — 사용자가 허락하기 전 보류
- [ ] GitHub Pages 실제 배포·Custom domain·도메인 소유 검증·HTTPS
- [ ] README용 및 제출용 desktop/mobile/dark 실제 화면 캡처 — 브라우저 없음

## 수행한 검증과 한계

- `node --check` 모든 JS 통과.
- Node test + jsdom **18/18 통과**. 테스트 의존성은 /tmp에만 설치, 사이트는 의존성 없음.
- 테스트 범위: HTML ID/label/anchor/로컬 에셋, 대표 저장소 필터, 복합 필터, URL, 페이지네이션, API 오류, API DOM 상태, 폼 검증·모의 전송, 메뉴/스크롤, 테마, 모션 감소·threshold, CSS 조건/대표 대비.
- 실제 GitHub API 응답에서 지정 저장소 11개 매칭·created_at 내림차순 확인.
- 로컬 HTTP HEAD 200 확인. 외부 HTTPS는 DNS 해석 실패.
- jsdom은 실제 CSS 레이아웃·페인팅·접근성 트리를 검증하지 않습니다. 모의 POST는 실제 메일 전달을 검증하지 않습니다.
- 브라우저 skill 연결은 `No browser is available`, 목록은 `[]`. 복구 확인 후 실제 화면 검증은 미완료로 남겼습니다.

2026-10-23 Skills 변경 추가 검증: 17개 원본 SVG를 렌더링해 18px 배지의 라이트·다크 색상 조합에서 시각 확인했습니다. Railway 흰 로고는 짙은 원형 배경으로 보완했습니다. 브라우저 목록이 비어 있어 실제 웹 페이지 레이아웃 검증은 계속 미완료입니다. Projects CSS와 복숭아 이미지 바이트가 기존과 동일한 것도 확인했습니다.
