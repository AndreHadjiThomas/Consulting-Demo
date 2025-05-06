import streamlit as st
import pandas as pd
import numpy as np
import geopandas as gpd
import folium
import matplotlib.pyplot as plt
from pathlib import Path
from streamlit_folium import st_folium

# --- PAGE CONFIG ---
st.set_page_config(page_title='Reforestation Assessment Dashboard', layout='wide')

# --- DATA CONFIG ---
BASE_DIR   = Path(__file__).resolve().parent.parent
data_folder   = BASE_DIR / "Biodiversity_brazil"
# GeoJSON files for each year 2018-2023
years = list(range(2018, 2024))
geojson_files = {year: data_folder / f'BrazilAmazon_{year}.geojson' for year in years}
# Ecosystem classes to represent
ecosystem_codes = [1,2,3,4,5,6,7,8,9,10,11,14,15,16,17]

# --- COMPUTE FFI FOR EACH YEAR ---
ffi_values = []
for year in years:
    file_path = geojson_files[year]
    if file_path.exists():
        gdf = gpd.read_file(file_path).to_crs(epsg=3857)
        gdf['area'] = gdf.geometry.area
        gdf['perimeter'] = gdf.geometry.length
        gdf['FD'] = np.log(gdf['perimeter']) / np.log(gdf['area'])
        mean_FD = gdf['FD'].mean()
        ffi_values.append(2 - mean_FD)
    else:
        ffi_values.append(np.nan)

# --- LOAD RICHNESS VALUES FROM PARIS FILE ---
richness_file = BASE_DIR / 'Paris' / 'processed_species_iucn_gbif_results_center.csv'
if richness_file.exists():
    richness_df = pd.read_csv(richness_file)
    richness_values = [
        float(richness_df.loc[richness_df['Year']==year, 'Richness'].iloc[0])
        if (richness_df['Year']==year).any() else np.nan
        for year in years
    ]
else:
    richness_values = [np.nan] * len(years)

# --- DENSITY METRICS & COMBINED DENSITY ---
# sample density values (plants, animals, fungi)
plant_density = [800, 850, 900, 950, 1000, 1050]
animal_density = [50, 55, 60, 65, 70, 75]
fungi_density  = [100, 110, 120, 130, 140, 150]
combined_density = (
    np.array(plant_density) +
    np.array(animal_density) +
    np.array(fungi_density)
).tolist()

# --- LOAD & FILTER 2023 LAND COVER ---
lc_file_2023 = geojson_files[2023]
if not lc_file_2023.exists():
    st.error(f"Land cover file not found: {lc_file_2023}")
    st.stop()
lc_gdf = gpd.read_file(lc_file_2023)
# filter only ecosystem polygons
if 'LC_Class' in lc_gdf.columns:
    lc_gdf = lc_gdf[lc_gdf['LC_Class'].isin(ecosystem_codes)]
elif 'label' in lc_gdf.columns:
    lc_gdf = lc_gdf[lc_gdf['label'].isin(ecosystem_codes)]
# project for mapping
lc_gdf = lc_gdf.to_crs(epsg=4326)

# === LAYOUT ===
left_col, right_col = st.columns([3, 1])

with left_col:
    st.subheader("2023 Ecosystem Polygons - Brazilian Amazon")
    m = folium.Map(location=[-3.5, -62.0], zoom_start=5, tiles='CartoDB positron')
    for _, row in lc_gdf.iterrows():
        folium.GeoJson(
            row.geometry,
            style_function=lambda _, color='green': {
                'fillColor': color,
                'color': 'black', 'weight': 0.3, 'fillOpacity': 0.6
            }
        ).add_to(m)
    st_folium(m, width=900, height=700)

with right_col:
    st.subheader("Metric Trends (2018-2023)")

    # FFI evolution
    ffi_df = pd.DataFrame({'Year': years, 'FFI': ffi_values})
    fig1 = px.line(ffi_df, x='Year', y='FFI', markers=True, title='FFI Evolution')
    st.plotly_chart(fig1, use_container_width=True)

    # Richness evolution
    richness_df_plot = pd.DataFrame({'Year': years, 'Richness': richness_values})
    fig2 = px.line(richness_df_plot, x='Year', y='Richness', markers=True, title='Richness Evolution', color_discrete_sequence=['#636EFA'])
    st.plotly_chart(fig2, use_container_width=True)

    # Combined density evolution
    density_df = pd.DataFrame({
        'Year': years,
        'Combined Density': combined_density
    })
    fig3 = px.line(density_df, x='Year', y='Combined Density', markers=True, title='Combined Plant, Animal & Fungi Density')
    st.plotly_chart(fig3, use_container_width=True)
