
"""
Volunteer Hub - Streamlit app (app.py)

Run locally:
    pip install streamlit
    streamlit run app.py

Behavior:
  - Loads opportunities from 'opportunities.json' (expects it in same folder)
  - Renders a 3x3 grid of "cards" per page (9 items per page) with equal gaps (CSS grid)
  - Clicking a card appends ?id=<opportunity_id>&page=<n> to the URL and shows a detail view
  - Pagination footer with numbered pages (anchors that set ?page=<n>)
  - Uses modern Streamlit query params API (st.query_params) and st.rerun()
"""

import streamlit as st
from dataclasses import dataclass
import json, math, os, html

st.set_page_config(page_title="Volunteer Hub", layout="wide")

DATA_PATH = os.path.join(os.path.dirname(__file__), "opportunities.json")

@dataclass
class Opportunity:
    id: str
    title: str
    description: str
    organization_url: str
    location: str
    timeframe: str
    requirements: list

    @classmethod
    def from_dict(cls, d):
        return cls(
            id=d["id"],
            title=d.get("title",""),
            description=d.get("description",""),
            organization_url=d.get("organization_url",""),
            location=d.get("location",""),
            timeframe=d.get("timeframe",""),
            requirements=d.get("requirements",[]),
        )

def load_opportunities(path=DATA_PATH):
    if not os.path.exists(path):
        st.error(f"Data file not found: {path}")
        return []
    with open(path,"r",encoding="utf-8") as f:
        raw = json.load(f)
    return [Opportunity.from_dict(r) for r in raw]

ops = load_opportunities()

PAGE_SIZE = 9
total = len(ops)
total_pages = max(1, math.ceil(total / PAGE_SIZE))

# helper to read a single query param value
def qp_get(name, default=None):
    # st.query_params provides get_all; use it for robust behavior
    try:
        vals = st.query_params.get_all(name)
        if vals:
            return vals[0]
    except Exception:
        pass
    v = st.query_params.get(name)
    if isinstance(v, list) and v:
        return v[0]
    return v or default

selected_id = qp_get("id")
page_param = qp_get("page")
try:
    current_page = int(page_param) if page_param is not None else 1
except Exception:
    current_page = 1
current_page = max(1, min(total_pages, current_page))

st.title("Volunteer Hub")
st.write("Find volunteering opportunities — click a card to view details.")

# DETAIL VIEW
if selected_id:
    op = next((o for o in ops if o.id == selected_id), None)
    if op is None:
        st.error("Opportunity not found.")
        if st.button("Back to list"):
            st.query_params.clear()
            st.query_params.from_dict({"page": str(current_page)})
            st.rerun()
    else:
        st.header(op.title)
        st.markdown(op.description)
        st.markdown(f"**Organization:** [{op.organization_url}]({op.organization_url})")
        st.write(f"**Location:** {op.location}")
        st.write(f"**Timeframe:** {op.timeframe}")
        st.write("**Requirements:**")
        for req in op.requirements:
            st.write(f"- {req}")

        if st.button("Back to list"):
            st.query_params.clear()
            st.query_params.from_dict({"page": str(current_page)})
            st.rerun()

# GRID + PAGINATION VIEW
else:
    start = (current_page - 1) * PAGE_SIZE
    page_items = ops[start:start+PAGE_SIZE]

    # CSS + HTML grid (3x3) with equal gaps (gap handles both horizontal and vertical spacing)
    css = """
    <style>
    a {
    color: inherit !important;
    text-decoration: none !important;
    }
    .vol-grid{display:grid;grid-template-columns:repeat(3,1fr);gap:20px;padding:0;margin:0}
    .vol-card{border:1px solid #e0e0e0;border-radius:10px;padding:16px;min-height:140px;display:flex;flex-direction:column;justify-content:space-between;text-decoration:none;color:inherit;background-color:var(--bg-color)}
    .vol-card h3{margin:0 0 8px 0;font-size:1.05rem}
    .vol-card p{margin:0 0 12px 0;color:var(--secondary-text-color)}
    .vol-meta{font-size:0.85rem;color:var(--secondary-text-color)}
    .pagination{display:flex;justify-content:center;gap:8px;margin-top:18px}
    .page-num{padding:6px 10px;border-radius:6px;border:1px solid #cfcfcf;text-decoration:none;color:inherit}
    .page-num.active{background:#0d6efd;color:white;border-color:#0d6efd}
    </style>
    """
    cards = [css, "<div class='vol-grid'>"]
    for op in page_items:
        short_desc = html.escape(op.description[:120]) + ("..." if len(op.description)>120 else "")
        cards.append(
            f"<a class='vol-card' href='?id={op.id}&page={current_page}'>"
            f"<h3>{html.escape(op.title)}</h3>"
            f"<p>{short_desc}</p>"
            f"<div class='vol-meta'>{html.escape(op.location)} • {html.escape(op.timeframe)}</div>"
            "</a>"
        )
    cards.append("</div>")
    st.markdown(''.join(cards), unsafe_allow_html=True)

    # pagination footer (numbered pages)
    footer = ["<div class='pagination'>"]
    for p in range(1, total_pages+1):
        cls = "page-num active" if p == current_page else "page-num"
        footer.append(f"<a class='{cls}' href='?page={p}'>{p}</a>")
    footer.append("</div>")
    st.markdown(''.join(footer), unsafe_allow_html=True)
