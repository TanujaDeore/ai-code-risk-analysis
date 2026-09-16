import pandas as pd
import xgboost as xgb
import shap

FEATURE_COLS = [
    'files_changed', 'insertions', 'deletions', 'message_length',
    'total_complexity', 'max_complexity', 'total_nloc',
    'max_duplication_similarity',
    'security_issues_low', 'security_issues_medium', 'security_issues_high'
]

train_df = pd.read_csv('train_data.csv')
test_df = pd.read_csv('test_data.csv').reset_index(drop=True)

X_train = train_df[FEATURE_COLS]
y_train = train_df['label']
X_test = test_df[FEATURE_COLS]
y_test = test_df['label']

scale_pos_weight = (y_train == 0).sum() / (y_train == 1).sum()
model = xgb.XGBClassifier(
    n_estimators=200, max_depth=4, learning_rate=0.05,
    scale_pos_weight=scale_pos_weight, eval_metric='logloss', random_state=42
)
model.fit(X_train, y_train)

y_prob = model.predict_proba(X_test)[:, 1]
y_pred = (y_prob >= 0.5).astype(int)

test_df['predicted'] = y_pred
test_df['probability'] = y_prob

true_positives = test_df[(test_df['label'] == 1) & (test_df['predicted'] == 1)]
false_positives = test_df[(test_df['label'] == 0) & (test_df['predicted'] == 1)]

explainer = shap.TreeExplainer(model)


def explain_row(idx, row):
    sv = explainer(X_test.iloc[[idx]])
    contributions = list(zip(FEATURE_COLS, X_test.iloc[idx].values, sv.values[0]))
    contributions.sort(key=lambda x: -abs(x[2]))

    print(f"\nCommit: {row['hash'][:8]}  |  Actually risky: {bool(row['label'])}  |  Model's probability: {row['probability']:.3f}")
    print("Top factors driving this prediction:")
    for name, value, shap_val in contributions[:5]:
        direction = "pushed toward RISKY" if shap_val > 0 else "pushed toward clean"
        print(f"   {name:<28} value={value:<8.2f} contribution={shap_val:+.3f}  ({direction})")


print("=== TRUE POSITIVES (correctly flagged as risky) ===")
for idx, row in true_positives.head(3).iterrows():
    explain_row(idx, row)

print("\n=== FALSE POSITIVES (flagged as risky, actually clean) ===")
for idx, row in false_positives.head(3).iterrows():
    explain_row(idx, row)