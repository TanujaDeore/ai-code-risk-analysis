import subprocess
import glob

ts_files = glob.glob('openfrontio/**/*.ts', recursive=True)
test_file = ts_files[0]
print(f"Testing against: {test_file}")

result = subprocess.run(
    ['semgrep', '--config=auto', '--json', test_file],
    capture_output=True, text=True, encoding='utf-8', errors='replace', timeout=60
)
print("\nSTDOUT (first 800 chars):")
print(result.stdout[:800])
print("\nSTDERR (full):")
print(result.stderr)