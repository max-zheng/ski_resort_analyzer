"""AWS Lambda handler for ski resort analysis."""

import os
from datetime import datetime, timezone

from resort_analyzer import ResortAnalyzer


def handler(event, context):
    bucket = os.environ["S3_BUCKET"]
    key = os.environ["S3_KEY"]

    print(f"Starting analysis at {datetime.now(timezone.utc).isoformat()}")
    print(f"Target: s3://{bucket}/{key}")

    # Run analysis
    analyzer = ResortAnalyzer()
    print("Analyzing all resorts...")
    summaries = analyzer.analyze_all_resorts()

    # Save to S3
    s3_path = analyzer.save_results_to_s3(summaries, bucket, key)
    print(f"Results saved to {s3_path}")

    # Return summary
    return {
        "statusCode": 200,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "resorts_analyzed": len(summaries),
        "s3_path": s3_path,
        "top_resort": summaries[0].resort_name if summaries else None,
        "top_score": round(summaries[0].composite_score, 1) if summaries else None,
    }
