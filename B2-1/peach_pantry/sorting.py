"""건수 제한이 없는 검색 결과를 임시 디스크에서 정렬한다."""

import json
from pathlib import Path
import sqlite3
from tempfile import TemporaryDirectory
from typing import Iterable, Iterator

from .errors import PantryError
from .models import Transaction


def latest_first(transactions: Iterable[Transaction]) -> Iterator[Transaction]:
    """JSONL을 한 건씩 읽어 정렬한다. 추가 디스크는 결과 건수에 비례한다."""
    with TemporaryDirectory(prefix="peach-pantry-search-") as directory:
        connection = None
        try:
            connection = sqlite3.connect(Path(directory) / "search.sqlite3")
            connection.execute("PRAGMA temp_store = FILE")
            connection.execute("PRAGMA cache_size = -1024")
            connection.execute("CREATE TABLE results (date TEXT, id TEXT, record TEXT)")
            for transaction in transactions:
                connection.execute(
                    "INSERT INTO results VALUES (?, ?, ?)",
                    (transaction.date, transaction.id,
                     json.dumps(transaction.to_record(), ensure_ascii=False)),
                )
            connection.commit()
            rows = connection.execute(
                "SELECT record FROM results ORDER BY date DESC, length(id) DESC, id DESC"
            )
            for (record,) in rows:
                yield Transaction.from_record(json.loads(record))
        except sqlite3.Error as exc:
            raise PantryError("검색 결과를 임시 파일에서 정렬할 수 없습니다.",
                              "임시 폴더의 접근 권한과 디스크 여유 공간을 확인해 주세요.") from exc
        finally:
            if connection is not None:
                connection.close()
