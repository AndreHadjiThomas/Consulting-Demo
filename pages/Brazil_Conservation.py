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

# --- COMPUTE FFI FOR EACH YEAR ---
ffi_values = []
for year in years:
    file_path = geojson_files[year]
    if file_path.exists():
        gdf = gpd.read_file(file_path)
        # Project to metric CRS for accurate area/perimeter
        gdf = gdf.to_crs(epsg=3857)
        gdf['area'] = gdf.geometry.area
        gdf['perimeter'] = gdf.geometry.length
        # Fractal dimension per patch
        gdf['FD'] = np.log(gdf['perimeter']) / np.log(gdf['area'])
        mean_FD = gdf['FD'].mean()
        ffi_values.append(2 - mean_FD)
    else:
        ffi_values.append(np.nan)

# --- SAMPLE RICHNESS & DENSITY DATA ---
# (Replace with real computations or data loading as needed)
richness_values = [0.60, 0.63, 0.66, 0.70, 0.73, 0.75]
plant_density = [800, 850, 900, 950, 1000, 1050]
animal_density = [50, 55, 60, 65, 70, 75]

# --- LOAD 2023 LAND COVER ---
lc_file_2023 = geojson_files[2023]
if lc_file_2023.exists():
    lc_gdf = gpd.read_file(lc_file_2023)
else:
    st.error(f"Land cover file not found: {lc_file_2023}")
    st.stop()

# Utility: plot line charts
def plot_line_chart(x, ys, labels, title, y_label):
    fig, ax = plt.subplots()
    for y, label in zip(ys, labels):
        ax.plot(x, y, marker='o', label=label)
    ax.set_title(title)
    ax.set_xlabel('Year')
    ax.set_ylabel(y_label)
    ax.legend()
    st.pyplot(fig)

# === LAYOUT ===
left_col, right_col = st.columns([2, 1])

with left_col:
    st.subheader("2023 Land Cover - Brazilian Amazon")
    m = folium.Map(location=[-3.5, -62.0], zoom_start=5, tiles='CartoDB positron')
    for _, row in lc_gdf.iterrows():
        folium.GeoJson(
            row.geometry,
            style_function=lambda feat, color='green': {
                'fillColor': color,
                'color': 'black', 'weight': 0.2, 'fillOpacity': 0.5
            }
        ).add_to(m)
    st_folium(m, width=700, height=500)

with right_col:
    st.subheader("Metric Trends (2018-2023)")

    st.markdown("**Fractal Fragmentation Index (FFI)**")
    plot_line_chart(years, [ffi_values], ['FFI'], 'FFI Evolution', 'FFI')

    st.markdown("**Species Richness (α/γ)**")
    plot_line_chart(years, [richness_values], ['Richness'], 'Richness Evolution', 'Richness')

    st.markdown("**Plant & Animal Density**")
    plot_line_chart(
        years,
        [plant_density, animal_density],
        ['Plant Density', 'Animal Density'],
        'Density Evolution',
        'Individuals per ha'
    )
