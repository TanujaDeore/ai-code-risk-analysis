import sqlite3
import pandas as pd

DB_PATH = "project_data.db"
conn = sqlite3.connect(DB_PATH)
df = pd.read_sql_query("SELECT * FROM labeled_commits", conn)
conn.close()

df['max_duplication_similarity'] = df['max_duplication_similarity'].fillna(0)
df['author_date'] = pd.to_datetime(df['author_date'], utc=True)
df = df.sort_values('author_date').reset_index(drop=True)

# Scope to 2011-2017: the window where bug-linkage signal is dense enough to trust.
# Several years after this show ZERO risky commits -- that's thinning ground truth,
# not proof the codebase became bug-free, so we don't evaluate against that period.
scoped = df[(df['author_date'] >= '2011-01-01') & (df['author_date'] < '2018-01-01')].reset_index(drop=True)
print(f"Scoped dataset (2011-2017): {len(scoped)} rows, {scoped['label'].sum()} risky ({scoped['label'].mean()*100:.1f}%)")

train_df = scoped[scoped['author_date'] < '2016-01-01']
test_df = scoped[scoped['author_date'] >= '2016-01-01']

print(f"\nTrain (2011-2015): {len(train_df)} rows, {train_df['label'].sum()} risky ({train_df['label'].mean()*100:.1f}%)")
print(f"Test  (2016-2017): {len(test_df)} rows, {test_df['label'].sum()} risky ({test_df['label'].mean()*100:.1f}%)")

train_df.to_csv("train_data.csv", index=False)
test_df.to_csv("test_data.csv", index=False)
print("\nSaved train_data.csv and test_data.csv (overwriting the earlier, unscoped versions)")