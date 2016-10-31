CREATE TABLE IF NOT EXISTS Accounts(
  id INTEGER PRIMARY KEY,
  checked BOOLEAN DEFAULT FALSE
);

/*
CREATE TABLE IF NOT EXISTS matches(
  match_id INTEGER,
  player_id INTEGER,
  start_time INTEGER NOT NULL,
  lobby_type INTEGER NOT NULL,

  PRIMARY KEY (match_ID, player_ID)
);
*/

CREATE TABLE IF NOT EXISTS matches(
  match_id INTEGER,
  match_seq_num INTEGER,
  start_time INTEGER NOT NULL,
  lobby_type INTEGER NOT NULL,

  originally_extracted_from_acc_match_history INTEGER, /* nice name tbh */

  PRIMARY KEY (match_id, originally_extracted_from_acc_match_history)
);

CREATE TABLE IF NOT EXISTS player_match(
  player_id INTEGER,
  match_id INTEGER,
  player_slot INTEGER,
  hero_id INTEGER,

  PRIMARY KEY (player_id, match_id),
  FOREIGN KEY(match_id) REFERENCES matches(match_id)
);

CREATE TABLE IF NOT EXISTS matches_detailed(
  radiant_win BOOLEAN,
  duration INTEGER NOT NULL,
  pre_game_duration INTEGER NOT NULL,
  start_time INTEGER NOT NULL,
  match_id INTEGER,
  match_seq_num INTEGER NOT NULL UNIQUE,
  tower_status_radiant INTEGER,
  tower_status_dire INTEGER,
  cluster INTEGER,
  first_blood_time INTEGER,
  lobby_type INTEGER,
  human_players INTEGER,
  leagueid INTEGER,
  positive_votes INTEGER,
  negative_votes INTEGER,
  game_mode INTEGER,
  flags INTEGER,
  engine INTEGER,
  radiant_score INTEGER,
  dire_score INTEGER,

  PRIMARY KEY (match_id),
  FOREIGN KEY(match_id) REFERENCES matches(match_id)
);