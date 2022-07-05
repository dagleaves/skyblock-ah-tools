from pprint import pprint
from sortedcontainers import SortedList as slist
import grequests
import json
import time

# TODO: See if there is a way to account for quantity differences
# TODO: Do stars matter?

# DEBUG = True
DEBUG = False

url_base = f"https://api.hypixel.net/skyblock/auctions"

MAX_CONNECTIONS = 10

data = {}
filtered_auctions = {"common": {}, "uncommon": {}, "rare": {}, "epic": {
}, "mythic": {}, "legendary": {}, "divine": {}, "special": {}, "very special": {}}
flips = []

MAX_PRICE = 1000000
MIN_PROFIT = 100000
REFORGES = ['Gentle ', 'Odd ', 'Fast ', 'Fair ', 'Epic ', 'Sharp ', 'Heroic ', 'Spicy ', 'Legendary ', 'Dirty ', 'Fabled ', 'Suspicious ', 'Gilded ', 'Warped ', 'Withered ', 'Bulky ', 'Treacherous ', 'Stiff ', 'Lucky ', 'Salty ', 'Deadly ', 'Fine ', 'Grand ', 'Hasty ', 'Neat ', 'Rapid ', 'Unreal ', 'Awkward ', 'Rich ', 'Precise ', 'Spiritual ', 'Headstrong ', 'Clean ', 'Fierce ', 'Heavy ', 'Light ', 'Mythic ', 'Pure ', 'Smart ', 'Titanic ', 'Wise ', 'Perfect ', 'Necrotic ', 'Ancient ', 'Spiked ', 'Renowned ', 'Cubic ', 'Hyper ', 'Reinforced ',
            'Loving ', 'Ridiculous ', 'Empowered ', 'Giant ', 'Submerged ', 'Jaded ', 'Double-Bit ', 'Lumberjack\'s ', 'Great ', 'Rugged ', 'Lush ', 'Green Thumb ', 'Peasant\'s ', 'Robust ', 'Zooming ', 'Unyielding ', 'Prospector\'s ', 'Excellent ', 'Sturdy ', 'Fortunate ', 'Moil ', 'Toil ', 'Blessed ', 'Bountiful ', 'Magnetic ', 'Fruitful ', 'Refined ', 'Stellar ', 'Mithraic ', 'Auspicious ', 'Fleet ', 'Heated ', 'Ambered ', 'Waxed ', 'Fortified ', 'Strengthened ', 'Glistening ', 'Very ', 'Highly ', 'Extremely ', 'Not So ', 'Thicc ', 'Absolutely ', 'Even More ']


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
        item_name = item['item_name']
        item_tier = item['tier']
        print('Found Item')
        try:
            item_ans = checkItem(item)
            print("Checked Item", item_ans)

            # Failed Filter
            if not item_ans[0]:
                print('Item Failed Filter')
                continue
            # Passed Filter
            print('Item Passed Filter')

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
                    break

            # Add item to sorted dictionary of items
            if item_name in filtered_auctions[item_tier.lower()]:
                print('Item exists in filtered auction')
                filtered_auctions[item_tier.lower(
                )][item_name].add(item)
                print('Appended item to filtered auction')
            else:
                print('Item does not exist in filtered auction')
                filtered_auctions[item_tier.lower()][item_name] = slist(
                    [item], key=lambda x: x['starting_bid'])
                print('New slist created for item')

        except:
            print("CHECK AUCTION FAILED")
            exit()


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
        print('URL Batch ' + i)
        resp = (grequests.get(url, stream=False)
                for url in urls[i:i + MAX_CONNECTIONS])
        time.sleep(1)
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


if __name__ == "__main__":
    main()
