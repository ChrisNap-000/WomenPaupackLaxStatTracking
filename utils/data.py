# =============================================================================
# utils/data.py
# =============================================================================
# Data loading, caching, and merging helpers shared across all page modules.
# Keeping these here avoids duplicating cache logic and merge logic in each page.
# =============================================================================

import re
import pandas as pd
import streamlit as st


# -----------------------------------------------------------------------------
# DATA LOADING
# GID values are pulled from st.secrets to keep them out of source code.
# The gid_set argument accepts either "real" or "test" to select the
# appropriate set of GIDs from secrets.
# -----------------------------------------------------------------------------
@st.cache_data
def load_data(main_url, schedule_url, fact_gid, players_gid, schedule_gid):
    """
    Loads data directly from Google Sheets.
    All URLs and GIDs are resolved from secrets before this function is called,
    so st.cache_data can hash them cleanly as plain strings.
    """

    def get_csv_url(url, gid):
        match = re.search(r"/spreadsheets/d/([a-zA-Z0-9-_]+)", url)
        if not match:
            raise ValueError("Invalid Google Sheets URL")
        sheet_id = match.group(1)
        return f"https://docs.google.com/spreadsheets/d/{sheet_id}/export?format=csv&gid={gid}"

    fact     = pd.read_csv(get_csv_url(main_url, fact_gid))
    players  = pd.read_csv(get_csv_url(main_url, players_gid))
    schedule = pd.read_csv(get_csv_url(schedule_url, schedule_gid))

    fact["Date"]     = pd.to_datetime(fact["Date"])
    schedule["Date"] = pd.to_datetime(schedule["Date"])

    for df in [fact, schedule, players]:
        num_cols = df.select_dtypes(include="number").columns
        df[num_cols] = df[num_cols].fillna(0)

    return fact, schedule, players


# -----------------------------------------------------------------------------
# MERGE HELPER
# Joins the fact table with player info and opponent/result info from schedule.
# Called at the top of each page function to build the full working DataFrame.
# -----------------------------------------------------------------------------
def get_merged(fact, players, schedule):
    """
    Returns a merged DataFrame combining:
      - fact      : one row per player per game
      - players   : player metadata (name, position, jersey)
      - schedule  : opponent name and win/loss result per game date
    """
    df = fact.merge(players, on="PlayerID", how="left")
    df = df.merge(
        schedule[["Date", "OpponentName", "Won?"]],
        on="Date",
        how="left"
    )
    return df