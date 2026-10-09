# Mini Redis

Python의 내장 `dict`를 사용하지 않고
해시맵, 이중 연결 리스트, 최소 힙을 직접 구현하여 만든 CLI 기반 Mini Redis

---

## 실행 방법
```
python3 main.py
```

`mini-redis>` 프롬프트에서 명령어를 입력합니다.
```shell
mini-redis> SET name Soojeong
OK
mini-redis> GET name
"Soojeong"
mini-redis> QUIT
```

- 명령어는 대소문자를 구분하지 않습니다.
- 공백이 포함된 값은 따옴표로 묶습니다. 예: `SET intro "hello world"`
- `EXIT` 또는 `QUIT`으로 종료하며, 종료 시 저장된 데이터는 초기화됩니다.

---

## 전체 구조
```vbnet
사용자
  │
  │ SET / GET / EXPIRE ...
  ▼
main.py
  │ 명령어 해석 및 결과 출력
  ▼
mini_redis.py
  │
  ├── hashmap.py              → Key-Value 저장 및 조회
  ├── doubly_linked_list.py   → LRU 사용 순서 관리
  └── min_heap.py             → TTL 만료 순서 관리
```

### 파일 구성

| 파일                      | 역할            | 주요 구현                |
| ----------------------- | ------------- | -------------------- |
| `main.py`               | CLI 인터페이스     | 명령어 파싱 및 오류 처리       |
| `mini_redis.py`         | Redis 기능 통합   | 저장·조회, 메모리, LRU, TTL |
| `hashmap.py`            | Key-Value 저장소 | 해시 함수, 체이닝, Resize   |
| `doubly_linked_list.py` | 양방향 연결 리스트    | 노드 삽입·삭제·이동          |
| `min_heap.py`           | 최소 힙          | 만료정보 삽입·조회·제거        |

---

## 명령어

### 기본 명령어

| 명령어      | 기능            | 예시                  |
| -------- | ------------- | ------------------- |
| `SET`    | 데이터 저장·덮어쓰기   | `SET name Soojeong` |
| `GET`    | 값 조회          | `GET name`          |
| `DEL`    | 데이터 삭제        | `DEL name`          |
| `EXISTS` | Key 존재 여부 확인  | `EXISTS name`       |
| `DBSIZE` | 저장된 Key 개수 확인 | `DBSIZE`            |
| `KEYS`   | 전체 Key 목록 확인  | `KEYS`              |

### 메모리 및 만료 관리

| 명령어                    | 기능             | 예시                        |
| ---------------------- | -------------- | ------------------------- |
| `CONFIG SET maxmemory` | 최대 메모리 설정(바이트) | `CONFIG SET maxmemory 25` |
| `INFO memory`          | 메모리 사용 정보 확인   | `INFO memory`             |
| `EXPIRE`               | 만료시간 설정(초)     | `EXPIRE name 10`          |
| `TTL`                  | 남은 유효시간 확인(초)  | `TTL name`                |

**주요 반환값**

| 반환값                 | 의미                   |
| ------------------- | -------------------- |
| `OK`                | 실행 성공                |
| `(nil)`             | 조회할 데이터 없음           |
| `(integer) 1` / `0` | 존재 여부 또는 처리 성공 여부    |
| `TTL -1`            | 만료시간이 설정되지 않음        |
| `TTL -2`            | Key가 없거나 만료됨         |
| `(error) ...`       | 잘못된 명령어·인자 또는 메모리 오류 |

---

## 핵심 구현

### 1. HashMap — 데이터 저장

- **해시 함수:** 문자열의 문자 코드를 이용해 버킷 인덱스 계산
- **체이닝:** 충돌 발생 시 버킷 내부의 연결 리스트에 데이터 저장
- **Resize:** Load Factor가 `0.75`를 초과하면 버킷 2배 확장 및 재해싱
- **시간 복잡도:** 저장·조회·삭제 평균 O(1)
```css
Bucket 0 → [Key A] ↔ [Key B]
Bucket 1 → [Key C]
Bucket 2 → ...
```

### 2. DoublyLinkedList — LRU 관리

각 노드가 이전(`prev`)·다음(`next`) 노드를 기억하는 이중 연결 리스트입니다.
```
HEAD                         TAIL
 ↓                             ↓
job  ↔  name  ↔  age  ↔  code
최근 사용                  오래된 사용
```

- `SET` 또는 성공한 `GET` 시 해당 Key를 맨 앞으로 이동
- 메모리 제한 초과 시 맨 뒤의 Key부터 제거
- 노드 참조를 이용해 이동·삭제 O(1)

**HashMap은 데이터를 찾고, 이중 연결 리스트는 사용 순서를 관리합니다.**

### 3. MinHeap — TTL 관리

가장 먼저 만료될 데이터를 빠르게 찾기 위한 최소 힙입니다.
```
          code (10초)
           /      \
   name (30초)   age (20초)
```

- 가장 빠른 만료시각을 루트(맨 위)에 유지
- `EXPIRE` 시 `(만료시각, Key)` 등록
- `peek()`으로 가장 빠른 만료정보 확인 — O(1)
- `push()`, `pop()`으로 삽입·제거 — O(log n)

실제로는 남은 초가 아닌 **만료시각**을 저장하며, 명령어 실행 시 만료된 데이터를 정리합니다.

### 4. 메모리 관리

Key와 Value의 UTF-8 바이트 수를 합산합니다.
```go
len(key.encode("utf-8")) + len(value.encode("utf-8"))
```

- `maxmemory 0`: 메모리 제한 없음
- 메모리 초과: LRU 순서에 따라 Key-Value 전체 제거
- 단일 데이터가 제한보다 큼: OOM 오류 반환

`INFO memory` 출력 항목:

| 항목             | 의미                     |
| -------------- | ---------------------- |
| `used_memory`  | 현재 사용 중인 데이터 바이트       |
| `maxmemory`    | 설정된 최대 바이트             |
| `evicted_keys` | LRU로 자동 제거된 Key의 누적 개수 |

`DEL`이나 TTL 만료로 삭제된 Key는 `evicted_keys`에 포함되지 않습니다.

---

## 동작 확인

각 예시는 `python3 main.py` 실행 후 입력합니다. 독립적인 결과를 확인하려면 예시마다 프로그램을 다시 실행합니다.

### 1. 기본 명령어
```sql
SET name Soojeong
SET job teacher
GET name
EXISTS job
DBSIZE
KEYS
DEL job
GET job
```

저장·조회·존재 여부·개수·목록·삭제 기능을 확인합니다.

### 2. TTL 만료
```css
SET code 1234
EXPIRE code 10
TTL code
```

10초 이상 기다린 뒤:
```css
GET code
TTL code
```

예상 결과:
```scss
(nil)
(integer) -2
```

### 3. LRU 및 메모리 관리

새로 실행한 프로그램에서 순서대로 입력합니다.
```sql
CONFIG SET maxmemory 25
SET name Soojeong
SET age 27
GET name
SET job teacher
GET age
GET name
INFO memory
```

| Key-Value           | 크기      |
| ------------------- | ------- |
| `name` + `Soojeong` | 12B     |
| `age` + `27`        | 5B      |
| `job` + `teacher`   | 10B     |
| **합계**              | **27B** |

`GET name`으로 사용 순서를 갱신했으므로, 25바이트 초과 시 가장 오래 사용하지 않은 `age`가 제거됩니다.

예상 결과:
```yaml
GET age  → (nil)
GET name → "Soojeong"

used_memory:22
maxmemory:25
evicted_keys:1
```

### 4. OOM 오류

`maxmemory`가 25바이트인 상태에서 입력합니다.
```sql
SET profile abcdefghijklmnopqrstuvwxyz
GET profile
```

단일 데이터가 제한을 초과하므로 OOM 오류가 발생하고 저장되지 않습니다.

---

## 테스트

전체 테스트:
```
python3 main.py test
```

자료구조별 테스트:
```
python3 hashmap.py
python3 doubly_linked_list.py
python3 min_heap.py
python3 mini_redis.py
```
