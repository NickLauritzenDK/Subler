# Subler 1.9.5 component modernization

## Scope and source

This branch starts at official Subler 1.9.5, `9077b6d149be621ff7d7b0d8eb46839a56610844`. It retains the application source, UI resources, assets, localizations, AppleScript dictionary and original feature code. No earlier custom OCR/settings/audio-policy changes are included.

The release's MP42Foundation gitlink `4648f9d585b38957a797bdb13632497abdbe4dfe` could not be fetched from its official origin. We do not claim to have recovered that source. Instead, our fork starts at the reachable `bfa477b799ce55716f744638e6dfe3f23d39c5d7` and repairs indexed track insertion, removal undo ordering and reversible track movement. The repaired baseline commit was `7f38350e1abdbde8f1968c71e8c89594ddb5fce8`. Component upgrades build on that repair; the application gitlink pins the exact updated revision in https://github.com/NickLauritzenDK/MP42Foundation.

The old contrib submodule stays pinned for the original traineddata and baseline headers. The production link now explicitly selects newly source-built universal dependency archives; it does not silently fall back to the old contrib libraries.

| Component | Baseline | Updated |
| --- | --- | --- |
| Tesseract | 5.0.0 | 5.5.4 |
| Leptonica | 1.82.0 | 1.87.0 |
| libpng | 1.6.37 | 1.6.59 |
| libtiff | 4.2.0 | 4.7.2 |
| JPEG | Prior bundled/transitive version not established | libjpeg-turbo 3.2.1 |
| FFmpeg | 4.4 | 9.0.2 |
| Sparkle | 2.9.6 | 2.10.1 (ab7d71291238df6e0492143b120c9b696a35f603) |
| MP4v2 | 2.1.3 with Subler-specific APIs | Current Subler source 76799d1 + required Director accessor |

Official archive URLs/checksums, compatibility patch, configurations and licenses are recorded under MP42Foundation/Dependencies. Build tooling is pinned locally to tested CMake 4.4.4, Ninja 1.13.2 and NASM 3.02.

## Reproduce Subler Neo

Use the local `neo` app branch and `neo/apple-silicon` framework branch. These local branches have not been published.

```sh
bash scripts/build-neo.sh
```

Requires an Apple Silicon Mac, Python 3 and Xcode. The recipe builds only arm64 static dependencies and Release `Subler Neo.app`, passing `ARCHS=arm64 ONLY_ACTIVE_ARCH=NO` to the app and framework build. It runs the native arm64 regression, OCR, FFmpeg, audio, save and FIFO checks. Outputs default to ignored `build/neo`; dependencies default to `MP42Foundation/build/dependencies`. Optional first and second arguments select those directories. Pinned sources/tools download on first build; verified completion stamps permit later reuse. A cache hit does not rerun dependency tests. No installation, notarization or publishing is performed.

macOS 13 remains the minimum. The historical verification below describes predecessor modernization builds, including their earlier architecture coverage; it is not a claim about Neo validation.

## Verification recorded 2026-11-05

- Both the framework and actual application build successfully from source with Xcode 27.2 at macOS 13, producing arm64 + x86_64 slices.
- 440 editing traces, 14 state/chapter traces, 14 explicit behavior checks, and 5 real-file workflows match the checksum-verified official 1.9.5 framework on arm64 and on x86_64 under Rosetta.
- File workflows include two AAC tracks, UTF-8 SRT subtitles, chapters, Unicode metadata, save/reopen, deletion/movement undo/redo, encoded sample hashes and timing comparisons.
- The unmodified available framework demonstrably fails the missing-API test. An intermediate repair failed seven additional state cases; the final repair passes them.
- Independent source/test review reran the arm64 suite and found no actionable issues.
- A completely fresh recursive clone from our GitHub fork fetched both pinned submodules, built successfully using scripts/build-modernization.sh, and passed the complete arm64 suite without using old working copies.
- Tests intentionally retain 19 official reverse-ordered multi-removal exception outcomes and the official chapter-replacement undo limitation. They are documented inherited behavior, not successful undo operations.

Full test harness and official reference provenance are in MP42Foundation/Tests. These results are targeted evidence; they do not prove every UI/workflow/codec matches. No native Intel hardware, older OS, complete OCR, malformed media, artwork, queue persistence, AppleScript, metadata-service network or automatic-update installation acceptance is claimed.

## Component validation and remaining scope

The updated framework/app build succeeds with all selected components. Component review identified two verification gaps (modified extraction reuse and mixed framework/archive tests); both were corrected, with explicit cache regression tests and separated FFmpeg executables. Runtime probes verify the actual Tesseract/Leptonica versions and unchanged OCR wrapper. FFmpeg checks distinguish actual-framework codec/PGS checks from the larger standalone archive configuration. Actual AAC/AC3 conversion preserves baseline timing, channel layout and metadata, with decoded-audio comparisons and an explicit 0.1% RMS limit. Source-cache integrity regressions and the upstream image-library suites complement the original frozen regression traces.

Copied Matroska/MPEG4IP/SFIFO/parser/muxer code and macOS-supplied libraries are retained and distinguished from updated archives. See MP42Foundation/Dependencies/README.md and Tests/README.md for configuration, measured verification and coverage limits. No claim is made that every inherited source component is the newest release.

The app's Swift/Objective-C interface source, windows, menus, assets, localizations and scripting dictionary remain unchanged from official 1.9.5. Build configuration, the updater package and underlying framework/dependencies are updated. This is source/resource preservation plus targeted behavior coverage, not full visual or every-feature acceptance.

PGS OCR enhancements, new OCR choices, redesigned settings and additional Apple Silicon performance optimization remain separate later phases. No application is installed or replaces the user's current app; unsigned/ad-hoc local builds are not notarized distribution releases. The upstream repositories and our mirror main branches are unchanged.

## Verified component results (2026-11-05)

The final universal app passed the original 454 editing/state scenarios, 14 direct checks and 5 file workflows on arm64 and x86_64/Rosetta. Both OCR language paths recognized the generated text; runtime Tesseract was 5.5.4 and Leptonica 1.87.0. Actual-framework libavcodec was 63.1.102, matching FFmpeg 9.0.2; its codec/PGS checks passed separately from the standalone full archive matrix.

Upstream image tests: PNG 37, JPEG 212, TIFF 21 per architecture (540 executions total), all passed. The explicit static-archive PNG/TIFF/JPEG probe also passed on each architecture. Three source-verification regressions passed; the original cache-reuse implementation failed the two tampering cases.

Actual AAC/AC3 conversions retained baseline metadata, timing, rate, channel count and decoded frame count. Relative decoded RMS differences were 0.00370% AAC / 0.01771% AC3 on arm64, and 0.00322% / 0.00121% on x86_64, below the stated 0.1% limit. Output is not described as byte-identical after encoding.

No full multichannel/all-codec corpus, every-feature regression, older macOS/native Intel hardware or automatic-update installation result is claimed. Existing compiler deprecation messages and NASM object platform-load-command warnings do not constitute a warning-free build claim.

The complete upgraded recipe was also rebuilt from a fresh recursive clone at application commit `6dd40f8` and framework commit `ba7f8d7`. All dependency builds, upstream image-library tests, source-verification tests, app build and arm64 baseline/OCR/FFmpeg/audio checks passed. The separately tested Intel slice ran under Rosetta; native Intel hardware and exhaustive interactive UI coverage remain unverified.

## Post-modernization correctness phase

The separate `correctness/post-modernization` branch fixes inherited samplerate/AC3 EOF defects, source/setup/track-write error propagation, queue language/state/persistence handling, OCR HTTP/model validation and optimization failure reporting. Cancellation now wakes FIFO waiters and releases workers after partial setup failure. UI resources and feature choices remain unchanged.

New behavior tests cover true decoded duration/pitch at 22.05/24/32/44.1/48/96 kHz, EOF padding, resampler draining, worker/FIFO cancellation, save failures/retry and application errors. They supplement the frozen official baseline; no reference goldens were regenerated. The build script now runs both arm64 and x86_64 checks on the tested Apple Silicon + Rosetta host.
