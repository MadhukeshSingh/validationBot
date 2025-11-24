# app.py
import streamlit as st
import pandas as pd
import re
import io
from difflib import SequenceMatcher

# ---------------------------
# Page config
# ---------------------------
st.set_page_config(page_title="Budget Validator", page_icon="🛰️", layout="wide")

# ---------------------------
# Helper: parse numbers
# ---------------------------
def parse_number(cell):
    """Return float or None if unparsable. Handles (123), commas, currency symbols."""
    if pd.isna(cell):
        return None
    s = str(cell).strip()
    if s == "":
        return None
    # remove common currency & letters
    s = re.sub(r"[^\d\-\.\,\(\)]", "", s)
    # parentheses => negative
    if re.match(r"^\(.*\)$", s):
        inner = s[1:-1].replace(",", "")
        try:
            return -float(inner)
        except:
            return None
    s = s.replace(",", "")
    # final try
    try:
        return float(s)
    except:
        return None

# ---------------------------
# Helper: fuzzy match
# ---------------------------
def similar(a, b):
    return SequenceMatcher(None, a, b).ratio()

# ---------------------------
# CSS / Futuristic UI + Responsive
# ---------------------------
SPLASH_PATH = "/mnt/data/Screenshot (38).png"  # provided splash in runtime

st.markdown(
    f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600;700&family=Orbitron:wght@400;700&display=swap');

:root{{
  --accent: #7be2ff;
  --accent-2: #7f7dff;
  --glass: rgba(255,255,255,0.04);
  --glass-2: rgba(255,255,255,0.02);
  --card: rgba(255,255,255,0.03);
}}

html, body, [class*="css"] {{
    font-family: 'Inter', sans-serif;
    color: #e8f6ff;
    background: radial-gradient(circle at 10% 10%, rgba(127,125,255,0.08), transparent 10%),
                radial-gradient(circle at 90% 80%, rgba(123,226,255,0.04), transparent 10%),
                linear-gradient(180deg, #020617 0%, #071532 50%, #001428 100%);
    min-height:100vh;
}}

/* starfield small dots */
body::after {{
  content: "";
  position: fixed;
  inset: 0;
  background-image:
    radial-gradient(1px 1px at 20% 10%, rgba(255,255,255,0.06) 50%, transparent 51%),
    radial-gradient(1px 1px at 40% 70%, rgba(255,255,255,0.04) 50%, transparent 51%),
    radial-gradient(1px 1px at 60% 30%, rgba(255,255,255,0.05) 50%, transparent 51%),
    radial-gradient(1px 1px at 80% 50%, rgba(255,255,255,0.04) 50%, transparent 51%);
  z-index:0;
  opacity:0.7;
  pointer-events:none;
}}

.header {{
  display:flex;
  align-items:center;
  gap:18px;
  padding:14px;
  border-radius:12px;
  background: linear-gradient(90deg, rgba(255,255,255,0.02), rgba(255,255,255,0.01));
  box-shadow: 0 8px 30px rgba(2,6,23,0.6);
  margin-bottom:12px;
}}

.logo {{
  width:80px;
  height:80px;
  border-radius:16px;
  background: linear-gradient(135deg, rgba(123,226,255,0.18), rgba(127,125,255,0.14));
  display:flex;
  align-items:center;
  justify-content:center;
  transition: transform 0.25s ease, box-shadow 0.25s ease;
  cursor: pointer;
}}
.logo img {{
  width:72px;
  height:72px;
  object-fit:cover;
  border-radius:12px;
}}

.logo:hover {{
  transform: translateY(-6px) rotate(-6deg) scale(1.03);
  box-shadow: 0 10px 30px rgba(127,125,255,0.18);
}}

.title {{
  font-family: 'Orbitron', monospace;
  letter-spacing:1px;
}}

.controls {{
  background: var(--glass);
  padding:12px;
  border-radius:10px;
  margin-bottom:12px;
}}

.input-field {{
  background: var(--glass-2);
  padding:8px;
  border-radius:8px;
  transition: box-shadow 0.18s ease, transform 0.12s ease;
}}
.input-field:hover {{
  transform: translateY(-4px);
  box-shadow: 0 8px 24px rgba(123,226,255,0.06);
}}

.result-card {{
  background: linear-gradient(180deg, rgba(255,255,255,0.02), rgba(255,255,255,0.01));
  border-radius:10px;
  padding:12px;
  margin-bottom:10px;
  transition: transform 0.14s ease, box-shadow 0.14s ease;
}}
.result-card:hover {{
  transform: translateY(-6px);
  box-shadow: 0 20px 50px rgba(2,6,23,0.6);
}}

.small-muted {{
  color: rgba(220,230,255,0.6);
  font-size:0.9rem;
}}

.kv {{
  display:flex;
  gap:8px;
  flex-wrap:wrap;
  align-items:center;
  margin-top:6px;
}}

.bad {{ color:#ff9b9b; font-weight:600; }}
.good {{ color:#9bffda; font-weight:700; }}
.warn {{ color:#ffd98b; font-weight:700; }}

/* responsive tweaks */
@media (max-width: 768px) {{
  .header {{ flex-direction:row; gap:12px; padding:10px; }}
  .logo {{ width:64px; height:64px; }}
}}
</style>
""",
    unsafe_allow_html=True,
)

# ---------------------------
# Header with splash image and hoverable icon
# ---------------------------
st.markdown(
    """
<div class="header">
  <div class="logo" title="Budget Validator">
    <img src="file://{splash}" alt="splash" />
  </div>
  <div>
    <div class="title" style="font-size:20px;">Budget & Actual Validator</div>
    <div class="small-muted">Upload your workbook — app auto-detects & skips header rows and compares values with fuzzy matching.</div>
  </div>
</div>
""".format(splash=SPLASH_PATH),
    unsafe_allow_html=True,
)

# ---------------------------
# Controls
# ---------------------------
st.markdown('<div class="controls">', unsafe_allow_html=True)
col1, col2, col3 = st.columns([2, 1, 1])

with col1:
    uploaded = st.file_uploader("Upload .xlsx / .xls / .et (if .et can't be parsed, save as .xlsx)", type=["xlsx", "xls", "et"])
with col2:
    tolerance = st.number_input("Numeric tolerance (absolute)", min_value=0.0, value=0.01, step=0.01)
with col3:
    auto_skip = st.checkbox("Auto-detect header row", value=True)

st.markdown("</div>", unsafe_allow_html=True)

# ---------------------------
# Utility: detect header row heuristics
# ---------------------------
def detect_header_row(df, left_budget_col=1, left_actual_col=2, right_budget_col=5, right_actual_col=6, max_check_rows=6):
    """
    Heuristic: check first `max_check_rows` rows. If first row budget/actual are unparsable (None)
    but most rows after are numeric -> first row is header.
    Returns index to skip (0-based) or None.
    """
    if df.shape[0] < 2:
        return None
    top = min(max_check_rows, df.shape[0])
    # parse budgets for top rows
    parsed = []
    for i in range(top):
        lb = parse_number(df.iloc[i, left_budget_col]) if df.shape[1] > left_budget_col else None
        la = parse_number(df.iloc[i, left_actual_col]) if df.shape[1] > left_actual_col else None
        rb = parse_number(df.iloc[i, right_budget_col]) if df.shape[1] > right_budget_col else None
        ra = parse_number(df.iloc[i, right_actual_col]) if df.shape[1] > right_actual_col else None
        parsed.append((lb, la, rb, ra))
    # Check first row has mostly None while subsequent rows have numeric values
    first = parsed[0]
    first_numeric_count = sum(1 for v in first if v is not None)
    subsequent = parsed[1:]
    subsequent_numeric_counts = [sum(1 for v in row if v is not None) for row in subsequent] if subsequent else []
    avg_sub = sum(subsequent_numeric_counts) / len(subsequent_numeric_counts) if subsequent_numeric_counts else 0
    # If first row numeric count less than 1 and avg_sub > 1 => first row is header
    if first_numeric_count <= 1 and avg_sub >= 2:
        return 0
    return None

# ---------------------------
# Main processing
# ---------------------------
if uploaded:
    st.markdown('<div class="input-field">', unsafe_allow_html=True)
    st.info(f"File: {uploaded.name}")
    # read file
    try:
        # pandas may fail on .et; user should resave as .xlsx if so
        df = pd.read_excel(uploaded, sheet_name=0, header=None)
    except Exception as e:
        st.error(f"Failed to read workbook: {e}\nTry opening in WPS/Excel and Save As .xlsx then upload.")
        st.stop()

    # Ensure enough columns
    if df.shape[1] < 7:
        st.error("Workbook must have at least 7 columns (A..G) — we expect left params on A,B,C and right mapping on E,F,G.")
        st.stop()

    st.markdown("</div>", unsafe_allow_html=True)

    # columns indexes (0-based)
    left_param_col = 0
    left_budget_col = 1
    left_actual_col = 2
    right_name_col = 4
    right_budget_col = 5
    right_actual_col = 6

    # detect header
    skip_index = None
    if auto_skip:
        skip_index = detect_header_row(df, left_budget_col, left_actual_col, right_budget_col, right_actual_col)
    # show detection result
    if skip_index is not None:
        st.success(f"Auto-detected header row at row index {skip_index} — that row will be skipped from comparisons.")
    else:
        st.info("No header row auto-detected. If your file has headers in the first row, enable 'Auto-detect header row' or manually ensure first row is header-like.")

    # Build right side lookup (normalize keys)
    right_map = {}
    for idx in range(df.shape[0]):
        if skip_index is not None and idx == skip_index:
            continue
        name_cell = df.iat[idx, right_name_col]
        if pd.isna(name_cell):
            continue
        key = str(name_cell).strip().lower()
        right_map[key] = {
            "row": idx,
            "name": str(name_cell).strip(),
            "budget": parse_number(df.iat[idx, right_budget_col]) if df.shape[1] > right_budget_col else None,
            "actual": parse_number(df.iat[idx, right_actual_col]) if df.shape[1] > right_actual_col else None,
        }

    # Now iterate left side and validate
    results = []
    mismatches = []
    for idx in range(df.shape[0]):
        if skip_index is not None and idx == skip_index:
            continue
        left_name_cell = df.iat[idx, left_param_col]
        if pd.isna(left_name_cell):
            continue
        left_key = str(left_name_cell).strip()
        left_key_norm = left_key.lower()

        left_budget = parse_number(df.iat[idx, left_budget_col]) if df.shape[1] > left_budget_col else None
        left_actual = parse_number(df.iat[idx, left_actual_col]) if df.shape[1] > left_actual_col else None

        entry = {
            "left_row": idx,
            "left_name": left_key,
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

        # Exact match first
        if left_key_norm in right_map:
            rm = right_map[left_key_norm]
            entry["match_found"] = True
            entry["right_row"] = rm["row"]
            entry["right_name"] = rm["name"]
            entry["right_budget"] = rm["budget"]
            entry["right_actual"] = rm["actual"]
        else:
            # fuzzy match: find best candidate by similarity threshold
            best = None
            best_score = 0.0
            for rkey, rm in right_map.items():
                s = similar(left_key_norm, rkey)
                if s > best_score:
                    best_score = s
                    best = rm
            # accept fuzzy only if reasonably close
            if best and best_score >= 0.6:
                entry["match_found"] = True
                entry["right_row"] = best["row"]
                entry["right_name"] = best["name"]
                entry["right_budget"] = best["budget"]
                entry["right_actual"] = best["actual"]
                entry["notes"].append(f"Fuzzy match used (score {best_score:.2f})")
            else:
                entry["notes"].append("No matching DBDisplayName found on right side")

        # Compare budget
        if entry["match_found"]:
            # budget
            if entry["right_budget"] is None or left_budget is None:
                entry["budget_ok"] = None
                entry["notes"].append("Budget could not be parsed on one side")
            else:
                entry["budget_ok"] = abs(left_budget - entry["right_budget"]) <= tolerance
                if not entry["budget_ok"]:
                    entry["notes"].append(f"Budget mismatch: left={left_budget} right={entry['right_budget']}")

            # actual
            if entry["right_actual"] is None or left_actual is None:
                entry["actual_ok"] = None
                entry["notes"].append("Actual could not be parsed on one side")
            else:
                entry["actual_ok"] = abs(left_actual - entry["right_actual"]) <= tolerance
                if not entry["actual_ok"]:
                    entry["notes"].append(f"Actual mismatch: left={left_actual} right={entry['right_actual']}")

        # record results
        results.append(entry)
        if (not entry["match_found"]) or (entry["budget_ok"] is False) or (entry["actual_ok"] is False):
            mismatches.append(entry)

    # Summary
    st.markdown('<div class="kv">', unsafe_allow_html=True)
    st.markdown(f"<div class='small-muted'>Total parameters checked: <strong>{len(results)}</strong></div>", unsafe_allow_html=True)
    st.markdown(f"<div class='small-muted'>Total mismatches/attention: <strong class='warn'>{len(mismatches)}</strong></div>", unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

    # Buttons to export
    if mismatches:
        export_df = []
        for m in mismatches:
            export_df.append({
                "Left Row": m["left_row"],
                "Left Name": m["left_name"],
                "Left Budget": m["left_budget"],
                "Left Actual": m["left_actual"],
                "Right Row": m["right_row"],
                "Right Name": m["right_name"],
                "Right Budget": m["right_budget"],
                "Right Actual": m["right_actual"],
                "Notes": " | ".join(m["notes"])
            })
        edf = pd.DataFrame(export_df)
        csv = edf.to_csv(index=False).encode("utf-8")
        st.download_button("Download mismatches CSV", data=csv, file_name="mismatches.csv", mime="text/csv")

    # Display mismatches (or all, toggle)
    show_only_mismatch = st.checkbox("Show only mismatches in results", value=True)

    display_list = mismatches if show_only_mismatch else results

    st.markdown("### Validation Results")
    for m in display_list:
        left = m["left_name"]
        right = m.get("right_name") or "—"
        left_row = m["left_row"]
        right_row = m.get("right_row") if m.get("right_row") is not None else "—"
        notes = m["notes"]

        badge = "good" if (m.get("budget_ok") or m.get("actual_ok")) else "bad"
        # card
        st.markdown('<div class="result-card">', unsafe_allow_html=True)
        colA, colB = st.columns([3,2])
        with colA:
            st.markdown(f"**Parameter:** {left}  —  <span class='small-muted'>Left row {left_row}</span>", unsafe_allow_html=True)
            st.markdown(f"**Matched to:** {right}  —  <span class='small-muted'>Right row {right_row}</span>", unsafe_allow_html=True)
        with colB:
            if m.get("budget_ok") is True and m.get("actual_ok") is True:
                st.markdown(f"<div class='good'>All values match</div>", unsafe_allow_html=True)
            else:
                st.markdown(f"<div class='bad'>Attention needed</div>", unsafe_allow_html=True)

        # details
        st.markdown("<div style='margin-top:8px'>", unsafe_allow_html=True)
        st.markdown(f"- Left Budget: **{m.get('left_budget')}**    |    Right Budget: **{m.get('right_budget')}**", unsafe_allow_html=True)
        st.markdown(f"- Left Actual: **{m.get('left_actual')}**    |    Right Actual: **{m.get('right_actual')}**", unsafe_allow_html=True)
        if notes:
            for n in notes:
                st.markdown(f"<div class='warn'>• {n}</div>", unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)

    # final tips
    st.markdown("<hr>", unsafe_allow_html=True)
    st.markdown("<div class='small-muted'>Tips: If you see parsing issues, open your file in Excel/WPS and ensure number formatting is plain (no notes inside cells). If a row is actually a header and auto-detect didn't skip it, toggle the 'Auto-detect header row' or edit your sheet to move header to topmost row.</div>", unsafe_allow_html=True)
