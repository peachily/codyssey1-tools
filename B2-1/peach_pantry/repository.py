"""3개 JSONL 파일의 모델 변환, 초기화와 고유 거래 ID 관리.

거래 파일 첫 줄에 마지막 발급 번호를 저장한다. 거래가 모두 삭제되어도
이 번호를 유지한다. 동시 프로세스의 쓰기는 지원하지 않는다.
"""

from dataclasses import asdict
from pathlib import Path
from typing import Iterable, Iterator, Sequence

from .errors import PantryError
from .jsonl import read_jsonl, replace_jsonl
from .models import Budget, Category, Transaction, transaction_number

DEFAULT_CATEGORIES = (
    "식비", "카페", "교통", "쇼핑", "생활", "주거",
    "건강", "문화", "교육", "급여", "용돈", "기타",
)


class PantryRepository:
    """3개 JSONL 파일의 초기화, 모델 변환과 안전한 저장을 담당한다."""

    def __init__(self, data_dir: str | Path = "./data") -> None:
        self.data_dir = Path(data_dir)
        self.transactions_path = self.data_dir / "transactions.jsonl"
        self.categories_path = self.data_dir / "categories.jsonl"
        self.budgets_path = self.data_dir / "budgets.jsonl"

    def initialize(self) -> None:
        """없는 파일만 만들며, 빈 카테고리 파일은 복원하지 않는다."""
        self.data_dir.mkdir(parents=True, exist_ok=True)
        if not self.transactions_path.exists():
            replace_jsonl(self.transactions_path, [self._metadata(0)])
        if not self.categories_path.exists():
            self.save_categories(Category(name) for name in DEFAULT_CATEGORIES)
        if not self.budgets_path.exists():
            self.save_budgets(())

    @staticmethod
    # 이 메서드가 self나 cls 없이 동작하도록 지정
    def _metadata(last_id: int) -> dict:
        """거래 파일 첫 줄에 보관할 마지막 발급 번호를 만든다."""
        return {"record_type": "metadata", "last_id": last_id}

    def _read_metadata(self, records: Iterator[dict]) -> int:
        """첫 레코드의 ID 메타데이터를 검증하여 반환한다."""
        record = next(records, None)
        if (not isinstance(record, dict)
                or set(record) != {"record_type", "last_id"}
                or record["record_type"] != "metadata"
                or type(record["last_id"]) is not int or record["last_id"] < 0):
            raise self._invalid_record(self.transactions_path, 1)
        return record["last_id"]

    @staticmethod
    def _invalid_record(path: Path, line_number: int) -> PantryError:
        """손상된 레코드 위치와 해당 파일에 맞는 복구 힌트를 구성한다."""
        hint = "파일을 백업한 뒤 필드와 값의 형식을 확인해 주세요."
        if path.name == "transactions.jsonl":
            hint += " 거래 파일 첫 줄에는 ID 메타데이터가 필요합니다."
        return PantryError(
            f"{path.name}의 {line_number}번째 줄에 잘못된 데이터가 있습니다.",
            hint,
        )

    def iter_transactions(self) -> Iterator[Transaction]:
        """메타데이터를 제외한 거래를 파일 순서대로 한 건씩 반환한다."""
        records = read_jsonl(self.transactions_path)
        try:
            last_id = self._read_metadata(records)
            for line_number, record in enumerate(records, 2):
                try:
                    transaction = Transaction.from_record(record)
                    if transaction_number(transaction.id) > last_id:
                        raise ValueError("발급 번호를 초과합니다.")
                except (TypeError, ValueError) as exc:
                    raise self._invalid_record(self.transactions_path, line_number) from exc
                yield transaction
        finally:
            records.close()

    def _last_id(self) -> int:
        """거래 전체를 읽지 않고 마지막 발급 번호만 조회한다."""
        records = read_jsonl(self.transactions_path)
        try:
            return self._read_metadata(records)
        finally:
            records.close()

    def add_transaction(
        self, *, date: str, type: str, category: str, amount: int,
        memo: str = "", tags: tuple[str, ...] = (),
    ) -> Transaction:
        """거래와 발급 번호를 함께 저장하여 성공한 거래에 ID를 발급한다."""
        last_id = self._last_id() + 1
        transaction = Transaction(f"TX-{last_id:06d}", date, type, category, amount, memo, tags)
        self._append_transactions([transaction])
        return transaction

    def save_transactions(self, transactions: Iterable[Transaction]) -> None:
        """거래를 교체하면서 마지막 발급 번호를 유지한다."""
        last_id = self._last_id()

        def records() -> Iterator[dict]:
            yield self._metadata(last_id)
            for transaction in transactions:
                if transaction_number(transaction.id) > last_id:
                    raise ValueError("발급되지 않은 거래 ID입니다.")
                yield transaction.to_record()

        replace_jsonl(self.transactions_path, records())

    def add_transactions(self, fields: Sequence[dict]) -> int:
        """검증된 여러 거래와 마지막 발급 번호를 한 번의 교체로 저장한다."""
        if not fields:
            return 0
        last_id = self._last_id()
        transactions = [Transaction(id=f"TX-{last_id + index:06d}", **values)
                        for index, values in enumerate(fields, 1)]
        self._append_transactions(transactions)
        return len(transactions)

    def _append_transactions(self, transactions: Sequence[Transaction]) -> None:
        """추가 거래와 발급 번호를 함께 반영한다. 기존 파일은 순차 복사한다."""

        def records() -> Iterator[dict]:
            yield self._metadata(transaction_number(transactions[-1].id))
            for existing in self.iter_transactions():
                yield existing.to_record()
            for transaction in transactions:
                yield transaction.to_record()

        replace_jsonl(self.transactions_path, records())

    def iter_categories(self) -> Iterator[Category]:
        """저장된 카테고리를 순차적으로 반환한다."""
        for line_number, record in enumerate(read_jsonl(self.categories_path), 1):
            try:
                category = Category(**record)
            except (TypeError, ValueError) as exc:
                raise self._invalid_record(self.categories_path, line_number) from exc
            yield category

    def save_categories(self, categories: Iterable[Category]) -> None:
        """카테고리 전체를 원자적으로 저장한다."""
        replace_jsonl(self.categories_path, (asdict(category) for category in categories))

    def iter_budgets(self) -> Iterator[Budget]:
        """저장된 월별 예산을 순차적으로 반환한다."""
        for line_number, record in enumerate(read_jsonl(self.budgets_path), 1):
            try:
                budget = Budget(**record)
            except (TypeError, ValueError) as exc:
                raise self._invalid_record(self.budgets_path, line_number) from exc
            yield budget

    def save_budgets(self, budgets: Iterable[Budget]) -> None:
        """월별 예산 전체를 원자적으로 저장한다."""
        replace_jsonl(self.budgets_path, (asdict(budget) for budget in budgets))
