"""터미널 안내 문구의 출력 형식."""

import sys
from typing import Iterable, TextIO

from .models import Transaction

CATEGORY_EMOJIS = {
    "식비": "🍚", "카페": "☕", "교통": "🚌", "쇼핑": "🛍️",
    "생활": "🧺", "주거": "🏠", "건강": "💊", "문화": "🎬",
    "교육": "📚", "급여": "💰", "용돈": "🎁", "기타": "📦",
}


def format_title(title: str) -> str:
    """표시 너비 계산 없이 제목과 구분선을 구성한다."""
    return f"복숭아창고 (Peach Pantry) | {title}\n{'─' * 40}"


def print_error(message: str, hint: str, stream: TextIO | None = None) -> None:
    """원인과 해결 힌트를 오류 출력 스트림에 표시한다."""
    target = sys.stderr if stream is None else stream
    print(f"[오류] {message}\n[힌트] {hint}", file=target)


def format_category(name: str) -> str:
    """이모지는 저장하지 않고 출력할 때만 붙인다."""
    return f"{CATEGORY_EMOJIS.get(name, '📦')} {name}"


def format_transaction(transaction: Transaction) -> str:
    """이모지 너비에 의존하지 않도록 필드를 구분자로 나누어 표시한다."""
    sign = "+" if transaction.type == "income" else "-"
    label = "수입" if transaction.type == "income" else "지출"
    memo = transaction.memo.replace("\r", "\\r").replace("\n", "\\n").replace("\t", "\\t")
    tags = ", ".join(transaction.tags) or "없음"
    return (
        f"{transaction.date} | {transaction.id} | {label} | {sign}{transaction.amount:,}원\n"
        f"  카테고리: {format_category(transaction.category)}\n"
        f"  메모: {memo or '없음'} | 태그: {tags}"
    )


def print_transactions(transactions: Iterable[Transaction]) -> None:
    """목록과 거래가 없는 경우의 안내를 출력한다."""
    print(format_title("최근 거래"))
    count = 0
    for transaction in transactions:
        print(f"\n{format_transaction(transaction)}")
        count += 1
    if count == 0:
        print("\n등록된 거래가 없습니다. add 명령으로 첫 거래를 기록해 주세요.")
    else:
        print(f"\n총 {count}건")
