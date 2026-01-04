# Browser automation on Linux servers (Google Maps / Selenium)

If you see an error like:

`chromedriver unexpectedly exited. Status code was: 127`

it usually means **ChromeDriver launched but could not run** because the server is missing:
- a Chrome/Chromium browser, and/or
- required shared libraries (common on minimal Docker images / Alpine).

## Recommended approach
- **Use headless mode on servers** (no GUI required).
- Prefer **system-installed** `chromium` + `chromedriver` on Linux.
- Override paths via env vars if needed:
  - `CHROME_BINARY=/usr/bin/chromium`
  - `CHROMEDRIVER_PATH=/usr/bin/chromedriver`

## Ubuntu/Debian (EC2/VPS)
Install Chromium + driver (package names differ by distro):

### Debian/Ubuntu (apt)
Try:
- `sudo apt-get update`
- `sudo apt-get install -y chromium chromium-driver`

If those packages aren’t available on your Ubuntu version, use Google Chrome:
- install `google-chrome-stable` (from Google’s repo)
- install a matching `chromedriver` (or rely on Selenium Manager)

### Common missing libs
If `chromedriver` still exits with `127`, run:
- `ldd /path/to/chromedriver | grep "not found" || true`

Then install the missing libs (often includes packages like):
`libnss3`, `libatk1.0-0`, `libatk-bridge2.0-0`, `libx11-6`, `libxcomposite1`, `libxdamage1`, `libxrandr2`, `libgbm1`, `libasound2`, `fonts-liberation`.

## Docker note (important)
If you’re using **Alpine Linux**, the official ChromeDriver binaries typically won’t run (musl vs glibc) and you’ll get `127`.
Use a Debian/Ubuntu-based image instead (or install a compatible Chromium/driver from Alpine repos).

## Non-headless (GUI) mode
Non-headless requires an X display. On servers, either:
- keep `headless=true`, or
- use Xvfb: `sudo apt-get install -y xvfb` and run the app under `xvfb-run ...`.

