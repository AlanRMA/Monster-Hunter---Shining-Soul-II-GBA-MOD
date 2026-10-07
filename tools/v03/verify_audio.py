"""Render native sound and verify all three hardware sample loops."""
from pathlib import Path
import sys,ctypes as C,numpy as np,wave,json,hashlib,tempfile,shutil
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'v02'))
from emulate import Emulator,LIB
from new_game import start_new_game
P=Path(__file__).resolve().parents[2];OUT=P/'validation/v03'
rom=P/'Monster Hunter Souls Arena - v0.3 Hunts.gba'
scratch=Path(tempfile.mkdtemp(prefix='ss2-v03-audio-'))
testrom=scratch/'v03.gba';shutil.copy2(rom,testrom);e=Emulator(testrom)
e.func('setAudioBufferSize',None,C.c_size_t)(e.core,4096)
channels=[e.func('getAudioChannel',C.c_void_p,C.c_int)(e.core,n) for n in [0,1]]
LIB.blip_set_rates.argtypes=[C.c_void_p,C.c_double,C.c_double]
LIB.blip_samples_avail.argtypes=[C.c_void_p];LIB.blip_samples_avail.restype=C.c_int
LIB.blip_read_samples.argtypes=[C.c_void_p,C.POINTER(C.c_int16),C.c_int,C.c_int]
LIB.blip_read_samples.restype=C.c_int
for ch in channels:LIB.blip_set_rates(ch,16777216,44100)
raw_frame=e.frame;capture=False;chunks=[];protect=False
w=e.func('busWrite32',None,C.c_uint32,C.c_uint32)
def frame(core):
    if protect:w(core,0x0200b260,45);w(core,0x03003ed0,45)
    raw_frame(core);buffers=[]
    for ch in channels:
        n=LIB.blip_samples_avail(ch);assert 0<=n<=4096
        b=(C.c_int16*n)();assert LIB.blip_read_samples(ch,b,n,0)==n
        buffers.append(np.frombuffer(b,dtype='<i2').copy())
    if capture:
        n=min(len(x) for x in buffers);chunks.append(np.column_stack([x[:n] for x in buffers]).astype('<i2'))
e.frame=frame
def wait(n):
    for _ in range(n):frame(e.core)
def press(k,n=180):e.keys(e.core,k);wait(2);e.keys(e.core,0);wait(n)
def pos(x,y):
    for off,v in [(0,x),(4,y),(8,x),(12,y)]:w(e.core,0x03003e98+off,v<<8)
reports=[]
def check(name,header,waveaddr,frames):
    global capture,chunks
    assert e.read32(e.core,0x03007710)==header
    chunks=[];capture=True;wait(180);capture=False;data=np.concatenate(chunks)
    with wave.open(str(OUT/(name+'-emulator.wav')),'wb') as f:
        f.setnchannels(2);f.setsampwidth(2);f.setframerate(44100);f.writeframes(data.tobytes())
    rms=float(np.sqrt(np.mean(data.astype(np.float64)**2)));assert rms>10
    previous=0;wraps=0;transitions=[]
    for _ in range(frames):
        wait(1)
        for i in range(8):
            b=0x030065d0+80+i*64
            if e.read32(e.core,b+36)==waveaddr:
                cursor=e.read32(e.core,b+40)
                if cursor and previous and cursor<previous:
                    wraps+=1;transitions.append([hex(previous),hex(cursor)])
                if cursor:previous=cursor
                break
    row={'theme':name,'header':hex(header),'wave':hex(waveaddr),'rendered_rms_s16':rms,
         'loop_wraps':wraps,'loop_transitions':transitions,'passed':wraps>=1}
    reports.append(row);print(json.dumps(row),flush=True);assert row['passed']
wait(900);check('menu',0x09004800,0x09310000,6000)
e.func('reset')(e.core);start_new_game(e,skip_book=False)
check('hub',0x09004000,0x09010000,5600)
pos(168,240);e.keys(e.core,64);wait(5);e.keys(e.core,0);wait(5)
press(1);press(1);press(1);press(2,300)
pos(360,240);press(8,100);press(1,100);press(128,100);press(1,100);press(32,100);press(1,100)
assert e.read32(e.core,0x0203ff04)==1
press(2,100);press(2,100);press(2,100)
protect=True;pos(360,100);e.keys(e.core,64);wait(110);e.keys(e.core,0);wait(500)
assert e.read32(e.core,0x03005e48)==11
check('battle',0x09004400,0x09110000,6000)
(OUT/'audio.json').write_text(json.dumps({'rom_sha256':hashlib.sha256(rom.read_bytes()).hexdigest(),
    'tests':reports},indent=2));e.func('deinit')(e.core)
