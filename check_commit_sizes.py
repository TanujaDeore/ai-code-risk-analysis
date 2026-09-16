import sqlite3

conn = sqlite3.connect("project_data.db")
hashes = ['a1fd038d', '4a309796', '7d8b87c3', '31c0962e']  # 2 suspicious, 2 solid ones for comparison

for h in hashes:
    row = conn.execute(
        "SELECT hash, files_changed, insertions, deletions, message FROM commits WHERE hash LIKE ?",
        (h + '%',)
    ).fetchone()
    if row:
        print(f"{row[0][:8]} | files={row[1]:<4} +{row[2]}/-{row[3]:<5} | {row[4].splitlines()[0]}")