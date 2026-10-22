"""화면 입출력과 독립적인 거래, 카테고리 및 예산 관리 규칙."""

import heapq
from calendar import monthrange
from contextlib import closing
from dataclasses import replace
from pathlib import Path
from typing import Iterator

from .errors import PantryError
from .csv_io import read_csv, write_csv
from .models import Budget, Category, MonthlySummary, Transaction, transaction_number
from .repository import PantryRepository
from .sorting import latest_first
from .validators import check_amount, parse_category_name, parse_date, parse_month, parse_type


class PantryService:
    """데이터 검증과 가계부 관리 규칙을 적용한다."""

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

    def add_category(self, name: str) -> Category:
        """이름 중복을 차단하고 카테고리를 영구 저장한다."""
        name = parse_category_name(name)
        categories = list(self.repository.iter_categories())
        if any(category.name == name for category in categories):
            raise PantryError(f"'{name}' 카테고리는 이미 등록되어 있습니다.",
                              "category list로 확인하거나 다른 이름을 입력해 주세요.")
        category = Category(name)
        self.repository.save_categories([*categories, category])
        return category

    def remove_category(self, name: str) -> None:
        """사용 중인 카테고리는 차단하고 나머지는 안전하게 삭제한다."""
        name = parse_category_name(name)
        categories = list(self.repository.iter_categories())
        if not any(category.name == name for category in categories):
            raise PantryError(f"'{name}' 카테고리를 찾을 수 없습니다.",
                              "category list로 등록된 이름을 확인해 주세요.")
        with closing(self.repository.iter_transactions()) as transactions:
            for transaction in transactions:
                if transaction.category == name:
                    raise PantryError(f"'{name}' 카테고리는 거래에서 사용 중입니다.",
                                      "해당 거래의 카테고리를 수정하거나 거래를 삭제한 뒤 다시 시도해 주세요.")
        self.repository.save_categories(category for category in categories if category.name != name)

    def set_budget(self, month: str, amount: int) -> Budget:
        """월별 예산을 저장하며 같은 월은 기존 금액을 대체한다."""
        budget = Budget(parse_month(month), check_amount(amount))
        budgets = [existing for existing in self.repository.iter_budgets()
                   if existing.month != budget.month]
        self.repository.save_budgets([*budgets, budget])
        return budget

    def summary(self, month: str, top: int = 3) -> MonthlySummary:
        """월별 합계를 순차 집계한다. 거래 대신 카테고리별 합계만 유지한다."""
        month = parse_month(month)
        if type(top) is not int or top <= 0:
            raise PantryError("지출 순위 건수가 올바르지 않습니다.",
                              "--top에 0보다 큰 정수를 지정해 주세요.", exit_code=2)
        income = expense = count = 0
        category_expenses: dict[str, int] = {}
        for transaction in self.repository.iter_transactions():
            if transaction.date[:7] != month:
                continue
            count += 1
            if transaction.type == "income":
                income += transaction.amount
            else:
                expense += transaction.amount
                category_expenses[transaction.category] = (
                    category_expenses.get(transaction.category, 0) + transaction.amount
                )
        top_expenses = tuple(sorted(category_expenses.items(),
                                    key=lambda item: (-item[1], item[0]))[:top])
        budget_amount = None
        for budget in self.repository.iter_budgets():
            if budget.month == month:
                budget_amount = budget.amount
        return MonthlySummary(month, income, expense, count, top_expenses, budget_amount)

    def import_csv(self, path: str | Path) -> int:
        """CSV 전체 검증 후 한 번의 파일 교체로 모든 거래를 가져온다."""
        fields = read_csv(Path(path), set(self.category_names()))
        return self.repository.add_transactions(fields)

    def export_csv(
        self, path: str | Path, *, month: str | None = None,
        date_from: str | None = None, date_to: str | None = None,
    ) -> int:
        """필수 날짜 조건을 검증하고 거래를 순차적으로 CSV에 내보낸다."""
        if month is not None and (date_from is not None or date_to is not None):
            raise PantryError("월과 날짜 범위 조건은 함께 사용할 수 없습니다.",
                              "--month 또는 --from/--to 중 하나를 선택해 주세요.")
        if month is None and date_from is None and date_to is None:
            raise PantryError("내보내기에 날짜 조건이 필요합니다.",
                              "--month 또는 --from/--to로 기간을 지정해 주세요.")
        if month is not None:
            month = parse_month(month)
            year, number = map(int, month.split("-"))
            start, end = f"{month}-01", f"{month}-{monthrange(year, number)[1]:02d}"
        else:
            start = parse_date(date_from) if date_from is not None else None
            end = parse_date(date_to) if date_to is not None else None
        if start is not None and end is not None and start > end:
            raise PantryError("내보내기 시작일이 종료일보다 늦습니다.",
                              "--from이 --to보다 이르거나 같도록 입력해 주세요.")
        destination = Path(path)
        for protected in (self.repository.transactions_path, self.repository.categories_path,
                          self.repository.budgets_path):
            if (destination.resolve() == protected.resolve()
                    or (destination.exists() and protected.exists() and destination.samefile(protected))):
                raise PantryError("데이터 저장소 파일에는 CSV를 덮어쓸 수 없습니다.",
                                  "--out에 JSONL 저장소와 다른 CSV 경로를 지정해 주세요.")

        def matches() -> Iterator[Transaction]:
            for transaction in self.repository.iter_transactions():
                if start is not None and transaction.date < start:
                    continue
                if end is not None and transaction.date > end:
                    continue
                yield transaction

        return write_csv(destination, matches())

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
