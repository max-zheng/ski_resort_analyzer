#!/usr/bin/env python3
"""
Ski Resort Analyzer

Analyzes webcam images using Perceptron AI to rank resorts
based on current conditions (crowdedness, snow quality, etc.)
"""

import base64
import json
import os
import time
from concurrent.futures import ThreadPoolExecutor, as_completed

from dotenv import load_dotenv
load_dotenv()
from dataclasses import dataclass, field
from typing import Optional, Union

from webcam_downloader.config import CameraType

import perceptron
from perceptron import image, perceive, pydantic_format, text
from pydantic import BaseModel, Field

from webcam_downloader import WebcamDownloader, ImageInfo
from utils import calc_averages



# =============================================================================
# STRUCTURED OUTPUT SCHEMA
# =============================================================================

class CategoryRatings(BaseModel):
    """Nested category ratings."""

    snow_quality: int = Field(ge=1, le=10)
    visibility: int = Field(ge=1, le=10)
    weather_conditions: int = Field(ge=1, le=10)
    activity: int = Field(ge=1, le=10)


class SkiConditionsRating(BaseModel):
    """Rating schema for ski resort webcam analysis."""

    confidence: int = Field(ge=1, le=10)
    notes: str = Field(description="Brief observation (1-2 sentences)")
    categories: CategoryRatings


# =============================================================================
# ANALYSIS FUNCTIONS
# =============================================================================

PROMPT = """Analyze this ski resort webcam image and respond with JSON.

Be decisive and honest. Avoid defaulting to safe middle scores (5-6). Use the full 1-10 range based on what you actually see.

Rating guide (1-10 scale):
- snow_quality: 1-2 = bare/icy, 3-4 = thin/crusty, 5-6 = average groomed, 7-8 = good coverage, 9-10 = fresh powder
- visibility: 1-2 = whiteout/can't see, 3-4 = foggy/poor, 5-6 = hazy, 7-8 = mostly clear, 9-10 = crystal clear
- weather_conditions: 1-2 = storm/rain, 3-4 = heavy snow, 5-6 = overcast, 7-8 = partly sunny, 9-10 = blue sky sunny
- activity: 1-2 = dead/overcrowded, 3-4 = very quiet/busy, 5-6 = moderate, 7-8 = good energy, 9-10 = perfect crowd level

- confidence: 1-2 = can barely see anything, 3-4 = very blurry/dark, 5-6 = somewhat unclear, 7-8 = mostly clear image, 9-10 = crystal clear sharp image

If conditions are clearly good, rate them high. If conditions are clearly bad, rate them low."""


@perceive(model="isaac-0.2-2b-preview", max_tokens=256, response_format=pydantic_format(SkiConditionsRating))
def analyze_webcam_image(image_source: Union[str, bytes], prompt: str):
    """Analyze a ski resort webcam image and return structured ratings.

    Args:
        image_source: Either a URL string or raw image bytes
        prompt: The analysis prompt to use
    """
    return image(image_source) + text(prompt)


def parse_rating_response(response_text: str) -> SkiConditionsRating:
    """Parse the model response into a SkiConditionsRating object."""
    return SkiConditionsRating.model_validate_json(response_text.strip())


@dataclass
class CameraAnalysis:
    """Analysis result for a single camera."""
    resort_name: str
    camera_name: str
    camera_type: CameraType = CameraType.OTHER
    rating: Optional[SkiConditionsRating] = None
    error: Optional[str] = None
    image_url: Optional[str] = None
    is_base64: bool = False


@dataclass
class ResortSummary:
    """Aggregated analysis for a resort."""
    resort_name: str
    resort_key: str
    camera_analyses: list[CameraAnalysis] = field(default_factory=list)
    averages: dict = field(default_factory=dict)
    composite_score: float = 0.0

    def calculate_averages(self):
        """Calculate average scores from all camera analyses."""
        successful = [a for a in self.camera_analyses if a.rating is not None]
        if not successful:
            return

        # Extract category ratings (nested) plus confidence from each
        ratings = []
        for a in successful:
            rating_dict = a.rating.categories.model_dump()
            rating_dict["confidence"] = a.rating.confidence
            ratings.append(rating_dict)

        self.averages = calc_averages(ratings)
        self.composite_score = self.averages.pop("composite", 0)


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

    def analyze_camera(self, camera_info: ImageInfo, max_retries: int = 3) -> CameraAnalysis:
        """Analyze a single camera by its URL or base64 data with retry logic."""
        analysis = CameraAnalysis(
            resort_name=camera_info.resort.name,
            camera_name=camera_info.camera.name,
            camera_type=camera_info.camera.type,
            image_url=camera_info.url,
            is_base64=camera_info.is_base64,
        )

        last_error = None
        for attempt in range(max_retries):
            try:
                # Handle base64 data vs URL
                if camera_info.is_base64:
                    image_data = base64.b64decode(camera_info.url)
                    result = analyze_webcam_image(image_data, PROMPT)
                else:
                    result = analyze_webcam_image(camera_info.url, PROMPT)
                analysis.rating = parse_rating_response(result.text)
                return analysis  # Success, return immediately
            except Exception as e:
                last_error = e
                if attempt < max_retries - 1:
                    time.sleep(1)  # Brief delay before retry

        # All retries failed
        analysis.error = str(last_error)
        return analysis

    def analyze_resort(self, resort_key: str) -> ResortSummary:
        """
        Analyze all cameras for a single resort.

        Args:
            resort_key: Resort key (e.g., "stevens_pass")

        Returns:
            ResortSummary with averaged scores
        """
        # Get webcam URLs (skip snow stake cameras)
        camera_infos = [
            c for c in self.downloader.get_resort_urls(resort_key)
            if c.camera.type != CameraType.SNOW_STAKE
        ]

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
            for field, value in summary.averages.items():
                if field != "snow_depth_inches":
                    print(f"   ├── {field}: {value:.1f}/10")

            # Print individual camera notes
            for analysis in summary.camera_analyses:
                if analysis.rating:
                    print(f"\n   📷 {analysis.camera_name}: {analysis.rating.notes}")

        print("\n" + "=" * 70)
        if summaries:
            best = summaries[0]
            print(f"🏆 RECOMMENDATION: {best.resort_name} (Score: {best.composite_score:.1f}/10)")
        print("=" * 70)

    @staticmethod
    def _rating_to_dict(rating: SkiConditionsRating) -> dict:
        """Convert a rating to a dictionary, excluding None values."""
        categories = {
            k: v for k, v in rating.categories.model_dump().items() if v is not None
        }

        return {
            "confidence": rating.confidence,
            "notes": rating.notes,
            "categories": categories,
        }

    @staticmethod
    def results_to_dict(summaries: list[ResortSummary]) -> dict:
        """Convert results to a dictionary for JSON serialization."""
        from datetime import datetime, timezone

        return {
            "updated_at": datetime.now(timezone.utc).isoformat(),
            "resorts": [
                {
                    "resort_name": s.resort_name,
                    "resort_key": s.resort_key,
                    "cameras": [
                        {
                            "camera_name": a.camera_name,
                            "camera_type": a.camera_type.value,
                            "image_url": a.image_url,
                            "is_base64": a.is_base64,
                            "rating": ResortAnalyzer._rating_to_dict(a.rating) if a.rating else None,
                            "error": a.error,
                        }
                        for a in s.camera_analyses
                    ],
                }
                for s in summaries
            ]
        }

    @staticmethod
    def save_results(summaries: list[ResortSummary], filepath: str = None):
        """Save analysis results to local JSON file."""
        from pathlib import Path

        if filepath is None:
            filepath = Path(__file__).parent / ".analysis_results.json"

        data = ResortAnalyzer.results_to_dict(summaries)

        with open(filepath, "w") as f:
            json.dump(data, f, indent=2)

        return filepath

    @staticmethod
    def save_results_to_s3(summaries: list[ResortSummary], bucket: str, key: str = "analysis_results.json"):
        """Save analysis results to S3."""
        import boto3

        data = ResortAnalyzer.results_to_dict(summaries)

        s3 = boto3.client("s3")
        s3.put_object(
            Bucket=bucket,
            Key=key,
            Body=json.dumps(data, indent=2),
            ContentType="application/json",
        )

        return f"s3://{bucket}/{key}"


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
        summaries = [summary]
    else:
        summaries = analyzer.analyze_all_resorts()

    analyzer.print_rankings(summaries)
    analyzer.save_results(summaries)

    return 0


if __name__ == "__main__":
    exit(main())
