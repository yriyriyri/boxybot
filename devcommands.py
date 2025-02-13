import argparse
import sqlite3

def clear_db():
    conn = sqlite3.connect("messages.db")
    c = conn.cursor()
    c.execute("DELETE FROM messages")
    conn.commit()
    conn.close()
    print("messages.db has been cleared.")

def show_stats():
    conn = sqlite3.connect("messages.db")
    c = conn.cursor()
    c.execute("SELECT COUNT(*) FROM messages")
    count = c.fetchone()[0]
    conn.close()
    print(f"Total messages in the database: {count}")

def main():
    parser = argparse.ArgumentParser(description="Development commands for boxybot.")
    parser.add_argument("command", choices=["clear_db", "stats"], help="Command to run")
    args = parser.parse_args()

    if args.command == "clear_db":
        clear_db()
    elif args.command == "stats":
        show_stats()

if __name__ == "__main__":
    main()