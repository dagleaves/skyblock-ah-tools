# coding=utf-8

from sortedcontainers import SortedList as slist
from base64 import b64decode
import grequests
import json
import uuid
import math
import time
import sys
import io

# TODO: Aggregate pages into one big json object to save to file

DEBUG = True

MAX_CONNECTIONS = 10
url_base = "https://api.hypixel.net/skyblock/auctions"


def load_average():
    pass


def save_average():
    pass


def main():
    resp = [grequests.get(url_base)]

    for res in grequests.map(resp):
        data = json.loads(res.content)
        total_pages = data['totalPages']
        print('Total Pages Found: ' + str(total_pages))

        # Verify success
        if data['success']:
            checkAuctions()
        else:
            print('Failed GET request: ' + data['cause'])

    # Remaining page urls
    urls = []
    if DEBUG:
        total_pages = 1
    for i in range(1, total_pages + 1):
        urls.append(url_base + '?page=' + str(i))

    # Async remaining pages - limited rate
    results = []
    for i in range(1, total_pages + 1, MAX_CONNECTIONS):
        print('Retrieving Auctions (' + str((i - 1) // MAX_CONNECTIONS + 1) +
              ' / ' + str(math.ceil(total_pages / MAX_CONNECTIONS)) + ')')
        resp = (grequests.get(url, stream=False)
                for url in urls[i:i + MAX_CONNECTIONS])
        time.sleep(1)
        results.extend(grequests.map(resp))

    # Get items from remaining pages
    print('Filtering Auctions...')
    for res in results:
        try:
            data = json.loads(res.content)
        except:
            print('Failed to access API... Please wait before running the program again')
        # Verify success
        if data['success']:
            with open('history/' + str(uuid.uuid4()), 'w') as f:
                json.dump(data, f, indent=4, sort_keys=True)
