"""This module contains some helper functions to use when connecting to Valve's API.
"""

import urllib.request
import urllib.parse


def connect(url: str, params: str):
    try:
        with urllib.request.urlopen(url + "?" + params) as link:
            return link.read().decode("UTF-8")
    except urllib.error.HTTPError as err:
        if err.code != 429 and err.code != 503 and err.code != 500:
            raise urllib.error.HTTPError
        print("Valve returned error {}.".format(err.code))
        return None
