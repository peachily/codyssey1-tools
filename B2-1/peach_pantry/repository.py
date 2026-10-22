"""제너레이터 읽기와 원자적 파일 교체를 제공하는 JSONL 저장소.

거래 파일의 첫 줄은 마지막 발급 번호 메타데이터다. 거래가 모두 삭제되어도
이 번호를 유지한다. 동시 프로세스의 쓰기는 지원하지 않는다.
"""

from dataclasses import asdict
import json
import os
from pathlib import Path
import tempfile
from typing import Iterable, Iterator

from .errors import PantryError
from .models import Budget, Category, Transaction, transaction_number

DEFAULT_CATEGORIES = (
    "식비", "카페", "교통", "쇼핑", "생활", "주거",
    "건강", "문화", "교육", "급여", "용돈", "기타",
)


def read_jsonl(path: Path) -> Iterator[dict]:
    """파일을 한 줄씩 읽고 손상된 레코드의 위치를 안내한다."""
    try:
        with path.open("r", encoding="utf-8") as source:
            for line_number, line in enumerate(source, 1):
                try:
                    record = json.loads(line)
                    if not isinstance(record, dict):
                        raise ValueError("객체가 아닙니다.")
                except ValueError as exc:
                    raise PantryError(
                        f"{path.name}의 {line_number}번째 줄이 올바른 JSON 객체가 아닙니다.",
                        "원본 파일을 백업한 뒤 해당 줄의 JSON 형식을 확인해 주세요.",
                    ) from exc
                yield record
    except UnicodeError as exc:
        raise PantryError(f"{path.name}을 UTF-8로 읽을 수 없습니다.",
                          "파일을 백업한 뒤 UTF-8 인코딩인지 확인해 주세요.") from exc


def replace_jsonl(path: Path, records: Iterable[dict]) -> None:
    """같은 폴더의 임시 파일에 기록한 뒤 원본을 한 번에 교체한다."""
    temporary_path = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="w", encoding="utf-8", newline="\n", dir=path.parent,
            prefix=f".{path.name}.", suffix=".tmp", delete=False,
        ) as target:
            temporary_path = Path(target.name)
            for record in records:
                target.write(json.dumps(record, ensure_ascii=False, allow_nan=False) + "\n")
            target.flush()
            os.fsync(target.fileno())
        os.replace(temporary_path, path)
    finally:
        if temporary_path is not None:
            temporary_path.unlink(missing_ok=True)


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
    def _metadata(last_id: int) -> dict:
        return {"record_type": "metadata", "last_id": last_id}

    def _read_metadata(self, records: Iterator[dict]) -> int:
        record = next(records, None)
        if (not isinstance(record, dict)
                or set(record) != {"record_type", "last_id"}
                or record["record_type"] != "metadata"
                or type(record["last_id"]) is not int or record["last_id"] < 0):
            raise self._invalid_record(self.transactions_path, 1)
        return record["last_id"]

    @staticmethod
    def _invalid_record(path: Path, line_number: int) -> PantryError:
        return PantryError(
            f"{path.name}의 {line_number}번째 줄에 잘못된 데이터가 있습니다.",
            "파일을 백업한 뒤 필드와 값의 형식을 확인해 주세요. 거래 파일 첫 줄에는 ID 메타데이터가 필요합니다.",
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

        def records() -> Iterator[dict]:
            yield self._metadata(last_id)
            for existing in self.iter_transactions():
                yield existing.to_record()
            yield transaction.to_record()

        replace_jsonl(self.transactions_path, records())
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
