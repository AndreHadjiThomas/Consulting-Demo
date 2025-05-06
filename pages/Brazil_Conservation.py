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
    page_icon='🌳',
    layout='wide',
    initial_sidebar_state='collapsed'
)
# Hide default UI elements and reduce padding
st.markdown("""
    <style>
        #MainMenu, footer, header {visibility: hidden;}
        .block-container {padding-top: 0.5rem;}
        .stButton>button {font-size:0.8rem; padding:0.25rem 0.5rem;}
        .css-1v3fvcr {font-size:1.25rem;}
    </style>
""", unsafe_allow_html=True)

# --- TOP BAR & CONTROLS ---
cols = st.columns([4, 1, 1, 1])
cols[0].markdown("## Reforestation & Biodiversity Platform")
if cols[1].button("Add Region"): st.info("Feature coming soon")
if cols[2].button("Settings"):   st.info("Feature coming soon")
if cols[3].button("Help"):       st.info("Feature coming soon")
st.divider()

# --- REGION SELECTION ---
BASE_DIR = Path(__file__).resolve().parent.parent
regions = {
    'Brazilian Amazon': {
        'data_folder': BASE_DIR / 'Biodiversity_brazil',
        'geo_prefix':  'BrazilAmazon',
        'center':      [-3.5, -62.0],
        'zoom':        5
    }
}
selected = st.selectbox("Select Region", list(regions.keys()), key="region")
cfg = regions[selected]
st.divider()

# --- DATA PREPARATION ---
years = list(range(2018, 2024))
files = {y: cfg['data_folder'] / f"{cfg['geo_prefix']}_{y}.geojson" for y in years}
eco_codes = [1,2,3,4,5,6,7,8,9,10,11,14,15,16,17]
labels = {
    1:'Evergreen needleleaf',2:'Evergreen broadleaf',3:'Deciduous needleleaf',4:'Deciduous broadleaf',
    5:'Mixed forest',6:'Wooded grassland',7:'Other wooded land',8:'Open shrubland',9:'Savanna',
    10:'Grassland',11:'Wetlands',14:'Crop/veg mosaic',15:'Snow & ice',16:'Barren',17:'Water'
}

# --- METRIC CALCULATIONS ---
# Fractal Fragmentation Index (FFI)
ffi = []
for y in years:
    path = files[y]
    if path.exists():
        gdf = gpd.read_file(path).to_crs(epsg=3857)
        gdf['area'] = gdf.geometry.area
        gdf['peri'] = gdf.geometry.length
        gdf['FD'] = np.log(gdf['peri']) / np.log(gdf['area'])
        ffi.append((2 - gdf['FD'].mean()).round(3))
    else:
        ffi.append(np.nan)

# Species Richness (sample load)
rich_file = BASE_DIR / 'Paris' / 'processed_species_iucn_gbif_results_center.csv'
if rich_file.exists():
    df_r = pd.read_csv(rich_file)
    rich = [float(df_r.loc[df_r.Year==y,'Richness']) if y in df_r.Year.values else np.nan for y in years]
else:
    rich = [np.nan]*len(years)

# Combined Density (plants, animals, fungi) — fluctuating example
density = [950, 1020, 980, 1050, 970, 1010]

# --- LAYOUT: MAP & GRAPH COLUMNS ---
map_col, graph_col = st.columns([3,1], gap="small")

with map_col:
    st.subheader(f"2023 Ecosystem Map — {selected}")
    path23 = files[2023]
    if path23.exists():
        lc = gpd.read_file(path23)
        lc['code'] = lc.get('LC_Class', lc.get('label')).astype(int)
        eco = lc[lc.code.isin(eco_codes)].to_crs(epsg=4326)
        m = folium.Map(location=cfg['center'], zoom_start=cfg['zoom'], tiles='CartoDB positron')
        for _, r in eco.iterrows():
            c = r.code; name = labels[c]
            col = 'blue' if c==17 else ('yellow' if c in (8,9) else 'green')
            folium.GeoJson(
                r.geometry,
                style_function=lambda feat, color=col: {'fillColor':color,'color':color,'weight':0.8,'fillOpacity':0.5},
                highlight_function=lambda feat: {'weight':2,'fillOpacity':0.7},
                tooltip=name
            ).add_to(m)
        st_folium(m, width=600, height=900)
    else:
        st.error(f"Missing GeoJSON: {path23}")

with graph_col:
    st.subheader("Indicator Trends (2018–2023)")
    dfm = pd.DataFrame({'Year':years,'FFI':ffi,'Richness':rich,'Density':density})
    # Slim graphs stacked vertically
    fig1 = px.line(dfm, x='Year', y='FFI', markers=True, title='FFI')
    st.plotly_chart(fig1, use_container_width=True, height=80)
    fig2 = px.line(dfm, x='Year', y='Richness', markers=True, title='Richness')
    st.plotly_chart(fig2, use_container_width=True, height=80)
    fig3 = px.line(dfm, x='Year', y='Density', markers=True, title='Combined Density')
    st.plotly_chart(fig3, use_container_width=True, height=80)

# --- FOOTER ---
st.divider()
st.markdown("© 2025 Biomet.life")






