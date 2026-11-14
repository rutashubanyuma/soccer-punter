"""Free picks have moved to our website; this page only points people there."""

import streamlit as st

URL = "https://sportspunter.co.tz"

st.set_page_config(page_title="The Sports Punter", page_icon="⚽")
st.title("⚽ The Sports Punter")
st.subheader("Free picks have moved to our website")
st.write("We no longer publish picks here. Visit our website for today's free picks, jackpots and results.")
st.link_button("Visit sportspunter.co.tz", URL, type="primary")
