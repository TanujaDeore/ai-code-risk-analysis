import pandas as pd
import xgboost as xgb
from sklearn.metrics import precision_score, recall_score, f1_score, roc_auc_score, confusion_matrix

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
print(f"Class imbalance ratio (scale_pos_weight): {scale_pos_weight:.1f}")

model = xgb.XGBClassifier(
    n_estimators=200,
    max_depth=4,
    learning_rate=0.05,
    scale_pos_weight=scale_pos_weight,
    eval_metric='logloss',
    random_state=42
)
model.fit(X_train, y_train)

y_pred = model.predict(X_test)
y_prob = model.predict_proba(X_test)[:, 1]

precision = precision_score(y_test, y_pred)
recall = recall_score(y_test, y_pred)
f1 = f1_score(y_test, y_pred)
auc = roc_auc_score(y_test, y_prob)
cm = confusion_matrix(y_test, y_pred)

print(f"\nTest set results ({len(y_test)} commits, {y_test.sum()} actually risky):")
print(f"  Precision: {precision:.3f}")
print(f"  Recall:    {recall:.3f}")
print(f"  F1:        {f1:.3f}")
print(f"  AUC-ROC:   {auc:.3f}")
print(f"\nConfusion matrix:")
print(f"                 Predicted clean   Predicted risky")
print(f"  Actually clean      {cm[0][0]:>6}            {cm[0][1]:>6}")
print(f"  Actually risky      {cm[1][0]:>6}            {cm[1][1]:>6}")

model.save_model('risk_model.json')
print("\nModel saved to risk_model.json")