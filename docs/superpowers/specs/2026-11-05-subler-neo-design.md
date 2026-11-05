# Subler Neo identity and Apple Silicon design

User-approved direction: separate app named Subler Neo, Apple Silicon only, independent preferences/data/update identity; preserve existing workflows and UI layout. User additionally requested a new modern, detailed 3D icon.

App ID: dk.nicklauritzen.SublerNeo. New app version1.0, build1, macOS13 minimum inherited. Product filename Subler Neo.app; keep internal Swift module/target naming to preserve nib and archive compatibility. Support data folder Subler Neo; do not migrate, rewrite or delete original Subler settings/data. Framework OCR path follows host identity. Explicit arm64 build and dependency recipe, no Intel runtime test requirement. Sparkle remains available but does not contact official Subler's feed or accept its releases. Until a signed Neo feed exists, update checks report an informative unavailable status; do not fabricate a feed/key or publish credentials.

Native Icon Composer icon: film/subtitle editing motif, blue background and separate vector glass layers. Current native icon is accepted only provisionally; the user still finds it too simple, so design refinement remains open. Retain upstream credits/licenses. No redesign of app controls. Preserve previous milestone and correctness branches; use neo/apple-silicon branches and a separate deliverable.
