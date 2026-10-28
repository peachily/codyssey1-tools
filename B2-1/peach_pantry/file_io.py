"""JSONL과 CSV가 함께 사용하는 안전한 파일 교체 절차."""
# 먼저 임시 파일에 기록하고, 기록이 정상적으로 끝나면 os.replace()로 교체

from contextlib import contextmanager
import os
from pathlib import Path
import tempfile
from typing import Iterator, TextIO


@contextmanager
# with 문으로 안전한 파일 저장 과정을 관리. 임시 파일에 기록을 완료한 후 기존 파일을 교체하는 방식.
def atomic_text_writer(path: Path) -> Iterator[TextIO]:
    """성공한 쓰기만 반영하고 오류·중단 시 원본 보존과 임시 파일 정리를 한다.

    대상과 같은 디렉터리에 만들어 같은 파일시스템에서 os.replace()한다.
    yield 뒤 동기화까지 성공해야 원본을 교체한다.
    """
    # 파일을 열고, 내용을 쓰고, 문제가 없으면 기존 파일을 교체하고, 마지막에 정리
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
