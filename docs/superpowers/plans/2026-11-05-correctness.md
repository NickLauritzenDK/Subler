# Code correctness implementation plan

Goal: Correct the nine audited defects while preserving UI and unrelated policies.
Architecture: Narrow fixes at the owning layer, behavioral regression tests independent of inherited golden defects; retain original modernization baseline.
Tech: Swift, Objective-C/C, Xcode, FFmpeg, Python test orchestration.

- [x] Audio: rate-only resampling, legal AC3 rate/timebase, deterministic EOF padding; failing behavioral tests then fixes, targeted runtime checks.
- [x] Saving: fail missing source/setup/track write; clean resource state; regression tests and normal baseline checks.
- [x] App: alternate-group language selection, Edit failure state, queue persistence errors, OCR response validation, optimization errors; test failures then fixes.
- [x] Independent reviews, integrate exact framework code into app, full build + targeted regressions both architectures.
- [x] Package locally signed test app and document results/remaining coverage. Do not claim full security or performance audit.
