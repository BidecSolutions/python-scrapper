import os
import platform
import shutil
from typing import Optional

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service


def _which(*names: str) -> Optional[str]:
    for name in names:
        path = shutil.which(name)
        if path:
            return path
    return None


def resolve_chrome_binary() -> Optional[str]:
    """
    Resolve a Chrome/Chromium binary path.

    Deployment override:
      - CHROME_BINARY=/usr/bin/google-chrome
    """
    env_path = os.getenv("CHROME_BINARY")
    if env_path:
        return env_path
    return _which("google-chrome", "google-chrome-stable", "chromium-browser", "chromium", "chrome")


def resolve_chromedriver_path() -> Optional[str]:
    """
    Resolve a ChromeDriver path.

    Deployment override:
      - CHROMEDRIVER_PATH=/usr/bin/chromedriver
    """
    env_path = os.getenv("CHROMEDRIVER_PATH")
    if env_path:
        return env_path
    return _which("chromedriver")


def ensure_display_or_headless(headless: bool) -> None:
    """
    Non-headless Chrome requires a display on Linux (DISPLAY/X11).
    """
    if headless:
        return
    if platform.system().lower() != "linux":
        return
    if os.getenv("DISPLAY"):
        return
    raise ValueError(
        "Non-headless Chrome requires a display (DISPLAY is not set). "
        "Run with headless=true, or install/configure Xvfb (virtual display)."
    )


def create_chrome_driver(chrome_options: Options) -> webdriver.Chrome:
    """
    Create a Selenium Chrome driver with robust resolution:
    - Prefer explicit CHROMEDRIVER_PATH / system chromedriver if present
    - Otherwise rely on Selenium Manager (Selenium 4.6+)
    - Optionally fall back to webdriver-manager if USE_WEBDRIVER_MANAGER=1
    """
    chromedriver_path = resolve_chromedriver_path()
    try:
        if chromedriver_path:
            return webdriver.Chrome(service=Service(chromedriver_path), options=chrome_options)
        return webdriver.Chrome(options=chrome_options)
    except Exception as first_error:
        if os.getenv("USE_WEBDRIVER_MANAGER") == "1":
            try:
                from webdriver_manager.chrome import ChromeDriverManager

                return webdriver.Chrome(
                    service=Service(ChromeDriverManager().install()),
                    options=chrome_options,
                )
            except Exception:
                pass

        raise ValueError(
            "Chrome driver not available. "
            "On Linux servers this is usually caused by missing Chrome/Chromium or shared libraries. "
            "Install Chrome/Chromium + dependencies, or set CHROME_BINARY and CHROMEDRIVER_PATH. "
            f"Root error: {first_error}"
        )

