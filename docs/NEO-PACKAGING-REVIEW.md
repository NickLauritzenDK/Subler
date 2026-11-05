# Subler Neo — anden kodegennemgang, 6. november 2026

## Rettet: utilstrækkelig kontrol af bibliotekers indlæsningsstier

Den hidtidige pakkekontrol fandt et bibliotek ud fra filnavn og placering et sted i appen. Den kunne derfor godkende en pakke, selv om biblioteket lå uden for programmets faktiske søgestier. Den kunne også godkende et hjælpeprogram, som ikke selv havde den nødvendige søgesti.

Kontrollen følger nu hvert programs afhængighedskæde, de angivne LC_RPATH-søgestier og betydningen af @loader_path og @executable_path. Hjælpeprogrammer kontrolleres i deres egen sammenhæng. Biblioteker uden en kendt indlæsningskæde afvises frem for at få gættet en vært.

En uafhængig gennemgang fandt yderligere et tilfælde: en eksisterende henvisning uden for appen blev sprunget over, hvis et senere søgeresultat lå inde i appen. Det er rettet, og en ny test viste fejlen før rettelsen og bestod efter.

## Verificering

- 15 pakketests med rigtige Mach-O-programmer og biblioteker består.
- Negative tests reproducerede de oprindelige fejl før rettelsen.
- Gyldige nedarvede søgestier, biblioteksrelative søgestier, hjælpeprogrammer, søgestirækkefølge, symbolske links og cirkulære afhængigheder er dækket.
- Den udgivne Neo 1.0 (2) med syv arm64-programmer/biblioteker består den nye kontrol.
- En fuld lokal pakning med den nye kontrol og streng signaturverifikation lykkedes.
- Alle eksisterende målrettede Neo-regressionstests består: app-identitet, app-korrekthed, kildeverifikation, arm64-opskrift, OCR-datasti, framework-baseline, OCR, FFmpeg, lyd-baseline, lydkorrekthed, lagringsfejl og FIFO.

Appens funktioner, konverteringskode og foreløbige ikon er uændrede. Denne rettelse forebygger, at fremtidige fejlbyggede pakker bliver godkendt. Den forbedrer ikke i sig selv lyd- eller billedkvalitet. Der er ikke behov for at geninstallere build 2.

## Grænser

Dette er en konservativ kontrol før pakning, ikke en fuldstændig efterligning af macOS' indlæser. Runtime-indlæste plugins, fysisk macOS 13-test, fuld format- og surroundtest samt Developer ID/notarisation og egen opdateringskanal er fortsat åbne punkter. Ikonet er stadig foreløbigt. PGS-OCR-forbedringer og målt Apple Silicon-optimering er separate faser.

Teknisk reference: [Apples dokumentation om run-path-afhængige biblioteker](https://developer.apple.com/library/archive/documentation/DeveloperTools/Conceptual/DynamicLibraries/100-Articles/RunpathDependentLibraries.html).
