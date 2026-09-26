# Mini Redis

Python의 내장 `dict`를 사용하지 않고
해시맵, 이중 연결 리스트, 최소 힙을 직접 구현하여 만든 CLI 기반 Mini Redis

---

## 전체 구조

```text
사용자
  │
  │ SET / GET / EXPIRE ...
  ▼
main.py
  │ 명령어 해석
  ▼
mini_redis.py
  │
  ├── hashmap.py              → Key-Value 데이터 저장
  ├── doubly_linked_list.py   → LRU 사용 순서 관리
  └── min_heap.py             → TTL 만료 순서 관리
```

---

## 파일 구성

### 1. `doubly_linked_list.py`

LRU 순서를 관리하기 위한 **이중 연결 리스트**

- `Node`: `prev`, `next`, `data` 저장
- `insert_front/back`: 앞/뒤에 노드 추가
- `remove_front/back/node`: 노드 삭제
- `move_to_front`: 사용된 노드를 맨 앞으로 이동
- 삽입·삭제·이동을 O(1)에 처리

### 2. `hashmap.py`

Python `dict` 대신 사용하는 **Key-Value 저장소**

- 직접 만든 해시 함수로 버킷 위치 계산
- `put`, `get`, `remove`, `contains`, `keys`, `size` 구현
- 충돌 발생 시 연결 리스트를 이용한 체이닝으로 해결
- Load Factor가 0.75를 초과하면 버킷을 2배로 확장

### 3. `min_heap.py`

TTL에서 가장 먼저 만료될 데이터를 찾기 위한 **최소 힙**

- `(expire_at, key)` 형태로 만료 정보 저장
- `push`, `pop`, `peek`, `size` 구현
- `_heapify_up`, `_heapify_down`으로 최소 힙 구조 유지
- 가장 빠른 만료 정보를 힙의 루트에서 확인

### 4. `mini_redis.py`

자료구조를 조합하여 실제 **Mini Redis 기능을 구현**

- `HashMap`: 실제 Key-Value 데이터 저장
- `DoublyLinkedList`: 최근 사용 순서(LRU) 관리
- `MinHeap`: TTL 만료 순서 관리
- `SET`, `GET`, `DEL`, `EXISTS`, `DBSIZE`, `KEYS` 구현
- `maxmemory` 초과 시 가장 오래 사용하지 않은 Key 제거
- `EXPIRE`, `TTL`을 통한 만료 시간 관리
- UTF-8 기준으로 `used_memory` 계산

### 5. `main.py`

사용자와 Mini Redis를 연결하는 **CLI 인터페이스**

- `mini-redis>` 프롬프트에서 명령어 입력
- 입력된 문자열을 명령어와 인자로 분리
- 알맞은 `MiniRedis` 메서드 호출
- 잘못된 명령어, 인자 개수, 정수 입력 등의 오류 처리
- `exit`, `quit`으로 종료

---

## 핵심 동작

### 데이터 저장

```text
SET key value
    ↓
HashMap에 데이터 저장
    ↓
LRU 리스트 맨 앞으로 등록
    ↓
used_memory 갱신
    ↓
메모리 초과 시 LRU 데이터 제거
```

### 데이터 조회

```text
GET key
    ↓
TTL 만료 여부 확인
    ↓
HashMap에서 값 조회
    ↓
조회 성공 시 LRU 맨 앞으로 이동
```

### TTL 관리

```text
EXPIRE key seconds
    ↓
만료 시간 계산
    ↓
MinHeap에 (expire_at, key) 저장
    ↓
만료 시간이 지나면 데이터 삭제
```