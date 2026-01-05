#!/usr/bin/env python3
"""
Streamlit interface for ski resort rankings.

Run with: streamlit run streamlit_app.py
"""

import json
from pathlib import Path

import streamlit as st

from utils import calc_composite

RESULTS_FILE = Path(__file__).parent / ".analysis_results.json"


def load_results():
    """Load analysis results from JSON file."""
    if not RESULTS_FILE.exists():
        raise FileNotFoundError(f"No analysis results found. Run `python resort_analyzer.py` first.")
    with open(RESULTS_FILE) as f:
        return json.load(f)


def calc_averages(resort):
    """Calculate average scores from camera ratings."""
    ratings = [c["rating"] for c in resort.get("cameras", []) if c.get("rating")]
    if not ratings:
        raise ValueError(f"No ratings found for resort: {resort.get('resort_name', 'unknown')}")

    n = len(ratings)
    avg = {
        "crowdedness": sum(r["crowdedness"] for r in ratings) / n,
        "snow_quality": sum(r["snow_quality"] for r in ratings) / n,
        "visibility": sum(r["visibility"] for r in ratings) / n,
        "weather": sum(r["weather_conditions"] for r in ratings) / n,
    }
    avg["composite"] = calc_composite(
        avg["crowdedness"],
        avg["snow_quality"],
        avg["visibility"],
        avg["weather"],
    )
    return avg


def main():
    st.set_page_config(
        page_title="Ski Resort Rankings",
        page_icon="⛷️",
        layout="wide",
    )

    st.title("⛷️ Ski Resort Rankings")

    results = load_results()
    resorts = results["resorts"]

    if not resorts:
        st.warning("No resorts were analyzed.")
        return

    # Initialize session state for current resort index
    if "resort_idx" not in st.session_state:
        st.session_state.resort_idx = 0

    # Navigation header
    col1, col2, col3 = st.columns([1, 3, 1])

    with col1:
        if st.button("← Previous", disabled=st.session_state.resort_idx == 0):
            st.session_state.resort_idx -= 1
            st.rerun()

    with col2:
        st.markdown(
            f"<h3 style='text-align: center;'>Resort {st.session_state.resort_idx + 1} of {len(resorts)}</h3>",
            unsafe_allow_html=True,
        )

    with col3:
        if st.button("Next →", disabled=st.session_state.resort_idx >= len(resorts) - 1):
            st.session_state.resort_idx += 1
            st.rerun()

    # Current resort data
    resort = resorts[st.session_state.resort_idx]
    rank = st.session_state.resort_idx + 1
    avg = calc_averages(resort)

    # Resort header with ranking
    st.markdown("---")
    medal = {1: "🥇", 2: "🥈", 3: "🥉"}.get(rank, f"#{rank}")
    st.title(f"{medal} {resort['resort_name']}")

    # Overall scores
    st.subheader("Overall Scores")
    score_cols = st.columns(5)

    with score_cols[0]:
        st.metric("Composite", f"{avg['composite']:.1f}/10")
    with score_cols[1]:
        st.metric("Crowdedness", f"{avg['crowdedness']:.1f}/10", help="Higher = less crowded")
    with score_cols[2]:
        st.metric("Snow Quality", f"{avg['snow_quality']:.1f}/10")
    with score_cols[3]:
        st.metric("Visibility", f"{avg['visibility']:.1f}/10")
    with score_cols[4]:
        st.metric("Weather", f"{avg['weather']:.1f}/10")

    # Camera analyses
    st.markdown("---")
    st.subheader("Camera Analysis")

    cameras = resort.get("cameras", [])

    if not cameras:
        st.info("No camera data available for this resort.")
        return

    for cam in cameras:
        with st.container():
            img_col, ratings_col = st.columns([1, 1])

            with img_col:
                st.markdown(f"**📷 {cam['camera_name']}**")
                image_url = cam.get("image_url")
                if image_url:
                    if cam.get("is_base64"):
                        st.image(f"data:image/jpeg;base64,{image_url}", width=800)
                    else:
                        st.image(image_url, width=800)
                else:
                    st.info("Image not available")

            with ratings_col:
                rating = cam.get("rating")
                if rating:
                    r1, r2, r3, r4 = st.columns(4)
                    r1.metric("Crowd", f"{rating['crowdedness']}/10")
                    r2.metric("Snow", f"{rating['snow_quality']}/10")
                    r3.metric("Vis", f"{rating['visibility']}/10")
                    r4.metric("Weather", f"{rating['weather_conditions']}/10")
                    st.caption(f"_{rating.get('notes', '')}_")
                elif cam.get("error"):
                    st.error(f"Analysis failed: {cam['error']}")

            st.markdown("---")

    # Quick navigation at bottom
    st.markdown("### Quick Navigation")
    resort_options = [f"#{i+1} {r['resort_name']} ({calc_averages(r)['composite']:.1f})" for i, r in enumerate(resorts)]
    selected = st.selectbox(
        "Jump to resort:",
        options=range(len(resorts)),
        format_func=lambda i: resort_options[i],
        index=st.session_state.resort_idx,
    )
    if selected != st.session_state.resort_idx:
        st.session_state.resort_idx = selected
        st.rerun()


if __name__ == "__main__":
    main()
