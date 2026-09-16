import sqlite3
import numpy as np
from transformers import AutoTokenizer, AutoModel
import torch
from pydriller import Repository

DB_PATH = "project_data.db"
LOCAL_CLONE_PATH = "requests_repo"

print("Loading CodeBERT (cached now, should be quick)...")
tokenizer = AutoTokenizer.from_pretrained("microsoft/codebert-base")
model = AutoModel.from_pretrained("microsoft/codebert-base")
model.eval()
print("Model ready.")

conn = sqlite3.connect(DB_PATH)
conn.execute("""
    CREATE TABLE IF NOT EXISTS method_embeddings (
        commit_hash TEXT,
        method_name TEXT,
        filename TEXT,
        embedding BLOB
    )
""")
conn.commit()

labeled_hashes = set(row[0] for row in conn.execute("SELECT hash FROM labeled_commits"))
print(f"Extracting changed methods for {len(labeled_hashes)} labeled commits")


def embed_code(code):
    inputs = tokenizer(code, return_tensors="pt", truncation=True, max_length=512)
    with torch.no_grad():
        outputs = model(**inputs)
    return outputs.last_hidden_state[:, 0, :].squeeze().numpy().astype(np.float32)


processed_commits = 0
total_methods = 0

for commit in Repository(LOCAL_CLONE_PATH).traverse_commits():
    if commit.hash not in labeled_hashes:
        continue

    for mf in commit.modified_files:
        if not mf.source_code or not mf.changed_methods:
            continue
        changed_names = set(m.name for m in mf.changed_methods)
        lines = mf.source_code.split('\n')

        for m in mf.methods:
            if m.name not in changed_names:
                continue
            snippet = '\n'.join(lines[m.start_line - 1:m.end_line])
            if not snippet.strip():
                continue
            try:
                embedding = embed_code(snippet)
            except Exception:
                continue
            conn.execute(
                "INSERT INTO method_embeddings VALUES (?, ?, ?, ?)",
                (commit.hash, m.name, mf.filename, embedding.tobytes())
            )
            total_methods += 1

    processed_commits += 1
    if processed_commits % 500 == 0:
        print(f"...processed {processed_commits}/{len(labeled_hashes)} commits, {total_methods} methods embedded so far")
        conn.commit()

conn.commit()
conn.close()
print(f"\nDone. Processed {processed_commits} commits, embedded {total_methods} changed methods.")