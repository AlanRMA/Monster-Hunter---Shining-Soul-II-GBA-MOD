"""Rebuild the tested v0.2 from the preserved v0.1 and converted PCM assets."""
import json
from pathlib import Path
import struct
import hashlib
from patch_tools import Thumb

project=Path(__file__).resolve().parents[2]
base=project/'Monster Hunter Souls Arena - v0.1 Hub.gba'
rom=bytearray(base.read_bytes())
assert hashlib.sha256(rom).hexdigest()=='b78d2d7b118d34543222164bd067cff574cdaa031476b088855c7534d1cc9303'
STATE=0x0203FF00
SHELF=0x09002000
ITEMS=0x09002400
MAGIC=0x51535432
# Reserve the final 256 bytes outside the native heap; IWRAM's apparent gap is audio RAM.
assert struct.unpack_from('<I',rom,0x1488)[0]==0x0203FFF0
assert struct.unpack_from('<I',rom,0x1490)[0]==0x0003FFFF
struct.pack_into('<I',rom,0x1488,0x0203FEF0)
struct.pack_into('<I',rom,0x1490,0x0003FEFF)

def install(code,site=None,register=3):
    data=code.finish();offset=code.base-0x08000000
    assert rom[offset:offset+len(data)]==bytes(len(data))
    rom[offset:offset+len(data)]=data
    if site is not None:
        assert site%4==0 or site%4==2
        # Aligned PC literal: with a site at +2 use an extra NOP before the literal.
        if site%4==0:
            hook=struct.pack('<HHI',0x4800|(register<<8),0x4700|(register<<3),code.base|1)
        else:
            hook=struct.pack('<HHHI',0x4801|(register<<8),0x4700|(register<<3),0x46C0,code.base|1)
        rom[site-0x08000000:site-0x08000000+len(hook)]=hook
    return len(data)

# Native appraisal still controls the NPC sprite/camera, but reuses potion-shop shelving.
open_shop=Thumb(0x09000400)
open_shop.literal(0,STATE)
open_shop.literal(1,MAGIC)
open_shop.h(0x6001,0x2101,0x60C1,0x2001)
open_shop.abs_bl(0x080847DC)
open_shop.literal(0,0x11201100)
open_shop.abs_bl(0x080003F4)
open_shop.literal(3,0x08031CFF)
open_shop.h(0x4718)
# Site +2 hook takes 10 bytes: original mov, BL, LDR and first half of BL wait.
# Cover full 12 bytes instead, and resume after that complete wait.
data=open_shop.finish()
rom[0x1000400:0x1000400+len(data)]=data
rom[0x31CF2:0x31CFE]=struct.pack('<HHHIH',0x4B01,0x4718,0x46C0,0x09000401,0x46C0)

close_shop=Thumb(0x09000500)
close_shop.literal(0,STATE)
close_shop.h(0x2100,0x60C1)
close_shop.abs_bl(0x080020F4)
close_shop.h(0x21AC,0x0049)
close_shop.literal(3,0x08031D35)
close_shop.h(0x4718)
install(close_shop,0x08031D2C)

# Reuse native 12-slot shelf copying; only this NPC sees the custom list.
shelf=Thumb(0x09000600)
shelf.h(0xB5F0,0x0003) # original push and r3=stock
shelf.literal(1,STATE)
shelf.h(0x68C9,0x2901)
shelf.branch('native',1)
shelf.literal(3,SHELF)
shelf.label('native')
shelf.literal(1,0x03006590)
shelf.h(0x6808)
shelf.literal(2,0x08084A69)
shelf.h(0x4710)
install(shelf,0x08084A60,register=2)

# New item resource IDs do not overwrite or rename any existing item.
resource=Thumb(0x09000700)
resource.h(0xB500)
resource.literal(1,0x0010FF00)
resource.h(0x1A42,0x2A03)
resource.branch('native',8)
resource.h(0x0252) # index * 512
resource.literal(0,ITEMS)
resource.h(0x1880,0xBC02,0x4708)
resource.label('native')
resource.literal(1,0x0856F954)
resource.abs_bl(0x08006A5C)
resource.h(0xBC02,0x4708)
install(resource,0x08006E34)

# Intercept only the shelf's native action, after dialogue/input guards have run.
# Entry hooks would mistake A used to dismiss the welcome for quest confirmation.
confirm=Thumb(0x09000900)
confirm.literal(0,STATE)
confirm.h(0x68C1,0x2901)
confirm.branch('native',1)
confirm.literal(1,0x0300142C)
confirm.h(0x8809,0x2201,0x4011,0x2900)
confirm.branch('native',0)
confirm.literal(1,0x03006590)
confirm.h(0x6809,0x69CA,0x2A16)
confirm.branch('native',1)
confirm.h(0x684A,0x2A03)
confirm.branch('native',8)
confirm.h(0x3201,0x6042,0x2200,0x624A)
confirm.literal(3,0x0807F8E9)
confirm.h(0x4718)
confirm.label('native')
confirm.literal(3,0x0807E45D)
confirm.h(0x4718)
install(confirm)
assert struct.unpack_from('<I',rom,0x7C128)[0]==0x0807E45C
struct.pack_into('<I',rom,0x7C128,confirm.base)

gate=Thumb(0x09000A00)
gate.literal(0,STATE)
gate.h(0x6841,0x3901,0x2903)
gate.branch('allowed',9)
# Reject before native fade starts, and move one tile back from the north trigger.
gate.h(0xB410)
gate.abs_bl(0x080020F4)
gate.h(0x21AC,0x0049,0x4348)
gate.literal(4,0x03003E9C)
gate.h(0x1824)
gate.literal(1,72<<8)
gate.h(0x6021,0x60A1,0xBC10,0x2000)
gate.literal(3,0x08088A73)
gate.h(0x4718)
gate.label('allowed')
gate.abs_bl(0x08015940)
gate.h(0x2003)
gate.abs_bl(0x0801A7B8)
gate.abs_bl(0x0800B544)
gate.literal(3,0x080888E5)
gate.h(0x4718)
install(gate,0x080888CC)
# Entire fade-start sequence is relocated, not left with split BL instructions.
rom[0x888D4:0x888DC]=bytes.fromhex('c046')*4

route=Thumb(0x09000B00)
route.h(0xB410)
route.literal(4,STATE)
route.h(0x6861,0x3901,0x004A,0x1851,0x0089) # index * 12
route.literal(2,0x09002100)
route.h(0x1852)
route.literal(0,0x03005E44)
route.h(0x6800,0x6811,0x8001,0x6851,0x8041,0x6401)
route.h(0x2100,0x8201,0x8381,0x86C1,0x2101,0x60A1) # phase active
route.literal(1,0x71C)
route.h(0x1840,0x6891,0x6001,0xBC10,0x2001)
route.literal(3,0x08088A73)
route.h(0x4718)
install(route,0x080888F0)
for n,(context,room_id,descriptor) in enumerate([(1,7,0x085472FC),(2,9,0x08549430),(3,14,0x0854C564),(4,12,0x0854EEB0)]):
    struct.pack_into('<III',rom,0x1002100+n*12,context,room_id,descriptor)

# Native full transitions into the castle now select the shop hall during a quest.
return_hub=Thumb(0x09000C00)
return_hub.h(0xB410)
return_hub.literal(4,STATE)
return_hub.h(0x68A3,0x2B01)
return_hub.branch('native',1)
return_hub.h(0x2800)
return_hub.branch('native',1)
return_hub.h(0x2101,0x2300,0x6063,0x60E3,0x2302,0x60A3)
return_hub.label('native')
return_hub.h(0xBC10,0xB530,0x0400,0x0C05,0x0409)
return_hub.literal(3,0x08026B1D)
return_hub.h(0x4718)
install(return_hub,0x08026B14)

# Starting another character in the same boot must not inherit a previous quest.
fresh=Thumb(0x09000D00)
fresh.literal(0,STATE)
fresh.h(0x2100,0x6001,0x6041,0x6081,0x60C1)
fresh.literal(3,0x09000001)
fresh.h(0x4718)
install(fresh,0x08022798,register=0)

# Returning via shop room 1 bypasses the castle's original infirmary cleanup.
# Do it at the arrival initializer, after native callers have set spawn selectors.
arrival=Thumb(0x09000E00)
arrival.h(0xB441) # preserve main pointer and r6
arrival.literal(6,STATE)
arrival.h(0x68B1,0x2902)
arrival.branch('native',1)
arrival.abs_bl(0x09001000) # native heal, animation request, then release controls
arrival.abs_bl(0x08056D60) # consume previous room's completion bit
arrival.abs_bl(0x08056DA0) # consume previous exit request
arrival.h(0x2100,0x60B1)
arrival.h(0x0020,0x21AC,0x0049,0x4348) # player index r4 * 344
arrival.literal(2,0x03003E3C)
arrival.h(0x1812,0x6810)
arrival.literal(1,0xFFFFFBFD) # victory-hide (0x400) and cached death-hide (2)
arrival.h(0x4008,0x6010,0xBC41,0x2100,0x86C1)
arrival.branch('placement')
arrival.label('native')
arrival.h(0xBC41)
arrival.label('placement')
arrival.h(0x8EC1,0x00C8,0x1840,0x0080,0x3004,0x183D)
arrival.literal(3,0x080887E3)
arrival.h(0x4718)
data=arrival.finish()
rom[0x1000E00:0x1000E00+len(data)]=data
rom[0x887D6:0x887E2]=struct.pack('<HHHIH',0x4B01,0x4718,0x46C0,arrival.base|1,0x46C0)

# Native boss callbacks normally wait for the exit-request bit (16).
# During an arena quest, the native completion bit (8) triggers the same return.
complete=Thumb(0x09000F00)
complete.literal(0,0x03005E44)
complete.h(0x6800,0x8881)
complete.literal(2,STATE)
complete.h(0x6892,0x2A01)
complete.branch('native',1)
complete.h(0x2218,0x4011,0x2900)
complete.branch('zero',0)
complete.h(0x2001,0x4770)
complete.label('zero')
complete.h(0x2000,0x4770)
complete.label('native')
complete.h(0x0908,0x2101,0x4008,0x4770)
install(complete,0x08056DB8)

# Use the same idle request/control-release ordering as the infirmary's
# resurrection cutscene (0803DC7C..0803DD68). The actor coroutine must consume
# the request before action 12 is cleared: clearing flags alone is overwritten
# by its cached death animation. Two native yields make that ordering explicit.
revive=Thumb(0x09001000)
revive.h(0xB510)
revive.abs_bl(0x08029828)
revive.abs_bl(0x0800C790)
revive.abs_bl(0x0800C8E0)
revive.h(0x2000,0x2100)
revive.abs_bl(0x08029030)
revive.h(0x2000,0x2101)
revive.abs_bl(0x08028FA0)
revive.abs_bl(0x080003F0)
revive.abs_bl(0x080003F0)
revive.abs_bl(0x080020F4)
revive.h(0x21AC,0x0049,0x4348)
revive.literal(1,0x03003E00)
revive.h(0x1840,0x2100,0x8541)
revive.abs_bl(0x080156A4)
revive.h(0xBC10,0xBC08,0x4718)
install(revive)

names=['Colonel Gobovich','Grove Giant','Wizari','Clione']
template=bytes(rom[0x424170+12*388:0x424170+13*388]) # native Valuing Scroll icon
assert len(template)==388
for n,name in enumerate(names):
    item=bytearray(template)
    struct.pack_into('<I',item,372,0) # Quest selection is free, unlike its scroll template.
    def glyph(c):
        if 'A'<=c<='Z':return ord(c)-ord('A')+1
        if 'a'<=c<='z':return ord(c)-ord('a')+33
        if c==' ':return 81
        raise ValueError(c)
    encoded=struct.pack('<'+'H'*(len(name)+1),*[glyph(c) for c in name],0)
    for language in range(6):
        item[language*62:language*62+62]=encoded+bytes(62-len(encoded))
    rom[0x1002400+n*512:0x1002400+n*512+388]=item
    rom[0x1002000+n*16:0x1002000+(n+1)*16]=struct.pack('<8H',1,0xFF00+n,1,0,0,0,0,0)



base_hash=hashlib.sha256(rom).hexdigest()
report=[]
for name,header,pcm_address,songs in [('HUB',0x09004000,0x09010000,[219]),('BATTLE',0x09004400,0x09110000,[11,217])]:
    tone=header+0x100
    track=header+0x20
    pcm=(project/'audio'/'converted'/(name+'-gba.pcm')).read_bytes()
    def put(address,data):
        offset=address-0x08000000
        assert rom[offset:offset+len(data)]==bytes(len(data)),hex(address)
        rom[offset:offset+len(data)]=data
    # One tied note: sample looping lives in WaveData, not timed retriggering.
    code=bytes([0xBC,0,0xBB,60,0xBD,0,0xBE,96,0xBF,64,0xCF,60,127])
    code+=bytes([0xB0,0xB2])+struct.pack('<I',track+13)
    put(track,code)
    put(header,struct.pack('<BBBBII',1,0,1,0x80,tone,track))
    put(tone,struct.pack('<BBBBIBBBB',8,60,0,0,pcm_address,255,0,255,255))
    put(pcm_address,struct.pack('<HHIII',0,0x4000,10512*1024,0,len(pcm))+pcm+bytes(16))
    original=[]
    for song in songs:
        entry=0xBC09C+song*8
        old,player,_=struct.unpack_from('<IHH',rom,entry)
        assert player==0
        original.append(hex(old))
        struct.pack_into('<I',rom,entry,header)
    report.append({'name':name,'songs':songs,'original_headers':original,'new_header':hex(header),'wave':hex(pcm_address),'pcm_bytes':len(pcm)})

# The shipping image must match the image exercised by the emulator tests.
EXPECTED_SHA256='8a96a0f3395d0df494e78060c85b1a3c43053b439c5d78d4bc4a277db341e71b'
digest=hashlib.sha256(rom).hexdigest()
assert digest==EXPECTED_SHA256,(digest,EXPECTED_SHA256)
path=project/'Monster Hunter Souls Arena - v0.2 Quests e Musica.gba'
if path.exists() and hashlib.sha256(path.read_bytes()).hexdigest()!=digest:
    raise FileExistsError('Refusing to overwrite a different ROM: '+str(path))
path.write_bytes(rom)
result={'rom':path.name,'size_bytes':len(rom),'base_quest_sha256':base_hash,
        'sha256':digest,'songs':report}
(project/'audio'/'music-patch-v0.2.json').write_text(json.dumps(result,indent=2))
print(json.dumps(result,indent=2))
