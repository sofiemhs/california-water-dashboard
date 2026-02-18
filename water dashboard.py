import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt

# -----------------------------
# CONSTANTS
# -----------------------------
ETO_2025 = 53.2  # inches/year (FY2025 DWR average ETo)
INCHES_TO_GALLONS_PER_SQFT = 0.623  # 1 inch of water over 1 sq ft = 0.623 gallons

# -----------------------------
# PLANT DATA (WUCOLS-BASED)
# -----------------------------
data = {
    "Plant": [
        "Lawn (Fescue)",
        "Lawn (Bermuda Grass)",
        "Roses",
        "Tomato",
        "Bougainvillea",
        "Lantana",
        "Lavender",
        "Rosemary",
        "Sage",
        "California Buckwheat",
        "Manzanita",
        "Olive Tree"
    ],
    "Kc": [
        0.8, 0.9, 0.6, 0.6,
        0.4, 0.4, 0.2, 0.2,
        0.2, 0.2, 0.2, 0.3
    ]
}

df = pd.DataFrame(data)
df["Annual Water Use (inches)"] = df["Kc"] * ETO_2025

# -----------------------------
# STREAMLIT UI
# -----------------------------
st.set_page_config(page_title="Lawn Conversion Water Savings", layout="centered")

st.title("💧 Lawn Conversion Water Savings Calculator")
st.write(
    "Estimate how much water you can save by converting traditional lawn "
    "to native or drought-tolerant plants in Los Angeles."
)

# -----------------------------
# USER INPUTS
# -----------------------------
area_sqft = st.number_input(
    "Enter lawn area (square feet):",
    min_value=0.0,
    step=50.0
)

current_lawn = st.selectbox(
    "Current lawn type:",
    ["Lawn (Fescue)", "Lawn (Bermuda Grass)"]
)

new_plant = st.selectbox(
    "Convert lawn to:",
    df[~df["Plant"].str.contains("Lawn")]["Plant"]
)

# -----------------------------
# CALCULATIONS
# -----------------------------
if area_sqft > 0:
    lawn_kc = df.loc[df["Plant"] == current_lawn, "Kc"].values[0]
    plant_kc = df.loc[df["Plant"] == new_plant, "Kc"].values[0]

    lawn_inches = lawn_kc * ETO_2025
    plant_inches = plant_kc * ETO_2025

    lawn_gallons = lawn_inches * area_sqft * INCHES_TO_GALLONS_PER_SQFT
    plant_gallons = plant_inches * area_sqft * INCHES_TO_GALLONS_PER_SQFT
    savings = lawn_gallons - plant_gallons

    # -----------------------------
    # OUTPUT
    # -----------------------------
    st.subheader("💦 Annual Water Use Results")

    col1, col2, col3 = st.columns(3)

    col1.metric(
        "Current Lawn (gallons/year)",
        f"{lawn_gallons:,.0f}"
    )

    col2.metric(
        "New Planting (gallons/year)",
        f"{plant_gallons:,.0f}"
    )

    col3.metric(
        "Water Saved (gallons/year)",
        f"{savings:,.0f}"
    )

    # -----------------------------
    # BAR CHART
    # -----------------------------
    chart_df = pd.DataFrame({
        "Scenario": ["Current Lawn", "New Planting"],
        "Gallons per Year": [lawn_gallons, plant_gallons]
    })

    fig, ax = plt.subplots()
    ax.barh(chart_df["Scenario"], chart_df["Gallons per Year"])
    ax.set_xlabel("Gallons per Year")
    ax.set_title("Annual Outdoor Water Use Comparison")

    st.pyplot(fig)
