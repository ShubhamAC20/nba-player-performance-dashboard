# app.py
import os
import pandas as pd
import streamlit as st
import plotly.express as px
from sklearn.linear_model import LinearRegression
import numpy as np

st.set_page_config(page_title="NBA Player Performance Dashboard", layout="wide")

# ---------- Load and prepare data ----------
@st.cache_data
def load_data(csv="2023_nba_player_stats.csv"):
    df = pd.read_csv(csv, low_memory=False)

    # keep abbrev for logos
    if "Team" in df.columns:
        df["team_abbrev"] = df["Team"].astype(str).str.strip()

    rename_map = {
        "PName": "Player",
        "Team": "Team",
        "GP": "Games Played",
        "PTS": "Points",
        "REB": "Rebounds",
        "AST": "Assists",
        "Min": "Minutes",
        "FG%": "Field Goal %",
        "3P%": "3PT %",
        "FT%": "Free Throw %",
        "OREB": "Off Rebounds",
        "DREB": "Def Rebounds",
    }
    df = df.rename(columns={k: v for k, v in rename_map.items() if k in df.columns})

    team_map = {
        "ATL": "Atlanta Hawks", "BOS": "Boston Celtics", "BKN": "Brooklyn Nets",
        "CHA": "Charlotte Hornets", "CHI": "Chicago Bulls", "CLE": "Cleveland Cavaliers",
        "DAL": "Dallas Mavericks", "DEN": "Denver Nuggets", "DET": "Detroit Pistons",
        "GSW": "Golden State Warriors", "HOU": "Houston Rockets", "IND": "Indiana Pacers",
        "LAC": "Los Angeles Clippers", "LAL": "Los Angeles Lakers", "MEM": "Memphis Grizzlies",
        "MIA": "Miami Heat", "MIL": "Milwaukee Bucks", "MIN": "Minnesota Timberwolves",
        "NOP": "New Orleans Pelicans", "NYK": "New York Knicks", "OKC": "Oklahoma City Thunder",
        "ORL": "Orlando Magic", "PHI": "Philadelphia 76ers", "PHX": "Phoenix Suns",
        "POR": "Portland Trail Blazers", "SAC": "Sacramento Kings", "SAS": "San Antonio Spurs",
        "TOR": "Toronto Raptors", "UTA": "Utah Jazz", "WAS": "Washington Wizards",
    }
    if "team_abbrev" in df.columns:
        df["Team"] = df["team_abbrev"].map(team_map).fillna(df["team_abbrev"])

    for col in ["Games Played", "Points", "Rebounds", "Assists", "Minutes"]:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")

    if "Points" in df.columns and "Games Played" in df.columns:
        df["Points per Game"] = df["Points"] / df["Games Played"].replace({0: pd.NA})

    df["Player"] = df.get("Player", "Unknown").astype(str).str.strip()
    df["Team"] = df.get("Team", "").astype(str).str.strip()
    return df


df = load_data()

# ---------- Page header ----------
st.title("🏀 NBA Player Performance Dashboard — 2023 Season")
st.markdown(
    "Explore 2023 NBA player statistics with logos, analytics, and live predictions."
)

# ---------- Sidebar filters ----------
st.sidebar.header("Filters")
team_list = ["All"] + sorted(df["Team"].dropna().unique().tolist())
team = st.sidebar.selectbox("Select Team", team_list)
max_gp = int(df["Games Played"].max()) if "Games Played" in df.columns else 1
min_games = st.sidebar.slider("Minimum Games Played", 0, max_gp, 10)

# ---------- Filter dataset ----------
filtered = df.copy()
if team != "All":
    filtered = filtered[filtered["Team"] == team]
filtered = filtered[filtered["Games Played"] >= min_games]

# ---------- KPIs ----------
col1, col2, col3 = st.columns(3)
col1.metric("Players (filtered)", int(filtered["Player"].nunique()))
col2.metric("Average PPG", round(filtered["Points per Game"].mean(), 2))
col3.metric("Highest PPG", round(filtered["Points per Game"].max(), 2))
st.markdown("---")

# ---------- Player search ----------
st.subheader("🔍 Search Player")
player_search = st.text_input("Type player name")
if player_search:
    res = df[df["Player"].str.contains(player_search, case=False, na=False)]
    st.dataframe(res[["Player", "Team", "Games Played", "Points per Game", "Rebounds", "Assists"]])
    st.markdown("---")

# ---------- Top players with logo cards ----------
st.subheader("Top Players — Visual")

logo_folder = "assets/logos"
def logo_path(abbrev):
    if not isinstance(abbrev, str):
        return None
    path = f"{logo_folder}/{abbrev.strip().upper()}.png"
    return path if os.path.exists(path) else None

top_n = st.sidebar.slider("Number of players to show", 5, 20, 10)
top_players = filtered.sort_values(by="Points per Game", ascending=False).head(top_n)

# CSS animation (fade-in)
st.markdown(
    """
    <style>
    [data-testid="stVerticalBlock"] div {
        animation: fadeIn 0.7s ease-in;
    }
    @keyframes fadeIn {
        from {opacity: 0;}
        to {opacity: 1;}
    }
    </style>
    """,
    unsafe_allow_html=True,
)

for _, row in top_players.iterrows():
    c1, c2, c3 = st.columns([0.12, 0.58, 0.3])
    lp = logo_path(row.get("team_abbrev", ""))
    if lp:
        c1.image(lp, width=56)
    else:
        c1.write("")

    c2.markdown(f"**{row['Player']}**  \n{row['Team']}")
    c3.markdown(
        f"PPG: **{row['Points per Game']:.1f}**  \nPTS: {int(row['Points'])}  \nREB: {int(row['Rebounds'])}  \nAST: {int(row['Assists'])}"
    )
    st.markdown("---")

# ---------- Bar chart ----------
st.subheader("Top Players — PPG Chart")
if not top_players.empty:
    fig = px.bar(
        top_players.sort_values("Points per Game"),
        x="Points per Game",
        y="Player",
        orientation="h",
        color="Team",
        height=600,
    )
    st.plotly_chart(fig, use_container_width=True)
else:
    st.info("No players to show for selected filters.")
st.markdown("---")

# ---------- Team comparison ----------
st.subheader("🏆 Compare Team A vs Team B")
team_a = st.selectbox("Team A", sorted(df["Team"].unique()), index=0)
team_b = st.selectbox("Team B", sorted(df["Team"].unique()), index=1)
compare = (
    df[df["Team"].isin([team_a, team_b])]
    .groupby("Team")[["Points per Game", "Rebounds", "Assists"]]
    .mean()
    .reset_index()
)
st.bar_chart(compare.set_index("Team"))
st.markdown("---")

# ---------- Mini ML model: Predict PPG ----------
st.sidebar.header("Predict Player PPG")
features = ["Rebounds", "Assists", "Minutes"]
train_df = df.dropna(subset=features + ["Points per Game"])
if not train_df.empty:
    model = LinearRegression().fit(train_df[features], train_df["Points per Game"])
    r = st.sidebar.slider("Rebounds", 0, 15, 5)
    a = st.sidebar.slider("Assists", 0, 15, 5)
    m = st.sidebar.slider("Minutes", 10, 40, 25)
    pred = model.predict([[r, a, m]])[0]
    st.sidebar.write(f"Expected PPG: **{pred:.1f}**")

# ---------- Insights ----------
if not df.empty:
    top_player = df.loc[df["Points per Game"].idxmax(), "Player"]
    avg_fg = np.nanmean(df.get("Field Goal %", []))
    st.info(f"🏅 {top_player} led the league in scoring this season.")
    if not np.isnan(avg_fg):
        st.info(f"🎯 League average FG%: {avg_fg:.1f}%")

st.caption("Built by Shubham Acharya | Data: Kaggle NBA 2023 | Tools: Pandas, Plotly, Streamlit, scikit-learn")