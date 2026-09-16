import sqlite3
from pydriller import Repository

DB_PATH = "openfrontio_data.db"
LOCAL_CLONE_PATH = "openfrontio"

conn = sqlite3.connect(DB_PATH)

existing_cols = {row[1] for row in conn.execute("PRAGMA table_info(commits)")}
for col in ["total_complexity", "max_complexity", "total_nloc"]:
    if col not in existing_cols:
        conn.execute(f"ALTER TABLE commits ADD COLUMN {col} INTEGER")
conn.commit()

all_hashes = set(row[0] for row in conn.execute("SELECT hash FROM commits"))
print(f"Computing complexity for {len(all_hashes)} commits")

processed = 0
for commit in Repository(LOCAL_CLONE_PATH).traverse_commits():
    if commit.hash not in all_hashes:
        continue

    total_complexity = 0
    max_complexity = 0
    total_nloc = 0

    for mf in commit.modified_files:
        if mf.complexity is not None:
            total_complexity += mf.complexity
            max_complexity = max(max_complexity, mf.complexity)
        if mf.nloc is not None:
            total_nloc += mf.nloc

    conn.execute("""
        UPDATE commits
        SET total_complexity = ?, max_complexity = ?, total_nloc = ?
        WHERE hash = ?
    """, (total_complexity, max_complexity, total_nloc, commit.hash))

    processed += 1
    if processed % 500 == 0:
        print(f"...processed {processed}/{len(all_hashes)} commits")
        conn.commit()

conn.commit()
conn.close()
print(f"\nDone. Added complexity features to {processed} commits.")