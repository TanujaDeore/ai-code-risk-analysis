import os
import re
from dotenv import load_dotenv
from github import Github, Auth

load_dotenv()
token = os.getenv("GITHUB_TOKEN")
g = Github(auth=Auth.Token(token))
repo = g.get_repo("psf/requests")

CLOSE_PATTERN = re.compile(r'\b(close[sd]?|fix(?:e[sd])?|resolve[sd]?)\b\s*#(\d+)', re.IGNORECASE)

pulls = repo.get_pulls(state='closed', sort='updated', direction='desc')

checked = 0
matched = 0
for pr in pulls:
    if not pr.merged:
        continue
    checked += 1
    title_match = CLOSE_PATTERN.search(pr.title or "")
    body_match = CLOSE_PATTERN.search(pr.body or "")
    if title_match or body_match:
        matched += 1
        where = "title" if title_match else "body"
        print(f"PR #{pr.number}: fix-reference found in {where} | {pr.title[:65]}")
    if checked >= 30:
        break

print(f"\n{matched}/{checked} merged PRs had a fix-reference in title or description.")