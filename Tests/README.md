# App correctness regression tests

Run from the app repository:

```sh
python3 Tests/app-correctness.py
```

Requires macOS, Python 3, and the Xcode Swift compiler. The valid OCR fixture is
`MP42Foundation/contrib/Tesseract/share/tessdata/eng.traineddata` from the existing
framework dependency build. The test uses a temporary directory and loopback
HTTP server; it never accesses or alters the user's OCR languages or queue.

The runner extracts and compiles the actual production methods/classes from
QueueAction, Queue, QueueController, Document, and OCRManager. It does not assert
source text or duplicate the application logic. MP42 operations and document/UI
boundaries use small doubles; Foundation serialization, real failed atomic disk
writes, URLSession HTTP responses, file installation, and asynchronous dispatch
remain real. This tests controller decisions and state restoration, not AppKit
window rendering or real movie optimization. Run the full app build separately
to validate these methods against the actual framework/AppKit types.

Coverage:

- Preferred audio/subtitle choices persist independently in multiple alternate
  groups, while an unmatched group retains its original enabled track.
- Archive persistence succeeds normally and throws when its destination is a
  directory.
- Failed preparation, failed completed-document opening, and absent prepared
  media restore the queue status, retain the item, refresh the UI, and report one
  error. A successful edit still removes the queue item.
- A successful save followed by failed optimization throws; successful
  optimization permits completion.
- OCR rejects HTTP 404 even when its response contains real traineddata, HTML
  delivered with HTTP 200, a truncated container, and an impossible component
  offset. A real bundled model replaces an existing corrupt file atomically;
  existing HTML does not count as an installed language.

The model check validates the Tesseract component directory and file bounds in
both byte orders. It is not a complete semantic model parse or an OCR accuracy
test. The framework's OCR tests cover recognition separately.

## Queue cancellation

```sh
python3 Tests/queue-cancellation.py
```

Compiles the complete production Queue class with real Foundation notifications,
dispatch and archiving. Controlled item operations reproduce stop before work,
stop between files, a writer throwing after cancellation, restart, ordinary
failures and duplicate starts. Test-only worker suspension lives in an extension
of the test fixture; no production test hooks or user data are involved.

### Audio format conversion matrix

Run on macOS with normal AudioToolbox access:

```sh
python3 Tests/audio-formats.py /path/to/Subler.app /path/to/evidence-directory
```

The first argument also accepts an `MP42Foundation.framework` or Neo package JSON
containing the actual app path. The helper links the framework from that app;
it does not rebuild or substitute framework sources. Requires Xcode command line
tools and built-in `afconvert`; generates synthetic media without downloads.

36 continuous conversions cover PCM WAV, ALAC M4A and AAC M4A, mono/stereo/5.1, at
32/44.1/48 kHz. Each converts to AAC preserving channels; 5.1 additionally
converts with an explicit stereo mixdown. Checks cover imported/output track
count, channels, sample timebase, decoded sample rate and valid duration,
per-channel tone identity, and center/surround contributions to the downmix.
Explicit standard channel layouts avoid confusing native AAC order with WAV
order. The low-frequency channel uses 71 Hz; other channels have distinct tones.

AAC inventory duration is checked against whole 1024-frame packets including
Apple encoder's 2112-frame priming; decoded valid duration remains independently
checked against the generated source frames. Output inventory must preserve input
inventory duration within 25 ms. Decoded duration tolerance is one AAC packet (1024/rate seconds) plus 2 ms.
This detects a full 2112-frame priming loss at the tested rates; it does not
prove sample-accurate alignment or preservation of every end sample. Output
codec must be AAC, and stereo downmix also rejects excess opposite-side tones.
`commands.log`, JSON track/spectral measurements, fixtures, and decoded audio are
retained. A failed conversion or unavailable fixture codec fails the run.

This is short synthetic audio coverage on the host architecture, not long-file,
all-codec, audiovisual-sync, real-device, or listening-quality certification.

The matrix also verifies tone onset and ending within 15 ms using independent
5 ms RMS windows. Two additional ALAC cases retain intentional +250/-100 ms
presentation edits; these use AVFoundation's interpreted media timeline because
afconvert's raw decode can omit intentional edit gaps/trims. The helper also
checks actual decoder initialization with 24-byte and 36-byte ALAC configurations
and rejection of a malformed 23-byte configuration. Matroska timing is not covered.
