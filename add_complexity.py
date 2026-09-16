import sqlite3
from pydriller import Repository

DB_PATH = "project_data.db"
LOCAL_CLONE_PATH = "requests_repo"

conn = sqlite3.connect(DB_PATH)

labeled_hashes = set(row[0] for row in conn.execute("SELECT hash FROM labeled_commits"))
print(f"Need complexity features for {len(labeled_hashes)} labeled commits")

existing_cols = {row[1] for row in conn.execute("PRAGMA table_info(labeled_commits)")}
for col in ["total_complexity", "max_complexity", "total_nloc"]:
    if col not in existing_cols:
        conn.execute(f"ALTER TABLE labeled_commits ADD COLUMN {col} INTEGER")
conn.commit()

processed = 0
for commit in Repository(LOCAL_CLONE_PATH).traverse_commits():
    if commit.hash not in labeled_hashes:
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
        UPDATE labeled_commits
        SET total_complexity = ?, max_complexity = ?, total_nloc = ?
        WHERE hash = ?
    """, (total_complexity, max_complexity, total_nloc, commit.hash))

    processed += 1
    if processed % 500 == 0:
        print(f"...processed {processed}/{len(labeled_hashes)} labeled commits")
        conn.commit()

conn.commit()
conn.close()
print(f"\nDone. Added complexity features to {processed} commits.")