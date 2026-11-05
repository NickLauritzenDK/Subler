# Component upgrades implementation plan

> Execute inline with superpowers:executing-plans; review and verify before completion.

**Goal:** Modernize the dependency stack without modifying the application interface or feature policy.
**Architecture:** Pin official source archives, build each architecture separately, combine universal static libraries, and select generated dependencies with Xcode settings. Keep independent baseline traces frozen.
**Tech Stack:** Xcode 27.2, CMake 4.4.4, Ninja 1.13.2, Python 3, macOS 13+, Objective-C/Swift.
**Spec:** ../specs/2026-11-05-component-upgrades-design.md

## Global constraints
- Preserve app source/resources and original traineddata.
- Both arm64 and x86_64 archives; no host-only compiler flags.
- No library outside the reviewed source manifest is silently bundled.
- Keep inherited parser components and system libraries distinguished from updated external archives.

## Review focus
- OCR initializes original traineddata and handles PNG/TIFF images on both architectures.
- No required static transitive dependency or architecture slice is missing.
- FFmpeg retains configured decoders/parsers/muxer and actual audio conversion.
- Encoded sample payload/timing comparisons against official baseline stay intact.
- Fresh-clone build downloads verify checksums; reused output cannot hide changed build inputs.

### Task 1: OCR stack
- [x] Pin Tesseract 5.5.4, Leptonica 1.87.0, PNG 1.6.59, TIFF 4.7.2, JPEG-turbo 3.2.1.
- [x] Add real OCR/image-codec/version tests; record baseline and expected version failure.
- [x] Implement dependency builder and explicit generated library/header paths.
- [x] Build/test arm64 and x86_64; run original regression suite.

### Task 2: FFmpeg and MP4v2
- [x] Pin FFmpeg 9.0.2 and current Subler MP4v2 revision, retain original feature configuration.
- [x] Add targeted decoder/encoder/subtitle cases before API migration.
- [x] Adapt only required FFmpeg API changes; no OCR/UI feature changes.
- [x] Build both architectures and compare output data/timing with baseline.

### Task 3: Sparkle and reproducibility
- [x] Upgrade exact Sparkle pin and Package.resolved to 2.10.1.
- [x] Wire dependency builds into app build script; document licenses/provenance and limits.
- [ ] Review complete patch, verify fresh build and tests, publish only our fork branches.

## Execution ledger

OCR stack built and tested before FFmpeg migration; legacy runtime-version assertions failed before upgrades. FFmpeg's old APIs failed the new-header build; const codecs/channel-layout/context lifecycle adaptations now compile and pass the frozen regression suite. MP4v2 lacked the shipped Director setter in its source; its test failed before the compatibility patch and passes afterward.

Component review found source-extraction cache trust and mixed framework/archive test gaps; both fixed. Two cache-tampering tests failed against the original builder and all three source-verification tests pass after correction. FFmpeg now has separate actual-framework and standalone executables. PNG/JPEG test configurations were corrected to actually register tests; ctest rejects an empty suite.

Final app tests passed on arm64 and x86_64/Rosetta, including OCR, synthetic PGS, actual AAC/AC3 conversion and original baseline scenarios. Fresh-clone recipe validation and final fork publication remain the last gate.
