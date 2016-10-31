"""This module retrieves account ids from the table accounts and then retrieves their respective match history to store in table matches.

TODO:
    Turn IDRetriever into a Generator.
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


class IDRetriever:
    """Thread-safe class to retrieve unchecked player account_ids from the database.
    """
    lock = threading.Lock()

    def get(self):
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


def save_to_disk(data: List[dict], account_id: int):
    """Saves the set of matches to the database.

    Args:
        data: The list of MATCH dictionaries. The dictionaries adhere to the JSON structure.
        account_id: The account id that was used to pull match history from.
    """
    conn, cur = database.get()

    for x in data:
        cur.execute('INSERT OR IGNORE INTO matches VALUES (?,?,?,?,?)', (x["match_id"], x["match_seq_num"], x["start_time"], x["lobby_type"], account_id))
        cur.execute('UPDATE Accounts SET checked=1 WHERE id=?', (account_id,))

    conn.commit()
    conn.close()


def get_last_matchid(data: dict):
    print(len(data["result"]["matches"]) - 1)
    return data["result"]["matches"][len(data["result"]["matches"]) - 1]["match_id"]


def generate_params(last_requested_match: int, id_: int):
    """Generates the GET parameters for the get_match_history request.

        Args:
            last_requested_match: last_requested_match field of JSON return.
            id_: account_id
    """
    if last_requested_match is not None:
        params = urllib.parse.urlencode(
            {'key': STEAM_WEBAPI_KEY, 'start_at_match_id': last_requested_match - 1, 'account_id': id_})
    else:
        params = urllib.parse.urlencode({'key': STEAM_WEBAPI_KEY, 'account_id': id_})

    return params


def get_match_batch(last_requested_match: int, id_: int):
    """Gets the batch of 100(or less) matches from the 500(or less) sequence returned by the get_match_history request.
    """
    params = generate_params(last_requested_match, id_)

    response = connect(GET_MATCH_HISTORY_URL, params)
    while response is None:
        time.sleep(10)
        response = connect(GET_MATCH_HISTORY_URL, params)

    return response


def get_matches(id_: int) -> List[dict]:
    """Retrieves the last 500(or less) matches of a player.

    Args:
        id_: account_id
    Return:
        The last 500(or less) matches.
    """
    last_requested_match = None
    matches = list()

    while True:
        time.sleep(1)

        response = get_match_batch(last_requested_match, id_)
        data = json.loads(response)
        matches.extend(data["result"]["matches"])
        last_requested_match = get_last_matchid(data)

        if data["result"]["results_remaining"] == 0 or data["result"]["num_results"] == 0:
            break

    return matches


def main():
    id_retriever = IDRetriever()

    conn, cur = database.setup()
    cur.execute('SELECT ID FROM accounts')

    try:
        # for _ in range(3000):
            # id_ = id_retriever.get()  # id returns a tuple (id, )
            # matches = get_matches(id_)
            # save_to_disk(matches, id_)

        for id_ in cur:
            id_ = id_[0]  # id returns a tuple (id, )
            matches = get_matches(id_)
            save_to_disk(matches, id_)
            print(id_retriever.get())


    except KeyboardInterrupt:
        save_to_disk(matches, id_)

    # conn.close()

if __name__ == "__main__":
    main()
