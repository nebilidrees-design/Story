import json
import os
import uuid

from bidding import AuctionItems, Bidder

VALID_PREFIXES = ("077", "070", "075", "079", "078", "074", "076")


def load_json(filename):
    try:
        with open(filename, "r") as file:
            return json.load(file)
    except (FileNotFoundError, json.JSONDecodeError):
        return {}


def clear_terminal():
    os.system("cls" if os.name == "nt" else "clear")


def continue_or_exit():
    while True:
        next_step = input("\nEnter N for the main menu or K to exit: ").strip().lower()
        if next_step == "n":
            return True
        if next_step == "k":
            print("GOODBYE")
            return False
        print("Please enter N or K.")


def format_contact(contact):
    contact = contact.strip().replace(" ", "")
    if len(contact) != 10 or not contact.isdigit():
        return None
    if not contact.startswith(VALID_PREFIXES):
        return None
    return "+256" + contact[1:]


def register_bidder():
    bidders = load_json("bidders.json")
    name = input("Name: ").strip()
    contact = format_contact(input("Contact (10 digits, e.g. 0771234567): "))
    if contact is None:
        print(
            "INVALID CONTACT. Use 10 digits beginning with 077, 070, 075, 079, 078, 074, or 076."
        )
        return

    for bidder in bidders.values():
        if bidder.get("contact") == contact:
            print("THIS CONTACT NUMBER IS ALREADY REGISTERED..")
            return

    bidder_id = f"BID-{uuid.uuid4().hex.upper()}"
    while bidder_id in bidders:
        bidder_id = f"BID-{uuid.uuid4().hex.upper()}"

    if Bidder(bidder_id, name, contact).save():
        print(f"Bidder registered successfully.")
        print(f"Your random bidder ID is: {bidder_id}")


def place_bids(auction):
    while True:
        bidders = load_json("bidders.json")
        bidder_id = input("Bidder ID: ").strip()
        if bidder_id not in bidders:
            print("ONLY REGISTERED BIDDERS CAN TAKE PART..")
            return True

        print("Enter the item you want and your offer.")
        item = input("Item name: ").strip()
        for attempt in range(1, 4):
            try:
                amount = float(input(f"Your bid amount (attempt {attempt}/3): "))
            except ValueError:
                print("INVALID BID NUMBER..")
                continue

            if auction.place_bid(bidder_id, amount, item):
                break
        else:
            print("GOODBYE. TOO MANY INVALID BID ATTEMPTS.")
            return False

        next_bidder = (
            input("Is another bidder ready to place a higher bid? (yes/no): ")
            .strip()
            .lower()
        )
        if next_bidder in ("yes", "y"):
            clear_terminal()
            continue
        return True


def search_bidder():
    bidder_id = input("Enter bidder ID: ").strip()
    bidder = load_json("bidders.json").get(bidder_id)
    if bidder is None:
        print("BIDDER ID NOT FOUND..")
        return
    print(f"\nBIDDER ID: {bidder_id}")
    for key, value in bidder.items():
        print(f"{key}: {value}")


def view_registered_bidders():
    bidders = load_json("bidders.json")
    print("========== REGISTERED BIDDERS ==========")
    if not bidders:
        print("NO REGISTERED BIDDERS..")
        return
    for bidder_id, bidder in bidders.items():
        print(
            f"{bidder_id}: {bidder.get('name', 'Unknown')} | "
            f"{bidder.get('contact', 'Unknown')}"
        )


def main():
    auction = AuctionItems("", "", 0)
    while True:
        clear_terminal()
        print("\n=================================================")
        print("          ONLINE AUCTION & BIDDING SYSTEM")
        print("=================================================")
        print("1. Browse Auction Items")
        print("2. Search for an Item")
        print("3. Register Bidder")
        print("4. View Registered Bidders")
        print("5. Start Auction")
        print("6. Place Bid")
        print("7. View Current Highest Bids")
        print("8. View Bidding History")
        print("9. Close Auction")
        print("10. View Auction Results")
        print("11. Exit")
        choice = input("Choose an option: ").strip()
        clear_terminal()

        if choice == "1":
            auction.browse_auction_items()
            if not continue_or_exit():
                return
        elif choice == "2":
            auction.search_items(input("Item name: "))
            if not continue_or_exit():
                return
        elif choice == "3":
            register_bidder()
            if not continue_or_exit():
                return
        elif choice == "4":
            view_registered_bidders()
            if not continue_or_exit():
                return
        elif choice == "5":
            auction.start_auction(input("Item to start: "))
            if not continue_or_exit():
                return
        elif choice == "6":
            if not place_bids(auction):
                break
            if not continue_or_exit():
                return
        elif choice == "7":
            auction.current_highest_bids()
            if not continue_or_exit():
                return
        elif choice == "8":
            auction.bidding_history(input("Item name: "))
            if not continue_or_exit():
                return
        elif choice == "9":
            auction.close_auction(input("Item to close: "))
            if not continue_or_exit():
                return
        elif choice == "10":
            auction.auction_results()
            if not continue_or_exit():
                return
        elif choice == "11":
            print("GOODBYE")
            break
        else:
            print("INVALID OPTION..")


if __name__ == "__main__":
    main()
