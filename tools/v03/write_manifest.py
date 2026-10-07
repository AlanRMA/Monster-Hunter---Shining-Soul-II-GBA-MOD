"""Record only the exact ROMs for which all final validation reports passed."""
from pathlib import Path
import json, hashlib
P=Path(__file__).resolve().parents[2]
def digest(path):return hashlib.sha256(path.read_bytes()).hexdigest()
rom=P/'Monster Hunter Souls Arena - v0.3 Hunts.gba';sha=digest(rom)
public=json.loads((P/'release/patch.json').read_text())
assert public['local_custom_music_rom_sha256']==sha
reports={}
for variant,expected,names in [('v03',sha,['hunts','regressions','audio']),
                             ('v03-public',public['target_sha256'],['hunts','regressions'])]:
    records=[]
    for name in names:
        data=json.loads((P/'validation'/variant/(name+'.json')).read_text())
        assert data['rom_sha256']==expected,(variant,name)
        assert data['tests'] and all(row['passed'] for row in data['tests'])
        records.append({'report':f'validation/{variant}/{name}.json','passed_tests':len(data['tests'])})
    reports[variant]=records
originals={
    'Shining Soul II (USA).gba':'b31c19d2d25683a0941d5d501912b5f21d4590cd7071fa01882e62aa5227a7c9',
    'Monster Hunter Souls Arena - v0.1 Hub.gba':'b78d2d7b118d34543222164bd067cff574cdaa031476b088855c7534d1cc9303',
    'Monster Hunter Souls Arena - v0.2 Quests e Musica.gba':'8a96a0f3395d0df494e78060c85b1a3c43053b439c5d78d4bc4a277db341e71b'}
for name,expected in originals.items():assert digest(P/name)==expected,name
result={
    'name':'Monster Hunter Souls Arena','version':'0.3-hunts','date':'2026-10-07',
    'rom':rom.name,'sha256':sha,'size_bytes':rom.stat().st_size,'requires_lua':False,
    'public_patch':public,'starting_gold_new_character':1000,
    'contracts':[{'selection':i+1,'item_id':hex(0xff00+i),'boss':name,'price':price,
                  'context':i+1,'room':room,'permitted_deaths':2}
                 for i,(name,price,room) in enumerate(zip(
                     ['Colonel Gobovich','Grove Giant','Wizari','Clione'],[20,40,70,100],[7,9,14,12]))],
    'activation':'Purchase stores scroll; inventory USE consumes it and activates one hunt',
    'flow':{'new_character':'hub; book opening skipped','continue':'hub; unused items and gold preserved',
            'death_1':'hub; heal; one death remains; native boss tasks cleaned',
            'death_2':'hub; hunt expires; north gate locked','victory':'hub; hunt ends',
            'reentry':'native arena reload; full boss HP','side_exits':'blocked',
            'south':'native save/title confirmation; two pages then Yes/No',
            'south_text':'Would you like to return main title? (You are currently in single player mode).',
            'boss_introductions':'dialogues skipped; original scripts retained',
            'boss_victory_dialogues':'preserved'},
    'save':{'unused_scrolls_saved':True,'gold_saved':True,'activated_hunt_saved':False,
            'legacy_save_import_verified':False},
    'purchase_feedback':{'native_success_sfx':95,'native_failure_sfx':97,
                         'holding_A_repeats':False,'no_charge_when_bag_full_or_poor':True},
    'title_art':json.loads((P/'assets/menu-v03/encoding.json').read_text()),
    'music':{'local_custom_music':True,'public_downloaded_audio_distributed':False,
             'menu':json.loads((P/'audio/converted/menu-conversion.json').read_text()),
             'hub_and_battle':json.loads((P/'audio/converted/conversion.json').read_text()),
             'native_driver':'M4A/MP2K; signed 8-bit PCM mono 10512 Hz'},
    'preserved':{'hp_green':True,'sp_yellow':True,'other_npc_stock':True,
                 'original_roms_checked':originals,'existing_saves_not_modified_by_tests':True},
    'verification':{'emulator':'mGBA 0.10.5 isolated macOS core',
                    'native_returns_per_variant':12,'reports':reports,
                    'HP_and_position_writes':'only in isolated diagnostic cores',
                    'patch_roundtrip_identical':True,
                    'independent_BPS_applier':'Floating IPS / Flips; exact target hash matched'},
    'limits':['active hunt not persisted','full manual campaign not tested','balance not changed',
              'custom drops/rewards not added','new bosses not added','multiplayer unchanged'],
    'rebuild_script':'tools/v03/build_v03.py','runtime_source':'tools/v03/runtime.s',
    'state_address':'0x0203FF00','state_reserved_bytes':256}
(P/'mod-v0.3.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps({'rom_sha256':sha,'public_target_sha256':public['target_sha256'],
                  'passed_reports':reports,'originals_verified':len(originals)},indent=2))
