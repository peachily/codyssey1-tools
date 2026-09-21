# Contributing Guide

이 저장소는 팀 소개 결과물을 만들며 GitHub Flow로 협업합니다. `main`은 항상 확인 가능한 상태로 유지하고, 모든 변경은 이슈와 PR을 통해 병합합니다. 작은 작업 단위로 나누면 리뷰와 충돌 해결 기록을 남기기 쉽습니다.

## 브랜치 전략과 이름

- `main`: 보호 브랜치입니다. 직접 push하지 않으며 PR 승인 1명 이상 후에만 병합합니다.
- `feature/*`: 이슈별 작업 브랜치입니다. `main`에서 만들고 `main`으로 PR을 엽니다.
- 형식: `feature/<issue-number>-<member>-<topic>`
- 예: `feature/12-minji-profile`, `feature/13-jun-contributing`

```bash
git switch main
git pull origin main
git switch -c feature/12-minji-profile
```

## 커밋 메시지

형식은 `<type>: <변경 대상과 결과>`입니다. 필요하면 본문 마지막에 `Refs: #이슈번호`를 넣습니다.

- `feat`: 사용자에게 보이는 결과물 추가
- `docs`: README·협업 문서 변경
- `fix`: 오류 또는 문서 오류 수정
- `refactor`: 동작을 바꾸지 않는 구조 개선
- `chore`: 설정·관리 작업

좋은 예: `docs: add minji team profile`, `feat: link member profiles from readme`

금지: `update`, `fix`, `temp`, `wip`, `final`, `edit file`처럼 무엇을 바꿨는지 알 수 없는 메시지

## 이슈와 PR 규칙

1. 작업 전에 Issue를 만들고 담당자와 완료 조건을 적습니다.
2. feature 브랜치에서 작업하고 의미 있는 단위로 커밋합니다.
3. PR 본문에 `Closes #<issue-number>`를 포함합니다.
4. PR에는 What(변경 사항), Why(변경 이유), How(검증 방법)를 모두 작성합니다.
5. 리뷰 승인 1명과 실질 리뷰 코멘트 1개 이상을 받은 뒤 병합합니다. 작성자는 코멘트에 답글을 남기거나 후속 커밋으로 반영합니다.

PR 예시:

```md
## 연결 이슈
Closes #12

## What
- `team/minji.md`에 팀원 소개를 추가했습니다.

## Why
- 팀 소개 결과물의 구성원을 README에서 확인할 수 있게 합니다.

## How
- Markdown 링크와 렌더링을 확인했습니다.
```

## 코드 리뷰 규칙

- `LGTM`만 남기지 않습니다. 파일 또는 줄을 근거로 질문, 대안, 누락된 검증 중 하나를 남깁니다.
- 예: “`team/minji.md`의 역할 설명이 README의 역할과 다릅니다. 한 표현으로 맞추면 어떨까요?”
- 작성자는 반영 여부와 이유를 답글로 남기고, 수정했다면 커밋 또는 변경 내용을 연결합니다.
- 본인 PR은 리뷰하지 않습니다. 각 팀원은 다른 팀원의 PR에 최소 2회 리뷰합니다.

## 충돌 대응 흐름

1. 충돌을 발견하면 팀 채널에 파일·브랜치·작업 내용을 공유합니다.
2. `main` 최신 내용을 반영한 뒤 충돌 마커(`<<<<<<<`, `=======`, `>>>>>>>`)를 확인합니다.
3. 한쪽을 단순 선택하지 말고 의도를 확인해 최종 내용을 정합니다.
4. 해결 후 로컬에서 확인하고 커밋·PR에 남깁니다.
5. 재현 절차, 명령, 결과, 배운 점을 `docs/conflict-resolution.md`에 기록합니다.

## 병합 방식과 보호 설정

- GitHub Settings에서 `main`에 “Require a pull request before merging”과 “Require approvals: 1”을 설정합니다.
- 승인 없이 직접 push하거나, 공유 브랜치의 강제 push·합의 없는 rebase는 금지합니다.
- 병합 후 feature 브랜치는 삭제해 작업 범위를 명확히 합니다.
