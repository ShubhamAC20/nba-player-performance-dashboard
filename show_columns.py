import pandas as pd
df = pd.read_csv("2023_nba_player_stats.csv", low_memory=False)
print(df.columns.tolist())