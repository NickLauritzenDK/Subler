#!/bin/bash
# Build the pinned dependency stack and the unchanged Subler application UI.
set -euo pipefail
repo_root=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)
build_root=${1:-"$repo_root/build/modernization"}
dependency_root=${2:-"$repo_root/MP42Foundation/build/dependencies"}
git -C "$repo_root" submodule update --init --recursive
mkdir -p "$build_root" "$dependency_root"
build_root=$(cd -- "$build_root" && pwd)
dependency_root=$(cd -- "$dependency_root" && pwd)
python3 "$repo_root/Tests/app-correctness.py"
python3 "$repo_root/MP42Foundation/Tests/test-source-verification.py"
python3 "$repo_root/MP42Foundation/scripts/build-dependencies.py" "$dependency_root" --components all
xcodebuild -project "$repo_root/Subler.xcodeproj" -scheme Subler \
  -configuration Release -derivedDataPath "$build_root/DerivedData" \
  -clonedSourcePackagesDirPath "$build_root/SourcePackages" \
  -destination 'generic/platform=macOS' ONLY_ACTIVE_ARCH=NO \
  "MP42_OCR_ROOT=$dependency_root/ocr" "MP42_FFMPEG_ROOT=$dependency_root/ffmpeg" \
  "MP42_MP4V2_ROOT=$dependency_root/mp4v2" \
  MACOSX_DEPLOYMENT_TARGET=13.0 CODE_SIGNING_ALLOWED=NO CODE_SIGNING_REQUIRED=NO build
app="$build_root/DerivedData/Build/Products/Release/Subler.app"
# Universal validation on the supported Apple Silicon + Rosetta build host.
for test_arch in arm64 x86_64; do
  python3 "$repo_root/MP42Foundation/Tests/run-tests.py" "$app" "$build_root/Tests-$test_arch" --arch "$test_arch"
  python3 "$repo_root/MP42Foundation/Tests/run-ocr-test.py" "$app" "$build_root/OCR-tests-$test_arch" --arch "$test_arch"
  python3 "$repo_root/MP42Foundation/Tests/run-ffmpeg-test.py" "$app" "$build_root/FFmpeg-tests-$test_arch" --include "$dependency_root/ffmpeg/include" --arch "$test_arch"
  python3 "$repo_root/MP42Foundation/Tests/run-audio-test.py" "$app" "$build_root/Audio-tests-$test_arch" --arch "$test_arch"
  python3 "$repo_root/MP42Foundation/Tests/run-audio-correctness-test.py" "$app" "$build_root/Audio-correctness-$test_arch" --dependencies "$dependency_root" --arch "$test_arch"
  python3 "$repo_root/MP42Foundation/Tests/run-save-failures.py" "$app" "$build_root/Save-tests-$test_arch" --arch "$test_arch"
  python3 "$repo_root/MP42Foundation/Tests/run-fifo-test.py" "$app" "$build_root/FIFO-tests-$test_arch" --arch "$test_arch"
done

# Keep notices for the new static dependencies with the local test bundle.
licenses="$app/Contents/Resources/DependencyLicenses"
mkdir -p "$licenses"
for component in ocr ffmpeg mp4v2; do
  ditto "$dependency_root/$component/licenses" "$licenses/$component"
done
cp "$repo_root/MP42Foundation/Dependencies/sources.json" "$licenses/sources.json"
