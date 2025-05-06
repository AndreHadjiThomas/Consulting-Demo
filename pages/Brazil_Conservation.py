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
    page_title='Biodiversity Monitoring Platform',
    page_icon='🌳',
    layout='wide'
)

# --- GLOBAL STYLES ---
st.markdown(
    """
    <style>
        /* Constrain app width and center */
        .stApp {
            max-width: 1200px;
            margin: auto;
        }
        /* Clean default UI elements */
        #MainMenu, footer, header {visibility: hidden;}
        .block-container {padding-top: 1rem;}
    </style>
    """,
    unsafe_allow_html=True
)

# --- APP HEADER & CONTROLS ---
col1, col2, col3, col4 = st.columns([4,1,1,1])
col1.markdown("# Reforestation & Biodiversity Monitoring Platform")
if col2.button("Add Region"): st.info("Add Region feature coming soon")
if col3.button("Settings"): st.info("Settings feature coming soon")
if col4.button("Help"): st.info("Help section coming soon")
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
    # Add more regions here
}
selected_region = st.selectbox('Select Region of Interest', list(regions.keys()))
cfg = regions[selected_region]

# --- DATA CONFIG ---
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

# --- METRIC CALCULATIONS ---
# Compute FFI per year
ffi_values = []
for year in years:
    path = geojson_files[year]
    if path.exists():
        gdf = gpd.read_file(path).to_crs(epsg=3857)
        gdf['area'] = gdf.geometry.area
        gdf['perimeter'] = gdf.geometry.length
        gdf['FD'] = np.log(gdf['perimeter']) / np.log(gdf['area'])
        ffi_values.append((2 - gdf['FD'].mean()).round(3))
    else:
        ffi_values.append(np.nan)

# Load species richness (sample from Paris)
richness_file = BASE_DIR / 'Paris' / 'processed_species_iucn_gbif_results_center.csv'
if richness_file.exists():
    df_r = pd.read_csv(richness_file)
    richness_values = [
        float(df_r.loc[df_r['Year']==y,'Richness'].iloc[0]) if y in df_r['Year'].values else np.nan
        for y in years
    ]
else:
    richness_values = [np.nan] * len(years)

# Combined density (sample values)
plant_density = [800, 850, 900, 950, 1000, 1050]
animal_density = [50, 55, 60, 65, 70, 75]
fungi_density  = [100, 110, 120, 130, 140, 150]
combined_density = (np.array(plant_density) + np.array(animal_density) + np.array(fungi_density)).tolist()

# --- DISPLAY MAP ---
file_2023 = geojson_files[2023]
if file_2023.exists():
    lc = gpd.read_file(file_2023)
    lc['code'] = lc.get('LC_Class', lc.get('label')).astype(int)
    eco = lc[lc['code'].isin(ecosystem_codes)].to_crs(epsg=4326)
    m = folium.Map(location=center, zoom_start=zoom_start, tiles='CartoDB positron')
    for _, row in eco.iterrows():
        code = row['code']
        name = land_use_classes.get(code)
        # Color logic
        if code == 17:
            fill = 'blue'
        elif code in [8, 9]:
            fill = 'yellow'
        else:
            fill = 'green'
        folium.GeoJson(
            row.geometry,
            style_function=lambda feat, fill=fill: {'fillColor': fill, 'color': fill, 'weight': 1, 'fillOpacity': 0.6},
            highlight_function=lambda feat: {'weight': 3, 'fillOpacity': 0.8},
            tooltip=name
        ).add_to(m)
    st_folium(m, width='100%', height=500)
else:
    st.error(f"2023 GeoJSON not found: {file_2023}")

# --- DISPLAY GRAPHS ---
st.subheader('Indicator Trends (2018–2023)')
cols = st.columns(3)
df_metrics = pd.DataFrame({
    'Year': years,
    'FFI': ffi_values,
    'Richness': richness_values,
    'Density': combined_density
})
cols[0].plotly_chart(px.line(df_metrics, x='Year', y='FFI', markers=True, title='FFI'), use_container_width=True)
cols[1].plotly_chart(px.line(df_metrics, x='Year', y='Richness', markers=True, title='Richness'), use_container_width=True)
cols[2].plotly_chart(px.line(df_metrics, x='Year', y='Density', markers=True, title='Combined Density'), use_container_width=True)

# --- FOOTER ---
st.divider()
st.markdown('© 2025 Biomet.life')




