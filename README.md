# Ski Resort Webcam Analyzer

Analyzes ski resort webcam images using Perceptron models to rank resorts based on current conditions (crowdedness, snow quality, visibility, weather).

## Supported Resorts

| Resort | Region | ToS Prohibits Crawling | Video Source | Extraction Method | Cameras | Status |
|--------|--------|------------------------|--------------|-------------------|---------|--------|
| Stevens Pass | WA | No | Brownrice CDN | Static JPEG URL | 5 | Enabled |
| White Pass | WA | No | Brownrice CDN | Static JPEG URL | 6 | Enabled |
| Whistler Blackcomb | BC | No | Brownrice CDN | Static JPEG URL | 9 | Enabled |
| Summit at Snoqualmie | WA | No | YouTube Livestream | Static thumbnail URL | 6 | Enabled |
| Crystal Mountain | WA | **Yes** (Alterra ToS) | Verkada/Roundshot | N/A | 2+ | Blocked |
| Mission Ridge | WA | No | YouTube Livestream | Static thumbnail URL | 3 | Enabled |
| 49 Degrees North | WA | No | Self-hosted | Download to base64 | 3 | Enabled |
| Mt Hood Meadows | OR | No | WetMet HLS | ffmpeg frame extraction | 4 | Enabled (needs ffmpeg) |
| Schweitzer | ID | **Yes** (Alterra ToS) | Roundshot | N/A | 5 | Blocked |
| Mt Baker | WA | Unknown | None found | N/A | 0 | No webcams on resort site |

## Installation

### 1. Clone and install dependencies

```bash
git clone <repo-url>
cd ski_resort_ranking
pip install -r requirements.txt
```

### 2. Configure environment variables

Copy the example environment file and add your API keys:

```bash
cp .env.example .env
```

Edit `.env` and add your Perceptron API key:

```
PERCEPTRON_API_KEY=your_api_key_here
```

### 3. Install ffmpeg (optional, for Mt Hood Meadows)

Mt Hood Meadows uses HLS video streams that require ffmpeg to extract frames.

**macOS (Homebrew):**
```bash
brew install ffmpeg
```

**Ubuntu/Debian:**
```bash
sudo apt update
sudo apt install ffmpeg
```

**Windows:**
Download from https://ffmpeg.org/download.html and add to PATH.

## Usage

### Analyze all resorts

```bash
python resort_analyzer.py
```

### Analyze a specific resort

```bash
python resort_analyzer.py --resort stevens_pass
```

### Analyze and launch GUI

```bash
python resort_analyzer.py --gui
```

The GUI (Streamlit) displays:
- Resorts ranked by composite score
- Webcam images with individual ratings per camera
- Navigation between resorts (previous/next)

### List available webcam URLs

```bash
# All resorts
python -m webcam_downloader

# Specific resort
python -m webcam_downloader --resort stevens_pass

# List available resorts
python -m webcam_downloader --list-resorts

# List cameras for a resort
python -m webcam_downloader --list-cameras stevens_pass
```

## How It Works

1. **Webcam Downloader** fetches current webcam images from each resort using provider-specific methods (see Provider Details below)

2. **Resort Analyzer** sends images to Perceptron AI for analysis, rating each on:
   - Crowdedness (1-10, higher = less crowded)
   - Snow quality (1-10)
   - Visibility (1-10)
   - Weather conditions (1-10)

3. **Rankings** are calculated using a weighted composite score:
   - Snow quality: 40%
   - Weather: 25%
   - Visibility: 20%
   - Crowdedness: 15%

## Provider Details

| Provider | URL Pattern | Response | URL Permanence | Used By |
|----------|-------------|----------|----------------|---------|
| Brownrice | `player.brownrice.com/snapshot/{id}` | Static JPEG | Permanent | Stevens Pass, White Pass, Whistler |
| YouTube | `i.ytimg.com/vi/{id}/maxresdefault_live.jpg` | Static JPEG thumbnail | Permanent (~5 min refresh) | Summit at Snoqualmie, Mission Ridge |
| Ski49n | `ski49n.com/webcams/{name}.jpg` | Downloads to base64 | Permanent | 49 Degrees North |
| WetMet | `api.wetmet.net/widgets/stream/frame.php?uid={uid}` | HLS stream (needs ffmpeg) | Temporary (30 min token) | Mt Hood Meadows |
| OpenSnow | `webcams.opensnow.com/current/{id}.jpg` | N/A | N/A | **Blocked** (ToS prohibits AI/ML) |

## ToS Investigation Notes

### Alterra Mountain Company (Crystal Mountain, Schweitzer)
> "Website access by means of bots, spiders, and similar tools is expressly prohibited, as is accessing the website for purposes of crawling or aggregating information"

### OpenSnow
> "You will not use the Content for the development of any software program, including training a machine learning or artificial intelligence (AI) system"

### 49 Degrees North
- No explicit crawling prohibition
- robots.txt has no restrictions

### Mission Ridge
- No explicit crawling prohibition in privacy policy
- robots.txt: `Allow: *`

### Mt Hood Meadows
- No crawling terms found
- robots.txt: `Allow: /`

### Mt Baker
- No web ToS found (only ski safety policies)
- robots.txt: `Allow: *`
- **Note**: Resort website has no webcams; only external sources (NWCAA air quality cam)

## Adding New Resorts

Edit `webcam_downloader/config.py` to add new resorts:

```python
"new_resort": Resort(
    name="New Resort Name",
    slug="new-resort",
    website="https://example.com",
    region="State/Province",
    cameras=[
        Camera(
            id="camera_id",
            name="Camera Name",
            provider="brownrice",  # or youtube, ski49n, wetmet
        ),
    ],
),
```
