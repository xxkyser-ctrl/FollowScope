"""Interactive local report for the latest saved Instagram collection."""

import argparse
import sqlite3
import zipfile
from html import escape
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

    collection_time = collection[1]
    print(f"\nProfile: {profile}")
    print(f"Collection timestamp: {collection_time}")
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
                print(f"\n{relationship.title()} {change} ({collection_time}):")
                print("\n".join(grouped[relationship][change]) or "(none)")

    if input("\nCreate a formatted Excel workbook? [y/N] ").strip().lower() == "y":
        output = Path.cwd() / f"ib-circlio_{profile}_{datetime.now():%Y%m%d_%H%M%S}.xlsx"
        write_workbook(output, profile, collection, grouped, connection)
        print(f"Report written to: {output}")


def write_workbook(output, profile, collection, grouped, connection):
    summary_rows = [
        ["Profile", profile],
        ["Collection timestamp", collection[1]],
        ["Status", "Complete" if collection[2] else "Partial"],
        ["Followers shown by Instagram", collection[3] or "Unknown"],
        ["Followers collected", count_members(connection, collection[0], "followers")],
        ["Following shown by Instagram", collection[4] or "Unknown"],
        ["Following collected", count_members(connection, collection[0], "following")],
        ["New followers", len(grouped["followers"]["added"])],
        ["Removed followers", len(grouped["followers"]["removed"])],
        ["New following", len(grouped["following"]["added"])],
        ["Removed following", len(grouped["following"]["removed"])],
    ]
    change_rows = [["Collection timestamp", "Relationship", "Change", "Username"]]
    for relationship in ("followers", "following"):
        for change in ("added", "removed"):
            for username in grouped[relationship][change]:
                change_rows.append([collection[1], relationship.title(), change.title(), username])

    content_types = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">
<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>
<Default Extension="xml" ContentType="application/xml"/>
<Override PartName="/xl/workbook.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet.main+xml"/>
<Override PartName="/xl/worksheets/sheet1.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.worksheet+xml"/>
<Override PartName="/xl/worksheets/sheet2.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.worksheet+xml"/>
<Override PartName="/xl/styles.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.styles+xml"/>
</Types>"""
    workbook = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<workbook xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main" xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships">
<sheets><sheet name="Summary" sheetId="1" r:id="rId1"/><sheet name="Changes" sheetId="2" r:id="rId2"/></sheets></workbook>"""
    relationships = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="xl/workbook.xml"/></Relationships>"""
    workbook_relationships = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/worksheet" Target="worksheets/sheet1.xml"/>
<Relationship Id="rId2" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/worksheet" Target="worksheets/sheet2.xml"/>
<Relationship Id="rId3" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/styles" Target="styles.xml"/></Relationships>"""
    styles = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<styleSheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main">
<fonts count="2"><font><sz val="11"/><name val="Calibri"/></font><font><b/><sz val="11"/><color rgb="FFFFFFFF"/><name val="Calibri"/></font></fonts>
<fills count="3"><fill><patternFill patternType="none"/></fill><fill><patternFill patternType="gray125"/></fill><fill><patternFill patternType="solid"><fgColor rgb="FF2563EB"/><bgColor indexed="64"/></patternFill></fill></fills>
<borders count="1"><border><left/><right/><top/><bottom/><diagonal/></border></borders>
<cellXfs count="2"><xf numFmtId="0" fontId="0" fillId="0" borderId="0"/><xf numFmtId="0" fontId="1" fillId="2" borderId="0" applyFont="1" applyFill="1"/></cellXfs></styleSheet>"""

    def cell(value, style=0):
        value = escape(str(value))
        return f'<c t="inlineStr" s="{style}"><is><t>{value}</t></is></c>'

    def sheet(rows, widths):
        xml_rows = []
        for index, row in enumerate(rows, 1):
            style = 1 if index == 1 or rows is summary_rows else 0
            cells = "".join(cell(value, style if (rows is change_rows and index == 1) else 0) for value in row)
            xml_rows.append(f'<row r="{index}">{cells}</row>')
        cols = "".join(f'<col min="{i}" max="{i}" width="{width}" customWidth="1"/>' for i, width in enumerate(widths, 1))
        return f'<?xml version="1.0" encoding="UTF-8" standalone="yes"?><worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main"><cols>{cols}</cols><sheetData>{"".join(xml_rows)}</sheetData><autoFilter ref="A1:{chr(64 + len(rows[0]))}{len(rows)}"/></worksheet>'

    with zipfile.ZipFile(output, "w", zipfile.ZIP_DEFLATED) as archive:
        archive.writestr("[Content_Types].xml", content_types)
        archive.writestr("_rels/.rels", relationships)
        archive.writestr("xl/workbook.xml", workbook)
        archive.writestr("xl/_rels/workbook.xml.rels", workbook_relationships)
        archive.writestr("xl/styles.xml", styles)
        archive.writestr("xl/worksheets/sheet1.xml", sheet(summary_rows, [34, 42]))
        archive.writestr("xl/worksheets/sheet2.xml", sheet(change_rows, [28, 18, 18, 32]))


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
