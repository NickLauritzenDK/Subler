"""Minimal deterministic, unlaced Matroska PCM fixture; no external muxer."""
import struct,math,pathlib

def vint(n):
 for size in range(1,9):
  if n < (1<<(7*size))-1:return ((1<<(7*size))|n).to_bytes(size,'big')
 raise ValueError(n)
def el(tag,data):
 return bytes.fromhex(tag)+vint(len(data))+data
def uint(tag,n):return el(tag,n.to_bytes(max(1,(n.bit_length()+7)//8),'big'))
def text(tag,s):return el(tag,s.encode())
def make(path,rate=48000,offset_ms=0):
 header=el('1a45dfa3',uint('4286',1)+uint('42f7',1)+uint('42f2',4)+uint('42f3',8)+text('4282','matroska')+uint('4287',4)+uint('4285',2))
 info=el('1549a966',uint('2ad7b1',100000)+el('4489',struct.pack('>d',(2000+offset_ms)*10))+text('4d80','Neo timing fixture')+text('5741','Neo timing fixture'))
 audio=el('e1',el('b5',struct.pack('>d',rate))+uint('9f',2)+uint('6264',16))
 track=el('1654ae6b',el('ae',uint('d7',1)+uint('73c5',1)+uint('83',2)+uint('9c',0)+uint('23e383',20000000)+text('86','A_PCM/INT/LIT')+audio))
 blocks=[]
 for block in range(100):
  first=block*rate//50;last=(block+1)*rate//50
  pcm=b''.join(struct.pack('<hh',*[round(6000*math.sin(2*math.pi*431*i/rate)) if i<rate*1.8 else 0]*2) for i in range(first,last))
  blocks.append(el('a3',b'\x81'+struct.pack('>hB',(offset_ms+block*20)*10,0x80)+pcm))
 cluster=el('1f43b675',uint('e7',0)+b''.join(blocks))
 pathlib.Path(path).write_bytes(header+el('18538067',info+track+cluster))
import struct

def boxes(data,start=0,end=None):
 end=len(data) if end is None else end
 while start+8<=end:
  n,kind=struct.unpack_from('>I4s',data,start);header=8
  if n==1:n=struct.unpack_from('>Q',data,start+8)[0];header=16
  if n==0:n=end-start
  assert n>=header and start+n<=end
  yield kind,data[start+header:start+n]
  start+=n

def alac_packets(path):
 b=path.read_bytes()
 def child(b,k):return next(v for t,v in boxes(b) if t==k)
 stbl=child(child(child(child(b,b'moov'),b'trak'),b'mdia'),b'minf')
 stbl=child(stbl,b'stbl')
 sz=child(stbl,b'stsz');fixed,count=struct.unpack_from('>II',sz,4)
 sizes=[fixed]*count if fixed else list(struct.unpack_from('>'+str(count)+'I',sz,12))
 try:co=child(stbl,b'stco');fmt='I'
 except StopIteration:co=child(stbl,b'co64');fmt='Q'
 offsets=struct.unpack_from('>'+str(struct.unpack_from('>I',co,4)[0])+fmt,co,8)
 sc=child(stbl,b'stsc');mapping=[struct.unpack_from('>III',sc,8+12*i) for i in range(struct.unpack_from('>I',sc,4)[0])]
 packets=[];sample=0
 for chunk,offset in enumerate(offsets,1):
  per=next(x[1] for x in reversed(mapping) if x[0]<=chunk)
  for _ in range(per):
   n=sizes[sample];packets.append(b[offset:offset+n]);offset+=n;sample+=1
 assert sample==count
 stts=child(stbl,b'stts');durations=[]
 for i in range(struct.unpack_from('>I',stts,4)[0]):
  n,d=struct.unpack_from('>II',stts,8+8*i);durations.extend([d]*n)
 entry=child(stbl,b'stsd')[8:];kind,payload=next(boxes(entry));assert kind==b'alac'
 config=child(payload[28:],b'alac');assert len(config)==28
 return packets,durations,config[4:]

def make_alac(path,source,rate,offset_ms):
 packets,durations,config=alac_packets(source)
 header=el('1a45dfa3',uint('4286',1)+uint('42f7',1)+uint('42f2',4)+uint('42f3',8)+text('4282','matroska')+uint('4287',4)+uint('4285',2))
 info=el('1549a966',uint('2ad7b1',1000)+el('4489',struct.pack('>d',(sum(durations)/rate+offset_ms/1000)*1000000))+text('4d80','Neo timing fixture')+text('5741','Neo timing fixture'))
 audio=el('e1',el('b5',struct.pack('>d',rate))+uint('9f',2)+uint('6264',16))
 track=el('1654ae6b',el('ae',uint('d7',1)+uint('73c5',1)+uint('83',2)+uint('9c',0)+text('86','A_ALAC')+el('63a2',config)+audio))
 clusters=[];position=0
 for packet,duration in zip(packets,durations):
  tick=round(position/rate*1000000)+offset_ms*1000
  block=el('a0',el('a1',b'\x81\x00\x00\x00'+packet)+uint('9b',round(duration/rate*1000000)))
  clusters.append(el('1f43b675',uint('e7',tick)+block));position+=duration
 pathlib.Path(path).write_bytes(header+el('18538067',info+track+b''.join(clusters)))
