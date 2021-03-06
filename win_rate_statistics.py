"""Need to refactor everything here.
"""

import database
import plotly
from plotly.graph_objs import Bar, Layout

# fields = ("radiant_win", "duration", "pre_game_duration", "start_time", "match_id", "match_seq_num", "tower_status_radiant", "tower_status_dire", "cluster", "first_blood_time", "lobby_type", "human_players",
#               "leagueid", "positive_votes", "negative_votes", "game_mode", "flags", "engine", "radiant_score", "dire_score", "player_id", "day")
break_time_hours = 8

fields = ("match_id", "match_seq_num", "start_time", "lobby_type", "originally_extracted_from_acc_match_history", "checked", "player_slot", "radiant_win", "day")

fieldPositions = dict(zip(fields, range(len(fields))))

conn, cur = database.get()
cur.execute("PRAGMA max_page_count = 2147483646")
cur.execute('''
             SELECT M.*, PM.player_slot, MD.radiant_win FROM matches M
             INNER JOIN player_match PM ON M.match_id=PM.match_id AND M.originally_extracted_from_acc_match_history=PM.player_id
             INNER JOIN matches_detailed MD ON M.match_id=MD.match_id
             WHERE MD.lobby_type IN (0, 2, 5, 6, 7) AND game_mode IN (1,2,3,4,5,12,13,14,16,22)
             ORDER BY M.start_time ASC
             ''')

print("Select statement done.")
# cur.execute('''
#             SELECT * FROM matches
#             ''')


player_matches = dict()  # Dict[player_id] -> list of their matches
average_matches = 0

for match in cur:
    id_ = match[fieldPositions["originally_extracted_from_acc_match_history"]]

    if id_ not in player_matches:
        player_matches[id_] = list()

    player_matches[id_].append(match)
    average_matches += 1
average_matches = average_matches / len(player_matches)
print(len(player_matches))


# Add days
for p, matches in player_matches.items():
    last_match_time = 0
    day = 0

    i = 0
    for match in matches:
        if match[fieldPositions["start_time"]] > last_match_time + (break_time_hours * 60 * 60):
            last_match_time = match[fieldPositions["start_time"]]
            day += 1

        match = match + (day,)
        player_matches[p][i] = match + (day, )  # Because for element in li returns a copy of the element, not the element itself.

        i += 1

    # print(day)


# https://gyazo.com/1217b1f13c9eb790dbbc261a534be989
def did_player_win(match, playerSlot):
    mask = 1 << 7
    player_on_dire = bool(playerSlot & mask)
    radiant_won = bool(match[fieldPositions["radiant_win"]])

    if player_on_dire == True and radiant_won == False:
        return True
    elif player_on_dire == True and radiant_won == True:
        return False
    elif player_on_dire == False and radiant_won == False:
        return False
    elif player_on_dire == False and radiant_won == True:
        return True

# Find win rate for each game of the day.
gameOfTheDay = dict()  # Dict[gameOfDay] -> List(bool). booleans ->WIN/LOSE
playx = dict()  # Dict[playerid] -> Dict[GameOfDay] -> GAMEOFDAY -> list(booleans). booleans -> WIN/LOSE

for p, matches in player_matches.items():
    gameOfDay = 0
    lastDay = 0
    i = 0

    if p not in playx:
        playx[p] = dict()

    for match in matches:
        day = match[fieldPositions["day"]]
        if i == 0:
            lastDay = day

        if lastDay != day:
            gameOfDay = 1
            lastDay = day
        else:
            gameOfDay += 1

        if gameOfDay not in playx[p]:
            playx[p][gameOfDay] = list()

        playx[p][gameOfDay].append(did_player_win(match, match[fieldPositions["player_slot"]]))

        # print(gameOfDay, day)

        i += 1

print("Players surveyed: ", len(playx))
print("Average games per player: ", average_matches)
for p, gameOfDay in playx.items():
    for day, matchBool in gameOfDay.items():  # matchBool -> List[booleans]. Bool = win or lose
        if day not in gameOfTheDay:
            gameOfTheDay[day] = list()

        gameOfTheDay[day].extend(matchBool)

plotlyRepresentation = dict()  # dict[day] -> average winrate
i = 0
firstDay = int()

for day, matches in gameOfTheDay.items():
    # print(len(matches), len([x for x in matches if x == 1]))
    print(day, sum(matches) / float(len(matches)))
    if day not in plotlyRepresentation:
        if i == 0:  # Ternary statement?
            firstDay = sum(matches) / float(len(matches))
        else:
            plotlyRepresentation[day] = firstDay - (sum(matches) / float(len(matches)))

    i += 1

t = [str(x) for x in plotlyRepresentation.keys()]
u = [str(x) for x in plotlyRepresentation.values()]

plotly.offline.plot({
    "data": [Bar(x=t[:-5], y=u[:-5])],
    "layout": Layout(title="hello world")
})