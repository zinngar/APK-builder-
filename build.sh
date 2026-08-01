#!/bin/bash
set -euo pipefail

BUILD_TYPE="${1:-release}"   # release | debug
OUT_DIR="/app/output"
mkdir -p "$OUT_DIR"

echo "==> Trafficlites APK build starting (type: $BUILD_TYPE)"

# Prebuild the native android/ folder if it doesn't exist yet
# (skip this if you already commit the android/ folder to the repo)
if [ ! -d "android" ]; then
  echo "==> No android/ folder found, running expo prebuild..."
  npx expo prebuild --platform android --non-interactive
fi

cd android
chmod +x ./gradlew

if [ "$BUILD_TYPE" = "debug" ]; then
  ./gradlew assembleDebug
  APK_PATH=$(find app/build/outputs/apk/debug -name "*.apk" | head -n 1)
else
  ./gradlew assembleRelease
  APK_PATH=$(find app/build/outputs/apk/release -name "*.apk" | head -n 1)
fi

if [ -z "$APK_PATH" ]; then
  echo "!! Build finished but no APK was found."
  exit 1
fi

cp "$APK_PATH" "$OUT_DIR/"
echo "==> APK copied to $OUT_DIR/$(basename "$APK_PATH")"
