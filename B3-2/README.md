# Giteuk

Git 변경사항을 분석해 커밋 메시지와 Pull Request 초안을 생성하는 Python CLI입니다.

## 주요 기능

- 스테이징 전후 변경사항과 신규 파일 수집
- Codyssey AI API를 이용한 커밋 메시지·PR 초안 생성
- 제목 길이, 본문, PR 필수 섹션 검증
- 민감정보 마스킹과 비밀 파일 제외

결과는 터미널에 출력하며, 커밋·push·PR 등록은 직접 진행합니다.

## 프로젝트 구조

```text
B3-2/
├── main.py           # CLI와 실행 흐름
├── config.py         # API 설정과 기본값
├── git_utils.py      # Git 변경사항 수집
├── ai_client.py      # API 요청과 오류 처리
├── prompts.py        # 작성 규칙
├── validators.py     # 출력 형식 검증
├── safe_mode.py      # 민감정보 보호
├── requirements.txt
├── .gitignore
├── README.md
└── tests/            # 단위 테스트
```

## 설치

Python 3.10 이상과 Git이 필요합니다. 저장소 최상위 폴더에서 실행합니다.

```bash
python3 -m venv B3-2/.venv
source B3-2/.venv/bin/activate
python -m pip install -r B3-2/requirements.txt
```

Windows PowerShell에서는 가상환경을 `B3-2\.venv\Scripts\Activate.ps1`로 활성화합니다.

## 환경변수 설정

Codyssey에서 발급받은 API Key를 등록합니다.

```bash
# macOS / Linux
export AI_API_KEY="발급받은_API_키"
```

```powershell
# Windows PowerShell
$env:AI_API_KEY="발급받은_API_키"
```

키는 환경변수로만 읽으며, `.env` 파일은 자동으로 불러오지 않습니다.

## CLI 명령 및 옵션

Git 저장소 최상위 폴더에서 실행합니다. **저장소 전체의 미커밋 변경사항**을 분석합니다.

```bash
python B3-2/main.py commit
python B3-2/main.py pr
python B3-2/main.py commit --max-tokens 1000
python B3-2/main.py --help
```

| 옵션 | 기본값 | 설명 |
| --- | --- | --- |
| `--model` | `gpt-5-mini` | AI 모델 |
| `--temperature` | `0.2` | 0~2 사이 숫자. `gpt-5` 계열 등 추론 모델에는 전송하지 않음 |
| `--max-tokens` | `8192` | 1~128000 사이 정수. 실제 한도는 모델에 따라 다름 |
| `--safe-mode` | 활성화 | 민감정보 마스킹 및 비밀 파일 제외 |
| `--no-safe-mode` | — | 안전 모드 비활성화 |

## 출력 예시

### 커밋 메시지

```text
feat: 사용자 이름 입력 처리 추가

- main.py에서 사용자 이름을 입력받도록 추가해요.
```

### PR 초안

Git 변경사항을 바탕으로 제목과 아래 세 항목을 작성합니다.

| 항목 | 작성 내용 |
| --- | --- |
| 제목 | 핵심 변경사항을 한 줄로 요약 |
| `Why` | 변경 배경이나 목적. 이유를 알 수 없으면 확인이 필요하다고 표시 |
| `What` | 변경한 기능, 파일과 주요 수정 내용 |
| `How to Test` | 사용자가 직접 실행할 수 있는 확인 절차. 실제 테스트 결과는 포함하지 않음 |

생성 후 변경 이유를 보완하고, 제안된 테스트를 실행한 결과를 직접 추가하세요.

```markdown
사용자 이름 입력 처리 추가

## Why
- 변경 이유는 제공된 변경사항만으로 확인할 수 없어요.

## What
- main.py에서 사용자 이름을 입력받도록 추가해요.

## How to Test
- 프로그램을 실행하고 이름을 입력한 뒤 입력값이 처리되는지 확인하세요.
```

## 안전 모드 및 주의사항

- 안전 모드는 API Key·이메일·비밀번호·토큰을 마스킹하고, `.env`·비밀키 파일 등을 제외합니다. 원본 파일은 수정하지 않습니다.
- 모든 민감정보를 탐지하지는 못합니다. 실행 전 diff와 신규 파일을 검토하고, 생성 결과도 사용 전에 확인하세요.
- 변경 내용은 Codyssey API로 전송됩니다. 명령당 최대 1회 호출하며 비용이 발생할 수 있습니다. 자동 재시도는 없습니다.
- 변경사항이 없거나 API Key가 누락되면 API를 호출하지 않습니다.

## 테스트

```bash
cd B3-2
python -m unittest discover -s tests -v
```

API 요청은 Mock으로 대체합니다. 실제 Codyssey 인증과 모델 호환성은 별도 확인이 필요합니다.
