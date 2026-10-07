"""Export a public delta only: no original ROM, player saves or downloaded music."""
from pathlib import Path
import sys, json, hashlib, struct, zlib
import numpy as np
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from apply_patch import apply
P = Path(__file__).resolve().parents[2]

def number(value):
    out = bytearray()
    while True:
        byte = value & 127; value >>= 7
        if not value:
            out.append(byte | 128); return bytes(out)
        out.append(byte); value -= 1

def create_bps(source, target, metadata):
    out = bytearray(b'BPS1')
    out += number(len(source))+number(len(target))+number(len(metadata))+metadata
    matches = np.zeros(len(target), dtype=np.bool_)
    n = min(len(source),len(target))
    matches[:n] = np.frombuffer(source,dtype=np.uint8)[:n] == np.frombuffer(target,dtype=np.uint8)[:n]
    # SourceRead where unchanged; TargetRead elsewhere; RLE for appended zeros.
    modes = np.ones(len(target),dtype=np.uint8); modes[matches] = 0
    modes[n:] = np.where(np.frombuffer(target,dtype=np.uint8)[n:] == 0, 3, 1)
    cuts = np.r_[0,np.flatnonzero(modes[1:] != modes[:-1])+1,len(target)]
    dst_relative = 0
    for start,end in zip(cuts[:-1],cuts[1:]):
        start,end = int(start),int(end); length = end-start; mode = int(modes[start])
        if mode == 0:
            out += number((length-1)<<2)
        elif mode == 1:
            out += number(((length-1)<<2)|1)+target[start:end]
        else:
            # Seed a zero, then overlap-copy it as many times as necessary.
            out += number(1)+b'\0'; start += 1; length -= 1
            if length:
                relative = start-1-dst_relative
                out += number(((length-1)<<2)|3)
                out += number((abs(relative)<<1)|(relative<0))
                dst_relative = start-1+length
    out += struct.pack('<II',zlib.crc32(source),zlib.crc32(target))
    out += struct.pack('<I',zlib.crc32(out))
    result = bytes(out)
    assert apply(source,result) == target
    return result

def main():
    source = (P/'Shining Soul II (USA).gba').read_bytes()
    full = (P/'Monster Hunter Souls Arena - v0.3 Hunts.gba').read_bytes()
    assert hashlib.sha256(source).hexdigest() == 'b31c19d2d25683a0941d5d501912b5f21d4590cd7071fa01882e62aa5227a7c9'
    target = bytearray(full)
    # Restore the original song pointers and remove ALL three external samples,
    # tones and track headers. Gameplay code and menu graphics are unchanged.
    for song in [11,197,217,219]:
        off = 0xbc09c+song*8
        target[off:off+8] = source[off:off+8]
    target[0x1004000:0x1004c00] = bytes(0xc00)
    music = json.loads((P/'audio/converted/conversion.json').read_text())
    if isinstance(music,dict): music = music.get('conversion',music.get('tracks',music))
    assert isinstance(music,list)
    for off,item in zip([0x1010000,0x1110000],music):
        length = item['pcm_bytes']+32
        target[off:off+length] = bytes(length)
    length = json.loads((P/'audio/converted/menu-conversion.json').read_text())['pcm_bytes']+32
    target[0x1310000:0x1310000+length] = bytes(length)
    target = bytes(target)
    release = P/'release'; release.mkdir(exist_ok=True)
    metadata = {'name':'Monster Hunter Souls Arena','version':'0.3',
                'audio':'original game music; downloaded tracks not distributed'}
    patch = create_bps(source,target,json.dumps(metadata).encode())
    (release/'Monster-Hunter-Souls-Arena-v0.3-native-audio.bps').write_bytes(patch)
    # Ignored local diagnostic target, never part of the public file allowlist.
    (release/'Monster Hunter Souls Arena - v0.3 Native Audio.gba').write_bytes(target)
    info = {'patch':'Monster-Hunter-Souls-Arena-v0.3-native-audio.bps',
            'source_sha256':hashlib.sha256(source).hexdigest(),
            'target_sha256':hashlib.sha256(target).hexdigest(),
            'local_custom_music_rom_sha256':hashlib.sha256(full).hexdigest(),
            'patch_sha256':hashlib.sha256(patch).hexdigest(),
            'patch_bytes':len(patch),'target_bytes':len(target),
            'music':'Original game music in public patch; custom tracks remain local',
            'roundtrip_byte_identical':True}
    (release/'patch.json').write_text(json.dumps(info,indent=2)+'\n')
    print(json.dumps(info,indent=2))

if __name__ == '__main__': main()
