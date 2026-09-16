import os
import re
import requests
from dotenv import load_dotenv
from github import Github, Auth

load_dotenv()
token = os.getenv("GITHUB_TOKEN")

g = Github(auth=Auth.Token(token))
repo = g.get_repo("psf/requests")

CLOSE_PATTERN = re.compile(r'\b(close[sd]?|fix(?:e[sd])?|resolve[sd]?)\b\s*#(\d+)', re.IGNORECASE)

GRAPHQL_QUERY = """
query($owner: String!, $repo: String!, $number: Int!) {
  repository(owner: $owner, name: $repo) {
    pullRequest(number: $number) {
      closingIssuesReferences(first: 5) {
        nodes { number }
      }
    }
  }
}
"""
headers = {"Authorization": f"Bearer {token}"}

pulls = repo.get_pulls(state='closed', sort='updated', direction='desc')

checked = 0
regex_matches = 0
graphql_matches = 0

for pr in pulls:
    if not pr.merged:
        continue
    checked += 1

    # Method A: our original text-keyword search
    text_match = CLOSE_PATTERN.search((pr.title or "") + " " + (pr.body or ""))
    if text_match:
        regex_matches += 1

    # Method B: ask GitHub directly which issues this PR actually closes
    variables = {"owner": "psf", "repo": "requests", "number": pr.number}
    resp = requests.post(
        "https://api.github.com/graphql",
        json={"query": GRAPHQL_QUERY, "variables": variables},
        headers=headers,
        timeout=15,
    ).json()
    linked = resp.get("data", {}).get("repository", {}).get("pullRequest", {}).get("closingIssuesReferences", {}).get("nodes", [])
    has_link = len(linked) > 0
    if has_link:
        graphql_matches += 1

    print(f"PR #{pr.number}: regex={bool(text_match)!s:5} graphql_linked={has_link!s:5} ({len(linked)} issue(s))")

    if checked >= 30:
        break

print(f"\nOut of {checked} merged PRs:")
print(f"  Regex (text keyword) found:   {regex_matches}")
print(f"  GraphQL (true linkage) found: {graphql_matches}")