from collections import deque

from commit import Commit
from sorting import merge_sort


def require_commit(commits: dict[str, Commit], commit_hash: str) -> None:
    if commit_hash not in commits:
        raise ValueError(f"Unknown commit: {commit_hash}")


def topological_order(commits: dict[str, Commit]) -> list[str]:
    """Kahn 알고리즘으로 모든 부모를 자식보다 먼저 반환."""
    hashes = merge_sort(commits)
    children = {commit_hash: [] for commit_hash in hashes}
    indegrees = {commit_hash: len(commits[commit_hash].parents) for commit_hash in hashes}
    for commit_hash in hashes:
        for parent in commits[commit_hash].parents:
            children[parent].append(commit_hash)
    queue = deque(commit_hash for commit_hash in hashes if indegrees[commit_hash] == 0)
    result = []
    while queue:
        current = queue.popleft()
        result.append(current)
        for child in children[current]:
            indegrees[child] -= 1
            if indegrees[child] == 0:
                queue.append(child)
    if len(result) != len(commits):
        raise ValueError("Cycle detected")
    return result


def ancestors(commits: dict[str, Commit], start: str) -> list[str]:
    """부모 방향 BFS 후 거리·hash 순으로 조상 반환."""
    require_commit(commits, start)
    distances = {start: 0}
    visited = {start}
    queue = deque([start])
    while queue:
        current = queue.popleft()
        for parent in commits[current].parents:
            if parent not in visited:
                visited.add(parent)
                distances[parent] = distances[current] + 1
                queue.append(parent)
    return merge_sort(
        (commit_hash for commit_hash in distances if commit_hash != start),
        key=lambda commit_hash: (distances[commit_hash], commit_hash),
    )


def shortest_path(commits: dict[str, Commit], start: str, end: str) -> list[str]:
    """무방향 BFS 거리와 탐욕 선택으로 사전순 최소 최단 경로 반환."""
    require_commit(commits, start)
    require_commit(commits, end)
    neighbors = {commit_hash: [] for commit_hash in commits}
    for commit_hash, commit in commits.items():
        for parent in commit.parents:
            neighbors[commit_hash].append(parent)
            neighbors[parent].append(commit_hash)
    distances = {end: 0}
    queue = deque([end])
    while queue:
        current = queue.popleft()
        for neighbor in neighbors[current]:
            if neighbor not in distances:
                distances[neighbor] = distances[current] + 1
                queue.append(neighbor)
    if start not in distances:
        return []
    path = [start]
    while path[-1] != end:
        current = path[-1]
        next_hash = min(
            neighbor for neighbor in neighbors[current]
            if distances.get(neighbor) == distances[current] - 1
        )
        path.append(next_hash)
    return path
