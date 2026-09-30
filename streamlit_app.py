"""
Streamlit web page for the soccer app.

Shows the picks made by the midnight routine (src/model/global_picks.py),
read from data/global_picks_log.csv. The GitHub Action commits that file
every night, and Streamlit Community Cloud redeploys on each commit, so the
page stays current without an API key or the database.

Run locally:  streamlit run streamlit_app.py
"""

from pathlib import Path

import pandas as pd
import streamlit as st

ROOT = Path(__file__).resolve().parent
LOG_CSV = ROOT / "data" / "global_picks_log.csv"
LOCAL_TZ = "Africa/Dar_es_Salaam"

st.set_page_config(page_title="Soccer Picks", page_icon="⚽", layout="wide")


@st.cache_data(ttl=600)
def load_picks():
    df = pd.read_csv(LOG_CSV, dtype=str).fillna("")
    df["prob"] = pd.to_numeric(df["prob"], errors="coerce")
    df["kickoff"] = pd.to_datetime(df["kickoff_utc"], utc=True).dt.tz_convert(LOCAL_TZ)
    return df.sort_values("kickoff")


def show_table(df):
    table = pd.DataFrame({
        "Kickoff (EAT)": df["kickoff"].dt.strftime("%a %d %b %H:%M"),
        "League": df["country"] + " - " + df["league"],
        "Match": df["home"] + " vs " + df["away"],
        "Pick": df["selection"],
        "Market": df["family"],
        "Chance": df["prob"],
        "Free": df["free_pick"].map({"yes": "⭐", "no": ""}),
        "Result": df["status"],
        "Score": df["score"],
    })
    st.dataframe(
        table,
        hide_index=True,
        use_container_width=True,
        column_config={"Chance": st.column_config.ProgressColumn(
            "Chance", format="percent", min_value=0.0, max_value=1.0)},
    )


def record_line(df):
    settled = df[df["status"].isin(["won", "lost"])]
    won = (settled["status"] == "won").sum()
    total = len(settled)
    rate = f"{won / total:.0%}" if total else "-"
    return won, total - won, rate


st.title("⚽ Soccer Picks")
st.caption("Picks from the global rating model, refreshed every night at 00:05 EAT.")

if not LOG_CSV.exists():
    st.error("No picks yet: data/global_picks_log.csv is missing.")
    st.stop()

picks = load_picks()

# Sidebar filters
st.sidebar.header("Filter")
search = st.sidebar.text_input("Search team or league")
continents = sorted(c for c in picks["continent"].unique() if c)
chosen = st.sidebar.multiselect("Continent", continents)
free_only = st.sidebar.checkbox("Free picks only")

view = picks
if search:
    s = search.lower()
    view = view[view[["home", "away", "league", "country"]]
                .apply(lambda col: col.str.lower().str.contains(s, regex=False)).any(axis=1)]
if chosen:
    view = view[view["continent"].isin(chosen)]
if free_only:
    view = view[view["free_pick"] == "yes"]

# Track record
won, lost, rate = record_line(picks)
free_won, free_lost, free_rate = record_line(picks[picks["free_pick"] == "yes"])
c1, c2, c3, c4 = st.columns(4)
c1.metric("Won", won)
c2.metric("Lost", lost)
c3.metric("Hit rate", rate)
c4.metric("Free picks hit rate", free_rate, help=f"{free_won} won, {free_lost} lost")

upcoming, results = st.tabs(["Pending", "Results"])
with upcoming:
    pending = view[view["status"] == "pending"]
    if pending.empty:
        st.info("No pending picks match your filters.")
    else:
        show_table(pending)
with results:
    settled = view[view["status"] != "pending"].sort_values("kickoff", ascending=False)
    if settled.empty:
        st.info("No settled picks match your filters.")
    else:
        show_table(settled)

st.caption("Probabilities are model estimates, not guarantees. Please bet responsibly.")
