# Subler Neo

Subler Neo is a separate Apple Silicon-only application based on official Subler 1.9.5, with modernized dependencies and targeted correctness fixes. macOS 13 or newer is required. Its identity (`dk.nicklauritzen.SublerNeo`), preferences, cache, queue, presets and OCR downloads are separate from Subler. No automatic data migration is performed.

Build with `scripts/build-neo.sh`. The resulting local test ZIP is ad-hoc signed, not notarized. Neo does not use the official Subler update feed; its own signed update service is not configured yet. The native Icon Composer icon is provisional; further design refinement remains open.

The original Subler project and its contributors retain their credits and licenses. Historical upstream information follows.

# README #

### What is this repository for? ###

Subler is an Mac OS X app created to mux and tag mp4 files. The main features includes:

* Creation of tx3g subtitles tracks, compatible with all Apple's devices (iPod, AppleTV, iPhone, QuickTime?).
* Mux video, audio, chapters, subtitles and closed captions tracks from mov, mp4 and mkv.
* Raw formats: H.264 Elementary streams (.h264, .264), AAC (.aac), AC3 (.ac3), Scenarist (.scc), VobSub? (.idx).
* metadata editing and TMDb, TVDB and iTunes Store support.

### Build and run

Clone the repository and include all submodules
```
git clone --recurse-submodules https://github.com/SublerApp/Subler.git
```
If you already cloned without submodules and need to add the submodules manually, `cd` into the `./Subler` directory and clone the dependency submodules with 
```
git submodule update --init --recursive
```
Open `Subler.xcodeproj` in XCode

Build and run the project by selecting the 'Subler' scheme (`Product` -> `Scheme` -> `Subler`) and clicking the 'Run' button in Xcode’s toolbar.



### Subler Neo local build

On Apple Silicon, run `bash scripts/build-neo.sh`. This builds `build/neo/DerivedData/Build/Products/Release/Subler Neo.app` and runs native arm64 checks. See [MODERNIZATION.md](MODERNIZATION.md) for pinned dependencies, reproduction and historical verification scope.
