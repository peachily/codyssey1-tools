# Mini Git CLI

## 1. 프로젝트 소개

Git의 커밋과 브랜치를 직접 구현하며 그래프, 탐색, 정렬, 역색인을 학습하는 메모리 기반 CLI 프로그램입니다. Python 3.10 이상과 표준 라이브러리만 사용합니다.

## 2. 프로젝트 구조

| 파일 | 역할 |
| --- | --- |
| `main.py` | 사용자 입력, 명령어 파싱, 결과 출력 |
| `mini_git.py` | 저장소 상태, 브랜치 관리, 커밋 생성 |
| `commit.py` | Commit 데이터 구조 |
| `graph.py` | 위상 정렬, 최단 경로 및 조상 탐색 |
| `index.py` | 키워드·작성자 역색인 |
| `sorting.py` | Merge Sort |
| `tests/test_mini_git.py` | unittest 자동화 테스트 |
| `README.md` | 프로그램 소개와 사용법 |

## 3. 실행 방법

B5-2 디렉터리에서 실행합니다.

```sh
python main.py
```

테스트 실행:

```sh
python -m unittest discover -s tests -v
```

## 4. 주요 명령어

| 명령어 | 기능 |
| --- | --- |
| `INIT <user_name>` | 저장소 초기화, 사용자 설정, main 브랜치 생성 |
| `BRANCH <branch_name>` | 현재 HEAD를 가리키는 브랜치 생성 |
| `SWITCH <branch_name>` | 현재 브랜치 전환 |
| `COMMIT <message>` | 현재 브랜치에 커밋 생성 |
| `LOG` | 모든 저장된 커밋을 부모 우선으로 출력 |
| `LOG --sort-by=date` | 날짜 오름차순 로그 |
| `LOG --sort-by=author` | 작성자 오름차순 로그 |
| `PATH <commit1> <commit2>` | 두 커밋 사이의 최단 경로 |
| `ANCESTORS <commit_hash>` | 지정한 커밋의 모든 조상 조회 |
| `SEARCH <keyword>` | 키워드 검색 |
| `SEARCH --author=<name>` | 작성자 검색 |
| `exit` / `quit` | 프로그램 종료 |

공백을 포함하는 인자는 `COMMIT "Start project"`처럼 따옴표로 감쌉니다.

## 5. 실행 예시

```text
mini-git> INIT peachily
Initialized main | user: peachily
mini-git> COMMIT "Start project"
000001 | peachily | 2026-10-08T06:00:00+00:00 | Start project
mini-git> BRANCH feature
Created branch: feature
mini-git> SWITCH feature
Switched to: feature
mini-git> COMMIT "Add search"
000002 | peachily | 2026-10-08T06:01:00+00:00 | Add search
mini-git> LOG
000001 | peachily | 2026-10-08T06:00:00+00:00 | Start project
000002 | peachily | 2026-10-08T06:01:00+00:00 | Add search
mini-git> PATH 000001 000002
000001 -> 000002
mini-git> SEARCH search
000002 | peachily | 2026-10-08T06:01:00+00:00 | Add search
```

시각은 예시이며, 실제 실행 시 커밋 생성 시각을 표시합니다.

## 6. 핵심 자료구조 및 알고리즘

### 커밋 그래프와 DAG

- 커밋은 부모 커밋의 hash를 저장하며, 새 커밋은 현재 브랜치의 HEAD를 부모로 연결합니다.
- 이미 존재하는 커밋만 부모가 되고 기존 부모 관계는 바뀌지 않으므로 순환이 없는 DAG를 이룹니다.
- 커밋은 dict에 저장하여 hash로 평균 O(1)에 조회합니다.

### 부모 우선 로그와 위상 정렬

- 기본 `LOG`는 생성 이력을 따라 부모가 자식보다 먼저 나오도록 위상 정렬을 사용합니다.
- Kahn 알고리즘으로 미처리 부모가 없는 커밋부터 출력하고, 해당 자식의 미처리 부모 수를 줄여 다음 출력 대상을 결정합니다.
- 모든 저장된 커밋을 대상으로 하므로 다른 브랜치의 이력도 포함합니다.

### 최단 경로와 조상 탐색

- `PATH`는 부모·자식 연결을 무방향 간선으로 보고 BFS로 최소 간선 수의 경로를 찾습니다.
- 목적지까지의 거리를 계산한 뒤, 거리가 1 감소하는 이웃 중 최소 hash를 선택하여 최단 경로 동률 시 전체 경로의 사전순 최소를 보장합니다.
- `ANCESTORS`는 부모 방향 BFS로 탐색하고 중복 방문을 막으며, 시작 커밋을 제외한 조상을 거리순으로 출력하고 같은 거리에서는 hash 오름차순을 적용합니다.

### 정렬 알고리즘

- 직접 구현한 Merge Sort로 날짜 또는 작성자 오름차순 정렬을 수행하며, 같은 값에서는 hash 오름차순을 적용합니다.
- 원소를 절반으로 나누고 정렬된 부분을 병합하므로 N개 원소의 평균·최악 시간복잡도는 모두 O(N log N)입니다.
- 병합 시 비교 키가 같으면 왼쪽 원소를 먼저 선택하여 안정 정렬을 유지하고, 입력을 복사하여 원본 순서를 보존합니다.

### 역색인

- `keyword → commit hash 목록`, `author → commit hash 목록`을 저장하여 관련 커밋만 조회합니다.
- 키워드는 `split()`과 `lower()`로 처리하고 같은 커밋의 중복 키워드는 한 번만 색인에 추가합니다.
- 문자열 처리 비용을 제외하면 전체 V개 커밋을 확인하는 O(V) 순회 대신, 평균 O(1) 색인 조회와 O(K) 결과 처리가 필요하며 K는 검색 결과 수입니다.
- 결과는 커밋 생성 순서로 반환하며, 화면 출력 비용은 결과 텍스트 길이에 비례합니다.
