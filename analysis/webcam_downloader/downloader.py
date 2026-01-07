"""
Main webcam downloader class.
"""

from dataclasses import dataclass
from typing import Optional

from .config import (
    RESORTS,
    Camera,
    Resort,
    get_all_cameras,
)
from .providers import get_provider


@dataclass
class ImageInfo:
    """Info for a single image."""
    resort: Resort
    camera: Camera
    url: str  # Image URL or base64 data (if is_base64=True)
    is_base64: bool = False  # True if url contains base64 data instead of URL
    url_expiry_minutes: Optional[int] = None  # None = permanent, otherwise minutes until expiry


class WebcamDownloader:
    """
    Returns webcam image URLs for ski resorts.
    """

    def get_camera_url(self, resort_key: str, camera_id: str) -> ImageInfo:
        """
        Get the URL for a single camera.

        Args:
            resort_key: Key from RESORTS dict (e.g., "stevens_pass")
            camera_id: Camera ID

        Returns:
            ImageInfo with URL
        """
        if resort_key not in RESORTS:
            raise ValueError(f"Unknown resort: {resort_key}")

        resort = RESORTS[resort_key]
        camera = next((c for c in resort.cameras if c.id == camera_id), None)

        if camera is None:
            raise ValueError(f"Unknown camera: {camera_id} for resort {resort_key}")

        provider = get_provider(camera.provider)
        url = provider.get_image_url(camera.id)

        return ImageInfo(
            resort=resort,
            camera=camera,
            url=url,
            is_base64=provider.returns_base64,
            url_expiry_minutes=provider.url_expiry_minutes,
        )

    def get_resort_urls(self, resort_key: str) -> list[ImageInfo]:
        """
        Get URLs for all enabled cameras at a resort.

        Args:
            resort_key: Key from RESORTS dict

        Returns:
            List of ImageInfo with URLs
        """
        if resort_key not in RESORTS:
            raise ValueError(f"Unknown resort: {resort_key}")

        resort = RESORTS[resort_key]
        cameras = resort.cameras

        results = []
        for camera in cameras:
            provider = get_provider(camera.provider)
            try:
                url = provider.get_image_url(camera.id)
            except Exception as e:
                print(f"    ⚠ Skipping {camera.name}: {e}")
                continue

            results.append(ImageInfo(
                resort=resort,
                camera=camera,
                url=url,
                is_base64=provider.returns_base64,
                url_expiry_minutes=provider.url_expiry_minutes,
            ))

        return results

    def get_all_urls(self) -> list[ImageInfo]:
        """
        Get URLs for all cameras across all resorts.

        Returns:
            List of ImageInfo with URLs
        """
        results = []
        for resort, camera in get_all_cameras():
            provider = get_provider(camera.provider)
            try:
                url = provider.get_image_url(camera.id)
            except Exception as e:
                print(f"    ⚠ Skipping {camera.name}: {e}")
                continue

            results.append(ImageInfo(
                resort=resort,
                camera=camera,
                url=url,
                is_base64=provider.returns_base64,
                url_expiry_minutes=provider.url_expiry_minutes,
            ))
        return results

    def list_resorts(self) -> dict[str, Resort]:
        """List available resorts."""
        return RESORTS

    def list_cameras(self, resort_key: str) -> list[Camera]:
        """List cameras for a resort."""
        if resort_key not in RESORTS:
            raise ValueError(f"Unknown resort: {resort_key}")
        return RESORTS[resort_key].cameras
