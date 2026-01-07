"""
Ski Resort Webcam URL Provider

Returns webcam image URLs for ski resorts.
"""

from .downloader import WebcamDownloader, ImageInfo
from .providers import get_provider
from .config import RESORTS, Resort, Camera

__all__ = [
    "WebcamDownloader",
    "ImageInfo",
    "get_provider",
    "RESORTS",
    "Resort",
    "Camera",
]
