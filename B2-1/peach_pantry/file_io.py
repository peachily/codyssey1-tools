"""JSONL과 CSV가 함께 사용하는 안전한 파일 교체 절차."""

from contextlib import contextmanager
import os
from pathlib import Path
import tempfile
from typing import Iterator, TextIO


@contextmanager
def atomic_text_writer(path: Path) -> Iterator[TextIO]:
    """성공한 쓰기만 반영하고 오류·중단 시 원본 보존과 임시 파일 정리를 한다.

    대상과 같은 디렉터리에 만들어 같은 파일시스템에서 os.replace()한다.
    yield 뒤 동기화까지 성공해야 원본을 교체한다.
    """
    temporary_path = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="w", encoding="utf-8", newline="", dir=path.parent,
            prefix=f".{path.name}.", suffix=".tmp", delete=False,
        ) as target:
            temporary_path = Path(target.name)
            yield target
            target.flush()
            os.fsync(target.fileno())
        os.replace(temporary_path, path)
    finally:
        if temporary_path is not None:
            temporary_path.unlink(missing_ok=True)
