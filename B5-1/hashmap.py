from doubly_linked_list import DoublyLinkedList


class HashEntry:
    """해시맵에 저장되는 key-value 한 쌍"""

    def __init__(self, key, value):
        self.key = key
        self.value = value


class HashMap:
    """체이닝 방식으로 충돌을 해결하는 해시맵"""

    def __init__(self, initial_capacity=8):
        self.capacity = initial_capacity
        self.count = 0

        # 버킷은 인덱스로 접근하기 위한 배열로 사용한다.
        # 각 버킷 내부에서는 이중 연결 리스트로 체이닝한다.
        self.buckets = [
            DoublyLinkedList() for _ in range(self.capacity)
        ]

    def _hash(self, key):
        """문자열 key를 버킷 인덱스로 변환한다."""
        hash_value = 0

        for char in key:
            hash_value = hash_value * 29 + ord(char)

        return hash_value % self.capacity

    def put(self, key, value):
        """key-value를 저장한다. 기존 key가 있으면 값을 덮어쓴다."""
        index = self._hash(key)
        bucket = self.buckets[index]

        current = bucket.head

        # 같은 key가 이미 있는지 확인한다.
        while current is not None:
            entry = current.data

            if entry.key == key:
                entry.value = value
                return

            current = current.next

        # 같은 key가 없다면 새 엔트리를 추가한다.
        bucket.insert_back(HashEntry(key, value))
        self.count += 1

        # 로드 팩터가 0.75를 초과하면 버킷을 2배 확장한다.
        if self.count / self.capacity > 0.75:
            self._resize()

    def get(self, key):
        """key에 해당하는 value를 반환한다. 없으면 None."""
        index = self._hash(key)
        bucket = self.buckets[index]

        current = bucket.head

        while current is not None:
            entry = current.data

            if entry.key == key:
                return entry.value

            current = current.next

        return None

    def remove(self, key):
        """key를 삭제하고 삭제한 value를 반환한다. 없으면 None."""
        index = self._hash(key)
        bucket = self.buckets[index]

        current = bucket.head

        while current is not None:
            entry = current.data

            if entry.key == key:
                value = entry.value

                bucket.remove_node(current)
                self.count -= 1

                return value

            current = current.next

        return None

    def contains(self, key):
        """key가 존재하면 True, 없으면 False."""
        index = self._hash(key)
        bucket = self.buckets[index]

        current = bucket.head

        while current is not None:
            entry = current.data

            if entry.key == key:
                return True

            current = current.next

        return False

    def keys(self):
        """저장된 모든 key를 리스트로 반환한다."""
        result = []

        for bucket in self.buckets:
            current = bucket.head

            while current is not None:
                entry = current.data
                result.append(entry.key)

                current = current.next

        return result

    def size(self):
        """현재 저장된 key 개수를 반환한다."""
        return self.count

    def _resize(self):
        """버킷을 2배로 확장하고 기존 데이터를 다시 배치한다."""
        old_buckets = self.buckets
        old_capacity = self.capacity

        self.capacity *= 2
        self.buckets = [
            DoublyLinkedList() for _ in range(self.capacity)
        ]

        self.count = 0

        for i in range(old_capacity):
            current = old_buckets[i].head

            while current is not None:
                entry = current.data
                self.put(entry.key, entry.value)

                current = current.next


if __name__ == "__main__":
    print("=== 기본 기능 테스트 ===")

    hashmap = HashMap()

    hashmap.put("name", "Soojeong")
    hashmap.put("age", "27")
    hashmap.put("job", "teacher")

    print("name:", hashmap.get("name"))
    print("age:", hashmap.get("age"))
    print("job 존재:", hashmap.contains("job"))
    print("city 존재:", hashmap.contains("city"))
    print("전체 key:", hashmap.keys())
    print("크기:", hashmap.size())

    hashmap.remove("age")

    print("age 삭제 후:", hashmap.get("age"))
    print("삭제 후 key:", hashmap.keys())
    print("삭제 후 크기:", hashmap.size())


    print("\n=== 같은 key 덮어쓰기 테스트 ===")

    hashmap.put("job", "special education teacher")

    print("변경된 job:", hashmap.get("job"))
    print("크기:", hashmap.size())


    print("\n=== 해시 충돌 / 체이닝 테스트 ===")

    collision_map = HashMap()

    # 현재 capacity가 8일 때 같은 버킷으로 가는 서로 다른 key를 찾는다.
    first_key = None
    second_key = None
    collision_index = None

    test_keys = [
        "peachily",
        "Soojeong",
        "teacher",
        "apple",
        "banana",
        "cat",
        "dog",
        "redis",
        "python",
        "school"
    ]

    for i in range(len(test_keys)):
        for j in range(i + 1, len(test_keys)):
            if collision_map._hash(test_keys[i]) == collision_map._hash(test_keys[j]):
                first_key = test_keys[i]
                second_key = test_keys[j]
                collision_index = collision_map._hash(test_keys[i])
                break

        if first_key is not None:
            break

    if first_key is not None:
        print(
            "충돌:",
            first_key,
            "와",
            second_key,
            "-> 버킷",
            collision_index
        )

        collision_map.put(first_key, "first")
        collision_map.put(second_key, "second")

        print(first_key, "조회:", collision_map.get(first_key))
        print(second_key, "조회:", collision_map.get(second_key))

        # 실제로 같은 버킷에 두 엔트리가 연결되어 있는지 확인
        bucket = collision_map.buckets[collision_index]
        current = bucket.head

        print("같은 버킷 내부:", end=" ")

        while current is not None:
            print(current.data.key, end=" ")
            current = current.next

        print()
    else:
        print("현재 테스트 key에서는 충돌을 찾지 못했습니다.")


    print("\n=== Resize 테스트 ===")

    resize_map = HashMap()

    print("초기 capacity:", resize_map.capacity)

    # capacity 8에서 6개까지는 load factor가 0.75이다.
    # 7번째 데이터가 들어가면 0.75를 초과하여 16으로 확장되어야 한다.
    resize_map.put("key1", "value1")
    resize_map.put("key2", "value2")
    resize_map.put("key3", "value3")
    resize_map.put("key4", "value4")
    resize_map.put("key5", "value5")
    resize_map.put("key6", "value6")

    print("6개 저장 후 capacity:", resize_map.capacity)
    print("6개 저장 후 size:", resize_map.size())

    resize_map.put("key7", "value7")

    print("7개 저장 후 capacity:", resize_map.capacity)
    print("7개 저장 후 size:", resize_map.size())

    # resize 이후에도 기존 데이터가 모두 남아 있는지 확인
    print("key1:", resize_map.get("key1"))
    print("key7:", resize_map.get("key7"))