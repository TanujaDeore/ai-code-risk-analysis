import sqlite3
import pandas as pd
import json
import random

DB_PATH = "openfrontio_data.db"
conn = sqlite3.connect(DB_PATH)
df = pd.read_sql_query("SELECT * FROM commits WHERE total_complexity IS NOT NULL", conn)
conn.close()

ai_df = df[df['is_ai_assisted'] == 1]
human_df = df[df['is_ai_assisted'] == 0]

metrics = ['total_complexity', 'max_complexity', 'total_nloc', 'files_changed', 'insertions']

baseline = {'ai': {}, 'human': {}}
for m in metrics:
    baseline['ai'][m] = {
        'p25': float(ai_df[m].quantile(0.25)), 'p50': float(ai_df[m].quantile(0.50)),
        'p75': float(ai_df[m].quantile(0.75)), 'p90': float(ai_df[m].quantile(0.90)),
    }
    baseline['human'][m] = {
        'p25': float(human_df[m].quantile(0.25)), 'p50': float(human_df[m].quantile(0.50)),
        'p75': float(human_df[m].quantile(0.75)), 'p90': float(human_df[m].quantile(0.90)),
    }

random.seed(42)
human_sample_hashes = set(random.sample(human_df['hash'].tolist(), min(350, len(human_df))))
ai_sample_hashes = set(ai_df['hash'].tolist())
sec_ai_df = ai_df[ai_df['hash'].isin(ai_sample_hashes)]
sec_human_df = human_df[human_df['hash'].isin(human_sample_hashes)]

for m in ['security_issues_low', 'security_issues_medium', 'security_issues_high']:
    baseline['ai'][m] = {'mean': float(sec_ai_df[m].mean())}
    baseline['human'][m] = {'mean': float(sec_human_df[m].mean())}

baseline['meta'] = {
    'source_repo': 'openfrontio/OpenFrontIO',
    'ai_commit_count': int(len(ai_df)),
    'human_commit_count': int(len(human_df)),
}

with open('ai_baseline.json', 'w') as f:
    json.dump(baseline, f, indent=2)
print("Saved ai_baseline.json")
print(json.dumps(baseline['meta'], indent=2))