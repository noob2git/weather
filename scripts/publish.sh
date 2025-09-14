#!/usr/bin/env bash
set -euo pipefail

REPO_DIR="$HOME/git/weather"
PYTHON="$REPO_DIR/weather_api/.venv/bin/python"
MAIN_PY="$REPO_DIR/weather_api/main.py"

cd "$REPO_DIR"

# Run Python to refresh outputs
"$PYTHON" "$MAIN_PY"

# Copy outputs to docs/
mkdir -p docs/assets
cp data/india_heatmap.png docs/assets/
cp data/current_temps.json docs/assets/

# Commit & push
STAMP="$(date +'%Y-%m-%d %H:%M:%S %Z')"
git add docs/ data/current_temps.json
git commit -m "Auto: publish heatmap $STAMP" || true
git push origin main
