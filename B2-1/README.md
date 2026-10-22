# 복숭아창고 (Peach Pantry)

**수입과 지출을 차곡차곡 기록하는 콘솔 가계부**

Python 표준 라이브러리만 사용하여 거래·카테고리·월별 예산을 JSONL 파일에 저장합니다.
코디세이 B2-1 과제이며, 명령어는 영어, 사용자 안내와 카테고리 이름은 한국어를 사용합니다.

## 1. 프로젝트 구조

```text
B2-1/
├── peach_pantry/
│   ├── __init__.py       # Python 패키지 선언
│   ├── __main__.py       # python -m peach_pantry 진입점
│   ├── cli.py            # 명령 실행과 서비스·출력 연결
│   ├── parser.py         # argparse 명령·옵션·도움말 등록
│   ├── prompts.py        # add/update 대화형 입력과 재입력
│   ├── service.py        # 거래·카테고리·예산·요약의 업무 규칙
│   ├── repository.py     # 모델 저장·복원, 초기화, 거래 ID 관리
│   ├── models.py         # Transaction/Category/Budget/MonthlySummary dataclass
│   ├── validators.py     # 사용자 입력 검증과 해결 힌트
│   ├── formatter.py      # 한국어 화면, 카테고리 이모지, 금액 출력
│   ├── errors.py         # 공통 예외와 오류 처리 데코레이터
│   ├── file_io.py        # JSONL·CSV 공통 임시 파일 및 원자적 교체
│   ├── jsonl.py          # yield 기반 JSONL 읽기·쓰기
│   ├── csv_io.py         # CSV 스키마 검증·읽기·쓰기
│   └── sorting.py        # 임시 SQLite 파일을 이용한 검색 정렬
├── tests/               # 단위·파일 안전성·CLI 통합 테스트
├── docs/
│   └── REQUIREMENTS.md   # 필수 요구사항별 구현·검증 점검표
├── .gitignore
└── README.md
```

`peach_pantry`는 `python -m peach_pantry` 실행에 사용하는 패키지입니다.
CLI는 입력·출력을 연결하고, 서비스는 업무 규칙을 적용하며, 저장소는 파일과 ID를 관리합니다.
안전 저장 코드는 `file_io.py`에서 한 번만 구현하여 JSONL과 CSV가 공유합니다.
주요 클래스와 함수에는 타입 힌트와 역할을 설명하는 docstring이 있습니다.

## 2. 실행 방법

Python **3.10 이상**과 UTF-8 터미널이 필요합니다. 외부 패키지 설치나 API 키는 필요하지 않습니다.
저장소 최상위 폴더에서 다음 명령을 실행합니다.

```bash
cd B2-1
python3 -m peach_pantry --help
python3 -m peach_pantry add
python3 -m peach_pantry list
```

아래 예시는 모두 `B2-1`에서 실행합니다. `python`이 Python 3.10 이상을 가리키는 환경에서는
`python3` 대신 `python`을 사용해도 됩니다.

이 프로그램은 메뉴를 계속 띄워 두는 방식이 아니라 **명령 하나를 실행한 뒤 종료하는 방식**입니다.
거래 추가·수정 명령에서는 필요한 값을 차례대로 입력합니다.

**저장 위치를 따로 지정하여 실행하기**

```bash
python3 -m peach_pantry --data-dir ./practice-data add
python3 -m peach_pantry list --data-dir ./practice-data
```

`--data-dir`는 명령 앞뒤와 하위 명령 뒤에서 사용할 수 있습니다.
다른 폴더를 지정하면 이후 명령에도 같은 경로를 지정해야 같은 데이터를 조회합니다.

## 3. 주요 명령어

| 명령어 | 기능 | 주요 옵션·인자 |
| --- | --- | --- |
| `add` | 대화형 거래 추가, 저장된 ID 출력 | 날짜·타입·카테고리·금액·메모·태그 입력 |
| `list` | 최신 거래 조회 | `--limit N`, 기본 10건 |
| `search` | 여러 조건을 모두 만족하는 거래 검색 | `--from`, `--to`, `--category`, `--type`, `--q`, `--tag` |
| `update` | 대화형 거래 수정 | `--id TX-000001`, Enter로 기존 값 유지 |
| `delete` | 거래 삭제 | `--id TX-000001` |
| `category add` | 카테고리 등록 | 한글 이름, 예: `여행` |
| `category list` | 카테고리 조회 | 기본·사용자 등록 카테고리 |
| `category remove` | 카테고리 삭제 | 한글 이름, 사용 중이면 삭제 차단 |
| `budget set` | 월별 예산 설정·재설정 | `--month YYYY-MM --amount 금액` |
| `summary` | 월별 수입·지출·잔액과 예산 요약 | `--month YYYY-MM`, `--top N` 기본 3 |
| `import` | UTF-8 CSV에서 거래 가져오기 | `--from 입력.csv` |
| `export` | 기간에 해당하는 거래를 UTF-8 CSV로 내보내기 | `--out 출력.csv`와 날짜 조건 필수 |

모든 명령과 하위 명령에서 `--help`를 사용할 수 있습니다.

```bash
python3 -m peach_pantry search --help
python3 -m peach_pantry category add --help
python3 -m peach_pantry budget set --help
```

## 4. 거래 입력·조회 예시

```bash
python3 -m peach_pantry add
```

날짜에 `2026-10-22`, 타입에 `expense`, 카테고리에 `식비`, 금액에 `12000`,
메모에 `점심`, 태그에 `회사,점심`을 차례대로 입력하면 `TX-000001` 같은 거래 ID를 출력합니다.

| 입력 | 규칙 |
| --- | --- |
| 날짜 | 실제 존재하는 `YYYY-MM-DD` 날짜 |
| 타입 | `income` 또는 `expense` |
| 카테고리 | 등록된 이름을 이모지 없이 입력 |
| 금액 | 0보다 큰 정수, 쉼표·소수점·부호 없이 입력 |
| 메모 | 선택 입력, 빈 값 허용 |
| 태그 | 선택 입력, 쉼표 구분, 앞뒤 공백과 빈 항목 제거 |

잘못 입력한 필드는 원인과 힌트를 안내한 뒤 다시 입력받습니다.
Ctrl+C 또는 입력 종료 시 거래를 부분 저장하지 않습니다.

```bash
python3 -m peach_pantry list --limit 5
python3 -m peach_pantry search --from 2026-10-01 --to 2026-10-31 --category 식비 --type expense --q 점심 --tag 회사
python3 -m peach_pantry update --id TX-000001
python3 -m peach_pantry delete --id TX-000001
```

- 목록·검색은 **날짜 내림차순 → 같은 날짜는 거래 ID 일련번호 내림차순**입니다.
- 검색 날짜의 양 끝은 포함하며, 여러 조건은 AND로 적용합니다.
- `--q`는 메모의 부분 일치, `--tag`는 태그 하나의 정확한 일치입니다. 대소문자는 구분합니다.
- 수정 시 각 필드에서 Enter를 누르면 기존 값을 유지합니다.
- 목록의 수입은 `+`, 지출은 `-`로 표시합니다. 이모지를 고정 너비 열에 맞추지 않고 필드를 구분합니다.

## 5. 카테고리와 월별 예산

```bash
python3 -m peach_pantry category list
python3 -m peach_pantry category add 여행
python3 -m peach_pantry category remove 여행
python3 -m peach_pantry budget set --month 2026-10 --amount 300000
python3 -m peach_pantry summary --month 2026-10 --top 3
```

**기본 카테고리**

🍚 식비 · ☕ 카페 · 🚌 교통 · 🛍️ 쇼핑 · 🧺 생활 · 🏠 주거 ·
💊 건강 · 🎬 문화 · 📚 교육 · 💰 급여 · 🎁 용돈 · 📦 기타

카테고리 파일이 없을 때만 기본값을 생성하며, 사용자가 모두 삭제한 빈 파일은 복원하지 않습니다.
새 카테고리는 한글 이름과 단어 사이 공백을 사용할 수 있고, 출력 시 기본으로 📦를 붙입니다.
이모지는 파일에 저장하지 않습니다. 중복 이름과 사용 중인 카테고리 삭제는 오류로 처리합니다.

같은 월의 예산을 다시 설정하면 금액을 교체하고 다른 월의 예산은 유지합니다.
`summary`는 총수입·총지출·잔액과 카테고리별 지출 순위를 표시합니다.
순위는 지출 합계 내림차순이며, 동률은 카테고리 이름 오름차순입니다.

예산이 있는 달에는 **총지출 ÷ 월 예산 × 100** 사용률을 소수점 한 자리로 표시합니다.
실제 지출이 예산보다 클 때만 초과 금액과 경고를 출력합니다.
거래가 없는 달에도 안내와 0원 합계를 표시하며, 설정된 예산이 있으면 사용률은 `0.0%`입니다.
예산 초과 경고는 정상 조회이므로 종료 코드는 0입니다.

## 6. CSV 가져오기·내보내기

**고정 스키마**

```csv
date,type,category,amount,memo,tags
2026-10-22,expense,식비,12000,"점심, 복숭아","회사,점심"
2026-10-25,income,급여,3000000,월급,회사
```

| 컬럼 | 값 필수 여부 | 형식 |
| --- | --- | --- |
| `date` | 필수 | `YYYY-MM-DD` |
| `type` | 필수 | `income` / `expense` |
| `category` | 필수 | 등록된 카테고리 이름 |
| `amount` | 필수 | 양수 정수 |
| `memo` | 선택 | 문자열, 빈 값 허용 |
| `tags` | 선택 | 쉼표로 구분한 태그, 빈 값 허용 |

값이 선택인 컬럼도 **헤더와 각 행의 6개 컬럼은 생략할 수 없습니다.** 헤더 순서도 고정입니다.
표준 `csv` 모듈로 쉼표·따옴표·줄바꿈을 처리합니다. 입력은 UTF-8과 UTF-8 BOM을 지원하고,
출력은 BOM 없는 UTF-8입니다.

```bash
python3 -m peach_pantry import --from ./input.csv
python3 -m peach_pantry export --out ./october.csv --month 2026-10
python3 -m peach_pantry export --out ./period.csv --from 2026-10-01 --to 2026-10-22
```

- 가져오기는 모든 행을 검증한 뒤 새 ID를 발급하여 한 번에 저장합니다. 오류가 하나라도 있으면 전체 취소하며 기존 거래와 ID 카운터를 유지합니다.
- 헤더만 있는 CSV는 0건 가져오기입니다. 정상 가져오기와 내보내기는 처리 건수를 출력합니다.
- 내보내기는 `--month` 또는 `--from`/`--to`가 필수이며 두 방식은 함께 사용할 수 없습니다.
- `--from` 또는 `--to` 하나만 지정한 열린 범위도 허용합니다. 날짜 경계는 포함합니다.
- 내보내기는 JSONL 파일 순서를 유지합니다. 조건에 맞는 거래가 없으면 헤더만 출력합니다.
- 기존 출력 CSV는 정상 완료 시 교체합니다. 저장 실패나 원본 손상 시 기존 출력 파일을 보존하고 임시 파일을 정리합니다.
- JSONL 저장소 자체 또는 그 별칭 경로로 내보내는 것은 차단합니다.

## 7. 저장 형식과 처리 방식

기본 위치는 **실행 당시 작업 폴더의 `./data`**입니다. `B2-1`에서 실행하면 `B2-1/data`에 저장합니다.
폴더와 없는 파일은 자동으로 생성합니다. 기본 `data/`와 Python 캐시는 Git에서 제외합니다.
사용자가 지정한 다른 데이터 폴더는 자동으로 Git 제외 대상이 되지 않습니다.

| 영구 파일 | 저장 내용 |
| --- | --- |
| `transactions.jsonl` | 첫 줄에 ID 메타데이터, 이후 한 줄당 거래 한 건 |
| `categories.jsonl` | 한 줄당 `{"name":"식비"}` 같은 카테고리 객체 |
| `budgets.jsonl` | 한 줄당 `{"month":"2026-10","amount":300000}` 같은 예산 객체 |

거래 파일 예시:

```jsonl
{"record_type":"metadata","last_id":1}
{"id":"TX-000001","date":"2026-10-22","type":"expense","category":"식비","amount":12000,"memo":"점심","tags":["회사","점심"]}
```

ID는 `TX-000001` 형식의 증가 번호입니다. 거래를 모두 삭제해도 마지막 발급 번호를 유지하므로
삭제한 ID를 다시 발급하지 않습니다. 999999를 넘으면 자릿수가 늘어납니다.
거래와 ID 메타데이터는 같은 파일에서 함께 교체하므로 별도 영구 카운터 파일은 없습니다.

**스트리밍과 메모리 사용**

| 처리 | 방식 |
| --- | --- |
| JSONL 읽기 | `yield`로 한 줄씩 읽고 모델로 변환 |
| `list --limit N` | 전체 거래를 순회하며 제한 크기 힙에 최신 N건 유지 |
| `search` | 조건에 맞는 거래를 임시 SQLite 파일에 저장·정렬, 결과 크기에 비례하는 추가 디스크 사용 |
| `summary` | 거래는 한 건씩 읽고 카테고리별 합계만 메모리에 유지 |
| `import` | 가져올 CSV의 검증 결과는 메모리에 보관, 기존 거래 JSONL은 순차 복사 |
| `export` | 조건에 맞는 거래를 한 건씩 CSV에 기록 |

SQLite는 표준 라이브러리 `sqlite3`로 사용하는 **검색용 임시 저장소**이며 영구 데이터는 JSONL입니다.
임시 검색 폴더는 조회 완료·중단·오류 시 정리합니다.
쓰기 작업은 대상과 같은 폴더에 임시 파일을 만들고, `flush`·`fsync` 후 `os.replace()`로 교체합니다.
동시에 여러 프로세스에서 쓰는 기능은 지원하지 않으므로 한 명령이 끝난 뒤 다음 명령을 실행합니다.

## 8. 오류 처리와 종료 코드

```text
[오류] 날짜 형식이나 값이 올바르지 않습니다.
[힌트] 실제로 존재하는 날짜를 YYYY-MM-DD 형식으로 입력해 주세요.
```

`main`에 적용한 `@handle_errors`가 예상 가능한 오류를 스택트레이스 대신 원인과 힌트로 바꿉니다.
입력값·없는 ID·잘못된 파일·저장 실패·UTF-8 오류·입력 중단을 처리합니다.

| 코드 | 의미 |
| --- | --- |
| `0` | 명령 정상 완료, 도움말, 빈 조회, 예산 초과 경고를 포함한 정상 요약 |
| `1` | 입력값·ID·파일·저장 등 실행 오류, 입력 종료 |
| `2` | 명령·옵션 사용법 오류, 잘못된 조회·순위 건수 |
| `130` | Ctrl+C로 실행 중단 |

## 9. 테스트와 요구사항 점검

```bash
# B2-1에서 전체 테스트
python3 -m unittest discover -s tests -v

# 별도 프로세스의 CLI 통합 테스트만 실행
python3 -m unittest tests.test_integration -v
```

Commit 08 검증 환경은 Python **3.14.0**이며 **전체 109개 테스트가 통과**했습니다.
이 중 3개는 모킹 없이 별도 Python 프로세스에서 실행하는 통합 테스트입니다.
모든 테스트는 임시 폴더를 사용하며 실제 사용자 `data/`를 초기화하지 않습니다.
실패를 주입하는 파일 안전성 테스트는 `unittest.mock`을 사용합니다.

| 테스트 파일 | 검증 내용 |
| --- | --- |
| `test_cli.py` | 전체 15개 도움말, 옵션 해석, 오류 형식과 종료 코드 |
| `test_repository.py` | JSONL·모델, 초기화, 제너레이터, ID 보존, 원자적 교체 |
| `test_transactions.py` | add/list, 재입력·입력 중단, 최신순과 메모리 사용 |
| `test_search_update_delete.py` | AND 검색, 수정·삭제, 없는 ID, 원본과 임시 파일 보호 |
| `test_category_budget.py` | 중복·사용 중 삭제 차단, 초기값 복원 방지, 예산 영속성 |
| `test_summary.py` | 월 경계, 합계·TOP N, 예산 사용률과 초과 경계값 |
| `test_csv.py` | 스키마, UTF-8·태그 왕복, 날짜 조건, 전체 취소·출력 보호 |
| `test_integration.py` | 전체 명령 연계, 프로세스 간 영속성, 실제 오류·종료 코드 |

세부 필수 요구사항별 구현·검증 결과는 [요구사항 점검표](docs/REQUIREMENTS.md)에 정리했습니다.
