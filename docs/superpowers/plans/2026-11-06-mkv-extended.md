# Extended MKV timing validation

Goal: complete the remaining deterministic compressed audio, negative timestamp and audiovisual synchronization checks. Preserve all app UI and unrelated behavior.

1. Build local pinned FFmpeg command-line tools from existing verified sources for independent fixture generation, packet/timeline inspection and decoded waveform comparison.
2. Add generated AAC/AC3/FLAC fixtures, positive and negative offsets, paired video/audio markers, plus codec delay/discard padding where supported. Compare the same source decoded by FFmpeg to framework-converted output on the presentation timeline, not raw packet counts alone.
3. Capture failing baseline and isolate importer/decoder/muxer responsibility before minimal production fixes. Keep known working lossless cases passing.
4. Build and run relevant regressions, document untestable hardware/player/OS limits and any concrete blockers. Do not treat synthetic sync checks as listening/hardware verification.

## Execution findings

The final independent 21-case test passes on the corrected framework and fails on build 4 (2/21). Fixed signed negative audio timestamps, MKV-to-AAC priming placement and valid sample-count bounds, including Opus decoder pre-skip and terminal positive discard. Existing 18 platform MKV, 38 general audio and 473 baseline checks pass on the isolated correction. Separate review found no actionable issue in frame-count/timebase/lifecycle handling. Build 5 integrates the reviewed framework commit. Physical playback/player/OS coverage and discontinuity/lacing variants remain explicitly outside this synthetic matrix.
