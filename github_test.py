import os
from dotenv import load_dotenv
from github import Github, Auth          # ← added Auth here

load_dotenv()  # reads your .env file and loads GITHUB_TOKEN into the environment
token = os.getenv("GITHUB_TOKEN")

g = Github(auth=Auth.Token(token))        # ← changed from Github(token)
repo = g.get_repo("psf/requests")

print("Repo:", repo.full_name)
print("Stars:", repo.stargazers_count)
print("Open issues:", repo.open_issues_count)

remaining, limit = g.rate_limiting
print(f"API calls remaining: {remaining}/{limit}")