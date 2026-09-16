import sqlite3
import pandas as pd
import random
from scipy import stats

DB_PATH = "openfrontio_data.db"
conn = sqlite3.connect(DB_PATH)
df = pd.read_sql_query("SELECT * FROM commits WHERE total_complexity IS NOT NULL", conn)
conn.close()

ai_df = df[df['is_ai_assisted'] == 1]
human_df = df[df['is_ai_assisted'] == 0]

# Reproduce the exact same random human sample used in add_security_ofio.py,
# so we only compare security findings against commits that were actually scanned
random.seed(42)
human_all_hashes = human_df['hash'].tolist()
human_sample_hashes = set(random.sample(human_all_hashes, min(350, len(human_all_hashes))))
ai_sample_hashes = set(ai_df['hash'].tolist())

security_ai_df = ai_df[ai_df['hash'].isin(ai_sample_hashes)]
security_human_df = human_df[human_df['hash'].isin(human_sample_hashes)]

print(f"AI-assisted commits: {len(ai_df)}")
print(f"Human commits: {len(human_df)}")
print(f"(Security comparison uses {len(security_ai_df)} AI + {len(security_human_df)} human real-sampled commits)\n")

full_pop_metrics = ['total_complexity', 'max_complexity', 'total_nloc', 'files_changed', 'insertions', 'deletions']
security_metrics = ['security_issues_low', 'security_issues_medium', 'security_issues_high']

print(f"{'Metric':<25} {'AI median':>10} {'Human median':>13} {'AI mean':>10} {'Human mean':>12} {'p-value':>10}")
for m in full_pop_metrics:
    ai_vals = ai_df[m].dropna()
    human_vals = human_df[m].dropna()
    stat, p = stats.mannwhitneyu(ai_vals, human_vals, alternative='two-sided')
    sig = "**" if p < 0.05 else ""
    print(f"{m:<25} {ai_vals.median():>10.2f} {human_vals.median():>13.2f} {ai_vals.mean():>10.2f} {human_vals.mean():>12.2f} {p:>10.4f} {sig}")

print("\n--- Security findings (sampled subset only) ---")
for m in security_metrics:
    ai_vals = security_ai_df[m].dropna()
    human_vals = security_human_df[m].dropna()
    stat, p = stats.mannwhitneyu(ai_vals, human_vals, alternative='two-sided')
    sig = "**" if p < 0.05 else ""
    print(f"{m:<25} {ai_vals.median():>10.2f} {human_vals.median():>13.2f} {ai_vals.mean():>10.2f} {human_vals.mean():>12.2f} {p:>10.4f} {sig}")