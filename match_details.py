"""This module pulls matches from the matches table and gets detailed information on them and saves it in the database.

TODO:
Fix the sql schema, season isn't included.
And also store all the data about the player such as item, level, abilities whatever etc.
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
from collections import namedtuple


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


class Table:
    def __init__(self, name: str, fields: tuple):
        self.name = name
        self.fields = fields

    def construct_insert(self):
        return "INSERT OR IGNORE INTO {0} VALUES ({1})".format(self.name, ("?,"*len(self.fields))[:-1])


def save_to_disk_matches_detailed(data : dict, cur):
    # I use it 'cause it's fancy and I want to remember namedtuples in the future :) This is a gross misuse though.
    fields = namedtuple('matches_detailed_fields',
                        ["radiant_win", "duration", "pre_game_duration", "start_time", "match_id", "match_seq_num",
                         "tower_status_radiant", "tower_status_dire", "cluster", "first_blood_time", "lobby_type",
                         "human_players",
                         "leagueid", "positive_votes", "negative_votes", "game_mode", "flags", "engine",
                         "radiant_score", "dire_score"])

    table = Table("matches_detailed", fields._fields)

    extracted_data = [data["result"][k] for k in fields._fields]

    try:
        cur.execute(table.construct_insert(),
                    extracted_data)
    except KeyError:
        pass


def save_to_disk_player_match_detailed(data : dict, cur):
    fields = namedtuple('player_match_detailed_fields',
                        ["account_id", "player_slot", "hero_id", "item_0", "item_1", "item_2", "item_3",
                         "item_4", "item_5", "kills", "deaths", "assists", "leaver_status", "gold", "last_hits", "denies",
                         "gold_per_min", "xp_per_min", "gold_spent", "hero_damage", "tower_damage", "hero_healing",
                         "level", "match_id"])
    field_positions = dict(zip(fields._fields, range(len(fields._fields))))

    table = Table("player_match_detailed", fields._fields)

    for player in data["result"]["players"]:
        extracted_data = list(map(player.get, fields._fields))
        extracted_data = [x if x else -1 for x in extracted_data]
        extracted_data[field_positions["match_id"]] = data["result"]["match_id"]  # Set match_id

        try:
            cur.execute(
                table.construct_insert(),
                extracted_data)
        except KeyError:
            pass


def save_to_disk_ability_upgrade(data : dict, cur):
    fields = namedtuple('ability_upgrade_fields',
                        ["ability", "time", "level", "account_id", "match_id"])
    field_positions = dict(zip(fields._fields, range(len(fields._fields))))

    table = Table("ability_upgrade", fields._fields)

    for player in data["result"]["players"]:
        for ability_upgrade in player["ability_upgrades"]:
            extracted_data = list(map(ability_upgrade.get, fields._fields))

            if "account_id" in player:
                extracted_data[field_positions["account_id"]] = player["account_id"]
            else:
                extracted_data[field_positions["account_id"]] = -1

            extracted_data[field_positions["match_id"]] = data["result"]["match_id"]

            cur.execute(
                table.construct_insert(),
                extracted_data)


def save_to_disk(data: dict):
    conn, cur = database.get()

    save_to_disk_matches_detailed(data, cur)
    save_to_disk_player_match_detailed(data, cur)
    save_to_disk_ability_upgrade(data, cur)

    conn.commit()
    conn.close()


def collect(api_key: int, match_details_counter: CollectionCounter = None):
    match_retriever = MatchIDRetriever()

    try:
        for id_ in match_retriever.get_ids(100000):
            params = urllib.parse.urlencode({'key': api_key, 'match_id': id_})
            response = fetch(GET_MATCH_DETAILS_URL, params)

            data = json.loads(response)
            match_details_counter.increment(1)
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
