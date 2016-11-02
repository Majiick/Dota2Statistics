import database

# fields = ("radiant_win", "duration", "pre_game_duration", "start_time", "match_id", "match_seq_num", "tower_status_radiant", "tower_status_dire", "cluster", "first_blood_time", "lobby_type", "human_players",
#               "leagueid", "positive_votes", "negative_votes", "game_mode", "flags", "engine", "radiant_score", "dire_score", "player_id", "day")
break_time_hours = 8

fields = ("match_id", "match_seq_num", "start_time", "lobby_type", "originally_extracted_from_acc_match_history", "checked", "day")

fieldPositions = dict()
for k, f in enumerate(fields):
    fieldPositions[f] = k

conn, cur = database.get()
cur.execute('''
            SELECT * FROM matches
            ''')

player_matches = dict()  # Dict[player_id] -> list of their matches

for match in cur:
    id_ = match[fieldPositions["originally_extracted_from_acc_match_history"]]

    if id_ not in player_matches:
        player_matches[id_] = list()

    player_matches[id_].append(match)

# Add days
for p, matches in player_matches.items():
    last_match_time = 0
    day = 0

    for match in matches:
        if match[fieldPositions["start_time"]] > last_match_time + (break_time_hours * 60 * 60):
            last_match_time = match[fieldPositions["start_time"]]
            day += 1

        match = match + (day,)

    print(day)

