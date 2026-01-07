#!/usr/bin/env python3
"""
Streamlit interface for ski resort rankings.

Run with: streamlit run streamlit_app.py
"""

import json
from pathlib import Path

import streamlit as st

from utils import calc_averages

RESULTS_FILE = Path(__file__).parent / ".analysis_results.json"


def load_results():
    """Load analysis results from JSON file."""
    if not RESULTS_FILE.exists():
        raise FileNotFoundError(f"No analysis results found. Run `python resort_analyzer.py` first.")
    with open(RESULTS_FILE) as f:
        return json.load(f)


def get_resort_averages(resort):
    """Calculate averages for a resort from camera ratings."""
    cameras = [c for c in resort.get("cameras", []) if c.get("rating")]
    if not cameras:
        raise ValueError(f"No ratings found for resort: {resort.get('resort_name', 'unknown')}")

    # Extract category ratings (nested) plus confidence from each
    ratings = []
    for c in cameras:
        rating = c["rating"]
        rating_dict = rating.get("categories", {}).copy()
        rating_dict["confidence"] = rating.get("confidence")
        ratings.append(rating_dict)

    return calc_averages(ratings)


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
    avg = get_resort_averages(resort)

    # Resort header with ranking
    st.markdown("---")
    medal = {1: "🥇", 2: "🥈", 3: "🥉"}.get(rank, f"#{rank}")
    st.title(f"{medal} {resort['resort_name']}")

    # Overall scores
    st.subheader("Overall Scores")

    # Display composite first, then all other categories dynamically
    display_fields = [("Composite", avg.get("composite", 0))]
    for key, value in avg.items():
        if key not in ("composite", "snow_depth_inches") and isinstance(value, (int, float)):
            label = key.replace("_", " ").title()
            display_fields.append((label, value))

    score_cols = st.columns(len(display_fields))
    for i, (label, value) in enumerate(display_fields):
        with score_cols[i]:
            st.metric(label, f"{value:.1f}/10")

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
                    categories = rating.get("categories", {})

                    # Build list of metrics to display
                    metrics = []
                    for key, value in categories.items():
                        if value is not None:
                            if key == "snow_depth_inches":
                                metrics.append((key.replace("_", " ").title(), f"{value}\""))
                            else:
                                label = key.replace("_", " ").title()
                                metrics.append((label, f"{value}/10"))

                    # Display metrics dynamically
                    if metrics:
                        cols = st.columns(len(metrics))
                        for i, (label, value) in enumerate(metrics):
                            cols[i].metric(label, value)

                    confidence = rating.get("confidence", 0)
                    conf_indicator = "🟢" if confidence >= 6 else "🔴"
                    st.caption(f"{conf_indicator} Confidence: {confidence}/10 — _{rating.get('notes', '')}_")
                elif cam.get("error"):
                    st.error(f"Analysis failed: {cam['error']}")

            st.markdown("---")

    # Quick navigation at bottom
    st.markdown("### Quick Navigation")
    resort_options = [f"#{i+1} {r['resort_name']} ({get_resort_averages(r)['composite']:.1f})" for i, r in enumerate(resorts)]
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
