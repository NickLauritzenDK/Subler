#!/usr/bin/env python3
"""Run the complete production Queue with deterministic item/file boundaries.

Foundation dispatch, archiving, notifications and the Queue state machine are
real. Item processing uses a controlled double so cancellation can be triggered
at exact boundaries without touching user media, data or preferences.
"""
from pathlib import Path
import subprocess,tempfile
ROOT=Path(__file__).resolve().parents[1]
source=(ROOT/'Classes/Queue.swift').read_text()
fixture=r'''
import Foundation
import IOKit.pwr_mgt
final class Logger {
 static let shared=Logger()
 func writeError(toLog: Error) {}
 func write(toLog: String) {}
}
final class QueueItem: NSObject,NSSecureCoding {
 enum Status { case ready,editing,working,completed,failed,cancelled }
 static var supportsSecureCoding: Bool { true }
 var status: Status = .ready
 let fileURL=URL(fileURLWithPath:"/synthetic-queue-fixture")
 var localizedWorkingDescription: String?
 weak var delegate: Queue?
 var operation: () throws -> Void = {}
 private(set) var calls=0
 override init() { super.init() }
 required init?(coder: NSCoder) { super.init() }
 func encode(with coder: NSCoder) {}
 func process() throws { calls += 1; try operation() }
 func cancel() {}
}
extension Queue {
 func suspendWorkerForTest() {workQueue.suspend()}
 func resumeWorkerForTest() {workQueue.resume()}
}
struct ExpectedFailure: Error {}
func require(_ condition: @autoclosure () -> Bool,_ label: String) {
 if !condition() { print("FAIL: \(label)"); failures += 1 }
 else { print("PASS: \(label)") }
}
func awaitSignal(_ semaphore: DispatchSemaphore,_ label: String) {
 require(semaphore.wait(timeout:.now()+5) == .success,label)
}
var failures=0
let temp=FileManager.default.temporaryDirectory.appendingPathComponent(UUID().uuidString)
try FileManager.default.createDirectory(at:temp,withIntermediateDirectories:true)
defer { try? FileManager.default.removeItem(at:temp) }
func makeQueue(_ name: String) -> (Queue,QueueItem,QueueItem) {
 let q=Queue(url:temp.appendingPathComponent(name));let a=QueueItem(),b=QueueItem()
 q.append(a);q.append(b);return(q,a,b)
}
// Stop before the worker starts must not claim or process any ready item.
do {
 let(q,a,b)=makeQueue("before-worker");let finished=DispatchSemaphore(value:0)
 let completed=NotificationCenter.default.addObserver(forName:Queue.Completed,object:nil,queue:nil) { note in
  if let owner=note.object as? Queue,owner === q {finished.signal()}
 }
 q.suspendWorkerForTest();q.start();q.stop();q.resumeWorkerForTest()
 awaitSignal(finished,"stopped pending worker exits")
 require(a.calls == 0 && b.calls == 0 && a.status == .ready && b.status == .ready,"stop before worker starts preserves all ready items")
 NotificationCenter.default.removeObserver(completed)
}
// A synchronous observer gives a deterministic boundary between completed work
// and selecting the next item. A stop must preserve that next item as ready.
do {
 let(q,a,b)=makeQueue("between-items");let finished=DispatchSemaphore(value:0)
 let working=NotificationCenter.default.addObserver(forName:Queue.Working,object:nil,queue:nil) { note in
  if let owner=note.object as? Queue,owner === q,(note.userInfo?["Progress"] as? Double)==100 {q.stop()}
 }
 let completed=NotificationCenter.default.addObserver(forName:Queue.Completed,object:nil,queue:nil) { note in
  if let owner=note.object as? Queue,owner === q {finished.signal()}
 }
 q.start();awaitSignal(finished,"stop between items completes the queue")
 require(a.status == .completed && a.calls == 1,"completed item remains completed")
 require(b.status == .ready && b.calls == 0,"stop between items never starts the next item")
 NotificationCenter.default.removeObserver(working)
 q.start();awaitSignal(finished,"queue can restart after stop")
 require(b.status == .completed && b.calls == 1,"restart processes remaining ready item exactly once")
 NotificationCenter.default.removeObserver(completed)
}
// A media writer may throw while responding to cancellation. This must remain
// cancellation rather than a failed-item notification and misleading error.
do {
 let(q,a,b)=makeQueue("throw-on-cancel");let entered=DispatchSemaphore(value:0),release=DispatchSemaphore(value:0),finished=DispatchSemaphore(value:0)
 a.operation={entered.signal();_ = release.wait(timeout:.now()+5);throw ExpectedFailure()}
 var failureNotifications=0,cancelNotifications=0
 let failed=NotificationCenter.default.addObserver(forName:Queue.Failed,object:nil,queue:nil) { note in
  if let owner=note.object as? Queue,owner === q {failureNotifications += 1}
 }
 let cancelled=NotificationCenter.default.addObserver(forName:Queue.Cancelled,object:nil,queue:nil) { note in
  if let owner=note.object as? Queue,owner === q {cancelNotifications += 1}
 }
 let completed=NotificationCenter.default.addObserver(forName:Queue.Completed,object:nil,queue:nil) { note in
  if let owner=note.object as? Queue,owner === q {finished.signal()}
 }
 q.start();awaitSignal(entered,"processing begins before stop");q.stop();release.signal();awaitSignal(finished,"throwing cancellation completes")
 require(a.status == .cancelled,"cancelled writer exception leaves cancelled status")
 require(failureNotifications == 0 && cancelNotifications == 1,"cancellation emits one cancellation and no failure")
 require(b.status == .ready && b.calls == 0,"cancelled conversion leaves following item ready")
 for token in [failed,cancelled,completed] {NotificationCenter.default.removeObserver(token)}
}
// Ordinary failure must still be reported and must not cancel later work.
do {
 let(q,a,b)=makeQueue("ordinary-failure");let finished=DispatchSemaphore(value:0);a.operation={throw ExpectedFailure()};var failureNotifications=0
 let failed=NotificationCenter.default.addObserver(forName:Queue.Failed,object:nil,queue:nil) { note in
  if let owner=note.object as? Queue,owner === q {failureNotifications += 1}
 }
 let completed=NotificationCenter.default.addObserver(forName:Queue.Completed,object:nil,queue:nil) { note in
  if let owner=note.object as? Queue,owner === q {finished.signal()}
 }
 q.start();q.start();awaitSignal(finished,"ordinary failure allows queue completion")
 require(a.status == .failed && failureNotifications == 1,"ordinary writer failure stays failed and is reported once")
 require(a.calls == 1 && b.calls == 1 && b.status == .completed,"ordinary failure continues and duplicate start does not duplicate processing")
 for token in [failed,completed] {NotificationCenter.default.removeObserver(token)}
}
if failures>0 {exit(1)}
print("ALL QUEUE CANCELLATION CHECKS PASSED")
'''
with tempfile.TemporaryDirectory(prefix='neo-queue-test-') as temp:
 temp=Path(temp);swift=temp/'main.swift';swift.write_text(source+'\n'+fixture);exe=temp/'queue-test'
 subprocess.run(['xcrun','swiftc','-module-cache-path',str(temp/'module-cache'),'-swift-version','5',str(swift),'-o',str(exe)],check=True)
 subprocess.run([str(exe)],check=True,timeout=30)
