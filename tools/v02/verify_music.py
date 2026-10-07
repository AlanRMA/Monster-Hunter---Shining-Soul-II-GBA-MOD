from pathlib import Path
from emulate import Emulator,LIB
from new_game import start_new_game
import ctypes as C
import numpy as np
import wave
import json
project=Path(__file__).resolve().parents[2]
root=project/'validation'/'v02'
root.mkdir(parents=True,exist_ok=True)
e=Emulator(project/'Monster Hunter Souls Arena - v0.2 Quests e Musica.gba')
e.func('setAudioBufferSize',None,C.c_size_t)(e.core,4096)
channels=[e.func('getAudioChannel',C.c_void_p,C.c_int)(e.core,n) for n in [0,1]]
LIB.blip_set_rates.argtypes=[C.c_void_p,C.c_double,C.c_double]
LIB.blip_samples_avail.argtypes=[C.c_void_p];LIB.blip_samples_avail.restype=C.c_int
LIB.blip_read_samples.argtypes=[C.c_void_p,C.POINTER(C.c_int16),C.c_int,C.c_int]
LIB.blip_read_samples.restype=C.c_int
for ch in channels:LIB.blip_set_rates(ch,16777216,44100)
raw_frame=e.frame
capture=False
chunks=[]
def frame(core):
    raw_frame(core)
    buffers=[]
    for ch in channels:
        count=LIB.blip_samples_avail(ch)
        assert 0<=count<=4096,count
        buf=(C.c_int16*count)()
        assert LIB.blip_read_samples(ch,buf,count,0)==count
        buffers.append(np.frombuffer(buf,dtype='<i2').copy())
    if capture:
        n=min(len(x) for x in buffers)
        chunks.append(np.column_stack([x[:n] for x in buffers]).astype('<i2'))
e.frame=frame
def wait(n):
    for _ in range(n):frame(e.core)
def press(k,n=180):
    e.keys(e.core,k);wait(2);e.keys(e.core,0);wait(n)
def save():
    size=e.func('stateSize',C.c_size_t)(e.core);b=(C.c_ubyte*size)()
    assert e.func('saveState',C.c_bool,C.c_void_p)(e.core,b)
    return b
def position(x,y):
    w=e.func('busWrite32',None,C.c_uint32,C.c_uint32)
    for off,v in [(0,x),(4,y),(8,x),(12,y)]:w(e.core,0x03003E98+off,v<<8)
def voices():
    return [{'slot':n,'flags':e.func('busRead8',C.c_uint32,C.c_uint32)(e.core,0x030065D0+80+n*64),
             'wave':hex(e.read32(e.core,0x030065D0+80+n*64+36)),
             'cursor':e.read32(e.core,0x030065D0+80+n*64+40)} for n in range(8)]
def render(name,frames):
    global capture,chunks
    chunks=[];capture=True;wait(frames);capture=False
    data=np.concatenate(chunks) if chunks else np.zeros((0,2),dtype='<i2')
    with wave.open(str(root/(name+'.wav')),'wb') as w:
        w.setnchannels(2);w.setsampwidth(2);w.setframerate(44100);w.writeframes(data.tobytes())
    rms=float(np.sqrt(np.mean(data.astype(np.float64)**2)))
    return {'samples':len(data),'rms_s16':rms,'peak_s16':int(np.max(np.abs(data.astype(np.int32)))),'passed':rms>10}
start_new_game(e,skip_book=False)
fresh=save()
report=[{'test':'hub-native-song-header','header':hex(e.read32(e.core,0x03007710)),'passed':e.read32(e.core,0x03007710)==0x09004000}]
report.append({'test':'hub-rendered-audio',**render('q03-hub-emulator',180)})
previous=0;wraps=0;observed=[]
for _ in range(5600):
    wait(1)
    pointers=[v['cursor'] for v in voices() if v['wave']=='0x9010000' and v['flags']&0x13]
    if pointers:
        p=pointers[0]
        if previous and p<previous:wraps+=1;observed.append([hex(previous),hex(p)])
        previous=p
report.append({'test':'hub-hardware-sample-loop','wraps':wraps,'transitions':observed,'passed':wraps>=1})
for n in range(4):
    assert e.func('loadState',C.c_bool,C.c_void_p)(e.core,fresh)
    position(168,240);e.keys(e.core,64);wait(5);e.keys(e.core,0);wait(5)
    press(1);press(1)
    if n==1:press(16,90)
    if n==2:press(16,90);press(16,90)
    if n==3:press(128,90)
    press(1,300);position(360,100);e.keys(e.core,64);wait(120);e.keys(e.core,0);wait(400)
    header=e.read32(e.core,0x03007710)
    report.append({'test':f'boss-{n+1}-battle-music','header':hex(header),'passed':header==0x09004400})
    if n==0:
        report.append({'test':'battle-rendered-audio',**render('q03-battle-emulator',180)})
        previous=0;wraps=0;observed=[]
        write=e.func('busWrite32',None,C.c_uint32,C.c_uint32)
        for _ in range(5800):
            # This long audio-loop diagnostic can outlast the native intro and enter combat.
            # Keep the scratch-core player alive; no HP changes are baked into the ROM.
            write(e.core,0x0200B260,45);write(e.core,0x03003ED0,45)
            wait(1)
            pointers=[v['cursor'] for v in voices() if v['wave']=='0x9110000' and v['flags']&0x13]
            if pointers:
                p=pointers[0]
                if previous and p<previous:wraps+=1;observed.append([hex(previous),hex(p)])
                previous=p
        report.append({'test':'battle-hardware-sample-loop','wraps':wraps,'transitions':observed,'passed':wraps>=1})
    # Native dialogue sequences differ in length; inspect the actual music state throughout.
    for i in range(24):
        press(1,120)
        if e.read32(e.core,0x03005E48)==11:break
    report.append({'test':f'boss-{n+1}-combat-music','song':e.read32(e.core,0x03005E48),
                   'header':hex(e.read32(e.core,0x03007710)),
                   'passed':e.read32(e.core,0x03005E48)==11 and e.read32(e.core,0x03007710)==0x09004400})
(root/'q03-music-validation.json').write_text(json.dumps(report,indent=2))
print(json.dumps(report,indent=2))
assert all(r['passed'] for r in report)
