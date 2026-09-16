import sqlite3
import subprocess
import json
import tempfile
import os
import shutil
import random
from pydriller import Repository

DB_PATH = "openfrontio_data.db"
LOCAL_CLONE_PATH = "openfrontio"
SAMPLE_SIZE_PER_GROUP = 350

conn = sqlite3.connect(DB_PATH)

existing_cols = {row[1] for row in conn.execute("PRAGMA table_info(commits)")}
for col in ["security_issues_low", "security_issues_medium", "security_issues_high"]:
    if col not in existing_cols:
        conn.execute(f"ALTER TABLE commits ADD COLUMN {col} INTEGER DEFAULT 0")
conn.commit()

ai_hashes = [row[0] for row in conn.execute("SELECT hash FROM commits WHERE is_ai_assisted = 1")]
human_all = [row[0] for row in conn.execute("SELECT hash FROM commits WHERE is_ai_assisted = 0")]
random.seed(42)
human_sample = random.sample(human_all, min(SAMPLE_SIZE_PER_GROUP, len(human_all)))

target_hashes = set(ai_hashes) | set(human_sample)
print(f"Analyzing {len(ai_hashes)} AI-assisted + {len(human_sample)} sampled human commits = {len(target_hashes)} total")


def analyze_commit_files(files_dict):
    tmpdir = tempfile.mkdtemp()
    counts = {"LOW": 0, "MEDIUM": 0, "HIGH": 0}
    try:
        for fname, code in files_dict.items():
            safe_name = fname.replace("/", "_").replace("\\", "_")
            with open(os.path.join(tmpdir, safe_name), "w", encoding="utf-8") as f:
                f.write(code)

        result = subprocess.run(
            ['semgrep', '--config=auto', '--json', '--quiet', tmpdir],
            capture_output=True, text=True, encoding='utf-8', errors='replace', timeout=60
        )
        data = json.loads(result.stdout)
        for issue in data.get('results', []):
            sev = issue.get('extra', {}).get('severity', 'INFO')
            mapped = {"ERROR": "HIGH", "WARNING": "MEDIUM", "INFO": "LOW"}.get(sev, "LOW")
            counts[mapped] += 1
    except Exception:
        pass
    finally:
        shutil.rmtree(tmpdir, ignore_errors=True)

    return counts


processed = 0
for commit in Repository(LOCAL_CLONE_PATH).traverse_commits():
    if commit.hash not in target_hashes:
        continue

    files_dict = {}
    for mf in commit.modified_files:
        if (mf.filename.endswith('.ts') or mf.filename.endswith('.js')) and mf.source_code:
            files_dict[mf.filename] = mf.source_code

    counts = analyze_commit_files(files_dict) if files_dict else {"LOW": 0, "MEDIUM": 0, "HIGH": 0}

    conn.execute("""
        UPDATE commits
        SET security_issues_low = ?, security_issues_medium = ?, security_issues_high = ?
        WHERE hash = ?
    """, (counts["LOW"], counts["MEDIUM"], counts["HIGH"], commit.hash))

    processed += 1
    if processed % 50 == 0:
        print(f"...processed {processed}/{len(target_hashes)} commits")
        conn.commit()

conn.commit()
conn.close()
print(f"\nDone. Ran static analysis on {processed} commits.")