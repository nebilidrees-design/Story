import json
from datetime import datetime


def auction_action(action):
    def decorator(method):
        method.action = action
        return method

    return decorator


class BidderRegistry:
    def load(self):
        try:
            with open("bidders.json", "r") as file:
                return json.load(file)
        except (FileNotFoundError, json.JSONDecodeError):
            return {}


class Bidder:
    def __init__(self, bidder_id, name, contact, bidding_history=None):
        self.__bidder_id = bidder_id
        self.__name = name
        self.__contact = contact
        self.__bidding_history = bidding_history or []
        self.__bidders_dict = {}

    @property
    def bidder_id(self):
        return self.__bidder_id

    def __str__(self):
        return f"{self.__name} ({self.__bidder_id})"

    def save(self):
        try:
            with open("bidders.json", "r") as file:
                bidders = json.load(file)
        except (FileNotFoundError, json.JSONDecodeError):
            bidders = {}

        if self.__bidder_id in bidders:
            return False

        bidders[self.__bidder_id] = {
            "name": self.__name,
            "contact": self.__contact,
            "bidding_history": self.__bidding_history,
        }
        with open("bidders.json", "w") as file:
            json.dump(bidders, file, indent=2)
        return True


class Auction:
    def place_bid(self, name, bid_amount, bid_item):
        raise NotImplementedError

    def close_auction(self, bid_item):
        raise NotImplementedError


class AuctionItems(Auction):
    def __init__(self, name="", condition="", base_price=0, bidder_registry=None):
        self.name = name
        self.condition = condition
        self.base_price = base_price
        self.bidder_registry = bidder_registry or BidderRegistry()

    def browse_auction_items(self):
        with open("bids.json", "r") as file:
            data = json.load(file)

        print("========== AUCTION ITEMS ==========")
        for item, value in data.items():
            current_bid = self._highest_bid(item, value["base price"])
            print(f"{item}")
            print(f"\tcondition: {value['condition']}")
            print(f"\tstarting price: {value['base price']}")
            print(f"\tcurrent bid: {current_bid}")
            print(f"\tstatus: {value['status']}")

    def _highest_bid(self, item_name, base_price):
        bidders = self.bidder_registry.load()

        highest = base_price
        for bidder in bidders.values():
            for bid in bidder.get("bidding_history", []):
                if (
                    bid.get("item_name", "").upper() == item_name.upper()
                    and bid.get("status") == "PENDING"
                ):
                    highest = max(highest, bid["bid_amount"])
        return highest

    @auction_action("start_auction")
    def start_auction(self, item_name):
        item_name = item_name.strip().upper()
        with open("bids.json", "r") as file:
            items = json.load(file)

        if item_name not in items:
            print("ITEM DOESNT EXIST..")
            return False
        if items[item_name]["status"].upper() == "ACTIVE":
            print("AUCTION IS ALREADY ACTIVE..")
            return False

        items[item_name]["status"] = "ACTIVE"
        with open("bids.json", "w") as file:
            json.dump(items, file, indent=2)
        print(f"AUCTION STARTED FOR {item_name}..")
        return True

    def current_highest_bids(self):
        with open("bids.json", "r") as file:
            items = json.load(file)

        print("========== CURRENT HIGHEST BIDS ==========")
        for item_name, item in items.items():
            highest = self._highest_bid(item_name, item["base price"])
            if highest == item["base price"]:
                print(
                    f"{item_name}: NO BIDS YET | "
                    f"Starting price: {item['base price']} | {item['status']}"
                )
            else:
                print(f"{item_name}: Current bid: {highest} | {item['status']}")

    def bidding_history(self, item_name):
        item_name = item_name.strip().upper()
        bidders = self.bidder_registry.load()

        print(f"========== BIDDING HISTORY: {item_name} ==========")
        found = False
        for bidder_id, bidder in bidders.items():
            for bid in bidder.get("bidding_history", []):
                if bid.get("item_name", "").upper() == item_name:
                    found = True
                    print(
                        f"{bidder_id} ({bidder.get('name', 'Unknown')}): "
                        f"{bid['bid_amount']} | {bid['status']} | {bid.get('date', 'Unknown date')}"
                    )
        if not found:
            print("NO BIDS FOUND FOR THIS ITEM..")

    def auction_results(self):
        with open("bids.json", "r") as file:
            items = json.load(file)
        bidders = self.bidder_registry.load()

        print("========== AUCTION RESULTS ==========")
        for item_name, item in items.items():
            if item["status"].upper() != "CLOSED":
                continue
            winner = None
            for bidder_id, bidder in bidders.items():
                for bid in bidder.get("bidding_history", []):
                    if (
                        bid.get("item_name", "").upper() == item_name
                        and bid.get("status") == "WON"
                    ):
                        winner = (
                            bidder_id,
                            bidder.get("name", "Unknown"),
                            bid["bid_amount"],
                        )
            if winner:
                print("\n----------------------------------------")
                print(f"ITEM: {item_name}")
                print("WINNER:")
                print(f"Name: {winner[1]}")
                print(f"Bidder ID: {winner[0]}")
                print(f"Winning Bid: {winner[2]}")
                print("Status: WON")
                print("----------------------------------------")
            else:
                print("\n----------------------------------------")
                print(f"ITEM: {item_name}")
                print("Status: UNSOLD")
                print("----------------------------------------")

    def search_items(self, item_name):

        with open("bids.json", "r") as file:
            data = json.load(file)

            item_name = item_name.upper()
            if item_name in data:
                print(item_name)
                item = data[item_name]
                for k, v in item.items():
                    print(f"{k}:{v}")
            else:
                print("ITEM NOT FOUND !")

    @auction_action("place_bid")
    def place_bid(self, name, bid_amount, bid_item):
        with open("bids.json", "r") as file:
            data = json.load(file)

        item_name = bid_item.strip().upper()

        if item_name not in data:
            print("ITEM DOESNT EXIST..")
            return False

        item = data[item_name]

        bidders = self.bidder_registry.load()

        if name not in bidders:
            print("ONLY REGISTERED BIDDERS CAN PLACE BIDS..")
            return False

        current_highest = item["base price"]
        for bidder in bidders.values():
            for previous_bid in bidder.get("bidding_history", []):
                previous_item = previous_bid.get("item_name", "").upper()
                previous_status = previous_bid.get("status", "PENDING")
                if previous_item == item_name and previous_status == "PENDING":
                    current_highest = max(current_highest, previous_bid["bid_amount"])

        print(f"CURRENT HIGHEST BID FOR {item_name}: {current_highest}")

        if item["status"].upper() != "ACTIVE":
            print("AUCTION IS NOT ACTIVE. START THE AUCTION FIRST..")
            return False

        if bid_amount <= current_highest:
            print(f"BID MUST BE HIGHER THAN {current_highest}..")
            return False

        bidder = bidders.setdefault(name, {"bidding_history": []})
        if "bidding_history" not in bidder:
            previous_bid = {
                key: bidder[key]
                for key in ("item_bided", "bids_price", "bid_item_status")
                if key in bidder
            }
            bidder.clear()
            bidder["bidding_history"] = [previous_bid] if previous_bid else []

        bidder["bidding_history"].append(
            {
                "item_name": item_name,
                "bid_amount": bid_amount,
                "status": "PENDING",
                "date": datetime.now().strftime("%d %B %Y"),
            }
        )

        with open("bidders.json", "w") as file:
            json.dump(bidders, file, indent=2)

        print(f"BID PLACED: {name} offered {bid_amount} for {item_name}")
        print(f"STATUS: PENDING | DATE: {bidders[name]['bidding_history'][-1]['date']}")
        return True

    @auction_action("close_auction")
    def close_auction(self, bid_item):
        item_name = bid_item.strip().upper()
        with open("bids.json", "r") as file:
            items = json.load(file)
        bidders = self.bidder_registry.load()

        if item_name not in items:
            print("ITEM DOESNT EXIST..")
            return False
        if items[item_name]["status"].upper() != "ACTIVE":
            print("AUCTION IS NOT ACTIVE..")
            return False

        bids = []
        for bidder_id, bidder in bidders.items():
            for bid in bidder.get("bidding_history", []):
                legacy_name = bid.get("item_name", bid.get("item_bided", ""))
                legacy_amount = bid.get("bid_amount", bid.get("bids_price"))
                if (
                    legacy_name.upper() == item_name
                    and bid.get("status", "PENDING") in ("PENDING", "AVAILABLE")
                    and legacy_amount is not None
                ):
                    bid["item_name"] = item_name
                    bid["bid_amount"] = legacy_amount
                    bid["status"] = "PENDING"
                    bid.setdefault("date", datetime.now().strftime("%d %B %Y"))
                    bids.append((legacy_amount, bidder_id, bid))

        if not bids:
            items[item_name]["status"] = "CLOSED"
            with open("bids.json", "w") as file:
                json.dump(items, file, indent=2)
            print(f"{item_name}: UNSOLD. NO BIDS WERE PLACED.")
            return True

        winner = max(bids, key=lambda entry: entry[0])
        for _, _, bid in bids:
            bid["status"] = "WON" if bid is winner[2] else "LOST"
        items[item_name]["status"] = "CLOSED"

        with open("bidders.json", "w") as file:
            json.dump(bidders, file, indent=2)
        with open("bids.json", "w") as file:
            json.dump(items, file, indent=2)

        print(f"WINNER: {winner[1]} WITH A BID OF {winner[0]}")
        for _, bidder_id, bid in bids:
            print(f"{bidder_id}: {bid['status']}")

    @auction_action("restart_auction")
    def restart_auction(self, bid_item):
        item_name = bid_item.strip().upper()
        with open("bids.json", "r") as file:
            items = json.load(file)
        if item_name not in items:
            print("ITEM DOESNT EXIST..")
            return
        items[item_name]["status"] = "AVAILABLE"
        with open("bids.json", "w") as file:
            json.dump(items, file, indent=2)
        print(f"{item_name} RESTARTED. BIDDER HISTORY WAS PRESERVED.")
