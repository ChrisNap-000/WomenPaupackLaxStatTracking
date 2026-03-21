# =============================================================================
# app.py — Main Entry Point
# =============================================================================
# Women's Lacrosse Analytics - Streamlit App
# =============================================================================
# This app loads three Google Sheets tabs (FactTable, DimSchedule, DimPlayers),
# merges them together, and displays stats across four pages:
#   1. Team Stats   - Overall team performance metrics and charts
#   2. Player Stats - Individual player deep-dive
#   3. Specialist   - Goalie save stats and draw control stats
#   4. Box Stats    - Full filterable stat table (like a box score)
#
# No data is stored between sessions. Users log in each time, which keeps
# player data private.
#
# Project file layout:
#   app.py                  ← this file (Streamlit entry point)
#   utils/
#       __init__.py         ← makes utils a package
#       config.py           ← shared color constants + Plotly layout helpers
#       data.py             ← load_data() and get_merged() helpers
#       ui.py               ← show_kpi() and date_hierarchy_filter()
#   pages/
#       __init__.py         ← makes pages a package
#       team_stats.py       ← Page 1: TeamStatsPage class + page_team_stats()
#       player_stats.py     ← Page 2: PlayerStatsPage class + page_player_stats()
#       specialist.py       ← Page 3: SpecialistPage class + page_specialist()
#       box_stats.py        ← Page 4: BoxStatsPage class + page_box_stats()
# =============================================================================

import streamlit as st

from utils.data import load_data
from pages.team_stats   import page_team_stats
from pages.player_stats import page_player_stats
from pages.specialist   import page_specialist
from pages.box_stats    import page_box_stats


# -----------------------------------------------------------------------------
# APP CONFIGURATION
# -----------------------------------------------------------------------------
st.set_page_config(
    page_title="Women's Lacrosse Stats",
    page_icon="🥍",
    layout="wide",
    initial_sidebar_state="collapsed",
    menu_items={},  # Hides the hamburger menu that reopens the sidebar
)

st.markdown(
    """
    <style>
    h1, h2 { text-align: center; }

    /* Hide the sidebar and its toggle arrow entirely */
    [data-testid="collapsedControl"] { display: none !important; }
    [data-testid="stSidebar"]        { display: none !important; }
    </style>
    """,
    unsafe_allow_html=True
)


# -----------------------------------------------------------------------------
# SESSION STATE INITIALIZATION
# -----------------------------------------------------------------------------
if "page" not in st.session_state:
    st.session_state.page = "Team Stats"

if "data_loaded" not in st.session_state:
    st.session_state.data_loaded = False

# Tracks whether the user logged in with the real password (True)
# or is viewing with test data (False). Defaults to False.
if "is_authenticated" not in st.session_state:
    st.session_state.is_authenticated = False


# -----------------------------------------------------------------------------
# LOGO
# -----------------------------------------------------------------------------
logo_url = "LaxLogo.jpg"

col1, col2, col3 = st.columns([3.5, 1, 3.5])
with col2:
    st.image(logo_url, width=200)


# -----------------------------------------------------------------------------
# NAVIGATION BAR
# Renders four tab-style buttons; active page is highlighted as "primary".
# -----------------------------------------------------------------------------
PAGES = ["Team Stats", "Player Stats", "Specialist", "Box Stats"]


def nav_bar():
    """Render the top navigation bar with one button per page."""
    cols = st.columns(len(PAGES))
    for i, page_name in enumerate(PAGES):
        btn_type = "primary" if st.session_state.page == page_name else "secondary"
        if cols[i].button(page_name, key=f"nav_{page_name}",
                          use_container_width=True, type=btn_type):
            st.session_state.page = page_name
            st.rerun()


# =============================================================================
# LOGIN / ACCESS SCREEN
# Shown when data_loaded is False.
#
# Two paths:
#   1. Password login  → loads real data, sets is_authenticated = True
#   2. Test data       → loads test data, is_authenticated stays False
#
# Google Form links and sheet URLs are read from st.secrets so they never
# appear in source code.
# =============================================================================
def upload_screen():
    """Render the login / demo access screen."""
    st.title("🥍 Women's Lacrosse Analytics")
    st.write("Enter the password to access the full report, or view a demo with test data.")
    st.divider()

    # --- PATH 1: PASSWORD LOGIN ---
    st.subheader("🔐 Staff Login")
    password_input = st.text_input("Password", type="password", key="login_password")

    if st.button("Login", use_container_width=True, type="primary"):
        if password_input == st.secrets["APP_PASSWORD"]:
            try:
                fact, schedule, players = load_data(     # Login button — real data
                    st.secrets["MAIN_SHEET_URL"],
                    st.secrets["SCHEDULE_URL"],
                    st.secrets["GID_FACT_REAL"],
                    st.secrets["GID_PLAYERS_REAL"],
                    st.secrets["GID_SCHEDULE_REAL"]
                )
                st.session_state.fact             = fact
                st.session_state.schedule         = schedule
                st.session_state.players          = players
                st.session_state.is_authenticated = True
                st.session_state.data_loaded      = True
                st.rerun()
            except Exception as e:
                st.error(
                    f"Could not load sheets. Check that the sheet URLs in secrets are correct."
                    f"\n\nError: {e}"
                )
        else:
            st.error("Incorrect password. Please try again.")

    st.divider()

    # --- PATH 2: TEST DATA (no password required) ---
    st.subheader("👀 View Demo")
    st.caption("Explore the report using sample data. No password needed.")

    if st.button("View with Test Data", use_container_width=True, type="secondary"):
        try:
            fact, schedule, players = load_data( # Test data button
                st.secrets["MAIN_SHEET_URL_TEST"],
                st.secrets["SCHEDULE_URL_TEST"],
                st.secrets["GID_FACT_TEST"],
                st.secrets["GID_PLAYERS_TEST"],
                st.secrets["GID_SCHEDULE_TEST"]
            )
            st.session_state.fact             = fact
            st.session_state.schedule         = schedule
            st.session_state.players          = players
            st.session_state.is_authenticated = False   # Not a full login
            st.session_state.data_loaded      = True
            st.rerun()
        except Exception as e:
            st.error(f"Could not load test data.\n\nError: {e}")


# =============================================================================
# MAIN — Entry point
# Decides whether to show the login screen or the main report,
# then routes to the correct page based on session_state.page.
# =============================================================================
def main():
    # If no data has been loaded yet, show the login screen and stop here
    if not st.session_state.data_loaded:
        upload_screen()
        return

    # Retrieve the DataFrames stored in session_state after login
    fact     = st.session_state.fact
    schedule = st.session_state.schedule
    players  = st.session_state.players

    # --- GOOGLE FORM LINKS (authenticated users only, shown above nav bar) ---
    if st.session_state.is_authenticated:
        col1, col2 = st.columns(2)
        with col1:
            st.link_button(
                "📋 Open Player Data Google Form",
                st.secrets["FORM_PLAYER_DATA"],
                use_container_width=True
            )
        with col2:
            st.link_button(
                "📋 Open Team Data Google Form",
                st.secrets["FORM_TEAM_DATA"],
                use_container_width=True
            )

    # Render the navigation bar at the top of every page
    nav_bar()
    st.divider()

    # Route to the correct page function based on what the user selected
    page = st.session_state.page
    if page == "Team Stats":
        page_team_stats(fact, schedule, players)
    elif page == "Player Stats":
        page_player_stats(fact, schedule, players)
    elif page == "Specialist":
        page_specialist(fact, schedule, players)
    elif page == "Box Stats":
        page_box_stats(fact, schedule, players)


# Standard Python entry point — runs main() only when this file is executed directly
if __name__ == "__main__":
    main()