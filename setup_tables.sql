CREATE TABLE IF NOT EXISTS Accounts(
  id INTEGER PRIMARY KEY,
  checked BOOLEAN DEFAULT 0
);


CREATE TABLE IF NOT EXISTS matches(
  match_id INTEGER,
  match_seq_num INTEGER,
  start_time INTEGER NOT NULL,
  lobby_type INTEGER NOT NULL,
  originally_extracted_from_acc_match_history INTEGER, /* nice name tbh */

  checked BOOLEAN DEFAULT 0,

  PRIMARY KEY (match_id)
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
  /*season*/
  radiant_win BOOLEAN,
  duration INTEGER,
  pre_game_duration INTEGER,
  start_time INTEGER,
  match_id INTEGER,
  match_seq_num INTEGER NOT NULL,
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

CREATE TABLE IF NOT EXISTS player_match_detailed(
  account_id INTEGER DEFAULT -1,
  player_slot INTEGER,
  hero_id INTEGER,
  item_0 INTEGER,
  item_1 INTEGER,
  item_2 INTEGER,
  item_3 INTEGER,
  item_4 INTEGER,
  item_5 INTEGER,
  kills INTEGER,
  deaths INTEGER,
  assists INTEGER,
  leaver_status INTEGER DEFAULT -1,
  gold INTEGER,
  last_hits INTEGER,
  denies INTEGER,
  gold_per_min INTEGER,
  xp_per_min INTEGER,
  gold_spent INTEGER,
  hero_damage INTEGER,
  tower_damage INTEGER,
  hero_healing INTEGER,
  level INTEGER,
  match_id INTEGER,

  PRIMARY KEY (account_id, match_id),
  FOREIGN KEY(match_id) REFERENCES matches(match_id)
  /*ability upgrades*/
  /*additional_units*/
);

CREATE TABLE IF NOT EXISTS ability_upgrade(
  ability INTEGER,
  time INTEGER,
  level INTEGER,
  account_id INTEGER,
  match_id INTEGER,

  PRIMARY KEY(account_id, match_id),
  FOREIGN KEY(account_id) REFERENCES player_match_detailed(account_id),
  FOREIGN KEY(match_id) REFERENCES player_match_detailed(match_id)
);