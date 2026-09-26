class Node:
    """이중 연결 리스트의 노드"""

    def __init__(self, data):
        self.data = data
        self.prev = None
        self.next = None


class DoublyLinkedList:
    """head와 tail을 가지는 이중 연결 리스트"""

    def __init__(self):
        self.head = None
        self.tail = None
        self.length = 0

    def insert_front(self, data):
        """리스트 맨 앞에 새 노드를 삽입하고 노드를 반환한다."""
        new_node = Node(data)

        if self.head is None:
            self.head = new_node
            self.tail = new_node
        else:
            new_node.next = self.head
            self.head.prev = new_node
            self.head = new_node

        self.length += 1
        return new_node

    def insert_back(self, data):
        """리스트 맨 뒤에 새 노드를 삽입하고 노드를 반환한다."""
        new_node = Node(data)

        if self.tail is None:
            self.head = new_node
            self.tail = new_node
        else:
            new_node.prev = self.tail
            self.tail.next = new_node
            self.tail = new_node

        self.length += 1
        return new_node

    def remove_front(self):
        """맨 앞의 노드를 제거하고 그 데이터를 반환한다."""
        if self.head is None:
            return None

        removed_node = self.head

        if self.head == self.tail:
            self.head = None
            self.tail = None
        else:
            self.head = removed_node.next
            self.head.prev = None

        removed_node.prev = None
        removed_node.next = None

        self.length -= 1
        return removed_node.data

    def remove_back(self):
        """맨 뒤의 노드를 제거하고 그 데이터를 반환한다."""
        if self.tail is None:
            return None

        removed_node = self.tail

        if self.head == self.tail:
            self.head = None
            self.tail = None
        else:
            self.tail = removed_node.prev
            self.tail.next = None

        removed_node.prev = None
        removed_node.next = None

        self.length -= 1
        return removed_node.data

    def remove_node(self, node):
        """전달받은 특정 노드를 리스트에서 제거한다."""
        if node is None:
            return None

        if node == self.head:
            return self.remove_front()

        if node == self.tail:
            return self.remove_back()

        node.prev.next = node.next
        node.next.prev = node.prev

        data = node.data

        node.prev = None
        node.next = None

        self.length -= 1
        return data

    def move_to_front(self, node):
        """기존 노드를 리스트 맨 앞으로 이동한다."""
        if node is None or node == self.head:
            return

        if node == self.tail:
            self.tail = node.prev
            self.tail.next = None
        else:
            node.prev.next = node.next
            node.next.prev = node.prev

        node.prev = None
        node.next = self.head

        if self.head is not None:
            self.head.prev = node

        self.head = node

        if self.tail is None:
            self.tail = node

    def size(self):
        """현재 노드 개수를 반환한다."""
        return self.length


def print_list(linked_list):
    """테스트를 위해 리스트의 현재 상태를 출력한다."""
    current = linked_list.head

    while current is not None:
        print(current.data, end="")

        if current.next is not None:
            print(" <-> ", end="")

        current = current.next

    print()


if __name__ == "__main__":
    linked_list = DoublyLinkedList()

    print("=== insert_front 테스트 ===")

    linked_list.insert_front("Soojeong")
    linked_list.insert_front("peachily")

    print_list(linked_list)
    print("size:", linked_list.size())


    print("\n=== insert_back 테스트 ===")

    teacher_node = linked_list.insert_back("teacher")
    linked_list.insert_back("27")

    print_list(linked_list)
    print("size:", linked_list.size())


    print("\n=== move_to_front 테스트 ===")

    linked_list.move_to_front(teacher_node)

    print_list(linked_list)
    print("head:", linked_list.head.data)
    print("tail:", linked_list.tail.data)


    print("\n=== remove_front 테스트 ===")

    removed = linked_list.remove_front()

    print("삭제:", removed)
    print_list(linked_list)
    print("size:", linked_list.size())


    print("\n=== remove_back 테스트 ===")

    removed = linked_list.remove_back()

    print("삭제:", removed)
    print_list(linked_list)
    print("size:", linked_list.size())


    print("\n=== remove_node 테스트 ===")

    # 현재 리스트의 두 번째 노드를 직접 지정하여 삭제
    target_node = linked_list.head.next

    removed = linked_list.remove_node(target_node)

    print("삭제:", removed)
    print_list(linked_list)
    print("size:", linked_list.size())


    print("\n=== 빈 리스트 테스트 ===")

    linked_list.remove_front()

    print("remove_front:", linked_list.remove_front())
    print("remove_back:", linked_list.remove_back())
    print("size:", linked_list.size())