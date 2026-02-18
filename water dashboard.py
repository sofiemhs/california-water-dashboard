import pandas as pd
import matplotlib.pyplot as plt
import streamlit as st

st.title("California Native Plant Water Use Dashboard")

# --------------------------
# LOAD DATA
# --------------------------
wucols = pd.read_excel("C:/Users/sofie/OneDrive/Desktop/WUCOLS_Los Angeles.xlsx")
cimis = pd.read_csv("C:/Users/sofie/OneDrive/Desktop/daily_eto_variance.csv")

wucols.columns = wucols.columns.str.strip()
cimis.columns = cimis.columns.str.strip()

type_column = "Type(s)"
plant_factor_column = "Plant_Factor"

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

wucols[type_column] = (
    wucols[type_column]
    .str.replace("California Native", "", regex=False)
    .str.replace("Arboretum All-Star", "", regex=False)
    .str.strip()
)

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
# DISPLAY BAR GRAPH
# --------------------------
st.subheader("Average Annual Water Use by Plant Type")

fig, ax = plt.subplots(figsize=(12,6))
etc_by_type.plot(kind="bar", ax=ax)

ax.set_ylabel("Annual Water Use (inches/year)")
ax.set_xlabel("Plant Type")
ax.set_xticklabels(etc_by_type.index, rotation=45, ha='right')
ax.spines['top'].set_visible(False)
ax.spines['right'].set_visible(False)

st.pyplot(fig)

# --------------------------
# USER INPUT
# --------------------------
st.subheader("Estimate Your Water & Cost Savings")

lawn_sqft = st.number_input("Enter lawn size (sq ft):", min_value=0.0, step=100.0)

selected_type = st.selectbox(
    "Select plant type to convert to:",
    etc_by_type.index.tolist()
)

# --------------------------
# WATER COST SOURCE
# Replace with official LADWP rate
# Example: $5.50 per HCF
# 1 HCF = 748 gallons
# --------------------------
water_cost_per_gallon = 5.50 / 748  # UPDATE using official rate source

if lawn_sqft > 0:

    lawn_pf = pf_by_type["Ornamental Grass"]

    lawn_inches = lawn_pf * annual_eto
    new_inches = etc_by_type[selected_type]

    lawn_gallons = lawn_inches * lawn_sqft * 0.623
    new_gallons = new_inches * lawn_sqft * 0.623

    gallons_saved = lawn_gallons - new_gallons
    cost_saved = gallons_saved * water_cost_per_gallon

    st.markdown("### Results")
    st.write(f"Annual Lawn Water Use: {lawn_gallons:,.0f} gallons")
    st.write(f"Annual {selected_type} Water Use: {new_gallons:,.0f} gallons")
    st.write(f"Annual Water Savings: {gallons_saved:,.0f} gallons")
    st.write(f"Estimated Annual Cost Savings: ${cost_saved:,.2f}")

    # --------------------------
    # SIDE-BY-SIDE COMPARISON
    # --------------------------
    st.subheader("Water Use Comparison")

    comparison_data = pd.Series(
        [lawn_gallons, new_gallons],
        index=["Current Lawn", selected_type]
    )

    fig2, ax2 = plt.subplots()
    comparison_data.plot(kind="bar", ax=ax2)

    ax2.set_ylabel("Gallons per Year")
    ax2.spines['top'].set_visible(False)
    ax2.spines['right'].set_visible(False)

    st.pyplot(fig2)
