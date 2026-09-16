import sqlite3
from pydriller import Repository

REPO_URL = "https://github.com/psf/requests.git"
DB_PATH = "project_data.db"

def create_table(conn):
    conn.execute("""
        CREATE TABLE IF NOT EXISTS commits (
            hash TEXT PRIMARY KEY,
            author_name TEXT,
            author_date TEXT,
            message TEXT,
            files_changed INTEGER,
            insertions INTEGER,
            deletions INTEGER
        )
    """)
    conn.commit()

def main():
    conn = sqlite3.connect(DB_PATH)
    create_table(conn)

    count = 0
    for commit in Repository(REPO_URL).traverse_commits():
        conn.execute("""
            INSERT OR IGNORE INTO commits
            (hash, author_name, author_date, message, files_changed, insertions, deletions)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            commit.hash,
            commit.author.name,
            commit.author_date.isoformat(),
            commit.msg,
            len(commit.modified_files),
            commit.insertions,
            commit.deletions,
        ))
        count += 1
        if count % 200 == 0:
            print(f"...processed {count} commits so far")
            conn.commit()

    conn.commit()
    conn.close()
    print(f"\nDone. Stored {count} commits in {DB_PATH}")

if __name__ == "__main__":
    main()