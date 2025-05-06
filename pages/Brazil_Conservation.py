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
    page_title='Reforestation & Biodiversity Monitoring Platform',
    page_icon='🌳',
    layout='wide',
    initial_sidebar_state='expanded'
)
# Hide default Streamlit header and footer for clean interface
st.markdown(
    """
    <style>
        #MainMenu {visibility: hidden;}
        footer {visibility: hidden;}
        header {visibility: hidden;}
    </style>
    """,
    unsafe_allow_html=True
)

# --- REGION SELECTION ---
BASE_DIR = Path(__file__).resolve().parent.parent
regions = {
    'Brazilian Amazon': {
        'name': 'Brazilian Amazon',
        'data_folder': BASE_DIR / 'Biodiversity_brazil',
        'geo_prefix': 'BrazilAmazon',
        'center': [-3.5, -62.0],
        'zoom': 5
    }
    # Add more regions here as needed
}
selected_region = st.selectbox(
    'Select Region of Interest',
    list(regions.keys()),
    key='region_select'
)
region_cfg = regions[selected_region]

data_folder = region_cfg['data_folder']
center = region_cfg['center']
zoom_start = region_cfg['zoom']
prefix = region_cfg['geo_prefix']

# --- DATA CONFIG ---
years = list(range(2018, 2024))
geojson_files = {year: data_folder / f"{prefix}_{year}.geojson" for year in years}
ecosystem_codes = [1,2,3,4,5,6,7,8,9,10,11,14,15,16,17]
# MODIS land cover class labels\m
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

# Load species richness from Paris dataset (as example)
richness_file = BASE_DIR / 'Paris' / 'processed_species_iucn_gbif_results_center.csv'
if richness_file.exists():
    df_r = pd.read_csv(richness_file)
    richness_values = [
        float(df_r.loc[df_r['Year']==y, 'Richness'].iloc[0]) if y in df_r['Year'].values else np.nan
        for y in years
    ]
else:
    richness_values = [np.nan] * len(years)

# Combined density: sample data
plant_density = [800,850,900,950,1000,1050]
animal_density = [50,55,60,65,70,75]
fungi_density = [100,110,120,130,140,150]
combined_density = (np.array(plant_density) + np.array(animal_density) + np.array(fungi_density)).tolist()

# --- LAYOUT: MAP & DASHBOARD ---
col_map, col_metrics = st.columns([3,1], gap='large')

with col_map:
    st.subheader(f"2023 Ecosystem Map — {selected_region}")
    # Load 2023 GeoJSON and filter ecosystems
    file_2023 = geojson_files[2023]
    if file_2023.exists():
        lc = gpd.read_file(file_2023)
        lc['code'] = lc.get('LC_Class', lc.get('label')).astype(int)
        eco = lc[lc['code'].isin(ecosystem_codes)].to_crs(epsg=4326)
        m = folium.Map(location=center, zoom_start=zoom_start, tiles='CartoDB positron')
        for _, row in eco.iterrows():
            code = row['code']; name = land_use_classes.get(code, f'Class {code}')
            # Color by class type
            if code == 17:
                fill = 'blue'
            elif code in [8,9]:
                fill = 'yellow'
            else:
                fill = 'green'
            folium.GeoJson(
                row.geometry,
                style_function=lambda feat, fill=fill: {'fillColor': fill, 'color': fill, 'weight': 1, 'fillOpacity': 0.6},
                highlight_function=lambda feat: {'weight': 3, 'fillOpacity': 0.8},
                tooltip=name
            ).add_to(m)
        st_folium(m, width='100%', height=700)
    else:
        st.error(f"2023 GeoJSON not found: {file_2023}")

with col_metrics:
    st.subheader('Indicator Trends (2018–2023)')
    df_metrics = pd.DataFrame({
        'Year': years,
        'FFI': ffi_values,
        'Richness': richness_values,
        'Combined Density': combined_density
    })
    # FFI chart
    fig1 = px.line(df_metrics, x='Year', y='FFI', markers=True, title='Fractal Fragmentation Index (FFI)', color_discrete_sequence=['#2E8B57'])
    st.plotly_chart(fig1, use_container_width=True)
    # Richness chart
    fig2 = px.line(df_metrics, x='Year', y='Richness', markers=True, title='Species Richness (α/γ)', color_discrete_sequence=['#1F78B4'])
    st.plotly_chart(fig2, use_container_width=True)
    # Density chart
    fig3 = px.line(df_metrics, x='Year', y='Combined Density', markers=True, title='Combined Density (Plants, Animals & Fungi)', color_discrete_sequence=['#FF8C00'])
    st.plotly_chart(fig3, use_container_width=True)

# Footer
st.divider()
st.markdown('© 2025 Biomet.life')




