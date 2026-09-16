import sqlite3
import subprocess
import json
import tempfile
import os
from pydriller import Repository

DB_PATH = "project_data.db"
LOCAL_CLONE_PATH = "requests_repo"

conn = sqlite3.connect(DB_PATH)

existing_cols = {row[1] for row in conn.execute("PRAGMA table_info(labeled_commits)")}
for col in ["security_issues_low", "security_issues_medium", "security_issues_high"]:
    if col not in existing_cols:
        conn.execute(f"ALTER TABLE labeled_commits ADD COLUMN {col} INTEGER DEFAULT 0")
conn.commit()

labeled_hashes = set(row[0] for row in conn.execute("SELECT hash FROM labeled_commits"))
print(f"Running static analysis for {len(labeled_hashes)} labeled commits")


def analyze_code(code):
    with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False, encoding='utf-8') as f:
        f.write(code)
        temp_path = f.name

    counts = {"LOW": 0, "MEDIUM": 0, "HIGH": 0}
    try:
        result = subprocess.run(
            ['bandit', '-f', 'json', temp_path],
            capture_output=True, text=True, timeout=10
        )
        data = json.loads(result.stdout)
        for issue in data.get('results', []):
            sev = issue.get('issue_severity', 'LOW')
            counts[sev] = counts.get(sev, 0) + 1
    except Exception:
        pass
    finally:
        os.unlink(temp_path)

    return counts


processed = 0
for commit in Repository(LOCAL_CLONE_PATH).traverse_commits():
    if commit.hash not in labeled_hashes:
        continue

    total = {"LOW": 0, "MEDIUM": 0, "HIGH": 0}
    for mf in commit.modified_files:
        if not mf.filename.endswith('.py') or not mf.source_code:
            continue
        counts = analyze_code(mf.source_code)
        for k in total:
            total[k] += counts[k]

    conn.execute("""
        UPDATE labeled_commits
        SET security_issues_low = ?, security_issues_medium = ?, security_issues_high = ?
        WHERE hash = ?
    """, (total["LOW"], total["MEDIUM"], total["HIGH"], commit.hash))

    processed += 1
    if processed % 500 == 0:
        print(f"...processed {processed}/{len(labeled_hashes)} commits")
        conn.commit()

conn.commit()
conn.close()
print(f"\nDone. Ran static analysis on {processed} commits.")
