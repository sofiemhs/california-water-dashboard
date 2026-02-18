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
# FLOATING CARD LAYOUT + CUSTOM STYLING
# --------------------------
import base64

def get_base64(file):
    with open(file, "rb") as f:
        return base64.b64encode(f.read()).decode()

img_base64 = get_base64("background.jpg")

st.markdown(f"""
<style>

/* Full page background image */
.stApp {{
    background-image: url("data:image/jpg;base64,{img_base64}");
    background-size: cover;
    background-position: center;
    background-attachment: fixed;
}}

/* FLOATING centered container */
.block-container {{
    background-color: rgba(250, 248, 242, 0.97);
    padding: 3rem 3rem 3rem 3rem;
    border-radius: 22px;
    box-shadow: 0 20px 60px rgba(0,0,0,0.18);
    max-width: 900px;
    margin-top: 5rem;
    margin-bottom: 5rem;
}}

/* Dark green text everywhere */
h1, h2, h3, h4, p, label, div, span {{
    color: #1b5e20 !important;
}}

/* Dropdown styling */
div[data-baseweb="select"] > div {{
    background-color: #1b5e20 !important;
    color: #f6f3ea !important;
    border-radius: 10px !important;
}}

/* Dropdown menu options */
ul {{
    background-color: #1b5e20 !important;
}}

li {{
    color: #f6f3ea !important;
}}

/* Text input styling */
input {{
    background-color: #f6f3ea !important;
    color: #1b5e20 !important;
    border-radius: 8px !important;
}}

</style>
""", unsafe_allow_html=True)

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

st.markdown("</div>", unsafe_allow_html=True)





