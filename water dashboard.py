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

/* FORCING DARK GREEN ON ALL GENERAL TEXT */
h1, h2, h3, h4, p, label, li, span, div {{
    color: #1b5e20 !important;
}}

.stMarkdown p, .stMarkdown li, .stMarkdown span {{
    color: #1b5e20 !important;
}}

/* DROPDOWN STYLING - FORCING WHITE TEXT */
div[data-baseweb="select"] > div {{
    background-color: #1b5e20 !important;
    border-radius: 10px !important;
    font-weight: 600;
}}

/* This ensures the selected text and the text in the list is WHITE */
div[data-baseweb="select"] * {{
    color: #FFFFFF !important;
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

.footer, .footer p, .footer b {{
    color: #000000 !important;
}}

.examples, .examples p, .examples li, .examples h4 {{
    color: #000000 !important;
}}

</style>
""", unsafe_allow_html=True)

# --------------------------
# LOAD DATA & ERROR HANDLING
# --------------------------
try:
    wucols = pd.read_excel("WUCOLS_Los Angeles.xlsx")
    cimis = pd.read_csv("daily_eto_variance.csv")
except Exception as e:
    st.error(f"Error loading data files: {e}")
    st.stop()

wucols.columns = wucols.columns.str.strip()
cimis.columns = cimis.columns.str.strip()

def find_col(possible_names):
    for name in possible_names:
        if name in wucols.columns: return name
    for col in wucols.columns:
        if possible_names[0].replace(" ", "").lower() in col.replace("_", "").lower():
            return col
    return possible_names[0]

type_column = find_col(["Type(s)", "Types"])
pf_column = find_col(["Plant_Factor", "Plant Factor", "PF"])
bot_name_col = find_col(["Botanical Name", "Botanical_Name"])
com_name_col = find_col(["Common Name", "Common_Name"])

wucols = wucols[
    wucols[type_column].str.contains("California Native", na=False)
    | wucols[type_column].str.contains("Ornamental Grass", na=False)
].copy()

pf_range_map = {
    "< 0.10": 0.05, "0.10-0.30": 0.20, "0.40-0.60": 0.50, "0.70-0.90": 0.80
}

wucols[pf_column] = wucols[pf_column].astype(str).str.strip().map(pf_range_map)
wucols = wucols.dropna(subset=[pf_column])

valid_types = ["Shrub","Ground Cover","Ornamental Grass","Perennial","Succulent","Palm and Cycad"]

def extract_primary_type(type_string):
    parts = [p.strip() for p in str(type_string).split(",")]
    for p in parts:
        if p in valid_types: return p
    return None

wucols["Primary_Type"] = wucols[type_column].apply(extract_primary_type)
wucols = wucols.dropna(subset=["Primary_Type"])

pf_by_type = wucols.groupby("Primary_Type")[pf_column].mean()
cimis["Avg ETo (in)"] = pd.to_numeric(cimis["Avg ETo (in)"], errors="coerce")
cimis = cimis.dropna(subset=["Avg ETo (in)"])
annual_eto = cimis["Avg ETo (in)"].sum()

# --------------------------
# USER INPUT
# --------------------------
st.markdown("## 💧 Transform Your Lawn, Save Water!")
st.header("🌿 Enter Your Lawn Information")

lawn_sqft = st.text_input("Enter total lawn area (square feet):", key="lawn_area_input")

selected_type = st.selectbox(
    "1. Pick a general group of plants:",
    [p for p in pf_by_type.index if p != "Ornamental Grass"],
    key="type_select"
)

type_filtered_plants = wucols[wucols["Primary_Type"] == selected_type].copy()
plant_list = sorted([str(name).title() for name in type_filtered_plants[com_name_col].dropna().unique().tolist()])

# Step 2: Simplified casing for "California native"
specific_plant = st.selectbox(
    f"2. Search for a specific California native {selected_type} (optional):",
    options=["Average for this type"] + plant_list,
    help="Every plant in this list is native to California! Type to search."
)

density_choice = st.selectbox(
    "3. How crowded will your plants be?",
    options=["Sparse (Lots of space/mulch visible)", "Medium (Standard spacing)", "Lush (Dense/Full coverage)"],
    index=1
)

density_map = {"Sparse (Lots of space/mulch visible)": 0.6, "Medium (Standard spacing)": 1.0, "Lush (Dense/Full coverage)": 1.3}
kd = density_map[density_choice]

st.caption("Calculations use LADWP Tier 2 Residential Rate = $5.50 per HCF")

# --------------------------
# CALCULATIONS
# --------------------------
TIER_2_RATE_PER_HCF = 5.50
water_cost_per_gallon = TIER_2_RATE_PER_HCF / 748

if lawn_sqft:
    try:
        lawn_sqft = float(lawn_sqft)
        lawn_ks = pf_by_type["Ornamental Grass"]
        lawn_gallons = (annual_eto * lawn_ks * 1.0) * lawn_sqft * 0.623
        
        if specific_plant == "Average for this type":
            current_ks = pf_by_type[selected_type]
        else:
            current_ks = type_filtered_plants[type_filtered_plants[com_name_col].str.title() == specific_plant][pf_column].values[0]

        new_inches = (annual_eto * current_ks * kd)
        new_gallons = new_inches * lawn_sqft * 0.623
        gallons_saved = lawn_gallons - new_gallons
        cost_saved = gallons_saved * water_cost_per_gallon

        tab1, tab2 = st.tabs(["📊 Results Dashboard", "🧪 Technical Methodology"])

        with tab1:
            st.header("Results")
            c1, c2 = st.columns(2)
            c1.metric("Annual Lawn Use", f"{lawn_gallons:,.0f} gal")
            c2.metric("New Landscape Use", f"{new_gallons:,.0f} gal")
            st.success(f"💧 Annual Water Savings: {gallons_saved:,.0f} gallons")
            st.success(f"💰 Estimated Annual Cost Savings: ${cost_saved:,.2f}")

            fig, ax = plt.subplots()
            ax.bar(["Current Lawn", "New Landscape"], [lawn_gallons, new_gallons], color='#1b5e20')
            ax.set_ylabel("Gallons per Year")
            ax.yaxis.grid(True, linestyle='--', alpha=0.5)
            st.pyplot(fig)

            st.markdown(f"""
            > **/n Ready to make the switch?** > We recommend Calscape.org to find **{specific_plant}s** near you. \n
            **Caution:** Plant names can be confusing!! Often times, multiple names can refer to the same plant, so when you seach and nothing seems to show up... don't despare! 
            A quick google seach should help you clear the air and see other variations of the plant's name to help you find the native plants that you seek!
            """)
        
        with tab2:
            st.header("Scientific Analysis & Methodology")
            st.write("""
                The irrigation demand for this project is calculated via the **Landscape Coefficient Method**, 
                the industry-standard protocol for determining Supplemental Irrigation Requirements. 
            """)
            
            st.subheader("Step 1: Environmental Demand ($ET_o$) - Santa Monica Station")
            st.write(f"""
                Reference Evapotranspiration ($ET_o$) is derived from the **California Irrigation Management Information System (CIMIS)**. 
                This model utilizes data from **Station #99 (Santa Monica)**, which monitors solar radiation, wind speed, vapor pressure, and air temperature. 
                Using the Santa Monica station ensures the calculations reflect the specific coastal-influenced microclimate of Los Angeles, where the cumulative annual $ET_o$ is **{annual_eto:.2f} inches**.
            """)
            
            st.subheader("Step 2: The WUCOLS Species Factor ($K_s$)")
            st.write(f"""
                The Species Factor is sourced from the **WUCOLS IV (Water Use Classification of Landscape Species)** database, 
                maintained by the University of California, Davis. This peer-reviewed database assigns water-need categories 
                to plants based on horticultural research. 
                * **Lawn Baseline:** Classified as a 'High' water-use species with a coefficient of **{lawn_ks:.2f}**.
                * **Current Selection:** Your choice ({specific_plant if specific_plant != 'Average for this type' else selected_type}) has a refined coefficient of **{current_ks:.2f}**.
            """)
            
            st.subheader("Step 3: Density Factor Adjustment ($K_d$)")
            st.write(f"""
                Based on guidelines from the **California Department of Water Resources (DWR)**, the Density Factor accounts for 
                vegetative canopy cover and competition. Your selection of **{density_choice.split(' ')[0]}** applies a coefficient of **{kd:.2f}**, 
                reflecting the total leaf surface area relative to the ground area.
            """)

            st.subheader("The Fundamental Equation")
            st.latex(r"ET_L = ET_o \times (K_s \times K_d)")
            st.latex(r"Total Gallons = ET_L \times Area_{(sqft)} \times 0.623")

            st.markdown("---")
            st.write("**Data Integrity Note:** All calculations assume a system efficiency of 100% to isolate the biological water demand difference between species.")

    except ValueError:
        st.error("Please enter a valid number for square footage.")

# --------------------------
# FOOTER
# --------------------------
st.markdown("""
<div class="footer">
<hr>
<b>Data Sources</b><br>
- WUCOLS IV (Water Use Classification of Landscape Species)<br>
- California CIMIS ETo Data (Station #99 - Santa Monica)<br>
- LADWP Residential Water Rate Schedule (Tier 2)<br>
- Native Plant Research via <a href="https://calscape.org" target="_blank" style="color:#000000; text-decoration:underline;">Calscape.org</a>
</div>
""", unsafe_allow_html=True)











