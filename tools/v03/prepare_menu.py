"""Fit generated forest artwork into the native 4bpp title, keeping font bank 15."""
from pathlib import Path
import shutil,struct,json,hashlib,sys
import numpy as np
from scipy.cluster.vq import kmeans2
from PIL import Image,ImageFilter,ImageEnhance
from gba_lz import compress,decompress
P=Path(__file__).resolve().parents[2]
OUT=P/'assets/menu-v03';OUT.mkdir(parents=True,exist_ok=True)
SOURCE=Path(sys.argv[1]).resolve() if len(sys.argv)>1 else OUT/'forest-source.png'
if SOURCE.resolve()!=(OUT/'forest-source.png').resolve():shutil.copy2(SOURCE,OUT/'forest-source.png')
image=Image.open(SOURCE).convert('RGB').resize((240,160),Image.Resampling.LANCZOS)
image=ImageEnhance.Color(image).enhance(1.08).filter(ImageFilter.UnsharpMask(radius=.5,percent=90,threshold=2))
image.save(OUT/'forest-240x160.png')
pixels=np.asarray(image).astype(np.float32)
tiles=pixels.reshape(20,8,30,8,3).transpose(0,2,1,3,4).reshape(600,64,3)
features=np.concatenate([tiles.mean(axis=1),tiles.std(axis=1)],axis=1)
_,groups=kmeans2(features,15,minit='++',iter=30,seed=20261007)
weight=np.array([1,1.25,.8],np.float32)
palettes=[]
for iteration in range(6):
    palettes=[]
    for g in range(15):
        members=tiles[groups==g].reshape(-1,3)
        if not len(members):members=tiles[g*40].copy()
        q=Image.fromarray(np.uint8(members).reshape(1,-1,3)).quantize(colors=15,method=Image.Quantize.MEDIANCUT)
        colors=np.asarray(q.getpalette(),dtype=np.float32).reshape(-1,3)[:15]
        colors=np.rint(colors*31/255).astype(np.int32)
        palettes.append(np.unique(colors,axis=0))
    errors=np.empty((600,15),np.float32)
    for g,p in enumerate(palettes):
        colors=p.astype(np.float32)*255/31
        distances=((tiles[:,:,None,:]-colors[None,None,:,:])*weight)**2
        errors[:,g]=distances.sum(axis=3).min(axis=2).sum(axis=1)
    groups=errors.argmin(axis=1)
base=(P/'Monster Hunter Souls Arena - v0.2 Quests e Musica.gba').read_bytes()
pal=bytearray(base[0x5ecb9c:0x5ecb9c+512]);preview=np.zeros((600,64,3),np.uint8)
for g,p in enumerate(palettes):
    values=[0]+[int(r|(gg<<5)|(b<<10)) for r,gg,b in p]
    pal[g*32:(g+1)*32]=struct.pack('<16H',*(values+[0]*(16-len(values))))
encoded=bytearray(32);lookup={bytes(32):0};entries=[0]*1024
for n,t in enumerate(tiles):
    g=int(groups[n]);colors=palettes[g].astype(np.float32)*255/31
    indices=(((t[:,None,:]-colors[None,:,:])*weight)**2).sum(axis=2).argmin(axis=1)
    preview[n]=np.rint(colors[indices]).astype(np.uint8)
    indices=indices+1
    tile=bytes(indices[i]|(indices[i+1]<<4) for i in range(0,64,2))
    if tile not in lookup:lookup[tile]=len(encoded)//32;encoded.extend(tile)
    entries[(n//30)*32+n%30]=lookup[tile]|(g<<12)
original_map=decompress(base[0x589784:0x589dc0])
tilemap=struct.pack('<1024H',*entries)+original_map[2048:]
packed=compress(tilemap)
assert decompress(packed)==tilemap
assert len(packed)<=0x589dc0-0x589784,len(packed)
assert len(encoded)<=0x8000
(OUT/'tiles.bin').write_bytes(encoded+bytes(0x8000-len(encoded)))
(OUT/'palette.bin').write_bytes(pal)
(OUT/'map.lz').write_bytes(packed)
preview=preview.reshape(20,30,8,8,3).transpose(0,2,1,3,4).reshape(160,240,3)
Image.fromarray(preview).save(OUT/'forest-gba-preview.png')
report={'source':'forest-source.png','source_sha256':hashlib.sha256(SOURCE.read_bytes()).hexdigest(),
        'resolution':[240,160],'palette_banks':15,'native_font_bank_preserved':15,
        'opaque_colors':len(set(struct.unpack('<240H',pal[:480])))-1,'unique_tiles':len(lookup),
        'compressed_map_bytes':len(packed),'compressed_map_capacity':1596,
        'palette_strategy':'15 local 15-color palettes; RGB555; opaque indices 1..15; no dithering'}
(OUT/'encoding.json').write_text(json.dumps(report,indent=2));print(json.dumps(report,indent=2))
