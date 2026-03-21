# =============================================================================
# pages/specialist.py
# =============================================================================
# PAGE 3 — SPECIALIST
# Focuses on goalie save stats and draw control stats.
# Player filter is limited to Goalies and Midfielders only.
# =============================================================================

import plotly.graph_objects as go
import streamlit as st

from utils.config import DARK, MUTED, PURPLE, PURPLE_D, PURPLE_L, TEXT, apply_layout
from utils.data import get_merged
from utils.ui import date_hierarchy_filter, show_kpi


# -----------------------------------------------------------------------------
# SPECIALIST PAGE CLASS
# Encapsulates all rendering logic for the Specialist page.
# Instantiate with the three DataFrames, then call .render().
# -----------------------------------------------------------------------------
class SpecialistPage:
    """
    Renders the Specialist page (goalie saves + draw control).

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
        """Render the complete Specialist page top-to-bottom."""
        st.title("Specialist")

        # Only show Goalie and Midfielder options in the player dropdown
        # CHANGED: Replaced .isin(spec_positions) with .str.contains() so that
        # hybrid positions like "Midfield/Defense" are captured, not just exact matches.
        # case=False makes it case-insensitive, na=False safely ignores blank position values.
        spec_mask    = self.players["Position"].str.contains("Goalie|Midfield", case=False, na=False)
        spec_players = self.players[spec_mask]["PlayerName"].tolist()
        opponents    = ["All"] + sorted(self.schedule["OpponentName"].unique().tolist())

        # --- FILTERS ---
        st.subheader("Filters")
        fcol1, fcol2 = st.columns(2)
        sel_player = fcol1.selectbox("Player (Goalie/Mid only)",
                                      ["All"] + sorted(spec_players), key="sp_player")
        sel_opp    = fcol2.selectbox("Opponent", opponents, key="sp_opp")

        # Date hierarchy: Year -> Month -> Day, each narrowing the next.
        # date_hierarchy_filter returns an already-filtered schedule DataFrame.
        st.caption("Date Filter")

        # Apply filters — always restrict to specialist positions
        sched_f = self.schedule.copy()

        # Apply the date filter
        sched_f = date_hierarchy_filter(self.schedule, key_prefix="ts")

        if sel_opp != "All":
            sched_f = sched_f[sched_f["OpponentName"] == sel_opp]

        df_f = self.df[
            self.df["Date"].isin(sched_f["Date"]) &
            # CHANGED: Replaced .isin(spec_positions) with .str.contains() to match
            # the same logic used in the dropdown above — catches any position value
            # that contains "Goalie" or "Midfield" rather than requiring an exact match.
            self.df["Position"].str.contains("Goalie|Midfield", case=False, na=False)
        ]
        if sel_player != "All":
            df_f = df_f[df_f["PlayerName"] == sel_player]

        games_played = len(sched_f)

        # --------------------------------
        # --------KPI Calculations--------
        # --------------------------------
        saves_tot   = int(df_f["Saves"].sum())
        shots_faced = int(df_f["ShotsFaced"].sum())
        save_pct    = f"{round(saves_tot / shots_faced * 100, 1)}%" if shots_faced else "N/A"

        opp_goals   = df_f["ShotsFaced"].sum() - df_f["Saves"].sum()  # Opponent goals = shots faced - saves
        opp_gpg     = round(opp_goals / games_played, 1) if games_played else 0

        draw_atts   = int(df_f["DrawAtts"].sum())
        draw_ctrl   = int(df_f["DrawControls"].sum())
        draw_pct    = f"{round(draw_ctrl / draw_atts * 100, 1)}%" if draw_atts else "N/A"

        # --- TOP KPI ROW: 3 summary metrics ---
        st.divider()
        k1, k2, k3 = st.columns(3)
        with k1: show_kpi("Save %",         save_pct)
        with k2: show_kpi("Opp Goals PG",   opp_gpg)
        with k3: show_kpi("Draw Control %", draw_pct)

        st.divider()

        # Render goalie and draw control sections
        self._render_goalie_section(df_f, sched_f, saves_tot, shots_faced)
        st.divider()
        self._render_draw_section(df_f, sched_f, draw_atts, draw_ctrl)

    # -------------------------------------------------------------------------
    # PRIVATE SECTION RENDERERS
    # -------------------------------------------------------------------------

    def _render_goalie_section(self, df_f, sched_f, saves_tot, shots_faced):
        """
        Goalie section:
        Layout: [KPIs (Shots Faced + Saves)] | [Save % Line Chart] | [Save % Donut]
        """
        # ==========================================================================
        # GOALIE SECTION
        # Layout: [KPIs (Shots Faced + Saves)] | [Save % Line Chart] | [Save % Donut]
        # ==========================================================================
        st.subheader("Goalie")

        g_kpi_col, g_line_col, g_donut_col = st.columns([1, 2, 1])

        # ---------------------------------
        # -----------Goalie KPIs-----------
        # ---------------------------------
        with g_kpi_col:
            with st.container(height=500):
                st.write("")
                st.write("")
                st.write("")
                show_kpi("Shots Faced", shots_faced)
                st.write("")
                st.write("")
                st.write("")
                st.write("")
                st.write("")
                st.write("")
                show_kpi("Total Saves", saves_tot)

        with g_line_col:
            self._chart_save_pct_line(df_f, sched_f)

        with g_donut_col:
            self._chart_save_pct_donut(saves_tot, shots_faced)

    def _render_draw_section(self, df_f, sched_f, draw_atts, draw_ctrl):
        """
        Draw control section:
        Layout: [KPIs (Draw Atts + Draw Controls)] | [Draw % Line Chart] | [Draw % Donut]
        """
        # ==========================================================================
        # DRAW CONTROL SECTION
        # Layout: [KPIs (Draw Atts + Draw Controls)] | [Draw % Line Chart] | [Draw % Donut]
        # ==========================================================================
        st.subheader("Draw Control")

        d_kpi_col, d_line_col, d_donut_col = st.columns([1, 2, 1])

        # --------------------------------
        # ----------Draw KPIs-------------
        # --------------------------------
        with d_kpi_col:
            with st.container(height=500):
                st.write("")
                st.write("")
                st.write("")
                show_kpi("Draw Atts", draw_atts)
                st.write("")
                st.write("")
                st.write("")
                st.write("")
                st.write("")
                st.write("")
                show_kpi("Draw Controls", draw_ctrl)

        with d_line_col:
            self._chart_draw_pct_line(df_f, sched_f)

        with d_donut_col:
            self._chart_draw_pct_donut(draw_atts, draw_ctrl)

    # -------------------------------------------------------------------------
    # INDIVIDUAL CHART METHODS
    # -------------------------------------------------------------------------

    def _chart_save_pct_line(self, df_f, sched_f):
        """
        Area line chart of Save % per game (goalie rows only).
        Points are colored red < 50%, green >= 50%.
        A dashed reference line marks the 50% threshold.
        """
        # --------------------------------
        # ---------Save % by Game---------
        # --------------------------------
        st.subheader("Save % by Game")
        goalie_df = df_f[df_f["Position"] == "Goalie"]

        if not goalie_df.empty:
            # Sum saves and shots faced per game date
            sg = goalie_df.groupby("Date")[["Saves", "ShotsFaced"]].sum().reset_index()
            sg = sg.merge(sched_f[["Date", "OpponentName"]], on="Date", how="left")
            sg["SavePct"] = sg.apply(
                lambda r: round(r["Saves"] / r["ShotsFaced"] * 100, 1)
                          if r["ShotsFaced"] else 0, axis=1
            )
            sg["Label"] = (
                sg["OpponentName"] + "<br>" +
                sg["Date"].dt.strftime("%m-%d-%Y")
            )
            # Color each data point: red if below 50%, green if at or above 50%
            sg["MarkerColor"] = sg["SavePct"].apply(
                lambda v: "#e74c3c" if v < 50 else "#2ecc71"
            )
            fig_sv = go.Figure()
            # Dashed reference line at 50% to show the "break-even" point
            fig_sv.add_hline(y=50, line_dash="dot", line_color=MUTED, opacity=0.5)
            fig_sv.add_trace(go.Scatter(
                x=sg["Label"], y=sg["SavePct"],
                mode="lines+markers", fill="tozeroy",
                line=dict(color=PURPLE_L, width=2.5),
                fillcolor="rgba(139, 47, 201, 0.20)",
                marker=dict(size=9, color=sg["MarkerColor"])
            ))
            apply_layout(fig_sv, height=500,
                yaxis=dict(title="Save %", range=[0, 105],
                           ticksuffix="%", gridcolor="#2a2a4a",
                           tickfont=dict(color=MUTED)))
            st.plotly_chart(fig_sv, use_container_width=True, config={"displayModeBar": False})
        else:
            st.info("No goalie data for this selection.")

    def _chart_save_pct_donut(self, saves_tot, shots_faced):
        """
        Donut chart: Saves vs Goals Allowed as a share of shots faced.
        """
        # --------------------------------
        # -------Save % Donut Chart-------
        # --------------------------------
        st.subheader("Save %")
        goals_allowed = max(shots_faced - saves_tot, 0)
        fig_sv_d = go.Figure(go.Pie(
            labels=["Saves", "Goals<br>Allowed"],
            values=[saves_tot, goals_allowed],
            hole=0.55,
            marker=dict(colors=[PURPLE, DARK]),
            textinfo="label+percent",
            textfont=dict(color=TEXT),
        ))
        apply_layout(fig_sv_d, height=500, showlegend=False,
                     margin=dict(l=10, r=10, t=10, b=10))
        st.plotly_chart(fig_sv_d, use_container_width=True, config={"displayModeBar": False})

    def _chart_draw_pct_line(self, df_f, sched_f):
        """
        Area line chart of Draw Control % per game (midfielder rows only).
        Same red/green coloring as the Save % chart (threshold at 50%).
        """
        # ------------------------------------
        # -------Draw Control % by Game-------
        # ------------------------------------
        st.subheader("Draw Control % by Game")
        mid_df = df_f[df_f["Position"] == "Midfield"]

        if not mid_df.empty:
            dg = mid_df.groupby("Date")[["DrawAtts", "DrawControls"]].sum().reset_index()
            dg = dg.merge(sched_f[["Date", "OpponentName"]], on="Date", how="left")
            dg["DrawPct"] = dg.apply(
                lambda r: round(r["DrawControls"] / r["DrawAtts"] * 100, 1)
                          if r["DrawAtts"] else 0, axis=1
            )
            dg["Label"] = (
                dg["OpponentName"] + "<br>" +
                dg["Date"].dt.strftime("%m-%d-%Y")
            )
            # Same red/green coloring logic as the save % chart
            dg["MarkerColor"] = dg["DrawPct"].apply(
                lambda v: "#e74c3c" if v < 50 else "#2ecc71"
            )
            fig_dc = go.Figure()
            fig_dc.add_hline(y=50, line_dash="dot", line_color=MUTED, opacity=0.5)
            fig_dc.add_trace(go.Scatter(
                x=dg["Label"], y=dg["DrawPct"],
                mode="lines+markers", fill="tozeroy",
                line=dict(color=PURPLE, width=2.5),
                fillcolor="rgba(139, 47, 201, 0.20)",
                marker=dict(size=9, color=dg["MarkerColor"])
            ))
            apply_layout(fig_dc, height=500,
                yaxis=dict(title="Draw %", range=[0, 105],
                           ticksuffix="%", gridcolor="#2a2a4a",
                           tickfont=dict(color=MUTED)))
            st.plotly_chart(fig_dc, use_container_width=True, config={"displayModeBar": False})
        else:
            st.info("No draw data for this selection.")

    def _chart_draw_pct_donut(self, draw_atts, draw_ctrl):
        """
        Donut chart: Draw Controls Won vs Controls Lost.
        """
        # ---------------------------------
        # -------Draw Controls Donut-------
        # ---------------------------------
        st.subheader("Draw Controls")
        draws_lost = max(draw_atts - draw_ctrl, 0)
        fig_dc_d = go.Figure(go.Pie(
            labels=["Controls<br>Won", "Controls<br>Lost"],
            values=[draw_ctrl, draws_lost],
            hole=0.55,
            marker=dict(colors=[PURPLE_L, DARK]),
            textinfo="label+percent",
            textfont=dict(color=TEXT),
        ))
        apply_layout(fig_dc_d, height=500, showlegend=False,
                     margin=dict(l=10, r=10, t=10, b=10))
        st.plotly_chart(fig_dc_d, use_container_width=True, config={"displayModeBar": False})


# -----------------------------------------------------------------------------
# MODULE-LEVEL FUNCTION
# Called by app.py — keeps the call signature identical to the original.
# -----------------------------------------------------------------------------
def page_specialist(fact, schedule, players):
    """Entry point called by app.py to render the Specialist page."""
    SpecialistPage(fact, schedule, players).render()