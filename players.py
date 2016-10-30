# noinspection PyUnresolvedReferences
import urllib.request
import urllib.parse
import json
import time
import threading
import database
from Info import *


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


def connect(params):
    try:
        with urllib.request.urlopen(GET_MATCH_HISTORY_SEQUENCE_URL + "?" + params) as url:
            return url.read().decode("UTF-8")
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

        response = connect(params)
        while response is None:
            time.sleep(10)
            response = connect(params)

        data = json.loads(response)

        for match in data["result"]["matches"]:
            self.matches.append(match)

        self.last_seq_requested = self.get_last_seq_num(data)


def save_to_disk(data):
    conn, cur = database.get()

    for x in data:
        cur.execute("INSERT OR IGNORE INTO accounts VALUES ({})".format(x))

    conn.commit()


def collect(starting_seq, api_key):
    y = Matches(starting_seq, api_key)

    try:
        with AccountIDsBuffer(1000) as account_ids:
            for match in y.next(100000):
                for player in match["players"]:
                    if "account_id" in player:
                        account_ids.add(player["account_id"])

    except KeyboardInterrupt:
        account_ids.save()

if __name__ == "__main__":
    for i in range(1, 5):  # 1,5
        key = API_KEYS[(i-1) % len(API_KEYS)]
        t = threading.Thread(target=collect, args=(i*500000000, key), name=key)
        t.start()
        time.sleep(1/6)  # so they're out of sync
