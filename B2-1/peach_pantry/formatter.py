"""터미널 안내 문구의 출력 형식."""

import sys
from typing import Iterable, TextIO

from .models import MonthlySummary, Transaction

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


def print_categories(names: Iterable[str]) -> None:
    """이모지를 포함한 카테고리 목록 또는 빈 목록 안내를 출력한다."""
    print(format_title("카테고리 목록"))
    count = 0
    for name in names:
        print(f"  {format_category(name)}")
        count += 1
    if count == 0:
        print("등록된 카테고리가 없습니다. category add로 등록해 주세요.")
    else:
        print(f"\n총 {count}개")


def print_summary(summary: MonthlySummary, top: int = 3) -> None:
    """월별 합계, 지출 순위와 설정된 예산의 사용률을 출력한다."""
    print(format_title(f"{summary.month} 월별 요약"))
    if summary.transaction_count == 0:
        print("\n해당 월에 등록된 거래가 없습니다.")
    print(f"\n총수입: +{summary.income:,}원")
    print(f"총지출: -{summary.expense:,}원")
    print(f"잔액: {summary.balance:+,}원")
    print(f"\n카테고리별 지출 TOP {top}")
    if summary.top_expenses:
        for rank, (category, amount) in enumerate(summary.top_expenses, 1):
            print(f"  {rank}. {format_category(category)} | {amount:,}원")
    else:
        print("  해당 월의 지출이 없습니다.")
    if summary.budget is not None:
        print(f"\n월 예산: {summary.budget:,}원")
        print(f"예산 사용률: {summary.budget_usage:.1f}%")
        if summary.budget_exceeded:
            print(f"[경고] 월 예산을 {summary.expense - summary.budget:,}원 초과했습니다.")


def format_transaction(transaction: Transaction) -> str:
    """이모지 너비에 의존하지 않도록 필드를 구분자로 나누어 표시한다."""
    sign = "+" if transaction.type == "income" else "-"
    label = "수입" if transaction.type == "income" else "지출"
    memo = single_line(transaction.memo)
    tags = ", ".join(single_line(tag) for tag in transaction.tags) or "없음"
    return (
        f"{transaction.date} | {transaction.id} | {label} | {sign}{transaction.amount:,}원\n"
        f"  카테고리: {format_category(transaction.category)}\n"
        f"  메모: {memo or '없음'} | 태그: {tags}"
    )


def single_line(value: str) -> str:
    """CSV에서 가져온 줄바꿈과 탭이 목록의 필드 구분을 깨지 않게 한다."""
    return value.replace("\r", "\\r").replace("\n", "\\n").replace("\t", "\\t")


def print_transactions(transactions: Iterable[Transaction], *, title: str = "최근 거래",
                       empty_message: str = "등록된 거래가 없습니다. add 명령으로 첫 거래를 기록해 주세요.") -> None:
    """목록과 거래가 없는 경우의 안내를 출력한다."""
    print(format_title(title))
    count = 0
    for transaction in transactions:
        print(f"\n{format_transaction(transaction)}")
        count += 1
    if count == 0:
        print(f"\n{empty_message}")
    else:
        print(f"\n총 {count}건")
