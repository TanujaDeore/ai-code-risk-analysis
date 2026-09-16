import time
from transformers import AutoTokenizer, AutoModel
import torch

print("Loading CodeBERT (first run downloads ~500MB, cached after that)...")
start_load = time.time()
tokenizer = AutoTokenizer.from_pretrained("microsoft/codebert-base")
model = AutoModel.from_pretrained("microsoft/codebert-base")
model.eval()
print(f"Model loaded in {time.time() - start_load:.1f}s")

sample_functions = [
    "def add(a, b):\n    return a + b",
    "def subtract(a, b):\n    return a - b",
    "def is_even(n):\n    return n % 2 == 0",
    "def get_max(items):\n    return max(items) if items else None",
    "def flatten(nested):\n    return [x for sub in nested for x in sub]",
]

print("\nTiming embedding generation...")
start = time.time()
for code in sample_functions:
    inputs = tokenizer(code, return_tensors="pt", truncation=True, max_length=512)
    with torch.no_grad():
        outputs = model(**inputs)
    embedding = outputs.last_hidden_state[:, 0, :].squeeze()
elapsed = time.time() - start

per_function = elapsed / len(sample_functions)
print(f"\nEmbedded {len(sample_functions)} functions in {elapsed:.2f}s")
print(f"Average: {per_function:.3f}s per function")
print(f"Estimated time for 20,000 functions: {per_function * 20000 / 60:.1f} minutes")