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
    layout='wide'
)
# --- CUSTOM CSS FOR SCALING ---
st.markdown(
    """
    <style>
        /* Container fills viewport */
        .block-container {
            max-width: 100vw;
            max-height: 100vh;
            padding: 0.5rem;
            margin: 0;
            overflow: hidden;
        }
        /* Adjust map iframe height */
        .stIframe iframe {
            height: 50vh !important;
        }
    </style>
    """,
    unsafe_allow_html=True
)

# Hide default Streamlit header/footer
st.markdown(
    """
    <style>
        #MainMenu, footer, header {visibility: hidden;}
    </style>
    """,
    unsafe_allow_html=True
)

# --- APP HEADER & CONTROLS ---
cols = st.columns([4,1,1,1])
cols[0].markdown("# Reforestation & Biodiversity Monitoring Platform")
if cols[1].button("Add Region"): st.info("Add Region feature coming soon")
if cols[2].button("Settings"): st.info("Settings feature coming soon")
if cols[3].button("Help"): st.info("Help section coming soon")
st.divider()

# --- REGION SELECTION ---
BASE_DIR = Path(__file__).resolve().parent.parent
regions = {
    'Brazilian Amazon': {'data_folder': BASE_DIR / 'Biodiversity_brazil', 'geo_prefix': 'BrazilAmazon', 'center': [-3.5, -62.0], 'zoom': 5}
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
land_use_classes = {1: 'Evergreen needleleaf forest',2:'Evergreen broadleaf forest',3:'Deciduous needleleaf forest',4:'Deciduous broadleaf forest',5:'Mixed forest',6:'Wooded grassland',7:'Other wooded land',8:'Open shrubland',9:'Savanna',10:'Grassland',11:'Permanent wetlands',14:'Cropland/natural vegetation mosaic',15:'Snow and ice',16:'Barren or sparsely vegetated',17:'Water'}

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
        ffi_values.append(round(2 - mean_FD, 3))
    else:
        ffi_values.append(np.nan)

# --- LOAD RICHNESS VALUES ---
richness_file = BASE_DIR / 'Paris' / 'processed_species_iucn_gbif_results_center.csv'
if richness_file.exists():
    df_r = pd.read_csv(richness_file)
    richness_values = [float(df_r.loc[df_r['Year']==y, 'Richness'].iloc[0]) if y in df_r['Year'].values else np.nan for y in years]
else:
    richness_values = [np.nan] * len(years)

# --- COMBINED DENSITY SAMPLE ---
plant_density = [800,850,900,950,1000,1050]
animal_density = [50,55,60,65,70,75]
fungi_density = [100,110,120,130,140,150]
combined_density = (np.array(plant_density) + np.array(animal_density) + np.array(fungi_density)).tolist()

# --- DISPLAY MAP & GRAPHS ---
st.subheader(f"2023 Ecosystem Map — {selected_region}")
file_2023 = geojson_files[2023]
if file_2023.exists():
    lc = gpd.read_file(file_2023)
    lc['code'] = lc.get('LC_Class', lc.get('label')).astype(int)
    eco = lc[lc['code'].isin(ecosystem_codes)].to_crs(epsg=4326)
    m = folium.Map(location=center, zoom_start=zoom_start, tiles='CartoDB positron')
    for _, r in eco.iterrows():
        code = r['code']; name = land_use_classes.get(code)
        if code == 17:
            fill = 'blue'
        elif code in [8,9]:
            fill = 'yellow'
        else:
            fill = 'green'
        folium.GeoJson(
            r.geometry,
            style_function=lambda feat, fill=fill: {'fillColor': fill, 'color': fill, 'weight': 1, 'fillOpacity': 0.6},
            highlight_function=lambda feat: {'weight': 3, 'fillOpacity': 0.8},
            tooltip=name
        ).add_to(m)
    st_folium(m, width='100%', height=None)
else:
    st.error(f"GeoJSON missing: {file_2023}")

st.subheader('Indicator Trends (2018–2023)')
cols = st.columns(3)
df_metrics = pd.DataFrame({'Year': years, 'FFI': ffi_values, 'Richness': richness_values, 'Density': combined_density})
# Create charts with fixed height
fig_ffi = px.line(df_metrics, x='Year', y='FFI', markers=True, title='FFI')
fig_ffi.update_layout(height=250)
cols[0].plotly_chart(fig_ffi, use_container_width=True)

fig_rich = px.line(df_metrics, x='Year', y='Richness', markers=True, title='Richness')
fig_rich.update_layout(height=250)
cols[1].plotly_chart(fig_rich, use_container_width=True)

fig_den = px.line(df_metrics, x='Year', y='Density', markers=True, title='Combined Density')
fig_den.update_layout(height=250)
cols[2].plotly_chart(fig_den, use_container_width=True)

st.divider()
st.markdown('© 2025 Biomet.life')




