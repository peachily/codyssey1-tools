"""명령 해석 결과를 서비스와 입출력에 연결하는 실행 계층."""

import argparse
from contextlib import closing
from typing import Sequence

from .errors import PantryError, handle_errors
from .formatter import (
    format_category, print_categories, print_summary, print_transactions,
)
from .parser import build_parser
from .prompts import add_interactive, update_interactive
from .repository import PantryRepository
from .service import PantryService


def dispatch(args: argparse.Namespace) -> int:
    """저장소를 초기화하고 선택한 명령을 실행한다."""
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
    elif args.command == "delete":
        service.delete_transaction(args.transaction_id)
        print(f"거래가 삭제되었습니다. 거래 ID: {args.transaction_id}")
    elif args.command == "category":
        if args.category_command == "add":
            category = service.add_category(args.name)
            print(f"카테고리가 등록되었습니다. {format_category(category.name)}")
        elif args.category_command == "list":
            print_categories(service.category_names())
        else:
            service.remove_category(args.name)
            print(f"카테고리가 삭제되었습니다. {format_category(args.name.strip())}")
    elif args.command == "budget":
        budget = service.set_budget(args.month, args.amount)
        print(f"{budget.month} 예산이 저장되었습니다. {budget.amount:,}원")
    elif args.command == "summary":
        print_summary(service.summary(args.month, args.top), args.top)
    elif args.command == "import":
        count = service.import_csv(args.input_csv)
        print(f"CSV 가져오기가 완료되었습니다. {count}건")
    else:
        count = service.export_csv(args.out, month=args.month,
                                   date_from=args.date_from, date_to=args.date_to)
        print(f"CSV 내보내기가 완료되었습니다. {count}건")
    return 0


@handle_errors
def main(argv: Sequence[str] | None = None) -> int:
    """CLI 인자를 해석하고 명령 실행 결과를 종료 코드로 반환한다."""
    args = build_parser().parse_args(argv)
    return dispatch(args)
