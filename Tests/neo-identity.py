#!/usr/bin/env python3
"""Execute production identity policy and validate update wiring."""
from pathlib import Path
import subprocess, tempfile, plistlib, xml.etree.ElementTree as ET
root = Path(__file__).resolve().parents[1]
source = (root/'Classes/Prefs.swift').read_text()
identity = source[source.index('enum AppIdentity {'):source.index('\nprivate let ud')]
with tempfile.TemporaryDirectory() as d:
    p = Path(d)/'main.swift'
    p.write_text('import Foundation\n'+identity+'''
let base = URL(fileURLWithPath: "/tmp/identity-test", isDirectory: true)
assert(AppIdentity.cacheURL(in: base).lastPathComponent == "dk.nicklauritzen.SublerNeo")
assert(AppIdentity.supportURL(in: base).path == "/tmp/identity-test/Subler Neo")
assert(AppIdentity.supportURL(in: base).path != base.appendingPathComponent("Subler").path)
let neo = UserDefaults(suiteName: AppIdentity.bundleIdentifier + ".test")!
let upstream = UserDefaults(suiteName: "org.subler.Subler.test")!
defer { neo.removePersistentDomain(forName: AppIdentity.bundleIdentifier + ".test"); upstream.removePersistentDomain(forName: "org.subler.Subler.test") }
upstream.set("original", forKey: "identity-test")
neo.set("neo", forKey: "identity-test")
assert(upstream.string(forKey: "identity-test") == "original")
neo.set(true, forKey: "SUEnableAutomaticChecks")
AppIdentity.configureUpdates(in: neo)
assert(!neo.bool(forKey: "SUEnableAutomaticChecks"))
assert(!neo.bool(forKey: "SUAutomaticallyUpdate"))
assert(!AppIdentity.updatesAvailable)
print("Neo identity behavior passed")
''')
    subprocess.run(['swift', '-module-cache-path', str(Path(d)/'module-cache'), str(p)],check=True)
info = plistlib.loads((root/'Info.plist').read_bytes())
assert 'SUFeedURL' not in info and 'SUPublicEDKey' not in info
assert info['MP42ApplicationSupportDirectoryName'] == 'Subler Neo'
assert info['SUEnableAutomaticChecks'] is False
for name in ['Logger', 'QueuePreferences', 'Preset', 'PresetManager', 'OCRManager']:
    code = (root / f'Classes/{name}.swift').read_text()
    assert 'AppIdentity.supportURL(in: $0)' in code
    assert 'appendingPathComponent("Subler"' not in code
menu = ET.parse(root/'Base.lproj/MainMenu.xib')
assert not any(e.get('customClass') == 'SPUStandardUpdaterController' for e in menu.iter())
action = next(e for e in menu.iter('action') if e.get('selector') == 'checkForUpdates:')
assert action.get('target') == '449'
print('Neo update wiring passed')
