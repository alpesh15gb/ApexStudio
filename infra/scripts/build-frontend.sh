#!/bin/bash
set -e

# Apex Studio — Frontend Builder
# Builds the Flutter Web frontend on the VPS host.
# Falls back to Docker build if Flutter SDK isn't installed locally.

FRONTEND_DIR="$(cd "$(dirname "$0")/../../frontend" && pwd)"
OUTPUT_DIR="$FRONTEND_DIR/build/web"
TARGET_DIR="${1:-/var/www/apex-studio}"

echo "=== Apex Studio Frontend Build ==="

# Option 1: Use host Flutter SDK if available
if command -v flutter &> /dev/null; then
    echo "Using host Flutter SDK: $(flutter --version | head -1)"
    cd "$FRONTEND_DIR"
    flutter pub get
    flutter build web --release
    echo "Frontend built at: $OUTPUT_DIR"

# Option 2: Use Docker to build
else
    echo "Host Flutter not found. Using Docker build..."
    docker run --rm \
        -v "$FRONTEND_DIR":/app \
        -w /app \
        ghcr.io/cirruslabs/flutter:3.44.0 \
        sh -c "flutter pub get && flutter build web --release"

    if [ ! -d "$OUTPUT_DIR" ]; then
        echo "ERROR: Build failed — output directory not found"
        exit 1
    fi
    echo "Frontend built via Docker"
fi

# Copy to target directory if different
if [ "$OUTPUT_DIR" != "$TARGET_DIR" ]; then
    mkdir -p "$TARGET_DIR"
    cp -r "$OUTPUT_DIR"/* "$TARGET_DIR/"
    echo "Copied to: $TARGET_DIR"
fi

echo "=== Frontend build complete ==="
