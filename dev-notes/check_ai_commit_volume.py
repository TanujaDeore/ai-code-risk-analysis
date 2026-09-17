import os
import requests
from dotenv import load_dotenv

load_dotenv()
token = os.getenv("GITHUB_TOKEN")
headers = {"Authorization": f"Bearer {token}"}

candidates = [
    "openfrontio/OpenFrontIO",
    "chainguard-sandbox/go-linear",
    "kamoras/civitas",
]

for repo in candidates:
    r = requests.get(
        "https://api.github.com/search/commits",
        params={"q": f'"Generated with Claude Code" repo:{repo}'},
        headers={**headers, "Accept": "application/vnd.github.cloak-preview+json"},
        timeout=15,
    )
    ai_count = r.json().get("total_count", "error")

    r2 = requests.get(f"https://api.github.com/repos/{repo}", headers=headers, timeout=15)
    repo_info = r2.json()

    print(f"{repo}")
    print(f"   Stars: {repo_info.get('stargazers_count')}  |  Language: {repo_info.get('language')}")
    print(f"   AI-tagged commits found: {ai_count}")
    print()