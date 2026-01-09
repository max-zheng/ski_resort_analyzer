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


class Category(Enum):
    """Rating categories for webcam analysis."""
    SNOW_QUALITY = "snow_quality"
    VISIBILITY = "visibility"
    WEATHER = "weather_conditions"
    ACTIVITY = "activity"


ALL = [Category.SNOW_QUALITY, Category.VISIBILITY, Category.WEATHER, Category.ACTIVITY]


@dataclass
class Camera:
    """Represents a single webcam."""
    id: str
    name: str
    provider: str
    categories: list[Category]

    def get_category_names(self) -> list[str]:
        """Get category names to evaluate for this camera."""
        return [c.value for c in self.categories]


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
            Camera(id="stevenspasssnowstake", name="Snow Stake", provider="brownrice", categories=[Category.SNOW_QUALITY, Category.WEATHER, Category.VISIBILITY]),
            Camera(id="stevenspasscourtyard", name="Courtyard", provider="brownrice", categories=ALL),
            Camera(id="stevenspassschool", name="Ski School", provider="brownrice", categories=ALL),
            Camera(id="stevenspassjupiter", name="Jupiter Chair", provider="brownrice", categories=ALL),
            Camera(id="stevenspassskyline", name="Skyline Chair", provider="brownrice", categories=ALL),
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
            Camera(id="pigtailpeak", name="Pigtail Peak", provider="brownrice", categories=ALL),
            Camera(id="couloir", name="Couloir", provider="brownrice", categories=ALL),
            Camera(id="whitepasslive", name="Base Area", provider="brownrice", categories=ALL),
            Camera(id="whitepasshighcamp", name="High Camp", provider="brownrice", categories=ALL),
            Camera(id="whitepasssnowstake", name="Snow Stake", provider="brownrice", categories=[Category.SNOW_QUALITY, Category.WEATHER, Category.VISIBILITY]),
            Camera(id="whitepassnordic", name="Nordic Center", provider="brownrice", categories=ALL),
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
            Camera(id="whistlerblackcomb", name="Blackcomb Base", provider="brownrice", categories=ALL),
            Camera(id="whistlerroundhouse", name="Roundhouse", provider="brownrice", categories=ALL),
            Camera(id="whistlerpeak", name="Peak", provider="brownrice", categories=ALL),
            Camera(id="whistlervillage", name="Village", provider="brownrice", categories=ALL),
            Camera(id="whistlercreekside", name="Creekside", provider="brownrice", categories=ALL),
            Camera(id="whistlersnowstack", name="Snow Stack", provider="brownrice", categories=[Category.SNOW_QUALITY, Category.WEATHER, Category.VISIBILITY]),
            Camera(id="whistler7thheaven", name="7th Heaven", provider="brownrice", categories=ALL),
            Camera(id="whistlerglacier", name="Glacier", provider="brownrice", categories=ALL),
            Camera(id="whistlervillagefitz", name="Village Fitzsimons", provider="brownrice", categories=[Category.WEATHER, Category.VISIBILITY, Category.ACTIVITY]),
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
            Camera(id="w4Sno8NIjmU", name="Summit Central Express Top", provider="youtube", categories=ALL),
            Camera(id="H7HwsNLqVC8", name="Silver Fir Base Area", provider="youtube", categories=ALL),
            Camera(id="c83QV-cloJs", name="Summit Central Base Area", provider="youtube", categories=[]),
            Camera(id="YhM0ns8LLOg", name="Summit West Base Area", provider="youtube", categories=ALL),
            Camera(id="vhO8nNqg9iw", name="Summit East Base Area", provider="youtube", categories=ALL),
            Camera(id="8wk81COX2cg", name="Alpental Base Area", provider="youtube", categories=ALL),
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
            Camera(id="Wy1f0CzNaAM", name="Sunspot", provider="youtube", categories=ALL),
            Camera(id="WviO5Mlq_TE", name="Midway", provider="youtube", categories=ALL),
            Camera(id="TERghSgEi_o", name="Mimi", provider="youtube", categories=ALL),
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
            Camera(id="lodge", name="Lodge", provider="ski49n", categories=ALL),
            Camera(id="summit", name="Summit", provider="ski49n", categories=ALL),
            Camera(id="sunrise", name="Sunrise Basin", provider="ski49n", categories=ALL),
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
            Camera(id="c878c340832e23aab90526673b71cc17", name="Top of Blue", provider="wetmet", categories=ALL),
            Camera(id="1be5f08dfca10d15d5e4ec9627c17c7c", name="Bottom of Vista", provider="wetmet", categories=ALL),
            Camera(id="eec27f8164fc1105656ea4d46df4cd37", name="Top of Vista", provider="wetmet", categories=[Category.SNOW_QUALITY, Category.WEATHER, Category.VISIBILITY]),
            Camera(id="072e3c1a6016174851619e4180909d3d", name="Base Area", provider="wetmet", categories=ALL),
        ],
    ),

    # -------------------------------------------------------------------------
    # BIG WHITE - British Columbia
    # Self-hosted static images (URLs scraped dynamically as they may change)
    # -------------------------------------------------------------------------
    "big_white": Resort(
        name="Big White",
        website="https://www.bigwhite.com",
        region="British Columbia",
        cameras=[
            Camera(id="village", name="Village Centre", provider="bigwhite", categories=ALL),
            Camera(id="powpow", name="Pow Cam", provider="bigwhite", categories=[Category.SNOW_QUALITY]),
            Camera(id="cliff", name="The Cliff", provider="bigwhite", categories=ALL),
            Camera(id="easystreet", name="Easy Street", provider="bigwhite", categories=ALL),
            Camera(id="happyvalley", name="Happy Valley", provider="bigwhite", categories=ALL),
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
