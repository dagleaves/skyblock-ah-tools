from calc_avg_prices import get_avg_prices
import argparse
import json
import os


def main():
    if not args.no_update:
        get_avg_prices('avg_prices.json')

    assert os.path.exists(
        'avg_prices.json'), 'File \'avg_prices.json\' does not exist. Please run with update to fetch prices.'
    with open('avg_prices.json') as f:
        average_prices = json.load(f)

    item_name = ' '.join(args.item_name)
    for tier in average_prices:
        if item_name in average_prices[tier]:
            print('Average price:', average_prices[tier][item_name])
            return
    print('No historical data available for this item')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description='Search for the average BIN price of an AH item')
    parser.add_argument('item_name', metavar='NAME', nargs='+',
                        help='item name to search for')
    parser.add_argument('--no-update', action='store_false',
                        help='update and fetch latest avg item prices')
    args = parser.parse_args()

    main()
