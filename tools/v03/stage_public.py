"""Copy an explicit publication allowlist to an already inspected Git clone."""
from pathlib import Path
import argparse, shutil, subprocess, json, hashlib
P=Path(__file__).resolve().parents[2]
parser=argparse.ArgumentParser()
parser.add_argument('checkout',type=Path)
args=parser.parse_args();dest=args.checkout.resolve()
remote=subprocess.check_output(['git','remote','get-url','origin'],cwd=dest,text=True).strip()
assert remote=='https://github.com/AlanRMA/Monster-Hunter---Shining-Soul-II-GBA-MOD.git'
assert not subprocess.check_output(['git','status','--porcelain'],cwd=dest,text=True).strip()
files=[P/name for name in ['README.md','.gitignore','TESTE-v0.3.md','mod-v0.3.json',
                         'bridge.lua','json.lua','release/patch.json',
                         'release/Monster-Hunter-Souls-Arena-v0.3-native-audio.bps']]
files += sorted(p for p in (P/'tools').rglob('*') if p.is_file() and p.suffix in ['.py','.s'])
files += sorted(p for p in (P/'assets/menu-v03').iterdir() if p.suffix in ['.png','.json','.bin','.lz'])
files += [P/name for name in ['audio/converted/conversion.json',
                            'audio/converted/menu-conversion.json','audio/music-patch-v0.2.json']]
for variant in ['v03','v03-public']:
    files += sorted((P/'validation'/variant).glob('*.json'))
    for name in ['main-menu','south-question','south-choice','fresh-hub','purchase-feedback',
                 'saved-scroll-resumed','reset-save-resumed','arena-1','hub-after-1','inventory-used']:
        files.append(P/'validation'/variant/(name+'.png'))
assert len(files)==len(set(files))
for source in files:
    assert source.is_file(),source
    assert source.suffix not in ['.gba','.sav','.wav','.pcm','.mp3','.mp4','.state']
    relative=source.relative_to(P);target=dest/relative;target.parent.mkdir(parents=True,exist_ok=True)
    if relative.name.endswith('.json') and 'validation' in relative.parts:
        # Only the temp diagnostic location is omitted; all evidence is retained.
        data=json.loads(source.read_text());data.pop('isolated_test_directory',None)
        target.write_text(json.dumps(data,indent=2)+'\n')
    else:shutil.copy2(source,target)
report={str(source.relative_to(P)):hashlib.sha256((dest/source.relative_to(P)).read_bytes()).hexdigest()
        for source in files}
print(json.dumps({'file_count':len(files),'bytes':sum((dest/source.relative_to(P)).stat().st_size for source in files),
                  'sha256_by_path':report},indent=2))
