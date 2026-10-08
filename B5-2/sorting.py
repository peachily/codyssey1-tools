from collections.abc import Callable, Iterable
from typing import TypeVar

T = TypeVar("T")


def merge_sort(values: Iterable[T], key: Callable = lambda value: value) -> list[T]:
    """입력을 보존하는 안정 병합 정렬. 평균·최악 O(N log N)."""
    items = list(values)
    if len(items) < 2:
        return items
    middle = len(items) // 2
    left = merge_sort(items[:middle], key)
    right = merge_sort(items[middle:], key)
    result = []
    i = j = 0
    while i < len(left) and j < len(right):
        if key(left[i]) <= key(right[j]):
            result.append(left[i])
            i += 1
        else:
            result.append(right[j])
            j += 1
    result.extend(left[i:])
    result.extend(right[j:])
    return result
