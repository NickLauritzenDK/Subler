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
    """Validate bundled load commands in each executable's own run-path context.

    Follow LC_RPATH along dependency chains, rather than accepting a matching
    filename anywhere in the app. This is a conservative packaging preflight:
    explicit system references are allowed, but optional non-system libraries
    must still be bundled. Runtime/dlopen and OS compatibility tests remain
    separate checks.
    """
    app=app.resolve()
    images={}
    dependency_commands={'LC_LOAD_DYLIB','LC_LOAD_WEAK_DYLIB','LC_REEXPORT_DYLIB','LC_LOAD_UPWARD_DYLIB','LC_LAZY_LOAD_DYLIB'}
    for entry in entries:
        binary=(app/entry).resolve()
        binary.relative_to(app)
        output=subprocess.check_output(['otool','-hv','-l',str(binary)],text=True)
        header=next(line.split() for line in output.splitlines() if line.strip().startswith('MH_'))
        dependencies=[];runpaths=[]
        for block in output.split('Load command ')[1:]:
            lines=[line.strip() for line in block.splitlines()]
            command=next((line.split()[-1] for line in lines if line.startswith('cmd ')), '')
            if command in dependency_commands:
                dependencies.append(next(line[5:].split(' (offset ')[0] for line in lines if line.startswith('name ')))
            elif command=='LC_RPATH':
                runpaths.append(next(line[5:].split(' (offset ')[0] for line in lines if line.startswith('path ')))
        images[binary]=(header[4],dependencies,runpaths)

    def expand(name, binary, executable):
        for prefix,base in [('@loader_path',binary.parent),('@executable_path',executable.parent)]:
            if name==prefix:return base
            if name.startswith(prefix+'/'):return base/name[len(prefix)+1:]
        return Path(name) if name.startswith('/') else None

    reached=set();checked=set()
    def visit(binary, executable, inherited, chain):
        if binary in chain:return
        filetype,dependencies,runpaths=images[binary]
        paths=tuple(dict.fromkeys(path for name in runpaths if (path:=expand(name,binary,executable)) is not None))+inherited
        key=(binary,executable,paths)
        if key in checked:return
        checked.add(key);reached.add(binary)
        for name in dependencies:
            if name.startswith(('/usr/lib/','/System/Library/')):continue
            if name.startswith('@rpath/'):
                candidates=[path/name[len('@rpath/'):] for path in paths]
            else:
                path=expand(name,binary,executable)
                candidates=[] if path is None else [path]
            target=None
            for candidate in candidates:
                resolved=candidate.resolve()
                if not resolved.is_file():continue
                try:resolved.relative_to(app)
                except ValueError:
                    raise RuntimeError(f'External dependency {name} would be selected before bundled alternatives: {binary.relative_to(app)}')
                if resolved not in images:
                    raise RuntimeError(f'Dependency is not bundled Mach-O code: {name} referenced by {binary.relative_to(app)}')
                target=resolved;break
            if target is None:
                raise RuntimeError(f'Unbundled dependency {name} referenced by {binary.relative_to(app)} (executable {executable.relative_to(app)}; no reachable bundled library)')
            visit(target,executable,paths,chain|{binary})

    executables=[binary for binary,(filetype,_,_) in images.items() if filetype=='EXECUTE']
    if not executables:raise RuntimeError('No executable found for dependency validation')
    for executable in executables:visit(executable,executable,(),set())
    for binary in images:
        if binary not in reached:
            raise RuntimeError(f'No executable load context for bundled library {binary.relative_to(app)}')

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
