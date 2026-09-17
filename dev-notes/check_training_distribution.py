import pandas as pd

train_df = pd.read_csv('train_data.csv')
clean = train_df[train_df['label'] == 0]

print("Distribution of feature values among CLEAN commits in training data (psf/requests):")
print(clean[['files_changed', 'insertions', 'deletions', 'total_nloc', 'max_complexity']].describe())