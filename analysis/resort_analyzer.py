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


import perceptron
from perceptron import image, perceive, pydantic_format, text
from pydantic import BaseModel, Field

from webcam_downloader import WebcamDownloader, ImageInfo
from utils import calc_averages



# =============================================================================
# STRUCTURED OUTPUT SCHEMA
# =============================================================================

def create_rating_schema(categories: list[str]):
    """Dynamically create a Pydantic model with only the specified category fields."""
    from pydantic import create_model

    # Build category fields dynamically
    category_fields = {
        cat: (int, Field(ge=1, le=10))
        for cat in categories
    }

    DynamicCategories = create_model("DynamicCategories", **category_fields)

    DynamicRating = create_model(
        "DynamicRating",
        confidence=(int, Field(ge=1, le=10)),
        notes=(str, Field(description="Concise observation (1 sentence)")),
        categories=(DynamicCategories, ...),
    )

    return DynamicRating


# =============================================================================
# ANALYSIS FUNCTIONS
# =============================================================================

# Category descriptions for dynamic prompt building
CATEGORY_DESCRIPTIONS = {
    "snow_quality": "snow_quality: 1-2 = bare/icy, 3-4 = thin/crusty, 5-6 = average groomed, 7-8 = good coverage, 9-10 = fresh powder",
    "visibility": "visibility: 1-2 = whiteout/can't see, 3-4 = foggy/poor, 5-6 = hazy, 7-8 = mostly clear, 9-10 = crystal clear",
    "weather_conditions": "weather_conditions: 1-2 = storm/rain, 3-4 = heavy snow, 5-6 = overcast, 7-8 = partly sunny, 9-10 = blue sky sunny",
    "activity": "activity: 1-2 = empty/no movement, 3-4 = few people/quiet, 5-6 = moderate activity, 7-8 = busy/lively, 9-10 = bustling/energetic",
}


def build_prompt(categories: list[str]) -> str:
    """Build a dynamic prompt based on the categories to evaluate."""
    category_guides = "\n".join(f"- {CATEGORY_DESCRIPTIONS[cat]}" for cat in categories if cat in CATEGORY_DESCRIPTIONS)

    return f"""Analyze this ski resort webcam image and rate these categories: {", ".join(categories)}

Be decisive and honest. Avoid defaulting to safe middle scores (5-6). Use the full 1-10 range based on what you actually see.

Rating guide (1-10 scale):
{category_guides}

- confidence: 1-2 = can barely see anything, 3-4 = very blurry/dark, 5-6 = somewhat unclear, 7-8 = mostly clear image, 9-10 = crystal clear sharp image

If conditions are clearly good, rate them high. If conditions are clearly bad, rate them low."""


def analyze_webcam_image(image_source: Union[str, bytes], prompt: str, categories: list[str]) -> BaseModel:
    """Analyze a ski resort webcam image and return structured ratings.

    Args:
        image_source: Either a URL string or raw image bytes
        prompt: The analysis prompt to use
        categories: List of categories to evaluate (schema is built dynamically)

    Returns:
        Dynamic Pydantic model with confidence, notes, and categories fields
    """
    # Create dynamic schema with only the requested categories
    schema = create_rating_schema(categories)

    # Build the perceive function with dynamic schema
    @perceive(model="isaac-0.2-2b-preview", max_tokens=256, response_format=pydantic_format(schema))
    def _analyze(img, txt):
        return image(img) + text(txt)

    result = _analyze(image_source, prompt)
    return schema.model_validate_json(result.text.strip())


@dataclass
class CameraAnalysis:
    """Analysis result for a single camera."""
    resort_name: str
    camera_name: str
    rating: Optional[BaseModel] = None
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
            image_url=camera_info.url,
            is_base64=camera_info.is_base64,
        )

        # Build prompt based on camera's categories
        categories = camera_info.camera.get_category_names()
        prompt = build_prompt(categories)

        last_error = None
        for attempt in range(max_retries):
            try:
                # Handle base64 data vs URL
                if camera_info.is_base64:
                    image_data = base64.b64decode(camera_info.url)
                    rating = analyze_webcam_image(image_data, prompt, categories)
                else:
                    rating = analyze_webcam_image(camera_info.url, prompt, categories)
                analysis.rating = rating
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
        # Get all webcam URLs
        all_camera_infos = self.downloader.get_resort_urls(resort_key)

        resort_name = all_camera_infos[0].resort.name if all_camera_infos else resort_key
        summary = ResortSummary(resort_name=resort_name, resort_key=resort_key)

        # Analyze all cameras in parallel (each camera has its own category config)
        print(f"  Analyzing {len(all_camera_infos)} cameras in parallel...")
        with ThreadPoolExecutor() as executor:
            future_to_cam = {
                executor.submit(self.analyze_camera, cam_info): cam_info
                for cam_info in all_camera_infos
            }

            for future in as_completed(future_to_cam):
                cam_info = future_to_cam[future]
                analysis = future.result()
                summary.camera_analyses.append(analysis)

                if analysis.rating:
                    categories = cam_info.camera.get_category_names()
                    print(f"    ✓ {cam_info.camera.name} [{', '.join(categories)}]: {analysis.rating.notes}")
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
    def _rating_to_dict(rating: BaseModel) -> dict:
        """Convert a rating to a dictionary."""
        return {
            "confidence": rating.confidence,
            "notes": rating.notes,
            "categories": rating.categories.model_dump(),
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
