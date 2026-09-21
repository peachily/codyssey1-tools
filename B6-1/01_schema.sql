PRAGMA foreign_keys = ON;
/*
외래키(FK) 제약조건 검사 켜기: 존재하지 않는 데이터를 참조하려 하면 오류 발생
( owned_pokemon.trainer_id에 들어가는 값은 trainer.trainer_id에 존재해야 한다. )
*/

CREATE TABLE trainer (
    trainer_id INTEGER PRIMARY KEY, -- 프라이머리 키
    name TEXT NOT NULL UNIQUE, -- NOT NULL: 비워 둘 수 없다 / UNIQUE: 같은 이름 중복될 수 없다
    trainer_class TEXT NOT NULL
);

CREATE TABLE pokemon (
    pokemon_id INTEGER PRIMARY KEY,
    name TEXT NOT NULL UNIQUE,
    primary_type TEXT NOT NULL,
    secondary_type TEXT,
    base_hp INTEGER NOT NULL,
    generation INTEGER NOT NULL
);

CREATE TABLE owned_pokemon (
    owned_id INTEGER PRIMARY KEY,
    trainer_id INTEGER NOT NULL,
    pokemon_id INTEGER NOT NULL,
    level INTEGER NOT NULL,
    FOREIGN KEY (trainer_id) REFERENCES trainer(trainer_id), -- 외래키
    FOREIGN KEY (pokemon_id) REFERENCES pokemon(pokemon_id)
);

CREATE TABLE battle (
    battle_id INTEGER PRIMARY KEY,
    winner_trainer_id INTEGER NOT NULL,
    loser_trainer_id INTEGER NOT NULL,
    battle_date TEXT NOT NULL,
    FOREIGN KEY (winner_trainer_id) REFERENCES trainer(trainer_id),
    FOREIGN KEY (loser_trainer_id) REFERENCES trainer(trainer_id)
);