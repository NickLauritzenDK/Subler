# Neo packaging: validate actual loader search paths

Scope: close the known packaging-check gap without changing the app UI, icon, conversion behavior or dependencies. Work continues on the isolated Neo branch.

- [x] Reproduce false acceptance with a real arm64 executable linked to an @rpath library present only outside its search path. Add positive fixtures for @loader_path, inherited executable run paths and framework-owned run paths; isolate helper executable contexts and reject symlinks escaping the bundle.
- [x] Replace suffix searching in scripts/package-neo.py: parse Mach-O types, dependencies and LC_RPATH, then walk each executable's dependency chain with its own executable directory and inherited run paths. Require dependencies to resolve to bundled Mach-O files or explicit system references. Keep existing strict treatment of weak non-system dependencies. Reject orphan libraries whose host cannot be established rather than guessing a host.
- [x] Run packaging and existing Neo regression suites, verify the existing app with the new checker, review the change, and publish the tested tooling update. The released app binary and icon remain build 2 because only packaging tooling changes.

Review focus: nested helper executable paths; transitive inherited run paths; loader-relative rpaths belong to the declaring image; symlinks must stay inside the app; cycles must terminate. This is a packaging preflight, not a complete replacement for dyld, code signing verification, runtime tests, or validation on macOS 13.

References: Apple's Dynamic Library Programming Topics / Run-Path Dependent Libraries; apple-oss-distributions/dyld Loader.cpp.

## Evidence and review

- Original checker: two negative real-Mach-O fixtures failed because no error was raised (library outside its run paths; helper incorrectly accepted without its own run paths).
- Updated checker: 15 packaging tests pass, including valid inherited and loader-owned paths, actual helper executable directory, escaping symlinks, orphan-library rejection and cyclic dependencies.
- Independent review found one P2: an existing external symlink candidate could be skipped in favor of a later bundled copy. The new two-runpath regression failed before the fix and passed after. A missing first candidate still permits a valid later candidate.
- Current released Neo build 2, all seven Mach-O images: passes the updated preflight. No app code or icon change is required.
- Policy: orphan libraries are rejected because their loader context cannot be established; this app has none. Future runtime-loaded plugins need explicit host coverage rather than a guessed search path. System references and weak-library treatment retain the earlier packaging policy.

Final verification: all 13 targeted suite stages pass (packaging: 15 tests). Full package/signature verification succeeds. No unresolved review findings. Tooling-only change: do not replace the released build 2 archive.
