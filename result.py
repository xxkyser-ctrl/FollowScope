"""Interactive local report for the latest saved Instagram collection."""

import argparse
import csv
import sqlite3
from datetime import datetime
from pathlib import Path


def choose_profile(connection, requested):
    if requested:
        return requested.strip().lower()
    rows = connection.execute(
        "SELECT username FROM profiles ORDER BY username"
    ).fetchall()
    if not rows:
        raise ValueError("No collections exist yet.")
    if len(rows) == 1:
        return rows[0][0]
    print("Profiles:")
    for index, row in enumerate(rows, 1):
        print(f"{index}. {row[0]}")
    choice = int(input("Choose a profile number: "))
    return rows[choice - 1][0]


def report(connection, profile):
    collection = connection.execute(
        """SELECT c.id, c.captured_at, c.complete, c.followers_header_total,
                  c.following_header_total
           FROM collections c JOIN profiles p ON p.id = c.profile_id
           WHERE p.username = ? ORDER BY c.captured_at DESC, c.id DESC LIMIT 1""",
        (profile,),
    ).fetchone()
    if not collection:
        raise ValueError(f"No collection found for {profile}.")
    changes = connection.execute(
        """SELECT u.username, mc.relationship, mc.change
           FROM membership_changes mc JOIN users u ON u.id = mc.user_id
           WHERE mc.collection_id = ? ORDER BY mc.relationship, mc.change, u.username""",
        (collection[0],),
    ).fetchall()
    grouped = {
        "followers": {"added": [], "removed": []},
        "following": {"added": [], "removed": []},
    }
    for username, relationship, change in changes:
        grouped[relationship][change].append(username)

    print(f"\nProfile: {profile}")
    print(f"Collection time: {collection[1]}")
    print(f"Status: {'complete' if collection[2] else 'partial (not used as a comparison baseline)'}")
    print(f"Followers shown by Instagram: {collection[3] or 'unknown'}")
    print(f"Followers collected: {count_members(connection, collection[0], 'followers')}")
    print(f"Following shown by Instagram: {collection[4] or 'unknown'}")
    print(f"Following collected: {count_members(connection, collection[0], 'following')}")
    for relationship in ("followers", "following"):
        print(f"\n{relationship.title()} changes:")
        print(f"  New: {len(grouped[relationship]['added'])}")
        print(f"  Removed: {len(grouped[relationship]['removed'])}")

    if input("\nShow changed usernames? [y/N] ").strip().lower() == "y":
        for relationship in ("followers", "following"):
            for change in ("added", "removed"):
                print(f"\n{relationship.title()} {change}:")
                print("\n".join(grouped[relationship][change]) or "(none)")

    if input("\nCreate an Excel-compatible CSV report? [y/N] ").strip().lower() == "y":
        output = Path.cwd() / f"ib-circlio_{profile}_{datetime.now():%Y%m%d_%H%M%S}.csv"
        with output.open("w", newline="", encoding="utf-8-sig") as file:
            writer = csv.writer(file)
            writer.writerow(["profile", "collection_datetime", "relationship", "change", "username"])
            for relationship in ("followers", "following"):
                for change in ("added", "removed"):
                    for username in grouped[relationship][change]:
                        writer.writerow([profile, collection[1], relationship, change, username])
        print(f"Report written to: {output}")


def count_members(connection, collection_id, relationship):
    return connection.execute(
        "SELECT COUNT(*) FROM collection_memberships WHERE collection_id = ? AND relationship = ?",
        (collection_id, relationship),
    ).fetchone()[0]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--data-dir", required=True)
    parser.add_argument("--profile")
    args = parser.parse_args()
    database = Path(args.data_dir) / "instagram.db"
    if not database.exists():
        raise ValueError("The SQLite database does not exist.")
    connection = sqlite3.connect(database)
    try:
        profile = choose_profile(connection, args.profile)
        report(connection, profile)
    finally:
        connection.close()


if __name__ == "__main__":
    try:
        main()
    except (OSError, ValueError, IndexError, sqlite3.Error) as error:
        print(f"Error: {error}")
        raise SystemExit(1)
