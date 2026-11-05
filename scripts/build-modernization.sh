#!/bin/bash
# Local source-recovery baseline: original app UI, macOS 13+, universal build.
set -euo pipefail
repo_root=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)
build_root=${1:-"$repo_root/build/modernization"}
mkdir -p "$build_root"
build_root=$(cd -- "$build_root" && pwd)
git -C "$repo_root" submodule update --init --recursive
xcodebuild -project "$repo_root/Subler.xcodeproj" -scheme Subler \
  -configuration Release -derivedDataPath "$build_root/DerivedData" \
  -clonedSourcePackagesDirPath "$build_root/SourcePackages" \
  -destination 'generic/platform=macOS' ONLY_ACTIVE_ARCH=NO \
  MACOSX_DEPLOYMENT_TARGET=13.0 CODE_SIGNING_ALLOWED=NO CODE_SIGNING_REQUIRED=NO build
python3 "$repo_root/MP42Foundation/Tests/run-tests.py" \
  "$build_root/DerivedData/Build/Products/Release/Subler.app" "$build_root/Tests"
