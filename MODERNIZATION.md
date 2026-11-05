# Subler modernization: source-recovery baseline

## Scope and source

This branch starts at official Subler 1.9.5, `9077b6d149be621ff7d7b0d8eb46839a56610844`. It retains the application source, Xcode project settings, UI resources, assets, localizations, AppleScript dictionary and original feature code. No earlier custom OCR/settings/audio-policy changes are included.

The release's MP42Foundation gitlink `4648f9d585b38957a797bdb13632497abdbe4dfe` could not be fetched from its official origin. We do not claim to have recovered that source. Instead, our fork starts at the reachable `bfa477b799ce55716f744638e6dfe3f23d39c5d7` and repairs indexed track insertion, removal undo ordering and reversible track movement. Subler points at the fixed commit `7f38350e1abdbde8f1968c71e8c89594ddb5fce8` in https://github.com/NickLauritzenDK/MP42Foundation.

Contrib remains at upstream `debd14253dba88addfd918d144fb7872a9e075f7`. Sparkle stays at exact version 2.9.6, revision `ac2def288cbff5cfc7df3ffef6abdf45b72bcb0a`, with a checked-in Package.resolved. Those dependencies have not yet been modernized in this source-recovery milestone.

## Reproduce

```sh
git clone --branch modernization/official-1.9.5 --recurse-submodules https://github.com/NickLauritzenDK/Subler.git
cd Subler
bash scripts/build-modernization.sh
```

Requires macOS, Python 3 and Xcode (validated with Xcode 27.2 build 27B52 / SDK 27.2). The script builds Release with both arm64 and x86_64, disables signing for local testing, and runs the full targeted framework suite against the actual app's framework. Outputs default to ignored build/modernization. Supply a different output directory as the first script argument.

The local build uses a command-line macOS 13 deployment target, as in the earlier working build. The upstream project still declares 10.13. Xcode 27 cannot target 10.13; this build does **not** establish support for 10.13–12. No installation, signing identity, notarization, updater installation or App Store distribution is performed.

To exercise Intel code on an Apple Silicon machine with Rosetta installed:

```sh
python3 MP42Foundation/Tests/run-tests.py build/modernization/DerivedData/Build/Products/Release/Subler.app build/modernization/Tests-x86_64 --arch x86_64
```

## Verification recorded 2026-11-05

- Both the framework and actual application build successfully from source with Xcode 27.2 at macOS 13, producing arm64 + x86_64 slices.
- 440 editing traces, 14 state/chapter traces, 14 explicit behavior checks, and 5 real-file workflows match the checksum-verified official 1.9.5 framework on arm64 and on x86_64 under Rosetta.
- File workflows include two AAC tracks, UTF-8 SRT subtitles, chapters, Unicode metadata, save/reopen, deletion/movement undo/redo, encoded sample hashes and timing comparisons.
- The unmodified available framework demonstrably fails the missing-API test. An intermediate repair failed seven additional state cases; the final repair passes them.
- Independent source/test review reran the arm64 suite and found no actionable issues.
- Tests intentionally retain 19 official reverse-ordered multi-removal exception outcomes and the official chapter-replacement undo limitation. They are documented inherited behavior, not successful undo operations.

Full test harness and official reference provenance are in MP42Foundation/Tests. These results are targeted evidence; they do not prove every UI/workflow/codec matches. No native Intel hardware, older OS, complete OCR, malformed media, artwork, queue persistence, AppleScript, metadata-service network or automatic-update installation acceptance is claimed.

## Next component-upgrade stages

1. Freeze this reproducible baseline before changing libraries.
2. Upgrade Sparkle in its own commit; current 2.10.x requires macOS 12. Preserve updater behavior unless separately testing a local preview configuration.
3. Rebuild/update the OCR library stack (Tesseract, Leptonica, PNG/TIFF) with pinned sources, licenses, build flags and architecture checks. Changing OCR accuracy/engine selection is a separate feature phase.
4. Update FFmpeg with explicit decoder/parser/encoder coverage and byte/timing/audio-conversion regression fixtures. Keep Subler-specific patches and APIs visible.
5. Review MP4v2 and copied parser/muxer components independently; a binary version bump is not proof those embedded sources were updated.
6. Broaden app, UI and compatibility acceptance before distributing a modernization build. PGS OCR enhancements and further Apple Silicon optimization remain later phases.

No upstream branch is changed. Our main fork branch remains an upstream mirror; modernization work lives on the named branches.
