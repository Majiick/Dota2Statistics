"""This module pulls matches from the matches table and gets detailed information on them and saves it in the database.
"""

import urllib.request
import urllib.parse
import json
import time
import database
from info import *
from connection import fetch
import threading
from CollectionCounter import CollectionCounter


class MatchIDRetriever:
    """Thread-safe class to retrieve unchecked player account_ids from the database.
    """
    lock = threading.Lock()

    def get_ids(self, n: int) -> int:  # Does this generator need to be here? I think just get() will suffice, although idk.
        """Generator to yield an unchecked match_id.
        Args:
            n: How many matches to yield.
        Yields:
            Yields an unchecked match.
        """
        i = 0

        while i < n:
            yield self.get_match()
            i += 1

    def get_match(self) -> int:
        """Get an unchecked match.
        Returns:
            Returns an a match id that hasn't been checked and checks it.
        """
        with self.lock:
            conn, cur = database.get()

            cur.execute('SELECT match_id from matches WHERE checked = 0 LIMIT 1')

            id_ = None
            for x in cur:
                id_ = x[0]

            cur.execute('UPDATE matches SET checked=1 WHERE match_id=?', (id_,))
            conn.commit()
            conn.close()

            return id_


def save_to_disk(data: dict):
    conn, cur = database.get()

    fields = ("radiant_win", "duration", "pre_game_duration", "start_time", "match_id", "match_seq_num", "tower_status_radiant", "tower_status_dire", "cluster", "first_blood_time", "lobby_type", "human_players",
              "leagueid", "positive_votes", "negative_votes", "game_mode", "flags", "engine", "radiant_score", "dire_score")

    try:
        extracted_data = [int(data["result"][k]) for k in fields]
        cur.execute('INSERT OR IGNORE INTO matches_detailed VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)',
                    extracted_data)
    except KeyError:
        pass

    conn.commit()
    conn.close()


def collect(api_key: int, matche_details_counter: CollectionCounter = None):
    match_retriever = MatchIDRetriever()

    try:
        for id_ in match_retriever.get_ids(1000):
            params = urllib.parse.urlencode({'key': api_key, 'match_id': id_})
            response = fetch(GET_MATCH_DETAILS_URL, params)

            data = json.loads(response)
            matche_details_counter.increment(1)
            save_to_disk(data)

    except KeyboardInterrupt:
        save_to_disk(data)


def main():
    match_details_counter = CollectionCounter()

    for i in range(1, 50):
        key = get_key()
        t = threading.Thread(target=collect, args=(key, match_details_counter), name=key)
        t.start()
        time.sleep(1 / 6)  # So requests are out of sync.


if __name__ == "__main__":
    main()
