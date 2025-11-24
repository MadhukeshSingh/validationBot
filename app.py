import streamlit as st
import pandas as pd
import re
import io

# -------------------------------------------------------
#  PAGE CONFIG + THEME
# -------------------------------------------------------
st.set_page_config(
    page_title="Budget & Actual Validator",
    page_icon="📘",
    layout="wide"
)

# -------------------------------------------------------
#  CUSTOM CSS (Modern UI)
# -------------------------------------------------------
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Poppins:wght@300;400;600&display=swap');

html, body, [class*="css"]  {
    font-family: 'Poppins', sans-serif;
}

body {
    background: linear-gradient(135deg, #0a1530, #11385b);
    color: #e9f2ff;
}

.upload-section {
    background: rgba(255,255,255,0.08);
    padding: 18px;
    border-radius: 12px;
    margin-bottom: 20px;
}

.result-card {
    background: rgba(255,255,255,0.07);
    padding: 14px;
    border-radius: 10px;
    margin-top: 12px;
}

.good {
    color: #90ffb0;
    font-weight: 600;
}

.bad {
    color: #ff9090;
    font-weight: 600;
}

</style>
""", unsafe_allow_html=True)


# -------------------------------------------------------
#  NUMBER PARSER
# -------------------------------------------------------
def parse_number(cell):
    """Convert '(9.15)' to -9.15, '1,234.56' to 1234.56, etc."""
    if pd.isna(cell):
        return 0.0

    s = str(cell).strip()
    if s == "":
        return 0.0

    s = re.sub(r"[^0-9.\-(),]", "", s)

    # Handle (negative)
    if re.match(r"^\(.*\)$", s):
        inner = s[1:-1].replace(",", "")
        return -float(inner) if inner else 0.0

    s = s.replace(",", "")

    try:
        return float(s)
    except:
        return None


# -------------------------------------------------------
#  PAGE UI
# -------------------------------------------------------
st.markdown("<h1>📘 Budget & Actual Validator</h1>", unsafe_allow_html=True)
st.markdown("<p>Upload your .et/.xlsx file to validate Budget & Actual values.</p>", unsafe_allow_html=True)

st.markdown("<div class='upload-section'>", unsafe_allow_html=True)

file = st.file_uploader("Upload your file (.xlsx recommended)", type=['xlsx', 'xls', 'et'])

tolerance = st.number_input("Numeric tolerance", value=0.01, step=0.01)
show_only_mismatch = st.checkbox("Show only mismatches", value=True)

st.markdown("</div>", unsafe_allow_html=True)

# -------------------------------------------------------
#  PROCESS THE FILE
# -------------------------------------------------------
if file:

    st.info(f"Uploaded: **{file.name}**")

    try:
        df = pd.read_excel(file, sheet_name=0, header=None)
    except Exception as e:
        st.error(f"❌ Unable to read file: {e}")
        st.stop()

    if df.shape[1] < 7:
        st.error("❌ File must contain at least 7 columns (A..G).")
        st.stop()

    left_param_col = 0
    left_budget_col = 1
    left_actual_col = 2

    right_name_col = 4
    right_budget_col = 5
    right_actual_col = 6

    # -------------------------------------------------------
    #  BUILD RIGHT SIDE MAP
    # -------------------------------------------------------
    right_map = {}

    for idx, row in df.iterrows():
        name = row.iloc[right_name_col]
        if pd.isna(name):
            continue

        key = str(name).strip().lower()

        right_map[key] = {
            "row": idx,
            "name": str(name).strip(),
            "budget": parse_number(row.iloc[right_budget_col]),
            "actual": parse_number(row.iloc[right_actual_col]),
        }

    # -------------------------------------------------------
    #  VALIDATION LOOP
    # -------------------------------------------------------
    results = []
    mismatches = []

    for idx, row in df.iterrows():
        left_name = row.iloc[left_param_col]
        if pd.isna(left_name): 
            continue

        left_key = str(left_name).strip().lower()

        left_budget = parse_number(row.iloc[left_budget_col])
        left_actual = parse_number(row.iloc[left_actual_col])

        entry = {
            "left_row": idx,
            "left_name": str(left_name).strip(),
            "left_budget": left_budget,
            "left_actual": left_actual,
            "match_found": False,
            "notes": []
        }

        if left_key in right_map:
            rm = right_map[left_key]
            entry["match_found"] = True
            entry["right_row"] = rm["row"]
            entry["right_budget"] = rm["budget"]
            entry["right_actual"] = rm["actual"]

            # Budget check
            if left_budget is None or rm["budget"] is None:
                entry["notes"].append("Budget value cannot be parsed.")
            else:
                if abs(left_budget - rm["budget"]) > tolerance:
                    entry["notes"].append(
                        f"Budget mismatch: left={left_budget} | right={rm['budget']}"
                    )

            # Actual check
            if left_actual is None or rm["actual"] is None:
                entry["notes"].append("Actual value cannot be parsed.")
            else:
                if abs(left_actual - rm["actual"]) > tolerance:
                    entry["notes"].append(
                        f"Actual mismatch: left={left_actual} | right={rm['actual']}"
                    )
        else:
            entry["notes"].append("No matching DBDisplayName found.")

        if entry["notes"]:
            mismatches.append(entry)

        results.append(entry)


    # -------------------------------------------------------
    #  SUMMARY
    # -------------------------------------------------------
    st.markdown("### ✅ Validation Summary")
    st.write(f"**Total Parameters Checked:** {len(results)}")
    st.write(f"**Total Mismatches:** {len(mismatches)}")

    # -------------------------------------------------------
    #  DISPLAY RESULTS
    # -------------------------------------------------------
    st.markdown("### 🔍 Validation Details")

    to_display = mismatches if show_only_mismatch else results

    for m in to_display:
        st.markdown(f"<div class='result-card'>", unsafe_allow_html=True)
        st.write(f"**Parameter:** {m['left_name']}  (Row {m['left_row']})")

        if m["match_found"]:
            st.write(f"Right side row: {m['right_row']}")
        else:
            st.write("❌ No matching right-side entry")

        st.write("Notes:")
        for note in m["notes"]:
            st.markdown(f"<span class='bad'>• {note}</span>", unsafe_allow_html=True)

        st.markdown("</div>", unsafe_allow_html=True)
