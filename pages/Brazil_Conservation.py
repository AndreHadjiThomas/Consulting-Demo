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
# Hide default Streamlit header and footer for a clean, app-like look
st.markdown("""
    <style>
        #MainMenu, footer, header {visibility: hidden;}
        .block-container {padding-top: 1rem;}
    </style>
""", unsafe_allow_html=True)

# --- APP HEADER & CONTROLS ---
header = st.container()
with header:
    cols = st.columns([4,1,1,1])
    cols[0].markdown("# Reforestation & Biodiversity Monitoring Platform")
    if cols[1].button("Add Region"):
        st.info("Add Region feature coming soon")
    if cols[2].button("Settings"):
        st.info("Settings feature coming soon")
    if cols[3].button("Help"):
        st.info("Help section coming soon")
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
    # Extend with additional regions if needed
}
selected_region = st.selectbox('Select Region of Interest', list(regions.keys()))
cfg = regions[selected_region]

data_folder = cfg['data_folder']
prefix = cfg['geo_prefix']
center = cfg['center']
zoom_start = cfg['zoom']

years = list(range(2018, 2024))
geojson_files = {y: data_folder / f"{prefix}_{y}.geojson" for y in years}
ecosystem_codes = [1,2,3,4,5,6,7,8,9,10,11,14,15,16,17]
land_use_classes = {
    1: 'Evergreen needleleaf forest', 2: 'Evergreen broadleaf forest',
    3: 'Deciduous needleleaf forest', 4: 'Deciduous broadleaf forest',
    5: 'Mixed forest', 6: 'Wooded grassland', 7: 'Other wooded land',
    8: 'Open shrubland', 9: 'Savanna', 10: 'Grassland',
    11: 'Permanent wetlands', 14: 'Cropland/natural vegetation mosaic',
    15: 'Snow and ice', 16: 'Barren or sparsely vegetated', 17: 'Water'
}

# --- CALCULATE METRICS ---
# FFI
ffi_vals = []
for y in years:
    path = geojson_files[y]
    if path.exists():
        gdf = gpd.read_file(path).to_crs(epsg=3857)
        gdf['area'] = gdf.geometry.area
        gdf['perimeter'] = gdf.geometry.length
        gdf['FD'] = np.log(gdf['perimeter'])/np.log(gdf['area'])
        ffi_vals.append((2 - gdf['FD'].mean()).round(3))
    else:
        ffi_vals.append(np.nan)
# Richness (fallback sample)
richness_file = BASE_DIR / 'Paris' / 'processed_species_iucn_gbif_results_center.csv'
if richness_file.exists():
    df_r = pd.read_csv(richness_file)
    richness_vals = [
        float(df_r.loc[df_r['Year']==y,'Richness'].iloc[0]) if y in df_r['Year'].values else np.nan
        for y in years
    ]
else:
    richness_vals = [np.nan]*len(years)
# Combined density sample
pd_plants = [800,850,900,950,1000,1050]
pd_animals = [50,55,60,65,70,75]
pd_fungi = [100,110,120,130,140,150]
combined_density = (np.array(pd_plants)+np.array(pd_animals)+np.array(pd_fungi)).tolist()

# --- DISPLAY MAP ---
map_container = st.container()
with map_container:
    st.subheader(f"2023 Ecosystem Map — {selected_region}")
    file2023 = geojson_files[2023]
    if file2023.exists():
        lc = gpd.read_file(file2023)
        lc['code'] = lc.get('LC_Class',lc.get('label')).astype(int)
        eco = lc[lc['code'].isin(ecosystem_codes)].to_crs(epsg=4326)
        m = folium.Map(location=center, zoom_start=zoom_start, tiles='CartoDB positron')
        for _, r in eco.iterrows():
            c = r['code']; name=land_use_classes.get(c,f'Class {c}')
            if c==17: fill='blue'
            elif c in [8,9]: fill='yellow'
            else: fill='green'
            folium.GeoJson(
                r.geometry,
                style_function=lambda feat, fill=fill:{{'fillColor':fill,'color':fill,'weight':1,'fillOpacity':0.6}},
                highlight_function=lambda feat:{{'weight':3,'fillOpacity':0.8}},
                tooltip=name
            ).add_to(m)
        st_folium(m,width='100%',height=600)
    else:
        st.error(f"GeoJSON missing: {file2023}")

# --- DISPLAY METRIC GRAPHS ---
graphs = st.container()
with graphs:
    st.subheader('Indicator Trends (2018–2023)')
    dfm = pd.DataFrame({'Year': years, 'FFI': ffi_vals, 'Richness': richness_vals, 'Density': combined_density})
    cols = st.columns(3)
    fig_ffi = px.line(dfm, x='Year', y='FFI', markers=True, title='FFI', color_discrete_sequence=['#2E8B57'])
    cols[0].plotly_chart(fig_ffi, use_container_width=True)
    fig_r = px.line(dfm, x='Year', y='Richness', markers=True, title='Richness', color_discrete_sequence=['#1F78B4'])
    cols[1].plotly_chart(fig_r, use_container_width=True)
    fig_d = px.line(dfm, x='Year', y='Density', markers=True, title='Combined Density', color_discrete_sequence=['#FF8C00'])
    cols[2].plotly_chart(fig_d, use_container_width=True)

# --- FOOTER ---
st.divider()
st.markdown('© 2025 Biomet.life')




