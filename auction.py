from pprint import pprint
from sortedcontainers import SortedList as slist
import grequests
import json
import time

DEBUG = True
#DEBUG = False

url_base = f"https://api.hypixel.net/skyblock/auctions"

MAX_CONNECTIONS = 10

data = {}
filtered_auctions = {"common": {}, "uncommon": {}, "rare": {}, "epic": {}, "mythic": {}, "legendary": {}, "divine": {}, "special": {}, "very special": {}}
flips = []

MAX_PRICE = 1000000
MIN_PROFIT = 100000
# REFORGES = ['Gentle ', 'Odd ', 'Fast ', 'Fair ', 'Epic ', 'Sharp ', 'Heroic ', 'Spicy ', 'Legendary ', 'Dirty ', 'Fabled ', 'Suspicious ', 'Gilded ', 'Warped ', 'Withered ', 'Bulky ', 'Treacherous ', 'Stiff ', 'Lucky ']


def checkItem(item):
    print('Checking Item')
    # Filters
    if not item['bin']:
        return (False, 'Not BIN')
    if item['claimed']:
        return (False, 'Claimed')
    if item['starting_bid'] > MAX_PRICE:
        return (False, 'Too Expensive')
    if item['item_name'] == 'Enchanted Book':
        return (False, 'Enchanted Book')
    return (True, 'Match')


def checkAuctions():
    global data, filtered_auctions
    for item in data['auctions']:
        print('Found Item')
        try:
            item_ans = checkItem(item)
            print("Checked Item", item_ans)
            # Passed filter
            if item_ans[0]:
                print('Item Passed Filter')
                # Add item to sorted dictionary of items
                if item['item_name'] in filtered_auctions[item['tier'].lower()]:
                    print('Item exists in filtered auction')
                    filtered_auctions[item['tier'].lower()][item['item_name']].add(item)
                    print('Appended item to filtered auction')
                else:
                    print('Item does not exist in filtered auction')
                    filtered_auctions[item['tier'].lower()][item['item_name']] = slist(
                        [item], key=lambda x: x['starting_bid'])
                    print('New slist created for item')

                # Failed filter
            else:
                continue

        except:
            print("CHECK AUCTION FAILED")
            exit()
            # pprint(data)


def findFlips():
    global filtered_auctions, flips
    for tier in filtered_auctions.keys():
        for item_name in filtered_auctions[tier]:
            item_list = filtered_auctions[tier][item_name]

            # Filter flips
            if len(item_list) < 2:
                continue
            if item_list[1]['starting_bid'] - item_list[0]['starting_bid'] < MIN_PROFIT:
                continue
            flip = item_list[0]
            # flips.append(item_list)
            flips.append(
                [flip['item_name'], "/viewauction " + flip['uuid'], "Price:", flip['starting_bid'], "Profit:", item_list[1]['starting_bid'] - item_list[0]['starting_bid']])


def main():
    global data, flips
    resp = [grequests.get(url_base)]

    for res in grequests.map(resp):
        data = json.loads(res.content)
        total_pages = data['totalPages']
        # remaining_requests = data['RateLimit-Remaining']
        print('Total Pages Found: ' + str(total_pages))
        # print('Remaining Requests' + str(remaining_requests))

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
        resp = (grequests.get(url, stream=False)
                for url in urls[i:i + MAX_CONNECTIONS])
        time.sleep(0.2)
        results.extend(grequests.map(resp))

    # Get items from remaining pages
    for res in results:
        data = json.loads(res.content)
        # Verify success
        if data['success']:
            checkAuctions()
        else:
            print('Failed GET request: ' + data['cause'])

    # Find flips
    findFlips()

    # Sort flips
    flips = sorted(flips, key=lambda x: x[-1])

    # Print results
    print(str(len(flips)) + ' items found')
    for item in flips:
        print(*item, sep=' # ')
    # for item_list in flips:
    #     print(item_list[0]['item_name'], item_list[0]['starting_bid'])
    #     print(item_list[1]['item_name'], item_list[1]['starting_bid'])


if __name__ == "__main__":
    main()
