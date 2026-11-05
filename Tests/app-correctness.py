#!/usr/bin/env python3
"""Run actual app method bodies against controlled file/network/UI boundaries.
No project/framework build needed. UI and MP42 boundaries are lightweight doubles;
Foundation archiving, disk writes, HTTP and dispatch remain real.
"""
from pathlib import Path
import subprocess, tempfile, threading, http.server
ROOT = Path(__file__).resolve().parents[1]
def block(file, signature):
    source = (ROOT / 'Classes' / file).read_text()
    start = source.index(signature)
    opening = source.index('{', start)
    depth = 1
    i = opening + 1
    while depth:
        depth += (source[i] == '{') - (source[i] == '}')
        i += 1
    return source[start:i]
class Handler(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        status = 404 if self.path.startswith('/missing/') else 200
        model = (ROOT / 'MP42Foundation/contrib/Tesseract/share/tessdata/eng.traineddata').read_bytes()
        payload = model if self.path.startswith(('/valid/', '/missing/')) else b'<html>server error</html>'
        if self.path.startswith('/truncated/'): payload = model[:100]
        if self.path.startswith('/badOffset/'): payload = bytes([1,0,0,0,255,255,255,255,255,255,255,127,42])
        self.send_response(status); self.end_headers(); self.wfile.write(payload)
    def log_message(self, *args): pass
server = http.server.ThreadingHTTPServer(('127.0.0.1', 0), Handler)
threading.Thread(target=server.serve_forever, daemon=True).start()
preamble = r'''
import Foundation
class NSWindowController {}
class NSDocument: NSObject {
 enum SaveOperationType { case saveOperation, saveAsOperation, other }
 var windowControllers: [NSWindowController] = []
 override init() { super.init() }
 init(contentsOf: URL, ofType: String) throws { super.init() }
 func writeSafely(to: URL, ofType: String, for: SaveOperationType) throws {}
 func makeWindowControllers() {}; func showWindows() {}
}
class NSDocumentController {
 static let shared = NSDocumentController()
 func addDocument(_ document: NSDocument) {}
}
let kMP42MediaType_Audio = "audio", kMP42MediaType_Subtitle = "subtitle", kMP42MediaType_ClosedCaption = "caption"
enum QueueActionType { case pre, post }
protocol QueueActionProtocol: NSSecureCoding {}
struct TestError: Error {}
class Track {
 let mediaType: String; let alternateGroup: Int; let language: String
 var mediaCharacteristicTags: Set<String>; var isEnabled: Bool
 init(_ type: String, _ group: Int, _ language: String, _ enabled: Bool, _ main: Bool = false) {
 self.mediaType=type; alternateGroup=group; self.language=language; isEnabled=enabled
 mediaCharacteristicTags = main ? ["public.main-program-content"] : []
 }
}
class MP4 {
 var tracks: [Track] = []; var optimizeResult = false; var saved = false
 func organizeAlternateGroups() {}; func inferTracksLanguages() {}; func inferMediaCharacteristics() {}
 func update(options: [String:Any]) throws { saved = true }
 func write(to: URL, options: [String:Any]) throws { saved = true }
 func optimize() -> Bool { optimizeResult }
}
class QueueItem: NSObject, NSSecureCoding {
 enum Status { case ready, working, completed, failed }
 var status: Status = .ready; var mp4File: MP4?; var failPrepare = false
 var destURL = URL(fileURLWithPath: "/missing")
 func prepare() throws { if failPrepare { throw TestError() } }
 static var supportsSecureCoding: Bool { true }
 func encode(with coder: NSCoder) {}
 required init?(coder: NSCoder) {}
 override init() {}
}
class Queue {
 let arrayQueue = DispatchQueue(label: "test.store"); var items: [QueueItem] = []; let url: URL
 init(_ url: URL) { self.url = url }
 func index(of item: QueueItem) -> Int { items.firstIndex(where: { $0 === item }) ?? -1 }
'''
pieces = [preamble, block('Queue.swift', '    func saveToDisk() throws'), r'''
}
class Document: NSDocument {
 var mp4 = MP4(); var optimize = true; var cancelled = false; var options: [String:Any] = [:]
 override init() { super.init() }
 init(mp4: MP4) { super.init(); self.mp4 = mp4 }
 override init(contentsOf: URL, ofType: String) throws { super.init(); throw TestError() }
 func unblockUserInteraction() {}; func preventSleep() {}; func allowSleep() {}
''', block('Document.swift', '    override func writeSafely('), r'''
}
class DocumentWindowController: NSWindowController { func setProgress(title: String) {} }
struct Prefs { static let organizeAlternateGroups = false; static let inferMediaCharacteristics = false }
class Popover { func close() {} }
class QueueController {
 let queue: Queue; var itemPopover: Popover?; var errors = 0; var refreshes = 0
 init(_ queue: Queue) { self.queue=queue }
 func updateUI(indexes: IndexSet) { refreshes += 1 }
 func presentError(_ error: Error) { errors += 1 }
 func remove(at: Int) { queue.items.remove(at: at) }
 func updateState() {}
''', block('QueueController.swift', '    internal func edit('), '\n}\n', block('QueueAction.swift', 'class QueueChangeAudioLanguageAction'), '\n', block('QueueAction.swift', 'class QueueChangeSubtitleLanguageAction'), '\n', r'''
class MP42Languages {
 static let defaultManager = MP42Languages()
 func localizedLang(forExtendedTag: String) -> String { forExtendedTag }
}
''', block('OCRManager.swift', 'final class OCRLanguage'), r'''
URLCache.shared = URLCache(memoryCapacity: 0, diskCapacity: 0, diskPath: nil)
var failures = 0
func check(_ condition: @autoclosure () -> Bool, _ name: String) {
 if condition() { print("PASS \(name)") } else { print("FAIL \(name)"); failures += 1 }
}
func wait(_ condition: () -> Bool) {
 let until = Date().addingTimeInterval(3)
 while !condition() && Date() < until { RunLoop.current.run(until: Date().addingTimeInterval(0.01)) }
}
let root = FileManager.default.temporaryDirectory.appendingPathComponent(UUID().uuidString)
try FileManager.default.createDirectory(at: root, withIntermediateDirectories: true)
defer { try? FileManager.default.removeItem(at: root) }
for type in [kMP42MediaType_Audio, kMP42MediaType_Subtitle] {
 let item=QueueItem(); let mp4=MP4(); item.mp4File=mp4
 mp4.tracks = [Track(type, 1, "en", false), Track(type, 1, "da", true), Track(type, 2, "en", false), Track(type, 2, "da", true), Track(type, 3, "fr", true)]
 if type == kMP42MediaType_Audio { _ = QueueChangeAudioLanguageAction(language:"en").runAction(item) }
 else { _ = QueueChangeSubtitleLanguageAction(language:"en").runAction(item) }
 check(mp4.tracks.map(\.isEnabled) == [true,false,true,false,true], "\(type) keeps one match in EACH group and preserves unmatched group")
}
let queue = Queue(root.appendingPathComponent("queue")); queue.items = [QueueItem()]
do { try queue.saveToDisk(); check(FileManager.default.fileExists(atPath: queue.url.path), "queue persists valid archive") }
catch { check(false, "queue persists valid archive") }
let badQueue = Queue(root) // Existing directory cannot be replaced by an archive.
do { try badQueue.saveToDisk(); check(false, "queue write error reaches caller") }
catch { check(true, "queue write error reaches caller") }
for scenario in ["prepare", "completed", "missingMP4"] {
 let item = QueueItem(); item.failPrepare = scenario == "prepare"; item.status = scenario == "completed" ? .completed : .ready
 let original = item.status; queue.items = [item]; let controller = QueueController(queue)
 controller.edit(item: item)
 wait { controller.errors > 0 || item.status != .working }
 // Allow any accidentally scheduled second stage to run too.
 RunLoop.current.run(until: Date().addingTimeInterval(0.05))
 check(item.status == original && queue.items.count == 1 && controller.refreshes >= 2 && controller.errors == 1, "edit \(scenario) restores job, refreshes UI and reports once")
}
let document=Document()
do { try document.writeSafely(to: root.appendingPathComponent("movie"), ofType:"", for:.saveAsOperation); check(false,"save reports failed optimization") }
catch { check(document.mp4.saved && !document.optimize, "save reports failed optimization") }
document.optimize=true; document.mp4.optimizeResult=true
do { try document.writeSafely(to: root.appendingPathComponent("movie"), ofType:"", for:.saveAsOperation); check(true,"save permits successful optimization") }
catch { check(false,"save permits successful optimization") }
''', f'let baseURL = URL(string:"http://127.0.0.1:{server.server_port}")!\n', r'''
for route in ["missing", "html", "truncated", "badOffset", "valid"] {
 let directory=root.appendingPathComponent(route); try FileManager.default.createDirectory(at:directory,withIntermediateDirectories:true)
 if route == "valid" { try Data("<html>old error</html>".utf8).write(to: directory.appendingPathComponent("eng.traineddata")) }
 let language=OCRLanguage(langCode:"en",name:"eng.traineddata"); var result: Result<URL, Error>?
 _ = language.startDownload(from:baseURL.appendingPathComponent(route),to:directory) { result=$0 }
 wait { result != nil }
 if route == "valid" {
  if case .success? = result { check(language.status == .downloaded,"OCR installs valid model") } else { check(false,"OCR installs valid model") }
 } else {
  if case .failure? = result { check(language.status == .available && !FileManager.default.fileExists(atPath:directory.appendingPathComponent(language.name).path),"OCR rejects \(route) without installing") } else { check(false,"OCR rejects \(route) without installing") }
 }
}
let corrupt=OCRLanguage(langCode:"en",name:"corrupt.traineddata")
try Data("<html>oops</html>".utf8).write(to:root.appendingPathComponent(corrupt.name))
corrupt.checkIfDownloaded(root)
check(corrupt.status == .available,"OCR does not mark existing error page downloaded")
let editable=QueueItem(); editable.mp4File=MP4(); queue.items=[editable]
let editor=QueueController(queue); editor.edit(item:editable)
wait { queue.items.isEmpty }
check(queue.items.isEmpty && editable.status == .ready && editor.errors == 0,"successful edit removes job after document opens")
exit(failures == 0 ? 0 : 1)
''']
with tempfile.TemporaryDirectory(prefix='subler-app-tests-') as directory:
    source = Path(directory) / 'main.swift'; source.write_text('\n'.join(pieces))
    binary = Path(directory) / 'tests'
    subprocess.run(['swiftc', '-module-cache-path', str(Path(directory) / 'cache'), '-swift-version', '5', str(source), '-o', str(binary)], check=True)
    result = subprocess.run([str(binary)])
server.shutdown()
raise SystemExit(result.returncode)
