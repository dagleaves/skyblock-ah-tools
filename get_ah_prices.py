# coding=utf-8
from apscheduler.schedulers.background import BackgroundScheduler
from datetime import date
from base64 import b64decode
import grequests
import json
import uuid
import math
import time
import nbt
import io
import os


DEBUG = False
MAX_CONNECTIONS = 10
url_base = "https://api.hypixel.net/skyblock/auctions"

lowest_bins = {"common": {}, "uncommon": {}, "rare": {}, "epic": {
}, "mythic": {}, "legendary": {}, "divine": {}, "special": {}, "very_special": {}, 'supreme': {}}


def get_lowest_bins(auction):
    for item in auction:
        if not item['bin']:
            continue
        item_name = item['item_name']
        item_name = ' '.join(item_name.encode(
            'ascii', 'ignore').decode().split())    # remove unicode characters
        item['item_name'] = item_name
        item_tier = item['tier'].lower()
        item_price = item['starting_bid']
        item_bytes = nbt.nbt.NBTFile(
            fileobj=io.BytesIO(b64decode(item['item_bytes'])))
        item_count = item_bytes[0][0][1].value

        # Account for item quantity in price
        if item_count > 1:
            item['starting_bid'] = item['starting_bid'] / item_count

        # Filter unwanted items
        if item['item_name'] == 'Enchanted Book' or item['item_name'] == 'Skeleton Skull':
            continue
        # Record lowest BIN price
        if item_name in lowest_bins[item_tier].keys() and item_price >= lowest_bins[item_tier][item_name]:
            continue
        lowest_bins[item_tier][item_name] = item_price


def save_auctions(data):
    today = date.today()
    with open('history/' + str(today) + '_' + str(uuid.uuid4()) + '.json', 'w') as f:
        json.dump(data, f, indent=4, sort_keys=True)


def main():
    print('Retrieving auction prices')
    resp = [grequests.get(url_base)]

    for res in grequests.map(resp):
        data = json.loads(res.content)
        total_pages = data['totalPages']
        print('Total Pages Found: ' + str(total_pages))

        # Verify success
        if data['success']:
            get_lowest_bins(data['auctions'])

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
            get_lowest_bins(data['auctions'])

    # Save data
    save_auctions(lowest_bins)
    print('Saved auction price data')
    print()


if __name__ == '__main__':
    sched = BackgroundScheduler()
    sched.add_job(main, 'interval', hours=1)
    # sched.add_job(main, 'interval', minutes=1)
    sched.start()

    try:
        # This is here to simulate application activity (which keeps the main thread alive).
        while True:
            time.sleep(5)
    except (KeyboardInterrupt, SystemExit):
        # Not strictly necessary if daemonic mode is enabled but should be done if possible
        sched.shutdown()

    # main()
