import streamlit as st
import geopandas as gpd
import pandas as pd
import shapely.geometry
import folium
from streamlit_folium import st_folium
import os
import math
import ast
from pathlib import Path
import plotly.express as px
import numpy as np
import openpyxl
import io
from docx import Document
import io, base64


st.set_page_config(page_title="Stanlow Risk Viewer", layout="wide")

# === USER CONFIG ===
latitude = 37.75
longitude = 22.25
radius_m = 5000
positions = [
    "top_left", "top_center", "top_right",
    "left_center", "center", "right_center",
    "bottom_left", "bottom_center", "bottom_right"
]

BASE_DIR   = Path(__file__).resolve().parent.parent  
data_folder = BASE_DIR / "MOH"
#threshold_path = data_folder / 'Water and Air Quality Thresholds.xlsx'
richness_folder = data_folder
risk_folder = data_folder
landcover_file = data_folder / 'export_land_cover_polygons_Motor_oil_landcov_2018.geojson'

# === Confirmed Invasive Species in Europe ===
invasive_species_europe = [
    "Eriocheir sinensis", "Alopochen aegyptiacus",
    "Sciurus carolinensis", "Muntiacus reevesi",
    "Pacifastacus leniusculus", "Trachemys scripta",
    "Lysichiton americanus", "Gunnera tinctoria",
    "Lagarosiphon major", "Hydrocotyle ranunculoides",
    "Heracleum mantegazzianum", "Impatiens glandulifera",
    "Elodea nuttallii", "Myriophyllum aquaticum"
]

# --- THRESHOLD LOADING & EXCEEDANCE FUNCTIONS ---
#threshold_path = data_folder / 'Water and Air Quality Thresholds.xlsx'
#thresholds = pd.read_excel(threshold_path, sheet_name=None)
#ecosystem_water = thresholds['Ecosystem Water Quality']
#human_water    = thresholds['Human Water Quality ']
#epa_air        = thresholds['EPA Air Quality']
#who_air        = thresholds['WHO Air Quality']

# def clean_names(s: pd.Series) -> pd.Series:
#     return (
#         s.astype(str)
#          .str.replace('\xa0',' ', regex=False)
#          .str.replace('\xad','',  regex=False)
#          .str.strip()
#          .str.lower()
#     )

# for df, col in [
#     (ecosystem_water, 'Pollutant (P = Priority Pollutant)'),
#     (human_water,    'Pollutant (P = Priority Pollutant)'),
#     (epa_air,        'Pollutant'),
#     (who_air,        'Pollutant'),
# ]:
#     df['clean_pollutant'] = clean_names(df[col])

# ecosystem_water['thr_num'] = pd.to_numeric(
#     ecosystem_water['Freshwater CCC (chronic, µg/L)'], errors='coerce'
# )
# human_water['thr_num']    = pd.to_numeric(
#     human_water['Freshwater CCC (chronic, µg/L)'], errors='coerce'
# )
# epa_air['thr_num'] = (
#     epa_air['Level'].astype(str).str.extract(r'(\d+\.?\d*)')[0].astype(float)
# )
# who_air['thr_num'] = (
#     who_air['2021 AQG Level'].astype(str).str.extract(r'(\d+\.?\d*)')[0].astype(float)
# )

def check_exceedances(sites: dict, df: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for site_name, measurements in sites.items():
        for pollutant, measured in measurements.items():
            key = pollutant.strip().lower()
            match = df[df['clean_pollutant'] == key]
            if not match.empty:
                thr = match['thr_num'].iloc[0]
                if pd.notna(thr) and measured > thr:
                    rows.append({
                        'Site': site_name,
                        'Pollutant': pollutant,
                        'Measured': measured,
                        'Threshold': thr
                    })
    return pd.DataFrame(rows)



def create_nine_centers(lat, lon, radius):
    earth_radius = 6378137
    delta_lat = (radius*math.sqrt(2))/earth_radius*(180/math.pi)
    delta_lon = delta_lat/math.cos(math.radians(lat))
    return [
        (lat+2*delta_lat, lon-2*delta_lon), (lat+2*delta_lat, lon), (lat+2*delta_lat, lon+2*delta_lon),
        (lat, lon-2*delta_lon), (lat, lon), (lat, lon+2*delta_lon),
        (lat-2*delta_lat, lon-2*delta_lon),(lat-2*delta_lat, lon),(lat-2*delta_lat, lon+2*delta_lon)
    ]

def create_square_region(lat, lon, radius_m):
    earth_radius = 6378137
    delta_lat = ((radius_m * math.sqrt(2)) / earth_radius) * (180 / math.pi)
    delta_lon = delta_lat / abs(math.cos(math.radians(lat)))
    top_left = [lon - delta_lon, lat + delta_lat]
    top_right = [lon + delta_lon, lat + delta_lat]
    bottom_right = [lon + delta_lon, lat - delta_lat]
    bottom_left = [lon - delta_lon, lat - delta_lat]
    return shapely.geometry.Polygon([top_left, top_right, bottom_right, bottom_left, top_left])

centers = create_nine_centers(latitude, longitude, radius_m)
grid_geometries = [create_square_region(lat, lon, radius_m) for lat, lon in centers]

richness_values, alpha_values = [], []
for pos in positions:
    path = richness_folder / f"processed_species_iucn_gbif_results_{pos}.csv"
    try:
        df = pd.read_csv(path)
        row = df[df['Year']==2023]
        richness_values.append(float(row['Richness'].values[0]) if not row.empty else None)
        alpha_values.append(float(row['Alpha'].values[0]) if not row.empty else None)
    except:
        richness_values.append(None)
        alpha_values.append(None)

grid_gdf = gpd.GeoDataFrame({
    'Position':positions, 'Richness':richness_values, 'Alpha':alpha_values
}, geometry=grid_geometries, crs="EPSG:4326")

water_classes = {511,512,521,522,523}
ecosystem_classes = {141,243,244,311,312,313,321,322,323,324,331,332,333,334,335,411,412,421,422,423}
land_cover_dict = {     111: "Continuous urban fabric", 112: "Discontinuous urban fabric",
    121: "Industrial/commercial units", 122: "Roads and rail",
    123: "Port areas", 124: "Airports", 131: "Mineral extraction sites",
    132: "Dump sites", 133: "Construction sites", 141: "Green urban areas",
    142: "Sport and leisure", 211: "Non‑irrigated arable land",
    212: "Permanently irrigated land", 213: "Rice fields",
    221: "Vineyards", 222: "Fruit trees and berry plantations",
    223: "Olive groves", 231: "Pastures",
    241: "Annual crops with natural vegetation",
    242: "Complex cultivation patterns", 243: "Agro‑forestry",
    311: "Broad‑leaved forest", 312: "Coniferous forest",
    313: "Mixed forest", 321: "Natural grasslands",
    322: "Moors and heathland", 323: "Sclerophyllous vegetation",
    324: "Transitional woodland‑shrub", 331: "Beaches and dunes",
    332: "Bare rocks", 333: "Sparsely vegetated", 334: "Burnt areas",
    335: "Glaciers", 411: "Inland wetlands", 412: "Peat bogs",
    421: "Salt marshes", 422: "Salines", 423: "Intertidal flats",
    511: "Water courses", 512: "Water bodies", 521: "Coastal lagoons",
    522: "Estuaries", 523: "Sea and ocean" }  

# Build map function with dynamic layers
def build_map(show_richness, show_risks, show_landcover, show_kba_only= True):
    m = folium.Map(location=[latitude, longitude], zoom_start=11, tiles='CartoDB positron')

    # Land cover
    if show_landcover and landcover_file.exists():
        lc_gdf = gpd.read_file(landcover_file)
        lc_gdf = lc_gdf[lc_gdf['label'].notna()]
        lc_gdf['label'] = lc_gdf['label'].astype(int)
        for _, row in lc_gdf.iterrows():
            fill_color = ('blue' if row['label'] in water_classes else
                          'green' if row['label'] in ecosystem_classes else 'gray')
            folium.GeoJson(
                row['geometry'],
                style_function=lambda feat, c=fill_color: {'fillColor': c, 'color': 'black', 'weight': 0.3, 'fillOpacity': 0.5},
                tooltip=land_cover_dict.get(row['label'], f'Unknown ({row["label"]})')
            ).add_to(m)

    # Species richness
    if show_richness:
        colormap = folium.LinearColormap(['red','orange','yellow'],
                                         vmin=min(v for v in richness_values if v is not None),
                                         vmax=max(v for v in richness_values if v is not None),
                                         caption="Species Richness")
        for _, row in grid_gdf.iterrows():
            color = colormap(row['Richness']) if row['Richness'] is not None else 'gray'
            weight = 3 if row['Position']=='center' else 1
            folium.GeoJson(
                row.geometry.__geo_interface__,
                style_function=lambda feat, col=color, w=weight: {'fillColor': col, 'color': 'black', 'weight': w, 'fillOpacity': 0.6}
            ).add_to(m)
            cent = row.geometry.centroid
            html = f"<div style='font-size:12px;text-align:center'><b>{row['Position']}</b><br>Richness: {row['Richness']:.2f}<br>Alpha: {row['Alpha']:.2f}</div>"
            folium.Marker(location=[cent.y, cent.x], icon=folium.DivIcon(html=html)).add_to(m)
        colormap.add_to(m)

    # Environmental risks
    if show_risks:
        for pos, (lat, lon) in zip(positions, centers):
            csv_path = risk_folder / f"environmental_risks_{pos}.csv"
            if not csv_path.exists(): continue
            df_risk = pd.read_csv(csv_path)
            for _, r in df_risk.iterrows():
                coords = r.get('Coordinates')
                if pd.isnull(coords) or coords=='None': continue
                popup_html = f"<div style='font-size:12px;max-width:300px'><b>Region:</b> {r.get('Region Name','Unknown')}<br><b>Risk Info:</b> {r.get('Water Risk Details','N/A')}</div>"
                try:
                    y, x = ast.literal_eval(coords)
                except:
                    continue
                if show_kba_only and r.get('Type of Protected Area')!='KBA':
                    continue
                if r.get('Type of Protected Area')=='KBA':
                    poly = r.get('Polygon')
                    if isinstance(poly, str) and poly!='N/A':
                        try:
                            geom = shapely.geometry.shape(ast.literal_eval(poly))
                            folium.GeoJson(data=geom.__geo_interface__, style_function=lambda feat: {"fillColor":"blue","color":"black","weight":1,"fillOpacity":0.3}, tooltip=popup_html).add_to(m)
                            continue
                        except:
                            pass
                folium.Marker(location=[y, x], icon=folium.Icon(color='darkred', icon='exclamation-sign'), popup=popup_html).add_to(m)
    # -------------------------------------------------------------------
    # Wind Turbine Layer (from KML)
    # -------------------------------------------------------------------
    try:
        # adjust this path if needed
        wind_kml = data_folder / 'MOH_Wind_map.kml'
        wind_gdf = gpd.read_file(wind_kml, driver='KML')
        folium.GeoJson(
            wind_gdf,
            name='Wind Turbines',
            style_function=lambda feat: {
                'color': 'black',
                'fillColor': 'white',
                'weight': 1,
                'fillOpacity': 0.6
            },
            tooltip=folium.GeoJsonTooltip(fields=[wind_gdf.columns[0]] 
                                          if len(wind_gdf.columns)>0 else None,
                                          aliases=['Turbine'] )
        ).add_to(m)
    except Exception as e:
        st.error(f"Could not load wind‐turbine KML: {e}")

    # Finally add a layer control so the user can toggle Wind Turbines on/off
    folium.LayerControl().add_to(m)
    
    return m


# === PAGE LAYOUT ===
st.title("Stanlow Biodiversity & Environmental Risk Viewer")
st.markdown("This dashboard visualizes biodiversity richness, land cover, and environmental risks around the Stanlow Refinery.")

left_col, center_col, right_col = st.columns([2,3,2])

with left_col:
    st.subheader("Pressures")
    with st.expander("Invasive Species Detected", expanded=False):
        invasive_species = set()
        for pos in positions:
            sp_path = data_folder / f"species_iucn_gbif_results_{pos}.csv"
            if not sp_path.exists(): continue
            df_sp = pd.read_csv(sp_path)
            names = df_sp['Species Name'].dropna().unique()
            invasive_species |= {n for n in names if n in invasive_species_europe}
        st.markdown(f"**Count:** {len(invasive_species)}")
        st.markdown("<div style='max-height:180px;overflow-y:auto'>"
                    + "<br>".join(sorted(invasive_species)) +
                    "</div>", unsafe_allow_html=True)
    with st.expander("Impactful Activities Growth & Thresholds", expanded=False):
        st.markdown("#### Impactful Activities Growth")
        years_available = [2001,2007,2012,2018]
        y1 = st.selectbox("Baseline year", years_available, index=0, key="growth_y1")
        y2 = st.selectbox("Comparison year", years_available, index=3, key="growth_y2")
        if y2 <= y1:
            st.warning("Pick a later comparison year.")
        else:
            file1 = data_folder / f"export_land_cover_polygons_Motor_oil_landcov_{y1}.geojson"
            file2 = data_folder / f"export_land_cover_polygons_Motor_oil_landcov_{y2}.geojson"
            if file1.exists() and file2.exists():
                gdf1, gdf2 = gpd.read_file(file1).to_crs(epsg=3857), gpd.read_file(file2).to_crs(epsg=3857)
                for gdf in (gdf1,gdf2): gdf["area_ha"] = gdf.geometry.area/10_000
                def human_label(gdf):
                    if "Class Name" in gdf.columns: return gdf["Class Name"]
                    elif "label" in gdf.columns:
                        return gdf["label"].astype(int).map(lambda c: land_cover_dict.get(c,f"Unknown ({c})"))
                    else:
                        st.warning("No 'Class Name' or 'label' in land‐cover data.")
                        return pd.Series(["Unknown"]*len(gdf), index=gdf.index)
                keywords = ["Refinery","Petrochemical","Industrial","Port","Airport",
                            "Landfill","Factory","Mining","Construction","Military"]
                def filter_imp(gdf):
                    names = human_label(gdf).str.lower()
                    mask = names.str.contains("|".join(kw.lower() for kw in keywords), na=False)
                    out = gdf[mask].copy(); out["Activity"] = human_label(gdf)[mask].values
                    return out
                imp1, imp2 = filter_imp(gdf1), filter_imp(gdf2)
                sum1 = imp1.groupby("Activity")["area_ha"].sum().rename(f"{y1} ha")
                sum2 = imp2.groupby("Activity")["area_ha"].sum().rename(f"{y2} ha")
                dfg = pd.concat([sum1,sum2],axis=1).fillna(0)
                dfg["Growth (ha)"] = dfg[f"{y2} ha"] - dfg[f"{y1} ha"]
                dfg["% change"] = (dfg["Growth (ha)"]/dfg[f"{y1} ha"].replace(0,np.nan)*100).fillna(0)
                dfg = dfg.reset_index().rename(columns={"index":"Activity"})
                dfg = dfg[dfg["Activity"].str.lower()!="sport and leisure"]
                st.dataframe(
                    dfg.style.format({f"{y1} ha":"{:.1f}", f"{y2} ha":"{:.1f}",
                                      "Growth (ha)":"{:.1f}","% change":"{:+.1f}%"}),
                    height=250
                )
            else:
                st.error(f"Missing GeoJSON for {y1} or {y2}.")

with center_col:
    st.subheader("Ecosystem Health")
    with st.expander("Map & Layer Controls", expanded=True):
        # Overlay selection
        layers = st.multiselect(
            "Choose overlays:",
            ["Species Richness", "Environmental Risks", "Land Cover"],
            default=["Species Richness", "Environmental Risks", "Land Cover"]
        )
        show_richness  = "Species Richness"  in layers
        show_risks     = "Environmental Risks" in layers
        show_landcover = "Land Cover"        in layers

        # Build and display map in its own container
        m = build_map(show_richness, show_risks, show_landcover)
        # finally render the map
        st_folium(m, width=700, height=600)

    with st.expander("Biometric Evolution Over Time", expanded=False):
        view_option = st.selectbox(
            "View under map:",
            ["Biometric Evolution Over Time","Additional Data Table"]
        )
        if view_option == "Biometric Evolution Over Time":
            metrics = ["Alpha","Gamma","Beta","Total_Mod_Beta","Richness","Similarity","Evenness","EvenxRichness"]
            sel_metrics = st.multiselect("Select metrics:", metrics, default=[metrics[0]])
            sel_positions = st.multiselect("Select grid positions:", positions, default=["center"])
            df_list = []
            for pos in sel_positions:
                path = data_folder / f"processed_species_iucn_gbif_results_{pos}.csv"
                if path.exists():
                    df_pos = pd.read_csv(path)
                    if "Year" in df_pos.columns:
                        cols = [m for m in sel_metrics if m in df_pos.columns]
                        if cols:
                            df = df_pos[["Year"]+cols].dropna()
                            df_m = df.melt(id_vars=["Year"], value_vars=cols, var_name="Metric", value_name="Value")
                            df_m["Position"] = pos
                            df_list.append(df_m)
            if df_list:
                df_all = pd.concat(df_list, ignore_index=True)
                fig = px.line(df_all, x="Year", y="Value",
                              color="Metric", line_dash="Position",
                              markers=True, title="Biometric Metrics Over Time")
                fig.update_layout(height=400)
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("No data available.")
        else:
            st.markdown("### Additional Data Table")
            file_map = {
                "High Integrity":"high_integrity.csv",
                "Rapid Decline":"rapid_decline.csv",
                "Corridors":"corridors_2018.csv"
            }
            table_option = st.selectbox("Choose data to display:", list(file_map))
            sel_file = data_folder / file_map[table_option]
            if sel_file.exists():
                try:
                    df_table = pd.read_csv(sel_file)
                    st.dataframe(df_table)
                except Exception as e:
                    st.warning(f"Could not load data: {e}")
            else:
                st.info(f"No data file for {table_option}")

with right_col:
    st.subheader("Risks")
    with st.expander("Threatened Species", expanded=True):
        at_risk_species = set()
        for pos in positions:
            csv_path = data_folder / f"species_iucn_gbif_results_{pos}.csv"
            if not csv_path.exists(): continue
            df_sp = pd.read_csv(csv_path)
            if "Year" in df_sp.columns:
                df_sp = df_sp[df_sp["Year"]==2024]
            if "Red List Category" in df_sp.columns and "Species Name" in df_sp.columns:
                mask = df_sp["Red List Category"].isin(
                    ["Critically Endangered","Endangered","Vulnerable"]
                )
                at_risk_species |= set(df_sp.loc[mask, "Species Name"].dropna())
        st.markdown(f"**Count:** {len(at_risk_species)}")
        st.markdown("<div style='max-height:180px;overflow-y:auto'>"
                    + "<br>".join(sorted(at_risk_species)) +
                    "</div>", unsafe_allow_html=True)
    with st.expander("Physical Environmental Risks", expanded=False):
        water_csv = data_folder / "water_risk_details.csv"
        if water_csv.exists():
            try:
                df_water = pd.read_csv(water_csv)
                if not df_water.empty:
                    st.dataframe(df_water)
                else:
                    st.write("No high‑risk water entries.")
            except Exception as e:
                st.error(f"Error loading: {e}")
        else:
            st.warning("water_risk_details.csv not found.")
    with st.expander("Download Full Report", expanded=False):
        report_path = data_folder / 'biodiversity_impact_report_101-5.docx'
        if report_path.exists():
            with open(report_path, 'rb') as f:
                report_bytes = f.read()
            st.download_button(
                label="Download Word report",
                data=report_bytes,
                file_name="biodiversity_impact_report_101-5.docx",
                mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                key="Generate_report"
            )
        else:
            st.error("Report file not found.")
