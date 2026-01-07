"""
Frame Extractor

Extract a single frame from a video stream URL using ffmpeg-python.
Returns base64-encoded JPEG.
"""

import base64
import os
import tempfile

import ffmpeg


def extract_frame(url: str) -> str:
    """
    Extract a single frame from a video stream URL.

    Args:
        url: Video stream URL (HLS, RTSP, etc.)

    Returns:
        Base64-encoded JPEG image

    Raises:
        RuntimeError: If ffmpeg is not installed or fails
    """
    with tempfile.NamedTemporaryFile(suffix=".jpg", delete=False) as tmp:
        tmp_path = tmp.name

    try:
        # Extract single frame from video stream
        # vframes=1: extract only 1 frame
        # qscale=2: high quality JPEG (1-31, lower is better)
        (
            ffmpeg
            .input(url)
            .output(tmp_path, vframes=1, qscale=2)
            .run(overwrite_output=True, capture_stderr=True, quiet=True)
        )

        with open(tmp_path, "rb") as f:
            image_data = f.read()

        return base64.b64encode(image_data).decode("utf-8")

    except ffmpeg.Error as e:
        stderr = e.stderr.decode("utf-8", errors="replace") if e.stderr else str(e)
        raise RuntimeError(f"ffmpeg failed: {stderr[:500]}")

    except FileNotFoundError:
        raise RuntimeError(
            "ffmpeg is required but not found. "
            "Install with: brew install ffmpeg (macOS) or apt install ffmpeg (Linux)"
        )

    finally:
        if os.path.exists(tmp_path):
            os.unlink(tmp_path)
