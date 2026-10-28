"""건수 제한이 없는 검색 결과를 임시 디스크에서 정렬한다."""
# 거래 받기 → 임시 DB에 넣기 → 최신순 정렬 → 한 건씩 전달 → 임시 DB 정리
# (거래가 많아져도 모든 데이터를 Python 메모리에 모아 정렬하지 않도록 임시 SQLite 데이터베이스를 사용
#  → 거래를 순차적으로 저장하고 SQL로 정렬한 뒤, 제너레이터를 통해 결과를 한 건씩 반환하도록 구현)

import json
from pathlib import Path
import sqlite3
from tempfile import TemporaryDirectory
from typing import Iterable, Iterator

from .errors import PantryError
from .models import Transaction


# transactioins: service.py 에서 검색 조건에 맞게 골라서 보내준 거래들
def latest_first(transactions: Iterable[Transaction]) -> Iterator[Transaction]:
    """전달받은 거래를 임시 SQLite에 저장하고 최신순으로 정렬하여 한 건씩 반환한다."""
    # Iterable[Transaction]: 거래를 하나씩 꺼낼 수 있는 데이터를 전달받는다는 뜻
    # Iterator[Transaction]: 거래를 하나씩 꺼낼 수 있는 반복자를 반환한다는 뜻
    with TemporaryDirectory(prefix="peach-pantry-search-") as directory:
    # 검색 결과를 정렬할 임시 폴더와 SQLite 데이터베이스 파일 만듦 -> with: 작업 끝나면 임시 폴더 자동 정리
        connection = None
        try:
            connection = sqlite3.connect(Path(directory) / "search.sqlite3")
            connection.execute("PRAGMA temp_store = FILE")
            connection.execute("PRAGMA cache_size = -1024")
            connection.execute("CREATE TABLE results (date TEXT, id TEXT, record TEXT)")
            for transaction in transactions:
                connection.execute(
                # 전달받은 거래를 하나씩 SQLite 테이블에 넣음 (?가 나중에 실제 값이 들어갈 자리)
                    "INSERT INTO results VALUES (?, ?, ?)",
                    (transaction.date, transaction.id,
                     json.dumps(transaction.to_record(), ensure_ascii=False)),
                )
            connection.commit()
            rows = connection.execute(
                "SELECT record FROM results ORDER BY date DESC, length(id) DESC, id DESC"
                # ORDER BY date DESC: 날짜가 최신인 것부터 정렬하라는 SQL 명령어
            )
            for (record,) in rows:
                yield Transaction.from_record(json.loads(record))
                # 정렬된 거래를 하나 전달하고 잠깐 멈췄다가, 다음 거래가 필요하면 이어서 전달
                # (yield: 함수의 실행 상태를 유지하면서 값을 하나씩 전달하는 제너레이터 문법)
                #  → 정렬된 거래를 리스트에 모두 담지 않고 한 건씩 반환하여 메모리 사용을 줄임
        except sqlite3.Error as exc:
            raise PantryError("검색 결과를 임시 파일에서 정렬할 수 없습니다.",
                              "임시 폴더의 접근 권한과 디스크 여유 공간을 확인해 주세요.") from exc
        finally:
            if connection is not None:
                connection.close()
                # SQLite 연결을 닫음. 임시 폴더도 with문이 끝나면 정리됨.
