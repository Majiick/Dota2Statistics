from Info import *
import sqlite3


def get():
    conn = sqlite3.connect(DB_URI, uri=True)
    cur = conn.cursor()

    return conn, cur


def setup():
    conn = sqlite3.connect(DB_URI, uri=True)
    cur = conn.cursor()
    cur.execute('''CREATE TABLE IF NOT EXISTS accounts
                  (ID INTEGER PRIMARY KEY)''')

    return conn, cur

setup()
