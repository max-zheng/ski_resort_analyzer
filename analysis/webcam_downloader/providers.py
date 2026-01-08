"""
Webcam URL providers.

Each provider knows how to construct the URL for a webcam image.

URL Permanence:
- Permanent: URL pattern is static, can be cached/bookmarked
- Temporary: URL contains auth tokens that expire, must fetch fresh each time
"""

from abc import ABC, abstractmethod
from typing import Optional


class WebcamProvider(ABC):
    """Abstract base class for webcam providers."""

    name: str = "base"
    returns_base64: bool = False  # True if get_image_url returns base64 data
    url_expiry_minutes: Optional[int] = None  # None = permanent, otherwise minutes until expiry

    @abstractmethod
    def get_image_url(self, camera_id: str) -> str:
        """Get the direct URL for a still image (or base64 if returns_base64=True)."""
        pass


class BrownriceProvider(WebcamProvider):
    """
    Brownrice webcam hosting provider.

    Used by: Stevens Pass, White Pass, Whistler Blackcomb, and many Vail resorts.
    Uses universal snapshot URL that auto-resolves to correct server.
    URL is permanent - always returns current snapshot.
    """

    name = "brownrice"
    snapshot_url = "https://player.brownrice.com/snapshot"

    def get_image_url(self, camera_id: str) -> str:
        return f"{self.snapshot_url}/{camera_id}"


class YouTubeProvider(WebcamProvider):
    """
    YouTube livestream thumbnail provider.

    Used by: Summit at Snoqualmie, Mission Ridge

    Uses the stable i.ytimg.com URL pattern to get livestream thumbnails.
    URL is permanent - image updates every ~5 minutes.
    """

    name = "youtube"
    thumbnail_url = "https://i.ytimg.com/vi"

    def get_image_url(self, camera_id: str) -> str:
        return f"{self.thumbnail_url}/{camera_id}/maxresdefault_live.jpg"


class Ski49nProvider(WebcamProvider):
    """
    49 Degrees North self-hosted webcam provider.

    Used by: 49 Degrees North

    Downloads and returns base64 since the server blocks cloud IPs.
    URL is permanent but must be downloaded locally (cloud IPs blocked).
    """

    name = "ski49n"
    base_url = "https://www.ski49n.com/webcams"
    returns_base64 = True

    def get_image_url(self, camera_id: str) -> str:
        from image_utils import download_image

        url = f"{self.base_url}/{camera_id}.jpg"
        return download_image(url)


class WetMetProvider(WebcamProvider):
    """
    WetMet HLS video stream provider.

    Used by: Mt Hood Meadows

    Fetches HLS stream URL from widget page, then extracts a frame using ffmpeg.
    Returns base64-encoded JPEG image.

    URL is temporary - contains wmsAuthSign token valid for 30 minutes.
    """

    name = "wetmet"
    widget_url = "https://api.wetmet.net/widgets/stream/frame.php"
    returns_base64 = True
    url_expiry_minutes = 30

    def get_image_url(self, camera_id: str) -> str:
        import re
        import urllib.request

        from image_utils import extract_frame

        # Fetch the HLS stream URL from the widget page
        url = f"{self.widget_url}?uid={camera_id}"
        with urllib.request.urlopen(url, timeout=10) as response:
            html = response.read().decode("utf-8")

        # Extract the HLS URL from the JavaScript
        match = re.search(r"var vurl = '([^']+)'", html)
        if not match:
            raise ValueError(f"Could not find stream URL in WetMet widget: {camera_id}")

        stream_url = match.group(1)
        return extract_frame(stream_url)


class BigWhiteProvider(WebcamProvider):
    """
    Big White self-hosted webcam provider.

    Used by: Big White

    Scrapes the webcam page to get current image URLs (they may change over time).
    Returns base64-encoded images.
    """

    name = "bigwhite"
    webcam_page = "https://www.bigwhite.com/mountain-conditions/webcams"
    returns_base64 = True
    _url_cache: dict[str, str] = {}

    def _fetch_webcam_urls(self) -> dict[str, str]:
        """Fetch current webcam URLs from the Big White webcams page."""
        import re
        import urllib.request

        with urllib.request.urlopen(self.webcam_page, timeout=10) as response:
            html = response.read().decode("utf-8")

        # Extract image URLs like /sites/default/files/village_849.jpg
        pattern = r'/sites/default/files/(\w+)_\d+\.jpg'
        matches = re.findall(pattern, html)

        urls = {}
        for match in matches:
            # Find the full URL for this camera
            full_pattern = rf'/sites/default/files/({match}_\d+\.jpg)'
            full_match = re.search(full_pattern, html)
            if full_match:
                urls[match.lower()] = f"https://www.bigwhite.com/sites/default/files/{full_match.group(1)}"

        return urls

    def get_image_url(self, camera_id: str) -> str:
        from image_utils import download_image

        # Fetch URLs if cache is empty
        if not self._url_cache:
            self._url_cache.update(self._fetch_webcam_urls())

        # camera_id is like "village", "powpow", "cliff"
        url = self._url_cache.get(camera_id.lower())
        if not url:
            raise ValueError(f"Camera '{camera_id}' not found on Big White webcams page")

        return download_image(url)


# Provider registry
PROVIDERS: dict[str, WebcamProvider] = {
    "brownrice": BrownriceProvider(),
    "youtube": YouTubeProvider(),
    "ski49n": Ski49nProvider(),
    "wetmet": WetMetProvider(),
    "bigwhite": BigWhiteProvider(),
}


def get_provider(name: str) -> WebcamProvider:
    """Get a provider instance by name."""
    if name not in PROVIDERS:
        raise ValueError(f"Unknown provider: {name}. Available: {list(PROVIDERS.keys())}")
    return PROVIDERS[name]
