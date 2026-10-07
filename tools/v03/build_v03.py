"""Versioned v0.3 patch; never changes original/v0.1/v0.2 or their saves."""
from pathlib import Path
import hashlib, struct, subprocess, json
PROJECT=Path(__file__).resolve().parents[2]
ROOT=Path(__file__).parent
BASE=PROJECT/'Monster Hunter Souls Arena - v0.2 Quests e Musica.gba'
OUTPUT=PROJECT/'Monster Hunter Souls Arena - v0.3 Hunts.gba'
BASE_HASH='8a96a0f3395d0df494e78060c85b1a3c43053b439c5d78d4bc4a277db341e71b'
def build():
    rom=bytearray(BASE.read_bytes())
    assert hashlib.sha256(rom).hexdigest()==BASE_HASH
    tool='/opt/devkitpro/devkitARM/bin/arm-none-eabi-'
    subprocess.run([tool+'as','-mcpu=arm7tdmi','-mthumb','-o',str(ROOT/'runtime.o'),str(ROOT/'runtime.s')],check=True)
    subprocess.run([tool+'ld','-Ttext=0x09006000','-e','gate','-o',str(ROOT/'runtime.elf'),str(ROOT/'runtime.o')],check=True)
    subprocess.run([tool+'objcopy','-O','binary',str(ROOT/'runtime.elf'),str(ROOT/'runtime.bin')],check=True)
    symbols={}
    for line in subprocess.check_output([tool+'nm',str(ROOT/'runtime.elf')],text=True).splitlines():
        parts=line.split()
        if len(parts)==3: symbols[parts[2]]=int(parts[0],16)
    data=(ROOT/'runtime.bin').read_bytes()
    assert len(data)<=0x2000,'Runtime overlaps the custom dialogue resource'
    assert rom[0x1006000:0x1006000+len(data)]==bytes(len(data))
    rom[0x1006000:0x1006000+len(data)]=data
    def hook(site,address):
        off=site-0x08000000
        assert site%4==0
        rom[off:off+8]=struct.pack('<HHI',0x4b00,0x4718,address|1)
    struct.pack_into('<I',rom,0x7c128,symbols['purchase'])
    hook(0x0805bcc8,symbols['use_scroll'])
    hook(0x09000d00,symbols['fresh'])
    hook(0x09000c00,symbols['return_hub'])
    hook(0x08006a5c,symbols['resources'])
    hook(0x0805df00,symbols['dialogue'])
    hook(0x09000a00,symbols['gate'])
    # This is the normal Continue branch, not the separate suspend loader.
    assert rom[0x226b8:0x226c0]==bytes.fromhex('0421012200f0fcfc')
    hook(0x080226b8,symbols['resume_hub'])
    for i,price in enumerate([20,40,70,100]):
        struct.pack_into('<I',rom,0x1002400+512*i+372,price)
    # Native title resource: reserve font bank 15 and preserve map metadata.
    assets=PROJECT/'assets/menu-v03'
    tiles=(assets/'tiles.bin').read_bytes();palette=(assets/'palette.bin').read_bytes()
    tilemap=(assets/'map.lz').read_bytes()
    assert len(tiles)==0x8000 and len(palette)==512 and len(tilemap)<=1596
    rom[0x5e4b9c:0x5ecb9c]=tiles
    rom[0x5ecb9c:0x5ecd9c]=palette
    rom[0x589784:0x589dc0]=tilemap+bytes(1596-len(tilemap))
    # Verified title track is song 197; the sound-effects table remains intact.
    pcm=(PROJECT/'audio/converted/MENU-gba.pcm').read_bytes()
    header=0x09004800;tone=header+0x100;track=header+0x20;wave=0x09310000
    def put(address,data):
        off=address-0x08000000
        assert rom[off:off+len(data)]==bytes(len(data)),hex(address)
        rom[off:off+len(data)]=data
    code=bytes([0xbc,0,0xbb,60,0xbd,0,0xbe,96,0xbf,64,0xcf,60,127,0xb0,0xb2])+struct.pack('<I',track+13)
    put(track,code);put(header,struct.pack('<BBBBII',1,0,1,0x80,tone,track))
    put(tone,struct.pack('<BBBBIBBBB',8,60,0,0,wave,255,0,255,255))
    put(wave,struct.pack('<HHIII',0,0x4000,10512*1024,0,len(pcm))+pcm+bytes(16))
    assert struct.unpack_from('<IHH',rom,0xbc09c+197*8)==(0x0835bdd8,0,0)
    struct.pack_into('<I',rom,0xbc09c+197*8,header)
    # Keep the native short dialogue pages and Yes/No control. Do not enlarge
    # native text buffers or force all four lines onto a single page.
    glyphs={' ':81,'.':79,'?':60,'(':86,')':87}
    def glyph(c):
        if 'A'<=c<='Z':return ord(c)-ord('A')+1
        if 'a'<=c<='z':return ord(c)-ord('a')+33
        return glyphs[c]
    values=[0,1]
    for i,line in enumerate(['Would you like to return','main title?',
                            '(You are currently in','single player mode).']):
        if i:
            # Native next-page control also expects a new speaker/voice header.
            # Avoid rendering a third row from the two-row text scratch buffer.
            values.extend([0xfffe,0,1] if i==2 else [0xffff])
        values.extend(glyph(c) for c in line)
    values.append(0xfffd)
    put(0x09008000,struct.pack('<'+'H'*len(values),*values))
    struct.pack_into('<I',rom,0x3d8d18+0x3d6*4,0x09008000)
    OUTPUT.write_bytes(rom)
    (ROOT/'symbols.json').write_text(json.dumps(symbols,indent=2))
    print(str(OUTPUT),hashlib.sha256(rom).hexdigest())
    return OUTPUT
if __name__=='__main__':build()
