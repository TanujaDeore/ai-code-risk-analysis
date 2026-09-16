import subprocess
import json

# vite.config.ts already gave us 2 real findings with --config=auto -- use it as ground truth
test_file = "openfrontio/vite.config.ts"

for config in ["auto", "p/typescript"]:
    result = subprocess.run(
        ['semgrep', f'--config={config}', '--json', '--quiet', test_file],
        capture_output=True, text=True, encoding='utf-8', errors='replace', timeout=60
    )
    try:
        data = json.loads(result.stdout)
        print(f"--config={config}: {len(data.get('results', []))} findings, {len(data.get('errors', []))} errors")
        if data.get('errors'):
            print("   First error:", data['errors'][0].get('message', '')[:200])
    except json.JSONDecodeError:
        print(f"--config={config}: FAILED to parse JSON. Raw stdout (first 300 chars):")
        print(result.stdout[:300])