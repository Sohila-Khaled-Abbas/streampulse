"""Convert SVG diagrams to high-quality, high-resolution PNG images.

Supports:
- Microsoft Edge Headless CLI
- Google Chrome Headless CLI
- CairoSVG (if installed)
"""

import contextlib
import os
import shutil
import subprocess
import sys
from typing import Optional

# Ensure project root is in sys.path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.utils.logger import logger


def find_browser_executable() -> Optional[str]:
    """Find Microsoft Edge or Google Chrome executable."""
    # Check in PATH
    for name in ["msedge", "chrome", "google-chrome", "chromium"]:
        found = shutil.which(name)
        if found:
            return found

    # Standard Windows install locations
    candidate_paths = [
        r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
        r"C:\Program Files\Microsoft\Edge\Application\msedge.exe",
        r"C:\Program Files\Google\Chrome\Application\chrome.exe",
        r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
        os.path.expandvars(r"%LOCALAPPDATA%\Microsoft\Edge\Application\msedge.exe"),
        os.path.expandvars(r"%LOCALAPPDATA%\Google\Chrome\Application\chrome.exe"),
    ]
    for path in candidate_paths:
        if os.path.exists(path):
            return path
    return None


def convert_svg_to_png_browser(
    svg_path: str,
    png_path: str,
    browser_exe: str,
    width: int = 2800,
    height: int = 1700,
) -> bool:
    """Render SVG to high-quality PNG using headless browser screenshot."""
    abs_svg = os.path.abspath(svg_path).replace("\\", "/")
    abs_png = os.path.abspath(png_path)
    file_url = f"file:///{abs_svg}"

    # HTML wrapper to ensure perfect full-bleed high DPI rendering
    wrapper_html_path = abs_svg + ".tmp.html"
    with open(wrapper_html_path, "w", encoding="utf-8") as f:
        f.write(f"""<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<style>
  * {{ box-sizing: border-box; }}
  html, body {{
    margin: 0;
    padding: 0;
    width: {width}px;
    height: {height}px;
    overflow: hidden;
    background: #0b0f19;
  }}
  img {{
    width: 100%;
    height: 100%;
    object-fit: contain;
    display: block;
  }}
</style>
</head>
<body>
  <img src="{file_url}" />
</body>
</html>
""")

    wrapper_url = f"file:///{os.path.abspath(wrapper_html_path).replace(chr(92), '/')}"
    temp_user_data = os.path.abspath(
        os.path.join(os.path.dirname(abs_png), ".browser_temp_profile")
    )
    os.makedirs(temp_user_data, exist_ok=True)

    cmd = [
        browser_exe,
        "--headless",
        "--disable-gpu",
        "--no-sandbox",
        "--hide-scrollbars",
        "--disable-dev-shm-usage",
        f"--user-data-dir={temp_user_data}",
        f"--window-size={width},{height}",
        f"--screenshot={abs_png}",
        wrapper_url,
    ]

    try:
        logger.info(f"Rendering {svg_path} -> {png_path} ({width}x{height}px)...")
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=20)
        if os.path.exists(abs_png) and os.path.getsize(abs_png) > 1000:
            logger.info(
                f"[SUCCESS] Generated high-res PNG: {png_path} ({os.path.getsize(abs_png):,} bytes)"
            )
            return True
        else:
            logger.warning(
                f"Browser screenshot failed: {result.stderr or result.stdout}"
            )
    except Exception as e:
        logger.error(f"Error running browser renderer: {e}")
    finally:
        if os.path.exists(wrapper_html_path):
            with contextlib.suppress(OSError):
                os.remove(wrapper_html_path)
        if os.path.exists(temp_user_data):
            with contextlib.suppress(OSError):
                shutil.rmtree(temp_user_data, ignore_errors=True)

    return False


def convert_all_diagrams() -> None:
    """Convert all project SVGs into high quality PNGs."""
    assets_dir = os.path.join("docs", "assets")
    diagrams = [
        {
            "svg": os.path.join(assets_dir, "streampulse_architecture.svg"),
            "png": os.path.join(assets_dir, "streampulse_architecture.png"),
            "width": 2800,
            "height": 1700,
        },
        {
            "svg": os.path.join(assets_dir, "streampulse_data_model.svg"),
            "png": os.path.join(assets_dir, "streampulse_data_model.png"),
            "width": 2600,
            "height": 1700,
        },
    ]

    browser_exe = find_browser_executable()
    if not browser_exe:
        logger.error(
            "No compatible browser (Edge/Chrome) found for rendering SVG to PNG."
        )
        return

    logger.info(f"Using browser renderer: {browser_exe}")

    for item in diagrams:
        if os.path.exists(item["svg"]):
            success = convert_svg_to_png_browser(
                svg_path=item["svg"],
                png_path=item["png"],
                browser_exe=browser_exe,
                width=item["width"],
                height=item["height"],
            )
            if not success:
                logger.error(f"Failed to convert {item['svg']}")
        else:
            logger.warning(f"SVG file not found: {item['svg']}")


if __name__ == "__main__":
    convert_all_diagrams()
