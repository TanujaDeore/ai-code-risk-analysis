import pandas as pd
import xgboost as xgb
from sklearn.metrics import precision_score, recall_score

FEATURE_COLS = [
    'files_changed', 'insertions', 'deletions', 'message_length',
    'total_complexity', 'max_complexity', 'total_nloc',
    'max_duplication_similarity',
    'security_issues_low', 'security_issues_medium', 'security_issues_high'
]

train_df = pd.read_csv('train_data.csv')
test_df = pd.read_csv('test_data.csv')

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

print("Precision/recall at different probability thresholds:")
print(f"{'Threshold':>10} {'Flagged':>8} {'Precision':>10} {'Recall':>8}")
for threshold in [0.5, 0.6, 0.7, 0.8, 0.9, 0.95, 0.99]:
    y_pred_t = (y_prob >= threshold).astype(int)
    flagged = y_pred_t.sum()
    prec = precision_score(y_test, y_pred_t, zero_division=0)
    rec = recall_score(y_test, y_pred_t, zero_division=0)
    print(f"{threshold:>10} {flagged:>8} {prec:>10.3f} {rec:>8.3f}")

print("\nFeature importance:")
importances = sorted(zip(FEATURE_COLS, model.feature_importances_), key=lambda x: -x[1])
for name, imp in importances:
    print(f"  {name:<30} {imp:.3f}")