"""터미널 안내 문구의 출력 형식."""

import sys
from typing import TextIO


def format_title(title: str) -> str:
    """표시 너비 계산 없이 제목과 구분선을 구성한다."""
    return f"복숭아창고 (Peach Pantry) | {title}\n{'─' * 40}"


def print_error(message: str, hint: str, stream: TextIO | None = None) -> None:
    """원인과 해결 힌트를 오류 출력 스트림에 표시한다."""
    target = sys.stderr if stream is None else stream
    print(f"[오류] {message}\n[힌트] {hint}", file=target)
