# Subler source recovery implementation plan

> For agentic workers: execute inline with superpowers:executing-plans and verify before completion.

**Goal:** Replace the unavailable MP42Foundation revision with a tested source build in our fork.
**Architecture:** Characterize official 1.9.5 track APIs, then minimally repair reachable source and wire the Subler fork to a committed replacement.
**Tech stack:** Objective-C, Swift 5 mode, Xcode 27.2, existing static contrib archives, macOS 13 local build.
**Spec:** ../specs/2026-11-05-source-recovery-design.md

## Global constraints
- Preserve app source/UI/resources outside necessary compatibility work.
- No OCR enhancements, redesign, or architecture optimization in this repair.
- No claim to reproduce missing source or cover all behaviors.

## Review focus
- Multi-track removal undo restores exact original ordering, including unsorted selections.
- Moving contiguous/noncontiguous tracks up/down and undo/redo preserve identity/order.
- Imported/muxed track state, deletion queue and references survive undo.
- Chapter ordering/undo and metadata remain unchanged.
- Fresh recursive clones of the modernization branch fetch every pinned object.

### Task 1: Establish baseline and regression cases
- [x] Build available MP42Foundation at macOS 13 with original contrib.
- [x] Add Tests/track-editing.m and a runner that work against official and rebuilt frameworks.
- [x] Record literal expected ordering and state from official 1.9.5.
- [x] Observe available-source failure for missing API or wrong undo behavior.

### Task 2: Repair only demonstrated differences
- [x] Modify MP42/MP42File.h and .m to add indexed insertion and reversible movement/removal.
- [x] Run identical tests against official and rebuilt frameworks; examine disagreements.
- [x] Build framework and Subler using source, retaining original UI/resources.

### Task 3: Make fork reproducible
- [x] Review source diff and test limits.
- [x] Commit verified framework repair and tests in our fork.
- [x] Change Subler .gitmodules and gitlink on modernization branch only.
- [x] Add build instructions, pinned provenance and validation results.
- [x] Verify fresh recursive source retrieval, rebuild, rerun tests; report remaining modernization work.

## Validation ledger

The framework patch is committed as 7f38350e1abdbde8f1968c71e8c89594ddb5fce8. Original-source API test failed before repair; 454 characterization traces, 14 checks and 5 real media workflows pass on arm64 and x86_64/Rosetta after repair. App and framework Release builds produce both slices. Independent review found no actionable issues. Fresh recursive clone of Subler f4698a2c6beaeff99a3a017b39ba681231670b3a fetched MP42Foundation 7f38350e1abdbde8f1968c71e8c89594ddb5fce8 and contrib debd14253dba88addfd918d144fb7872a9e075f7. The documented build script completed successfully and the complete arm64 suite passed. Source recovery milestone complete; dependency upgrades remain the next stage.
