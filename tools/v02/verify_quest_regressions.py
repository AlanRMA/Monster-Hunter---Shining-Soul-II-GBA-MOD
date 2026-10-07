from emulate import Emulator
from new_game import start_new_game
from pathlib import Path
import ctypes as C
import hashlib
import json
project=Path(__file__).resolve().parents[2]
root=project/'validation'/'v02'
root.mkdir(parents=True,exist_ok=True)
report=[]
def boot(path):
    e=Emulator(path);start_new_game(e,skip_book=False);return e
def wait(e,n):
    for _ in range(n):e.frame(e.core)
def press(e,key,n=180):
    e.keys(e.core,key);wait(e,2);e.keys(e.core,0);wait(e,n)
def save(e):
    size=e.func('stateSize',C.c_size_t)(e.core);b=(C.c_ubyte*size)()
    assert e.func('saveState',C.c_bool,C.c_void_p)(e.core,b)
    return b
def position(e,x,y):
    w=e.func('busWrite32',None,C.c_uint32,C.c_uint32)
    for off,v in [(0,x),(4,y),(8,x),(12,y)]:w(e.core,0x03003E98+off,v<<8)
def open_npc(e,x):
    position(e,x,240);e.keys(e.core,64);wait(e,5);e.keys(e.core,0);wait(e,5)
    press(e,1);press(e,1)
def room(e):return [e.read32(e.core,a) for a in [0x0300331C,0x03003320]]
old=boot(project/'Monster Hunter Souls Arena - v0.1 Hub.gba')
new=boot(project/'Monster Hunter Souls Arena - v0.2 Quests e Musica.gba')
fresh=save(new)
report.append({'test':'fresh-boot-no-book','passed':room(new)==[0,1]})
new.screenshot(root/'q02-fresh-hub.png')
snapshots=[save(old),fresh]
for x,label in [(232,'potions'),(296,'bank'),(424,'weapons'),(488,'armor'),(552,'smith')]:
    hashes=[]
    for e,b in zip([old,new],snapshots):
        assert e.func('loadState',C.c_bool,C.c_void_p)(e.core,b)
        open_npc(e,x)
        ui=e.read32(e.core,0x03006590)
        data=b''.join(e.read32(e.core,ui+0x104+i).to_bytes(4,'little') for i in range(0,192,4))
        hashes.append(hashlib.sha256(data).hexdigest())
    report.append({'test':'unchanged-'+label,'hashes':hashes,'passed':hashes[0]==hashes[1]})
assert new.func('loadState',C.c_bool,C.c_void_p)(new.core,fresh)
open_npc(new,168)
press(new,2,300)
q=[new.read32(new.core,0x0203FF00+j) for j in [4,8,12]]
report.append({'test':'cancel-does-not-activate','quest':q,'passed':q[0]==0})
for label,x,y,key in [('left-stairs',48,100,64),('right-stairs',680,100,64),('left-edge',48,118,32),('right-edge',680,118,16)]:
    assert new.func('loadState',C.c_bool,C.c_void_p)(new.core,fresh)
    position(new,x,y);new.keys(new.core,key);wait(new,300);new.keys(new.core,0);wait(new,30)
    report.append({'test':label,'room':room(new),'passed':room(new)==[0,1]})
assert new.func('loadState',C.c_bool,C.c_void_p)(new.core,fresh)
new.keys(new.core,128);wait(new,160);new.keys(new.core,0);wait(new,200)
new.screenshot(root/'q02-south-prompt.png')
report.append({'test':'south-confirmation-stays-safe','room':room(new),'passed':room(new)==[0,1]})
(root/'q02-regressions.json').write_text(json.dumps(report,indent=2))
print(json.dumps(report,indent=2))
assert all(r['passed'] for r in report)
