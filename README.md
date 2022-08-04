# Skyblock Auction House Tools

This repository is a collection of my open-source tools for the Hypixel Skyblock auction house.

## Dependencies

These tools are written in Python, so you must have Python 3 installed on your system (and pip for dependencies).

To install the required Python libraries, using pip run

```
pip install -r requirements.txt
```

## Tools

All commands will be entered in the command line.

1. Flip Finder
	- Run `python3 find_flips.py`
	- This will find all flips currently in the auction house. The maximum price, minimum profit, and minimum volume can be set 
with their respective variables at the top of the program.

2. Auction House Price History
	- Run `python3 get_ah_prices.py`
	- This will get the current lowest prices for each item on the auction house and save them to `history/`

3. Historical Average Item Price
	- Run `python3 calc_avg_prices.py`
	- This will calculate the average item prices from the saved historical data in `history/` (See #2) and save them to `avg_prices.json`

4. Search Average Item Price
	- Run `python3 seaarch_avg_prices.py ITEM_NAME` where ITEM_NAME is the name of the item you want to search for
	- This will print the average price of the item you search for if data for it exists
