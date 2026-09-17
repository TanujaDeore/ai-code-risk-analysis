import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

fig, axes = plt.subplots(1, 2, figsize=(11, 5))

metrics1 = ['Complexity', 'Lines touched\n(÷10)', 'Files changed\n(×10)']
ai_vals1 = [197, 174.9, 50]
human_vals1 = [59, 43.0, 20]

x = range(len(metrics1))
width = 0.35
axes[0].bar([i - width/2 for i in x], ai_vals1, width, label='AI-assisted', color='#e07b39')
axes[0].bar([i + width/2 for i in x], human_vals1, width, label='Human', color='#4a7ba6')
axes[0].set_xticks(list(x))
axes[0].set_xticklabels(metrics1)
axes[0].set_title('Code Size & Complexity (median)')
axes[0].legend()

metrics2 = ['Low severity', 'Medium severity']
ai_vals2 = [0.27, 0.24]
human_vals2 = [0.08, 0.04]

x2 = range(len(metrics2))
axes[1].bar([i - width/2 for i in x2], ai_vals2, width, label='AI-assisted', color='#e07b39')
axes[1].bar([i + width/2 for i in x2], human_vals2, width, label='Human', color='#4a7ba6')
axes[1].set_xticks(list(x2))
axes[1].set_xticklabels(metrics2)
axes[1].set_title('Security Findings (mean per commit)')
axes[1].legend()

fig.suptitle('AI-Assisted vs Human Commits — OpenFrontIO (n=317 AI, n=350 human sample)', fontsize=12)
plt.tight_layout()
plt.savefig('docs/ai_vs_human_chart.png', dpi=150)
print("Saved chart")