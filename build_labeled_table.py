import sqlite3
from datetime import datetime, timedelta

DB_PATH = "project_data.db"
conn = sqlite3.connect(DB_PATH)

min_date, max_date = conn.execute("SELECT MIN(author_date), MAX(author_date) FROM commits").fetchone()
print(f"Commit history spans: {min_date[:10]} to {max_date[:10]}")

risky_hashes = set(row[0] for row in conn.execute("SELECT DISTINCT inducing_commit_hash FROM inducing_commits"))
print(f"Total distinct risky (inducing) commits: {len(risky_hashes)}")

max_dt = datetime.fromisoformat(max_date)
cutoff = max_dt - timedelta(days=365)
print(f"Excluding non-risky commits after {cutoff.date()} (too recent to trust as 'clean')")

conn.execute("""
    CREATE TABLE IF NOT EXISTS labeled_commits (
        hash TEXT PRIMARY KEY,
        author_date TEXT,
        files_changed INTEGER,
        insertions INTEGER,
        deletions INTEGER,
        message_length INTEGER,
        label INTEGER
    )
""")
conn.commit()

all_commits = conn.execute(
    "SELECT hash, author_date, files_changed, insertions, deletions, message FROM commits"
).fetchall()

included = 0
excluded_recent = 0
risky_count = 0
clean_count = 0

for hash_, author_date, files_changed, insertions, deletions, message in all_commits:
    commit_dt = datetime.fromisoformat(author_date)
    is_risky = hash_ in risky_hashes

    if not is_risky and commit_dt > cutoff:
        excluded_recent += 1
        continue

    label = 1 if is_risky else 0
    conn.execute("""
        INSERT OR REPLACE INTO labeled_commits
        (hash, author_date, files_changed, insertions, deletions, message_length, label)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (hash_, author_date, files_changed, insertions, deletions, len(message), label))

    included += 1
    if label == 1:
        risky_count += 1
    else:
        clean_count += 1

conn.commit()
conn.close()

print(f"\nExcluded {excluded_recent} commits (too recent to label as clean)")
print(f"Included {included} commits in labeled dataset")
print(f"  Risky (label=1): {risky_count}")
print(f"  Clean (label=0): {clean_count}")