"""
Resort and webcam configuration.

To add a new resort or camera:
1. Add the resort to RESORTS dict
2. Specify the provider and camera IDs
3. The downloader will automatically use the correct provider

Supported providers:
- brownrice: Static image snapshots from player.brownrice.com
- youtube: YouTube livestream thumbnails from i.ytimg.com
- ski49n: Static images from ski49n.com/webcams
- wetmet: HLS video streams from WetMet (requires ffmpeg for frame extraction)
"""

from dataclasses import dataclass
from enum import Enum


class CameraType(Enum):
    """Type of webcam view."""
    BASE = "base"          # Base area / lodge
    SUMMIT = "summit"      # Summit / peak
    LIFT = "lift"          # Chair lift / gondola
    TERRAIN = "terrain"    # Ski runs / terrain
    PARKING = "parking"    # Parking lot
    SNOW_STAKE = "snow_stake"  # Snow measurement
    OTHER = "other"


@dataclass
class Camera:
    """Represents a single webcam."""
    id: str
    name: str
    provider: str
    type: CameraType = CameraType.OTHER


@dataclass
class Resort:
    """Represents a ski resort with webcams."""
    name: str
    website: str
    cameras: list[Camera]
    region: str = "Pacific Northwest"


# =============================================================================
# RESORT DEFINITIONS
# =============================================================================

RESORTS: dict[str, Resort] = {

    # -------------------------------------------------------------------------
    # STEVENS PASS (Vail Resorts) - Washington
    # -------------------------------------------------------------------------
    "stevens_pass": Resort(
        name="Stevens Pass",
        website="https://www.stevenspass.com",
        region="Washington",
        cameras=[
            Camera(
                id="stevenspasssnowstake",
                name="Snow Stake",
                provider="brownrice",
                type=CameraType.SNOW_STAKE,
            ),
            Camera(
                id="stevenspasscourtyard",
                name="Courtyard",
                provider="brownrice",
                type=CameraType.BASE,
            ),
            Camera(
                id="stevenspassschool",
                name="Ski School",
                provider="brownrice",
                type=CameraType.BASE,
            ),
            Camera(
                id="stevenspassjupiter",
                name="Jupiter Chair",
                provider="brownrice",
                type=CameraType.LIFT,
            ),
            Camera(
                id="stevenspassskyline",
                name="Skyline Chair",
                provider="brownrice",
                type=CameraType.LIFT,
            ),
        ],
    ),

    # -------------------------------------------------------------------------
    # WHITE PASS - Washington
    # -------------------------------------------------------------------------
    "white_pass": Resort(
        name="White Pass",
        website="https://skiwhitepass.com",
        region="Washington",
        cameras=[
            Camera(
                id="pigtailpeak",
                name="Pigtail Peak",
                provider="brownrice",
                type=CameraType.SUMMIT,
            ),
            Camera(
                id="couloir",
                name="Couloir",
                provider="brownrice",
                type=CameraType.TERRAIN,
            ),
            Camera(
                id="whitepasslive",
                name="Base Area",
                provider="brownrice",
                type=CameraType.BASE,
            ),
            Camera(
                id="whitepasshighcamp",
                name="High Camp",
                provider="brownrice",
                type=CameraType.TERRAIN,
            ),
            Camera(
                id="whitepasssnowstake",
                name="Snow Stake",
                provider="brownrice",
                type=CameraType.SNOW_STAKE,
            ),
            Camera(
                id="whitepassnordic",
                name="Nordic Center",
                provider="brownrice",
            ),
        ],
    ),

    # -------------------------------------------------------------------------
    # WHISTLER BLACKCOMB (Vail Resorts) - British Columbia
    # Uses universal player.brownrice.com/snapshot endpoint (auto-resolves server)
    # -------------------------------------------------------------------------
    "whistler_blackcomb": Resort(
        name="Whistler Blackcomb",
        website="https://www.whistlerblackcomb.com",
        region="British Columbia",
        cameras=[
            Camera(
                id="whistlerblackcomb",
                name="Blackcomb Base",
                provider="brownrice",
                type=CameraType.BASE,
            ),
            Camera(
                id="whistlerroundhouse",
                name="Roundhouse",
                provider="brownrice",
            ),
            Camera(
                id="whistlerpeak",
                name="Peak",
                provider="brownrice",
                type=CameraType.SUMMIT,
            ),
            Camera(
                id="whistlervillage",
                name="Village",
                provider="brownrice",
                type=CameraType.BASE,
            ),
            Camera(
                id="whistlercreekside",
                name="Creekside",
                provider="brownrice",
                type=CameraType.BASE,
            ),
            Camera(
                id="whistlersnowstack",
                name="Snow Stack",
                provider="brownrice",
                type=CameraType.SNOW_STAKE,
            ),
            Camera(
                id="whistler7thheaven",
                name="7th Heaven",
                provider="brownrice",
                type=CameraType.TERRAIN,
            ),
            Camera(
                id="whistlerglacier",
                name="Glacier",
                provider="brownrice",
                type=CameraType.TERRAIN,
            ),
            Camera(
                id="whistlervillagefitz",
                name="Village Fitzsimons",
                provider="brownrice",
                type=CameraType.BASE,
            ),
        ],
    ),

    # -------------------------------------------------------------------------
    # SUMMIT AT SNOQUALMIE (Boyne Resorts) - Washington
    # Uses YouTube livestream thumbnails
    # -------------------------------------------------------------------------
    "summit_snoqualmie": Resort(
        name="The Summit at Snoqualmie",
        website="https://www.summitatsnoqualmie.com",
        region="Washington",
        cameras=[
            Camera(
                id="w4Sno8NIjmU",
                name="Summit Central Express Top",
                provider="youtube",
                type=CameraType.LIFT,
            ),
            Camera(
                id="H7HwsNLqVC8",
                name="Silver Fir Base Area",
                provider="youtube",
                type=CameraType.BASE,
            ),
            Camera(
                id="c83QV-cloJs",
                name="Summit Central Base Area",
                provider="youtube",
                type=CameraType.BASE,
            ),
        ],
    ),

    # -------------------------------------------------------------------------
    # MISSION RIDGE - Washington
    # Uses YouTube livestream thumbnails
    # -------------------------------------------------------------------------
    "mission_ridge": Resort(
        name="Mission Ridge",
        website="https://www.missionridge.com",
        region="Washington",
        cameras=[
            Camera(
                id="Wy1f0CzNaAM",
                name="Sunspot",
                provider="youtube",
                type=CameraType.TERRAIN,
            ),
            Camera(
                id="WviO5Mlq_TE",
                name="Midway",
                provider="youtube",
                type=CameraType.TERRAIN,
            ),
            Camera(
                id="TERghSgEi_o",
                name="Mimi",
                provider="youtube",
                type=CameraType.TERRAIN,
            ),
        ],
    ),

    # -------------------------------------------------------------------------
    # 49 DEGREES NORTH - Washington
    # Self-hosted static images
    # -------------------------------------------------------------------------
    "49_degrees_north": Resort(
        name="49 Degrees North",
        website="https://www.ski49n.com",
        region="Washington",
        cameras=[
            Camera(
                id="lodge",
                name="Lodge",
                provider="ski49n",
                type=CameraType.BASE,
            ),
            Camera(
                id="summit",
                name="Summit",
                provider="ski49n",
                type=CameraType.SUMMIT,
            ),
            Camera(
                id="sunrise",
                name="Sunrise Basin",
                provider="ski49n",
                type=CameraType.TERRAIN,
            ),
        ],
    ),

    # -------------------------------------------------------------------------
    # MT HOOD MEADOWS - Oregon
    # Uses WetMet HLS video streams (requires ffmpeg)
    # -------------------------------------------------------------------------
    "mt_hood_meadows": Resort(
        name="Mt Hood Meadows",
        website="https://www.skihood.com",
        region="Oregon",
        cameras=[
            Camera(
                id="c878c340832e23aab90526673b71cc17",
                name="Top of Blue",
                provider="wetmet",
                type=CameraType.TERRAIN,
            ),
            Camera(
                id="1be5f08dfca10d15d5e4ec9627c17c7c",
                name="Bottom of Vista",
                provider="wetmet",
                type=CameraType.TERRAIN,
            ),
            Camera(
                id="eec27f8164fc1105656ea4d46df4cd37",
                name="Top of Vista",
                provider="wetmet",
                type=CameraType.TERRAIN,
            ),
            Camera(
                id="072e3c1a6016174851619e4180909d3d",
                name="Base Area",
                provider="wetmet",
                type=CameraType.BASE,
            ),
        ],
    ),
}


def get_all_cameras() -> list[tuple[Resort, Camera]]:
    """Return all cameras across all resorts."""
    result = []
    for resort in RESORTS.values():
        for camera in resort.cameras:
            result.append((resort, camera))
    return result
