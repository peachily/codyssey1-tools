"""명령·옵션 등록과 argparse 도움말을 담당한다."""

import argparse
from pathlib import Path
from typing import Any

from .errors import PantryError
from .formatter import format_title


class PantryArgumentParser(argparse.ArgumentParser):
    """잘못된 CLI 입력을 공통 오류 형식으로 전달한다."""

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        kwargs.setdefault("add_help", False)
        kwargs.setdefault("allow_abbrev", False)
        super().__init__(*args, **kwargs)
        self._positionals.title = "명령 및 인자"
        self._optionals.title = "옵션"
        self.add_argument("-h", "--help", action="help", help="도움말을 표시하고 종료합니다")

    def error(self, message: str) -> None:
        """사용법 오류를 한국어 원인·힌트와 종료 코드 2로 전달한다."""
        # argparse의 내부 영문 진단은 사용자에게 필요한 원인으로 바꾼다.
        if message.startswith("the following arguments are required: "):
            reason = "필수 명령이나 옵션이 누락되었습니다: " + message.split(": ", 1)[1]
        elif message.startswith("unrecognized arguments: "):
            reason = "알 수 없는 옵션이나 인자입니다: " + message.split(": ", 1)[1]
        elif "invalid int value:" in message:
            reason = "정수 값이 필요한 옵션입니다: " + message.split(":", 1)[0].removeprefix("argument ")
        elif "invalid choice:" in message:
            reason = "허용되지 않는 명령이나 옵션 값입니다: " + message.split("invalid choice:", 1)[1].split(" (choose from", 1)[0].strip()
        elif "expected one argument" in message:
            reason = "옵션에 값이 필요합니다: " + message.split(":", 1)[0].removeprefix("argument ")
        else:
            reason = "명령어나 옵션이 올바르지 않습니다."
        raise PantryError(
            reason,
            f"'{self.prog} --help'로 사용법과 필수 옵션을 확인해 주세요.",
            exit_code=2,
        )

    def format_help(self) -> str:
        """도움말의 사용법 표제를 한국어로 표시한다."""
        return super().format_help().replace("usage: ", "사용법: ", 1)


def add_data_dir(parser: argparse.ArgumentParser) -> None:
    """명령의 어느 단계에서도 데이터 폴더를 지정할 수 있게 한다."""
    parser.add_argument(
        "--data-dir", type=Path, default=argparse.SUPPRESS, metavar="경로",
        help="데이터 폴더 (기본값: ./data)",
    )


def build_parser() -> argparse.ArgumentParser:
    """필수 명령과 옵션을 등록한다. 데이터 파일은 생성하지 않는다."""
    parser = PantryArgumentParser(
        prog="python -m peach_pantry",
        description=format_title("수입과 지출을 기록하는 작은 창고"),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    add_data_dir(parser)
    parser.set_defaults(data_dir=Path("./data"))
    commands = parser.add_subparsers(dest="command", required=True, title="명령")

    descriptions = {
        "add": "거래를 대화형으로 추가합니다",
        "list": "최근 거래를 조회합니다",
        "search": "조건을 만족하는 거래를 검색합니다",
        "update": "거래를 대화형으로 수정합니다",
        "delete": "거래를 삭제합니다",
        "category": "카테고리를 관리합니다",
        "budget": "월별 예산을 관리합니다",
        "summary": "월별 수입과 지출을 요약합니다",
        "import": "CSV에서 거래를 가져옵니다",
        "export": "기간에 해당하는 거래를 CSV로 내보냅니다",
    }
    parsers = {}
    for name, description in descriptions.items():
        command = commands.add_parser(name, help=description, description=description)
        add_data_dir(command)
        parsers[name] = command

    parsers["list"].add_argument("--limit", type=int, default=10, metavar="N", help="출력 건수 (기본값: 10)")
    search = parsers["search"]
    search.epilog = "메모는 부분 일치, 태그는 정확히 일치합니다. 여러 조건은 모두 만족해야 합니다. 정렬에 결과 크기에 비례하는 임시 디스크 공간을 사용합니다."
    add_date_range(search)
    search.add_argument("--category", metavar="카테고리", help="카테고리 조건")
    search.add_argument("--type", choices=("income", "expense"), help="거래 타입 조건")
    search.add_argument("--q", metavar="검색어", help="메모 검색어")
    search.add_argument("--tag", metavar="태그", help="태그 조건")
    for name in ("update", "delete"):
        parsers[name].add_argument("--id", required=True, dest="transaction_id", metavar="거래ID", help="대상 거래 ID")

    category = parsers["category"].add_subparsers(dest="category_command", required=True, title="하위 명령")
    for name, description in (("add", "카테고리를 등록합니다"), ("list", "카테고리를 조회합니다"), ("remove", "카테고리를 삭제합니다")):
        child = category.add_parser(name, help=description, description=description)
        add_data_dir(child)
        if name != "list":
            child.add_argument("name", metavar="카테고리", help="카테고리 이름")

    budget = parsers["budget"].add_subparsers(dest="budget_command", required=True, title="하위 명령")
    budget_set = budget.add_parser("set", help="월별 예산을 설정합니다", description="월별 예산을 설정합니다")
    add_data_dir(budget_set)
    budget_set.add_argument("--month", required=True, metavar="YYYY-MM", help="예산 대상 월")
    budget_set.add_argument("--amount", required=True, type=int, metavar="금액", help="예산 금액")

    summary = parsers["summary"]
    summary.add_argument("--month", required=True, metavar="YYYY-MM", help="요약 대상 월")
    summary.add_argument("--top", type=int, default=3, metavar="N", help="카테고리별 지출 순위 건수 (기본값: 3)")
    parsers["import"].add_argument("--from", dest="input_csv", required=True, type=Path, metavar="CSV", help="가져올 UTF-8 CSV 파일")
    parsers["import"].epilog = "헤더: date,type,category,amount,memo,tags. 모든 행을 검증한 뒤 저장하며 검증 결과는 CSV 크기에 비례하는 메모리를 사용합니다."
    export = parsers["export"]
    export.epilog = "날짜 조건은 필수입니다. --month와 --from/--to는 함께 사용할 수 없습니다. 날짜 경계는 포함하며 --from 또는 --to만 지정할 수도 있습니다."
    export.add_argument("--out", required=True, type=Path, metavar="CSV", help="내보낼 UTF-8 CSV 파일")
    export.add_argument("--month", metavar="YYYY-MM", help="내보낼 월 (--from/--to와 함께 사용할 수 없음)")
    add_date_range(export)
    return parser


def add_date_range(parser: argparse.ArgumentParser) -> None:
    """예약어와 충돌하지 않는 이름으로 날짜 범위 옵션을 등록한다."""
    parser.add_argument("--from", dest="date_from", metavar="YYYY-MM-DD", help="시작일 (포함)")
    parser.add_argument("--to", dest="date_to", metavar="YYYY-MM-DD", help="종료일 (포함)")
