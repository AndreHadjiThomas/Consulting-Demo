
import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import plotly.express as px
import geopandas as gpd
import folium
import branca
from pathlib import Path
from shapely.geometry import box
from streamlit_folium import st_folium
import shap

st.set_page_config(
    page_title="Fire Readiness Scenario Viewer",
    page_icon="🔥",
    layout="wide",
)
# Add chatbot call-to-action
st.write(
    "For mor info on the fires in California check out this "
    "[page](https://en.wikipedia.org/wiki/List_of_California_wildfires)"
)

# === Top controls ===
st.title("Fire Readiness Scenario Viewer")
scenario = st.selectbox("Select scenario", ["LA fires (ROI)"])
generate = st.button("Generate Dashboard")

# Initialize flag
if "generated" not in st.session_state:
    st.session_state.generated = False
if generate:
    st.session_state.generated = True

if not st.session_state.generated:
    st.info("Please select a scenario and click **Generate Dashboard** to continue.")
    st.stop()

# === Helper functions ===
def create_la_grid(bounds, cell_size_deg, n_cells=110):
    feats, idx = [], 0
    lat = bounds["min_lat"]
    while lat < bounds["max_lat"] and idx < n_cells:
        lon = bounds["min_lon"]
        while lon < bounds["max_lon"] and idx < n_cells:
            feats.append({
                "cell_id": f"cell_{idx}",
                "geometry": box(lon, lat, lon+cell_size_deg, lat+cell_size_deg)
            })
            idx += 1
            lon += cell_size_deg
        lat += cell_size_deg
    gdf = gpd.GeoDataFrame(feats, geometry="geometry", crs="EPSG:4326")
    gdf["centroid"] = gdf.geometry.centroid
    gdf["lat_lon"] = gdf.centroid.apply(lambda p: f"{p.y:.4f}_{p.x:.4f}")
    return gdf

def make_colormap(vmin=0, vmax=100):
    return branca.colormap.LinearColormap(
        colors=["yellow","red"],
        index=[vmin, vmax],
        vmin=vmin, vmax=vmax
    )

# === Constants ===
LA_BOUNDS     = {"min_lon": -118.7, "max_lon": -118.0,
                 "min_lat":  34.0,  "max_lat":  34.5}
GRID_SIZE_DEG = 0.045
N_CELLS       = 110

positions = [
    "top_left", "top_center", "top_right",
    "left_center", "center", "right_center",
    "bottom_left", "bottom_center", "bottom_right"
]
# === Data loading ===
BASE_DIR   = Path(__file__).resolve().parent.parent 
DATA_DIR       = BASE_DIR / "LA"
@st.cache_data
def load_monthly():
    path = DATA_DIR / "LA_Fire_Readiness.csv"
    df = pd.read_csv(DATA_DIR / "LA_Fire_Readiness.csv", parse_dates=["Date"])
    return df.dropna(subset=["Date"])

@st.cache_data
def load_matrix():
    path = DATA_DIR / "Annual_Fire_Readiness.csv"
    return pd.read_csv(path, parse_dates=["Date"])

@st.cache_data
def load_shap():
    df = pd.read_csv(DATA_DIR / "shap_values_with_dates.csv")
    df["Date"] = pd.to_datetime(df["Date"])
    return df

@st.cache_data
def load_landcover():
    path = DATA_DIR/ "export_land_cover_polygonsLA.geojson"
    gdf = gpd.read_file(path)
    gdf = gdf[gdf["label"].notna()]
    gdf["label"] = gdf["label"].astype(int)
    return gdf

df_monthly = load_monthly()
df_matrix  = load_matrix()
shap_df    = load_shap()
gdf_lc     = load_landcover()

# Land cover styling
land_cover_dict = {
    1:'Evergreen needleleaf forest',2:'Evergreen broadleaf forest',
    3:'Deciduous needleleaf forest',4:'Deciduous broadleaf forest',
    5:'Mixed forest',6:'Wooded grassland',7:'Other wooded land',
    8:'Open shrubland',9:'Savanna',10:'Grassland',
    11:'Permanent wetlands',12:'Cropland',13:'Urban and built-up',
    14:'Cropland/natural vegetation mosaic',15:'Snow and ice',
    16:'Barren or sparsely vegetated',17:'Water',18:'Urban areas',
    19:'Cropland'
}
water_classes     = {11,17}
ecosystem_classes = set(range(1,11)) | {16}

# === Main dashboard ===
st.markdown("---")

left, center, right = st.columns([4,5,4])

# --- LEFT: time‐series & slider ---
with left:
    st.subheader("Time Filters & Trends")
    min_d = df_monthly["Date"].dt.date.min()
    max_d = df_monthly["Date"].dt.date.max()
    date_range = st.slider(
        "Date range:",
        min_value=min_d,
        max_value=max_d,
        value=(min_d, max_d)
    )
    df_f = df_monthly[
        (df_monthly["Date"].dt.date >= date_range[0]) &
        (df_monthly["Date"].dt.date <= date_range[1])
    ]

    # Fire Readiness
    if "Fire Readiness (%)" in df_f.columns:
        with st.expander("Fire Readiness Over Time", expanded=True):
            fig_fr = px.line(
                df_f, x="Date", y="Fire Readiness (%)", markers=True
            )
            fig_fr.update_layout(hovermode="x unified")
            st.plotly_chart(fig_fr, use_container_width=True)

    # Environmental Conditions
    env_cols = ["Avg Soil Moisture", "Avg Wind Speed", "Avg Precipitation"]
    valid_env = [c for c in env_cols if c in df_f.columns]
    if valid_env:
        with st.expander("Environmental Conditions", expanded=False):
            fig_env = px.line(
                df_f,
                x="Date",
                y=valid_env,
                markers=True,
                labels={col: col for col in valid_env}
            )
            fig_env.update_layout(hovermode="x unified")
            st.plotly_chart(fig_env, use_container_width=True)

    # Vegetation Count
    if "Vegetation Count" in df_f.columns:
        with st.expander("Vegetation Count Over Time", expanded=False):
            fig_vc = px.line(
                df_f,
                x="Date",
                y="Vegetation Count",
                markers=True,
                labels={"Vegetation Count": "Vegetation Count"}
            )
            fig_vc.update_layout(hovermode="x unified")
            st.plotly_chart(fig_vc, use_container_width=True)

    # Average Temperature
    if "Avg Temperature" in df_f.columns:
        with st.expander("Average Temperature Over Time", expanded=False):
            fig_temp = px.line(
                df_f,
                x="Date",
                y="Avg Temperature",
                markers=True,
                labels={"Avg Temperature": "Temperature (°C)"}
            )
            fig_temp.update_layout(hovermode="x unified")
            st.plotly_chart(fig_temp, use_container_width=True)


# — Center: Year/Month select & Map —
with center:
    st.subheader("Map: Fire Readiness & Land Cover")
    # Build year/month selectors
    avail = df_matrix["Date"].dt.to_period("M").drop_duplicates().dt.to_timestamp()
    years = sorted(avail.dt.year.unique())
    mons  = sorted(avail.dt.month.unique())
    mm    = {1:"January",2:"February",3:"March",4:"April",
             5:"May",6:"June",7:"July",8:"August",
             9:"September",10:"October",11:"November",12:"December"}
    month_names = [mm[m] for m in mons]

    sel_y = st.selectbox("Year", years, index=len(years)-1)
    idx   = mons.index(avail.dt.month.mode()[0])
    sel_m = st.selectbox("Month", month_names, index=idx)
    mnum  = mons[month_names.index(sel_m)]
    target = pd.to_datetime(f"{sel_y}-{mnum:02d}-01")

    # Create base map
    m = folium.Map(location=[34.0522,-118.2437],
                   zoom_start=11, tiles="CartoDB positron")

    # Land cover layer
    lc_fg = folium.FeatureGroup(name="Land Cover")
    for _, r in gdf_lc.iterrows():
        lbl = int(r["label"])
        col = ("blue" if lbl in water_classes
               else "green" if lbl in ecosystem_classes
               else "gray")
        folium.GeoJson(
            r["geometry"],
            style_function=lambda feat, col=col: {
                "fillColor": col,
                "color": "black",
                "weight": 0.3,
                "fillOpacity": 0.5
            },
            tooltip=land_cover_dict.get(lbl, "Unknown")
        ).add_to(lc_fg)
    lc_fg.add_to(m)

    # Fire Readiness grid layer
    fr_fg = folium.FeatureGroup(name="Fire Readiness")
    row = df_matrix[df_matrix["Date"] == target]
    if row.empty:
        st.warning(f"No readiness data for {target.date()}")
    else:
        vals = row.set_index("Date").iloc[0].to_dict()
        grid = create_la_grid(LA_BOUNDS, GRID_SIZE_DEG, n_cells=N_CELLS)
        grid["Readiness"] = grid["lat_lon"].map(vals)
        cmap = make_colormap(0,100)

        for _, r in grid.iterrows():
            if pd.notna(r.Readiness):
                folium.GeoJson(
                    r["geometry"],
                    style_function=lambda feat, c=cmap(r.Readiness): {
                        "fillColor": c,
                        "color": c,
                        "weight": 1,
                        "fillOpacity": 0.7
                    },
                    tooltip=f"{r.lat_lon}: {r.Readiness:.1f}%"
                ).add_to(fr_fg)

    fr_fg.add_to(m)
    folium.LayerControl(collapsed=False).add_to(m)
    st_folium(m, width=900, height=525)

# — Right: SHAP waterfall —
with right:
    st.subheader("Predictions Explainability")

   # SHAP waterfall code…
    sel_row = shap_df[shap_df["Date"] == target]
    if sel_row.empty:
        st.warning(f"No SHAP for {target.date()}")
    else:
        feats = [c for c in shap_df.columns if c not in ["Date","base_value"]]
        sv    = sel_row[feats].values[0]
        bv    = sel_row["base_value"].values[0]
        raw   = df_monthly[df_monthly["Date"] == target]
        present = [f for f in feats if f in df_monthly.columns]
        vals  = raw[present].iloc[0].values
        expl  = shap.Explanation(
            values=sv, base_values=bv,
            data=vals, feature_names=present
        )

        st.markdown(f"**SHAP for {target.strftime('%b %Y')}**")
        fig, ax = plt.subplots(figsize=(8,5))
        shap.plots.waterfall(expl, max_display=15, show=False)
        st.pyplot(fig)

        # — Threatened Species expander (now correctly indented) —
        with st.expander("**Threatened Species**", expanded=True):
            at_risk_species = set()
            for pos in positions:
                csv_path = Path(__file__).parent / f"species_iucn_gbif_results_{pos}.csv"
                if not csv_path.exists():
                    continue
                df_sp = pd.read_csv(csv_path)
                if "Year" in df_sp.columns:
                    df_sp = df_sp[df_sp["Year"] == 2024]
                if {"Red List Category","Species Name"}.issubset(df_sp.columns):
                    mask = df_sp["Red List Category"].isin(
                        ["Critically Endangered","Endangered","Vulnerable"]
                    )
                    at_risk_species |= set(df_sp.loc[mask, "Species Name"].dropna())

            st.markdown(f"**Count:** {len(at_risk_species)}")
            st.markdown(
                "<div style='max-height:180px;overflow-y:auto'>"
                + "<br>".join(sorted(at_risk_species))
                + "</div>",
                unsafe_allow_html=True
            )

