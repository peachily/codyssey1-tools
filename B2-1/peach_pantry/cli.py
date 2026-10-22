"""argparse 기반 명령 등록과 실행 흐름."""

import argparse
from pathlib import Path
from typing import Sequence

from .errors import PantryError, handle_errors
from .formatter import format_title


class PantryArgumentParser(argparse.ArgumentParser):
    """잘못된 CLI 입력을 공통 오류 형식으로 전달한다."""

    def __init__(self, *args, **kwargs) -> None:
        kwargs.setdefault("add_help", False)
        kwargs.setdefault("allow_abbrev", False)
        super().__init__(*args, **kwargs)
        self._positionals.title = "명령 및 인자"
        self._optionals.title = "옵션"
        self.add_argument("-h", "--help", action="help", help="도움말을 표시하고 종료합니다")

    def error(self, message: str) -> None:
        raise PantryError(
            f"명령어나 옵션이 올바르지 않습니다. ({message})",
            f"'{self.prog} --help'로 사용법과 필수 옵션을 확인해 주세요.",
            exit_code=2,
        )


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
    export = parsers["export"]
    export.add_argument("--out", required=True, type=Path, metavar="CSV", help="내보낼 UTF-8 CSV 파일")
    export.add_argument("--month", metavar="YYYY-MM", help="내보낼 월 (--from/--to와 함께 사용할 수 없음)")
    add_date_range(export)
    return parser


def add_date_range(parser: argparse.ArgumentParser) -> None:
    """예약어와 충돌하지 않는 이름으로 날짜 범위 옵션을 등록한다."""
    parser.add_argument("--from", dest="date_from", metavar="YYYY-MM-DD", help="시작일 (포함)")
    parser.add_argument("--to", dest="date_to", metavar="YYYY-MM-DD", help="종료일 (포함)")


def dispatch(args: argparse.Namespace) -> int:
    """후속 단계에서 연결할 명령에 현재 구현 상태를 안내한다."""
    raise PantryError(
        f"'{args.command}' 기능은 아직 구현되지 않았습니다.",
        "현재는 CLI 구성 단계입니다. '--help'로 명령과 옵션을 확인해 주세요.",
    )


@handle_errors
def main(argv: Sequence[str] | None = None) -> int:
    """CLI 인자를 해석하고 명령 실행 결과를 종료 코드로 반환한다."""
    args = build_parser().parse_args(argv)
    return dispatch(args)
