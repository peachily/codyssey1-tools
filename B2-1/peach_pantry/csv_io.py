"""고정 CSV 스키마 검증과 안전한 UTF-8 파일 입출력."""

import csv
from pathlib import Path
from typing import Iterable

from .errors import PantryError
from .file_io import atomic_text_writer
from .models import Transaction
from .validators import parse_amount, parse_date, parse_tags, parse_type

CSV_COLUMNS = ("date", "type", "category", "amount", "memo", "tags")


def read_csv(path: Path, categories: set[str]) -> list[dict]:
    """모든 행을 검증하여 반환한다. 검증 중에는 거래 파일을 변경하지 않는다.

    가져올 CSV의 검증 결과는 메모리에 보관한다. 기존 거래 JSONL은 별도로
    스트리밍하며 CSV 크기에 비례하는 메모리 사용과 구분한다.
    """
    transactions = []
    try:
        with path.open("r", encoding="utf-8-sig", newline="") as source:
            reader = csv.reader(source, strict=True)
            if next(reader, None) != list(CSV_COLUMNS):
                raise PantryError("CSV 헤더가 올바르지 않습니다. 전체 가져오기를 취소합니다.",
                                  "헤더를 date,type,category,amount,memo,tags 순서로 작성해 주세요.")
            for row in reader:
                try:
                    if len(row) != len(CSV_COLUMNS):
                        raise PantryError("CSV 컬럼 수가 올바르지 않습니다.",
                                          "모든 행은 6개 컬럼이어야 합니다. 메모나 태그의 쉼표는 CSV 따옴표로 감싸 주세요.")
                    date, type, category, amount, memo, tags = row
                    category = category.strip()
                    if category not in categories:
                        raise PantryError("등록되지 않은 카테고리입니다.",
                                          "category list에서 확인한 이름을 이모지 없이 사용해 주세요.")
                    transactions.append(dict(
                        date=parse_date(date), type=parse_type(type), category=category,
                        amount=parse_amount(amount), memo=memo, tags=parse_tags(tags),
                    ))
                except PantryError as exc:
                    raise PantryError(
                        f"CSV {reader.line_num}번째 줄: {exc} 전체 가져오기를 취소합니다.", exc.hint,
                    ) from exc
    except UnicodeError as exc:
        raise PantryError("CSV를 UTF-8로 읽을 수 없습니다. 전체 가져오기를 취소합니다.",
                          "파일을 UTF-8 인코딩으로 저장한 뒤 다시 시도해 주세요.") from exc
    except csv.Error as exc:
        raise PantryError("CSV 형식이 올바르지 않습니다. 전체 가져오기를 취소합니다.",
                          "따옴표, 쉼표 구분과 각 필드의 길이를 확인해 주세요.") from exc
    return transactions


def write_csv(path: Path, transactions: Iterable[Transaction]) -> int:
    """같은 폴더의 임시 CSV를 완성한 뒤 교체하고 처리 건수를 반환한다."""
    count = 0
    try:
        with atomic_text_writer(path) as target:
            writer = csv.writer(target)
            writer.writerow(CSV_COLUMNS)
            for transaction in transactions:
                writer.writerow((transaction.date, transaction.type, transaction.category,
                                 transaction.amount, transaction.memo, ",".join(transaction.tags)))
                count += 1
    except (UnicodeError, csv.Error) as exc:
        raise PantryError("거래를 UTF-8 CSV로 기록할 수 없습니다.",
                          "메모와 태그의 문자열 형식을 확인해 주세요. 기존 출력 파일은 유지됩니다.") from exc
    return count
