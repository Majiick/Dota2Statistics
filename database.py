"""This module contains helper functions to manage the database.
"""

from info import *
import sqlite3


def get():
    conn = sqlite3.connect(DB_URI, uri=True)
    cur = conn.cursor()

    return conn, cur


def setup():
    """Sets up the database by filling it with the tables described in setup_tables.sql.

    Returns:
         The connection and a cursor.
    """
    conn = sqlite3.connect(DB_URI, uri=True)
    cur = conn.cursor()

    with open('setup_tables.sql') as fp:
        cur.executescript(fp.read())

    conn.commit()
    return conn, cur

conn, cur = setup()
conn.close()
