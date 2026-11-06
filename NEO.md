# Subler Neo 1.0 (5)

Separat Apple Silicon-app baseret på den moderniserede Subler 1.9.5-kode. Minimum macOS 13. Eksisterende funktioner og hovedvindue er bevaret; navn, ikon og app-identitet er adskilt.

- Eget bundle-id: dk.nicklauritzen.SublerNeo.
- Egne indstillinger, cache og Application Support/Subler Neo. Ingen automatisk import eller ændring af originalens data.
- Intel-understøttelse fjernet, også fra de indbyggede Sparkle-hjælpeprogrammer.
- Godkendt native Icon Composer-ikon med tonet undertekstplade, lagdybde og detaljeret filmramme.
- Automatisk opdatering er deaktiveret, indtil Neo har sin egen opdateringstjeneste og nøgle.
- Testpakken er lokalt signeret, ikke notariseret (Apple har ikke godkendt den til distribution).

Den tidligere opstartsfejl skyldtes en manglende delt PNG-afhængighed. PNG linkes nu statisk, og pakningen afviser manglende eksterne biblioteker. Den færdige app er startet manuelt med korrekt navn, ikon og version.

Bygning med Xcode 27.2 lykkedes. Identitet, pakning, kildeverifikation, arm64-opskrift og OCR-datasti testes sammen med frameworkets eksisterende funktionstests, lydkonvertering, fejlhåndtering ved lagring og køsynkronisering. Se den medfølgende testoversigt. Dette er målrettet regressionstest; ikke en garanti for samtlige funktioner eller dokumentation for øget konverteringskvalitet. macOS 13 er ikke afprøvet på en fysisk maskine.

Fem eksisterende Subler-filer var uændrede i det kontrollerede interval omkring den endelige Neo-opstart. En tidligere sammenligning var påvirket af, at original Subler også var åben, og bruges ikke som bevis for isolation.

PGS-OCR-forbedringer og yderligere optimering er fortsat separate senere faser.

Seneste korrekthedsrettelser: se docs/NEO-QUEUE-AUDIO-REVIEW.md. Køannullering, ALAC og AAC-timing er rettet og verificeret i build 3.

Build 4 indbygger det nye godkendte ikon. Se docs/NEO-ICON.md for verificering.

Build 5 retter MKV-lydtiming og negative tidsstempler samt Opus-slutpadding. Se docs/NEO-MKV-TIMING.md for uafhængige audiovisuelle tests og begrænsninger. Ikonet er uændret fra build 4.
