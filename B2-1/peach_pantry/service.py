"""화면 입출력과 독립적인 거래 추가 및 조회 규칙."""

import heapq

from .errors import PantryError
from .models import Transaction, transaction_number
from .repository import PantryRepository
from .validators import check_amount, parse_date, parse_type


class PantryService:
    """거래 검증과 메모리 효율적인 최신 거래 조회를 담당한다."""

    def __init__(self, repository: PantryRepository) -> None:
        self.repository = repository

    def category_names(self) -> list[str]:
        """입력 안내에 사용할 등록 카테고리 이름을 반환한다."""
        return [category.name for category in self.repository.iter_categories()]

    def validate_category(self, name: str) -> str:
        """등록된 카테고리만 거래에 사용할 수 있게 한다."""
        name = name.strip()
        if name not in self.category_names():
            raise PantryError("등록되지 않은 카테고리입니다.",
                              "안내된 카테고리 이름을 이모지 없이 입력해 주세요.")
        return name

    def add_transaction(
        self, *, date: str, type: str, category: str, amount: int,
        memo: str = "", tags: tuple[str, ...] = (),
    ) -> Transaction:
        """필드를 검증한 후 거래를 저장하고 발급된 ID를 반환한다."""
        return self.repository.add_transaction(
            date=parse_date(date), type=parse_type(type),
            category=self.validate_category(category), amount=check_amount(amount),
            memo=memo, tags=tags,
        )

    def list_transactions(self, limit: int = 10) -> list[Transaction]:
        """파일 전체를 순회하면서 최신 N건만 힙에 유지한다 (메모리 O(N))."""
        if type(limit) is not int or limit <= 0:
            raise PantryError("조회 건수가 올바르지 않습니다.",
                              "--limit에 0보다 큰 정수를 지정해 주세요.", exit_code=2)
        return heapq.nlargest(
            limit, self.repository.iter_transactions(),
            key=lambda transaction: (transaction.date, transaction_number(transaction.id)),
        )
