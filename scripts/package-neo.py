#!/usr/bin/env python3
"""Prepare and locally sign an Apple Silicon-only Neo app without cloud metadata."""
from pathlib import Path
import argparse,hashlib,json,os,plistlib,shutil,subprocess,tempfile
MACHO_MAGIC={bytes.fromhex(x) for x in ['feedface','cefaedfe','feedfacf','cffaedfe','cafebabe','bebafeca','cafebabf','bfbafeca']}
def thin_bundle(app):
    architectures=[]
    for path in sorted(app.rglob('*')):
        if path.is_symlink() or not path.is_file():continue
        with path.open('rb') as f:magic=f.read(4)
        if magic not in MACHO_MAGIC:continue
        archs=subprocess.check_output(['lipo','-archs',str(path)],text=True).split()
        if 'arm64' not in archs:raise RuntimeError(f'Missing arm64 code in {path.relative_to(app)}: {archs}')
        if archs!=['arm64']:
            replacement=path.with_name(path.name+'.neo-thin')
            try:
                subprocess.run(['lipo',str(path),'-thin','arm64','-output',str(replacement)],check=True)
                shutil.copystat(path,replacement);os.replace(replacement,path)
            finally:replacement.unlink(missing_ok=True)
        architectures.append(str(path.relative_to(app)))
    if not architectures:raise RuntimeError('No arm64 Mach-O code found')
    return architectures

def validate_dependencies(app, entries):
    """Reject development-library references that cannot be loaded from the bundle."""
    app=app.resolve()
    for entry in entries:
        binary=app/entry
        commands=subprocess.check_output(['otool','-l',str(binary)],text=True)
        for block in commands.split('Load command ')[1:]:
            lines=block.splitlines()
            command=next((line.strip().split()[-1] for line in lines if line.strip().startswith('cmd ')), '')
            if command not in {'LC_LOAD_DYLIB','LC_LOAD_WEAK_DYLIB','LC_REEXPORT_DYLIB','LC_LOAD_UPWARD_DYLIB','LC_LAZY_LOAD_DYLIB'}:continue
            name=next(line.strip()[5:].split(' (offset ')[0] for line in lines if line.strip().startswith('name '))
            if name.startswith(('/usr/lib/','/System/Library/')):continue
            if name.startswith('@rpath/'):
                suffix=name[len('@rpath/'):]
                candidates=[path for path in app.rglob(Path(suffix).name) if path.as_posix().endswith('/'+suffix)]
            elif name.startswith('@loader_path/'):
                candidates=[binary.parent/name[len('@loader_path/'):]]
            elif name.startswith('@executable_path/'):
                container=next(parent for parent in binary.parents if parent.suffix in {'.app','.xpc'})
                candidates=[container/'Contents/MacOS'/name[len('@executable_path/'):]]
            else:candidates=[Path(name)]
            valid=False
            for candidate in candidates:
                try:
                    candidate.resolve().relative_to(app)
                    valid=candidate.is_file()
                except ValueError:continue
                if valid:break
            if not valid:raise RuntimeError(f'Unbundled dependency {name} referenced by {entry}')

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('app',type=Path);p.add_argument('archive',type=Path);a=p.parse_args()
    source=a.app.resolve();archive=a.archive.resolve();archive.parent.mkdir(parents=True,exist_ok=True)
    info=plistlib.loads((source/'Contents/Info.plist').read_bytes())
    if info.get('CFBundleIdentifier')!='dk.nicklauritzen.SublerNeo':raise RuntimeError('Refusing to package a different application identity')
    if info.get('SUFeedURL') or info.get('SUPublicEDKey'):raise RuntimeError('Neo update channel is not configured; upstream feed/key must be absent')
    # Retain this clean signed copy for local verification. iCloud resource-fork
    # metadata must not enter the signing input or distribution archive.
    folder=Path(tempfile.mkdtemp(prefix='subler-neo-',dir='/private/tmp'));app=folder/'Subler Neo.app'
    subprocess.run(['ditto','--norsrc','--noextattr','--noqtn',str(source),str(app)],check=True)
    subprocess.run(['xattr','-cr',str(app)],check=True)
    entries=thin_bundle(app)
    validate_dependencies(app,entries)
    subprocess.run(['codesign','--force','--deep','--sign','-',str(app)],check=True)
    subprocess.run(['codesign','--verify','--deep','--strict',str(app)],check=True)
    subprocess.run(['ditto','-c','-k','--sequesterRsrc','--keepParent',str(app),str(archive)],check=True)
    manifest={'app':str(app),'architecture':'arm64','mach_o_files':entries,'bundle_identifier':info['CFBundleIdentifier'],'version':info.get('CFBundleShortVersionString'),'build':info.get('CFBundleVersion'),'signing':'local ad-hoc; not notarized','archive_sha256':hashlib.sha256(archive.read_bytes()).hexdigest()}
    archive.with_suffix('.json').write_text(json.dumps(manifest,indent=2)+'\n')
    print(str(app))
if __name__=='__main__':main()
