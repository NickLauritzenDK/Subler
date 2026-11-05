# Component modernization design

Preserve the official Subler application source, UI/UX and feature set on the repaired 1.9.5 baseline. Update third-party components incrementally: OCR stack, Sparkle, FFmpeg, and rebuild the current Subler-specific MP4v2 source as appropriate. Continue macOS 13 local build floor and universal arm64/x86_64 output. No added OCR engine, changed settings, new audio policy or redesign.

Use checksum-pinned official source archives and scripts in MP42Foundation/Dependencies and scripts. Build dependency archives outside version-controlled source; reference generated archives through explicit Xcode build settings. This avoids a third fork of prebuilt binaries and makes the exact source/configuration reviewable. Preserve original traineddata and API consumers; retain existing codec matrix while adapting FFmpeg APIs.

Test real OCR with a fixed synthetic image, compiled version checks and image codecs, all existing baseline comparisons, and targeted audio decode/encode plus subtitle regression fixtures for FFmpeg. OCR words can change with Tesseract revisions; establish feature functionality and report differences rather than claiming identical accuracy or improvement. Run both CPU architectures, describing Rosetta accurately. Keep network service/updater-installation and broad corpus limitations explicit.
