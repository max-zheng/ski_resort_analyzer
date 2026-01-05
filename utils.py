"""Shared utilities for ski resort analysis."""

# Weights for composite score calculation
WEIGHTS = {
    "crowdedness": 0.15,
    "snow_quality": 0.40,
    "visibility": 0.20,
    "weather": 0.25,
}


def calc_composite(crowdedness: float, snow_quality: float, visibility: float, weather: float) -> float:
    """Calculate composite score from individual ratings."""
    return (
        crowdedness * WEIGHTS["crowdedness"] +
        snow_quality * WEIGHTS["snow_quality"] +
        visibility * WEIGHTS["visibility"] +
        weather * WEIGHTS["weather"]
    )
