from commit import Commit


class InvertedIndex:
    """키워드·작성자별 생성 순서 커밋 ID 목록."""

    def __init__(self) -> None:
        self.keywords: dict[str, list[str]] = {}
        self.authors: dict[str, list[str]] = {}

    def add(self, commit: Commit) -> None:
        """중복 키워드를 제거한 뒤 두 색인 갱신."""
        for keyword in set(commit.message.lower().split()):
            self.keywords.setdefault(keyword, []).append(commit.hash)
        self.authors.setdefault(commit.author, []).append(commit.hash)

    def search_keyword(self, keyword: str) -> list[str]:
        return list(self.keywords.get(keyword.lower(), []))

    def search_author(self, author: str) -> list[str]:
        return list(self.authors.get(author, []))
