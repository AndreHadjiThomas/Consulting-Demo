import streamlit as st
import pandas as pd
import numpy as np
import geopandas as gpd
import folium
import plotly.express as px
from pathlib import Path
from streamlit_folium import st_folium

# --- PAGE CONFIG ---
st.set_page_config(
    page_title='Reforestation & Biodiversity Monitoring',
    layout='wide',
    initial_sidebar_state='collapsed'
)
st.markdown("""
    <style>
        #MainMenu, footer, header {visibility: hidden;}
        .block-container {padding: 0.5rem 1rem;}
        .stButton>button {font-size:0.75rem; padding:0.2rem 0.4rem;}
        .css-1v3fvcr {font-size:1rem;}
    </style>
""", unsafe_allow_html=True)

# --- HEADER CONTROLS ---
col1, col2, col3, col4 = st.columns([4,1,1,1], gap='small')
col1.markdown("### 🔍 Reforestation & Biodiversity Platform")
if col2.button("Add Region"): st.info("Feature coming soon")
if col3.button("Settings"):   st.info("Feature coming soon")
if col4.button("Help"):       st.info("Feature coming soon")
st.divider()

# --- REGION SELECTION ---
BASE_DIR = Path(__file__).resolve().parent.parent
regions = {
    'Brazilian Amazon': {
        'data_folder': BASE_DIR / 'Biodiversity_brazil',
        'geo_prefix': 'BrazilAmazon',
        'center': [-3.5, -62.0],
        'zoom': 5
    }
}
selected = st.selectbox("Select Region", list(regions.keys()), key="region_select")
cfg = regions[selected]

years = list(range(2018, 2024))
files = {y: cfg['data_folder'] / f"{cfg['geo_prefix']}_{y}.geojson" for y in years}
eco_codes = [1,2,3,4,5,6,7,8,9,10,11,14,15,16,17]
labels = {
    1:'Evergreen needleleaf',2:'Evergreen broadleaf',3:'Deciduous needleleaf',4:'Deciduous broadleaf',
    5:'Mixed forest',6:'Wooded grassland',7:'Other wooded land',8:'Open shrubland',9:'Savanna',
    10:'Grassland',11:'Wetlands',14:'Crop/veg mosaic',15:'Snow & ice',16:'Barren',17:'Water'
}

# --- COMPUTE FFI ---
ffi_values = []
for year in years:
    path = files[year]
    if path.exists():
        gdf = gpd.read_file(path).to_crs(epsg=3857)
        gdf['area'] = gdf.geometry.area
        gdf['perimeter'] = gdf.geometry.length
        gdf['FD'] = np.log(gdf['perimeter']) / np.log(gdf['area'])
        mean_FD = gdf['FD'].mean()
        ffi_values.append((2 - mean_FD).round(3))
    else:
        ffi_values.append(np.nan)

# --- LOAD SPECIES RICHNESS ---
richness_file = BASE_DIR / 'Paris' / 'processed_species_iucn_gbif_results_center.csv'
if richness_file.exists():
    df_r = pd.read_csv(richness_file)
    richness_values = [
        float(df_r.loc[df_r['Year']==y, 'Richness'].iloc[0]) if y in df_r['Year'].values else np.nan
        for y in years
    ]
else:
    richness_values = [np.nan]*len(years)

# --- FLUCTUATING DENSITY SAMPLE ---
plant = [800, 820, 790, 910, 880, 940]
animal= [50, 60, 55, 65, 60, 70]
fungi = [100,95,120,110,130,125]
combined_density = (np.array(plant) + np.array(animal) + np.array(fungi)).tolist()

# --- LAYOUT: MAP & SLIM GRAPHS ---
map_col, graph_col = st.columns([2,1], gap='small')

with map_col:
    st.subheader(f"2023 Ecosystem Map — {selected}")
    f23 = files[2023]
    if f23.exists():
        lc = gpd.read_file(f23)
        lc['code'] = lc.get('LC_Class', lc.get('label')).astype(int)
        eco = lc[lc['code'].isin(eco_codes)].to_crs(epsg=4326)
        m = folium.Map(location=cfg['center'], zoom_start=cfg['zoom'], tiles='CartoDB positron')
        for _, r in eco.iterrows():
            c = int(r['code']); name = labels[c]
            fill = 'blue' if c==17 else 'yellow' if c in (8,9) else 'green'
            folium.GeoJson(
                r.geometry,
                style_function=lambda feat, fill=fill: {'fillColor': fill, 'color': fill, 'weight': 0.6, 'fillOpacity': 0.5},
                highlight_function=lambda feat: {'weight':2,'fillOpacity':0.7},
                tooltip=name
            ).add_to(m)
        st_folium(m, width='100%', height=500)
    else:
        st.error(f"Missing GeoJSON: {f23}")

with graph_col:
    st.subheader("Indicator Trends")
    dfm = pd.DataFrame({'Year': years, 'FFI': ffi_values, 'Richness': richness_values, 'Density': combined_density})
    # Slim line charts
    st.plotly_chart(px.line(dfm, x='Year', y='FFI', markers=True, height=150, title='FFI'), use_container_width=True)
    st.plotly_chart(px.line(dfm, x='Year', y='Richness', markers=True, height=150, title='Richness'), use_container_width=True)
    st.plotly_chart(px.line(dfm, x='Year', y='Density', markers=True, height=150, title='Combined Density'), use_container_width=True)

st.divider()
st.markdown("© 2025 Biomet.life")





