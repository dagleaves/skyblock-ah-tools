from datetime import date
import json
import os

item_sums = item_averages = {"common": {}, "uncommon": {}, "rare": {}, "epic": {
}, "mythic": {}, "legendary": {}, "divine": {}, "special": {}, "very_special": {}, 'supreme': {}}


def add_auction_to_sums(auction):
    for tier in auction:
        for item in auction[tier]:
            if item in item_sums[tier]:
                item_sums[tier][item][0] += auction[tier][item]
                item_sums[tier][item][1] += 1
                continue
            item_sums[tier][item] = [auction[tier][item], 1]


def load_history():
    for file in os.listdir('history'):
        filedate = file.split('_')[0]
        year = filedate.split('-')[0]
        month = filedate.split('-')[1]
        day = filedate.split('-')[2]
        today = str(date.today())

        # Purge old data
        if year != today.split('-')[0] or month != today.split('-')[1]:
            os.remove('history/' + file)
            continue
        if int(day) - int(today.split('-')[2]) > 7:
            os.remove('history/' + file)
            continue

        # Add item prices to sum dictionary
        with open('history/' + file, 'r') as f:
            auction = json.load(f)
            add_auction_to_sums(auction)


def calc_item_avgs():
    for tier in item_sums:
        for item in item_sums[tier]:
            item_averages[tier][item] = int(item_sums[tier][item][0] /
                                            item_sums[tier][item][1])


def save_avgs(filename='avg_prices.json'):
    with open(filename, 'w') as f:
        json.dump(item_averages, f, indent=4, sort_keys=True)


def get_avg_prices():
    load_history()
    calc_item_avgs()
    save_avgs()


def main():
    # print('Loading history...')
    load_history()
    print('Loaded history')
    # print('Calculating average prices...')
    calc_item_avgs()
    print('Calculated average prices')
    # print('Saving average prices...')
    save_avgs()
    print('Saved average prices')


if __name__ == '__main__':
    main()
