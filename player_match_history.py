"""This module retrieves account ids from the table accounts and then retrieves their respective match history to store in table matches.
"""

# noinspection PyUnresolvedReferences
import urllib.request
import urllib.parse
import json
import time
from info import *
import database
from connection import connect
from typing import List
import threading


class PlayerMatchCombo:
    def __init__(self, match, player, player_slot, hero_id):
        self.match = match
        self.player = player
        self.player_slot = player_slot
        self.hero_id = hero_id


class IDRetriever:
    """Thread-safe class to retrieve unchecked player account_ids from the database.
    """
    lock = threading.Lock()

    def get_ids(self, n: int) -> int:  # Does this generator need to be here? I think just get() will suffice, although idk.
        """Generator to yield an unchecked id.
        Args:
            n: How many ids to yield.
        Yields:
            Yields an unchecked account_id.
        """
        i = 0

        while i < n:
            yield self.get_match()
            i += 1

    def get_match(self) -> int:
        """Get an unchecked account_id.
        Returns:
            Returns an account id that hasn't been processed before and marks it as processed.
        """
        with self.lock:
            conn, cur = database.get()

            cur.execute('SELECT id from accounts WHERE checked = 0 LIMIT 1')

            id_ = None
            for x in cur:
                id_ = x[0]

            cur.execute('UPDATE Accounts SET checked=1 WHERE id=?', (id_,))
            conn.commit()
            conn.close()

            return id_


def save_to_disk(matches: List[dict], players: List[PlayerMatchCombo], account_id: int):
    """Saves the set of matches to the database.

    Args:
        matches: The list of MATCH dictionaries. The dictionaries adhere to the JSON structure.
        players: The list of players and the match id they've played.
        account_id: The account id that was used to pull match history from.
    """
    conn, cur = database.get()

    for x in matches:
        cur.execute('INSERT OR IGNORE INTO matches VALUES (?,?,?,?,?)', (x["match_id"], x["match_seq_num"], x["start_time"], x["lobby_type"], account_id))
        cur.execute('UPDATE Accounts SET checked=1 WHERE id=?', (account_id,))

    for x in players:
        cur.execute('INSERT OR IGNORE INTO player_match VALUES (?,?,?,?)', (x.player, x.match, x.player_slot, x.hero_id))

    conn.commit()
    conn.close()


def get_last_matchid(data: dict) -> int:
    print(len(data["result"]["matches"]) - 1)
    return data["result"]["matches"][len(data["result"]["matches"]) - 1]["match_id"]


def generate_params(last_requested_match: int, id_: int, api_key: str) -> str:
    """Generates the GET parameters for the get_match_history request.

        Args:
            last_requested_match: last_requested_match field of JSON return.
            id_: account_id
            api_key: api key to use.
    """
    if last_requested_match is not None:
        params = urllib.parse.urlencode({'key': STEAM_WEBAPI_KEY, 'start_at_match_id': last_requested_match - 1, 'account_id': id_, 'key': api_key})
    else:
        params = urllib.parse.urlencode({'key': STEAM_WEBAPI_KEY, 'account_id': id_, 'key': api_key})

    return params


def get_match_batch(last_requested_match: int, id_: int, api_key: str) -> List[dict]:
    """Gets the batch of 100(or less) matches from the 500(or less) sequence returned by the get_match_history request.

    Args:
        last_requested_match: last_requested_match variable of the GetMatchHistory request.
        id_: account id
        api_key: api key to use

    Returns:
        A batch of 100 matches as per id_ and last_requested_match.
    """
    params = generate_params(last_requested_match, id_, api_key)

    response = connect(GET_MATCH_HISTORY_URL, params)
    while response is None:
        time.sleep(10)
        response = connect(GET_MATCH_HISTORY_URL, params)

    return response


def extract_players(matches: List[dict]) -> List[PlayerMatchCombo]:
    combos = list()

    for match in matches:
        match_id = match["match_id"]

        for player in match["players"]:
            if "account_id" in player:
                combos.append(PlayerMatchCombo(match_id, player["account_id"], player["player_slot"], player["hero_id"]))
            else:
                combos.append(PlayerMatchCombo(match_id, 0, player["player_slot"], player["hero_id"]))

    return combos


def get_matches(id_: int, api_key: str) -> List[dict]:
    """Retrieves the last 500(or less) matches of a player.

    Args:
        id_: account_id
        api_key: the api key to use
    Return:
        The last 500(or less) matches.
    """
    last_requested_match = None
    matches = list()

    while True:
        time.sleep(1)

        response = get_match_batch(last_requested_match, id_, api_key)
        data = json.loads(response)
        matches.extend(data["result"]["matches"])
        last_requested_match = get_last_matchid(data)

        if data["result"]["results_remaining"] == 0 or data["result"]["num_results"] == 0:
            break

    return matches


def collect(api_key: str):
    id_retriever = IDRetriever()

    try:
        for id_ in id_retriever.get_ids(1000):
            matches = get_matches(id_, api_key)
            players = extract_players(matches)

            save_to_disk(matches, players, id_)

    except KeyboardInterrupt:
        save_to_disk(matches, id_)


def main():
    for i in range(1, 10):
        key = get_key()
        t = threading.Thread(target=collect, args=(key, ), name=key)
        t.start()
        time.sleep(1 / 6)  # So requests are out of sync.

if __name__ == "__main__":
    main()
