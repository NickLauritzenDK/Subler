# MKV audio presentation timing — build 5, 6 November 2026

## Findings and correction

Build 4 passed 18 macOS lossless checks, but independent FFmpeg decoding exposed problems masked by platform AAC priming compensation: PCM/FLAC audio started 44 ms late, AC3/EAC3 approximately 38 ms late, and negative block timestamps could wrap into an approximately 40-day positive start. MKV Opus terminal DiscardPadding was not applied.

Build 5 preserves signed MKV timestamps through offset/duration calculations and clamps negative progress to zero. For MKV-to-AAC only, source frames are retained instead of applying guessed codec-specific decoder drops. Cleanup explicitly combines source offset, new AAC priming and actual consumed PCM frame count into presentation edits. OpusHead decoder pre-skip is accounted for once and terminal positive DiscardPadding shortens the valid presentation. The offset is marked applied so a later generic rewrite cannot remove priming. UI and icon are unchanged.

## Independent regression

`python3 Tests/mkv-extended.py FFMPEG_TOOL_DIRECTORY APP OUTPUT_DIRECTORY`

21 generated audiovisual cases exercise PCM, FLAC, AAC, AC3, EAC3, DTS and Opus at 48 kHz stereo, each with -100/0/+250 ms offset. Each contains a three-second 64x64 MPEG4 video timeline and two synthetic audio pulses. The test checks:

- Negative timestamps are present in negative-offset source fixtures.
- Opus fixtures really carry initial skip and terminal discard metadata.
- Source/output pulse boundaries agree within 12 ms on an independently decoded, zero-anchored presentation timeline.
- All video packet presentation timestamps agree within 2 ms and decoded video bytes have identical SHA256.
- Raw MP4 audio edit-list presentation length agrees with independently decoded source duration within 3 ms. Additional raw AAC decode padding is bounded by one AAC packet plus 3 ms.

The final test exits nonzero on build 4 (2/21 pass) and passes 21/21 on the corrected framework. All logs, packets, generated files and tool provenance are retained. No user media is committed.

Some decoders expose raw AAC padding after a leading empty edit even when the edit list specifies the correct presentation end. Therefore raw decoded frame count and playable edit duration are checked separately; neither replaces pulse timing or picture checks. The previous claim that platform lossless checks alone ruled out a timing correction was too broad.

## Test tool reproduction

The independent tools were built from the same checksum-verified FFmpeg 9.0.2 archive recorded in `MP42Foundation/Dependencies/sources.json` (SHA256 `8c3850283eb25fa026482078a04051e0be17347b09ef81a0849bec15a96e002e`). The tools are test-only and are not embedded in the app. The configuration is retained in `tool-provenance.json` via `ffmpeg -version`, together with tool binary hashes. Build in a path without spaces. Enable ffmpeg/ffprobe, file protocol, lavfi input, testsrc2 and aresample filters, Matroska/MOV/WAV demuxers, Matroska/MP4/WAV/rawvideo muxers and the native codecs used by the test. DTS and Opus fixture encoders run with explicit experimental mode; they are synthetic test generators, not Neo encoder choices.

## Existing regression coverage

The 18 PCM/ALAC MKV cases at 32/44.1/48 kHz and 0/250/1000 ms offsets remain in `Tests/mkv-timing.py`. The existing 38 general audio cases cover PCM/ALAC/AAC, mono/stereo/5.1, downmix and edited ALAC. Baseline editing/media checks remain unchanged.

## Limits

Synthetic frame/timeline agreement is not a listening test or proof of sync in every player. Long real files, external players/surround hardware, and other macOS versions remain broader acceptance work. Internal timestamp discontinuities, midstream/negative DiscardPadding, laced-packet variants and MKV surround/multiple-audio-track fixtures remain outside this matrix. No changes were made for those unverified cases. H264/HEVC B-frame timing is not established by the MPEG4 no-B-frame fixture.

References: [Matroska block structure](https://www.matroska.org/technical/notes.html), [codec mappings](https://www.matroska.org/technical/codec_specs.html).
