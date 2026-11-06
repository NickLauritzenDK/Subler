# Subler Neo — current status

## Current version

1.0 (build 5), macOS 13+, Apple Silicon only. The approved Icon Composer design is in `NeoAppIcon.icon`: 12 editable layers in four groups, using silver, smoked subtitle glass, a tilted filmstrip and a metal stylus. Intel support was deliberately removed from Neo, including embedded helper executables.

## Achieved

- Official Subler 1.9.5 provenance retained; reachable framework source reconstructed where the release gitlink was unavailable. Dependency sources/checksums and patches are recorded in the framework repository.
- Frameworks/libraries/build tooling modernized; separate Neo settings, data and update identity. No automatic migration from original Subler.
- Targeted correctness fixes include saving failures, audio rate/EOF handling, queue choices/state/persistence, OCR download validation, cancellation, ALAC configuration/channels and AAC presentation timing for tested lossless-source paths.
- Build 4 integrated the approved icon. Build 5 fixes independently reproduced MKV audio timing, negative timestamp wrap and terminal Opus padding; the icon is unchanged.

## Verification scope

Build 3 passed the complete targeted arm64 regression stages and 38 synthetic audio conversion/timeline cases (PCM/ALAC/AAC, mono/stereo/5.1, 32/44.1/48 kHz, preserved channels, stereo downmix, and edited ALAC timelines), plus decoder-configuration checks.

Build 4 passed Release build, identity checks, 15 packaging tests, strict archive/signature/arm64 verification and manual startup/About inspection with the new icon. The complete audio matrix was not repeated for this icon-only update. The original official-reference tests and immutable goldens remain in the framework Tests directory. Historical Intel/Rosetta results are not claims about current Neo support.

Build 5 passed a fresh Release build and strict unpacked signature/identity/seven-arm64-image verification. The packaged app passes 21 independent MKV audiovisual cases, 18 platform MKV cases, 473 baseline scenarios/checks, identity and 15 packaging tests, plus audio EOF/rate/cancellation correctness tests. The isolated corrected framework also passes all 38 general audio cases. See the MKV report for reproduced build 4 failures and decoder-specific padding distinctions.

## Open work, in priority order

1. Broaden MKV acceptance beyond the passing 21 independent compressed/lossless audiovisual cases and 18 platform lossless cases: real files/players, H264/HEVC B-frames, internal discontinuities, midstream/negative discard, lacing, surround and multiple audio tracks. See [MKV evidence and limits](NEO-MKV-TIMING.md).
2. Measure conversion speed, CPU and peak memory on Apple Silicon before selecting performance changes. Modernization alone does not establish a speed or quality improvement.
3. Broader real-media/long-file, codec, audiovisual-sync, listening, surround hardware and cancellation coverage. macOS 13 has not been tested on a physical machine.
4. Feature acceptance where still unverified: AppleScript, Apple TV transfer, live metadata providers and full OCR-language-download workflows.

PGS OCR improvements remain a separate later phase. Developer ID signing, notarization and a dedicated signed update feed are separate distribution work; the current artifact is locally signed and automatic updates are disabled.

## Workspace housekeeping

The parent development workspace keeps active source repositories, the latest Neo build, current arm64 dependency archives/tools, original baseline material, test source/goldens and result documentation. Superseded generated builds and duplicate intermediate dependency builds can be moved to macOS Trash with a local manifest; Trash is not emptied automatically. No source code, unregistered source files, app settings or OCR data should be discarded as build cleanup. Historical source snapshots are preserved.

The detailed local cleanup inventory is kept with the parent workspace outputs, not uploaded with user media or machine-specific paths.

## Detailed records

- [Neo identity and behavior](../NEO.md)
- [Original modernization record](../MODERNIZATION.md)
- [Queue/audio correctness review](NEO-QUEUE-AUDIO-REVIEW.md)
- [Packaging review](NEO-PACKAGING-REVIEW.md)
- [Approved icon and build 4 verification](NEO-ICON.md)
- [Test entry points](../Tests/README.md)
