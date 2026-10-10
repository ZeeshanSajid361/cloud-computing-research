import matplotlib.pyplot as plt
import os

def create_preliminary_chart():
    # Data from the preliminary fault-injection results
    labels = ['Baseline (Static 30s)', 'Proposed (Adaptive)']
    loss_percentages = [14.77, 0.83]
    colors = ['#e63946', '#2a9d8f'] # Red for baseline, Green for adaptive

    fig, ax = plt.subplots(figsize=(7, 5))
    bars = ax.bar(labels, loss_percentages, color=colors, edgecolor='black', width=0.5)

    # Add numeric labels on top of the bars
    for bar in bars:
        height = bar.get_height()
        ax.annotate(f'{height}%',
                    xy=(bar.get_x() + bar.get_width() / 2, height),
                    xytext=(0, 3),  # 3 points vertical offset
                    textcoords="offset points",
                    ha='center', va='bottom', fontweight='bold', fontsize=11)

    # Formatting
    ax.set_ylabel('State Loss at Failover (%)', fontweight='bold', fontsize=12)
    ax.set_title('Preliminary Results: Failover Data Loss Comparison', fontweight='bold', fontsize=14)
    ax.set_ylim(0, 18) # Leave room for the label
    ax.yaxis.grid(True, linestyle='--', alpha=0.7)
    
    # Save as both PDF (for the paper) and PNG (for the README)
    os.makedirs('results', exist_ok=True)
    plt.tight_layout()
    plt.savefig('results/d2_preliminary_results.pdf', format='pdf', dpi=300)
    plt.savefig('results/d2_preliminary_results.png', format='png', dpi=300)
    print("Saved graphs to results/d2_preliminary_results.pdf and .png")

if __name__ == '__main__':
    create_preliminary_chart()
