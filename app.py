# app.py — Final Clean Version (Dark Theme Only, 1280px Max Width)

import streamlit as st
import pandas as pd
import re
from difflib import SequenceMatcher
from typing import Optional

# ---------------------------
# Streamlit page config
# ---------------------------
st.set_page_config(
    page_title="Budget & Actual Validator",
    page_icon="📖",
    layout="wide"
)

# ---------------------------
# Helpers
# ---------------------------

def parse_number(cell) -> Optional[float]:
    """Parse numbers, including (123) => -123 and comma-formatted numbers."""
    if pd.isna(cell):
        return None
    s = str(cell).strip()
    if s == "":
        return None
    # remove everything except digits, minus, dot, parentheses
    s = re.sub(r"[^\d\-\.\,\(\)]", "", s)
    if re.match(r"^\(.*\)$", s):  # (123)
        val = s[1:-1].replace(",", "")
        try:
            return -float(val)
        except:
            return None
    s = s.replace(",", "")
    try:
        return float(s)
    except:
        return None


def similar(a, b):
    return SequenceMatcher(None, a, b).ratio()


def detect_header_row(df, lb=1, la=2, rb=5, ra=6, max_check=6):
    """Heuristic to detect header row."""
    if df.shape[0] < 2:
        return None
    rows = min(max_check, df.shape[0])
    parsed = []
    for i in range(rows):
        l_b = parse_number(df.iloc[i, lb]) if df.shape[1] > lb else None
        l_a = parse_number(df.iloc[i, la]) if df.shape[1] > la else None
        r_b = parse_number(df.iloc[i, rb]) if df.shape[1] > rb else None
        r_a = parse_number(df.iloc[i, ra]) if df.shape[1] > ra else None
        parsed.append((l_b, l_a, r_b, r_a))

    first = parsed[0]
    first_nums = sum(v is not None for v in first)
    rest = parsed[1:]
    if not rest:
        return None
    rest_nums = [sum(v is not None for v in row) for row in rest]
    avg_rest = sum(rest_nums) / len(rest_nums)

    if first_nums <= 1 and avg_rest >= 2:
        return 0
    return None


# ---------------------------
# CSS — DARK THEME ONLY + 1280px CONTAINER
# ---------------------------

CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700&family=Orbitron:wght@500;700&display=swap');

body {
    background-image: url("https://images.unsplash.com/photo-1526378722484-bd91ca387e72?auto=format&fit=crop&w=1600&q=90");
    background-size: cover;
    background-attachment: fixed;
    color: #EAEAEA;
    font-family: 'Inter', sans-serif;
}

.stApp {
    background: rgba(6, 10, 25, 0.86);
    backdrop-filter: blur(14px);
    border-radius: 16px;
    padding: 2rem;
    margin: 2rem auto;
    max-width: 1280px;
    border: 1px solid rgba(0,255,255,0.12);
    box-shadow: 0 0 45px rgba(0,255,255,0.18);
}

/* HEADER */
.header {
    display: flex;
    align-items: center;
    justify-content: center;
    gap: 22px;
    padding: 10px 0 20px 0;
    animation: floatHeader 6s ease-in-out infinite;
}
@keyframes floatHeader {
    0% { transform: translateY(0px); }
    50% { transform: translateY(-6px); }
    100% { transform: translateY(0px); }
}

.book-icon {
    font-size: 4rem;
    cursor: pointer;
    transition: 0.3s ease;
}
.book-icon:hover {
    transform: scale(1.15) rotate(-6deg);
    text-shadow: 0 0 20px rgba(0,255,255,0.6);
}

.title {
    font-family: 'Orbitron', sans-serif;
    font-size: 2.5rem;
    letter-spacing: 1px;
    font-weight: 700;
    text-align: center;
    color: #00eaff;
    position: relative;
    padding-bottom: 8px;
}
.title::after {
    content: "";
    position: absolute;
    left: 50%;
    width: 70%;
    height: 3px;
    bottom: -4px;
    transform: translateX(-50%) scaleX(0);
    transform-origin: center;
    background: linear-gradient(90deg, #00eaff, #ff7bff);
    border-radius: 4px;
    transition: transform 0.3s ease;
}
.title:hover::after {
    transform: translateX(-50%) scaleX(1);
}

.subtitle {
    text-align: center;
    color: #cfd9df;
    margin-top: 4px;
}

/* Controls */
.controls {
    background: rgba(255,255,255,0.04);
    padding: 16px;
    border-radius: 12px;
    border: 1px solid rgba(255,255,255,0.06);
    margin-bottom: 18px;
}

/* Cards */
.result-card {
    background: rgba(255,255,255,0.03);
    border: 1px solid rgba(255,255,255,0.06);
    border-radius: 12px;
    padding: 14px;
    margin-bottom: 12px;
}

.good {
    color: #9bffda;
    font-weight: 700;
}
.bad {
    color: #ff9b9b;
    font-weight: 700;
}
.warn {
    color: #ffd98b;
    font-weight: 600;
}

@media (max-width: 768px) {
    .title { font-size: 1.8rem; }
    .book-icon { font-size: 3rem; }
    .stApp { padding: 1rem; }
}
</style>
"""

st.markdown(CSS, unsafe_allow_html=True)

# ---------------------------
# Header
# ---------------------------
st.markdown("""
<div class="header">
    <div class="book-icon">📖</div>
    <div>
        <div class="title">Budget & Actual Validation</div>
        <div class="subtitle">Upload your workbook — auto-detect headers, fuzzy match, validate budgets & actuals.</div>
    </div>
</div>
""", unsafe_allow_html=True)

# ---------------------------
# Controls Panel
# ---------------------------

st.markdown('<div class="controls">', unsafe_allow_html=True)
col1, col2, col3 = st.columns([2.5, 1, 1])

with col1:
    uploaded = st.file_uploader("Upload .xlsx / .xls / .et", type=["xlsx", "xls", "et"])
with col2:
    tolerance = st.number_input("Tolerance", value=0.01, min_value=0.0, step=0.01)
with col3:
    auto_skip = st.checkbox("Auto-detect header", value=True)

st.markdown("</div>", unsafe_allow_html=True)

# ---------------------------
# Validation Logic
# ---------------------------

def run_validation(file, tol, auto_header):
    try:
        df = pd.read_excel(file, header=None)
    except Exception as e:
        st.error(f"Cannot read file: {e}")
        return None, None, None

    if df.shape[1] < 7:
        st.error("The sheet must contain at least 7 columns (A..G).")
        return None, None, None

    lp, lb, la = 0, 1, 2
    rp, rb, ra = 4, 5, 6

    skip_row = detect_header_row(df) if auto_header else None

    # Build right side map
    right_map = {}
    for i in range(df.shape[0]):
        if skip_row == i:
            continue
        name = df.iat[i, rp]
        if pd.isna(name):
            continue
        key = str(name).strip().lower()
        right_map[key] = {
            "row": i,
            "name": str(name).strip(),
            "budget": parse_number(df.iat[i, rb]),
            "actual": parse_number(df.iat[i, ra])
        }

    results = []
    mismatches = []

    for i in range(df.shape[0]):
        if skip_row == i:
            continue

        left_name_cell = df.iat[i, lp]
        if pd.isna(left_name_cell):
            continue

        left_name = str(left_name_cell).strip()
        left_norm = left_name.lower()

        left_budget = parse_number(df.iat[i, lb])
        left_actual = parse_number(df.iat[i, la])

        entry = {
            "left_row": i,
            "left_name": left_name,
            "left_budget": left_budget,
            "left_actual": left_actual,
            "match_found": False,
            "right_row": None,
            "right_name": None,
            "right_budget": None,
            "right_actual": None,
            "budget_ok": None,
            "actual_ok": None,
            "notes": []
        }

        # Exact match
        if left_norm in right_map:
            rm = right_map[left_norm]
        else:
            # fuzzy
            best, score = None, 0
            for k, rm in right_map.items():
                s = similar(left_norm, k)
                if s > score:
                    score = s
                    best = rm
            rm = best if score >= 0.6 else None
            if rm:
                entry["notes"].append(f"Fuzzy match (score {score:.2f})")

        # Fill match info
        if rm:
            entry["match_found"] = True
            entry["right_row"] = rm["row"]
            entry["right_name"] = rm["name"]
            entry["right_budget"] = rm["budget"]
            entry["right_actual"] = rm["actual"]
        else:
            entry["notes"].append("No matching DBDisplayName found")

        # Compare
        if entry["match_found"]:
            if entry["right_budget"] is None or left_budget is None:
                entry["notes"].append("Unparsable budget")
            else:
                entry["budget_ok"] = abs(left_budget - entry["right_budget"]) <= tol
                if entry["budget_ok"] is False:
                    entry["notes"].append(f"Budget mismatch")

            if entry["right_actual"] is None or left_actual is None:
                entry["notes"].append("Unparsable actual")
            else:
                entry["actual_ok"] = abs(left_actual - entry["right_actual"]) <= tol
                if entry["actual_ok"] is False:
                    entry["notes"].append("Actual mismatch")

        results.append(entry)
        if (not entry["match_found"]) or entry["budget_ok"] is False or entry["actual_ok"] is False:
            mismatches.append(entry)

    return results, mismatches, skip_row

# ---------------------------
# Run validation
# ---------------------------

if uploaded:
    with st.spinner("Analyzing workbook..."):
        results, mismatches, hdr = run_validation(uploaded, tolerance, auto_skip)

    if hdr is not None:
        st.success(f"Header row auto-detected at index {hdr}")

    # Summary
    st.markdown(f"**Total parameters checked:** {len(results)}")
    st.markdown(f"**Total mismatches:** <span class='warn'>{len(mismatches)}</span>", unsafe_allow_html=True)

    # Download mismatches
    if mismatches:
        df_exp = pd.DataFrame([{
            "Left Row": m["left_row"],
            "Left Name": m["left_name"],
            "Left Budget": m["left_budget"],
            "Left Actual": m["left_actual"],
            "Right Row": m["right_row"],
            "Right Name": m["right_name"],
            "Right Budget": m["right_budget"],
            "Right Actual": m["right_actual"],
            "Notes": " | ".join(m["notes"])
        } for m in mismatches])
        st.download_button(
            "Download mismatches CSV",
            df_exp.to_csv(index=False).encode("utf-8"),
            file_name="mismatches.csv"
        )

    # Results view
    show_mis = st.checkbox("Show only mismatches", True)
    display = mismatches if show_mis else results

    st.markdown("## Validation Results")
    for m in display:
        st.markdown("<div class='result-card'>", unsafe_allow_html=True)
        colA, colB = st.columns([3, 1])
        with colA:
            st.markdown(f"**Parameter:** {m['left_name']} (Row {m['left_row']})")
            st.markdown(f"Matched: **{m.get('right_name','—')}** (Row {m.get('right_row','—')})")
        with colB:
            if m.get("budget_ok") and m.get("actual_ok"):
                st.markdown("<div class='good'>All OK</div>", unsafe_allow_html=True)
            else:
                st.markdown("<div class='bad'>Needs attention</div>", unsafe_allow_html=True)

        # Show mismatch notes + actual numbers
        for note in m["notes"]:
            if "Budget mismatch" in note:
                st.markdown(
                    f"<div class='warn'>• Budget mismatch → Left: <b>{m.get('left_budget')}</b>, Right: <b>{m.get('right_budget')}</b></div>",
                    unsafe_allow_html=True,
                )
            elif "Actual mismatch" in note:
                st.markdown(
                    f"<div class='warn'>• Actual mismatch → Left: <b>{m.get('left_actual')}</b>, Right: <b>{m.get('right_actual')}</b></div>",
                    unsafe_allow_html=True,
                )
            else:
                st.markdown(f"<div class='warn'>• {note}</div>", unsafe_allow_html=True)

        st.markdown("</div>", unsafe_allow_html=True)

else:
    st.info("Upload a workbook to begin validation.")
