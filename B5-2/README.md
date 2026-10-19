# Mini Git CLI

**Git 커밋 구조 기반 자료구조·알고리즘 구현**

`Hash Map` · `DAG` · `Topological Sort` · `BFS` · `Merge Sort` · `Inverted Index`

## 1. 프로젝트 구조

| 파일 | 역할 |
|---|---|
| `main.py` | CLI 입력·파싱·출력 |
| `mini_git.py` | 저장소·브랜치·커밋 관리 |
| `commit.py` | Commit 데이터 구조 |
| `graph.py` | 위상 정렬 및 그래프 탐색 |
| `index.py` | 키워드·작성자 역색인 |
| `sorting.py` | Merge Sort |
| `tests/test_mini_git.py` | 자동화 테스트 |

- **모듈화:** 저장소 관리, 그래프 탐색, 검색, 정렬 로직 분리
- **코드 문서화:** 주요 클래스·함수의 간결한 docstring

## 2. 실행 방법

Python 3.10 이상에서 표준 라이브러리만 사용합니다. 아래 명령은 `B5-2` 디렉터리에서 실행합니다.

**프로그램 실행**

```bash
python main.py
```

**테스트 실행**

```bash
python -m unittest discover -s tests -v
```

## 3. 주요 명령어

| 명령어 | 기능 |
|---|---|
| `INIT <user_name>` | 저장소 초기화 및 사용자 설정 |
| `BRANCH <branch_name>` | 현재 HEAD 기준 브랜치 생성 |
| `SWITCH <branch_name>` | 브랜치 전환 |
| `COMMIT <message>` | 현재 브랜치에 커밋 생성 |
| `LOG` | 부모 우선 커밋 로그 |
| `LOG --sort-by=date` | 날짜 오름차순 정렬 |
| `LOG --sort-by=author` | 작성자 오름차순 정렬 |
| `PATH <commit1> <commit2>` | 최단 경로 탐색 |
| `ANCESTORS <commit_hash>` | 모든 조상 커밋 조회 |
| `SEARCH <keyword>` | 메시지 키워드 검색 |
| `SEARCH --author=<name>` | 작성자 검색 |
| `exit` / `quit` | 프로그램 종료 |

**입력 규칙:** 명령어 대소문자 구분 없음 · 공백 포함 인자는 따옴표 사용

## 4. 실행 예시

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

## 5. 핵심 자료구조 및 알고리즘

### 5.1. 커밋과 브랜치 관리 — Hash Map

**Hash Map(해시맵)**은 Key와 Value를 쌍으로 저장하는 자료구조로, 특정 Key를 이용해 데이터를 빠르게 조회할 수 있습니다.

Mini Git에서는 커밋과 브랜치를 각각 딕셔너리로 관리합니다.

| 구성 요소 | 저장 정보 | 역할 |
|---|---|---|
| `Commit` | hash, message, author, timestamp, parents | 커밋 정보 |
| `commits` | hash → Commit | 커밋 저장 및 조회 |
| `branches` | 브랜치명 → HEAD hash 또는 None | 브랜치별 최신 커밋 관리, 커밋이 없으면 None |
| `current_branch` | 브랜치명 | 현재 작업 브랜치 |
| `user` | 사용자명 | 커밋 작성자 |

**커밋 생성 과정**

```text
COMMIT "Add login"
       │
       ▼
  새 커밋 생성
       │
       ├── hash       고유 ID 생성
       ├── message    커밋 메시지
       ├── author     현재 사용자
       ├── timestamp  생성 시각
       └── parents    현재 HEAD
       │
       ▼
  commits에 저장
       │
       ├── 현재 브랜치 HEAD 갱신
       └── 검색용 역색인 갱신
```

- **조회 성능:** 딕셔너리 기반 평균 O(1)
- **중복 방지:** 증가 카운터 기반 고유 커밋 ID
- **브랜치 전환:** `current_branch` 변경, 기존 커밋 관계 유지

### 5.2. 커밋 그래프 — DAG

**DAG(Directed Acyclic Graph)**는 방향은 있지만 순환은 없는 그래프입니다.

Git의 커밋은 이전 커밋을 부모로 참조하며, 이러한 부모 관계가 모여 DAG를 형성합니다.

**커밋 그래프 예시**

```text
             A (최초 커밋)
            / \
           B   C
           |   |
           D   E
```

*부모 → 자식 방향으로 표현한 이력 구조*

실제 커밋 데이터에는 자식에서 부모로 향하는 참조를 저장합니다.

- **방향성:** 각 커밋이 부모 커밋을 참조
- **비순환성:** 새 커밋은 이미 존재하는 커밋만 부모로 연결
- **불변 관계:** 기존 커밋의 부모 정보 유지

사이클이 생기면 커밋이 자신의 조상이 되는 모순이 발생하고, 부모 우선 위상 정렬도 불가능해집니다.

### 5.3. 커밋 로그 — Topological Sort

**위상 정렬(Topological Sort)**은 방향성 비순환 그래프에서 선행 관계를 지키면서 노드를 나열하는 알고리즘입니다.

Mini Git의 기본 `LOG`는 최신순이 아니라 **부모 커밋이 자식 커밋보다 먼저 출력되는 순서**를 사용합니다.

**Kahn 알고리즘의 처리 과정**

```text
부모가 없는 커밋을 큐에 추가
             ↓
         커밋 출력
             ↓
    자식의 미처리 부모 수 감소
             ↓
  부모가 모두 처리된 자식을 큐에 추가
             ↓
         반복 실행
```

예를 들어 A가 B와 C의 부모라면 `A → B → C`, `A → C → B` 모두 유효한 출력 순서입니다.

- **적용 명령:** `LOG`
- **탐색 범위:** 전체 저장소의 커밋
- **시간복잡도:** O(V + E) — Kahn 알고리즘 자체 기준

V는 커밋 수, E는 부모·자식 연결 수입니다. 실제 구현은 출력 순서를 일정하게 유지하기 위해 hash를 먼저 정렬하므로, 정렬을 포함한 시간복잡도는 O(V log V + E)입니다. 화면 출력 비용은 별도입니다.

### 5.4. 그래프 탐색 — BFS

**BFS(Breadth-First Search)**는 시작 노드에서 가까운 노드부터 차례로 탐색하는 너비 우선 탐색 알고리즘입니다.

큐를 사용하며, 가중치가 없는 그래프에서 최단 거리를 구하는 데 적합합니다.

#### PATH — 두 커밋 사이의 최단 경로

```text
          A
         / \
        B   C
        |   |
        D   E
```

예: `PATH D E`

```text
D → B → A → C → E
```

- **간선 방향:** 부모 ↔ 자식, 양방향 이동 허용
- **탐색 기준:** 이동 간선 수가 가장 적은 경로
- **경로 동률:** 전체 hash 경로의 사전순 최소 선택
- **연결되지 않은 경우:** `No path`

부모 방향만 허용하면 다른 브랜치의 커밋으로 이동할 수 없는 경우가 생기므로, 과제에서 정의한 PATH는 부모·자식 관계를 무방향으로 처리합니다.

#### ANCESTORS — 모든 조상 탐색

```text
A ← B ← C ← D
```

`ANCESTORS D` → `C, B, A`

- **간선 방향:** 자식 → 부모
- **탐색 범위:** 도달 가능한 모든 조상
- **중복 방지:** visited 집합
- **출력 순서:** 가까운 조상부터, 같은 거리는 hash 오름차순

**BFS 자체의 시간복잡도:** O(V + E)

각 노드를 한 번씩 방문하고 연결된 간선을 확인하기 때문입니다. 실제 기능에서는 BFS 외의 처리 비용도 구분해야 합니다.

| 기능 | 추가 처리 | 전체 시간복잡도 — 화면 출력 제외 |
|---|---|---|
| `PATH` | 무방향 인접 목록 구성, 거리 정보를 따라 경로 복원 | O(V + E) |
| `ANCESTORS` | 탐색한 조상을 거리·hash 기준으로 병합 정렬 | O(V + E + A log A) — 최악 기준 |

V와 E는 전체 저장소의 커밋 수와 연결 수, A는 시작 커밋을 제외한 조상 수입니다. `ANCESTORS`의 BFS는 실제로 시작 커밋에서 부모 방향으로 도달 가능한 부분만 탐색합니다.

### 5.5. 커밋 정렬 — Merge Sort

**Merge Sort(병합 정렬)**는 데이터를 절반씩 나누어 정렬한 뒤 다시 합치는 분할 정복 알고리즘입니다.

Python의 `sorted()`나 `list.sort()` 대신 직접 구현했습니다.

**정렬 과정**

```text
       [8, 3, 5, 1]
          분할
        /       \
     [8, 3]    [5, 1]
      /  \      /  \
    [8]  [3]  [5]  [1]
      \  /      \  /
     [3, 8]    [1, 5]
        \       /
          병합
     [1, 3, 5, 8]
```

**정렬 기준**

| 명령어 | 정렬 기준 | 동률 처리 |
|---|---|---|
| `LOG --sort-by=date` | 생성 시각 오름차순 | hash 오름차순 |
| `LOG --sort-by=author` | 작성자 이름 오름차순 | hash 오름차순 |

**알고리즘 특성**

| 구분 | 특성 |
|---|---|
| 평균 시간복잡도 | O(N log N) |
| 최악 시간복잡도 | O(N log N) |
| 보조 공간복잡도 | O(N) |
| 안정 정렬 | 지원 |

**안정 정렬(Stable Sort)**은 비교 기준이 같은 데이터의 기존 상대적 순서를 유지하는 정렬입니다. 병합 과정에서 비교 키가 같을 때 왼쪽 원소를 먼저 선택하여 안정성을 보장합니다.

### 5.6. 커밋 검색 — Inverted Index

**역색인(Inverted Index)**은 검색어를 기준으로 해당 데이터의 위치를 미리 저장하는 구조입니다.

전체 커밋을 하나씩 검사하는 대신, 검색어와 연결된 커밋 목록에 바로 접근할 수 있습니다.

**일반 저장 구조**

```text
000001 → "Add login"
000002 → "Fix login"
000003 → "Add search"
```

**역색인 구조**

`MiniGit`의 `self.index`가 가진 두 딕셔너리입니다. 아래는 자료구조를 설명하기 위한 여러 작성자의 예시이며, 현재 CLI는 `INIT`에서 지정한 한 작성자로 커밋을 생성합니다. 다시 `INIT`하면 기존 커밋과 색인이 초기화됩니다.

```text
self.index.keywords
├── add    → [000001, 000003]
├── login  → [000001, 000002]
├── fix    → [000002]
└── search → [000003]

self.index.authors
├── peachily → [000001, 000002]
└── Alice    → [000003]
```

**색인 갱신 과정**

```text
COMMIT "Add login"
        ↓
소문자 변환: lower()
        ↓
메시지 분리: split()
        ↓
중복 키워드 제거
        ↓
keyword / author 인덱스 갱신
        ↓
SEARCH에서 해당 커밋만 조회
```

키워드는 `set(commit.message.lower().split())`으로 처리합니다. 공백 기준으로 나누므로 `hello`와 `hello,`는 서로 다른 키워드입니다. 작성자 이름은 소문자로 변환하지 않고 그대로 색인하므로 작성자 검색은 대소문자를 구분합니다.

**검색 방식 비교**

| 구분 | 전체 순회 검색 | 역색인 검색 |
|---|---|---|
| 탐색 대상 | 전체 커밋 | 검색어에 연결된 커밋 |
| 조회 방식 | 커밋마다 비교 | 딕셔너리에서 직접 조회 |
| 시간복잡도 | O(V) | 평균 O(1 + K) |

- **V:** 전체 커밋 수
- **K:** 검색 결과 수
- **검색 결과:** 커밋 생성 순서 유지
- **별도 비용:** 문자열 정규화 및 결과 출력
