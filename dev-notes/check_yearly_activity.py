import sqlite3
import pandas as pd

DB_PATH = "project_data.db"
conn = sqlite3.connect(DB_PATH)
df = pd.read_sql_query("SELECT * FROM labeled_commits", conn)
conn.close()

df['author_date'] = pd.to_datetime(df['author_date'], utc=True)
df['year'] = df['author_date'].dt.year

yearly = df.groupby('year').agg(
    total_commits=('label', 'count'),
    risky_commits=('label', 'sum')
)
yearly['risky_pct'] = (yearly['risky_commits'] / yearly['total_commits'] * 100).round(1)
pd.set_option('display.max_rows', None)
print(yearly)