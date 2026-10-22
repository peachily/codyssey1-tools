"""거래 추가·수정의 대화형 입력과 재입력을 담당한다."""

from typing import Callable, TypeVar

from .errors import PantryError
from .formatter import format_category, format_title, print_error
from .service import PantryService
from .validators import parse_amount, parse_date, parse_tags, parse_type

T = TypeVar("T")


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
                          "category add로 카테고리를 먼저 등록해 주세요.")
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
