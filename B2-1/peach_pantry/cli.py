"""argparse 기반 명령 등록과 실행 흐름."""

import argparse
from contextlib import closing
from pathlib import Path
from typing import Callable, Sequence, TypeVar

from .errors import PantryError, handle_errors
from .formatter import format_category, format_title, print_error, print_transactions
from .repository import PantryRepository
from .service import PantryService
from .validators import parse_amount, parse_date, parse_tags, parse_type

T = TypeVar("T")


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
    """구현된 명령을 서비스에 연결한다."""
    if args.command in ("add", "list", "search", "update", "delete"):
        if args.command == "list" and args.limit <= 0:
            raise PantryError("조회 건수가 올바르지 않습니다.",
                              "--limit에 0보다 큰 정수를 지정해 주세요.", exit_code=2)
        repository = PantryRepository(args.data_dir)
        repository.initialize()
        service = PantryService(repository)
        if args.command == "add":
            add_interactive(service)
        elif args.command == "list":
            print_transactions(service.list_transactions(args.limit))
        elif args.command == "search":
            with closing(service.search_transactions(
                date_from=args.date_from, date_to=args.date_to,
                category=args.category, type=args.type, q=args.q, tag=args.tag,
            )) as transactions:
                print_transactions(transactions, title="검색 결과",
                                   empty_message="검색 조건에 맞는 거래가 없습니다.")
        elif args.command == "update":
            update_interactive(service, args.transaction_id)
        else:
            service.delete_transaction(args.transaction_id)
            print(f"거래가 삭제되었습니다. 거래 ID: {args.transaction_id}")
        return 0
    raise PantryError(
        f"'{args.command}' 기능은 아직 구현되지 않았습니다.",
        "'--help'로 명령과 옵션을 확인해 주세요. 해당 기능은 후속 단계에서 구현됩니다.",
    )


def prompt_value(prompt: str, validator: Callable[[str], T]) -> T:
    """필드가 올바를 때까지 원인과 힌트를 안내하며 재입력받는다."""
    while True:
        try:
            return validator(input(prompt))
        except PantryError as exc:
            print_error(str(exc), exc.hint)


def add_interactive(service: PantryService) -> None:
    """날짜, 타입, 카테고리, 금액, 메모와 태그를 입력받는다."""
    categories = service.category_names()
    if not categories:
        raise PantryError("등록된 카테고리가 없어 거래를 추가할 수 없습니다.",
                          "카테고리를 먼저 등록해 주세요.")
    print(format_title("거래 추가"))
    date = prompt_value("날짜 (YYYY-MM-DD): ", parse_date)
    transaction_type = prompt_value("타입 (income/expense): ", parse_type)
    print("카테고리: " + " / ".join(format_category(name) for name in categories))
    category = prompt_value("카테고리 이름: ", service.validate_category)
    amount = prompt_value("금액 (양수 정수): ", parse_amount)
    memo = input("메모 (선택): ")
    tags = parse_tags(input("태그 (선택, 쉼표 구분): "))
    transaction = service.add_transaction(
        date=date, type=transaction_type, category=category, amount=amount,
        memo=memo, tags=tags,
    )
    print(f"\n거래가 저장되었습니다. 거래 ID: {transaction.id}")


def prompt_update(label: str, current: T, validator: Callable[[str], T]) -> T:
    """빈 입력은 기존 값을 유지하고 변경 입력은 검증한다."""
    return prompt_value(f"{label} [{current}] (Enter: 유지): ",
                        lambda value: current if value == "" else validator(value))


def update_interactive(service: PantryService, transaction_id: str) -> None:
    """각 필드를 수정하거나 Enter로 기존 값을 유지한다."""
    current = service.get_transaction(transaction_id)
    print(format_title(f"거래 수정 | {current.id}"))
    date = prompt_update("날짜 (YYYY-MM-DD)", current.date, parse_date)
    transaction_type = prompt_update("타입 (income/expense)", current.type, parse_type)
    print("카테고리: " + " / ".join(format_category(name) for name in service.category_names()))
    category = prompt_update("카테고리", current.category, service.validate_category)
    amount = prompt_update("금액", current.amount, parse_amount)
    memo = prompt_update("메모", current.memo, lambda value: value)
    tags_text = input(f"태그 [{', '.join(current.tags)}] (쉼표 구분, Enter: 유지): ")
    tags = current.tags if tags_text == "" else parse_tags(tags_text)
    service.update_transaction(transaction_id, date=date, type=transaction_type,
                               category=category, amount=amount, memo=memo, tags=tags)
    print(f"\n거래가 수정되었습니다. 거래 ID: {transaction_id}")


@handle_errors
def main(argv: Sequence[str] | None = None) -> int:
    """CLI 인자를 해석하고 명령 실행 결과를 종료 코드로 반환한다."""
    args = build_parser().parse_args(argv)
    return dispatch(args)
