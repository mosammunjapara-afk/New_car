#!/usr/bin/env bash
# Render build script — dependencies + Playwright Chrome install
set -o errexit

pip install -r requirements.txt
# Playwright ka Chromium browser install (scraping/sync ke liye)
playwright install chromium
playwright install-deps chromium
