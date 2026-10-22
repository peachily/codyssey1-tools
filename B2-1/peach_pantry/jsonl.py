"""도메인 모델과 독립적인 JSONL 순차 읽기와 원자적 저장."""

import json
from pathlib import Path
from typing import Iterable, Iterator

from .errors import PantryError
from .file_io import atomic_text_writer


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
    """같은 디렉터리의 임시 파일을 완성한 뒤 원본을 교체한다."""
    with atomic_text_writer(path) as target:
        for record in records:
            target.write(json.dumps(record, ensure_ascii=False, allow_nan=False) + "\n")
