import subprocess
import time
import glob

test_file = glob.glob('openfrontio/**/*.ts', recursive=True)[0]
print(f"Testing against: {test_file}\n")

configs = ['auto', 'p/typescript']
for config in configs:
    start = time.time()
    result = subprocess.run(
        ['semgrep', f'--config={config}', '--json', '--quiet', test_file],
        capture_output=True, text=True, encoding='utf-8', errors='replace', timeout=60
    )
    elapsed = time.time() - start
    print(f"--config={config}: {elapsed:.2f}s")