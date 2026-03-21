# =============================================================================
# pages/player_stats.py
# =============================================================================
# PAGE 2 — PLAYER STATS
# Deep-dive on a single player: KPIs, shooting %, goals over time, penalties.
# =============================================================================

import plotly.graph_objects as go
import streamlit as st

from utils.config import ACCENT, DARK, MUTED, PURPLE, PURPLE_D, TEXT, apply_layout
from utils.data import get_merged
from utils.ui import date_hierarchy_filter, show_kpi


# -----------------------------------------------------------------------------
# PLAYER STATS PAGE CLASS
# Encapsulates all rendering logic for the Player Stats page.
# Instantiate with the three DataFrames, then call .render().
# -----------------------------------------------------------------------------
class PlayerStatsPage:
    """
    Renders the Player Stats page.

    Parameters
    ----------
    fact     : pd.DataFrame — fact table (one row per player per game)
    schedule : pd.DataFrame — schedule/results table (one row per game)
    players  : pd.DataFrame — player dimension table
    """

    def __init__(self, fact, schedule, players):
        self.fact     = fact
        self.schedule = schedule
        self.players  = players
        # Build the full merged DataFrame once; all chart methods read from it.
        self.df = get_merged(fact, players, schedule)

    # -------------------------------------------------------------------------
    # PUBLIC ENTRY POINT
    # -------------------------------------------------------------------------
    def render(self):
        """Render the complete Player Stats page top-to-bottom."""
        st.title("Player Stats")

        # --- FILTERS ---
        st.subheader("Filters")
        fcol1, fcol2 = st.columns(2)

        player_list = sorted(self.players["PlayerName"].unique().tolist())
        opponents   = ["All"] + sorted(self.schedule["OpponentName"].unique().tolist())

        sel_player = fcol1.selectbox("Player",   player_list, key="ps_player")
        sel_opp    = fcol2.selectbox("Opponent", opponents,   key="ps_opp")

        # Date hierarchy: Year -> Month -> Day, each narrowing the next.
        # date_hierarchy_filter returns an already-filtered schedule DataFrame.
        st.caption("Date Filter")

        # Filter schedule, then filter fact table to matching dates
        sched_f = self.schedule.copy()
        sched_f = date_hierarchy_filter(self.fact, key_prefix="ts")
        if sel_opp != "All":
            sched_f = sched_f[sched_f["OpponentName"] == sel_opp]

        df_f = self.df[
            (self.df["PlayerName"] == sel_player) &
            (self.df["Date"].isin(sched_f["Date"]))
        ]

        if df_f.empty:
            st.warning("No data found for the selected filters.")
            return

        # Pass filtered data to each section
        self._render_player_card_and_kpis(df_f, sel_player)
        st.divider()
        self._render_charts(df_f, sched_f)
        st.divider()
        self._render_additional_stats(df_f)

    # -------------------------------------------------------------------------
    # PRIVATE SECTION RENDERERS
    # -------------------------------------------------------------------------

    def _render_player_card_and_kpis(self, df_f, sel_player):
        """
        Show the player card (jersey + position) and five KPI tiles.
        """
        # --- PLAYER INFO LOOKUP ---
        # .iloc[0] gets the first (and should be only) row for this player
        player_info = self.players[self.players["PlayerName"] == sel_player].iloc[0]
        jersey = player_info["JerseyNum"]
        pos    = player_info["Position"]

        # ----------------------------------
        # ---------KPI Calculations---------
        # ----------------------------------
        gp      = len(df_f)                         # Games played = number of rows for this player
        goals   = int(df_f["Goals"].sum())
        assists = int(df_f["Assists"].sum())
        points  = goals + assists
        ppg     = round(points / gp, 1) if gp else 0
        gbs     = int(df_f["GBs"].sum())

        # --- PLAYER CARD + KPIs ---
        st.divider()

        # Player card (jersey + position) sits in its own column alongside the KPIs
        pc, k1, k2, k3, k4, k5 = st.columns([1, 1.2, 1.2, 1.2, 1.2, 1.2])

        with pc:
            # st.container(border=True) draws a simple outlined box — no HTML needed
            with st.container(border=True):
                st.metric(label="Jersey", value=f"#{jersey}")
                st.caption(f"**Position:** {pos}")

        with k1: show_kpi("PPG",          ppg)
        with k2: show_kpi("Points",       points)
        with k3: show_kpi("Goals",        goals)
        with k4: show_kpi("Assists",      assists)
        with k5: show_kpi("Ground Balls", gbs)

    def _render_charts(self, df_f, sched_f):
        """
        ROW 2: Shooting % donut + % of Points gauge on the left;
               Stats over time line + Penalty minutes area chart on the right.
        """
        left_col, right_col = st.columns(2)

        # --- LEFT COLUMN ---
        with left_col:
            self._chart_shooting_donut(df_f)
            self._chart_points_from_gauge(df_f)

        # --- RIGHT COLUMN ---
        with right_col:
            self._chart_stats_over_time(df_f, sched_f)
            self._chart_penalty_minutes(df_f, sched_f)

    def _render_additional_stats(self, df_f):
        """
        Additional KPI tiles displayed in two rows of five at the bottom.
        Includes turnovers, woman-up goals, penalty card counts, etc.
        """
        st.subheader("Additional Stats")

        # Count penalties by card type — value_counts() tallies each unique PenType.
        # .get(type, 0) safely returns 0 if that card type never appears for this player.
        pen_counts = df_f["PenType"].value_counts()
        gp         = len(df_f)

        # List of (label, value) tuples — easy to add or remove stats here
        extra_stats = [
            ("Caused TOs",       int(df_f["CTOs"].sum())),
            ("Turnovers",        int(df_f["TOs"].sum())),
            ("Shots PG",         round(df_f["Shots"].sum() / gp, 1) if gp else 0),
            ("Woman-Up Goals",   int(df_f["WomanUpGoals"].sum())),
            ("Woman-Down Goals", int(df_f["WomanDownGoals"].sum())),
            ("Games Played",     gp),
            ("12m Penalties",    int(pen_counts.get("12m",    0))),
            ("Green Cards",      int(pen_counts.get("Green",  0))),
            ("Yellow Cards",     int(pen_counts.get("Yellow", 0))),
            ("Red Cards",        int(pen_counts.get("Red",    0))),
        ]

        # Display in two rows of 5 so the layout stays readable
        row1 = extra_stats[:5]
        row2 = extra_stats[5:]

        cols1 = st.columns(len(row1))
        for i, (label, value) in enumerate(row1):
            with cols1[i]:
                show_kpi(label, value)

        st.write("")  # Small vertical gap between rows

        cols2 = st.columns(len(row2))
        for i, (label, value) in enumerate(row2):
            with cols2[i]:
                show_kpi(label, value)

    # -------------------------------------------------------------------------
    # INDIVIDUAL CHART METHODS
    # -------------------------------------------------------------------------

    def _chart_shooting_donut(self, df_f):
        """
        Shooting % donut: Goals as a share of total shots taken.
        """
        # ----------------------------------
        # ------Shooting % Donut Chart------
        # ----------------------------------
        st.subheader("Shooting %")
        goals  = int(df_f["Goals"].sum())
        shots  = int(df_f["Shots"].sum())
        missed = max(shots - goals, 0)   # max() prevents a negative value if data is off

        # "Shots<br>Missed" forces a line break in the slice label so both
        # labels fit vertically within their slices at the same orientation.
        fig_shoot = go.Figure(go.Pie(
            labels=["Goals", "Shots<br>Missed"],
            values=[goals, missed],
            hole=0.55,
            marker=dict(colors=[PURPLE, "#1a1a3e"]),
            textinfo="label+percent",
            textfont=dict(color=TEXT),
        ))
        apply_layout(fig_shoot, height=500, showlegend=False)
        st.plotly_chart(fig_shoot, use_container_width=True, config={"displayModeBar": False})

    def _chart_points_from_gauge(self, df_f):
        """
        Toggle gauge: % of points that came from Goals vs from Assists.
        State stored in session_state.ptg_mode.
        """
        # % OF POINTS FROM GOALS / ASSISTS GAUGE
        # Toggle button swaps between the two modes.
        # Goals %  = goals / points * 100
        # Assists % = 1 - Goals % (the remainder of points not from goals)
        if "ptg_mode" not in st.session_state:
            st.session_state.ptg_mode = "Goals"

        goals   = int(df_f["Goals"].sum())
        assists = int(df_f["Assists"].sum())
        points  = goals + assists

        gc, ac = st.columns(2)
        if gc.button("Goals",   key="ptg_goals",
                     type="primary" if st.session_state.ptg_mode == "Goals" else "secondary",
                     use_container_width=True):
            st.session_state.ptg_mode = "Goals";   st.rerun()
        if ac.button("Assists", key="ptg_assists",
                     type="primary" if st.session_state.ptg_mode == "Assists" else "secondary",
                     use_container_width=True):
            st.session_state.ptg_mode = "Assists"; st.rerun()

        st.subheader(f"% of Points from {st.session_state.ptg_mode}")

        pct_from_goals   = round(goals   / points * 100, 1) if points else 0
        pct_from_assists = round(100 - pct_from_goals, 1)   # Remainder of points not from goals

        gauge_val = pct_from_goals if st.session_state.ptg_mode == "Goals" else pct_from_assists

        fig_ptg = go.Figure(go.Indicator(
            mode="gauge+number",
            value=gauge_val,
            number={"suffix": "%", "font": {"size": 34, "color": ACCENT}},
            gauge={
                "axis":        {"range": [0, 100], "tickcolor": MUTED},
                "bar":         {"color": PURPLE},
                "bgcolor":     DARK,
                "bordercolor": PURPLE_D,
                "steps":       [{"range": [0, 100], "color": "#1a1a3e"}],
            }
        ))
        apply_layout(fig_ptg, height=500, margin=dict(l=20, r=20, t=10, b=10))
        st.plotly_chart(fig_ptg, use_container_width=True, config={"displayModeBar": False})

    def _chart_stats_over_time(self, df_f, sched_f):
        """
        Line chart showing Goals, Assists, or Points per game over time.
        Toggle buttons switch between the three stat types.
        State stored in session_state.ps_line_mode.
        """
        # ----------------------------------
        # ----STATS OVER TIME LINE CHART----
        # ----------------------------------
        st.subheader("Stats Over Time")

        # Default value is points in the line chart
        if "ps_line_mode" not in st.session_state:
            st.session_state.ps_line_mode = "Points"

        # Render three side-by-side buttons — highlight the active one as primary
        btn1, btn2, btn3 = st.columns(3)
        if btn1.button("Points",  key="ps_line_points",
                       type="primary" if st.session_state.ps_line_mode == "Points"  else "secondary",
                       use_container_width=True):
            st.session_state.ps_line_mode = "Points";  st.rerun()
        if btn2.button("Goals",   key="ps_line_goals",
                       type="primary" if st.session_state.ps_line_mode == "Goals"   else "secondary",
                       use_container_width=True):
            st.session_state.ps_line_mode = "Goals";   st.rerun()
        if btn3.button("Assists", key="ps_line_assists",
                       type="primary" if st.session_state.ps_line_mode == "Assists" else "secondary",
                       use_container_width=True):
            st.session_state.ps_line_mode = "Assists"; st.rerun()

        # Attach opponent names to each game row for x-axis labels
        time_df = df_f.merge(
            sched_f[["Date", "OpponentName"]], on="Date", how="left"
        )
        time_df["Label"] = (
            time_df["OpponentName"] + "<br>" +
            time_df["Date"].dt.strftime("%m-%d-%Y")
        )

        # Calculate Points column (not stored in fact table, derived here)
        time_df["Points"] = time_df["Goals"] + time_df["Assists"]

        # All three modes use the same ACCENT color — the button label makes
        # it clear which stat is showing, so different colors aren't needed.
        line_col = st.session_state.ps_line_mode

        fig_time = go.Figure()
        fig_time.add_trace(go.Scatter(
            x=time_df["Label"], y=time_df[line_col],
            mode="lines+markers", name=line_col,
            line=dict(color=ACCENT, width=2.5),
            marker=dict(size=7, color=ACCENT)
        ))

        apply_layout(fig_time, height=500,
            legend=dict(orientation="h", y=1.08, bgcolor="rgba(0,0,0,0)"),
            yaxis=dict(
                gridcolor="#2a2a4a", linecolor="#2a2a4a", tickfont=dict(color=MUTED),
                rangemode="tozero",  # y axis always starts at 0
                tickvals=list(range(1, 9)), # y axis has a tick of 1 and a max of 8
            ))
        st.plotly_chart(fig_time, use_container_width=True, config={"displayModeBar": False})

    def _chart_penalty_minutes(self, df_f, sched_f):
        """
        Area line chart showing penalty minutes per game over time.
        Shows an annotation instead if the player has no penalties.
        """
        # ---------------------------------
        # ------Pen Minutes Over Time------
        # ---------------------------------
        st.subheader("Penalty Minutes Over Time")

        # Only include rows where a penalty was recorded (non-null PenType)
        pen_df = df_f[df_f["PenType"].notna()].copy()

        fig_pen = go.Figure()

        if not pen_df.empty:
            # Merge OpponentName onto pen_df — df_f does not carry OpponentName
            # directly, it must be joined from sched_f using Date as the key.
            pen_df = pen_df.merge(
                sched_f[["Date", "OpponentName"]], on="Date", how="left"
            )
            pen_df["Label"] = (
                pen_df["OpponentName"] + "<br>" +
                pen_df["Date"].dt.strftime("%m-%d-%Y")
            )
            # Area chart: fill="tozeroy" shades the area under the line down to the x-axis
            fig_pen.add_trace(go.Scatter(
                x=pen_df["Label"], y=pen_df["MinsServed"],
                mode="lines+markers", fill="tozeroy",
                line=dict(color=PURPLE, width=2),
                fillcolor="rgba(139, 47, 201, 0.27)",  # PURPLE at 27% opacity
                marker=dict(size=7, color=ACCENT)
            ))
        else:
            # If no penalties, add a text annotation inside the empty chart
            fig_pen.add_annotation(
                text="No penalties recorded",
                x=0.5, y=0.5, xref="paper", yref="paper",
                showarrow=False, font=dict(color=MUTED, size=14)
            )

        apply_layout(fig_pen, height=500,
            yaxis=dict(
                title="Mins Served", gridcolor="#2a2a4a", tickfont=dict(color=MUTED),
                rangemode="tozero",  # y axis always starts at 0
                dtick=1,             # Force integer increments of 1
            ))
        st.plotly_chart(fig_pen, use_container_width=True, config={"displayModeBar": False})


# -----------------------------------------------------------------------------
# MODULE-LEVEL FUNCTION
# Called by app.py — keeps the call signature identical to the original.
# -----------------------------------------------------------------------------
def page_player_stats(fact, schedule, players):
    """Entry point called by PaupackWLaxApp.py to render the Player Stats page."""
    PlayerStatsPage(fact, schedule, players).render()