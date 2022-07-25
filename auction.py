# coding=utf-8

from sortedcontainers import SortedList as slist
from base64 import b64decode
import traceback
import grequests
import json
import math
import time
import nbt
import sys
import io

DEBUG = True
DEBUG = False

url_base = "https://api.hypixel.net/skyblock/auctions"

data = {}
filtered_auctions = {"common": {}, "uncommon": {}, "rare": {}, "epic": {
}, "mythic": {}, "legendary": {}, "divine": {}, "special": {}, "very_special": {}, 'supreme': {}}
flips = []

MAX_CONNECTIONS = 10
MAX_PRICE = 2000000
MIN_PROFIT = 200000
MIN_VOLUME = 10      # filter out low sale volume listings
REFORGES = ['Shiny ', 'Gentle ', 'Odd ', 'Fast ', 'Fair ', 'Epic ', 'Sharp ', 'Heroic ', 'Spicy ', 'Legendary ', 'Dirty ', 'Fabled ', 'Suspicious ', 'Gilded ', 'Warped ', 'Withered ', 'Bulky ', 'Treacherous ', 'Stiff ', 'Lucky ', 'Salty ', 'Deadly ', 'Fine ', 'Grand ', 'Hasty ', 'Neat ', 'Rapid ', 'Unreal ', 'Awkward ', 'Rich ', 'Precise ', 'Spiritual ', 'Headstrong ', 'Clean ', 'Fierce ', 'Heavy ', 'Light ', 'Mythic ', 'Pure ', 'Smart ', 'Titanic ', 'Wise ', 'Perfect ', 'Necrotic ', 'Ancient ', 'Spiked ', 'Renowned ', 'Cubic ', 'Hyper ', 'Reinforced ',
            'Loving ', 'Ridiculous ', 'Empowered ', 'Giant ', 'Submerged ', 'Jaded ', 'Double-Bit ', 'Lumberjack\'s ', 'Great ', 'Rugged ', 'Lush ', 'Green Thumb ', 'Peasant\'s ', 'Robust ', 'Zooming ', 'Unyielding ', 'Prospector\'s ', 'Excellent ', 'Sturdy ', 'Fortunate ', 'Moil ', 'Toil ', 'Blessed ', 'Bountiful ', 'Magnetic ', 'Fruitful ', 'Refined ', 'Stellar ', 'Mithraic ', 'Auspicious ', 'Fleet ', 'Heated ', 'Ambered ', 'Waxed ', 'Fortified ', 'Strengthened ', 'Glistening ', 'Very ', 'Highly ', 'Extremely ', 'Not So ', 'Thicc ', 'Absolutely ', 'Even More ']


def checkItem(item):
    # print('Checking Item')
    # Filters
    if not item['bin']:
        return (False, 'Not BIN')
    if item['claimed']:
        return (False, 'Claimed')
    if item['starting_bid'] > MAX_PRICE:
        return (False, 'Too Expensive')
    if item['item_name'] == 'Enchanted Book':
        return (False, 'Enchanted Book')
    if item['item_name'] == 'Skeleton Skull':
        return (False, 'Skeleton Skull')
    return (True, 'Match')


def checkAuctions():
    global data, filtered_auctions
    for item in data['auctions']:
        item_name = item['item_name']
        item_name = ' '.join(item_name.encode(
            'ascii', 'ignore').decode().split())    # remove unicode characters
        item['item_name'] = item_name
        item_tier = item['tier']
        item_bytes = nbt.nbt.NBTFile(
            fileobj=io.BytesIO(b64decode(item['item_bytes'])))
        item_count = item_bytes[0][0][1].value

        # Account for item quantity in price
        if item_count > 1:
            item['starting_bid'] = item['starting_bid'] / item_count

        # print('Found Item')
        try:
            item_ans = checkItem(item)
            # print("Checked Item", item_ans)

            # Failed Filter
            if not item_ans[0]:
                # print('Item Failed Filter')
                continue
            # Passed Filter
            # print('Item Passed Filter')

            for reforge in REFORGES:
                # Check if item is reforged
                if item_name.startswith(reforge):
                    # Make sure it is not a duplicate prefix item
                    if reforge == 'Wise ' and item_name[len(reforge):] == 'Dragon Armor':
                        continue
                    if reforge == 'Strong ' and item_name[len(reforge):] == 'Dragon Armor':
                        continue
                    if reforge == 'Superior ' and item_name[len(reforge):] == 'Dragon Armor':
                        continue
                    if reforge == 'Heavy ' and item_name[len(reforge):] == 'Armor':
                        continue
                    if reforge == 'Perfect ' and item_name[len(reforge):] == 'Armor':
                        continue
                    if reforge == 'Refined ' and item_name[len(reforge):] == 'Mithril Pickaxe':
                        continue
                    if reforge == 'Refined ' and item_name[len(reforge):] == 'Titanium Pickaxe':
                        continue
                    item_name = item_name[len(reforge):]
                    item['item_name'] = item_name
                    break

            # Add item to sorted dictionary of items
            if item_name in filtered_auctions[item_tier.lower()]:
                # print('Item exists in filtered auction')
                filtered_auctions[item_tier.lower(
                )][item_name].add(item)
                # print('Appended item to filtered auction')
            else:
                # print('Item does not exist in filtered auction')
                filtered_auctions[item_tier.lower()][item_name] = slist(
                    [item], key=lambda x: x['starting_bid'])
                # print('New slist created for item')

        except:
            # print("CHECK AUCTION FAILED")
            traceback.print_exception(*sys.exc_info())
            exit()


def findFlips():
    global filtered_auctions, flips
    for tier in filtered_auctions.keys():
        for item_name in filtered_auctions[tier]:
            item_list = filtered_auctions[tier][item_name]

            # Filter flips
            if len(item_list) < MIN_VOLUME:
                continue
            if item_list[1]['starting_bid'] - item_list[0]['starting_bid'] < MIN_PROFIT:
                continue
            flip = item_list[0]
            flips.append(
                ["/viewauction " + flip['uuid'], flip['item_name'], "Price: " + str(int(flip['starting_bid'])), "Profit: " + str(int(item_list[1]['starting_bid'] - item_list[0]['starting_bid'])), 'Tier: ' + flip['tier']])


def main():
    global data, flips
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
            checkAuctions()
        else:
            print('Failed GET request: ' + data['cause'])

    # Find flips
    findFlips()

    # Sort flips
    flips = sorted(flips, key=lambda x: int(x[-2][8:]))

    # Format output
    lens = [max(map(len, col)) for col in zip(*flips)]
    fmt = '\t'.join('{{:{}}}'.format(x)
                    for x in lens)
    table = [fmt.format(*row) for row in flips]

    # Print results
    print(str(len(flips)) + ' items found')
    time.sleep(1)
    # print(*table, sep='\n')
    print('\n'.join(table))


if __name__ == "__main__":
    main()
