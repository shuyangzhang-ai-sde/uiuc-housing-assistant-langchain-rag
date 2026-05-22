# app.py
# Streamlit chat UI for the UIUC Housing Assistant
#
# Run: streamlit run app.py

import re
import pandas as pd
import streamlit as st
from rag_chain import chain, retriever

# ── Page config ───────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="AI-powered housing search for UIUC students",
    layout="wide",
)

# ── Cache the chain so the embedding model + Chroma only load once ────────────
# Without this, Streamlit reloads everything on every interaction — very slow.
@st.cache_resource
def load_chain():
    return chain

rag = load_chain()

# ── Sidebar ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.header("About")
    st.markdown(
        """
        **Data source:** Green Street Realty
        **Listings:** 489 floor plans · 251 properties
        **Last scraped:** May 20, 2026
        **Area:** Champaign, IL (UIUC)
        """
    )
    st.divider()
    st.markdown(
        """
        **Tips**
        - Mention bed count: *"2BR"* or *"2 bedroom"*
        - Set a budget: *"under $900/bed"*
        - Ask about location: *"near Grainger"*, *"downtown"*
        - Ask about availability: *"August 2026"*
        """
    )
    st.divider()
    if st.button("🗑 Clear chat", use_container_width=True):
        st.session_state.messages = []
        st.rerun()

# ── Header ────────────────────────────────────────────────────────────────────
st.title("🏠 UIUC Housing Assistant")
st.caption("Green Street Realty · Champaign, IL · Ask in plain English")

# ── Suggested questions (shown only when chat is empty) ───────────────────────
SUGGESTED = [
    "2BR under $900/bed — what's available?",
    "Cheapest available 1 bedroom near campus",
    "4BR options and total monthly cost?",
    "Units available for August 2026",
]

# ── Session state ─────────────────────────────────────────────────────────────
if "messages" not in st.session_state:
    st.session_state.messages = []
if "pending" not in st.session_state:
    st.session_state.pending = None

# Show suggestion buttons only on a fresh chat
if not st.session_state.messages:
    st.markdown("**Try asking:**")
    col1, col2 = st.columns(2)
    for i, q in enumerate(SUGGESTED):
        col = col1 if i % 2 == 0 else col2
        if col.button(q, key=f"sq_{i}", use_container_width=True):
            st.session_state.pending = q
            st.rerun()

# ── Avatars ───────────────────────────────────────────────────────────────────
USER_AVATAR      = "🌽"   # corn — UIUC is a land-grant / agriculture school
ASSISTANT_AVATAR = "🏠"   # house — housing assistant


# ── Helpers ───────────────────────────────────────────────────────────────────
def format_response(text: str) -> str:
    """
    Two fixes applied to every LLM response before rendering:

    1. Dollar sign escaping — Streamlit renders $x$ as LaTeX math, which makes
       prices like $900 appear in italic Times New Roman. Escaping \$900 forces
       a literal dollar sign.

    2. Line break fix — Streamlit markdown collapses single \n into one line.
       Insert a blank line before each listing field so every icon starts on
       its own line.
    """
    # Fix 1: escape $ before digits so Streamlit doesn't treat them as LaTeX
    text = re.sub(r'\$(\d)', r'\\$\1', text)

    # Fix 2: ensure each field marker starts on its own line
    for marker in ["📍", "🛏", "💰", "📅", "🔗", "⚠️", "Found", "Note"]:
        text = text.replace(f"\n{marker}", f"\n\n{marker}")

    return text.strip()


def price_str(low, high) -> str:
    """Format a price pair as a readable string."""
    if low is None:
        return "—"
    if low == high:
        return f"${low:,}"
    return f"${low:,}–${high:,}"


def build_summary(docs: list) -> tuple[pd.DataFrame | None, str]:
    """
    Build a grouped comparison table from retrieved docs.
    Rows are sorted by address; within each property group, the Address
    cell is shown only on the first row and left blank on subsequent rows
    so the table visually groups units under their property.
    Returns (dataframe_or_None, summary_text).
    """
    if not docs:
        return None, "No matching listings found."

    rows = []
    for doc in docs:
        m = doc.metadata
        ppb_low   = m.get("price_per_bed_low")
        ppb_high  = m.get("price_per_bed_high")
        ptot_low  = m.get("price_total_low")  or ppb_low
        ptot_high = m.get("price_total_high") or ppb_high

        rows.append({
            "Address":        m.get("address", ""),
            "Unit":           m.get("unit_type", ""),
            "Beds":           m.get("beds", ""),
            "Price/bed":      price_str(ppb_low, ppb_high),
            "Price/mo total": price_str(ptot_low, ptot_high),
            "Availability":   m.get("availability", ""),
            "Link":           m.get("url", ""),
        })

    df = pd.DataFrame(rows)

    # Sort by address so all units of the same property are adjacent
    df = df.sort_values("Address").reset_index(drop=True)

    # Blank out the Address for every row that isn't the first in its group,
    # creating a visual "merged cell" effect without needing actual cell merging
    df["Address"] = df["Address"].where(df["Address"] != df["Address"].shift(), "")

    return df, ""


def render_summary(docs: list) -> None:
    """Render a full-width comparison table, or a no-results message."""
    df, _ = build_summary(docs)

    st.markdown("#### Summary")

    if df is not None and not df.empty:
        st.dataframe(
            df,
            use_container_width=True,
            hide_index=True,
            column_config={
                "Link": st.column_config.LinkColumn("Link", display_text="View →")
            },
        )
    else:
        st.info("No valid properties found for this query.")


# ── Display chat history ──────────────────────────────────────────────────────
for msg in st.session_state.messages:
    avatar = USER_AVATAR if msg["role"] == "user" else ASSISTANT_AVATAR
    with st.chat_message(msg["role"], avatar=avatar):
        st.markdown(msg["content"])


# ── Handle input — from chat box or suggestion button ────────────────────────
user_input = st.chat_input("e.g. 2BR under $900/month near Grainger")

if st.session_state.pending:
    user_input = st.session_state.pending
    st.session_state.pending = None

if user_input:
    # Show user message
    st.session_state.messages.append({"role": "user", "content": user_input})
    with st.chat_message("user", avatar=USER_AVATAR):
        st.markdown(user_input)

    with st.chat_message("assistant", avatar=ASSISTANT_AVATAR):
        try:
            docs = retriever.invoke(user_input)
            render_summary(docs)
        except Exception as e:
            st.markdown(f"⚠️ Something went wrong: {e}")

    st.session_state.messages.append({"role": "assistant", "content": user_input})
