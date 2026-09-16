import sqlite3
import numpy as np
from collections import defaultdict

DB_PATH = "project_data.db"
conn = sqlite3.connect(DB_PATH)

rows = conn.execute("SELECT commit_hash, method_name, filename, embedding FROM method_embeddings").fetchall()
print(f"Loaded {len(rows)} method embeddings")

embeddings = np.array([np.frombuffer(r[3], dtype=np.float32) for r in rows])
commit_hashes = [r[0] for r in rows]

# Normalize each vector to unit length -- a dot product between two unit vectors equals cosine similarity
norms = np.linalg.norm(embeddings, axis=1, keepdims=True)
normalized = embeddings / norms

# One matrix multiply computes every pairwise similarity at once
similarity_matrix = normalized @ normalized.T
np.fill_diagonal(similarity_matrix, -1)  # exclude comparing a function to itself
max_similarity_per_method = similarity_matrix.max(axis=1)

# Roll up to commit level: a commit's score = its single most-duplicated changed function
commit_max_dup = defaultdict(float)
for hash_, sim in zip(commit_hashes, max_similarity_per_method):
    commit_max_dup[hash_] = max(commit_max_dup[hash_], float(sim))

print(f"Computed duplication scores for {len(commit_max_dup)} commits")

existing_cols = {row[1] for row in conn.execute("PRAGMA table_info(labeled_commits)")}
if "max_duplication_similarity" not in existing_cols:
    conn.execute("ALTER TABLE labeled_commits ADD COLUMN max_duplication_similarity REAL")
conn.commit()

for hash_, score in commit_max_dup.items():
    conn.execute("UPDATE labeled_commits SET max_duplication_similarity = ? WHERE hash = ?", (score, hash_))

conn.commit()
conn.close()
print("Done.")