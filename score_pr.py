import sys
import subprocess
import json
import tempfile
import os
import xgboost as xgb
import shap
import numpy as np
from pydriller import Repository

FEATURE_COLS = [
    'files_changed', 'insertions', 'deletions', 'message_length',
    'total_complexity', 'max_complexity', 'total_nloc',
    'max_duplication_similarity',
    'security_issues_low', 'security_issues_medium', 'security_issues_high'
]


def analyze_code(code):
    with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False, encoding='utf-8') as f:
        f.write(code)
        temp_path = f.name
    counts = {"LOW": 0, "MEDIUM": 0, "HIGH": 0}
    try:
        result = subprocess.run(['bandit', '-f', 'json', temp_path], capture_output=True, text=True, timeout=10)
        data = json.loads(result.stdout)
        for issue in data.get('results', []):
            sev = issue.get('issue_severity', 'LOW')
            counts[sev] = counts.get(sev, 0) + 1
    except Exception:
        pass
    finally:
        os.unlink(temp_path)
    return counts


def extract_features(repo_path, commit_hash):
    for commit in Repository(repo_path, single=commit_hash).traverse_commits():
        total_complexity, max_complexity, total_nloc = 0, 0, 0
        sec_totals = {"LOW": 0, "MEDIUM": 0, "HIGH": 0}

        for mf in commit.modified_files:
            if mf.complexity is not None:
                total_complexity += mf.complexity
                max_complexity = max(max_complexity, mf.complexity)
            if mf.nloc is not None:
                total_nloc += mf.nloc
            if mf.filename.endswith('.py') and mf.source_code:
                counts = analyze_code(mf.source_code)
                for k in sec_totals:
                    sec_totals[k] += counts[k]

        return {
            'files_changed': len(commit.modified_files),
            'insertions': commit.insertions,
            'deletions': commit.deletions,
            'message_length': len(commit.msg),
            'total_complexity': total_complexity,
            'max_complexity': max_complexity,
            'total_nloc': total_nloc,
            'max_duplication_similarity': 0.0,  # not computed live -- kept fast for CI, see note below
            'security_issues_low': sec_totals["LOW"],
            'security_issues_medium': sec_totals["MEDIUM"],
            'security_issues_high': sec_totals["HIGH"],
        }, commit.msg


def build_comment(prob, contributions, msg):
    lines = [
        f"### 🔍 Code Debt Risk Check",
        f"**Risk score: {prob:.2f}** (informational — not a blocker)",
        f"",
        f"Top factors behind this score:",
    ]
    for name, value, shap_val in contributions[:5]:
        direction = "⬆️ toward risky" if shap_val > 0 else "⬇️ toward clean"
        lines.append(f"- `{name}` = {value:.2f} ({direction})")
    lines.append("")
    lines.append("*Note: duplication similarity isn't computed live to keep this check fast — treated as unknown (0) here.*")
    return "\n".join(lines)


if __name__ == "__main__":
    repo_path = sys.argv[1]
    commit_hash = sys.argv[2]

    features, msg = extract_features(repo_path, commit_hash)
    print("Extracted features:")
    for k, v in features.items():
        print(f"   {k}: {v}")

    model = xgb.XGBClassifier()
    model.load_model("risk_model.json")

    X = np.array([[features[c] for c in FEATURE_COLS]])
    prob = model.predict_proba(X)[0][1]

    explainer = shap.TreeExplainer(model)
    sv = explainer(X)
    contributions = sorted(zip(FEATURE_COLS, X[0], sv.values[0]), key=lambda x: -abs(x[2]))

    print(f"\nCommit message: {msg.strip()}")
    print(f"Risk score: {prob:.3f}")
    print("Top contributing factors:")
    for name, value, shap_val in contributions[:5]:
        direction = "toward RISKY" if shap_val > 0 else "toward clean"
        print(f"   {name:<28} value={value:<8.2f} ({direction})")

    repo_full_name = os.getenv("GITHUB_REPOSITORY")
    pr_number = os.getenv("PR_NUMBER")
    token = os.getenv("GITHUB_TOKEN")

    if repo_full_name and pr_number and token:
        from github import Github, Auth
        g = Github(auth=Auth.Token(token))
        repo = g.get_repo(repo_full_name)
        pr = repo.get_pull(int(pr_number))
        comment_body = build_comment(prob, contributions, msg)
        pr.create_issue_comment(comment_body)
        print("\nPosted comment to PR.")
    else:
        print("\n(Running locally -- skipped posting a PR comment.)")