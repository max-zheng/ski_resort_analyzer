#!/usr/bin/env python3
"""
Command-line interface for the webcam URL provider.

Usage:
    python -m webcam_downloader                    # Show all webcam URLs
    python -m webcam_downloader --resort stevens_pass
    python -m webcam_downloader --list-resorts
"""

import argparse
import sys

from .downloader import WebcamDownloader
from .config import RESORTS


def main():
    parser = argparse.ArgumentParser(
        description="Get webcam URLs from ski resorts",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    # Show all webcam URLs
    python -m webcam_downloader

    # Show URLs for specific resort
    python -m webcam_downloader --resort stevens_pass

    # List available resorts
    python -m webcam_downloader --list-resorts

    # List cameras for a resort
    python -m webcam_downloader --list-cameras stevens_pass
        """,
    )

    parser.add_argument(
        "--resort", "-r",
        help="Show URLs for this resort only (use key like 'stevens_pass')",
    )
    parser.add_argument(
        "--list-resorts",
        action="store_true",
        help="List available resorts and exit",
    )
    parser.add_argument(
        "--list-cameras",
        metavar="RESORT",
        help="List cameras for a resort and exit",
    )
    parser.add_argument(
        "--include-disabled",
        action="store_true",
        help="Include disabled resorts/cameras in listings",
    )

    args = parser.parse_args()

    downloader = WebcamDownloader()

    # Handle list commands
    if args.list_resorts:
        print("\nAvailable Resorts:")
        print("=" * 60)
        for key, resort in downloader.list_resorts(include_disabled=args.include_disabled).items():
            status = "enabled" if resort.enabled else "disabled"
            cam_count = len([c for c in resort.cameras if c.enabled])
            total_cams = len(resort.cameras)
            print(f"  {key}")
            print(f"    Name: {resort.name}")
            print(f"    Region: {resort.region}")
            print(f"    Cameras: {cam_count}/{total_cams} enabled")
            print(f"    Status: {status}")
            print()
        return 0

    if args.list_cameras:
        resort_key = args.list_cameras
        if resort_key not in RESORTS:
            print(f"Error: Unknown resort '{resort_key}'")
            print(f"Available: {', '.join(RESORTS.keys())}")
            return 1

        resort = RESORTS[resort_key]
        print(f"\nCameras for {resort.name}:")
        print("=" * 60)
        for cam in downloader.list_cameras(resort_key, include_disabled=args.include_disabled):
            status = "enabled" if cam.enabled else "disabled"
            print(f"  {cam.id}")
            print(f"    Name: {cam.name}")
            print(f"    Provider: {cam.provider}")
            print(f"    Status: {status}")
            print()
        return 0

    # Show webcam URLs
    if args.resort:
        if args.resort not in RESORTS:
            print(f"Error: Unknown resort '{args.resort}'")
            print(f"Available: {', '.join(RESORTS.keys())}")
            return 1
        camera_infos = downloader.get_resort_urls(args.resort)
        print(f"\nWebcam URLs for {RESORTS[args.resort].name}:")
    else:
        camera_infos = downloader.get_all_urls()
        print("\nAll Webcam URLs:")

    print("=" * 60)
    for cam_info in camera_infos:
        print(f"\n{cam_info.resort.name} / {cam_info.camera.name}")
        print(f"  {cam_info.url}")

    print(f"\nTotal: {len(camera_infos)} cameras")
    return 0


if __name__ == "__main__":
    sys.exit(main())
