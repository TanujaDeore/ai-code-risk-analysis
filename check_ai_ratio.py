import os
import requests
from urllib.parse import urlparse, parse_qs
from dotenv import load_dotenv

load_dotenv()
token = os.getenv("GITHUB_TOKEN")
headers = {"Authorization": f"Bearer {token}"}

candidates = ["kamoras/civitas", "openfrontio/OpenFrontIO"]

for repo in candidates:
    r = requests.get(
        f"https://api.github.com/repos/{repo}/commits",
        params={"per_page": 1},
        headers=headers,
        timeout=15,
    )
    link = r.headers.get("Link", "")
    total_commits = "unknown"
    if 'rel="last"' in link:
        last_part = [p for p in link.split(",") if 'rel="last"' in p][0]
        url = last_part.split(";")[0].strip().strip("<>")
        params = parse_qs(urlparse(url).query)
        total_commits = params.get("page", ["unknown"])[0]

    print(f"{repo}")
    print(f"   Total commits (approx): {total_commits}")
    print()