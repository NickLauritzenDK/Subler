# MKV audio timing validation

Scope: establish deterministic lossless MKV-to-AAC timing coverage before changing importer edit handling. Preserve UI and behavior outside demonstrated defects.

1. Generate independently timestamped PCM/ALAC Matroska fixtures, at 32/44.1/48 kHz, starting at 0/250/1000 ms. Preserve exact packets and manifest expectations.
2. Exercise actual build 4 framework, inspect both raw MP4 edit tables and AVFoundation presentation segments, decode and locate generated tone onset/end, check rate/channels/duration.
3. If tests fail, identify boundary and add failing regression before a minimal correction; otherwise retain production code.
4. Record results and precise coverage limits. Compressed source delay/DiscardPadding, negative timestamps, discontinuities and video sync are separate cases until tested.
