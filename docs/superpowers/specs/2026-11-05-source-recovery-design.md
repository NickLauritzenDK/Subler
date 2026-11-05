# Subler 1.9.5 source recovery

Scope: repair source retrieval and the baseline build in the two maintained forks.

Start Subler at official tag 1.9.5, commit 9077b6d149be621ff7d7b0d8eb46839a56610844. Use reachable MP42Foundation bfa477b799ce55716f744638e6dfe3f23d39c5d7 as repair base because exact gitlink 4648f9d585b38957a797bdb13632497abdbe4dfe cannot be retrieved. This is a replacement implementation, not recovered upstream source.

Preserve official UI/resources/features. No earlier OCR, settings or audio-policy changes are imported. Recover missing track editing/undo behavior using the checksum-verified official binary as an independent oracle. Test chapters and metadata as regression coverage. Use macOS 13 for local diagnostic builds as previously described; do not advertise compatibility with older systems from that build.

Approaches: exact source recovery is ideal but blocked by unavailable commit; blindly pinning bfa477b loses known APIs and undo order; a narrow tested repair in our fork allows progress. The selected approach is the narrow tested repair. Unknown behavior beyond tested scenarios must remain documented.

Commit the framework repair on modernization/components; point only the Subler modernization branch at the repaired fork revision. Keep upstream main unchanged. Add reproducible build and test instructions. Treat source initialization and an actual application build as distinct gates. Component upgrades follow a working baseline and are incremental.
