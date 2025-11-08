import pandas as pd
import matplotlib.pyplot as plt

# Load dataset
df = pd.read_csv("2023_nba_player_stats.csv")

# Peek at columns
print("Columns:", df.columns.tolist())
print("Shape:", df.shape)

# Clean column names (lowercase, no spaces)
df.columns = [c.strip().lower() for c in df.columns]

# Rename for consistency
if 'pname' in df.columns:
    df.rename(columns={'pname': 'player'}, inplace=True)

# Check we have 'player' and 'pts' columns
if 'player' not in df.columns or 'pts' not in df.columns:
    raise ValueError(f"Expected columns not found. Columns: {df.columns.tolist()}")

# Drop rows with missing values in key fields
df = df.dropna(subset=['player', 'pts'])

# Get top 10 scorers
top_scorers = df.sort_values(by='pts', ascending=False).head(10)
print("\nTop 10 Scorers:")
print(top_scorers[['player', 'team', 'pts', 'ast', 'reb']])

# Save top 10 to CSV
top_scorers.to_csv("top_10_scorers_2023.csv", index=False)
print("\nSaved top_10_scorers_2023.csv")

# Plot bar chart
plt.figure(figsize=(10,6))
plt.barh(top_scorers['player'][::-1], top_scorers['pts'][::-1], color='mediumseagreen')
plt.xlabel('Points per Game')
plt.title('Top 10 NBA Scorers - 2023 Season')
plt.tight_layout()
plt.savefig("top_10_scorers_chart.png")
plt.show()