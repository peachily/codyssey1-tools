PRAGMA foreign_keys = ON;

-- ============================================
-- Pokemon Trainer Database - Core Queries
-- ============================================


-- ============================================
-- 1. 기본 SELECT
-- 전체 트레이너 조회
-- ============================================
SELECT *
FROM trainer;


-- ============================================
-- 2. 기본 SELECT - WHERE
-- 물 타입 포켓몬 조회
-- ============================================
SELECT pokemon_id, name, primary_type, base_hp
FROM pokemon
WHERE primary_type = 'Water';


-- ============================================
-- 3. 기본 SELECT - ORDER BY
-- 포켓몬을 HP가 높은 순서대로 조회
-- ============================================
SELECT name, primary_type, base_hp
FROM pokemon
ORDER BY base_hp DESC;


-- ============================================
-- 4. 기본 SELECT - LIMIT
-- 레벨이 가장 높은 보유 포켓몬 5마리 조회
-- ============================================
SELECT *
FROM owned_pokemon
ORDER BY level DESC
LIMIT 5;


-- ============================================
-- 5. INNER JOIN
-- 각 트레이너가 보유한 포켓몬 ID와 레벨 조회
-- ============================================
SELECT
    t.name AS trainer_name,
    op.pokemon_id,
    op.level
FROM trainer t
INNER JOIN owned_pokemon op
    ON t.trainer_id = op.trainer_id;


-- ============================================
-- 6. INNER JOIN
-- 트레이너 이름과 실제 포켓몬 이름을 함께 조회
-- ============================================
SELECT
    t.name AS trainer_name,
    p.name AS pokemon_name,
    op.level
FROM owned_pokemon op
INNER JOIN trainer t
    ON op.trainer_id = t.trainer_id
INNER JOIN pokemon p
    ON op.pokemon_id = p.pokemon_id
ORDER BY t.trainer_id;


-- ============================================
-- 7. INNER JOIN
-- 배틀 기록의 승자와 패자를 이름으로 조회
-- ============================================
SELECT
    b.battle_id,
    winner.name AS winner,
    loser.name AS loser,
    b.battle_date
FROM battle b
INNER JOIN trainer winner
    ON b.winner_trainer_id = winner.trainer_id
INNER JOIN trainer loser
    ON b.loser_trainer_id = loser.trainer_id
ORDER BY b.battle_date;


-- ============================================
-- 8. LEFT JOIN
-- 모든 트레이너와 보유 포켓몬 조회
-- 포켓몬이 없는 트레이너도 조회 가능
-- ============================================
SELECT
    t.name AS trainer_name,
    p.name AS pokemon_name,
    op.level
FROM trainer t
LEFT JOIN owned_pokemon op
    ON t.trainer_id = op.trainer_id
LEFT JOIN pokemon p
    ON op.pokemon_id = p.pokemon_id
ORDER BY t.trainer_id;


-- ============================================
-- 9. 집계 - COUNT + GROUP BY
-- 트레이너별 보유 포켓몬 수
-- ============================================
SELECT
    t.name AS trainer_name,
    COUNT(op.owned_id) AS pokemon_count
FROM trainer t
LEFT JOIN owned_pokemon op
    ON t.trainer_id = op.trainer_id
GROUP BY t.trainer_id, t.name;


-- ============================================
-- 10. 집계 - AVG + GROUP BY
-- 트레이너별 보유 포켓몬 평균 레벨
-- ============================================
SELECT
    t.name AS trainer_name,
    ROUND(AVG(op.level), 1) AS average_level
FROM trainer t
INNER JOIN owned_pokemon op
    ON t.trainer_id = op.trainer_id
GROUP BY t.trainer_id, t.name
ORDER BY average_level DESC;


-- ============================================
-- 11. 집계 - SUM + GROUP BY
-- 트레이너별 보유 포켓몬 레벨의 합
-- ============================================
SELECT
    t.name AS trainer_name,
    SUM(op.level) AS total_level
FROM trainer t
INNER JOIN owned_pokemon op
    ON t.trainer_id = op.trainer_id
GROUP BY t.trainer_id, t.name
ORDER BY total_level DESC;


-- ============================================
-- 12. 서브쿼리
-- 전체 평균 레벨보다 높은 보유 포켓몬 조회
-- ============================================
SELECT
    p.name AS pokemon_name,
    op.level
FROM owned_pokemon op
INNER JOIN pokemon p
    ON op.pokemon_id = p.pokemon_id
WHERE op.level > (
    SELECT AVG(level)
    FROM owned_pokemon
)
ORDER BY op.level DESC;


-- ============================================
-- 13. UPDATE
-- Soojeong의 Eevee 레벨을 82에서 83으로 변경
-- ============================================
UPDATE owned_pokemon
SET level = 83
WHERE trainer_id = 1
  AND pokemon_id = 133;


-- 변경 결과 확인
SELECT
    t.name AS trainer_name,
    p.name AS pokemon_name,
    op.level
FROM owned_pokemon op
INNER JOIN trainer t
    ON op.trainer_id = t.trainer_id
INNER JOIN pokemon p
    ON op.pokemon_id = p.pokemon_id
WHERE op.trainer_id = 1
  AND op.pokemon_id = 133;


-- ============================================
-- 14. DELETE
-- battle_id가 20인 배틀 기록 삭제
-- ============================================
DELETE FROM battle
WHERE battle_id = 20;


-- 삭제 결과 확인
SELECT *
FROM battle
WHERE battle_id = 20;


-- ============================================
-- 15. JOIN + 집계
-- 트레이너별 승리 횟수 조회
-- ============================================
SELECT
    t.name AS trainer_name,
    COUNT(b.battle_id) AS win_count
FROM trainer t
LEFT JOIN battle b
    ON t.trainer_id = b.winner_trainer_id
GROUP BY t.trainer_id, t.name
ORDER BY win_count DESC;


-- ============================================
-- INDEX
-- 트레이너 ID를 기준으로 보유 포켓몬을 조회하거나
-- JOIN할 때 검색 성능을 높이기 위한 인덱스
-- ============================================
CREATE INDEX idx_owned_pokemon_trainer
ON owned_pokemon(trainer_id);