from pydriller import Repository

# Small real repo, just to confirm the pipeline works end-to-end
REPO_URL = "https://github.com/octocat/Hello-World.git"

print(f"Testing PyDriller on: {REPO_URL}\n")

count = 0
for commit in Repository(REPO_URL).traverse_commits():
    print(f"{commit.hash[:8]} | {commit.author.name} | {commit.msg.splitlines()[0][:60]}")
    count += 1

print(f"\nSuccess — pulled {count} commits.")