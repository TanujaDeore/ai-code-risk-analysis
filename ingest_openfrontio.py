import sqlite3
import re
from pydriller import Repository

REPO_PATH = "openfrontio"
DB_PATH = "openfrontio_data.db"

AI_MARKERS = [
    re.compile(r'Co-Authored-By:\s*Claude', re.IGNORECASE),
    re.compile(r'Generated with Claude Code', re.IGNORECASE),
    re.compile(r'\(aider\)', re.IGNORECASE),
    re.compile(r'Co-Authored-By:\s*.*copilot', re.IGNORECASE),
]


def is_ai_assisted(message, author_name):
    combined = message + " " + author_name
    return any(pattern.search(combined) for pattern in AI_MARKERS)


def create_table(conn):
    conn.execute("""
        CREATE TABLE IF NOT EXISTS commits (
            hash TEXT PRIMARY KEY,
            author_name TEXT,
            author_date TEXT,
            message TEXT,
            files_changed INTEGER,
            insertions INTEGER,
            deletions INTEGER,
            is_ai_assisted INTEGER
        )
    """)
    conn.commit()


def main():
    conn = sqlite3.connect(DB_PATH)
    create_table(conn)

    count = 0
    ai_count = 0
    for commit in Repository(REPO_PATH).traverse_commits():
        ai_flag = int(is_ai_assisted(commit.msg, commit.author.name))
        conn.execute("""
            INSERT OR IGNORE INTO commits
            (hash, author_name, author_date, message, files_changed, insertions, deletions, is_ai_assisted)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            commit.hash,
            commit.author.name,
            commit.author_date.isoformat(),
            commit.msg,
            len(commit.modified_files),
            commit.insertions,
            commit.deletions,
            ai_flag,
        ))
        count += 1
        ai_count += ai_flag
        if count % 1000 == 0:
            print(f"...processed {count} commits so far ({ai_count} AI-tagged)")
            conn.commit()

    conn.commit()
    conn.close()
    print(f"\nDone. Stored {count} commits, {ai_count} AI-tagged ({ai_count/count*100:.1f}%)")


if __name__ == "__main__":
    main()