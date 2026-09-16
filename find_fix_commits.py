import sqlite3
import re

DB_PATH = "project_data.db"

CLOSE_PATTERN = re.compile(r'\b(close[sd]?|fix(?:e[sd])?|resolve[sd]?)\b\s*#(\d+)', re.IGNORECASE)

def create_table(conn):
    conn.execute("""
        CREATE TABLE IF NOT EXISTS fix_commits (
            hash TEXT PRIMARY KEY,
            issue_number INTEGER,
            keyword_used TEXT,
            message TEXT
        )
    """)
    conn.commit()

def main():
    conn = sqlite3.connect(DB_PATH)
    create_table(conn)

    all_commits = conn.execute("SELECT hash, message FROM commits").fetchall()

    found = 0
    for commit_hash, message in all_commits:
        match = CLOSE_PATTERN.search(message)
        if match:
            keyword, issue_num = match.groups()
            conn.execute("""
                INSERT OR IGNORE INTO fix_commits (hash, issue_number, keyword_used, message)
                VALUES (?, ?, ?, ?)
            """, (commit_hash, int(issue_num), keyword.lower(), message.splitlines()[0][:80]))
            found += 1

    conn.commit()

    total = len(all_commits)
    print(f"Scanned {total} commits.")
    print(f"Found {found} fix-commits ({found/total*100:.1f}% of all commits).")

    print("\nSample fix-commits found:")
    for row in conn.execute("SELECT hash, issue_number, keyword_used, message FROM fix_commits LIMIT 5"):
        print(f"  #{row[1]:<6} ({row[2]:<7}) {row[0][:8]} - {row[3]}")

    conn.close()

if __name__ == "__main__":
    main()