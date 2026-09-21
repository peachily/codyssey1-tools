PRAGMA foreign_keys = ON;

-- 1. Trainer
INSERT INTO trainer (trainer_id, name, trainer_class) VALUES
(1, 'Soojeong', 'Champion'),
(2, 'Hyunsoo', 'Champion'),
(3, 'Gahui', 'Elite Four'),
(4, 'Daeyeong', 'Elite Four'),
(5, 'Wonmo', 'Gym Leader'),
(6, 'Changrae', 'Gym Leader'),
(7, 'Eunsu', 'Gym Leader'),
(8, 'Hyeonseo', 'Trainer'),
(9, 'Yeju', 'Trainer'),
(10, 'Donghyeon', 'Trainer');


-- 2. Pokemon
INSERT INTO pokemon
(pokemon_id, name, primary_type, secondary_type, base_hp, generation)
VALUES
(1, 'Bulbasaur', 'Grass', 'Poison', 45, 1),
(4, 'Charmander', 'Fire', NULL, 39, 1),
(7, 'Squirtle', 'Water', NULL, 44, 1),
(25, 'Pikachu', 'Electric', NULL, 35, 1),
(37, 'Vulpix', 'Fire', NULL, 38, 1),
(39, 'Jigglypuff', 'Normal', 'Fairy', 115, 1),
(43, 'Oddish', 'Grass', 'Poison', 45, 1),
(52, 'Meowth', 'Normal', NULL, 40, 1),
(54, 'Psyduck', 'Water', NULL, 50, 1),
(79, 'Slowpoke', 'Water', 'Psychic', 90, 1),
(94, 'Gengar', 'Ghost', 'Poison', 60, 1),
(104, 'Cubone', 'Ground', NULL, 50, 1),
(129, 'Magikarp', 'Water', NULL, 20, 1),
(132, 'Ditto', 'Normal', NULL, 48, 1),
(133, 'Eevee', 'Normal', NULL, 55, 1),
(143, 'Snorlax', 'Normal', NULL, 160, 1),
(147, 'Dratini', 'Dragon', NULL, 41, 1),
(149, 'Dragonite', 'Dragon', 'Flying', 91, 1),
(152, 'Chikorita', 'Grass', NULL, 45, 2),
(202, 'Wobbuffet', 'Psychic', NULL, 190, 2);


-- 3. Owned Pokemon
INSERT INTO owned_pokemon
(owned_id, trainer_id, pokemon_id, level)
VALUES
-- Soojeong
(1, 1, 132, 100),  -- Ditto
(2, 1, 133, 82),   -- Eevee
(3, 1, 94, 88),    -- Gengar

-- Hyunsoo
(4, 2, 39, 100),   -- Jigglypuff
(5, 2, 149, 94),   -- Dragonite
(6, 2, 143, 89),   -- Snorlax

-- Gahui
(7, 3, 25, 86),    -- Pikachu
(8, 3, 37, 71),    -- Vulpix
(9, 3, 54, 63),    -- Psyduck

-- Daeyeong
(10, 4, 104, 79),  -- Cubone
(11, 4, 94, 83),   -- Gengar
(12, 4, 147, 68),  -- Dratini

-- Wonmo
(13, 5, 7, 65),    -- Squirtle
(14, 5, 54, 52),   -- Psyduck
(15, 5, 129, 21),  -- Magikarp

-- Changrae
(16, 6, 1, 69),    -- Bulbasaur
(17, 6, 43, 47),   -- Oddish
(18, 6, 152, 61),  -- Chikorita

-- Eunsu
(19, 7, 79, 64),   -- Slowpoke
(20, 7, 202, 77),  -- Wobbuffet
(21, 7, 143, 81),  -- Snorlax

-- Hyeonseo
(22, 8, 147, 73),  -- Dratini
(23, 8, 52, 44),   -- Meowth
(24, 8, 4, 59),    -- Charmander

-- Yeju
(25, 9, 37, 66),   -- Vulpix
(26, 9, 7, 58),    -- Squirtle
(27, 9, 1, 55),    -- Bulbasaur

-- Donghyeon
(28, 10, 4, 67),   -- Charmander
(29, 10, 43, 42),  -- Oddish
(30, 10, 129, 27); -- Magikarp


-- 4. Battle
INSERT INTO battle
(battle_id, winner_trainer_id, loser_trainer_id, battle_date)
VALUES
(1, 1, 3, '2026-03-05'),
(2, 2, 5, '2026-03-12'),
(3, 4, 6, '2026-03-21'),
(4, 1, 10, '2026-04-03'),
(5, 3, 8, '2026-04-15'),
(6, 2, 4, '2026-04-28'),
(7, 7, 9, '2026-05-07'),
(8, 5, 10, '2026-05-19'),
(9, 1, 6, '2026-06-02'),
(10, 8, 9, '2026-06-14'),
(11, 2, 3, '2026-06-27'),
(12, 4, 5, '2026-07-08'),
(13, 7, 10, '2026-07-20'),
(14, 1, 4, '2026-08-01'),
(15, 2, 7, '2026-08-11'),
(16, 3, 6, '2026-08-22'),
(17, 8, 5, '2026-09-01'),
(18, 1, 2, '2026-09-07'),
(19, 2, 1, '2026-09-12'),
(20, 9, 10, '2026-09-16');