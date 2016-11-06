"""This module contains some helper functions to use when connecting to Valve's API.
"""

import urllib.request
import urllib.parse
import time


def connect(url: str, params: str):
    try:
        with urllib.request.urlopen(url + "?" + params) as link:
            return link.read().decode("UTF-8")
    except urllib.error.HTTPError as err:
        if err.code != 429 and err.code != 503 and err.code != 500:
            raise urllib.error.HTTPError
        print("Valve returned error {}.".format(err.code))
        return None
    except urllib.error.URLError:
        return None


def fetch(url: str, params: str, wait_interval: int = 10):
    response = connect(url, params)
    while response is None:
        time.sleep(wait_interval)
        response = connect(url, params)

    return response
