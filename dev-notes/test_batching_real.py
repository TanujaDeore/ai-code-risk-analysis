import subprocess
import time
import glob

test_files = glob.glob('openfrontio/**/*.ts', recursive=True)[:3]
print("Testing with:", test_files)

# One file, one call
start = time.time()
subprocess.run(
    ['semgrep', '--config=auto', '--json', '--quiet', test_files[0]],
    capture_output=True, text=True, encoding='utf-8', errors='replace', timeout=60
)
print(f"1 file, 1 call: {time.time() - start:.2f}s")

# Same 3 files, ONE call (batching)
start = time.time()
subprocess.run(
    ['semgrep', '--config=auto', '--json', '--quiet'] + test_files,
    capture_output=True, text=True, encoding='utf-8', errors='replace', timeout=60
)
print(f"3 files, 1 call: {time.time() - start:.2f}s")