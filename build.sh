#!/bin/bash
set -euo pipefail

BUILD_TYPE="${1:-release}"
    # release | debug
OUT_DIR="/app/output"
mkdir -p "$OUT_DIR"

echo "==> Trafficlites APK build starting (type: $BUILD_TYPE)"

# Ensure we are in the project source directory /app
cd /app

#/usr.bin/env npm dependencies first if node_modules does not exist
if [ ! -d "node_modules" ]; then
  if [ -f "yarn.lock" ]; then
    echo "==> yarn.lock found, running yarn install..."
    yarn install
  else
    echo "==> node_modules not found, running npm install..."
    npm install
  fi
fi

# Prebuild the native android/ folder if it doesn't exist yet
if [ ! -d "android" ]; then
  echo "==> No android/ folder found, running expo prebuild..."
  npx expo prebuild --platform android --non-interactive
fi

cd android
chmod +x ./gradlew

if [ "$BUILD_TYPE" = "debug" ]; then
  echo "==> Building Debug APK..."
  ./gradlew assembleDebug
  APK_PATH=$(find app/build/outputs/apk/debug -name "*.apk" | head -n 1)
else
  echo "==> Building Release APK..."
  ./gradlew assembleRelease
  APK_PATH=$(find app/build/outputs/apk/release -name "*.apk" | head -n 1)
fi

if [ -z "$APK_PATH" ]; then
  echo "!! Build finished but no APK was found."
  exit 1
fi

cp "$APK_PATH" "$OUT_DIR/"
echo "==> APK successfully built and copied to $OUT_DIR/$(basename "$APK_PATH")"
