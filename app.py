# app.py
"""
Dynamic Budget & Actual Validator (final)
- Dark theme, 1280px centered layout
- User chooses which columns to validate (fully dynamic)
- Header row selection (or no header)
- Fuzzy-match names and numeric comparison
- Shows mismatch values and notes
"""

import streamlit as st
import pandas as pd
import re
from difflib import SequenceMatcher
from typing import Optional, List

# ---------------------------
# Developer-provided local path (kept per instruction)
# ---------------------------
UPLOADED_LOCAL_PATH = "/mnt/data/189d892e-48db-4c6e-be43-8d2876146188.png"

# ---------------------------
# Page config
# ---------------------------
st.set_page_config(page_title="Budget & Actual Validator", page_icon="📖", layout="wide")

# ---------------------------
# Utility functions
# ---------------------------
def parse_number(cell) -> Optional[float]:
    """Return float or None if unparsable. Handles parentheses as negatives and commas/currency."""
    if pd.isna(cell):
        return None
    s = str(cell).strip()
    if s == "":
        return None
    # remove letters and common currency symbols but keep digits, minus, dot, comma, parentheses
    s = re.sub(r"[^\d\-\.\,\(\)]", "", s)
    # parentheses => negative
    if re.match(r"^\(.*\)$", s):
        inner = s[1:-1].replace(",", "")
        try:
            return -float(inner)
        except:
            return None
    # remove commas
    s = s.replace(",", "")
    try:
        return float(s)
    except:
        return None

def similar(a: str, b: str) -> float:
    return SequenceMatcher(None, str(a).lower(), str(b).lower()).ratio()

# ---------------------------
# Heuristic header detection (keeps original logic but not required)
# ---------------------------
def detect_header_row(df: pd.DataFrame, max_check: int = 6) -> Optional[int]:
    """Return an index that appears to be the header row (0-based) or None."""
    if df.shape[0] < 2:
        return None
    top = min(max_check, df.shape[0])
    parsed = []
    for i in range(top):
        # check first few columns for numeric parsability heuristics
        row_vals = []
        for j in range(min(6, df.shape[1])):  # up to 6 columns for heuristic
            try:
                row_vals.append(parse_number(df.iat[i, j]))
            except Exception:
                row_vals.append(None)
        parsed.append(row_vals)
    first = parsed[0]
    first_count = sum(1 for v in first if v is not None)
    rest = parsed[1:]
    if not rest:
        return None
    rest_counts = [sum(1 for v in r if v is not None) for r in rest]
    avg_rest = sum(rest_counts) / len(rest_counts)
    # if first row is mostly unparsable but subsequent rows have numeric values, it's likely a header
    if first_count <= 1 and avg_rest >= 2:
        return 0
    return None

# ---------------------------
# CSS - Dark theme & layout (1280px centered)
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
    background: rgba(6,10,25,0.86);
    backdrop-filter: blur(14px);
    border-radius: 16px;
    padding: 2rem;
    margin: 2rem auto;
    max-width: 1280px;
    border: 1px solid rgba(0,255,255,0.12);
    box-shadow: 0 0 45px rgba(0,255,255,0.18);
}

/* header */
.header {
    display:flex;
    align-items:center;
    justify-content:center;
    gap:22px;
    padding:10px 0 18px 0;
    animation: floatHeader 6s ease-in-out infinite;
}
@keyframes floatHeader {
    0% { transform: translateY(0px); } 50% { transform: translateY(-6px); } 100% { transform: translateY(0px); }
}

.book-icon { font-size: 3.8rem; cursor:pointer; transition:0.28s; }
.book-icon:hover { transform: scale(1.12) rotate(-6deg); text-shadow: 0 0 20px rgba(0,255,255,0.6); }

.title { font-family:'Orbitron',sans-serif; font-size:2.4rem; color:#00eaff; position:relative; padding-bottom:6px; }
.title::after { content:""; position:absolute; left:50%; transform:translateX(-50%) scaleX(0); bottom:-2px; height:4px; width:70%; background:linear-gradient(90deg,#00eaff,#ff7bff); border-radius:4px; transition:0.25s;}
.title:hover::after { transform:translateX(-50%) scaleX(1); }

.subtitle { color:#cfd9df; font-size:0.98rem; margin-top:2px; }

/* controls */
.controls { background: rgba(255,255,255,0.04); padding:12px; border-radius:10px; border:1px solid rgba(255,255,255,0.06); margin-bottom:16px; }

/* result cards */
.result-card { background: rgba(255,255,255,0.03); border:1px solid rgba(255,255,255,0.06); border-radius:12px; padding:12px; margin-bottom:10px; }
.good { color:#9bffda; font-weight:700; }
.bad { color:#ff9b9b; font-weight:700; }
.warn { color:#ffd98b; font-weight:600; }

.footer { font-family: 'Orbitron', monospace; font-size:1.05rem; color:#00eaff; text-align:center; margin-top:28px; padding-top:10px; letter-spacing:1px; text-shadow:0 0 12px rgba(0,255,255,0.6); opacity:0.95; }
.footer:hover { transform: translateY(-3px); text-shadow: 0 0 18px rgba(0,255,255,0.9); }

/* responsive */
@media (max-width: 992px) {
    .title { font-size:1.8rem; }
    .book-icon { font-size:2.6rem; }
    .stApp { padding:1rem; margin: 10px; }
}
</style>
"""
st.markdown(CSS, unsafe_allow_html=True)

# ---------------------------
# Header (clean)
# ---------------------------
st.markdown(
    """
    <div class="header">
      <div class="book-icon">📖</div>
      <div>
        <div class="title">Budget & Actual Validation</div>
        <div class="subtitle">Choose columns to compare — fully dynamic & robust parsing.</div>
      </div>
    </div>
    """,
    unsafe_allow_html=True
)

# ---------------------------
# Controls: file upload + header selection + similarity threshold
# ---------------------------
st.markdown('<div class="controls">', unsafe_allow_html=True)
c1, c2, c3 = st.columns([2.5, 1, 1])

with c1:
    uploaded = st.file_uploader("Upload .xlsx / .xls / .et", type=["xlsx", "xls", "et"])
with c2:
    tolerance = st.number_input("Numeric tolerance (abs)", min_value=0.0, value=0.01, step=0.01)
with c3:
    sim_thresh = st.slider("Name fuzzy threshold", min_value=0.4, max_value=1.0, value=0.60, step=0.01)

st.markdown("</div>", unsafe_allow_html=True)

# ---------------------------
# Helper: convert column index to letter (0->A, 1->B, etc.)
# ---------------------------
def col_letter(idx: int) -> str:
    # support indices up to ~1000 (not necessary huge)
    letters = ""
    i = idx
    while True:
        i, r = divmod(i, 26)
        letters = chr(65 + r) + letters
        if i == 0:
            break
        i -= 1
    return letters

# ---------------------------
# If file uploaded, parse and show dynamic mapping UI
# ---------------------------
if uploaded:
    try:
        raw_df = pd.read_excel(uploaded, header=None)
    except Exception as e:
        st.error(f"Failed to read workbook: {e}\nIf this is a .et file save as .xlsx and re-upload.")
        st.stop()

    st.markdown("### Sheet preview (first 8 rows)")
    st.dataframe(raw_df.head(8))

    # Allow user choose header row or "No header"
    header_options = ["No header"] + [f"Row {i} (0-based)" for i in range(min(10, raw_df.shape[0]))]
    header_sel = st.selectbox("Select header row (if your sheet uses a header row)", header_options, index=0)

    if header_sel == "No header":
        header_row = None
        # column labels will be letters
        display_cols = [f"{col_letter(i)}" for i in range(raw_df.shape[1])]
        df = raw_df.copy()
    else:
        header_row = int(header_sel.replace("Row ", "").split(" ")[0])
        # build df where header row becomes column names, and data starts after header row
        header_values = raw_df.iloc[header_row].astype(str).fillna("").tolist()
        # Create columns names - if duplicates, append index
        seen = {}
        cols = []
        for i, v in enumerate(header_values):
            txt = v.strip() if v.strip() != "" else f"Column_{col_letter(i)}"
            if txt in seen:
                seen[txt] += 1
                txt = f"{txt}_{seen[txt]}"
            else:
                seen[txt] = 0
            cols.append(txt)
        df = raw_df.copy()
        df.columns = list(range(df.shape[1]))  # ensure integer columns
        df = df.iloc[header_row + 1 :].reset_index(drop=True)
        df.columns = cols
        display_cols = cols

    # create options for dropdowns (show both index and readable label)
    col_options = []
    for idx, label in enumerate(display_cols):
        col_options.append((idx, label))  # idx always used as identifier

    def option_label(opt):
        return f"{opt[1]} ({col_letter(opt[0])})"

    # show mapping UI
    st.markdown("### Map columns for validation")
    st.info("Pick which columns contain the *parameter name*, *budget* and *actual* for LEFT and RIGHT sets. Any columns can be selected.")

    # Build dropdown choices mapping: key is idx, value label
    choice_map = {opt[0]: opt[1] for opt in col_options}
    # present in two columns for left and right mapping
    l1, l2 = st.columns(2)

    with l1:
        left_name_idx = st.selectbox("Left — Parameter column (names)", options=list(choice_map.keys()), format_func=lambda k: f"{choice_map[k]} ({col_letter(k)})", index=0)
        left_budget_idx = st.selectbox("Left — Budget column", options=list(choice_map.keys()), format_func=lambda k: f"{choice_map[k]} ({col_letter(k)})", index=min(1, len(choice_map)-1))
        left_actual_idx = st.selectbox("Left — Actual column", options=list(choice_map.keys()), format_func=lambda k: f"{choice_map[k]} ({col_letter(k)})", index=min(2, len(choice_map)-1))
    with l2:
        right_name_idx = st.selectbox("Right — Parameter column (names)", options=list(choice_map.keys()), format_func=lambda k: f"{choice_map[k]} ({col_letter(k)})", index=min(3, len(choice_map)-1))
        right_budget_idx = st.selectbox("Right — Budget column", options=list(choice_map.keys()), format_func=lambda k: f"{choice_map[k]} ({col_letter(k)})", index=min(4, len(choice_map)-1))
        right_actual_idx = st.selectbox("Right — Actual column", options=list(choice_map.keys()), format_func=lambda k: f"{choice_map[k]} ({col_letter(k)})", index=min(5, len(choice_map)-1))

    # Option: choose rows range to process (optional)
    st.markdown("### Row selection (optional)")
    total_rows = df.shape[0]
    r1, r2 = st.columns([1,1])
    with r1:
        start_row = st.number_input("Start row (0-based relative to data shown)", min_value=0, max_value=max(0,total_rows-1), value=0, step=1)
    with r2:
        end_row = st.number_input("End row (0-based relative to data shown)", min_value=0, max_value=max(0,total_rows-1), value=max(0,total_rows-1), step=1)

    if start_row > end_row:
        st.error("Start row cannot be greater than end row.")
        st.stop()

    # extract helper to get cell from df given display-mode (header/no header)
    def get_cell(df_inner, row_idx: int, col_idx: int):
        """Return cell value; if df has header names, col_idx may be label or index.
           In our mapping col_idx refers to display index; convert to df column."""
        if header_row is None:
            # df columns are integer indices 0..n-1
            return df_inner.iat[row_idx, col_idx]
        else:
            # df columns are header labels (we created cols list)
            col_label = display_cols[col_idx]
            return df_inner.iat[row_idx, df_inner.columns.get_loc(col_label)]

    # Build mapping dictionary to be used by validation
    mapping = {
        "left_name_idx": left_name_idx,
        "left_budget_idx": left_budget_idx,
        "left_actual_idx": left_actual_idx,
        "right_name_idx": right_name_idx,
        "right_budget_idx": right_budget_idx,
        "right_actual_idx": right_actual_idx,
    }

    # Run validation button
    if st.button("Run Validation"):
        # Build right side map: key -> (row_index_in_df, name_str, budget_value, actual_value)
        right_map = {}
        # iterate only over selected rows
        for r in range(start_row, end_row + 1):
            try:
                name_cell = get_cell(df, r, mapping["right_name_idx"])
            except Exception:
                continue
            if pd.isna(name_cell) or str(name_cell).strip() == "":
                continue
            name_key = str(name_cell).strip().lower()
            budget_val = parse_number(get_cell(df, r, mapping["right_budget_idx"]))
            actual_val = parse_number(get_cell(df, r, mapping["right_actual_idx"]))
            right_map[name_key] = {
                "row": r,
                "name": str(name_cell).strip(),
                "budget": budget_val,
                "actual": actual_val
            }

        # Iterate left side and compare
        results = []
        mismatches = []
        for r in range(start_row, end_row + 1):
            try:
                left_name_cell = get_cell(df, r, mapping["left_name_idx"])
            except Exception:
                continue
            if pd.isna(left_name_cell) or str(left_name_cell).strip() == "":
                continue
            left_name = str(left_name_cell).strip()
            left_key = left_name.lower()
            left_budget = parse_number(get_cell(df, r, mapping["left_budget_idx"]))
            left_actual = parse_number(get_cell(df, r, mapping["left_actual_idx"]))

            entry = {
                "left_row": r,
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

            # exact match
            if left_key in right_map:
                rm = right_map[left_key]
            else:
                # fuzzy match find best candidate (choose highest ratio)
                best = None
                best_score = 0.0
                for k, v in right_map.items():
                    s = similar(left_key, k)
                    if s > best_score:
                        best_score = s
                        best = v
                if best and best_score >= sim_thresh:
                    rm = best
                    entry["notes"].append(f"Fuzzy match (score {best_score:.2f})")
                else:
                    rm = None
                    entry["notes"].append("No matching parameter found on right side")

            # fill rm info
            if rm:
                entry["match_found"] = True
                entry["right_row"] = rm["row"]
                entry["right_name"] = rm["name"]
                entry["right_budget"] = rm["budget"]
                entry["right_actual"] = rm["actual"]

                # compare budgets
                if entry["right_budget"] is None or entry["left_budget"] is None:
                    entry["notes"].append("Budget unparsable on one side")
                    entry["budget_ok"] = None
                else:
                    entry["budget_ok"] = abs(entry["left_budget"] - entry["right_budget"]) <= tolerance
                    if not entry["budget_ok"]:
                        entry["notes"].append("Budget mismatch")

                # compare actuals
                if entry["right_actual"] is None or entry["left_actual"] is None:
                    entry["notes"].append("Actual unparsable on one side")
                    entry["actual_ok"] = None
                else:
                    entry["actual_ok"] = abs(entry["left_actual"] - entry["right_actual"]) <= tolerance
                    if not entry["actual_ok"]:
                        entry["notes"].append("Actual mismatch")
            # record
            results.append(entry)
            if (not entry["match_found"]) or entry["budget_ok"] is False or entry["actual_ok"] is False:
                mismatches.append(entry)

        # Summary
        st.markdown(f"**Total parameters checked:** {len(results)}")
        st.markdown(f"**Total mismatches/attention:** <span style='color:#ffd98b;font-weight:700'>{len(mismatches)}</span>", unsafe_allow_html=True)

        # Download CSV of mismatches
        if mismatches:
            df_out = pd.DataFrame([{
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
            csv_bytes = df_out.to_csv(index=False).encode("utf-8")
            st.download_button("Download mismatches CSV", data=csv_bytes, file_name="mismatches.csv", mime="text/csv")

        # Display results (option to show all or only mismatches)
        show_only_mismatch = st.checkbox("Show only mismatches in results", value=True)
        display_list = mismatches if show_only_mismatch else results

        st.markdown("### Validation Results")
        for m in display_list:
            st.markdown('<div class="result-card">', unsafe_allow_html=True)
            colA, colB = st.columns([3, 1])
            with colA:
                st.markdown(f"**Parameter:** {m['left_name']}  —  <span style='color:rgba(255,255,255,0.78)'>Left row {m['left_row']}</span>", unsafe_allow_html=True)
                st.markdown(f"**Matched to:** {m.get('right_name','—')}  —  <span style='color:rgba(255,255,255,0.78)'>Right row {m.get('right_row','—')}</span>", unsafe_allow_html=True)
                # numeric display
                st.markdown(f"- Left Budget: **{m.get('left_budget')}**    |    Right Budget: **{m.get('right_budget')}**", unsafe_allow_html=True)
                st.markdown(f"- Left Actual: **{m.get('left_actual')}**    |    Right Actual: **{m.get('right_actual')}**", unsafe_allow_html=True)
                # detailed notes with numeric values for mismatches
                for note in m["notes"]:
                    if "Budget mismatch" in note:
                        st.markdown(f"<div style='color:#ffd98b'>• Budget mismatch → Left: <b>{m.get('left_budget')}</b>, Right: <b>{m.get('right_budget')}</b></div>", unsafe_allow_html=True)
                    elif "Actual mismatch" in note:
                        st.markdown(f"<div style='color:#ffd98b'>• Actual mismatch → Left: <b>{m.get('left_actual')}</b>, Right: <b>{m.get('right_actual')}</b></div>", unsafe_allow_html=True)
                    else:
                        st.markdown(f"<div style='color:#ffd98b'>• {note}</div>", unsafe_allow_html=True)
            with colB:
                if (m.get("budget_ok") is True) and (m.get("actual_ok") is True):
                    st.markdown("<div style='color:#9bffda;font-weight:700'>All values match</div>", unsafe_allow_html=True)
                else:
                    st.markdown("<div style='color:#ff9b9b;font-weight:700'>Attention needed</div>", unsafe_allow_html=True)
            st.markdown("</div>", unsafe_allow_html=True)

    # end Run Validation button
else:
    st.info("Upload a workbook to begin validation.")

# ---------------------------
# Footer
# ---------------------------
st.markdown("<div class='footer'>Built with ❤️ using FastAPI + Streamlit by <b>Madhukesh</b></div>", unsafe_allow_html=True)
