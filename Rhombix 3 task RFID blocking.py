import random
import time
import csv
import os

# File paths for persistent storage
CARDS_FILE = "registered_cards.csv"
BLOCKED_FILE = "blocked_cards.csv"
LOG_FILE = "scan_log.csv"

def load_cards():
    # Load registered cards from CSV
    cards = {}
    if os.path.exists(CARDS_FILE):
        with open(CARDS_FILE, "r") as f:
            for row in csv.reader(f):
                if len(row) == 2:
                    cards[row[0]] = row[1]
    return cards

def save_cards(cards):
    # Save registered cards to CSV
    with open(CARDS_FILE, "w", newline="") as f:
        writer = csv.writer(f)
        for card_id, owner in cards.items():
            writer.writerow([card_id, owner])

def load_blocked():
    # Load blocked cards from CSV
    blocked = []
    if os.path.exists(BLOCKED_FILE):
        with open(BLOCKED_FILE, "r") as f:
            for row in csv.reader(f):
                if row:
                    blocked.append(row[0])
    return blocked

def save_blocked(blocked):
    # Save blocked cards to CSV
    with open(BLOCKED_FILE, "w", newline="") as f:
        writer = csv.writer(f)
        for card_id in blocked:
            writer.writerow([card_id])

def log_scan(card_id, status):
    # Append scan entry to log file
    timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
    with open(LOG_FILE, "a", newline="") as f:
        csv.writer(f).writerow([timestamp, card_id, status])
    return timestamp

def generate_random_card_id():
    # Simulate a random RFID scan
    return f"CARD-{random.randint(1000, 9999)}"

def scan_card(card_id, cards, blocked):
    if card_id in blocked:
        owner = cards.get(card_id, "Unknown")
        ts = log_scan(card_id, "BLOCKED")
        print(f"[{ts}] ❌ RFID BLOCKED   | Card: {card_id} | Owner: {owner}")

    elif card_id in cards:
        owner = cards[card_id]
        ts = log_scan(card_id, "ALLOWED")
        print(f"[{ts}] ✅ ACCESS GRANTED | Card: {card_id} | Owner: {owner}")

    else:
        ts = log_scan(card_id, "SUSPICIOUS")
        print(f"[{ts}] ⚠️  UNKNOWN CARD   | Card: {card_id} | Flagged for review")

def add_card(cards):
    # Add new card dynamically
    card_id = input("Enter new Card ID (e.g. CARD-1234): ").strip().upper()
    if card_id in cards:
        print(f"⚠️  Card {card_id} already exists.")
        return
    owner = input("Enter owner name: ").strip()
    cards[card_id] = owner
    save_cards(cards)
    print(f"✅ Card {card_id} registered for {owner}.")

def remove_card(cards, blocked):
    # Remove a card from registered list
    card_id = input("Enter Card ID to remove: ").strip().upper()
    if card_id not in cards:
        print(f"⚠️  Card {card_id} not found.")
        return
    del cards[card_id]
    if card_id in blocked:
        blocked.remove(card_id)
        save_blocked(blocked)
    save_cards(cards)
    print(f"🗑️  Card {card_id} removed successfully.")

def block_card(card_id, blocked):
    # Block a card
    if card_id in blocked:
        print(f"⚠️  Card {card_id} is already blocked.")
    else:
        blocked.append(card_id)
        save_blocked(blocked)
        print(f"🔒 Card {card_id} BLOCKED successfully.")

def unblock_card(card_id, blocked):
    # Unblock a card
    if card_id not in blocked:
        print(f"⚠️  Card {card_id} is not blocked.")
    else:
        blocked.remove(card_id)
        save_blocked(blocked)
        print(f"🔓 Card {card_id} UNBLOCKED successfully.")

def show_log():
    # Display scan log from file
    if not os.path.exists(LOG_FILE):
        print("No scan log found.")
        return
    print("\n--- Scan Log ---")
    with open(LOG_FILE, "r") as f:
        for row in csv.reader(f):
            if row:
                print(f"  [{row[0]}] {row[1]} -> {row[2]}")

def show_cards(cards, blocked):
    # Display all registered cards
    if not cards:
        print("No cards registered.")
        return
    print("\n--- Registered Cards ---")
    for card_id, owner in cards.items():
        status = "🔴 BLOCKED" if card_id in blocked else "🟢 Active"
        print(f"  {card_id} | {owner} | {status}")

def menu():
    print("\n==============================")
    print("   RFID Blocking System")
    print("==============================")
    print("1.  Scan a card manually")
    print("2.  Simulate random scan")
    print("3.  Add new card")
    print("4.  Remove a card")
    print("5.  Block a card")
    print("6.  Unblock a card")
    print("7.  View scan log")
    print("8.  View all registered cards")
    print("9.  Exit")
    print("------------------------------")

def main():
    print("🛡️  RFID Blocking System — Rhombix Technologies")

    # Load data from files on startup
    cards = load_cards()
    blocked = load_blocked()

    # Add default cards if first run
    if not cards:
        cards = {
            "CARD-4829": "Ali Hassan",
            "CARD-7731": "Sara Khan",
            "CARD-1102": "Usman Malik",
            "CARD-9984": "Ayesha Noor",
        }
        save_cards(cards)

    if not blocked:
        blocked = ["CARD-9984"]
        save_blocked(blocked)

    while True:
        menu()
        choice = input("Enter choice: ").strip()

        if choice == "1":
            card_id = input("Enter Card ID (e.g. CARD-4829): ").strip().upper()
            scan_card(card_id, cards, blocked)

        elif choice == "2":
            card_id = generate_random_card_id()
            print(f"\n📡 Simulating scan for: {card_id}")
            scan_card(card_id, cards, blocked)

        elif choice == "3":
            add_card(cards)

        elif choice == "4":
            remove_card(cards, blocked)

        elif choice == "5":
            card_id = input("Enter Card ID to block: ").strip().upper()
            block_card(card_id, blocked)

        elif choice == "6":
            card_id = input("Enter Card ID to unblock: ").strip().upper()
            unblock_card(card_id, blocked)

        elif choice == "7":
            show_log()

        elif choice == "8":
            show_cards(cards, blocked)

        elif choice == "9":
            print("\nExiting... Stay secure! 🔐")
            break

        else:
            print("❌ Invalid choice. Try again.")

main()
