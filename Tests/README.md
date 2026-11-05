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
