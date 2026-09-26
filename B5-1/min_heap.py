class MinHeap:
    """(expire_at, key) 형태의 데이터를 관리하는 최소 힙"""

    def __init__(self):
        self.heap = []

    def push(self, item):
        """새 요소를 힙에 추가한다."""
        self.heap.append(item)
        self._heapify_up(len(self.heap) - 1)

    def pop(self):
        """가장 작은 요소를 제거하고 반환한다."""
        if self.size() == 0:
            return None

        if self.size() == 1:
            return self.heap.pop()

        root = self.heap[0]

        # 마지막 요소를 루트로 이동한 뒤 힙 구조를 복구한다.
        self.heap[0] = self.heap.pop()
        self._heapify_down(0)

        return root

    def peek(self):
        """가장 작은 요소를 제거하지 않고 반환한다."""
        if self.size() == 0:
            return None

        return self.heap[0]

    def size(self):
        """현재 힙에 저장된 요소 개수를 반환한다."""
        return len(self.heap)

    def _heapify_up(self, index):
        """새로 삽입된 요소를 위로 이동시키며 최소 힙을 유지한다."""
        while index > 0:
            parent_index = (index - 1) // 2

            if self.heap[parent_index][0] <= self.heap[index][0]:
                break

            self.heap[parent_index], self.heap[index] = (
                self.heap[index],
                self.heap[parent_index]
            )

            index = parent_index

    def _heapify_down(self, index):
        """루트에서 아래로 이동시키며 최소 힙을 유지한다."""
        heap_size = self.size()

        while True:
            left_index = 2 * index + 1
            right_index = 2 * index + 2
            smallest = index

            if (
                left_index < heap_size
                and self.heap[left_index][0] < self.heap[smallest][0]
            ):
                smallest = left_index

            if (
                right_index < heap_size
                and self.heap[right_index][0] < self.heap[smallest][0]
            ):
                smallest = right_index

            if smallest == index:
                break

            self.heap[index], self.heap[smallest] = (
                self.heap[smallest],
                self.heap[index]
            )

            index = smallest


if __name__ == "__main__":
    heap = MinHeap()

    print("=== push 테스트 ===")

    heap.push((30, "name"))
    heap.push((10, "job"))
    heap.push((50, "age"))
    heap.push((20, "peachily"))

    print("heap:", heap.heap)
    print("size:", heap.size())


    print("\n=== peek 테스트 ===")

    print("가장 빠른 만료:", heap.peek())
    print("peek 후 size:", heap.size())


    print("\n=== pop 테스트 ===")

    print("pop:", heap.pop())
    print("다음 만료:", heap.peek())
    print("size:", heap.size())


    print("\n=== 전체 만료 순서 테스트 ===")

    while heap.size() > 0:
        print(heap.pop())

    print("size:", heap.size())


    print("\n=== 빈 힙 테스트 ===")

    print("peek:", heap.peek())
    print("pop:", heap.pop())