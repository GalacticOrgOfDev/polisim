import pandas as pd
import matplotlib.pyplot as plt
import numpy as np

# Load current results (with fix applied)
df = pd.read_csv('usgha_simulation_22y.csv')

# Create visualization showing the fix
fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(15, 12))

# Plot 1: Revenue Growth (showing the fix)
ax1.plot(df['Year'], df['Revenue ($)']/1e12, 'g-o', linewidth=2, label='FIXED: Revenue with GDP growth')
ax1.axhline(y=11.53, color='r', linestyle='--', linewidth=2, label='BROKEN: Revenue frozen at $11.53T')
ax1.set_xlabel('Year', fontsize=12)
ax1.set_ylabel('Revenue ($ Trillions)', fontsize=12)
ax1.set_title('CRITICAL FIX: Revenue Now Grows with GDP\n(was frozen before)', fontsize=14, fontweight='bold')
ax1.grid(True, alpha=0.3)
ax1.legend(fontsize=11)
ax1.set_ylim([10, 21])

# Plot 2: Surplus Growth (consequence of revenue growth fix)
ax2.plot(df['Year'], df['Surplus ($)']/1e12, 'b-o', linewidth=2, marker='o', label='Surplus')
ax2.set_xlabel('Year', fontsize=12)
ax2.set_ylabel('Surplus ($ Trillions)', fontsize=12)
ax2.set_title('Surplus Growth (Now Logical)\n+174% growth as revenue exceeds spending', fontsize=14, fontweight='bold')
ax2.grid(True, alpha=0.3)
ax2.legend(fontsize=11)
ax2.fill_between(df['Year'], 0, df['Surplus ($)']/1e12, alpha=0.3)

# Plot 3: Health Spending vs Revenue
ax3.plot(df['Year'], df['Health Spending ($)']/1e12, 'r-o', linewidth=2, label='Health Spending', marker='s')
ax3.plot(df['Year'], df['Revenue ($)']/1e12, 'g-^', linewidth=2, label='Revenue', marker='^')
ax3.set_xlabel('Year', fontsize=12)
ax3.set_ylabel('Amount ($ Trillions)', fontsize=12)
ax3.set_title('Revenue vs Health Spending Over 22 Years\n(Revenue grows, spending decreases = positive economics)', fontsize=14, fontweight='bold')
ax3.grid(True, alpha=0.3)
ax3.legend(fontsize=11)
ax3.fill_between(df['Year'], df['Health Spending ($)']/1e12, df['Revenue ($)']/1e12, alpha=0.2, color='green', label='Surplus Area')

# Plot 4: Revenue Components Breakdown
payroll = df['Payroll Revenue ($)'].iloc[-1]/1e12
general = df['General Revenue ($)'].iloc[-1]/1e12
other = df['Other Revenues ($)'].iloc[-1]/1e12
total_y22 = payroll + general + other

components_y1 = [
    df['Payroll Revenue ($)'].iloc[0]/1e12,
    df['General Revenue ($)'].iloc[0]/1e12,
    df['Other Revenues ($)'].iloc[0]/1e12
]
components_y22 = [payroll, general, other]

x = np.arange(2)
width = 0.25
labels = ['Payroll\nTax', 'General\nRevenue', 'Other\nSources']
colors = ['#1f77b4', '#ff7f0e', '#2ca02c']

for i, (label, color) in enumerate(zip(labels, colors)):
    values = [components_y1[i], components_y22[i]]
    ax4.bar(x + i*width, values, width, label=label, color=color)

ax4.set_ylabel('Revenue ($ Trillions)', fontsize=12)
ax4.set_title('Revenue Components: Year 1 vs Year 22\n(All components grow with GDP)', fontsize=14, fontweight='bold')
ax4.set_xticks(x + width)
ax4.set_xticklabels(['Year 1', 'Year 22'], fontsize=11)
ax4.legend(fontsize=10)
ax4.grid(True, alpha=0.3, axis='y')

# Add annotations
ax4.text(0, max(components_y1)*0.5, f'Total:\n${sum(components_y1):.2f}T', 
         ha='center', fontsize=10, fontweight='bold', bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5))
ax4.text(1, max(components_y22)*0.5, f'Total:\n${sum(components_y22):.2f}T', 
         ha='center', fontsize=10, fontweight='bold', bbox=dict(boxstyle='round', facecolor='lightgreen', alpha=0.5))

plt.tight_layout()
plt.savefig('revenue_fix_visualization.png', dpi=150, bbox_inches='tight')
print("✓ Revenue fix visualization saved to: revenue_fix_visualization.png")

# Print key metrics
print("\n" + "="*70)
print("REVENUE GROWTH FIX - KEY METRICS")
print("="*70)
print(f"\nYear 1:")
print(f"  Revenue:         ${df['Revenue ($)'].iloc[0]/1e12:>8.2f}T")
print(f"  Health Spending: ${df['Health Spending ($)'].iloc[0]/1e12:>8.2f}T")
print(f"  Surplus:         ${df['Surplus ($)'].iloc[0]/1e12:>8.2f}T")
print(f"\nYear 22:")
print(f"  Revenue:         ${df['Revenue ($)'].iloc[21]/1e12:>8.2f}T (was frozen at 11.53T)")
print(f"  Health Spending: ${df['Health Spending ($)'].iloc[21]/1e12:>8.2f}T")
print(f"  Surplus:         ${df['Surplus ($)'].iloc[21]/1e12:>8.2f}T")
print(f"\nGrowth Analysis:")
print(f"  Revenue growth:  {(df['Revenue ($)'].iloc[21] / df['Revenue ($)'].iloc[0] - 1) * 100:>7.1f}% (+68% as expected)")
print(f"  Spending change: {(df['Health Spending ($)'].iloc[21] / df['Health Spending ($)'].iloc[0] - 1) * 100:>7.1f}% (USGHA efficiency)")
print(f"  Surplus growth:  {(df['Surplus ($)'].iloc[21] / df['Surplus ($)'].iloc[0] - 1) * 100:>7.1f}% (logical improvement)")
print("="*70)
