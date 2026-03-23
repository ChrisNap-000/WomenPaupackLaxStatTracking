# 🥍 Wallenpaupack Women's Lacrosse — Stats Tracker

An interactive analytics dashboard built with Streamlit for the **Wallenpaupack Area Women's Lacrosse** program. This app provides coaches and staff with a comprehensive view of player and team performance across multiple seasons — all in one place.

---

## 🌐 Live App

The dashboard is hosted and accessible at:
**[Wallenpaupack Lacrosse Streamlit App](https://paupacklaxstattracking.streamlit.app)**

Use the **"View Demo"** option on the login screen to explore the full app with test data.

---

## 🔒 Privacy First

Player data is private. To protect the identity and stats of current and former players, the app requires a **staff password** to access real program data.

Anyone can explore the full functionality of the dashboard using the **"View Demo"** option on the login screen, which loads a set of test data. All four pages, filters, and charts work identically in demo mode — no password required.

---

## 📊 What It Tracks

This dashboard tracks all relevant women's lacrosse statistics across multiple years of the Wallenpaupack program, including:

- **Scoring** — Goals, assists, points, and points per game
- **Shooting** — Shot attempts and shooting percentage
- **Possession** — Ground balls, turnovers, and caused turnovers
- **Special Teams** — Woman-up (power play) and woman-down (penalty kill) performance
- **Clearing & Riding** — Team clearing percentage and opponent clear failure rate
- **Draws** — Draw control attempts and draw control percentage
- **Goalie** — Shots faced, saves, and save percentage per game
- **Penalties** — 12-meter penalties, green/yellow/red cards, and minutes served
- **Results** — Win/loss record including overtime outcomes

---

## 📁 Project Structure

```
PaupackWLaxApp.py       # Streamlit entry point — login, navigation, and page routing
utils/
    __init__.py
    config.py           # Shared color constants and Plotly layout helpers
    data.py             # Google Sheets data loading and DataFrame merge logic
    ui.py               # Reusable UI components (KPI tiles, date hierarchy filter)
pages/
    __init__.py
    team_stats.py       # Page 1: Team-level performance metrics and charts
    player_stats.py     # Page 2: Individual player deep-dive
    specialist.py       # Page 3: Goalie saves and draw control stats
    box_stats.py        # Page 4: Full filterable box score table
```

---

## 📄 Pages

### 1 — Team Stats
High-level team performance for any filtered date range or opponent. Includes goals and assists per game, clearing and riding percentages, a win/loss donut, a goals-over-time line chart with OT game indicators, a woman-up/down toggle gauge, a goals-vs-assists scatter plot by player, and a top-5 scorers bar chart.

### 2 — Player Stats
Full individual breakdown for any selected player. Includes a player card (jersey number and position), PPG, points, goals, assists, ground balls, shooting percentage donut, a stats-over-time line chart (goals / assists / points), penalty minutes over time, and additional stat tiles covering turnovers, woman-up goals, card counts, and more.

### 3 — Specialist
Focused view for goalies and midfielders (specifically draw percentages for the midfielders). The goalie section shows save percentage by game with a donut breakdown of saves vs. goals allowed. The draw control section shows draw control percentage by game with a donut of won vs. lost draws. Both charts color data points green or red relative to the 50% threshold.

### 4 — Box Stats
A traditional box score table aggregated across all filtered games. One row per player, with a **TOTAL** row appended at the bottom. Filterable by opponent, position, player name search, and date. Columns include all tracked stats with percentage columns calculated automatically.

---

## 🔧 Tech Stack

| Layer | Technology |
|---|---|
| Frontend / App | [Streamlit](https://streamlit.io) |
| Charts | [Plotly](https://plotly.com/python/) |
| Data Processing | [pandas](https://pandas.pydata.org) |
| Data Source | Google Sheets (via CSV export URL) |
| Secrets Management | Streamlit Secrets (`st.secrets`) |

---

## 📐 Data Structure

Data is stored across three Google Sheets tabs. This structure was intentionally designed for **ease of data entry** rather than strict database normalization — keeping the input process simple for staff is the priority. The tradeoff is that some data is spread across tables in a way that requires merging before analysis, which the app handles automatically on load.

---

### DimPlayers
Stores static player information. One row per player, updated when a new player joins the program.

| Column | Description |
|---|---|
| `PlayerID` | Unique identifier linking players to the FactTable |
| `PlayerName` | Full player name |
| `JerseyNum` | Jersey number |
| `Position` | Player position (Attack, Midfield, Defense, Goalie) |

---

### DimSchedule
Stores team-level data for each game — both our team's performance and the opposing team's. One row per game, entered after each match.

| Column | Description |
|---|---|
| `Date` | Game date — primary key linking to the FactTable since there is only one game per day |
| `OpponentName` | Name of the opposing team |
| `Won?` | Game result (Y / N) |
| `OT?` | Whether the game went to overtime (Y / N) |
| `OppGoals` | Goals scored by the opponent |
| `ClearAtts` | Our clear attempts |
| `ClearSuccesses` | Our successful clears |
| `OppClearAtts` | Opponent clear attempts |
| `OppClearSuccesses` | Opponent successful clears |
| `WomanUpAtts` | Our woman-up (power play) opportunities |
| `OppWomanUpAtts` | Opponent woman-up opportunities |
| `OppWomanUpGoals` | Goals scored by opponent on their woman-up |

---

### FactTable
Stores individual player statistics for every game. One row per player per game, entered after each match. This is the most frequently updated table.

| Column | Description |
|---|---|
| `PlayerID` | Links to DimPlayers |
| `Date` | Links to DimSchedule |
| `Goals` | Goals scored |
| `Assists` | Assists recorded |
| `Shots` | Shot attempts |
| `GBs` | Ground balls |
| `TOs` | Turnovers |
| `CTOs` | Caused turnovers |
| `WomanUpGoals` | Goals scored on woman-up opportunities |
| `WomanDownGoals` | Goals scored while woman-down |
| `DrawAtts` | Draw control attempts |
| `DrawControls` | Draw controls won |
| `Saves` | Saves (goalies) |
| `ShotsFaced` | Shots faced (goalies) |
| `PenType` | Penalty type (12m, Green, Yellow, Red) |
| `MinsServed` | Penalty minutes served |

---

*Built for the Wallenpaupack Area Women's Lacrosse program.*