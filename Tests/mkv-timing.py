#!/usr/bin/env python3
"""Deterministic lossless Matroska -> AAC presentation timing regression.

Usage: python3 Tests/mkv-timing.py APP_OR_FRAMEWORK OUTPUT_DIRECTORY
Uses real framework, macOS AAC encoder/decoder and AVFoundation. No downloads.
Fixtures follow https://www.matroska.org/technical/notes.html (unlaced blocks).
"""
import argparse,array,importlib.util,json,math,pathlib,platform,struct,subprocess,sys,wave
p=argparse.ArgumentParser(description=__doc__);p.add_argument('framework',type=pathlib.Path);p.add_argument('output',type=pathlib.Path);a=p.parse_args()
root=pathlib.Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('fixture',root/'matroska-fixture.py');fixture=importlib.util.module_from_spec(spec);spec.loader.exec_module(fixture)
out=a.output.resolve();out.mkdir(parents=True,exist_ok=True);fw=a.framework.resolve()
if fw.suffix=='.app':fw=fw/'Contents/Frameworks/MP42Foundation.framework'
log=(out/'commands.log').open('w')
def run(args):
 log.write(repr(list(map(str,args)))+'\n');log.flush()
 subprocess.run(list(map(str,args)),stdout=log,stderr=log,check=True,timeout=60)
exe=out/'probe'
run(['xcrun','clang','-arch',platform.machine(),'-fobjc-arc','-Wl,-headerpad_max_install_names','-F'+str(fw.parent),'-framework','MP42Foundation','-framework','AppKit','-framework','AVFoundation','-framework','CoreMedia',root/'audio-formats.m','-o',exe])
old=next(x.strip().split(' (')[0] for x in subprocess.check_output(['otool','-L',str(exe)],text=True).splitlines() if 'MP42Foundation.framework/' in x)
run(['install_name_tool','-change',old,fw/'Versions/A/MP42Foundation',exe]);run(['codesign','-f','-s','-',exe])
def decode(path):
 b=path.read_bytes();chunks={};i=12
 while i+8<=len(b):
  k=b[i:i+4];n=struct.unpack_from('<I',b,i+4)[0];chunks[k]=b[i+8:i+8+n];i+=8+n+n%2
 _,ch,rate,_,_,bits=struct.unpack_from('<HHIIHH',chunks[b'fmt ']);assert bits==16
 v=array.array('h');v.frombytes(chunks[b'data'])
 if sys.byteorder!='little':v.byteswap()
 return ch,rate,v

def edits(path):
 def walk(data):
  for k,v in fixture.boxes(data):
   if k==b'elst':
    version=v[0];n=struct.unpack_from('>I',v,4)[0];fmt='>Qqhh' if version else '>Iihh';size=struct.calcsize(fmt)
    return [struct.unpack_from(fmt,v,8+i*size)[:2] for i in range(n)]
   if k in (b'moov',b'trak',b'edts'):
    result=walk(v)
    if result is not None:return result
 return walk(path.read_bytes())
results=[]
for rate in (32000,44100,48000):
 source=out/f'{rate}.wav'
 with wave.open(str(source),'wb') as w:
  w.setparams((2,2,rate,0,'NONE',''));w.writeframes(b''.join(struct.pack('<hh',*[round(6000*math.sin(2*math.pi*431*i/rate)) if i<rate*1.8 else 0]*2) for i in range(rate*2)))
 alac=out/f'{rate}.m4a';alac.unlink(missing_ok=True);run(['afconvert','-f','m4af','-d','alac',source,alac])
 for codec in ('pcm','alac'):
  for offset in (0,250,1000):
   case=f'{codec}-{rate}-{offset}ms';inp=out/f'{case}.mkv';target=out/f'{case}.mp4';decoded=out/f'{case}.wav';timeline=out/f'{case}.json';errors=[];details={}
   try:
    if codec=='pcm':fixture.make(inp,rate,offset)
    else:fixture.make_alac(inp,alac,rate,offset)
    for path in (target,decoded,timeline):path.unlink(missing_ok=True)
    run([exe,inp,target,'preserve']);run([exe,'--timeline',target,timeline]);run(['afconvert','-f','WAVE','-d','LEI16',target,decoded])
    segments=json.loads(timeline.read_text());audio=[s for s in segments if not s['empty']];assert len(audio)==1,segments
    s=audio[0];ch,rr,v=decode(decoded);samples=v[::ch];width=round(rr*.005)
    active=[i/rr for i in range(0,len(samples)-width+1,width) if math.sqrt(sum(x*x for x in samples[i:i+width])/width)>500]
    assert active,'no tone'
    interior=samples[rr//2:rr];pitch=2*sum(x<=0<y for x,y in zip(interior,interior[1:]))
    if abs(pitch-431)>4:errors.append(f'pitch {pitch}, expected 431 Hz')
    for label,actual,expected,tol in [('presentation start',s['start'],offset/1000,.002),('presentation duration',s['duration'],2,1024/rate+.003),('tone onset',active[0],0,.015),('tone end',active[-1]+width/rr,1.8,.015),('rate',rr,rate,0),('channels',ch,2,0)]:
     if abs(actual-expected)>tol:errors.append(f'{label}: {actual}, expected {expected} +/- {tol}')
    if offset and not any(s['empty'] and abs(s['duration']-offset/1000)<.002 for s in segments):errors.append('missing intentional leading gap')
    details=dict(timeline=segments,raw_mp4_edits=edits(target),pitch_hz=pitch,tone_onset=active[0],tone_end=active[-1]+width/rr,decoded_duration=len(samples)/rr,expected_start=offset/1000,expected_duration=2)
   except Exception as e:errors.append(str(e))
   results.append(dict(case=case,status='FAIL' if errors else 'PASS',errors=errors,**details));print(case,results[-1]['status'],'; '.join(errors),flush=True)
report=dict(framework=str(fw),results=results,scope='PCM and ALAC lossless input; 32/44.1/48kHz stereo; 0/250/1000ms offset; platform timeline and decoded tone. Not compressed-source delay, discard padding, negative timestamps, discontinuities or video sync.')
(out/'results.json').write_text(json.dumps(report,indent=2)+'\n');log.close();failed=sum(r['status']=='FAIL' for r in results);print(f'{len(results)-failed}/{len(results)} passed');sys.exit(bool(failed))
