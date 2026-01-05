#!/usr/bin/env python3
"""
Ski Resort Analyzer

Analyzes webcam images using Perceptron AI to rank resorts
based on current conditions (crowdedness, snow quality, etc.)
"""

import base64
import json
import os
from concurrent.futures import ThreadPoolExecutor, as_completed

from dotenv import load_dotenv
load_dotenv()
from dataclasses import dataclass, field
from typing import Optional, Union

import perceptron
from perceptron import image, perceive, text
from pydantic import BaseModel, Field

from webcam_downloader import WebcamDownloader, ImageInfo



# =============================================================================
# STRUCTURED OUTPUT SCHEMA
# =============================================================================

class SkiConditionsRating(BaseModel):
    """Rating schema for ski resort webcam analysis."""

    crowdedness: int = Field(
        ge=1, le=10,
        description="1 = very crowded/busy, 10 = empty/no people visible"
    )
    snow_quality: int = Field(
        ge=1, le=10,
        description="1 = poor/icy/bare spots, 10 = fresh powder/excellent coverage"
    )
    visibility: int = Field(
        ge=1, le=10,
        description="1 = foggy/whiteout/poor, 10 = crystal clear/sunny"
    )
    weather_conditions: int = Field(
        ge=1, le=10,
        description="1 = stormy/heavy snow/rain, 10 = perfect sunny day"
    )

    notes: str = Field(
        description="Brief observation about current conditions (1-2 sentences)"
    )


# =============================================================================
# ANALYSIS FUNCTIONS
# =============================================================================

ANALYSIS_PROMPT = """Analyze this ski resort webcam image and rate the current conditions.

You MUST respond with ONLY valid JSON in this exact format:
{
    "crowdedness": <1-10>,
    "snow_quality": <1-10>,
    "visibility": <1-10>,
    "weather_conditions": <1-10>,
    "notes": "<brief observation>"
}

Rating guide:
- crowdedness: 1 = very crowded, 10 = empty/no people
- snow_quality: 1 = poor/icy/bare, 10 = fresh powder/excellent
- visibility: 1 = foggy/whiteout, 10 = crystal clear
- weather_conditions: 1 = stormy, 10 = perfect sunny

If nighttime/dark, rate based on visible snow coverage and note "nighttime" in notes.

Respond with JSON only, no other text."""


@perceive(model="isaac-0.1", max_tokens=1024)
def analyze_webcam_image(image_source: Union[str, bytes]):
    """Analyze a ski resort webcam image and return structured ratings.

    Args:
        image_source: Either a URL string or raw image bytes
    """
    return image(image_source) + text(ANALYSIS_PROMPT)


def parse_rating_response(response_text: str) -> SkiConditionsRating:
    """Parse the model response into a SkiConditionsRating object."""
    data = json.loads(response_text.strip())

    # Validate and clamp values to 1-10 range
    for key in ["crowdedness", "snow_quality", "visibility", "weather_conditions"]:
        if key in data:
            data[key] = max(1, min(10, int(data[key])))

    return SkiConditionsRating(**data)


@dataclass
class CameraAnalysis:
    """Analysis result for a single camera."""
    resort_name: str
    camera_name: str
    rating: Optional[SkiConditionsRating] = None
    error: Optional[str] = None


@dataclass
class ResortSummary:
    """Aggregated analysis for a resort."""
    resort_name: str
    resort_key: str
    camera_analyses: list[CameraAnalysis] = field(default_factory=list)

    # Averaged scores
    avg_crowdedness: float = 0.0
    avg_snow_quality: float = 0.0
    avg_visibility: float = 0.0
    avg_weather: float = 0.0

    # Final composite score
    composite_score: float = 0.0

    def calculate_averages(self):
        """Calculate average scores from all successful camera analyses."""
        successful = [a for a in self.camera_analyses if a.rating is not None]

        if not successful:
            return

        n = len(successful)
        self.avg_crowdedness = sum(a.rating.crowdedness for a in successful) / n
        self.avg_snow_quality = sum(a.rating.snow_quality for a in successful) / n
        self.avg_visibility = sum(a.rating.visibility for a in successful) / n
        self.avg_weather = sum(a.rating.weather_conditions for a in successful) / n

        # Weighted composite score
        self.composite_score = (
            self.avg_crowdedness * 0.15 +
            self.avg_snow_quality * 0.40 +
            self.avg_visibility * 0.20 +
            self.avg_weather * 0.25
        )


class ResortAnalyzer:
    """
    Analyzes ski resort webcams using Perceptron AI.

    Usage:
        analyzer = ResortAnalyzer()
        results = analyzer.analyze_all_resorts()
        analyzer.print_rankings(results)
    """

    def __init__(self):
        """
        Initialize the analyzer.
        """
        perceptron.configure(provider="perceptron", api_key=os.environ.get("PERCEPTRON_API_KEY"))
        self.downloader = WebcamDownloader()

    def analyze_camera(self, camera_info: ImageInfo) -> CameraAnalysis:
        """Analyze a single camera by its URL or base64 data."""
        analysis = CameraAnalysis(
            resort_name=camera_info.resort.name,
            camera_name=camera_info.camera.name,
        )

        try:
            # Handle base64 data vs URL
            if camera_info.is_base64:
                # Decode base64 to bytes for Perceptron
                image_data = base64.b64decode(camera_info.url)
                result = analyze_webcam_image(image_data)
            else:
                # Pass URL directly to model - no download needed!
                result = analyze_webcam_image(camera_info.url)
            analysis.rating = parse_rating_response(result.text)
        except Exception as e:
            analysis.error = str(e)

        return analysis

    def analyze_resort(self, resort_key: str) -> ResortSummary:
        """
        Analyze all cameras for a single resort.

        Args:
            resort_key: Resort key (e.g., "stevens_pass")

        Returns:
            ResortSummary with averaged scores
        """
        # Get webcam URLs
        camera_infos = self.downloader.get_resort_urls(resort_key)

        resort_name = camera_infos[0].resort.name if camera_infos else resort_key
        summary = ResortSummary(resort_name=resort_name, resort_key=resort_key)

        # Analyze cameras in parallel
        print(f"  Analyzing {len(camera_infos)} cameras in parallel...")
        with ThreadPoolExecutor() as executor:
            future_to_cam = {
                executor.submit(self.analyze_camera, cam_info): cam_info
                for cam_info in camera_infos
            }

            for future in as_completed(future_to_cam):
                cam_info = future_to_cam[future]
                analysis = future.result()
                summary.camera_analyses.append(analysis)

                if analysis.rating:
                    print(f"    ✓ {cam_info.camera.name}: {analysis.rating.notes}")
                else:
                    print(f"    ✗ {cam_info.camera.name}: {analysis.error}")

        # Calculate averages
        summary.calculate_averages()

        return summary

    def analyze_all_resorts(self) -> list[ResortSummary]:
        """
        Analyze all enabled resorts.

        Returns:
            List of ResortSummary sorted by composite score (best first)
        """
        summaries = []

        for resort_key in self.downloader.list_resorts().keys():
            print(f"\n{'='*50}")
            print(f"Analyzing {resort_key}...")
            print('='*50)

            summary = self.analyze_resort(resort_key)
            summaries.append(summary)

        # Sort by composite score (highest first)
        summaries.sort(key=lambda s: s.composite_score, reverse=True)

        return summaries

    @staticmethod
    def print_rankings(summaries: list[ResortSummary]):
        """Print a formatted ranking of resorts."""
        print("\n")
        print("=" * 70)
        print("SKI RESORT RANKINGS - CURRENT CONDITIONS")
        print("=" * 70)

        for i, summary in enumerate(summaries, 1):
            successful = len([a for a in summary.camera_analyses if a.rating])
            total = len(summary.camera_analyses)

            print(f"\n#{i} {summary.resort_name}")
            print(f"   Composite Score: {summary.composite_score:.1f}/10")
            print(f"   Cameras analyzed: {successful}/{total}")
            print(f"   ├── Crowdedness:  {summary.avg_crowdedness:.1f}/10 (higher = less crowded)")
            print(f"   ├── Snow Quality: {summary.avg_snow_quality:.1f}/10")
            print(f"   ├── Visibility:   {summary.avg_visibility:.1f}/10")
            print(f"   └── Weather:      {summary.avg_weather:.1f}/10")

            # Print individual camera notes
            for analysis in summary.camera_analyses:
                if analysis.rating:
                    print(f"\n   📷 {analysis.camera_name}: {analysis.rating.notes}")

        print("\n" + "=" * 70)
        if summaries:
            best = summaries[0]
            print(f"🏆 RECOMMENDATION: {best.resort_name} (Score: {best.composite_score:.1f}/10)")
        print("=" * 70)


# =============================================================================
# CLI
# =============================================================================

def main():
    import argparse

    parser = argparse.ArgumentParser(
        description="Analyze ski resort conditions using AI"
    )
    parser.add_argument(
        "--resort", "-r",
        help="Analyze only this resort (e.g., 'stevens_pass')"
    )

    args = parser.parse_args()
    analyzer = ResortAnalyzer()

    if args.resort:
        summary = analyzer.analyze_resort(args.resort)
        analyzer.print_rankings([summary])
    else:
        summaries = analyzer.analyze_all_resorts()
        analyzer.print_rankings(summaries)

    return 0


if __name__ == "__main__":
    exit(main())
