"""Native input workflows; RAM HP/position changes only in isolated diagnostics."""
from pathlib import Path
import sys, ctypes as C, json, hashlib, tempfile, shutil, argparse
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'v02'))
from emulate import Emulator
from new_game import start_new_game
P=Path(__file__).resolve().parents[2]
parser=argparse.ArgumentParser()
parser.add_argument('--rom',type=Path,default=P/'Monster Hunter Souls Arena - v0.3 Hunts.gba')
parser.add_argument('--output',type=Path,default=P/'validation/v03')
args=parser.parse_args();rom=args.rom;OUT=args.output;OUT.mkdir(parents=True,exist_ok=True)
scratch=Path(tempfile.mkdtemp(prefix='ss2-v03-hunts-'))
testrom=scratch/'v03.gba';shutil.copy2(rom,testrom)
e=Emulator(testrom)
w32=e.func('busWrite32',None,C.c_uint32,C.c_uint32)
w16=e.func('busWrite16',None,C.c_uint32,C.c_uint32)
def room():return [e.read16(e.core,a) for a in [0x0300331c,0x03003320]]
def state(off):return e.read32(e.core,0x0203ff00+off)
def wait(n,protect=False):
    for _ in range(n):
        if protect and room()[0]:
            w32(e.core,0x0200b260,45);w32(e.core,0x03003ed0,45)
        e.frame(e.core)
def press(k,n=100,protect=False):
    e.keys(e.core,k);wait(2,protect);e.keys(e.core,0);wait(n,protect)
def pos(x,y):
    for off,v in [(0,x),(4,y),(8,x),(12,y)]:w32(e.core,0x03003e98+off,v<<8)
def save():
    b=C.create_string_buffer(e.func('stateSize',C.c_size_t)(e.core))
    assert e.func('saveState',C.c_bool,C.c_void_p)(e.core,b);return b
def load(b):assert e.func('loadState',C.c_bool,C.c_void_p)(e.core,b)
def slots():
    p=e.read32(e.core,0x03003600)+348
    return [(e.read16(e.core,p+16*i),e.read16(e.core,p+16*i+2),e.read32(e.core,p+16*i+4)) for i in range(25)]
def buy(n):
    pos(168,240);e.keys(e.core,64);wait(5);e.keys(e.core,0);wait(5)
    press(1,180);press(1,180)
    if n in [1,2]:
        for _ in range(n):press(16)
    if n==3:press(128)
    press(1,100)
    assert state(4)==0 and state(16)==0
    assert any(t==1 and i==0xff00+n for t,i,v in slots())
    e.screenshot(OUT/f'shop-{n+1}.png');press(2,300)
def use():
    pos(360,240);wait(120)
    for k in [8,1,128,1,32,1]:press(k)
    e.screenshot(OUT/'inventory-used.png')
    assert state(16)==2
    press(2);press(2);press(2)
def enter():
    pos(360,100);e.keys(e.core,64);wait(110,True);e.keys(e.core,0)
    for n in range(800):
        wait(1,True)
        if room()[0] and e.read32(e.core,0x03005e48)==11:break
    return n
def finish(outcome,n):
    if outcome=='death':
        w32(e.core,0x0200b260,0);w32(e.core,0x03003ed0,0)
    else:
        boss=e.read32(e.core,[0x030003e8,0x030003f4,0x03000404,0x03000428][n])
        assert 0x02000000<=boss<0x02040000
        w16(e.core,boss+92,0)
    for f in range(3600):
        e.keys(e.core,1 if outcome=='victory' and f%120<2 else 0)
        wait(1,outcome=='victory')
        if room()==[0,1] and state(8)==0:break
    e.keys(e.core,0);wait(120)
    assert room()==[0,1] and state(8)==0, (outcome,room(),state(8),hex(e.register('pc')))
    return f

start_new_game(e,skip_book=False)
assert room()==[0,1]
assert sum(v for t,i,v in slots() if t==10)==1000
fresh=save(); reports=[]
expected=[[1,7],[2,9],[3,14],[4,12]]
for n in range(4):
    load(fresh);buy(n)
    gold=sum(v for t,i,v in slots() if t==10)
    assert gold==1000-[20,40,70,100][n],gold
    # Buying cannot open the gate before USE.
    pos(360,100);e.keys(e.core,64);wait(160);e.keys(e.core,0);wait(80)
    assert room()==[0,1]
    use();assert state(4)==n+1
    ready=save()
    intro=enter(); assert room()==expected[n]
    assert e.read32(e.core,0x03005e48)==11,'boss introduction still requires input'
    boss=e.read32(e.core,[0x030003e8,0x030003f4,0x03000404,0x03000428][n])
    fullhp=e.read16(e.core,boss+92)
    e.screenshot(OUT/f'arena-{n+1}.png')
    first=finish('death',n)
    assert state(4)==n+1 and state(16)==1
    tasks=[e.read32(e.core,0x03004370+i*40+4) for i in range(5)]
    refs=[e.read32(e.core,a) for a in [0x030003e8,0x030003f4,0x03000404,0x03000428]]
    assert tasks==[0]*5 and refs==[0]*4,(tasks,refs)
    enter(); assert room()==expected[n]
    newboss=e.read32(e.core,[0x030003e8,0x030003f4,0x03000404,0x03000428][n])
    rehp=e.read16(e.core,newboss+92)
    assert rehp==fullhp,(fullhp,rehp)
    second=finish('death',n)
    assert state(4)==0 and state(16)==0
    pos(360,100);e.keys(e.core,64);wait(160);e.keys(e.core,0);wait(80)
    assert room()==[0,1]
    load(ready);enter(); victory=finish('victory',n)
    assert state(4)==0 and state(16)==0
    e.screenshot(OUT/f'hub-after-{n+1}.png')
    report={'boss':n+1,'gold_after_purchase':gold,'intro_without_A_frames':intro,
            'first_death_return_frames':first,'second_death_return_frames':second,
            'victory_return_frames':victory,'old_tasks_after_death':tasks,
            'old_boss_references':refs,'initial_hp':fullhp,'reload_hp':rehp,
            'purchase_does_not_activate':True,'two_deaths_expire':True,'passed':True}
    reports.append(report);print(json.dumps(report),flush=True)
    (OUT/'hunts.json').write_text(json.dumps({'rom_sha256':hashlib.sha256(rom.read_bytes()).hexdigest(),
        'tests':reports},indent=2))
e.func('deinit')(e.core)
