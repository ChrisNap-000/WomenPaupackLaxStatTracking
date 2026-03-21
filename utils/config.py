# =============================================================================
# utils/config.py
# =============================================================================
# Shared constants and Plotly layout helpers used across every page module.
# Centralizing these here means color or layout changes only need to be made
# in one place and automatically propagate to all pages.
# =============================================================================

# -----------------------------------------------------------------------------
# COLOR CONSTANTS
# -----------------------------------------------------------------------------
PURPLE   = "#8B2FC9"
PURPLE_L = "#B060E8"
PURPLE_D = "#5A1A8A"
BLACK    = "#0D0D0D"
DARK     = "#1A1A2E"
TEXT     = "#F0F0F0"
MUTED    = "#A0A0C0"
ACCENT   = "#E040FB"

# -----------------------------------------------------------------------------
# SHARED PLOTLY LAYOUT SETTINGS
# Applied as a base to every Plotly figure via apply_layout().
# Individual pages can override any key by passing kwargs to apply_layout().
# -----------------------------------------------------------------------------
BASE_LAYOUT = dict(
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="rgba(0,0,0,0)",
    font=dict(family="sans-serif", color=TEXT),
    legend=dict(bgcolor="rgba(0,0,0,0)", font=dict(color=TEXT)),
    xaxis=dict(gridcolor="#2a2a4a", linecolor="#2a2a4a", tickfont=dict(color=MUTED)),
    yaxis=dict(gridcolor="#2a2a4a", linecolor="#2a2a4a", tickfont=dict(color=MUTED)),
)


def apply_layout(fig, **kwargs):
    """
    Merge BASE_LAYOUT with any page-specific overrides and apply to the figure.
    Keyword arguments passed in override the corresponding keys in BASE_LAYOUT.
    """
    merged = {**BASE_LAYOUT, **kwargs}
    fig.update_layout(**merged)
    return fig