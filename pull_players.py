"""Retrieves account ids from Valve's DOTA2 API through GetMatchHistoryBySequenceNum.

This module retrieves account ids by retrieving matches from GetMatchHistoryBySequenceNum and
then retrieving players from the retrieved matches. The account_ids are put into a database.

"""

import urllib.parse
import json
import time
import threading
import database
from connection import fetch
from info import *
from CollectionCounter import CollectionCounter


class AccountIDsBuffer:
    """A buffer object to store account_ids in memory and write them into the database once we have enough account_ids.
    """
    def __init__(self, size: int):
        self.account_ids = set()
        self.size = size

    def add(self, id_: int):
        self.account_ids.add(id_)

        if len(self.account_ids) > self.size:
            self.save()

    def save(self):
        self.save_to_disk(self.account_ids)
        self.account_ids.clear()

    @staticmethod
    def save_to_disk(data: set) -> None:
        """Saves a set of account_ids to the database.

        Args:
            data: The set of account_ids to save.
        """
        conn, cur = database.get()

        for x in data:
            cur.execute("INSERT OR IGNORE INTO accounts (id) VALUES ({})".format(x))

        conn.commit()
        conn.close()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.save()


class Matches:
    """Provides matches by pulling them from the Valve API.
    """

    def __init__(self, starting_seq: int, api_key: str):
        """
        Args:
            starting_seq: The starting match sequence to collect from.
            api_key: The API key to use.
        """
        self.matches = list()
        self._nextMatch = 0
        self.last_seq_requested = starting_seq
        self.api_key = api_key

    def get_matches(self, n: int) -> dict:
        """Generator to yield the next match.
        Args:
            n: How many matches to yield.
        Yields:
            Yields a match dict according to the match JSON structure.
        """
        i = 0

        while i < n:
            if self._nextMatch > len(self.matches) - 1:
                self.matches.clear()
                self._nextMatch = 0
                self._request_matches()

            yield self.matches[self._nextMatch]
            i += 1
            self._nextMatch += 1

    @staticmethod
    def get_last_seq_num(data: dict):
        return data["result"]["matches"][len(data["result"]["matches"]) - 1]["match_seq_num"]

    def _request_matches(self) -> None:
        """Requests (500) matches from Valve and updates self.matches with the retrieved matches.
        """
        print("Sequence#: {}".format(self.last_seq_requested))
        time.sleep(1)

        params = urllib.parse.urlencode({'key': self.api_key, 'start_at_match_seq_num': self.last_seq_requested})
        response = fetch(GET_MATCH_HISTORY_SEQUENCE_URL, params)
        data = json.loads(response)

        for match in data["result"]["matches"]:
            self.matches.append(match)

        self.last_seq_requested = self.get_last_seq_num(data)


def collect(starting_seq: int, api_key: str, player_counter: CollectionCounter = None) -> None:
    """This function will collect account ids until interrupted by a KeyboardInterrupt.

    Args:
        starting_seq: The starting match sequence to collect from.
        api_key: The API key to use.
        player_counter: Counter object to count the amount of players retrieved. Optional.
    """
    match_retriever = Matches(starting_seq, api_key)

    try:
        with AccountIDsBuffer(1000) as account_ids:
            for match in match_retriever.get_matches(100000):
                for player in match["players"]:
                    if "account_id" in player:
                        account_ids.add(player["account_id"])
                        player_counter.increment(1)

    except KeyboardInterrupt:
        account_ids.save()


def main():
    pc = CollectionCounter()

    for i in range(1, 25):  # Create 24 threads to collect players.
        key = get_key()
        t = threading.Thread(target=collect, args=(i * 100000000, key), kwargs={'player_counter': pc}, name=key)
        t.start()
        time.sleep(1 / 6)  # So requests are out of sync.

if __name__ == "__main__":
    main()
