import streamlit as st
import streamlit as st
from pathlib import Path
from PIL import Image 

st.set_page_config(page_title="My Multi‑Dashboards", layout="centered")
st.title("Welcome to the Biomet.life Demo")
st.write(
    """
    Use the sidebar (►) to navigate between:

    1. Paris Risk Viewer  
    2. Stanlow Biodiversity & Environmental Risk Viewer  
    3. Fire Readiness Scenario Viewer
    """
)
# Add chatbot call-to-action
st.write(
    "💬 For a **tailored analysis**, check out our chatbot: "
    "[Biomet Chatbot](https://biomet-webapp.azurewebsites.net/)"
)

# load & display your logo
BASE_DIR = Path(__file__).parent
logo_path = BASE_DIR / "Biomet Logo.png"
logo = Image.open(logo_path)
st.image(logo, width=700)  # adjust width as needed
