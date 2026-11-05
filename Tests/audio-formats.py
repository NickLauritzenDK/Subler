#!/usr/bin/env python3
"""Independent synthetic PCM/ALAC/AAC -> AAC channel/rate/duration/pitch checks.

Usage: python3 Tests/audio-formats.py APP_OR_FRAMEWORK EVIDENCE_DIRECTORY
Requires macOS, Xcode command line tools, afconvert; no third party packages.
All subprocess output and generated inputs/outputs are retained for diagnosis.
"""
import argparse, array, json, math, pathlib, platform, struct, subprocess, sys, wave
p=argparse.ArgumentParser(description=__doc__)
p.add_argument('framework', type=pathlib.Path)
p.add_argument('output', type=pathlib.Path)
a=p.parse_args(); root=pathlib.Path(__file__).resolve().parent
out=a.output.resolve(); out.mkdir(parents=True,exist_ok=True)
fw=a.framework.resolve()
if fw.suffix=='.json': fw=pathlib.Path(json.loads(fw.read_text())['app'])
if fw.suffix=='.app': fw=fw/'Contents/Frameworks/MP42Foundation.framework'
log=(out/'commands.log').open('w'); results=[]
def run(args,timeout=90):
    log.write('$ '+repr([str(x) for x in args])+'\n'); log.flush()
    r=subprocess.run([str(x) for x in args],stdout=log,stderr=log,timeout=timeout)
    log.flush()
    if r.returncode: raise RuntimeError(f'command exited {r.returncode}: {args[0]} (see commands.log)')
exe=out/'audio-formats-probe'
run(['xcrun','clang','-arch',platform.machine(),'-fobjc-arc','-Wl,-headerpad_max_install_names','-F'+str(fw.parent),'-framework','MP42Foundation','-framework','AppKit','-framework','AVFoundation','-framework','CoreMedia',root/'audio-formats.m','-o',exe])
deps=subprocess.check_output(['otool','-L',str(exe)],text=True)
old=next(x.strip().split(' (')[0] for x in deps.splitlines() if 'MP42Foundation.framework/' in x)
run(['install_name_tool','-change',old,fw/'Versions/A/MP42Foundation',exe]);run(['codesign','-f','-s','-',exe])
run([exe,'--decoder-cookies'])
def read_wav(path):
    raw=path.read_bytes(); pos=12; chunks={}
    while pos+8<=len(raw):
        kind=raw[pos:pos+4]; n=struct.unpack_from('<I',raw,pos+4)[0]
        chunks[kind]=raw[pos+8:pos+8+n];pos+=8+n+(n%2)
    _,ch,rate,_,_,bits=struct.unpack_from('<HHIIHH',chunks[b'fmt ']); assert bits==16
    data=array.array('h');data.frombytes(chunks[b'data'])
    if sys.byteorder!='little': data.byteswap()
    return ch,rate,data
# WAV channel order: L R C LFE Ls Rs. LFE stays below its 120 Hz cutoff.
freqs=(431,617,829,71,1051,1277)
def magnitude(samples,rate,freq):
    # Single-frequency projection over a stable 0.5 second interior window.
    re=sum(x*math.cos(2*math.pi*freq*i/rate) for i,x in enumerate(samples))
    im=sum(x*math.sin(2*math.pi*freq*i/rate) for i,x in enumerate(samples))
    return 2*math.hypot(re,im)/len(samples)
def active_window(data,channels,rate):
    """Locate generated 0..1.8s tone using independent 5ms RMS windows.

    Frame duration alone cannot detect an encoder delay hidden inside a valid
    length edit. A 500-unit threshold rejects low-level AAC pre/post ringing.
    """
    samples=data[::channels]; width=max(1,round(rate*.005)); active=[]
    for start in range(0,len(samples)-width+1,width):
        block=samples[start:start+width]
        if math.sqrt(sum(x*x for x in block)/width)>500:
            active.append(start)
    return dict(onset_seconds=active[0]/rate if active else None,
                end_seconds=(active[-1]+width)/rate if active else None,
                rms_window_frames=width, rms_threshold=500)

for rate in (32000,44100,48000):
 for channels in (1,2,6):
    source=out/f'pcm-{channels}ch-{rate}.wav'; n=2*rate+137
    with wave.open(str(source),'wb') as w:
        w.setparams((channels,2,rate,0,'NONE',''))
        w.writeframes(b''.join(struct.pack('<'+'h'*channels,*[round(3500*math.sin(2*math.pi*f*i/rate)) if i<rate*1.8 else 0 for f in freqs[:channels]]) for i in range(n)))
    for codec in ('pcm','alac','aac'):
        inp=source
        if codec!='pcm':
            inp=out/f'{codec}-{channels}ch-{rate}.m4a';inp.unlink(missing_ok=True)
            try: run(['afconvert','-f','m4af','-d',codec]+(['-l','MPEG_5_1_A','-l', 'MPEG_5_1_D' if codec=='aac' else 'MPEG_5_1_A'] if channels==6 else [])+[source,inp])
            except Exception as e:
                results.append(dict(case=inp.stem,status='FAIL',errors=[f'fixture generation: {e}']));continue
        for mode in (('preserve','stereo') if channels==6 else ('preserve',)):
            case=f'{codec}-{channels}ch-{rate}-{mode}';target=out/f'{case}.mp4';decoded=out/f'{case}-decoded.wav'
            target.unlink(missing_ok=True);decoded.unlink(missing_ok=True); errors=[]; details={}
            try:
                run([exe,inp,target,mode]);run(['afconvert','-f','WAVE','-d','LEI16']+(['-l','MPEG_5_1_A'] if channels==6 and mode=='preserve' else [])+[target,decoded])
                meta=json.loads(pathlib.Path(str(target)+'.json').read_text());ch,rr,data=read_wav(decoded)
                expected_ch=2 if mode=='stereo' else channels
                assert len(meta['input'])==len(meta['output'])==1, 'expected one imported/output audio track'
                it,ot=meta['input'][0],meta['output'][0]
                for label,actual,expected in [('output codec',ot['format'],0x61616320),('import channels',it['channels'],channels),('import timebase',it['timescale'],rate),('output channels',ot['channels'],expected_ch),('decoded channels',ch,expected_ch),('output timebase',ot['timescale'],rate),('decoded rate',rr,rate)]:
                    if actual!=expected: errors.append(f'{label}: {actual}, expected {expected}')
                # AAC MP4 inventory includes packet padding/2112 encoder priming frames.
                # Decoded duration must still match the original valid PCM frames.
                metadata_expected=math.ceil((n+2112)/1024)*1024/rate if codec=='aac' else n/rate
                for label,duration,expected,tolerance in [('import',it['duration_ms']/1000,metadata_expected,.002 if codec=='aac' else .075),('output',ot['duration_ms']/1000,it['duration_ms']/1000,.025),('decoded',len(data)/ch/rr,n/rate,1024/rate+.002)]:
                    if abs(duration-expected)>tolerance: errors.append(f'{label} duration {duration:.6f}, expected {expected:.6f}')
                timing=active_window(data,ch,rr)
                if timing['onset_seconds'] is None:
                    errors.append('no audible synthetic tone detected')
                else:
                    if abs(timing['onset_seconds'])>.015:
                        errors.append(f"tone onset {timing['onset_seconds']:.6f}s, expected 0 within15ms")
                    if abs(timing['end_seconds']-1.8)>.015:
                        errors.append(f"tone end {timing['end_seconds']:.6f}s, expected1.8 within15ms")
                levels=[]
                for c in range(ch):
                    samples=data[c::ch][rr//2:rr]
                    amps=[round(magnitude(samples,rr,f),2) for f in freqs[:channels]];levels.append(amps)
                    if mode=='preserve' and c<channels:
                        if amps[c]<500 or amps[c]<max([v for j,v in enumerate(amps) if j!=c] or [0])*4:
                            errors.append(f'channel {c} expected dominant {freqs[c]} Hz: {amps}')
                if mode=='stereo':
                    # L/R identity plus center and surround contribution; LFE inclusion is implementation-dependent.
                    for c,required in ((0,(0,2,4)),(1,(1,2,5))):
                        for j in required:
                            if levels[c][j]<150: errors.append(f'downmix channel {c} missing {freqs[j]} Hz: {levels[c]}')
                    # A duplicated mono mix or swapped/crossfed channels must fail.
                    for c,forbidden in ((0,(1,5)),(1,(0,4))):
                        limit=max(100,max(levels[c])*.1)
                        for j in forbidden:
                            if levels[c][j]>limit: errors.append(f'downmix channel {c} unexpected crossfeed {freqs[j]} Hz: {levels[c]}')
                details=dict(metadata=meta,decoded_channels=ch,decoded_rate=rr,duration=len(data)/ch/rr,tone_amplitudes=levels,active_window=timing)
            except Exception as e: errors.append(str(e))
            result=dict(case=case,status='FAIL' if errors else 'PASS',errors=errors,**details);results.append(result)
            print(case,result['status'], '; '.join(errors),flush=True)
# Edited ALAC sources exercise empty and nonempty edit preservation separately
# from the continuous matrix. Offsets are milliseconds in MP42Track's API.
for offset_ms in (250,-100):
    case=f'alac-edited-{offset_ms}ms';inp=out/f'{case}.m4a';target=out/f'{case}.mp4';decoded=out/f'{case}.wav';errors=[];details={}
    for path in (inp,target,decoded):path.unlink(missing_ok=True)
    try:
        run([exe,'--make-offset',out/'alac-2ch-44100.m4a',inp,str(offset_ms)])
        run([exe,inp,target,'preserve']);run(['afconvert','-f','WAVE','-d','LEI16',target,decoded])
        meta=json.loads(pathlib.Path(str(target)+'.json').read_text());ch,rr,data=read_wav(decoded)
        # afconvert can omit intentional edit gaps/trims; inspect the platform's
        # actual presentation timeline rather than treating raw decode as playback.
        timeline_path=out/f'{case}-timeline.json';run([exe,'--timeline',target,timeline_path]);segments=json.loads(timeline_path.read_text())
        audio=[segment for segment in segments if not segment['empty']]
        if len(audio)!=1:errors.append(f'expected one nonempty edited segment: {segments}')
        else:
            segment=audio[0]
            for label,actual,expected in [('target start',segment['start'],max(0,offset_ms/1000)),('media start',segment['source_start'],2112/44100+max(0,-offset_ms/1000)),('duration',segment['duration'],(2*44100+137)/44100+min(0,offset_ms/1000))]:
                if abs(actual-expected)>.003:errors.append(f'edited {label} {actual}, expected {expected}')
        if offset_ms>0 and not any(segment['empty'] and abs(segment['duration']-offset_ms/1000)<.003 for segment in segments):errors.append('intentional empty edit was lost')
        timing=active_window(data,ch,rr)
        expected_duration=(2*44100+137)/44100+offset_ms/1000
        if abs(meta['output'][0]['duration_ms']/1000-expected_duration)>.003:errors.append('edited presentation duration changed')
        if ch!=2 or rr!=44100:errors.append('edited channel/rate changed')
        details=dict(metadata=meta,timeline=segments,raw_decode_active_window=timing,decoded_frames=len(data)//ch)
    except Exception as e:errors.append(str(e))
    results.append(dict(case=case,status='FAIL' if errors else 'PASS',errors=errors,**details))
    print(case,results[-1]['status'],'; '.join(errors),flush=True)
report=dict(framework=str(fw),architecture=platform.machine(),tone_hz=freqs,results=results)
(out/'results.json').write_text(json.dumps(report,indent=2)+'\n'); log.close()
failures=sum(r['status']=='FAIL' for r in results)
print(f'{len(results)-failures}/{len(results)} passed; evidence: {out}')
sys.exit(bool(failures))
