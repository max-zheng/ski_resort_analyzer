"""
Image Downloader

Download an image directly from a URL and return as base64.
Useful for servers that block cloud IPs or require specific headers.
"""

import base64
import urllib.request
from typing import Optional


def download_image(
    url: str,
    timeout: int = 15,
    user_agent: Optional[str] = None,
) -> str:
    """
    Download an image from a URL and return as base64.

    Args:
        url: Direct image URL
        timeout: Timeout in seconds
        user_agent: Optional User-Agent header (some servers block default)

    Returns:
        Base64-encoded image data

    Raises:
        urllib.error.URLError: If download fails
        urllib.error.HTTPError: If server returns error status
    """
    headers = {}
    if user_agent:
        headers["User-Agent"] = user_agent
    else:
        # Default to a browser-like user agent
        headers["User-Agent"] = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)"

    req = urllib.request.Request(url, headers=headers)

    with urllib.request.urlopen(req, timeout=timeout) as response:
        image_data = response.read()

    return base64.b64encode(image_data).decode("utf-8")
