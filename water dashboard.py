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
# LOAD BACKGROUND IMAGE (Mocked or handled via local file)
# --------------------------
def get_base64(file):
    try:
        with open(file, "rb") as f:
            return base64.b64encode(f.read()).decode()
    except FileNotFoundError:
        return ""

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
h1, h2, h3, h4, p, label {{ color: #1b5e20 !important; }}
</style>
""", unsafe_allow_html=True)

# --------------------------
# LOAD DATA & CLEANING
# --------------------------
# Assuming files are present in the directory
try:
    wucols = pd.read_excel("WUCOLS_Los Angeles.xlsx")
    cimis = pd.read_csv("daily_eto_variance.csv")
except Exception as e:
    st.error(f"Data files missing: {e}")
    st.stop()

wucols.columns = wucols.columns.str.strip()
cimis.columns = cimis.columns.str.strip()

type_column = "Type(s)"
plant_factor_column = "Plant_Factor"
plant_name_column = "Botanical Name"

# Filter for Native/Ornamental but REMOVE high-variance density types
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

# REFINED TYPES: Removed Vines, Bamboo, and Bulbs for better density predictability
valid_types = [
    "Shrub", "Ground Cover", "Ornamental Grass",
    "Perennial", "Succulent", "Palm and Cycad"
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

# --------------------------
# TITLE & USER INPUT
# --------------------------
st.markdown("## 💧 Transform Your Lawn, Save Water!")
st.caption("Calculate savings based on plant species and planting density.")

col_left, col_right = st.columns(2)

with col_left:
    lawn_sqft = st.text_input("Total Area (sq ft):", key="lawn_area_input")
    selected_type = st.selectbox("Convert TO:", [p for p in pf_by_type.index if p != "Ornamental Grass"])

with col_right:
    # ADDING DENSITY CONTROL
    density_label = st.select_slider(
        "Planting Density:",
        options=["Sparse", "Average", "Lush"],
        value="Average",
        help="Sparse: Lots of mulch/space. Lush: Plants overlapping/full coverage."
    )
    
    # Map selection to a density factor (Kd)
    density_map = {"Sparse": 0.6, "Average": 1.0, "Lush": 1.3}
    kd = density_map[density_label]

# --------------------------
# WATER CALCULATIONS
# --------------------------
TIER_2_RATE_PER_HCF = 5.50
water_cost_per_gallon = TIER_2_RATE_PER_HCF / 748

if lawn_sqft:
    try:
        lawn_sqft = float(lawn_sqft)
        
        # LAWN baseline (Usually Kd=1.0 because grass is a carpet)
        lawn_ks = pf_by_type["Ornamental Grass"]
        lawn_gallons = (annual_eto * lawn_ks * 1.0) * lawn_sqft * 0.623

        # NEW LANDSCAPE
        new_ks = pf_by_type[selected_type]
        # Formula: ET_L = ETo * (Ks * Kd)
        new_gallons = (annual_eto * (new_ks * kd)) * lawn_sqft * 0.623

        gallons_saved = lawn_gallons - new_gallons
        cost_saved = gallons_saved * water_cost_per_gallon

        st.divider()
        st.header("📊 Results")

        m1, m2, m3 = st.columns(3)
        m1.metric("Lawn Use", f"{lawn_gallons:,.0f} gal")
        m2.metric(f"New {selected_type} Use", f"{new_gallons:,.0f} gal")
        m3.metric("Savings", f"{gallons_saved:,.0f} gal", delta_color="normal")

        st.success(f"💰 **Estimated Annual Cost Savings: ${cost_saved:,.2f}**")

        # Visuals
        fig, ax = plt.subplots(figsize=(8, 4))
        bars = ax.bar(["Current Lawn", f"New {selected_type}"], [lawn_gallons, new_gallons], color=['#d32f2f', '#2e7d32'])
        ax.set_ylabel("Gallons per Year")
        ax.set_title(f"Impact of {density_label} Density Planting")
        st.pyplot(fig)

    except ValueError:
        st.error("Please enter a numeric value for square footage.")

# --------------------------
# FOOTER
# --------------------------
st.markdown("""
<div style="font-size:0.8rem; color:gray; margin-top:2rem;">
<b>Technical Note:</b> Calculations use the Landscape Coefficient Method 
$K_L = K_s \\times K_d$, where $K_s$ is the species factor and $K_d$ is the density factor.
</div>
""", unsafe_allow_html=True)
