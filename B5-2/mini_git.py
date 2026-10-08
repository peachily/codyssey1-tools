from datetime import datetime, timezone

from commit import Commit
from graph import ancestors, shortest_path, topological_order
from index import InvertedIndex
from sorting import merge_sort


class MiniGit:
    """메모리 저장소, 브랜치 HEAD 및 세션 커밋 카운터."""

    def __init__(self) -> None:
        self.commits: dict[str, Commit] = {}
        self.branches: dict[str, str | None] = {}
        self.current_branch = ""
        self.user = ""
        self.index = InvertedIndex()
        self._counter = 0

    def require_initialized(self) -> None:
        if not self.current_branch:
            raise ValueError("Repository not initialized")

    @staticmethod
    def require_text(value: str) -> None:
        if not isinstance(value, str) or not value.strip():
            raise ValueError("Invalid args")

    def init(self, user: str) -> None:
        """저장소 초기화. 세션 고유 ID 카운터 유지."""
        self.require_text(user)
        self.commits = {}
        self.branches = {"main": None}
        self.current_branch = "main"
        self.user = user
        self.index = InvertedIndex()

    def branch(self, name: str) -> None:
        self.require_initialized()
        self.require_text(name)
        if name in self.branches:
            raise ValueError(f"Branch already exists: {name}")
        self.branches[name] = self.branches[self.current_branch]

    def switch(self, name: str) -> None:
        self.require_initialized()
        self.require_text(name)
        if name not in self.branches:
            raise ValueError(f"Unknown branch: {name}")
        self.current_branch = name

    def commit(self, message: str) -> Commit:
        """현재 HEAD를 부모로 새 커밋 생성 및 색인 갱신."""
        self.require_initialized()
        self.require_text(message)
        if self._counter >= 999999:
            raise ValueError("Commit ID limit reached")
        self._counter += 1
        head = self.branches[self.current_branch]
        commit = Commit(
            f"{self._counter:06d}", message, self.user,
            datetime.now(timezone.utc), [head] if head is not None else [],
        )
        self.commits[commit.hash] = commit
        self.branches[self.current_branch] = commit.hash
        self.index.add(commit)
        return commit

    def log(self, sort_by: str | None = None) -> list[Commit]:
        self.require_initialized()
        if sort_by is None:
            return [self.commits[commit_hash] for commit_hash in topological_order(self.commits)]
        if sort_by == "date":
            return merge_sort(self.commits.values(), key=lambda commit: (commit.timestamp, commit.hash))
        if sort_by == "author":
            return merge_sort(self.commits.values(), key=lambda commit: (commit.author, commit.hash))
        raise ValueError("Invalid args")

    def ancestors(self, commit_hash: str) -> list[str]:
        self.require_initialized()
        return ancestors(self.commits, commit_hash)

    def path(self, start: str, end: str) -> list[str]:
        self.require_initialized()
        return shortest_path(self.commits, start, end)

    def search(self, value: str, by_author: bool = False) -> list[Commit]:
        self.require_initialized()
        self.require_text(value)
        hashes = self.index.search_author(value) if by_author else self.index.search_keyword(value)
        return [self.commits[commit_hash] for commit_hash in hashes]
