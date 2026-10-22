"""화면 입출력과 독립적인 거래 추가 및 조회 규칙."""

import heapq
from contextlib import closing
from dataclasses import replace
from typing import Iterator

from .errors import PantryError
from .models import Transaction, transaction_number
from .repository import PantryRepository
from .sorting import latest_first
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

    def search_transactions(
        self, *, date_from: str | None = None, date_to: str | None = None,
        category: str | None = None, type: str | None = None,
        q: str | None = None, tag: str | None = None,
    ) -> Iterator[Transaction]:
        """조건을 AND로 적용하고 임시 디스크에서 최신순 정렬한다."""
        start = parse_date(date_from) if date_from is not None else None
        end = parse_date(date_to) if date_to is not None else None
        if start is not None and end is not None and start > end:
            raise PantryError("검색 시작일이 종료일보다 늦습니다.",
                              "--from이 --to보다 이르거나 같도록 입력해 주세요.")
        if type is not None:
            type = parse_type(type)
        if category is not None:
            category = self.validate_category(category)

        def matches() -> Iterator[Transaction]:
            for transaction in self.repository.iter_transactions():
                if start is not None and transaction.date < start:
                    continue
                if end is not None and transaction.date > end:
                    continue
                if category is not None and transaction.category != category:
                    continue
                if type is not None and transaction.type != type:
                    continue
                if q is not None and q not in transaction.memo:
                    continue
                if tag is not None and tag not in transaction.tags:
                    continue
                yield transaction

        return latest_first(matches())

    @staticmethod
    def _check_id(transaction_id: str) -> None:
        try:
            transaction_number(transaction_id)
        except ValueError as exc:
            raise PantryError("거래 ID 형식이 올바르지 않습니다.",
                              "list에서 확인한 TX-000001 형식의 ID를 입력해 주세요.") from exc

    @staticmethod
    def _missing_id(transaction_id: str) -> PantryError:
        return PantryError(f"거래 ID '{transaction_id}'를 찾을 수 없습니다.",
                           "list 명령으로 거래 ID를 확인해 주세요.")

    def get_transaction(self, transaction_id: str) -> Transaction:
        """수정할 거래를 순차 탐색하고 파일을 닫는다."""
        self._check_id(transaction_id)
        with closing(self.repository.iter_transactions()) as transactions:
            for transaction in transactions:
                if transaction.id == transaction_id:
                    return transaction
        raise self._missing_id(transaction_id)

    def update_transaction(
        self, transaction_id: str, *, date: str | None = None,
        type: str | None = None, category: str | None = None,
        amount: int | None = None, memo: str | None = None,
        tags: tuple[str, ...] | None = None,
    ) -> Transaction:
        """None 필드는 유지하고 검증된 수정본으로 원본을 안전하게 교체한다."""
        current = self.get_transaction(transaction_id)
        try:
            updated = replace(
                current, date=current.date if date is None else parse_date(date),
                type=current.type if type is None else parse_type(type),
                category=current.category if category is None else self.validate_category(category),
                amount=current.amount if amount is None else check_amount(amount),
                memo=current.memo if memo is None else memo,
                tags=current.tags if tags is None else tags,
            )
        except ValueError as exc:
            raise PantryError("수정할 값이 올바르지 않습니다.",
                              "메모와 태그의 문자열 형식을 확인해 주세요.") from exc

        def replacements() -> Iterator[Transaction]:
            found = False
            for transaction in self.repository.iter_transactions():
                if transaction.id == transaction_id:
                    found = True
                    yield updated
                else:
                    yield transaction
            if not found:
                raise self._missing_id(transaction_id)

        self.repository.save_transactions(replacements())
        return updated

    def delete_transaction(self, transaction_id: str) -> None:
        """대상을 제외한 레코드로 교체하며 없는 ID면 원본을 유지한다."""
        self._check_id(transaction_id)

        def remaining() -> Iterator[Transaction]:
            found = False
            for transaction in self.repository.iter_transactions():
                if transaction.id == transaction_id:
                    found = True
                else:
                    yield transaction
            if not found:
                raise self._missing_id(transaction_id)

        self.repository.save_transactions(remaining())
