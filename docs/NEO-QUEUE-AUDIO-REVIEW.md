# Subler Neo 1.0 (3) — kø og lydkonvertering

Dato: 6. november 2026. Lokal testudgave til Apple Silicon, macOS 13 eller nyere.

## Rettelser

- Stop før arbejdet eller mellem filer starter ikke længere den næste fil. Valg og registrering af den aktive fil sker samlet, så Stop ikke kan overse den.
- En skrivefejl som følge af annullering giver nu annulleret status og én annulleringsmeddelelse. Almindelige skrivefejl rapporteres stadig, og køen fortsætter til næste fil.
- Gyldig ALAC kunne ikke konverteres til AAC: importeren leverer en 24-byte konfiguration, mens FFmpeg forventer en 36-byte alac-boks. Tilpasningen sker nu kun ved dekoderens grænse; importerens data ændres ikke. FFmpegs bufferpadding nulstilles også.
- ALAC-kanalantal læses nu fra den egentlige konfiguration. Den gamle sample-entry-værdi kunne være 2 både for mono og 5.1, hvilket også forhindrede korrekt stereo-nedmixning.
- PCM→AAC havde i testen en cirka 44,9 ms forsinkelse ved 44,1 kHz. AVFoundation/MP4-importeret PCM og ALAC får nu korrigeret AAC-præsentationen med encoderens faktiske indledende frames. Eksisterende bevidste pauser og trim bevares.

## Verificering

- 15 deterministiske køchecks består. De observerede fejl blev reproduceret før rettelserne.
- 38 lydkonverterings-/tidslinjetests består mod den endelige signerede build 3-pakke: PCM, ALAC og AAC; mono, stereo og 5.1; 32/44,1/48 kHz; bevarede kanaler og eksplicit 5.1→stereo; +250/-100 ms ALAC-tidslinjer.
- Uafhængige toner pr. kanal efterprøver kanalidentitet, nedmixningsbidrag og uønsket krydstale. Output skal være AAC. Start og slut kontrolleres inden for 15 ms på de kontinuerte testfiler; det er ikke en påstand om sample-præcis timing.
- Direkte dekoderchecks: 24- og 36-byte ALAC-konfiguration accepteres; en ugyldig 23-byte konfiguration afvises. Original build 2 fejlede på den gyldige 24-byte konfiguration. ALAC-testfilen blev også afkodet byte-identisk til original PCM med Apples dekoder.
- Hele den eksisterende målrettede regressionstest består: identitet, app-korrekthed, kø, pakning, kildeverifikation, arm64-opskrift, OCR-sti, framework-baseline, OCR, FFmpeg, lyd-baseline, lydkorrekthed, lagringsfejl og FIFO.
- Release-bygning, lokal signering og streng signaturkontrol er gennemført. Alle syv indbyggede programmer/biblioteker er arm64. Den færdige app er startet manuelt og viser version 1.0 (3).
- Uafhængig kodegennemgang fandt ingen uløste regressioner i kø- eller ALAC-rettelserne. Timinggennemgangen afgrænsede rettelsen som beskrevet nedenfor.

## Afgrænsning og åbne punkter

Timingrettelsen omfatter de testede AVFoundation/MP4-veje med tabsfri kilder. Matroska konstruerer tidslinjer anderledes; den vej er bevidst uændret, da en generel forskydning kunne skabe for lange edits. Det er et åbent punkt, som kræver en særskilt MKV-testfil. Andre komprimerede kilders eksisterende timingpolitik er ikke ændret.

Kort syntetisk lyd er ikke fuld gennemlytning, audiovisuel læbesynkronisering, surroundhardwaretest, lange filer eller alle codecs. Køens mediearbejde kontrolleres med en test-double; de eksisterende dekoder/encoder-tests efterprøver desuden annullering på blokeret input. Fysisk macOS 13-test er fortsat åben.

Det tidligere accepterede ikon er brugt i pakken. En separat lokal ikonjustering i arbejdsprojektet er bevaret og ikke medtaget i denne kodeændring. PGS-OCR-forbedringer og yderligere målt optimering er stadig separate faser. Testudgaven er lokalt signeret, ikke notariseret; egen automatisk opdatering er fortsat deaktiveret.

Kildekode, tests og dokumentation vedligeholdes på grenen `neo/apple-silicon` i NickLauritzenDK/Subler og NickLauritzenDK/MP42Foundation. Framework-versionen er fastlåst i appens submodule-reference.
