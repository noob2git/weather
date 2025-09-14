#!/usr/bin/env bash
set -euo pipefail

REPO_DIR="$HOME/git/weather"
PYTHON="$REPO_DIR/weather_api/.venv/bin/python"
MAIN_PY="$REPO_DIR/weather_api/main.py"

cd "$REPO_DIR"

# 1) Regenerate outputs
"$PYTHON" "$MAIN_PY"

# 2) Copy only the heatmap
mkdir -p docs/assets
cp data/india_heatmap.png docs/assets/india_heatmap.png

# 3) Build identifiers
#    - STAMP: full UTC timestamp (for your records)
#    - BUILD_HEX: 6-hex chars derived from epoch seconds (UTC) -> traceable
EPOCH_UTC=$(date -u +%s)
BUILD_HEX=$(printf '%06X' $(( EPOCH_UTC & 0xFFFFFF )))   # 24-bit hex
STAMP=$(date -u +'%Y-%m-%d %H:%M:%S UTC')                # human-readable

# 4) README with cache-busting using BUILD_HEX
README="$REPO_DIR/README.md"
IMG_PATH="docs/assets/india_heatmap.png"
cat > "$README" <<EOF
# Weather Project

Here’s the latest heatmap of weather:

![India Heatmap]($IMG_PATH?v=$BUILD_HEX)
EOF

# 5) Optional: keep a lookup log so any 6-hex can be traced exactly
#    Format: HEX,epoch_utc,timestamp_utc,git_short_sha(after commit)
LOG="$REPO_DIR/docs/assets/builds.csv"
touch "$LOG"
# We'll append git SHA after commit below.

# 6) Commit & push only PNG + README (+ log if changed)
git add docs/assets/india_heatmap.png "$README" "$LOG" || true
if ! git diff --cached --quiet; then
    git commit -m "auto publish $BUILD_HEX"
    # After commit, capture short SHA and finalize the log row
    GIT_SHA=$(git rev-parse --short HEAD)
    echo "$BUILD_HEX,$EPOCH_UTC,$STAMP,$GIT_SHA" >> "$LOG"
    git add "$LOG"
    git commit -m "log build $BUILD_HEX"
    git push origin main
fi
