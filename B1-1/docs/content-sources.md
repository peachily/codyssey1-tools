# 콘텐츠와 기술 선정 근거

확인일: 2026-10-23. 자기소개는 사용자 제공 내용이며, 프로젝트 설명·태그는 아래 공개 저장소의 README와 소스에서 확인했습니다.

| 저장소 | 한 줄 소개 근거 | 기술 태그 근거 |
| --- | --- | --- |
| school01-numbermonster | [README](https://github.com/peachily/school01-numbermonster/blob/main/README.md): 수준별 1~9 수 읽기 | public/index.html, public/app.js, CSS, server.js, package.json → HTML/CSS/JavaScript/Node.js |
| school02-countcake | [README](https://github.com/peachily/school02-countcake/blob/main/README.md): 교사·학생 화면과 1~9 개수 세기 | public/index.html, public/app.js, CSS, server.js, package.json → HTML/CSS/JavaScript/Node.js |
| school04-pet-simulator | [usePetGame.js](https://github.com/peachily/school04-pet-simulator/blob/main/src/hooks/usePetGame.js), src/data/pets/dog.js: 먹이·놀이·산책 요청 해결. 루트 README 없음 | [package.json](https://github.com/peachily/school04-pet-simulator/blob/main/package.json), JS/JSX 소스 → JavaScript/React/Vite |
| school05-animal-rescue | [README](https://github.com/peachily/school05-animal-rescue/blob/main/README.md), js/tensComplement.js: 10의 보수를 맞추는 동물 구출 게임 | index.html, css/, js/ → HTML/CSS/JavaScript |
| school06-snack-market | [README](https://github.com/peachily/school06-snack-market/blob/main/README.md): 현금 이동으로 네 자리 수와 자릿값 학습 | [apps/web/package.json](https://github.com/peachily/school06-snack-market/blob/main/apps/web/package.json), TSX/CSS 소스 → TypeScript/React/Tailwind CSS |
| school03-lunch-menu-extractor | [lunch_menu_extractor.py](https://github.com/peachily/school03-lunch-menu-extractor/blob/main/lunch_menu_extractor.py): HWPX 급식표를 날짜별 텍스트로 저장 | Python 표준 라이브러리 tkinter, xml.etree.ElementTree → Python/Tkinter/XML |
| codyssey0-python | 루트 README는 저장소 제목뿐. [4-2/inventory_manager.py](https://github.com/peachily/codyssey0-python/blob/main/4-2/inventory_manager.py): CSV 재고 분석과 파일 저장 | 같은 소스의 csv/pickle 사용 → Python/CSV |
| codyssey0-devops | [1-2/README](https://github.com/peachily/codyssey0-devops/blob/main/1-2/README.md), 1-2/app.py: Flask 메뉴판 | app.py의 Flask/render_template, templates/menu.html → Python/Flask/HTML |
| codyssey1-selection | [E1-2/README](https://github.com/peachily/codyssey1-selection/blob/main/E1-2/README.md): 퀴즈·점수 저장, E1-1/README: Docker·Git 실습 | Python 소스, Dockerfile/Compose 및 문서 → Python/Docker/Git |
| codyssey1-tools | [B3-2/README](https://github.com/peachily/codyssey1-tools/blob/main/B3-2/README.md): AI 커밋·PR 초안 CLI, B5-1/2의 자료구조 구현 | Python 소스, Git 명령·API 클라이언트 → Python/Git/REST API |
| codyssey1-termproject | [README](https://github.com/peachily/codyssey1-termproject/blob/main/README.md): 까무룩 대화·마법약 처방 서비스 | requirements.txt와 frontend/package.json → Python/FastAPI/React/SQLAlchemy |

## API와 수동 설정의 역할

- `featuredProjects`는 위 11개의 선택·제목·카테고리·설명·검증한 기술 태그를 관리합니다. 배열 순서가 화면 순서를 결정하지 않습니다.
- 개인 `/users/peachily/repos` API의 공개 저장소·소유자·유효 HTTPS URL을 매칭하고 `created_at` 내림차순으로 명시적 정렬합니다. 동률은 저장소 이름으로 정렬합니다. 생성일이 없는 비정상 응답은 마지막으로 보냅니다.
- API 요청은 `sort=created&direction=desc`를 명시하고 페이지네이션합니다. 화면에서도 별도로 정렬하므로 기본 응답 순서에 의존하지 않습니다.
- `updated_at`과 `pushed_at`은 사용하지 않습니다. 필터는 이미 정렬된 목록에 적용하여 순서를 보존합니다.
- 언어 필터는 API의 저장소 **주 언어**를 사용합니다. 기술 태그는 실제 사용 기술 여러 개를 나타내며, 언어 필터와 역할이 다릅니다.
- 2026-10-23 실제 개인 API에서 11개 공개 저장소 매칭과 생성일 순서를 확인했습니다. 첫 카드 school06-snack-market, 마지막 카드 codyssey0-devops입니다.

이번 카드는 텍스트 중심으로 구성하며 이미지 영역을 만들지 않습니다. README의 장식 이미지나 게임 에셋을 실제 화면 캡처처럼 사용하지 않습니다. 카드 전체 링크는 GitHub 저장소 하나로 연결합니다.

Skills는 검증된 기존 기술 3개 그룹을 유지하고 크림 계열로 통일했습니다. 프로젝트의 React 등은 해당 프로젝트의 기술 태그로 표시되며, 이 포트폴리오 구현은 계속 Vanilla JavaScript입니다.

YouTube·Blog·Instagram과 images/peachily.jpg는 사용자 제공 정보입니다. MADI 조직 저장소의 미확인 링크는 생성하지 않았습니다.
