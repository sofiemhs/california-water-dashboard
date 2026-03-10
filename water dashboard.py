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

# Filtering plants by type and removing duplicates for the dropdown
type_filtered_plants = wucols[wucols["Primary_Type"] == selected_type].copy()
plant_list = sorted(type_filtered_plants[com_name_col].dropna().unique().tolist())

specific_plant = st.selectbox(
    f"2. Search for a specific {selected_type} (optional):",
    options=["Average for this type"] + plant_list,
    help="Type to search for a specific plant name!"
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
            current_ks = type_filtered_plants[type_filtered_plants[com_name_col] == specific_plant][pf_column].values[0]

        new_inches = (annual_eto * current_ks * kd)
        new_gallons = new_inches * lawn_sqft * 0.623
        gallons_saved = lawn_gallons - new_gallons
        cost_saved = gallons_saved * water_cost_per_gallon

        tab1, tab2 = st.tabs(["📊 Results Dashboard", "🧪 Methodology (How the Math Works)"])

        with tab1:
            st.header("Results")
            c1, c2 = st.columns(2)
            c1.metric("Annual Lawn Use", f"{lawn_gallons:,.0f} gal")
            c2.metric("New Landscape Use", f"{new_gallons:,.0f} gal")
            st.success(f"💧 Annual Water Savings: {gallons_saved:,.0f} gallons")
            st.success(f"💰 Estimated Annual Cost Savings: ${cost_saved:,.2f}")

            # BARS ARE NOW THE SAME COLOR
            fig, ax = plt.subplots()
            ax.bar(["Current Lawn", "New Landscape"], [lawn_gallons, new_gallons], color='#1b5e20')
            ax.set_ylabel("Gallons per Year")
            ax.yaxis.grid(True, linestyle='--', alpha=0.5)
            st.pyplot(fig)

        with tab2:
            st.header("How do we figure this out?")
            st.write("Imagine your yard is a giant thirsty sponge. We use three main 'secrets' to calculate how much water it drinks.")
            
            st.subheader("Secret #1: The Sun Factor ($ET_o$)")
            st.write(f"The sun and wind 'steal' water from the ground. In your area, the sun steals about **{annual_eto:.2f} inches** of water every year! We call this the Reference Evapotranspiration.")
            
            st.subheader("Secret #2: The Thirsty Factor ($K_s$)")
            st.write(f"Not all plants drink the same! Grass is very thirsty, but a {selected_type} is much better at saving water.")
            st.write(f"* Grass has a Thirsty Factor of **{lawn_ks:.2f}**.")
            st.write(f"* Your choice ({specific_plant if specific_plant != 'Average for this type' else selected_type}) has a Thirsty Factor of **{current_ks:.2f}**.")
            
            st.subheader("Secret #3: The Crowd Factor ($K_d$)")
            st.write(f"If you pack your plants together like a jungle, they use more water. If you leave space for mulch, they use less. You chose **{density_choice.split(' ')[0]}**, which has a multiplier of **{kd:.2f}**.")

            st.markdown("---")
            st.subheader("The Grand Total Formula")
            st.write("We multiply the Sun Factor × Thirsty Factor × Crowd Factor to see how many inches of water you need. Then we multiply by your yard size and a 'magic number' (0.623) to turn those inches into gallons!")
            st.latex(r"\text{Gallons} = \text{Sun} \times \text{Thirsty} \times \text{Crowd} \times \text{Area} \times 0.623")

    except ValueError:
        st.error("Please enter a valid number for square footage.")

# --------------------------
# FOOTER
# --------------------------
st.markdown('<div style="text-align:center; margin-top:1rem; font-size:1.1rem; color:#000000;">'
            'Make the Change → <a href="https://www.nourish.la/good-karma-gardens" target="_blank" style="color:#000000;">Good Karma Gardens Website</a></div>', unsafe_allow_html=True)

st.markdown("""
<div class="footer">
<hr>
<b>Data Sources</b><br>
- WUCOLS IV (Water Use Classification of Landscape Species)<br>
- California CIMIS ETo Data<br>
- LADWP Residential Water Rate Schedule (Tier 2)
</div>
""", unsafe_allow_html=True)
