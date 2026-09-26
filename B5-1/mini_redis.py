import time

from hashmap import HashMap
from doubly_linked_list import DoublyLinkedList
from min_heap import MinHeap


class RedisValue:
    """Redis에 저장되는 값과 해당 key의 LRU 노드를 함께 관리한다."""

    def __init__(self, value, lru_node):
        self.value = value
        self.lru_node = lru_node


class MiniRedis:
    """HashMap, 이중 연결 리스트, 최소 힙을 이용한 Mini Redis"""

    def __init__(self):
        # 실제 key-value 데이터 저장
        self.data = HashMap()

        # LRU 사용 순서 관리
        # head = 가장 최근 사용
        # tail = 가장 오래 사용하지 않음
        self.lru = DoublyLinkedList()

        # TTL 만료 시간 관리
        self.ttl_heap = MinHeap()

        # key별 현재 만료 시간 저장
        self.expire_times = HashMap()

        # 메모리 관리
        self.used_memory = 0
        self.maxmemory = 0
        self.evicted_keys = 0

    def _entry_size(self, key, value):
        """key와 value의 UTF-8 바이트 수를 계산한다."""
        return len(key.encode("utf-8")) + len(value.encode("utf-8"))

    def _delete_key(self, key):
        """데이터, LRU, TTL 정보에서 key를 삭제한다."""
        redis_value = self.data.get(key)

        if redis_value is None:
            return False

        # 사용 메모리 감소
        self.used_memory -= self._entry_size(
            key,
            redis_value.value
        )

        # LRU 리스트에서 제거
        self.lru.remove_node(redis_value.lru_node)

        # 실제 데이터 삭제
        self.data.remove(key)

        # TTL 정보 삭제
        if self.expire_times.contains(key):
            self.expire_times.remove(key)

        # ttl_heap은 lazy deletion 방식을 사용한다.
        # 힙에 남아 있는 오래된 정보는 나중에 무시한다.

        return True

    def _cleanup_expired(self):
        """최소 힙을 이용하여 이미 만료된 key를 정리한다."""
        now = time.time()

        while self.ttl_heap.size() > 0:
            expire_at, key = self.ttl_heap.peek()

            # 가장 빠른 만료 시간도 아직 지나지 않았다면 종료
            if expire_at > now:
                break

            self.ttl_heap.pop()

            current_expire = self.expire_times.get(key)

            # 이미 DEL되었거나 SET으로 TTL이 없어진 경우
            if current_expire is None:
                continue

            # EXPIRE가 다시 설정되어 예전 TTL 정보가 남은 경우
            if current_expire != expire_at:
                continue

            self._delete_key(key)

    def _is_expired(self, key):
        """특정 key가 만료되었는지 확인한다."""
        if not self.data.contains(key):
            return False

        expire_at = self.expire_times.get(key)

        if expire_at is None:
            return False

        if time.time() >= expire_at:
            self._delete_key(key)
            return True

        return False

    def _touch_lru(self, key):
        """사용된 key를 LRU 리스트의 맨 앞으로 이동한다."""
        redis_value = self.data.get(key)

        if redis_value is not None:
            self.lru.move_to_front(redis_value.lru_node)

    def _evict_if_needed(self):
        """메모리 제한을 초과하면 오래 사용하지 않은 key부터 삭제한다."""
        while (
            self.maxmemory > 0
            and self.used_memory > self.maxmemory
        ):
            if self.lru.tail is None:
                break

            # tail이 가장 오래 사용되지 않은 key
            key = self.lru.tail.data

            if self._delete_key(key):
                self.evicted_keys += 1

    def set(self, key, value):
        """SET key value"""
        self._cleanup_expired()

        new_size = self._entry_size(key, value)

        # 하나의 데이터 자체가 maxmemory보다 큰 경우 저장하지 않는다.
        if (
            self.maxmemory > 0
            and new_size > self.maxmemory
        ):
            return (
                "(error) OOM command not allowed "
                "when used_memory > 'maxmemory'"
            )

        # 기존 key를 덮어쓰는 경우
        if self.data.contains(key):
            self._delete_key(key)

        # 새로운 key는 가장 최근 사용 위치에 추가
        lru_node = self.lru.insert_front(key)

        redis_value = RedisValue(
            value,
            lru_node
        )

        self.data.put(key, redis_value)

        self.used_memory += new_size

        # SET으로 기존 TTL은 초기화된다.
        if self.expire_times.contains(key):
            self.expire_times.remove(key)

        # 메모리 제한 초과 시 LRU 제거
        self._evict_if_needed()

        return "OK"

    def get(self, key):
        """GET key"""
        self._cleanup_expired()

        if self._is_expired(key):
            return "(nil)"

        redis_value = self.data.get(key)

        if redis_value is None:
            return "(nil)"

        # 조회 성공 시에만 LRU 갱신
        self._touch_lru(key)

        return f'"{redis_value.value}"'

    def delete(self, key):
        """DEL key"""
        self._cleanup_expired()

        if self._is_expired(key):
            return "(integer) 0"

        if self._delete_key(key):
            return "(integer) 1"

        return "(integer) 0"

    def exists(self, key):
        """EXISTS key"""
        self._cleanup_expired()

        if self._is_expired(key):
            return "(integer) 0"

        if self.data.contains(key):
            return "(integer) 1"

        return "(integer) 0"

    def dbsize(self):
        """DBSIZE"""
        self._cleanup_expired()

        return f"(integer) {self.data.size()}"

    def keys(self):
        """KEYS"""
        self._cleanup_expired()

        keys = self.data.keys()

        if len(keys) == 0:
            return "(empty array)"

        result = []

        for i in range(len(keys)):
            result.append(
                f'{i + 1}. "{keys[i]}"'
            )

        return "\n".join(result)

    def config_set_maxmemory(self, bytes_value):
        """CONFIG SET maxmemory bytes"""
        if bytes_value < 0:
            return (
                "(error) ERR value is not an integer "
                "or out of range"
            )

        self.maxmemory = bytes_value

        # 기존 데이터가 새 제한을 초과하면 LRU 제거
        self._evict_if_needed()

        return "OK"

    def info_memory(self):
        """INFO memory"""
        self._cleanup_expired()

        return (
            f"used_memory:{self.used_memory}\n"
            f"maxmemory:{self.maxmemory}\n"
            f"evicted_keys:{self.evicted_keys}"
        )

    def expire(self, key, seconds):
        """EXPIRE key seconds"""
        self._cleanup_expired()

        if self._is_expired(key):
            return "(integer) 0"

        if not self.data.contains(key):
            return "(integer) 0"

        # 0 이하이면 즉시 만료
        if seconds <= 0:
            self._delete_key(key)
            return "(integer) 1"

        expire_at = time.time() + seconds

        self.expire_times.put(
            key,
            expire_at
        )

        self.ttl_heap.push(
            (expire_at, key)
        )

        return "(integer) 1"

    def ttl(self, key):
        """TTL key"""
        self._cleanup_expired()

        if self._is_expired(key):
            return "(integer) -2"

        if not self.data.contains(key):
            return "(integer) -2"

        expire_at = self.expire_times.get(key)

        # key는 있지만 TTL이 없음
        if expire_at is None:
            return "(integer) -1"

        remaining = int(
            expire_at - time.time()
        )

        if remaining < 0:
            self._delete_key(key)
            return "(integer) -2"

        return f"(integer) {remaining}"


def print_lru(redis):
    """테스트를 위해 현재 LRU 순서를 출력한다."""
    current = redis.lru.head

    while current is not None:
        print(current.data, end="")

        if current.next is not None:
            print(" <-> ", end="")

        current = current.next

    print()


if __name__ == "__main__":
    print("=== 기본 명령어 테스트 ===")

    redis = MiniRedis()

    print("SET name:", redis.set("name", "Soojeong"))
    print("SET age:", redis.set("age", "27"))
    print("SET job:", redis.set("job", "teacher"))

    print("GET name:", redis.get("name"))

    print(
        "EXISTS name:",
        redis.exists("name")
    )

    print(
        "EXISTS city:",
        redis.exists("city")
    )

    print(
        "DBSIZE:",
        redis.dbsize()
    )

    print("KEYS:")
    print(redis.keys())

    print(
        "DEL age:",
        redis.delete("age")
    )

    print(
        "DBSIZE:",
        redis.dbsize()
    )


    print("\n=== UTF-8 메모리 계산 테스트 ===")

    print(
        '"name" + "Soojeong":',
        redis._entry_size(
            "name",
            "Soojeong"
        ),
        "bytes"
    )

    print(
        '"이름" + "수정":',
        redis._entry_size(
            "이름",
            "수정"
        ),
        "bytes"
    )


    print("\n=== LRU + maxmemory 테스트 ===")

    lru_redis = MiniRedis()

    print(
        "CONFIG SET maxmemory 25:",
        lru_redis.config_set_maxmemory(25)
    )

    # name + Soojeong = 12 bytes
    print(
        "SET name:",
        lru_redis.set(
            "name",
            "Soojeong"
        )
    )

    # age + 27 = 5 bytes
    print(
        "SET age:",
        lru_redis.set(
            "age",
            "27"
        )
    )

    print("현재 LRU:")
    print_lru(lru_redis)

    # name을 조회하여 최근 사용으로 만든다.
    print(
        "GET name:",
        lru_redis.get("name")
    )

    print("GET 이후 LRU:")
    print_lru(lru_redis)

    # job + teacher = 10 bytes
    # 총 27 bytes가 되어 maxmemory 25 초과
    # 가장 오래 사용하지 않은 age가 제거되어야 한다.
    print(
        "SET job:",
        lru_redis.set(
            "job",
            "teacher"
        )
    )

    print("메모리 초과 처리 후 LRU:")
    print_lru(lru_redis)

    print(
        "GET age:",
        lru_redis.get("age")
    )

    print(
        "GET name:",
        lru_redis.get("name")
    )

    print(
        "GET job:",
        lru_redis.get("job")
    )

    print("INFO memory:")
    print(lru_redis.info_memory())


    print("\n=== 단일 엔트리 OOM 테스트 ===")

    # profile + special_education_teacher는
    # 25 bytes 제한보다 크기 때문에 저장되면 안 된다.
    print(
        lru_redis.set(
            "profile",
            "special_education_teacher"
        )
    )

    print(
        "GET profile:",
        lru_redis.get("profile")
    )

    print("INFO memory:")
    print(lru_redis.info_memory())


    print("\n=== TTL 기본 테스트 ===")

    ttl_redis = MiniRedis()

    print(
        "SET nickname:",
        ttl_redis.set(
            "nickname",
            "peachily"
        )
    )

    print(
        "TTL 설정 전:",
        ttl_redis.ttl("nickname")
    )

    print(
        "EXPIRE nickname 30:",
        ttl_redis.expire(
            "nickname",
            30
        )
    )

    print(
        "TTL 설정 후:",
        ttl_redis.ttl("nickname")
    )


    print("\n=== SET 시 TTL 초기화 테스트 ===")

    print(
        "SET nickname 다시:",
        ttl_redis.set(
            "nickname",
            "Soojeong"
        )
    )

    print(
        "TTL:",
        ttl_redis.ttl("nickname")
    )


    print("\n=== 실제 만료 테스트 ===")

    print(
        "SET temp:",
        ttl_redis.set(
            "temp",
            "hello"
        )
    )

    print(
        "EXPIRE temp 1:",
        ttl_redis.expire(
            "temp",
            1
        )
    )

    print("1초 후 만료를 확인합니다.")

    time.sleep(1.1)

    print(
        "GET temp:",
        ttl_redis.get("temp")
    )

    print(
        "TTL temp:",
        ttl_redis.ttl("temp")
    )


    print("\n=== EXPIRE 예외 테스트 ===")

    print(
        "없는 key:",
        ttl_redis.expire(
            "nothing",
            10
        )
    )

    ttl_redis.set(
        "instant",
        "bye"
    )

    print(
        "EXPIRE instant 0:",
        ttl_redis.expire(
            "instant",
            0
        )
    )

    print(
        "EXISTS instant:",
        ttl_redis.exists("instant")
    )


    print("\n=== DEL + TTL 테스트 ===")

    ttl_redis.set(
        "code",
        "1234"
    )

    ttl_redis.expire(
        "code",
        30
    )

    print(
        "DEL code:",
        ttl_redis.delete("code")
    )

    print(
        "TTL code:",
        ttl_redis.ttl("code")
    )