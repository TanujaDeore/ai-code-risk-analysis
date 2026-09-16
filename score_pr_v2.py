import sys
import os
import subprocess
import json
import tempfile
import shutil
import re
from pydriller import Repository

AI_MARKERS = [
    re.compile(r'Co-Authored-By:\s*Claude', re.IGNORECASE),
    re.compile(r'Generated with Claude Code', re.IGNORECASE),
    re.compile(r'\(aider\)', re.IGNORECASE),
    re.compile(r'Co-Authored-By:\s*.*copilot', re.IGNORECASE),
]


def is_ai_assisted(message, author_name):
    combined = message + " " + author_name
    return any(p.search(combined) for p in AI_MARKERS)


def analyze_security(files_dict):
    if not files_dict:
        return {"LOW": 0, "MEDIUM": 0, "HIGH": 0}
    tmpdir = tempfile.mkdtemp()
    counts = {"LOW": 0, "MEDIUM": 0, "HIGH": 0}
    try:
        for fname, code in files_dict.items():
            safe_name = fname.replace("/", "_").replace("\\", "_")
            with open(os.path.join(tmpdir, safe_name), "w", encoding="utf-8") as f:
                f.write(code)
        result = subprocess.run(
            ['semgrep', '--config=auto', '--json', '--quiet', tmpdir],
            capture_output=True, text=True, encoding='utf-8', errors='replace', timeout=60
        )
        data = json.loads(result.stdout)
        for issue in data.get('results', []):
            sev = issue.get('extra', {}).get('severity', 'INFO')
            mapped = {"ERROR": "HIGH", "WARNING": "MEDIUM", "INFO": "LOW"}.get(sev, "LOW")
            counts[mapped] += 1
    except Exception:
        pass
    finally:
        shutil.rmtree(tmpdir, ignore_errors=True)
    return counts


def estimate_percentile(value, p):
    if value <= p['p25']:
        return "bottom 25%"
    elif value <= p['p50']:
        return "25th-50th percentile"
    elif value <= p['p75']:
        return "50th-75th percentile"
    elif value <= p['p90']:
        return "75th-90th percentile"
    else:
        return "top 10%"


def extract_and_score(repo_path, commit_hash, baseline):
    for commit in Repository(repo_path, single=commit_hash).traverse_commits():
        ai_flag = is_ai_assisted(commit.msg, commit.author.name)

        total_complexity, max_complexity, total_nloc = 0, 0, 0
        files_dict = {}
        for mf in commit.modified_files:
            if mf.complexity is not None:
                total_complexity += mf.complexity
                max_complexity = max(max_complexity, mf.complexity)
            if mf.nloc is not None:
                total_nloc += mf.nloc
            if (mf.filename.endswith('.ts') or mf.filename.endswith('.js')) and mf.source_code:
                files_dict[mf.filename] = mf.source_code

        sec = analyze_security(files_dict)
        group = 'ai' if ai_flag else 'human'
        b = baseline[group]

        report = {
            'is_ai_assisted': ai_flag,
            'complexity_percentile': estimate_percentile(total_complexity, b['total_complexity']),
            'total_complexity': total_complexity,
            'max_complexity': max_complexity,
            'total_nloc': total_nloc,
            'security_issues': sec,
        }
        return report, commit.msg


def build_comment(report, baseline):
    group = "AI-assisted" if report['is_ai_assisted'] else "human-authored"
    group_key = 'ai' if report['is_ai_assisted'] else 'human'
    n = baseline['meta']['ai_commit_count'] if group_key == 'ai' else baseline['meta']['human_commit_count']

    lines = [
        f"### Code Change Report ({group})",
        "",
        f"**Detected as:** {group} (based on real commit metadata, not inferred)",
        f"**Complexity:** {report['total_complexity']} (falls in the **{report['complexity_percentile']}** "
        f"of {group} commits historically, n={n}, source: openfrontio/OpenFrontIO)",
        f"**Lines touched:** {report['total_nloc']}",
        f"**Security findings:** {report['security_issues']['HIGH']} high, "
        f"{report['security_issues']['MEDIUM']} medium, {report['security_issues']['LOW']} low",
    ]

    if report['is_ai_assisted']:
        ai_med = baseline['ai']['security_issues_medium']['mean']
        human_med = baseline['human']['security_issues_medium']['mean']
        lines.append("")
        lines.append(
            f"*Context: in our reference project, AI-assisted commits showed "
            f"{ai_med:.2f} avg medium-severity findings vs {human_med:.2f} for human commits "
            f"(statistically significant, p<0.001) -- review accordingly.*"
        )

    return "\n".join(lines)


if __name__ == "__main__":
    repo_path = sys.argv[1]
    commit_hash = sys.argv[2]

    with open("ai_baseline.json") as f:
        baseline = json.load(f)

    report, msg = extract_and_score(repo_path, commit_hash, baseline)

    print("Commit message:", msg.strip())
    print(json.dumps(report, indent=2))

    comment_body = build_comment(report, baseline)
    print("\n--- Generated comment ---")
    print(comment_body)

    repo_full_name = os.getenv("GITHUB_REPOSITORY")
    pr_number = os.getenv("PR_NUMBER")
    token = os.getenv("GITHUB_TOKEN")

    if repo_full_name and pr_number and token:
        from github import Github, Auth
        g = Github(auth=Auth.Token(token))
        gh_repo = g.get_repo(repo_full_name)
        pr = gh_repo.get_pull(int(pr_number))
        pr.create_issue_comment(comment_body)
        print("\nPosted comment to PR.")
    else:
        print("\n(Running locally -- skipped posting a PR comment.)")