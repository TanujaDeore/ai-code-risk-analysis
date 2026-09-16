import os
import requests
from dotenv import load_dotenv
from collections import Counter

load_dotenv()
token = os.getenv("GITHUB_TOKEN")
headers = {"Authorization": f"Bearer {token}", "Accept": "application/vnd.github.cloak-preview+json"}

repo_counts = Counter()

for page in range(1, 11):  # up to 1000 results total, 100 per page
    r = requests.get(
        "https://api.github.com/search/commits",
        params={
            "q": '"Generated with Claude Code"',
            "per_page": 100,
            "page": page,
            "sort": "committer-date",
            "order": "desc",
        },
        headers=headers,
        timeout=15,
    )
    if r.status_code != 200:
        print(f"Stopped at page {page}: {r.status_code} - {r.json().get('message')}")
        break
    items = r.json().get("items", [])
    if not items:
        break
    for item in items:
        repo_counts[item["repository"]["full_name"]] += 1

print("Top repos by AI-tagged commit count (in this sample):")
for repo, count in repo_counts.most_common(15):
    print(f"   {repo}: {count}")