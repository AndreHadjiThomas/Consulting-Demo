import streamlit as st


def show_diversity_metrics_page():
    """
    Streamlit page to describe biodiversity metrics
    """
    st.title("Biodiversity Metrics Overview")

    # Spatial Alpha Diversity
    st.header("Spatial Alpha Diversity")
    st.write(
        "**Definition:** Number of unique species observed at a given site during a specific time period Ti.\n"
        "\n**Purpose:** Indicates the abundance of species at the site for time Ti. "
        "A higher value over increasing Ti implies greater local diversity over time."
    )

    # Spatial Beta Diversity
    st.header("Spatial Beta Diversity")
    st.write(
        "**Definition:** Count of species unique to either time Ti or Ti-1 (but not both) across a site (region 5) and its neighbors, over years 2015–2023.\n"
        "\n**Purpose:** Measures species turnover between consecutive periods. "
        "A beta score near 0 indicates little divergence from the previous period."
    )

    # Spatial Gamma Diversity
    st.header("Spatial Gamma Diversity")
    st.write(
        "**Definition:** Total number of unique species observed at or before time Ti across a site (region 5) and its neighbors, for years 2015–2023.\n"
        "\n**Purpose:** Reflects cumulative diversity of the community. "
        "A growing value suggests an expanding ecosystem."
    )

    # Modified Beta Diversity
    st.header("Modified Beta Diversity")
    st.write(
        "**Definition:** Total count of unique species observed at or before time Ti across a site (region 5) and its neighbors, for years 2015–2023.\n"
        "\n**Purpose:** Captures lifetime diversity turnover. "
        "Increasing values indicate broader diversity accumulation."
    )

    # Biodiversity Evenness
    st.header("Biodiversity Evenness")
    st.write(
        "**Definition:** Measure of how evenly individuals are distributed among the species observed at or before time Ti in region 5 and neighbors (2015–2023).\n"
        "\n**Purpose:** Higher evenness indicates a more balanced ecosystem with no dominant species."
    )

    # Biodiversity Richness
    st.header("Biodiversity Richness")
    st.write(
        "**Definition:** Total number of distinct species observed at or before time Ti across region 5 and its neighbors (2015–2023).\n"
        "\n**Purpose:** Quantifies the overall species count; larger values denote richer communities."
    )

    # Biodiversity Similarity
    st.header("Biodiversity Similarity")
    st.write(
        "**Definition:** Proportion of species shared between region 5 and its neighbors at or before time Ti (2015–2023).\n"
        "\n**Purpose:** Indicates how similar the species composition is across neighboring sites. "
        "Higher values imply more homogeneous communities."
    )

    # Biodiversity Evenness x Richness
    st.header("Evenness × Richness")
    st.write(
        "**Definition:** Product of biodiversity evenness and richness metrics at time Ti for region 5 and neighbors (2015–2023).\n"
        "\n**Purpose:** Combines both balance and count into a single metric. "
        "Higher combined values reflect diverse and well-distributed ecosystems."
    )

    st.markdown("---")
    st.info(
        "These descriptions can be used as guidance for interpreting the biodiversity analytics displayed elsewhere in the dashboard."
    )


if __name__ == '__main__':
    show_diversity_metrics_page()
