import pandas as pd
import matplotlib.pyplot as plt
import streamlit as st

# --------------------------
# PAGE CONFIG
# --------------------------
st.set_page_config(
    page_title="California Water Savings Tool",
    page_icon="💧",
    layout="centered"
)

# --------------------------
# CUSTOM STYLING (WATERY 🌊)
# --------------------------
st.markdown("""
    <style>
    .stApp {
        background: linear-gradient(to bottom, #e0f7fa, #ffffff);
    }
    h1 {
        color: #01579b;
    }
    h2, h3 {
        color: #0277bd;
    }
    .stButton>button {
        background-color: #4fc3f7;
        color: white;
    }
    </style>
""", unsafe_allow_html=True)

st.title("💧 California Lawn Conversion Water Savings Tool")

st.markdown("""
### What This Tool Does
This dashboard estimates how much **water and money you could save annually**
by replacing traditional lawn space with California native plant types.

It uses:
- WUCOLS Plant Factors
- CIMIS Evapotranspiration (ETo) Data
- LADWP Tier 2 Residential Water Rates

Enter your lawn size below and select a plant type to compare.
""")

# --------------------------
# LOAD DATA (NO LOCAL PATHS)
# --------------------------
wucols = pd.read_excel("WUCOLS_Los Angeles.xlsx")
cimis = pd.read_csv("daily_eto_variance.csv")

wucols.columns = wucols.columns.str.strip()
cimis.columns = cimis.columns.str.strip()

type_column = "Type(s)"
plant_factor_column = "Plant_Factor"

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
    "Tree","Shrub","Ground Cover","Ornamental Grass",
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
# BASELINE = LAWN (ORNAMENTAL GRASS PF)
# --------------------------
lawn_pf = pf_by_type["Ornamental Grass"]
lawn_inches = lawn_pf * annual_eto

# Remove lawn from dropdown options
plant_options = [p for p in etc_by_type.index if p != "Ornamental Grass"]

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
# WATER RATE (TIER 2)
# --------------------------
TIER_2_RATE_PER_HCF = 5.50  # LADWP Tier 2 Residential
water_cost_per_gallon = TIER_2_RATE_PER_HCF / 748

st.caption("Water cost calculations use LADWP Tier 2 Residential Rate: "
           "$5.50 per HCF")

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

        # --------------------------
        # COMPARISON GRAPH (FIXED)
        # --------------------------
        st.subheader("Water Use Comparison")

        fig, ax = plt.subplots()
        ax.bar(["Current Lawn", selected_type],
               [lawn_gallons, new_gallons])

        ax.set_ylabel("Gallons per Year")
        ax.spines['top'].set_visible(False)
        ax.spines['right'].set_visible(False)

        st.pyplot(fig)

    except ValueError:
        st.error("Please enter a valid number for square footage.")

# --------------------------
# FOOTER
# --------------------------
st.markdown("""
---
**Data Sources**
- WUCOLS IV (Water Use Classification of Landscape Species)
- California CIMIS ETo Data
- LADWP Residential Water Rate Schedule (Tier 2)
""")
