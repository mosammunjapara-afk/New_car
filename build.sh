#!/usr/bin/env bash
# Render build script — sirf dependencies (API ke liye)
# NOTE: Playwright browser cloud pe install NAHI karte (root chahiye, Render deta nahi).
# API sirf database se prices serve karti hai — browser sirf sync (scraping) ke liye,
# jo aap apne PC se chalate ho. Isliye cloud pe browser ki zaroorat nahi.
set -o errexit

pip install -r requirements.txt
