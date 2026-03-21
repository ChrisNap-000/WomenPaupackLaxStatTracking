# =============================================================================
# pages/team_stats.py
# =============================================================================
# PAGE 1 — TEAM STATS
# Shows overall team performance: KPIs, woman-up gauge, goals over time,
# scatter of goals vs assists per player, wins/losses, and top scorers.
# =============================================================================

import plotly.graph_objects as go
import streamlit as st

from utils.config import (
    ACCENT, DARK, MUTED, PURPLE, PURPLE_D, TEXT,
    apply_layout,
)
from utils.data import get_merged
from utils.ui import date_hierarchy_filter, show_kpi


# -----------------------------------------------------------------------------
# TEAM STATS PAGE CLASS
# Encapsulates all rendering logic for the Team Stats page.
# Instantiate with the three DataFrames, then call .render().
# -----------------------------------------------------------------------------
class TeamStatsPage:
    """
    Renders the Team Stats page.

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
        """Render the complete Team Stats page top-to-bottom."""
        st.title("Team Stats")

        # --- FILTERS ---
        st.subheader("Filters")

        # Opponent dropdown sits above the date hierarchy
        opponents = ["All"] + sorted(self.schedule["OpponentName"].unique().tolist())
        sel_opp   = st.selectbox("Opponent", opponents, key="ts_opp")

        # Date hierarchy: Year -> Month -> Day, each narrowing the next.
        # date_hierarchy_filter returns an already-filtered schedule DataFrame.
        st.caption("Date Filter")
        sched_f = date_hierarchy_filter(self.schedule, key_prefix="ts")

        # Apply the opponent filter on top of whatever the date hierarchy returned
        if sel_opp != "All":
            sched_f = sched_f[sched_f["OpponentName"] == sel_opp]

        # Filter the merged fact table to only rows whose date is in sched_f
        df_f         = self.df[self.df["Date"].isin(sched_f["Date"])]
        games_played = len(sched_f)

        # Render each section, passing the filtered data down
        self._render_kpis(df_f, sched_f, games_played)
        st.divider()
        self._render_wl_and_goals_chart(df_f, sched_f)
        st.divider()
        self._render_gauge_scatter_bar(df_f, sched_f)

    # -------------------------------------------------------------------------
    # PRIVATE SECTION RENDERERS
    # -------------------------------------------------------------------------

    def _render_kpis(self, df_f, sched_f, games_played):
        """
        Calculate and display the six top-level KPI tiles.

        KPIs shown:
          Goals PG, Assists PG, Clearing %, Riding %, Opp Goals PG,
          % of Goals Assisted
        """
        # ----------------------------------
        # ---------KPI Calculations---------
        # ----------------------------------
        # Guard against division by zero with "if games_played else 0"
        total_goals   = df_f["Goals"].sum()
        total_assists = df_f["Assists"].sum()
        goals_pg      = round(total_goals   / games_played, 1) if games_played else 0
        assists_pg    = round(total_assists / games_played, 1) if games_played else 0

        # Clearing %: how often we successfully clear the ball
        clear_atts  = sched_f["ClearAtts"].sum()
        clear_succ  = sched_f["ClearSuccesses"].sum()
        clearing_pct = f"{round(clear_succ / clear_atts * 100, 1)}%" if clear_atts else "N/A"

        # Riding %: how often we forced the opponent to fail their clear
        # Formula: (OppClearAtts - OppClearSuccesses) / OppClearAtts
        opp_clear_atts  = sched_f["OppClearAtts"].sum()
        opp_clear_succ  = sched_f["OppClearSuccesses"].sum()
        forced_fails    = opp_clear_atts - opp_clear_succ
        riding_pct = f"{round(forced_fails / opp_clear_atts * 100, 1)}%" if opp_clear_atts else "N/A"

        # Opponent goals per game
        opp_goals    = sched_f["OppGoals"].sum()
        opp_goals_pg = round(opp_goals / games_played, 1) if games_played else 0

        # % of team goals that were assists
        per_assisted = f"{round(total_assists / total_goals * 100, 1)}%" if total_goals else "N/A"

        # --- KPI DISPLAY ---
        st.divider()
        k1, k2, k3, k4, k5, k6 = st.columns(6)
        with k1: show_kpi("Goals PG",             goals_pg)
        with k2: show_kpi("Assists PG",           assists_pg)
        with k3: show_kpi("Clearing %",           clearing_pct)
        with k4: show_kpi("Riding %",             riding_pct)
        with k5: show_kpi("Opp Goals PG",         opp_goals_pg)
        with k6: show_kpi("% of Goals Assisted",  per_assisted)

    def _render_wl_and_goals_chart(self, df_f, sched_f):
        """
        ROW 2: W/L Donut on the left, Goals vs Opp Goals line chart on the right.
        """
        left_col, right_col = st.columns([1, 2])

        with left_col:
            self._chart_wl_donut(sched_f)

        with right_col:
            self._chart_goals_over_time(df_f, sched_f)

    def _render_gauge_scatter_bar(self, df_f, sched_f):
        """
        ROW 3: Woman-Up/Down gauge, Goals vs Assists scatter, Top 5 bar chart.
        """
        col_a, col_b, col_c = st.columns([1, 2, 2])

        with col_a:
            self._chart_woman_up_gauge(df_f, sched_f)

        with col_b:
            self._chart_goals_vs_assists_scatter(df_f)

        with col_c:
            self._chart_top5_bar(df_f)

    # -------------------------------------------------------------------------
    # INDIVIDUAL CHART METHODS
    # -------------------------------------------------------------------------

    def _chart_wl_donut(self, sched_f):
        """
        Win/Loss donut chart.
        Purple slice = wins; dark slice = losses.
        """
        # ----------------------------------
        # ----------Win/Loss Donut----------
        # ----------------------------------
        st.subheader("W / L")

        wins   = (sched_f["Won?"] == "Y").sum()
        losses = (sched_f["Won?"] == "N").sum()

        # Donut chart (pie with a hole in the middle)
        fig_wl = go.Figure(go.Pie(
            labels=["Wins", "Losses"],
            values=[wins, losses],
            hole=0.6,
            marker=dict(colors=[PURPLE, "#222244"]),
            textinfo="label+percent",
            textfont=dict(color=TEXT),
        ))
        apply_layout(fig_wl, height=500, showlegend=False,
                     margin=dict(l=10, r=10, t=10, b=10))
        st.plotly_chart(fig_wl, use_container_width=True, config={"displayModeBar": False})

    def _chart_goals_over_time(self, df_f, sched_f):
        """
        Line chart: our goals vs opponent goals per game.
        OT games get colored markers (green = OT win, red = OT loss).
        """
        # ----------------------------------
        # ----Goals OVER TIME LINE CHART----
        # ----------------------------------
        st.subheader("Team Goals vs Opponent Goals by Game")

        # Aggregate total goals scored per game date from the fact table
        game_goals = df_f.groupby("Date")["Goals"].sum().reset_index()

        # Merge in opponent name, their goal total, OT flag, and result from schedule.
        # We need OT? and Won? to color the "Our Goals" markers conditionally.
        game_goals = game_goals.merge(
            sched_f[["Date", "OpponentName", "OppGoals", "OT?", "Won?"]],
            on="Date", how="left"
        )

        # Build a readable x-axis label: "Riverside HS<br>3/8"
        # Plotly renders <br> as a line break on axis tick labels,
        # whereas \n is ignored — so we use <br> to stack the date under the name.
        game_goals["Label"] = (
            game_goals["OpponentName"] + "<br>" +
            game_goals["Date"].dt.strftime("%-m/%-d")
        )

        # Determine marker color for each "Our Goals" point:
        #   Green  — OT game we won  (came back or held on in OT)
        #   Red    — OT game we lost
        #   ACCENT — regular (non-OT) game, no special color needed
        def our_goals_marker_color(row):
            if row["OT?"] == "Y" and row["Won?"] == "Y":
                return "#2ecc71"   # Green — OT win
            elif row["OT?"] == "Y" and row["Won?"] == "N":
                return "#e74c3c"   # Red — OT loss
            else:
                return ACCENT      # Default — non-OT game

        game_goals["MarkerColor"] = game_goals.apply(our_goals_marker_color, axis=1)

        fig_line = go.Figure()

        # Our team's goals — line stays ACCENT, markers change color per game
        fig_line.add_trace(go.Scatter(
            x=game_goals["Label"], y=game_goals["Goals"],
            mode="lines+markers", name="Our Goals",
            line=dict(color=ACCENT, width=2.5),
            marker=dict(color=game_goals["MarkerColor"], size=10,
                        line=dict(color=ACCENT, width=1))
        ))

        # Opponent's goals — neutral color so ours stands out
        fig_line.add_trace(go.Scatter(
            x=game_goals["Label"], y=game_goals["OppGoals"],
            mode="lines+markers", name="Opp Goals",
            line=dict(color="#888888", width=2.5),
            marker=dict(color=TEXT, size=7)
        ))

        # --- LEGEND ENTRIES FOR OT MARKER COLORS ---
        # We add a small caption below the chart using st.caption instead of
        # relying on Plotly dummy traces, which are unreliable across versions.
        # The caption clearly explains the green/red marker meaning to the user.
        apply_layout(fig_line, height=500,
            legend=dict(orientation="h", y=1.1, bgcolor="rgba(0,0,0,0)"),
            yaxis=dict(
                gridcolor="#2a2a4a", linecolor="#2a2a4a", tickfont=dict(color=MUTED),
                rangemode="tozero",
                dtick=1,
            ))
        st.plotly_chart(fig_line, use_container_width=True, config={"displayModeBar": False})

        # Caption explains the OT marker colors since Plotly legend entries
        # for mixed-color markers are unreliable across versions.
        # The colored squares are rendered using Unicode block characters.
        st.caption("🟢 = OT Win   🔴 = OT Loss")

    def _chart_woman_up_gauge(self, df_f, sched_f):
        """
        Toggle gauge: Woman-Up % (our power play) or Woman-Down % (our penalty kill).
        State stored in session_state.gauge_mode.
        """
        # ---------------------------------
        # -------Woman-Up/Down Gauge-------
        # ---------------------------------

        # Toggle button: clicking it flips between Woman-Up and Woman-Down mode.
        # We store the current mode in session_state so it persists across reruns.
        if "gauge_mode" not in st.session_state:
            st.session_state.gauge_mode = "Woman-Up %"

        # The button label always shows the opposite mode (what you'll switch TO)
        btn_label = (
            "Switch to Woman-Down %"
            if st.session_state.gauge_mode == "Woman-Up %"
            else "Switch to Woman-Up %"
        )
        if st.button(btn_label, key="ts_gauge_toggle", use_container_width=True):
            # Flip the mode when clicked
            st.session_state.gauge_mode = (
                "Woman-Down %"
                if st.session_state.gauge_mode == "Woman-Up %"
                else "Woman-Up %"
            )
            st.rerun()

        st.subheader(st.session_state.gauge_mode)

        if st.session_state.gauge_mode == "Woman-Up %":
            # Woman-Up %: how often we score when we have the extra player
            # Formula: WomanUpGoals / WomanUpAtts
            wu_atts  = sched_f["WomanUpAtts"].sum()
            wu_goals = df_f["WomanUpGoals"].sum()
            gauge_val = round(wu_goals / wu_atts * 100, 1) if wu_atts else 0
        else:
            # Woman-Down %: how often we prevent the opponent from scoring
            # when they have the extra player (their woman-up situation)
            # Formula: (OppWomanUpAtts - OppWomanUpGoals) / OppWomanUpAtts
            opp_wu_atts  = sched_f["OppWomanUpAtts"].sum()
            opp_wu_goals = sched_f["OppWomanUpGoals"].sum()
            gauge_val = (
                round((opp_wu_atts - opp_wu_goals) / opp_wu_atts * 100, 1)
                if opp_wu_atts else 0
            )

        # Gauge chart — same visual for both modes, only the value changes
        fig_gauge = go.Figure(go.Indicator(
            mode="gauge+number",
            value=gauge_val,
            number={"suffix": "%", "font": {"size": 36, "color": ACCENT}},
            gauge={
                "axis":        {"range": [0, 100], "tickcolor": MUTED},
                "bar":         {"color": PURPLE},
                "bgcolor":     DARK,
                "bordercolor": PURPLE_D,
                "steps":       [{"range": [0, 100], "color": "#1a1a3e"}],
            }
        ))
        apply_layout(fig_gauge, height=500, margin=dict(l=20, r=20, t=10, b=10))
        st.plotly_chart(fig_gauge, use_container_width=True, config={"displayModeBar": False})

    def _chart_goals_vs_assists_scatter(self, df_f):
        """
        Scatter plot: each player as a point (x=Assists, y=Goals).
        A y=x reference line splits goal-heavy vs assist-heavy players.
        Shaded zones highlight which side of the line each player falls on.
        """
        # -----------------------------------
        # ---G vs A by Player Scatter Plot---
        # -----------------------------------
        st.subheader("Goals vs Assists by Player")

        # Sum each player's total goals and assists across all filtered games
        scatter_df = df_f.groupby("PlayerName")[["Goals", "Assists"]].sum().reset_index()

        # --- REFERENCE LINE: y = x (equal goals and assists) ---
        # Players above the line score more than they assist (goal-heavy).
        # Players below the line assist more than they score (playmaker).
        # We extend the line slightly beyond the data range so it always
        # crosses the full chart area regardless of the data values.
        max_val = int(max(scatter_df["Assists"].max(), scatter_df["Goals"].max(), 1)) + 3
        line_x  = list(range(0, max_val + 1))
        line_y  = line_x  # y = 1x + 0, so y equals x at every point

        fig_sc = go.Figure()

        # --- SHADING: above the line (more goals than assists) ---
        # We draw a filled area from the line up to max_val.
        # The line color must be set (even if thin) because Plotly uses it
        # for the legend swatch — width=0 makes the border invisible on the
        # chart but the color still appears as the legend icon.
        fig_sc.add_trace(go.Scatter(
            x=line_x + line_x[::-1],   # Forward along top, then back along line
            y=[max_val] * len(line_x) + line_y[::-1],
            fill="toself",
            fillcolor="rgba(139, 47, 201, 0.25)",   # Purple — goal-heavy zone
            line=dict(color="rgba(139, 47, 201, 0.8)", width=0.5),
            showlegend=True,
            name="More Goals",
            hoverinfo="skip",           # Don't show tooltip on the shading
        ))

        # --- SHADING: below the line (more assists than goals) ---
        # Different color (White) so the two zones are clearly distinct
        fig_sc.add_trace(go.Scatter(
            x=line_x + line_x[::-1],
            y=line_y + [0] * len(line_x),
            fill="toself",
            fillcolor="rgba(255, 255, 255, 0.15)",    # White — assist-heavy zone
            line=dict(color="rgba(255, 255, 255, 0.8)", width=0.5),
            showlegend=True,
            name="More Assists",
            hoverinfo="skip",
        ))

        # --- REFERENCE LINE: y = x drawn as a dashed line ---
        fig_sc.add_trace(go.Scatter(
            x=line_x, y=line_y,
            mode="lines",
            line=dict(color=MUTED, width=1.5, dash="dash"),
            showlegend=False,
            hoverinfo="skip",
        ))

        # --- PLAYER DATA POINTS on top of the shading ---
        # mode="markers" only — no text labels rendered on the chart.
        # customdata bundles extra columns onto each point so we can reference
        # them in hovertemplate. The order here (PlayerName, Goals, Assists)
        # maps to customdata[0], customdata[1], customdata[2] in the template.
        # <extra></extra> suppresses the default grey trace-name box in the tooltip.
        fig_sc.add_trace(go.Scatter(
            x=scatter_df["Assists"],
            y=scatter_df["Goals"],
            mode="markers",
            customdata=scatter_df[["PlayerName", "Goals", "Assists"]].values,
            hovertemplate=(
                "<b>%{customdata[0]}</b><br>"
                "Goals: %{customdata[1]}<br>"
                "Assists: %{customdata[2]}"
                "<extra></extra>"
            ),
            marker=dict(color=ACCENT, size=10, line=dict(color=PURPLE, width=1)),
            showlegend=False,
            name="Player",
        ))

        apply_layout(fig_sc, height=500,
            xaxis=dict(title="Total Assists", gridcolor="#2a2a4a",
                       tickfont=dict(color=MUTED), range=[0, max_val]),
            yaxis=dict(title="Total Goals",   gridcolor="#2a2a4a",
                       tickfont=dict(color=MUTED), range=[0, max_val]),
            legend=dict(orientation="h", y=1.08, bgcolor="rgba(0,0,0,0)",
                        font=dict(color=TEXT)))
        st.plotly_chart(fig_sc, use_container_width=True, config={"displayModeBar": False})

    def _chart_top5_bar(self, df_f):
        """
        Horizontal bar chart of the top 5 players by total points (goals + assists).
        """
        # ---------------------------------
        # -----Top 5 Players by Points-----
        # ---------------------------------
        st.subheader("Top 5 Players by Points")

        # Calculate total points (goals + assists) per player, then take top 5
        pts = df_f.groupby("PlayerName").apply(
            lambda x: x["Goals"].sum() + x["Assists"].sum()
        ).reset_index()
        pts.columns = ["PlayerName", "Points"]
        top5 = pts.nlargest(5, "Points")

        fig_bar = go.Figure(go.Bar(
            x=top5["PlayerName"],
            y=top5["Points"],
            marker=dict(color=PURPLE, line=dict(color=ACCENT, width=1)),
            text=top5["Points"],
            textposition="outside",
            textfont=dict(color=TEXT),
        ))
        apply_layout(fig_bar, height=500,
                     xaxis=dict(tickfont=dict(size=11, color=TEXT)))
        st.plotly_chart(fig_bar, use_container_width=True, config={"displayModeBar": False})


# -----------------------------------------------------------------------------
# MODULE-LEVEL FUNCTION
# Called by app.py — keeps the call signature identical to the original.
# -----------------------------------------------------------------------------
def page_team_stats(fact, schedule, players):
    """Entry point called by PaupackWLaxApp.py to render the Team Stats page."""
    TeamStatsPage(fact, schedule, players).render()