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
cp data/india_heatmap.png docs/assets/india_heatmap.png
cp data/current_temps.json docs/assets/

# Update README.md with cache-busting timestamp
STAMP="$(date +'%Y-%m-%d %H:%M:%S %Z')"
README="$REPO_DIR/weather_api/README.md"
IMG_PATH="docs/assets/india_heatmap.png"

# Replace or insert the image link
if grep -q "!\[India Heatmap\]" "$README"; then
    # Match only the line with "India Heatmap"
    sed -i "s|!\[India Heatmap\](.*)|![India Heatmap]($IMG_PATH?v=$STAMP)|" "$README"
else
    echo -e "\n![India Heatmap]($IMG_PATH?v=$STAMP)" >> "$README"
fi

# Commit & push only the updated files
git add docs/assets/india_heatmap.png docs/assets/current_temps.json "$README" || true
if ! git diff --cached --quiet; then
    git commit -m "auto publish $STAMP"
    git push origin main
fi
