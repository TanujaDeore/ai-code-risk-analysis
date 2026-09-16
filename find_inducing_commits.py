import os
import subprocess
import sqlite3
from pydriller import Repository
from git import Repo

REPO_URL = "https://github.com/psf/requests.git"
LOCAL_CLONE_PATH = "requests_repo"
DB_PATH = "project_data.db"

# Clone once, persistently -- skip if we've already done this before
if not os.path.exists(os.path.join(LOCAL_CLONE_PATH, ".git")):
    print("Cloning psf/requests locally (one-time, a few minutes)...")
    subprocess.run(["git", "clone", REPO_URL, LOCAL_CLONE_PATH], check=True)
else:
    print("Local clone already exists, reusing it.")

git_repo = Repo(LOCAL_CLONE_PATH)


def find_inducing_commits(fix_commit_hash):
    """For one fix-commit, trace its changed lines back to whoever last touched them."""
    inducing = set()
    for commit in Repository(LOCAL_CLONE_PATH, single=fix_commit_hash).traverse_commits():
        if not commit.parents:
            continue
        parent_hash = commit.parents[0]
        for mf in commit.modified_files:
            if mf.old_path is None:
                continue  # file was newly created, nothing earlier to blame
            deleted_lines = [ln for ln, _ in mf.diff_parsed.get('deleted', [])]
            if not deleted_lines:
                continue
            try:
                blame_result = git_repo.blame(parent_hash, mf.old_path)
            except Exception:
                continue
            line_to_commit = {}
            line_num = 1
            for blame_commit, lines in blame_result:
                for _ in lines:
                    line_to_commit[line_num] = blame_commit.hexsha
                    line_num += 1
            for ln in deleted_lines:
                if ln in line_to_commit:
                    inducing.add(line_to_commit[ln])
    return inducing


conn = sqlite3.connect(DB_PATH)
conn.execute("""
    CREATE TABLE IF NOT EXISTS inducing_commits (
        fix_commit_hash TEXT,
        inducing_commit_hash TEXT,
        PRIMARY KEY (fix_commit_hash, inducing_commit_hash)
    )
""")
conn.commit()

fix_commits = conn.execute("SELECT hash FROM fix_commits").fetchall()
print(f"Running blame-tracing on {len(fix_commits)} fix-commits...")

processed = 0
total_links = 0
for (fix_hash,) in fix_commits:
    inducing = find_inducing_commits(fix_hash)
    for ind_hash in inducing:
        conn.execute("INSERT OR IGNORE INTO inducing_commits VALUES (?, ?)", (fix_hash, ind_hash))
        total_links += 1
    processed += 1
    if processed % 20 == 0:
        print(f"...processed {processed}/{len(fix_commits)} fix-commits")
        conn.commit()

conn.commit()
conn.close()
print(f"\nDone. {processed} fix-commits processed, {total_links} inducing-commit links found.")