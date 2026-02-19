import pandas as pd
import matplotlib.pyplot as plt
import streamlit as st
import base64

# --------------------------
# PAGE CONFIG
# --------------------------
st.set_page_config(
    page_title="Transform Your Lawn 💧",
    page_icon="💧",
    layout="centered"
)

# --------------------------
# LOAD BACKGROUND IMAGE
# --------------------------
def get_base64(file):
    with open(file, "rb") as f:
        return base64.b64encode(f.read()).decode()

img_base64 = get_base64("wildlifeheader.jpg")

# --------------------------
# GLOBAL STYLING
# --------------------------
st.markdown(f"""
<style>

.stApp {{
    background-image: url("data:image/jpg;base64,{img_base64}");
    background-size: cover;
    background-position: center;
    background-attachment: fixed;
}}

.block-container {{
    background-color: rgba(250, 248, 242, 0.97);
    padding: 3rem;
    border-radius: 22px;
    box-shadow: 0 20px 60px rgba(0,0,0,0.18);
    max-width: 900px;
    margin-top: 5rem;
    margin-bottom: 5rem;
}}

h1, h2, h3, h4, p, label {{
    color: #1b5e20 !important;
}}

div[data-baseweb="select"] > div {{
    background-color: #1b5e20 !important;
    color: #FFFFFF !important;
    border-radius: 10px !important;
    font-weight: 600;
}}

ul[role="listbox"] {{
    background-color: #1b5e20 !important;
}}

ul[role="listbox"] li {{
    color: #FFFFFF !important;
    background-color: #1b5e20 !important;
}}

ul[role="listbox"] li:hover {{
    background-color: #2e7d32 !important;
}}

input {{
    background-color: #f6f3ea !important;
    color: #1b5e20 !important;
    border-radius: 8px !important;
}}

/* Footer text */
.footer, .footer p, .footer b {{
    color: #000000 !important;
}}

/* Example section text */
.examples, .examples p, .examples li, .examples h4 {{
    color: #000000 !important;
}}

</style>
""", unsafe_allow_html=True)

# --------------------------
# LOAD DATA
# --------------------------
wucols = pd.read_excel("WUCOLS_Los Angeles.xlsx")
cimis = pd.read_csv("daily_eto_variance.csv")

wucols.columns = wucols.columns.str.strip()
cimis.columns = cimis.columns.str.strip()

type_column = "Type(s)"
plant_factor_column = "Plant_Factor"
plant_name_column = "Botanical Name"

# Filter plants
wucols = wucols[
    wucols[type_column].str.contains("California Native", na=False)
    | wucols[type_column].str.contains("Ornamental Grass", na=False)
]

pf_range_map = {
    "< 0.10": 0.05,
    "0.10-0.30": 0.20,
    "0.40-0.60": 0.50,
    "0.70-0.90": 0.80
}

wucols[plant_factor_column] = (
    wucols[plant_factor_column]
    .astype(str)
    .str.strip()
    .map(pf_range_map)
)

wucols = wucols.dropna(subset=[plant_factor_column])

valid_types = [
    "Shrub","Ground Cover","Ornamental Grass",
    "Vine","Perennial","Succulent","Palm and Cycad",
    "Bamboo","Bulb"
]

def extract_primary_type(type_string):
    parts = [p.strip() for p in str(type_string).split(",")]
    for p in parts:
        if p in valid_types:
            return p
    return None

wucols["Primary_Type"] = wucols[type_column].apply(extract_primary_type)
wucols = wucols.dropna(subset=["Primary_Type"])

pf_by_type = wucols.groupby("Primary_Type")[plant_factor_column].mean()

cimis["Avg ETo (in)"] = pd.to_numeric(cimis["Avg ETo (in)"], errors="coerce")
cimis = cimis.dropna(subset=["Avg ETo (in)"])

annual_eto = cimis["Avg ETo (in)"].sum()
etc_by_type = (pf_by_type * annual_eto).sort_values(ascending=False)

# --------------------------
# BASELINE
# --------------------------
lawn_pf = pf_by_type["Ornamental Grass"]
lawn_inches = lawn_pf * annual_eto
plant_options = [p for p in etc_by_type.index if p != "Ornamental Grass"]

# --------------------------
# TITLE
# --------------------------
st.markdown("## 💧 Transform Your Lawn, Save Water!")
st.caption("Enter lawn size and choose a native plant type to compare water savings.")

# --------------------------
# USER INPUT
# --------------------------
st.header("🌿 Enter Your Lawn Information")

lawn_sqft = st.text_input("Enter total lawn area (square feet):")

selected_type = st.selectbox(
    "Select plant type to convert TO:",
    plant_options
)

# --------------------------
# WATER RATE
# --------------------------
TIER_2_RATE_PER_HCF = 5.50
water_cost_per_gallon = TIER_2_RATE_PER_HCF / 748

# --------------------------
# CALCULATIONS
# --------------------------
if lawn_sqft:
    try:
        lawn_sqft = float(lawn_sqft)

        new_inches = etc_by_type[selected_type]

        lawn_gallons = lawn_inches * lawn_sqft * 0.623
        new_gallons = new_inches * lawn_sqft * 0.623

        gallons_saved = lawn_gallons - new_gallons
        cost_saved = gallons_saved * water_cost_per_gallon

        st.header("📊 Results")

        col1, col2 = st.columns(2)
        col1.metric("Annual Lawn Use", f"{lawn_gallons:,.0f} gal")
        col2.metric(f"{selected_type} Use", f"{new_gallons:,.0f} gal")

        st.success(f"💧 Annual Water Savings: {gallons_saved:,.0f} gallons")
        st.success(f"💰 Estimated Annual Cost Savings: ${cost_saved:,.2f}")

        st.subheader("Water Use Comparison")

        fig, ax = plt.subplots()

        ax.bar(
            ["Current Lawn", selected_type],
            [lawn_gallons, new_gallons]
        )

        ax.set_ylabel("Gallons per Year")
        ax.spines['top'].set_visible(False)
        ax.spines['right'].set_visible(False)
        ax.yaxis.grid(True, linestyle='--', linewidth=0.8, alpha=0.5)
        ax.set_axisbelow(True)

        st.pyplot(fig)

    except ValueError:
        st.error("Please enter a valid number for square footage.")

# --------------------------
# EXAMPLES SECTION (BOTTOM, SMALLER TITLE, BLACK TEXT, COMMA SEPARATED)
# --------------------------
if selected_type:
    example_plants = (
        wucols[wucols["Primary_Type"] == selected_type][plant_name_column]
        .dropna()
        .unique()
    )

    example_list = example_plants[:5]

    if len(example_list) > 0:
        st.markdown('<div class="examples">', unsafe_allow_html=True)
        st.markdown(f"#### 🌼 Example Plants in This Category")
        st.markdown(", ".join(example_list))
        st.markdown('</div>', unsafe_allow_html=True)

# --------------------------
# FOOTER
# --------------------------
st.markdown("""
<div class="footer">
<hr>
<b>Data Sources</b><br>
- WUCOLS IV (Water Use Classification of Landscape Species)<br>
- California CIMIS ETo Data<br>
- LADWP Residential Water Rate Schedule (Tier 2)
</div>
""", unsafe_allow_html=True)

