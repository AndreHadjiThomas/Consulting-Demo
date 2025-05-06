
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
    page_title='Plateforme de Suivi Reforestation & Biodiversité',
    page_icon='🌳',
    layout='wide',
    initial_sidebar_state='collapsed'
)
# Hide Streamlit menu and footer for a cleaner look
st.markdown("""
    <style>
        #MainMenu {visibility: hidden;}
        footer {visibility: hidden;}
        header {visibility: hidden;}
    </style>
""", unsafe_allow_html=True)

# --- HEADER ---
header_container = st.container()
with header_container:
    st.markdown(
        "# Plateforme de Suivi Reforestation & Biodiversité  🌳\n"
        "**Ministère de la Transition Écologique**"
        "Suivi des indicateurs clés de l’Amazonie brésilienne pour l’allocation budgétaire"
    )
    st.divider()

# --- DATA CONFIG ---
BASE_DIR   = Path(__file__).resolve().parent.parent
data_folder   = BASE_DIR / "Biodiversity_brazil"
# Years and files
years = list(range(2018, 2024))
geojson_files = {year: data_folder / f'BrazilAmazon_{year}.geojson' for year in years}
# Ecosystem codes and labels
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
# FFI
ffi_values = []
for year in years:
    file_path = geojson_files[year]
    if file_path.exists():
        gdf = gpd.read_file(file_path).to_crs(epsg=3857)
        gdf['area'] = gdf.geometry.area
        gdf['perimeter'] = gdf.geometry.length
        gdf['FD'] = np.log(gdf['perimeter']) / np.log(gdf['area'])
        ffi_values.append(2 - gdf['FD'].mean())
    else:
        ffi_values.append(np.nan)
# Richness
richness_file = BASE_DIR / 'Paris' / 'processed_species_iucn_gbif_results_center.csv'
if richness_file.exists():
    df_r = pd.read_csv(richness_file)
    richness_values = [
        float(df_r.loc[df_r['Year']==y, 'Richness'].iloc[0]) if y in df_r['Year'].values else np.nan
        for y in years
    ]
else:
    richness_values = [np.nan]*len(years)
# Combined density (plants+animals+fungi)
plant_density  = [800,850,900,950,1000,1050]
animal_density = [50,55,60,65,70,75]
fungi_density  = [100,110,120,130,140,150]
combined_density = (np.array(plant_density)+np.array(animal_density)+np.array(fungi_density)).tolist()

# --- LAYOUT: MAP & METRICS ---
map_col, metrics_col = st.columns([3,1], gap='large')

with map_col:
    st.subheader("Carte des écosystèmes 2023 - Amazonie brésilienne")
    # Load and filter 2023
    lc_file_2023 = geojson_files[2023]
    if not lc_file_2023.exists():
        st.error(f"Fichier introuvable: {lc_file_2023}")
    else:
        lc = gpd.read_file(lc_file_2023)
        lc['code'] = lc.get('LC_Class', lc.get('label')).astype(int)
        eco = lc[lc['code'].isin(ecosystem_codes)].to_crs(epsg=4326)
        m = folium.Map(location=[-3.5, -62.0], zoom_start=5, tiles='CartoDB positron')
        # Add polygons
        for _, row in eco.iterrows():
            cls = row['code']; name = land_use_classes.get(cls,f"Class {cls}")
            # color logic
            if cls==17: fill='blue'
            elif cls in [8,9]: fill='yellow'
            else: fill='green'
            folium.GeoJson(
                row.geometry,
                style_function=lambda f, fill=fill: {{'fillColor':fill,'color':fill,'weight':1,'fillOpacity':0.5}},
                highlight_function=lambda f: {{'weight':3,'fillOpacity':0.8}},
                tooltip=name
            ).add_to(m)
        st_folium(m, width= '100%', height=700)

with metrics_col:
    st.subheader("Évolution des indicateurs")
    # Prepare DataFrame
    df_metrics = pd.DataFrame({
        'Year': years,
        'FFI': ffi_values,
        'Richness': richness_values,
        'Density': combined_density
    })
    # FFI
    fig_ffi = px.line(df_metrics, x='Year', y='FFI', markers=True, title='Indice de fragmentation (FFI)', color_discrete_sequence=['#238b45'])
    st.plotly_chart(fig_ffi, use_container_width=True)
    # Richness
    fig_r = px.line(df_metrics, x='Year', y='Richness', markers=True, title='Richesse α/γ', color_discrete_sequence=['#2c7fb8'])
    st.plotly_chart(fig_r, use_container_width=True)
    # Density
    fig_d = px.line(df_metrics, x='Year', y='Density', markers=True, title='Densité combinée (plantes+faune+champignons)', color_discrete_sequence=['#7f2704'])
    st.plotly_chart(fig_d, use_container_width=True)

# --- FOOTER ---
st.divider()
st.markdown("© 2025 Ministère de la Transition Écologique")




