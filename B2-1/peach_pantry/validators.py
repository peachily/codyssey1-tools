"""사용자 입력을 검증하고 한국어 해결 힌트를 제공한다."""

import re

from .errors import PantryError
from .models import validate_amount, validate_date


def parse_date(value: str) -> str:
    """실제 달력 날짜를 지정된 형식으로 받는다."""
    value = value.strip()
    try:
        validate_date(value)
    except ValueError as exc:
        raise PantryError("날짜 형식이나 값이 올바르지 않습니다.",
                          "실제로 존재하는 날짜를 YYYY-MM-DD 형식으로 입력해 주세요.") from exc
    return value


def parse_type(value: str) -> str:
    """거래 타입의 영어 이름을 검증한다."""
    value = value.strip()
    if value not in ("income", "expense"):
        raise PantryError("거래 타입이 올바르지 않습니다.", "income 또는 expense를 입력해 주세요.")
    return value


def check_amount(amount: int) -> int:
    """서비스에 전달된 금액도 양수 정수인지 확인한다."""
    try:
        validate_amount(amount)
    except ValueError as exc:
        raise PantryError("금액이 올바르지 않습니다.", "0보다 큰 정수로 입력해 주세요.") from exc
    return amount


def parse_amount(value: str) -> int:
    """부호, 소수점과 쉼표 없는 양수 정수 입력을 변환한다."""
    value = value.strip()
    try:
        if not re.fullmatch(r"[0-9]+", value):
            raise ValueError("정수가 아닙니다.")
        amount = int(value)
    except ValueError as exc:
        raise PantryError("금액이 올바르지 않습니다.",
                          "쉼표나 소수점 없이 0보다 큰 정수로 입력해 주세요.") from exc
    return check_amount(amount)


def parse_tags(value: str) -> tuple[str, ...]:
    """쉼표로 구분한 태그를 정리하고 빈 항목은 제외한다."""
    return tuple(tag.strip() for tag in value.split(",") if tag.strip())
