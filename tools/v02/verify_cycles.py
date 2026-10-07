"""Fresh-ROM, native return/re-entry audit; HP triggers are scratch diagnostics."""
from pathlib import Path
import ctypes as C
import hashlib
import json
from emulate import Emulator
from new_game import start_new_game

project=Path(__file__).resolve().parents[2]
root=project/'validation'/'v02'
root.mkdir(parents=True,exist_ok=True)
rom = project/'Monster Hunter Souls Arena - v0.2 Quests e Musica.gba'
e = Emulator(rom)
w32 = e.func('busWrite32', None, C.c_uint32, C.c_uint32)
w16 = e.func('busWrite16', None, C.c_uint32, C.c_uint32)
expected = [(1,7,0x085472FC), (2,9,0x08549430),
            (3,14,0x0854C564), (4,12,0x0854EEB0)]

def wait(n, protect=False):
    for _ in range(n):
        if protect and room()[0] != 0:
            w32(e.core,0x0200B260,45); w32(e.core,0x03003ED0,45)
        e.frame(e.core)

def press(key,n=180,protect=False):
    e.keys(e.core,key);wait(2,protect);e.keys(e.core,0);wait(n,protect)

def room():
    return [e.read16(e.core,a) for a in [0x0300331C,0x03003320]]

def xy():
    return [e.read32(e.core,0x03003E98+j)>>8 for j in [0,4]]

def position(x,y):
    for off,v in [(0,x),(4,y),(8,x),(12,y)]:w32(e.core,0x03003E98+off,v<<8)

def save():
    b=C.create_string_buffer(e.func('stateSize',C.c_size_t)(e.core))
    assert e.func('saveState',C.c_bool,C.c_void_p)(e.core,b)
    return b

def load(b):
    assert e.func('loadState',C.c_bool,C.c_void_p)(e.core,b)

def select(n,teleport=False):
    if teleport:position(168,240)
    e.keys(e.core,64);wait(5);e.keys(e.core,0);wait(5)
    press(1);press(1)
    if n==1:press(16,90)
    if n==2:press(16,90);press(16,90)
    if n==3:press(128,90)
    e.screenshot(root/f'v02-contract-{n+1}.png')
    press(1,300)
    return e.read32(e.core,0x0203FF04)==n+1

def walk(axis,target):
    previous=None;stuck=0
    for _ in range(700):
        p=xy()[axis]
        if abs(p-target)<=2:break
        stuck=stuck+1 if p==previous else 0;previous=p
        if stuck>90:break
        k=(16 if p<target else 32) if axis==0 else (128 if p<target else 64)
        e.keys(e.core,k);wait(1)
    e.keys(e.core,0);wait(4)
    return abs(xy()[axis]-target)<=6

def gate():
    e.keys(e.core,64);wait(160);e.keys(e.core,0);wait(400)

start_new_game(e,skip_book=False)
assert room()==[0,1]
fresh=save();reports=[]
for n in range(4):
    load(fresh);assert select(n,True)
    position(360,100);gate()
    assert room()==list(expected[n][:2])
    for _ in range(24):
        press(1,120,True)
        if e.read32(e.core,0x03005E48)==11:break
    assert e.read32(e.core,0x03007710)==0x09004400
    arena=save()
    for outcome in ['death','victory']:
        load(arena)
        if outcome=='death':
            w32(e.core,0x0200B260,0);w32(e.core,0x03003ED0,0)
        else:
            boss=e.read32(e.core,[0x030003E8,0x030003F4,0x03000404,0x03000428][n])
            assert 0x02000000<=boss<0x02040000
            w16(e.core,boss+0x5C,0)
        saw_pending=False
        for frames in range(3600):
            if outcome=='victory' and room()[0]!=0:
                w32(e.core,0x0200B260,45);w32(e.core,0x03003ED0,45)
            e.keys(e.core,1 if frames%120<2 else 0)
            wait(1)
            saw_pending |= e.read32(e.core,0x0203FF08)==2
            if room()==[0,1] and e.read32(e.core,0x0203FF08)==0:break
        e.keys(e.core,0);wait(120)
        main=e.read32(e.core,0x03005E44)
        result={'boss':n+1,'outcome':outcome,'return_frames':frames,
                'room':room(),'descriptor':hex(e.read32(e.core,main+0x71C)),
                'native_pending_seen':bool(saw_pending),
                'hp':e.read32(e.core,0x03003ED0),'sp':e.read16(e.core,0x03003ECE),
                'quest_cleared':e.read32(e.core,0x0203FF04)==0,
                'hub_music':e.read32(e.core,0x03007710)==0x09004000,
                'player_flags':hex(e.read32(e.core,0x03003E3C)),
                'visible':not bool(e.read32(e.core,0x03003E3C)&0x402)}
        e.screenshot(root/f'v02-boss-{n+1}-{outcome}-hub.png')
        before=xy();e.keys(e.core,32);wait(48);e.keys(e.core,0);wait(8)
        result['movable']=xy()!=before
        position(360,100);e.keys(e.core,64);wait(160);e.keys(e.core,0);wait(80)
        result['gate_blocked_until_new_contract']=room()==[0,1] and e.read32(e.core,0x0203FF08)==0
        result['npc_approach']=walk(1,268) and walk(0,168) and walk(1,240)
        result['selected_again']=select(n)
        result['gate_approach']=walk(1,268) and walk(0,360) and walk(1,100)
        gate()
        result['reentry_room']=room()
        result['reentered']=room()==list(expected[n][:2])
        result['battle_music_again']=e.read32(e.core,0x03007710)==0x09004400
        result['passed']=(result['room']==[0,1] and result['hp']>0 and
                          all(result[k] for k in ['visible','native_pending_seen','quest_cleared','hub_music',
                          'movable','gate_blocked_until_new_contract','npc_approach',
                          'selected_again','gate_approach','reentered','battle_music_again']))
        reports.append(result)
        print(json.dumps(result),flush=True)
        (root/'v02-cycles.json').write_text(json.dumps({
            'rom_sha256':hashlib.sha256(rom.read_bytes()).hexdigest(),
            'method':'fresh boot + native shelf selection; scratch HP-zero triggers native death/victory; movement and re-selection use ordinary inputs',
            'tests':reports},indent=2))
        assert result['passed'],result
e.func('deinit')(e.core)
