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

/* FORCING DARK GREEN ON ALL TEXT ELEMENTS */
h1, h2, h3, h4, p, label, li, span, div {{
    color: #1b5e20 !important;
}}

/* Ensuring LaTeX and Markdown inside tabs specifically are dark green */
.stMarkdown p, .stMarkdown li, .stMarkdown span {{
    color: #1b5e20 !important;
}}

div[data-baseweb="select"] > div {{
    background-color: #1b5e20 !important;
    color: #FFFFFF !important;
    border-radius: 10px !important;
    font-weight: 600;
}}

/* Select box inner text needs to stay white for contrast */
div[data-baseweb="select"] span {{
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

/* Footer override back to black as requested in original */
.footer, .footer p, .footer b {{
    color: #000000 !important;
}}

/* Example section override back to black as requested in original */
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
botanical_name_column = "Botanical Name"
common_name_column = "Common Name"

# Filter plants (Excluding Vine, Bamboo, and Bulb for density accuracy)
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
    "Perennial","Succulent","Palm and Cycad"
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

lawn_sqft = st.text_input(
    "Enter total lawn area (square feet):",
    key="lawn_area_input"
)

selected_type = st.selectbox(
    "Select plant type to convert TO:",
    plant_options,
    key="plant_type_select"
)

# DENSITY DROPDOWN
density_choice = st.selectbox(
    "Select Planting Density:",
    options=[
        "Sparse (Minimalist, lots of space/mulch visible)",
        "Medium (Standard garden spacing)",
        "Lush (Dense, overlapping plants/full coverage)"
    ],
    index=1,
    help="Higher density means more leaf surface area and slightly higher water use."
)

# Density mapping logic
density_map = {
    "Sparse (Minimalist, lots of space/mulch visible)": 0.6,
    "Medium (Standard garden spacing)": 1.0,
    "Lush (Dense, overlapping plants/full coverage)": 1.3
}
kd = density_map[density_choice]

st.caption("Calculations use LADWP Tier 2 Residential Rate = $5.50 per HCF")

# --------------------------
# WATER RATE
# --------------------------
TIER_2_RATE_PER_HCF = 5.50
water_cost_per_gallon = TIER_2_RATE_PER_HCF / 748

# --------------------------
# CALCULATIONS & TABS
# --------------------------
if lawn_sqft:
    try:
        lawn_sqft = float(lawn_sqft)

        # Baseline Lawn Use (Kd = 1.0)
        lawn_gallons = lawn_inches * lawn_sqft * 0.623
        
        # New Landscape Use (Using Species Factor * Density Factor)
        new_ks = pf_by_type[selected_type]
        new_inches = (annual_eto * new_ks * kd)
        new_gallons = new_inches * lawn_sqft * 0.623

        gallons_saved = lawn_gallons - new_gallons
        cost_saved = gallons_saved * water_cost_per_gallon

        # CREATE TABS
        tab1, tab2 = st.tabs(["📊 Results Dashboard", "🧪 Methodology Breakdown"])

        with tab1:
            st.header("Results")
            col1, col2 = st.columns(2)
            col1.metric("Annual Lawn Use", f"{lawn_gallons:,.0f} gal")
            col2.metric(f"{selected_type} Use", f"{new_gallons:,.0f} gal")

            st.success(f"💧 Annual Water Savings: {gallons_saved:,.0f} gallons")
            st.success(f"💰 Estimated Annual Cost Savings: ${cost_saved:,.2f}")

            st.subheader("Water Use Comparison")
            fig, ax = plt.subplots()
            ax.bar(
                ["Current Lawn", f"{selected_type}"],
                [lawn_gallons, new_gallons],
                color=['#4CAF50', '#8BC34A']
            )
            ax.set_ylabel("Gallons per Year")
            ax.spines['top'].set_visible(False)
            ax.spines['right'].set_visible(False)
            ax.yaxis.grid(True, linestyle='--', linewidth=0.8, alpha=0.5)
            ax.set_axisbelow(True)
            st.pyplot(fig)

        with tab2:
            st.header("Calculation Methodology")
            st.write("We use the standard Landscape Coefficient Method ($K_L$) to determine irrigation needs.")
            
            st.subheader("1. Landscape Evapotranspiration ($ET_L$)")
            st.write("First, we determine the water depth (inches) required by the landscape:")
            st.latex(r"ET_L = ET_o \times (K_s \times K_d)")
            st.markdown(f"""
            * **$ET_o$ (Reference Evapotranspiration):** {annual_eto:.2f}" (Total annual local evapotranspiration from CIMIS).
            * **$K_s$ (Species Factor):** {new_ks:.2f} (The water need for {selected_type}).
            * **$K_d$ (Density Factor):** {kd:.2f} (Based on your density selection).
            """)

            st.subheader("2. Total Volume (Gallons)")
            st.write("We convert depth and area into total gallons:")
            st.latex(r"Gallons = ET_L \times Area \times 0.623")
            st.write("* **0.623:** The constant used to convert 1 inch of water over 1 square foot into gallons.")

            st.subheader("3. Financial Savings")
            st.latex(r"Savings = (Gallons_{Lawn} - Gallons_{New}) \times \text{Cost per Gallon}")
            st.write(f"* **Cost per Gallon:** ${water_cost_per_gallon:.5f} (Based on $5.50 per HCF).")

    except ValueError:
        st.error("Please enter a valid number for square footage.")

# --------------------------
# EXAMPLES SECTION
# --------------------------
if selected_type:
    # Improved accessibility: Fetching both Common and Botanical names
    example_data = (
        wucols[wucols["Primary_Type"] == selected_type][[common_name_column, botanical_name_column]]
        .dropna()
        .drop_duplicates()
    )

    example_list = example_data.head(5)

    if not example_list.empty:
        st.markdown('<div class="examples">', unsafe_allow_html=True)
        st.markdown(f"#### Recommended Plants of this Type")
        
        # Formatting as "Common Name (Scientific Name)"
        formatted_names = [f"{row[common_name_column]} (*{row[botanical_name_column]}*)" for _, row in example_list.iterrows()]
        st.markdown(", ".join(formatted_names))
        st.markdown('</div>', unsafe_allow_html=True)

# --------------------------
# MAKE THE CHANGE LINK
# --------------------------
st.markdown('<div style="text-align:center; margin-top:1rem; font-size:1.1rem; color:#000000;">'
            'Make the Change → '
            '<a href="https://www.nourish.la/good-karma-gardens?gad_source=1&gad_campaignid=23078365112&gbraid=0AAAAAp3lr9qaWt7GIuHmQdK7B69WzZG4V&gclid=Cj0KCQiA49XMBhDRARIsAOOKJHbLQ5znII6Lm6YRfUjNvc-zlInEhDjnUNT0YV1nSAOIWWWYsXbss5kaAjwWEALw_wcB" '
            'target="_blank" style="color:#000000; text-decoration: underline;">Good Karma Gardens Website</a></div>', unsafe_allow_html=True)

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
