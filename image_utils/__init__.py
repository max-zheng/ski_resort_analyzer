"""
Image utilities for fetching webcam images.

Provides reusable functions for:
- Extracting frames from video streams (ffmpeg)
- Downloading images directly to base64
"""

from .frame_extractor import extract_frame
from .image_downloader import download_image

__all__ = ["extract_frame", "download_image"]
