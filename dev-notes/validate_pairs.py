import sqlite3
import random
from git import Repo

DB_PATH = "project_data.db"
LOCAL_CLONE_PATH = "requests_repo"

conn = sqlite3.connect(DB_PATH)
git_repo = Repo(LOCAL_CLONE_PATH)

pairs = conn.execute("""
    SELECT ic.fix_commit_hash, ic.inducing_commit_hash, fc.message
    FROM inducing_commits ic
    JOIN fix_commits fc ON ic.fix_commit_hash = fc.hash
""").fetchall()

sample = random.sample(pairs, min(10, len(pairs)))

for fix_hash, inducing_hash, fix_msg in sample:
    inducing_commit = git_repo.commit(inducing_hash)
    print(f"FIX:            {fix_hash[:8]} - {fix_msg}")
    print(f"INTRODUCED BY:  {inducing_hash[:8]} - {inducing_commit.message.strip().splitlines()[0]}")
    print(f"                (on {inducing_commit.committed_datetime.date()}, by {inducing_commit.author.name})")
    print()

conn.close()