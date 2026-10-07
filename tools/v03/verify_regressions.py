"""Isolated negative purchases, input/SFX feedback, shops, exits, and title art."""
from pathlib import Path
import sys,ctypes as C,json,tempfile,shutil,hashlib,argparse,struct
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'v02'))
from emulate import Emulator
from new_game import start_new_game
P=Path(__file__).resolve().parents[2]
parser=argparse.ArgumentParser()
parser.add_argument('--rom',type=Path,default=P/'Monster Hunter Souls Arena - v0.3 Hunts.gba')
parser.add_argument('--output',type=Path,default=P/'validation/v03')
parser.add_argument('--trace',action='store_true')
args=parser.parse_args();rom=args.rom;OUT=args.output;OUT.mkdir(parents=True,exist_ok=True)
scratch=Path(tempfile.mkdtemp(prefix='ss2-v03-audit-'))
testrom=scratch/'v03.gba';shutil.copy2(rom,testrom)
e=Emulator(testrom);reports=[]
trace_resume=False
w32=e.func('busWrite32',None,C.c_uint32,C.c_uint32)
w16=e.func('busWrite16',None,C.c_uint32,C.c_uint32)
def wait(n):
    if trace_resume:
        counter=e.func('frameCounter',C.c_uint32);end=counter(e.core)+n
        regs=(C.c_uint32*16).from_address(C.c_void_p.from_address(e.core).value)
        while counter(e.core)<end:
            if regs[15]-2 in [0x08026b14,0x080230b8,0x08022ca4,0x080227ec,0x08022982]:
                print('RESUME',hex(regs[15]-2),[hex(regs[i]) for i in [0,1,2,14]],flush=True)
            e.step(e.core)
        return
    for _ in range(n):e.frame(e.core)
def press(k,n=180):e.keys(e.core,k);wait(2);e.keys(e.core,0);wait(n)
def pos(x,y):
    for off,v in [(0,x),(4,y),(8,x),(12,y)]:w32(e.core,0x03003e98+off,v<<8)
def room():return [e.read16(e.core,a) for a in [0x0300331c,0x03003320]]
def save():
    b=C.create_string_buffer(e.func('stateSize',C.c_size_t)(e.core));assert e.func('saveState',C.c_bool,C.c_void_p)(e.core,b);return b
def load(b):assert e.func('loadState',C.c_bool,C.c_void_p)(e.core,b)
def slots():
    p=e.read32(e.core,0x03003600)+348
    return [(e.read16(e.core,p+16*i),e.read16(e.core,p+16*i+2),e.read32(e.core,p+16*i+4)) for i in range(25)]
def gold():return sum(v for t,i,v in slots() if t==10)
def open_npc(x):
    pos(x,240);e.keys(e.core,64);wait(5);e.keys(e.core,0);wait(5);press(1);press(1)
def trace_A():
    regs=(C.c_uint32*16).from_address(C.c_void_p.from_address(e.core).value)
    counter=e.func('frameCounter',C.c_uint32);last=counter(e.core)+2;sounds=[];e.keys(e.core,1)
    for _ in range(300000):
        if regs[15]-2==0x08058588:sounds.append(int(regs[0]))
        e.step(e.core)
        if counter(e.core)>=last:break
    else:raise AssertionError('trace did not finish two frames')
    e.keys(e.core,0);wait(100);return sounds
def report(name,passed,**data):
    row={'test':name,'passed':bool(passed),**data};reports.append(row);print(json.dumps(row),flush=True)
    assert passed,row
wait(900);e.screenshot(OUT/'title.png')
title_track=struct.unpack_from('<I',rom.read_bytes(),0xbc09c+197*8)[0]
report('native-menu-music',e.read32(e.core,0x03007710)==title_track)
press(8);e.screenshot(OUT/'main-menu.png')
e.func('reset')(e.core);start_new_game(e,skip_book=False)
report('fresh-boot-skips-book-and-starts-1000',room()==[0,1] and gold()==1000)
e.screenshot(OUT/'fresh-hub.png');fresh=save()
open_npc(168);shop=save();sounds=trace_A()
count=sum(t==1 and i==0xff00 for t,i,v in slots())
report('single-A-purchases-one-with-native-sound',count==1 and gold()==980 and 95 in sounds,sounds=sounds)
report('purchase-is-not-activation',e.read32(e.core,0x0203ff04)==0)
purchased=save()
e.keys(e.core,1);wait(24);e.keys(e.core,0);wait(100)
count=sum(t==1 and i==0xff00 for t,i,v in slots())
report('held-A-does-not-repeat-purchases',count==2 and gold()==960,count=count,gold=gold())
e.screenshot(OUT/'purchase-feedback.png')
load(shop);p=e.read32(e.core,0x03003600)+348
for idx,(t,i,v) in enumerate(slots()):
    if t==10:w32(e.core,p+idx*16+4,10)
before=slots();sounds=trace_A()
report('insufficient-money-keeps-inventory-and-gold',slots()==before and gold()==10 and 97 in sounds,sounds=sounds)
load(shop);p=e.read32(e.core,0x03003600)+348
for idx,(t,i,v) in enumerate(slots()):
    if t==0:
        w16(e.core,p+idx*16,1);w16(e.core,p+idx*16+2,0);w32(e.core,p+idx*16+4,1)
before=slots();sounds=trace_A()
report('full-bag-does-not-charge',slots()==before and gold()==1000 and 97 in sounds,sounds=sounds)
load(fresh);open_npc(168);press(2,300)
report('cancel-no-charge-no-hunt',gold()==1000 and e.read32(e.core,0x0203ff04)==0)
# Compare item identities, not transient sprite/cache pointers or player gold.
oldrom=scratch/'reference-v02.gba'
shutil.copy2(P/'Monster Hunter Souls Arena - v0.2 Quests e Musica.gba',oldrom)
old=Emulator(oldrom);start_new_game(old,skip_book=False)
b=C.create_string_buffer(old.func('stateSize',C.c_size_t)(old.core));old.func('saveState',C.c_bool,C.c_void_p)(old.core,b)
for x,label in [(232,'potions'),(296,'bank'),(424,'weapons'),(488,'armor'),(552,'smith')]:
    load(fresh);w32(e.core,0x030025d0,0x12345678);open_npc(x);u=e.read32(e.core,0x03006590)
    ids=[(e.read16(e.core,u+260+i*16),e.read16(e.core,u+262+i*16),e.read32(e.core,u+264+i*16)) for i in range(12)]
    # Stocks are generated when the character is initialized. Compare both ROM
    # implementations from identical RAM, gold, generated stock and RNG state.
    assert old.func('loadState',C.c_bool,C.c_void_p)(old.core,fresh)
    ow=old.func('busWrite32',None,C.c_uint32,C.c_uint32)
    ow(old.core,0x030025d0,0x12345678)
    for off,v in [(0,x),(4,240),(8,x),(12,240)]:ow(old.core,0x03003e98+off,v<<8)
    old.keys(old.core,64)
    for _ in range(5):old.frame(old.core)
    old.keys(old.core,0)
    for _ in range(5):old.frame(old.core)
    for _ in range(2):
        old.keys(old.core,1)
        for _ in range(2):old.frame(old.core)
        old.keys(old.core,0)
        for _ in range(180):old.frame(old.core)
    ou=old.read32(old.core,0x03006590)
    oids=[(old.read16(old.core,ou+260+i*16),old.read16(old.core,ou+262+i*16),old.read32(old.core,ou+264+i*16)) for i in range(12)]
    report('preserved-'+label,ids==oids,new=ids,reference=oids)
old.func('deinit')(old.core)
for label,x,y,key in [('left-stairs',48,100,64),('right-stairs',680,100,64),('left-edge',48,118,32),('right-edge',680,118,16)]:
    load(fresh);pos(x,y);e.keys(e.core,key);wait(300);e.keys(e.core,0);wait(30)
    report('blocked-'+label,room()==[0,1])
load(purchased);press(2,300);pos(360,270)
e.keys(e.core,128);wait(160);e.keys(e.core,0);wait(700)
e.screenshot(OUT/'south-question.png')
report('south-first-page-awaits-advance',room()==[0,1])
press(1,300)
e.screenshot(OUT/'south-choice.png');question=save()
pool=e.read32(e.core,0x03005eb8);mask=e.read16(e.core,0x03005ebc)&15
dialog_states=[e.read32(e.core,pool+136*i+116) for i in range(4) if mask&(1<<i)]
report('south-second-page-awaits-Yes-No',room()==[0,1] and 6 in dialog_states,
       dialogue_states=dialog_states)
press(2,300);e.screenshot(OUT/'south-cancel.png')
report('south-No-returns-to-hub',room()==[0,1])
load(question);press(1,200)
for _ in range(10):
    if room()==[0,0]:break
    press(1,180)
report('south-Yes-completes-native-save-title',room()==[0,0])
wait(1000);e.screenshot(OUT/'returned-title.png')
trace_resume=args.trace
press(8,120);press(1,120);press(1,120);press(1,200);wait(1000)
trace_resume=False
e.screenshot(OUT/'saved-scroll-resumed.png')
report('unused-scroll-survives-native-save-and-continue',room()==[0,1] and gold()==980 and
    sum(t==1 and i==0xff00 for t,i,v in slots())==1,room=room(),gold=gold(),items=slots())
report('resumed-player-visible-and-alive',e.read32(e.core,0x03003ed0)>0 and
       not bool(e.read32(e.core,0x03003e3c)&0x402))
pos(360,240)
for k in [8,1,128,1,32,1]:press(k,100)
report('saved-scroll-can-be-used-after-continue',e.read32(e.core,0x0203ff04)==1 and
       e.read32(e.core,0x0203ff10)==2)
# Reset clears live RAM while retaining native cartridge save memory. The last
# saved character still owns the unused scroll, not the later unsaved USE.
e.func('reset')(e.core);wait(900)
press(8,120);press(1,120);press(1,120);press(1,200);wait(1000)
report('reset-retains-native-save-without-live-hunt',room()==[0,1] and gold()==980 and
       sum(t==1 and i==0xff00 for t,i,v in slots())==1 and
       e.read32(e.core,0x0203ff04)==0 and e.read32(e.core,0x0203ff10)==0)
e.screenshot(OUT/'reset-save-resumed.png')
e.func('deinit')(e.core)
(OUT/'regressions.json').write_text(json.dumps({'rom_sha256':hashlib.sha256(rom.read_bytes()).hexdigest(),
    'isolated_test_directory':str(scratch),'tests':reports},indent=2))
