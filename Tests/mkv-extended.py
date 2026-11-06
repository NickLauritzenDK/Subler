#!/usr/bin/env python3
"""Independent MKV-to-AAC audiovisual timing regressions.

Usage: python3 Tests/mkv-extended.py FFMPEG_TOOL_DIRECTORY APP OUTPUT_DIRECTORY
Requires FFmpeg/ffprobe with the native encoders listed below and macOS audio
services. Generates only synthetic media. Retains command logs and per-packet
metadata; exits nonzero on any failure. See docs/NEO-MKV-TIMING.md for setup.
"""
import argparse,pathlib,subprocess,json,wave,struct,math,array,platform,hashlib
p=argparse.ArgumentParser();p.add_argument('tools',type=pathlib.Path);p.add_argument('app',type=pathlib.Path);p.add_argument('out',type=pathlib.Path);a=p.parse_args();out=a.out.resolve();out.mkdir(parents=True,exist_ok=True);ff=a.tools.resolve()/'ffmpeg';fp=a.tools.resolve()/'ffprobe';fw=a.app.resolve()/'Contents/Frameworks/MP42Foundation.framework';log=(out/'commands.log').open('w')
def run(args):
 log.write(repr(list(map(str,args)))+'\n');log.flush();subprocess.run(list(map(str,args)),stdout=log,stderr=log,check=True,timeout=90)
exe=out/'convert'
run(['xcrun','clang','-arch',platform.machine(),'-fobjc-arc','-Wl,-headerpad_max_install_names','-F'+str(fw.parent),'-framework','MP42Foundation','-framework','AppKit',pathlib.Path(__file__).resolve().parent.parent/'MP42Foundation/Tests/audio-conversion.m','-o',exe]);old=next(x.strip().split(' (')[0] for x in subprocess.check_output(['otool','-L',str(exe)],text=True).splitlines() if 'MP42Foundation.framework/' in x);run(['install_name_tool','-change',old,fw/'Versions/A/MP42Foundation',exe]);run(['codesign','-f','-s','-',exe])
source=out/'pulses.wav';rate=48000
with wave.open(str(source),'wb') as w:
 w.setparams((2,2,rate,0,'NONE',''));w.writeframes(b''.join(struct.pack('<hh',*[round(12000*math.sin(2*math.pi*1000*i/rate)) if .5<=i/rate<.65 or 2<=i/rate<2.15 else 0]*2) for i in range(rate*3)))
def probe(path):
 return json.loads(subprocess.check_output([str(fp),'-v','error','-show_streams','-show_packets','-of','json',str(path)]))
def pulses(path,name):
 wav=out/(name+'.wav');run([ff,'-v','error','-y','-copyts','-i',path,'-map','0:a:0','-af','aresample=async=1:first_pts=0','-t','5','-c:a','pcm_s16le',wav])
 with wave.open(str(wav)) as w:ch=w.getnchannels();rr=w.getframerate();v=array.array('h',w.readframes(w.getnframes()))[::ch]
 width=rr//1000;active=[i/rr for i in range(0,len(v)-width+1,width) if math.sqrt(sum(x*x for x in v[i:i+width])/width)>2000];groups=[]
 for t in active:
  if not groups or t-groups[-1][-1]>.005:groups.append([])
  groups[-1].append(t)
 return dict(duration=len(v)/rr,pulses=[(g[0],g[-1]+.001) for g in groups])
def mp4_audio_duration(path):
 def boxes(data):
  i=0
  while i+8<=len(data):
   size,kind=struct.unpack_from('>I4s',data,i);header=8
   if size==1:size=struct.unpack_from('>Q',data,i+8)[0];header=16
   if not size:size=len(data)-i
   assert size>=header and i+size<=len(data)
   yield kind,data[i+header:i+size];i+=size
 def child(data,kind):return next(v for k,v in boxes(data) if k==kind)
 moov=child(path.read_bytes(),b'moov');mvhd=child(moov,b'mvhd');scale=struct.unpack_from('>I',mvhd,20 if mvhd[0] else 12)[0]
 for kind,trak in boxes(moov):
  if kind!=b'trak':continue
  if child(child(trak,b'mdia'),b'hdlr')[8:12]!=b'soun':continue
  elst=child(child(trak,b'edts'),b'elst');fmt='>Qqhh' if elst[0] else '>Iihh';size=struct.calcsize(fmt);n=struct.unpack_from('>I',elst,4)[0]
  entries=[struct.unpack_from(fmt,elst,8+size*i)[:2] for i in range(n)]
  return sum(e[0] for e in entries)/scale,entries
 raise AssertionError('audio edit list missing')
def video_hash(path,name):
 raw=out/(name+'.yuv');run([ff,'-v','error','-y','-i',path,'-map','0:v:0','-fps_mode','passthrough','-c:v','rawvideo','-pix_fmt','yuv420p','-f','rawvideo',raw]);digest=hashlib.sha256(raw.read_bytes()).hexdigest();raw.unlink();return digest
results=[]
for codec in ('pcm_s16le','flac','aac','ac3','eac3','dca','opus'):
 for offset in (-.1,0,.25):
  case=f'{codec}-{offset}';inp=out/(case+'.mkv');target=out/(case+'.mp4');errors=[];details={}
  try:
   run([ff,'-v','error','-y','-f','lavfi','-i','testsrc2=size=64x64:rate=25:duration=3','-itsoffset',str(offset),'-i',source,'-map','0:v','-map','1:a','-c:v','mpeg4','-bf','0','-c:a',codec,'-strict','experimental','-avoid_negative_ts','disabled',inp])
   target.unlink(missing_ok=True);run([exe,'convert',inp,target]);before=pulses(inp,case+'-source');after=pulses(target,case+'-output');meta=probe(inp);actual=probe(target)
   audio_packets=[packet for packet in meta['packets'] if packet['stream_index']==1]
   if offset<0 and not any(float(packet['pts_time'])<0 for packet in audio_packets):errors.append('fixture did not contain negative timestamps')
   if codec=='opus':
    side=[item for packet in audio_packets for item in packet.get('side_data_list',[])]
    if not any(item.get('skip_samples',0)>0 for item in side):errors.append('fixture missing Opus pre-skip')
    if not any(item.get('discard_padding',0)>0 for item in side):errors.append('fixture missing Opus tail discard')
   for label,m in (('source',meta),('output',actual)):(out/(case+'-'+label+'-packets.json')).write_text(json.dumps(m,indent=2))
   presentation_duration,edit_entries=mp4_audio_duration(target)
   if abs(before['duration']-presentation_duration)>.003:errors.append(f'presentation duration {presentation_duration} != {before["duration"]}')
   if after['duration']-before['duration']>1024/48000+.003:errors.append('excess raw decoded padding')
   if len(before['pulses'])!=len(after['pulses']):errors.append('pulse count')
   else:
    for b,c in zip(before['pulses'],after['pulses']):
     for x,y in zip(b,c):
      if abs(x-y)>.012:errors.append(f'pulse timing {y:.4f} != {x:.4f}')
   bv=[float(x['pts_time']) for x in meta['packets'] if x['stream_index']==0];av=[float(x['pts_time']) for x in actual['packets'] if x['stream_index']==0]
   if len(av)!=len(bv) or any(abs(x-y)>.002 for x,y in zip(bv,av)):errors.append('video presentation timestamps changed')
   source_hash=video_hash(inp,case+'-source');output_hash=video_hash(target,case+'-output')
   if source_hash!=output_hash:errors.append('decoded video content changed')
   details=dict(source=before,output=after,presentation_duration=presentation_duration,audio_edits=edit_entries,video_sha256=output_hash,source_video_pts=bv,output_video_pts=av)
  except Exception as e:errors.append(str(e))
  results.append(dict(case=case,errors=errors,**details));print(case,'FAIL' if errors else 'PASS',errors,flush=True)
(out/'tool-provenance.json').write_text(json.dumps({'version':subprocess.check_output([str(ff),'-version'],text=True),'ffmpeg_sha256':hashlib.sha256(ff.read_bytes()).hexdigest(),'ffprobe_sha256':hashlib.sha256(fp.read_bytes()).hexdigest()},indent=2));(out/'results.json').write_text(json.dumps(results,indent=2));print('done',sum(not x['errors'] for x in results),'/',len(results))

raise SystemExit(any(x['errors'] for x in results))
