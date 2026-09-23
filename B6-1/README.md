# Pokémon Trainer Database

![데이터베이스 관계도](results/db.png)

## 데이터베이스 구성

- `trainer`: 트레이너 정보
- `pokemon`: 포켓몬 기본 정보
- `owned_pokemon`: 트레이너별 보유 포켓몬과 레벨
- `battle`: 트레이너 간 배틀 기록

- `PRIMARY KEY`: 각 데이터를 구분하는 고유한 값
- `FOREIGN KEY`: 서로 다른 테이블의 데이터를 연결하는 참조 값
- `NOT NULL`: 반드시 값이 존재하도록 설정하는 제약조건
- `UNIQUE`: 중복된 값이 저장되지 않도록 설정하는 제약조건
- `1:N 관계`: 하나의 데이터가 여러 데이터와 연결되는 관계

![테이블 생성 결과](results/00_tables.png)

→ `trainer`, `pokemon`, `owned_pokemon`, `battle` 테이블 생성  
→ PK와 FK를 이용하여 테이블 간 관계 설정


## SELECT / WHERE / ORDER BY / LIMIT

- `SELECT`: 테이블에서 필요한 데이터 조회

![SELECT 실행 결과](results/01_select_all.png)

→ `trainer` 테이블에 저장된 전체 트레이너 데이터 조회

- `WHERE`: 조건에 맞는 데이터만 조회

![WHERE 실행 결과](results/02_where.png)

→ `WHERE`를 사용하여 주 타입이 `Water`인 포켓몬만 조회

- `ORDER BY`: 지정한 값을 기준으로 조회 결과 정렬
- `DESC`: 큰 값부터 내림차순 정렬

![ORDER BY 실행 결과](results/03_order_by.png)

→ `ORDER BY`와 `DESC`를 사용하여 기본 HP가 높은 포켓몬부터 정렬

- `LIMIT`: 조회할 데이터의 개수 제한

![LIMIT 실행 결과](results/04_limit.png)

→ 보유 포켓몬을 레벨이 높은 순서로 정렬하고 상위 5마리만 조회


## INNER JOIN / LEFT JOIN

- `JOIN`: 서로 다른 테이블의 관련 데이터를 연결하여 조회
- `INNER JOIN`: 양쪽 테이블에 연결되는 데이터가 존재하는 경우만 조회
- `ON`: 두 테이블을 연결할 기준 지정

![INNER JOIN 실행 결과](results/05_inner_join.png)

→ `trainer`와 `owned_pokemon`을 `trainer_id`로 연결하여 트레이너별 보유 포켓몬 정보 조회

- `INNER JOIN`: 여러 테이블을 연결하여 필요한 정보를 함께 조회

![INNER JOIN 실행 결과](results/06_inner_join.png)

→ `trainer`, `owned_pokemon`, `pokemon`을 연결하여 트레이너 이름, 포켓몬 이름, 레벨을 함께 조회

- `INNER JOIN`: 같은 테이블을 서로 다른 역할로 여러 번 연결 가능

![배틀 JOIN 실행 결과](results/07_battle_join.png)

→ `battle`과 `trainer`를 연결하여 ID로 저장된 승자와 패자를 실제 트레이너 이름으로 조회

- `LEFT JOIN`: 왼쪽 테이블의 데이터는 모두 유지하고 연결되는 오른쪽 데이터 조회

![LEFT JOIN 실행 결과](results/08_left_join.png)

→ 모든 트레이너를 기준으로 보유 포켓몬 정보를 연결하여 조회


## COUNT / AVG / SUM / GROUP BY

- `COUNT`: 데이터의 개수 계산
- `GROUP BY`: 같은 값을 가진 데이터를 그룹으로 묶어 집계

![COUNT 실행 결과](results/09_count.png)

→ 트레이너별로 데이터를 묶어 각 트레이너가 보유한 포켓몬 수 계산

- `AVG`: 데이터의 평균값 계산

![AVG 실행 결과](results/10_avg.png)

→ 트레이너별 보유 포켓몬의 평균 레벨 계산

- `SUM`: 데이터의 합계 계산

![SUM 실행 결과](results/11_sum.png)

→ 트레이너별 보유 포켓몬 레벨의 합계 계산


## 서브쿼리

- `Subquery`: 하나의 SQL문 내부에서 다른 SQL문의 결과를 다시 활용하는 방법

![서브쿼리 실행 결과](results/12_subquery.png)

→ 전체 보유 포켓몬의 평균 레벨을 서브쿼리로 계산  
→ 계산된 평균보다 레벨이 높은 포켓몬만 조회


## UPDATE / DELETE

- `UPDATE`: 기존에 저장된 데이터의 값 수정
- `SET`: 변경할 값 지정

![UPDATE 실행 결과](results/13_update.png)

→ Soojeong이 보유한 Eevee의 레벨을 `82 → 83`으로 변경  
→ 변경 후 데이터를 다시 조회하여 결과 확인

- `DELETE`: 조건에 맞는 기존 데이터 삭제

![DELETE 실행 결과](results/14_delete.png)

→ `battle_id = 20`인 배틀 기록 삭제  
→ 삭제 후 다시 조회하여 해당 데이터가 없는지 확인


## JOIN + 집계

- `JOIN + GROUP BY`: 여러 테이블을 연결한 뒤 특정 기준으로 데이터를 묶어 집계

![승리 횟수 조회 결과](results/15_win_count.png)

→ `trainer`와 `battle`을 연결하여 트레이너별 승리 횟수 계산  
→ 승리 횟수가 많은 순서로 정렬


## CREATE INDEX

- `INDEX`: 특정 열의 데이터를 빠르게 찾기 위한 색인
- `CREATE INDEX`: 지정한 열에 새로운 인덱스 생성

![INDEX 생성 결과](results/16_index.png)

→ 트레이너별 보유 포켓몬 조회와 JOIN에 사용하는 `owned_pokemon.trainer_id`에 인덱스 생성


## 파일 구성

```text
B6-1/
├── 01_schema.sql
├── 02_data.sql
├── 03_queries.sql
├── README.md
└── results/
```

- `01_schema.sql`: 테이블 및 제약조건 생성
- `02_data.sql`: 샘플 데이터 입력
- `03_queries.sql`: SQL 실습 쿼리
- `results/`: SQL 실행 결과
