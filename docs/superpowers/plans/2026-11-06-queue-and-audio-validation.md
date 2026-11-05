# Neo: queue cancellation and broader conversion validation

Continue the accepted correctness audit without visual or feature changes.

- [x] Reproduce queue cancellation at the boundary between items and a writer throwing after cancellation using the complete production Queue.swift with real dispatch/notifications/archiving and controlled item processing.
- [x] Fix only confirmed queue-state defects; keep ordinary failures reported and later work progressing; ensure selection/registering the current item is synchronized with stop.
- [x] Add broader synthetic audio coverage using the actual embedded framework: mono/stereo/multichannel where supported, more input formats and explicit downmix/preservation checks. Document actual formats run and any blockers rather than weaken expectations.
- [x] Integrate tests in the Neo build workflow, independent review, build and package next local test app, run full targeted regressions, publish exact tested source and report limits.

Review focus: stopping between items must leave next item ready; cancelled write exceptions must not become ordinary failure notifications; real failures must still continue; duplicate start must not duplicate work; wider tests must derive expected duration/channels/pitch independently of production output. No changes to PGS OCR policy or icon. macOS 13 and listening/surround hardware coverage remain separate.

## Evidence and review

- Queue:15 assertions pass; before fixes, five assertions failed across stop-before-work, stop-between-items and cancelled-writer cases. Independent review found no actionable regression. Real media cancellation blocking remains covered only by existing decoder/encoder cancellation tests, not the controlled QueueItem double.
- Audio: original24/36 matrix passed with12 ALAC failures. After decoder repair, tests exposed legacy channel count and presentation duration defects. Independent RMS checks also found44.9ms PCM->AAC onset delay. All38 final conversion/timeline cases and three decoder config checks pass.
- Review ruling: limit AAC presentation correction to tested AVFoundation/MP4 lossless sources. Matroska constructs edits from encoded output duration and needs its own fixture before changing its policy; applying the generic shift could create overlong edits. Cost of deferral: Matroska timing remains unverified and may retain an inherited defect.
- Intentional gaps/trims use AVFoundation timeline checks rather than afconvert's raw decode; real+250/-100ms cases pass. Empty edit sentinel handling covers both edit-list versions.
- Full app Release build succeeds. All14 targeted verification stages pass against the signed build3 bundle. Seven embedded executables/libraries are arm64. Manual startup/About confirms1.0(3).
- The accepted icon is compiled from a separate committed copy. The user's local Icon Composer edit remains untouched and excluded from this code commit.
