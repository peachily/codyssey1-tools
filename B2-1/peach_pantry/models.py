"""JSONL에 저장하는 거래, 카테고리와 월별 예산 모델."""

from dataclasses import asdict, dataclass
from datetime import date
from decimal import Decimal
import re


def transaction_number(transaction_id: str) -> int:
    """정규 형식의 거래 ID에서 일련번호를 얻는다."""
    if not isinstance(transaction_id, str) or not re.fullmatch(r"TX-[0-9]{6,}", transaction_id):
        raise ValueError("거래 ID 형식이 올바르지 않습니다.")
    number = int(transaction_id[3:])
    if number < 1 or transaction_id != f"TX-{number:06d}":
        raise ValueError("거래 ID 형식이 올바르지 않습니다.")
    return number


def validate_amount(amount: int) -> None:
    """금액은 bool을 제외한 양수 정수로 제한한다."""
    if type(amount) is not int or amount <= 0:
        raise ValueError("금액은 양수 정수여야 합니다.")


def validate_date(value: str) -> None:
    """실제로 존재하는 YYYY-MM-DD 날짜인지 확인한다."""
    if not isinstance(value, str) or not re.fullmatch(r"[0-9]{4}-[0-9]{2}-[0-9]{2}", value):
        raise ValueError("날짜는 YYYY-MM-DD 형식이어야 합니다.")
    date.fromisoformat(value)


def validate_month(value: str) -> None:
    """실제로 존재하는 YYYY-MM 월인지 확인한다."""
    if not isinstance(value, str) or not re.fullmatch(r"[0-9]{4}-[0-9]{2}", value):
        raise ValueError("월은 YYYY-MM 형식이어야 합니다.")
    date.fromisoformat(f"{value}-01")


@dataclass(frozen=True)
class Transaction:
    """이모지가 포함되지 않은 하나의 거래 레코드."""

    id: str
    date: str
    type: str
    category: str
    amount: int
    memo: str = ""
    tags: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        transaction_number(self.id)
        validate_date(self.date)
        if self.type not in ("income", "expense"):
            raise ValueError("타입은 income 또는 expense여야 합니다.")
        Category(self.category)
        validate_amount(self.amount)
        if not isinstance(self.memo, str):
            raise ValueError("메모는 문자열이어야 합니다.")
        if not isinstance(self.tags, tuple) or any(not isinstance(tag, str) for tag in self.tags):
            raise ValueError("태그는 문자열 튜플이어야 합니다.")

    def to_record(self) -> dict:
        """JSON 객체로 직렬화할 수 있는 필드를 반환한다."""
        record = asdict(self)
        record["tags"] = list(self.tags)
        return record

    @classmethod
    def from_record(cls, record: dict) -> "Transaction":
        """JSON 배열로 저장된 태그를 튜플로 복원한다."""
        fields = dict(record)
        tags = fields.get("tags")
        if not isinstance(tags, list):
            raise ValueError("저장된 태그는 배열이어야 합니다.")
        fields["tags"] = tuple(tags)
        return cls(**fields)


@dataclass(frozen=True)
class Category:
    """출력용 이모지를 제외한 카테고리 이름."""

    name: str

    def __post_init__(self) -> None:
        if not isinstance(self.name, str) or not self.name.strip():
            raise ValueError("카테고리 이름은 비어 있을 수 없습니다.")


@dataclass(frozen=True)
class Budget:
    """한 달의 예산 금액."""

    month: str
    amount: int

    def __post_init__(self) -> None:
        validate_month(self.month)
        validate_amount(self.amount)


@dataclass(frozen=True)
class MonthlySummary:
    """파일에 저장하지 않는 월별 집계 결과."""

    month: str
    income: int
    expense: int
    transaction_count: int
    top_expenses: tuple[tuple[str, int], ...]
    budget: int | None

    @property
    def balance(self) -> int:
        """해당 월의 총수입에서 총지출을 뺀 금액."""
        return self.income - self.expense

    @property
    def budget_usage(self) -> Decimal | None:
        """수입과 무관한 지출 기준 예산 사용률 (%)."""
        if self.budget is None:
            return None
        return Decimal(self.expense) / Decimal(self.budget) * 100

    @property
    def budget_exceeded(self) -> bool:
        """반올림한 사용률 대신 실제 금액으로 초과 여부를 판정한다."""
        return self.budget is not None and self.expense > self.budget
