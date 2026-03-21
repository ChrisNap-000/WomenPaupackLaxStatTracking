# =============================================================================
# pages/box_stats.py
# =============================================================================
# PAGE 4 — BOX STATS
# A full aggregated stat table — one row per player for the filtered games.
# Includes a totals row at the bottom, similar to a traditional box score.
# =============================================================================

import streamlit as st

from utils.data import get_merged
from utils.ui import date_hierarchy_filter


# -----------------------------------------------------------------------------
# BOX STATS PAGE CLASS
# Encapsulates all rendering logic for the Box Stats page.
# Instantiate with the three DataFrames, then call .render().
# -----------------------------------------------------------------------------
class BoxStatsPage:
    """
    Renders the Box Stats page (full aggregated stat table).

    Parameters
    ----------
    fact     : pd.DataFrame — fact table (one row per player per game)
    schedule : pd.DataFrame — schedule/results table (one row per game)
    players  : pd.DataFrame — player dimension table
    """

    # CHANGED: Replaced sorted(players["Position"].unique().tolist()) with a
    # fixed list of clean position keywords. The old approach pulled raw values
    # from the data (e.g. "Midfield/Defense") into the dropdown, which caused
    # comparison errors. Now the dropdown shows clean labels and str.contains()
    # matches any position value that contains the selected keyword.
    POSITIONS = ["All", "Attack", "Midfield", "Defense", "Goalie", "Undefined"]

    # Columns to include in the final display table, in display order
    DISPLAY_COLS = [
        "PlayerName", "Position", "GP", "Goals", "Assists", "Points", "PPG",
        "GBs", "TOs", "CTOs", "Shots", "Shot%",
        "WomanUpGoals", "WomanDownGoals",
        "DrawAtts", "DrawControls", "Draw%",
        "ShotsFaced", "Saves", "Save%", "MinsServed", "12m", "Green", "Yellow", "Red"
    ]

    # Shorter display-friendly column header overrides
    RENAME_MAP = {
        "PlayerName":     "Player",
        "WomanUpGoals":   "W-Up G",
        "WomanDownGoals": "W-Dn G",
        "DrawAtts":       "Draw Atts",
        "DrawControls":   "Draw Ctrl",
        "ShotsFaced":     "Shots Faced",
        "MinsServed":     "Pen Mins",
    }

    def __init__(self, fact, schedule, players):
        self.fact     = fact
        self.schedule = schedule
        self.players  = players
        # Build the full merged DataFrame once
        self.df = get_merged(fact, players, schedule)

    # -------------------------------------------------------------------------
    # PUBLIC ENTRY POINT
    # -------------------------------------------------------------------------
    def render(self):
        """Render the complete Box Stats page top-to-bottom."""
        st.title("Box Stats")

        # --- FILTERS ---
        st.subheader("Filters")

        # Top row: opponent, position, and name search
        fcol1, fcol2, fcol3 = st.columns(3)
        opponents = ["All"] + sorted(self.schedule["OpponentName"].unique().tolist())

        sel_opp  = fcol1.selectbox("Opponent", opponents,      key="bs_opp")
        sel_pos  = fcol2.selectbox("Position", self.POSITIONS, key="bs_pos")
        sel_name = fcol3.text_input("Player Name Search",      key="bs_name")

        # Date hierarchy: Year -> Month -> Day, each narrowing the next.
        # date_hierarchy_filter returns an already-filtered schedule DataFrame.
        st.caption("Date Filter")
        sched_f = date_hierarchy_filter(self.schedule, key_prefix="bs")

        # Apply opponent filter on top of the date hierarchy result
        if sel_opp != "All":
            sched_f = sched_f[sched_f["OpponentName"] == sel_opp]

        df_f = self.df[self.df["Date"].isin(sched_f["Date"])]

        if sel_pos != "All":
            # CHANGED: Replaced == sel_pos with str.contains() so that hybrid
            # position values like "Midfield/Defense" match when "Midfield" or
            # "Defense" is selected, rather than requiring an exact string match.
            df_f = df_f[df_f["Position"].str.contains(sel_pos, case=False, na=False)]
        if sel_name:
            # str.contains() does a partial, case-insensitive match
            df_f = df_f[df_f["PlayerName"].str.contains(sel_name, case=False, na=False)]

        st.divider()
        self._render_table(df_f)

    # -------------------------------------------------------------------------
    # PRIVATE SECTION RENDERERS
    # -------------------------------------------------------------------------

    def _render_table(self, df_f):
        """
        Build the aggregated stat table and display it with a TOTAL row appended.
        """
        # ---------------------------------
        # ------------Box Stats------------
        # ---------------------------------
        # Group by player and sum all numeric stats across all filtered games.
        # "nunique" on Date gives us games played (counts distinct game dates).
        agg = df_f.groupby(["PlayerName", "Position"]).agg(
            GP             = ("Date",           "nunique"),
            Goals          = ("Goals",          "sum"),
            Assists        = ("Assists",         "sum"),
            GBs            = ("GBs",            "sum"),
            TOs            = ("TOs",            "sum"),
            CTOs           = ("CTOs",           "sum"),
            DrawAtts       = ("DrawAtts",       "sum"),
            DrawControls   = ("DrawControls",   "sum"),
            Shots          = ("Shots",          "sum"),
            WomanUpGoals   = ("WomanUpGoals",   "sum"),
            WomanDownGoals = ("WomanDownGoals", "sum"),
            ShotsFaced     = ("ShotsFaced",     "sum"),
            Saves          = ("Saves",          "sum"),
            MinsServed     = ("MinsServed",     "sum"),
        ).reset_index()

        # --- PENALTY TYPE COUNTS (done separately since .agg() doesn't support conditional counts) ---
        for pen in ["12m", "Green", "Yellow", "Red"]:
            agg[pen] = (
                df_f[df_f["PenType"] == pen]
                .groupby("PlayerName")["PenType"]
                .count()
                .reindex(agg["PlayerName"])
                .fillna(0)
                .astype(int)
                .values
            )

        # Calculated columns — derived from the aggregated totals above
        agg["Points"] = agg["Goals"] + agg["Assists"]
        agg["PPG"]    = (agg["Points"] / agg["GP"]).round(1)

        # Format percentages as strings with "%" so they display cleanly in the table
        agg["Shot%"] = agg.apply(
            lambda r: f"{round(r['Goals'] / r['Shots'] * 100, 1)}%" if r["Shots"] else "0%", axis=1
        )
        agg["Save%"] = agg.apply(
            lambda r: f"{round(r['Saves'] / r['ShotsFaced'] * 100, 1)}%" if r["ShotsFaced"] else "0%", axis=1
        )
        agg["Draw%"] = agg.apply(
            lambda r: f"{round(r['DrawControls'] / r['DrawAtts'] * 100, 1)}%" if r["DrawAtts"] else "0%", axis=1
        )

        # Apply column ordering and rename for display
        table = (
            agg[self.DISPLAY_COLS]
            .rename(columns=self.RENAME_MAP)
            .sort_values("Points", ascending=False)
        )

        # --- TOTALS ROW ---
        # Build a single-row dict with summed values for all numeric columns
        numeric_cols = [
            "Goals", "Assists", "Points", "GBs", "TOs", "CTOs",
            "Shots", "W-Up G", "W-Dn G", "Draw Atts", "Draw Ctrl",
            "Shots Faced", "Saves", "Pen Mins", "12m", "Green", "Yellow", "Red"
        ]

        totals = {col: "" for col in table.columns}   # Start with empty strings
        for col in numeric_cols:
            if col in table.columns:
                totals[col] = table[col].sum()         # Fill in numeric sums

        totals["Player"]   = "TOTAL"
        totals["Position"] = "Team"
        totals["GP"]       = table["GP"].max()       # Total games is the max GP among players, not the sum
        totals["PPG"]      = round(totals["Points"] / totals["GP"], 1) if totals["GP"] else 0
        totals["Shot%"]    = f"{round(totals['Goals'] / totals['Shots'] * 100, 1)}%"   if totals["Shots"]       else "0%"
        totals["Draw%"]    = f"{round(totals['Draw Ctrl'] / totals['Draw Atts'] * 100, 1)}%" if totals["Draw Atts"] else "0%"
        totals["Save%"]    = f"{round(totals['Saves'] / totals['Shots Faced'] * 100, 1)}%"  if totals["Shots Faced"] else "0%"

        # Convert the totals dict to a single-row DataFrame and append to the table
        import pandas as pd
        totals_df = pd.DataFrame([totals])
        final_df  = pd.concat([table, totals_df], ignore_index=True)
        # Drop extra blank rows
        final_df = final_df.dropna(how="all")

        # Display as an interactive Streamlit dataframe (sortable columns, scrollable)
        st.dataframe(
            final_df,
            use_container_width=True,
            height=520,
            hide_index=True,
        )


# -----------------------------------------------------------------------------
# MODULE-LEVEL FUNCTION
# Called by app.py — keeps the call signature identical to the original.
# -----------------------------------------------------------------------------
def page_box_stats(fact, schedule, players):
    """Entry point called by PaupackWLaxApp.py to render the Box Stats page."""
    BoxStatsPage(fact, schedule, players).render()