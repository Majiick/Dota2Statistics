# noinspection PyUnresolvedReferences
import urllib.request
import urllib.parse
import json
import time
import threading
import database
from info import *


class PlayerCollectionCounter:
    lock = threading.Lock()

    def __init__(self):
        self.players = 0
        self.timeStarted = time.time() - 1  # So we don't get ZeroDivisionError
        self.print_collection_rate()

    def increment(self, amount):
        with self.lock:
            self.players += amount

    def print_collection_rate(self):
        threading.Timer(1.0, self.print_collection_rate).start()

        print("Average collection rate: {}/sec".format(int(self.players / (time.time() - self.timeStarted))))
        print("{} seconds since start".format(int(time.time() - self.timeStarted)))


class AccountIDsBuffer:
    def __init__(self, size):
        self.account_ids = set()
        self.size = size

    def add(self, x):
        self.account_ids.add(x)

        if len(self.account_ids) > self.size:
            self.save()

    def save(self):
        save_to_disk(self.account_ids)
        self.account_ids.clear()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.save()


def connect(url, params):
    try:
        with urllib.request.urlopen(url + "?" + params) as link:
            return link.read().decode("UTF-8")
    except urllib.error.HTTPError as err:
        if err.code != 429 and err.code != 503 and err.code != 500:
            raise urllib.error.HTTPError
        print("Valve returned error {}.".format(err.code))
        return None


class Matches:
    def __init__(self, starting_seq, api_key):
        self.matches = list()
        self.nextMatch = 0
        self.last_seq_requested = starting_seq
        self.api_key = api_key

    def next(self, n):
        i = 0

        while i < n:
            if self.nextMatch > len(self.matches) - 1:
                self.matches.clear()
                self.nextMatch = 0
                self.request_matches()

            yield self.matches[self.nextMatch]
            i += 1
            self.nextMatch += 1

    @staticmethod
    def get_last_seq_num(data):
        return data["result"]["matches"][len(data["result"]["matches"]) - 1]["match_seq_num"]

    def request_matches(self):
        print("Sequence#: {}".format(self.last_seq_requested))
        time.sleep(1)

        params = urllib.parse.urlencode({'key': self.api_key, 'start_at_match_seq_num': self.last_seq_requested})

        response = connect(GET_MATCH_HISTORY_SEQUENCE_URL, params)
        while response is None:
            time.sleep(10)
            response = connect(GET_MATCH_HISTORY_SEQUENCE_URL, params)

        data = json.loads(response)

        for match in data["result"]["matches"]:
            self.matches.append(match)

        self.last_seq_requested = self.get_last_seq_num(data)


def save_to_disk(data):
    conn, cur = database.get()

    for x in data:
        cur.execute("INSERT OR IGNORE INTO accounts (id) VALUES ({})".format(x))

    conn.commit()


def collect(starting_seq, api_key):
    y = Matches(starting_seq, api_key)

    try:
        with AccountIDsBuffer(1000) as account_ids:
            for match in y.next(100000):
                for player in match["players"]:
                    if "account_id" in player:
                        account_ids.add(player["account_id"])
                        playerCounter.increment(1)

    except KeyboardInterrupt:
        account_ids.save()


if __name__ == "__main__":
    playerCounter = PlayerCollectionCounter()

    for i in range(1, 25):  # 1,5
        key = get_key()
        t = threading.Thread(target=collect, args=(i*100000000, key), name=key)
        t.start()
        time.sleep(1/6)  # so they're out of sync
