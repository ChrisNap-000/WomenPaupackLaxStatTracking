# =============================================================================
# utils/ui.py
# =============================================================================
# Reusable Streamlit UI components shared across all page modules.
# Any widget or layout helper used on more than one page lives here.
# =============================================================================

import pandas as pd
import streamlit as st


# -----------------------------------------------------------------------------
# KPI METRIC HELPER
# Renders a single centered metric inside a bordered container.
# Accepts any label string and any scalar value (int, float, str).
# -----------------------------------------------------------------------------
def show_kpi(label, value):
    """Render a single KPI tile with a centered label and value."""
    with st.columns(1)[0]:
        with st.container(border=True):
            st.markdown(
                """
                <style>
                [data-testid="stMetric"] { text-align: center; }
                [data-testid="stMetricLabel"] {
                    justify-content: center;
                    display: block;
                    text-align: center;
                    width: 100%;
                }
                [data-testid="stMetricLabel"] > div {
                    text-align: center;
                    width: 100%;
                }
                [data-testid="stMetricValue"] { justify-content: center; }
                </style>
                """,
                unsafe_allow_html=True
            )
            st.metric(label=label, value=value)


# -----------------------------------------------------------------------------
# DATE HIERARCHY FILTER
# Renders three linked selectboxes: Year → Month → Day.
# Each level narrows the options available in the next level.
# Returns a filtered copy of the passed-in schedule DataFrame.
# key_prefix must be unique per page to avoid Streamlit widget key collisions.
# -----------------------------------------------------------------------------
def date_hierarchy_filter(schedule, key_prefix):
    """
    Render a Year / Month / Day filter cascade and return the filtered schedule.

    Parameters
    ----------
    schedule   : pd.DataFrame  — must have a 'Date' column of datetime dtype
    key_prefix : str           — unique string prepended to each widget key
                                 to prevent collisions across pages

    Returns
    -------
    pd.DataFrame — filtered schedule containing only rows matching the selection
    """
    years = ["All"] + sorted(schedule["Date"].dt.year.unique().tolist(), reverse=True)
    col1, col2, col3 = st.columns(3)

    default_year_index = 1 if len(years) > 1 else 0
    sel_year = col1.selectbox("Year", years, index=default_year_index, key=f"{key_prefix}_year")

    sched_y = schedule.copy()
    if sel_year != "All":
        sched_y = sched_y[sched_y["Date"].dt.year == sel_year]

    month_nums   = sorted(sched_y["Date"].dt.month.unique().tolist(), reverse=True)
    month_labels = {m: pd.Timestamp(2000, m, 1).strftime("%B") for m in month_nums}
    month_options = ["All"] + [month_labels[m] for m in month_nums]

    sel_month_label = col2.selectbox("Month", month_options, key=f"{key_prefix}_month")

    label_to_num  = {v: k for k, v in month_labels.items()}
    sel_month_num = label_to_num.get(sel_month_label)

    sched_ym = sched_y.copy()
    if sel_month_label != "All":
        sched_ym = sched_ym[sched_ym["Date"].dt.month == sel_month_num]

    days    = ["All"] + sorted(sched_ym["Date"].dt.day.unique().tolist())
    sel_day = col3.selectbox("Day", days, key=f"{key_prefix}_day")

    sched_f = sched_ym.copy()
    if sel_day != "All":
        sched_f = sched_f[sched_f["Date"].dt.day == sel_day]

    return sched_f