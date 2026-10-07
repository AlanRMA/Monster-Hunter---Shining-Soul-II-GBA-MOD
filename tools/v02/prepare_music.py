from pathlib import Path
import subprocess
import numpy as np
import wave
import json
import hashlib

project=Path(__file__).resolve().parents[2]
audio=project/'audio'
out=audio/'converted'
out.mkdir(exist_ok=True)
rate=10512 # Verified native m4a mixer frequency in this ROM.
result=[]
for name,source,seconds in [('HUB','hub-5C21ln9supc.wav',90),('BATTLE','battle-CBgmwMqm3ac.wav',96)]:
    source=audio/'sources'/source
    filters='highpass=f=70,lowpass=f=4300,loudnorm=I=-18:TP=-2:LRA=11'
    raw=subprocess.check_output(['ffmpeg','-v','error','-i',str(source),'-t',str(seconds),'-af',filters,'-ac','1','-ar',str(rate),'-f','f32le','pipe:1'])
    samples=np.frombuffer(raw,dtype='<f4').copy()
    overlap=int(1.5*rate)
    ramp=np.linspace(0,1,overlap,dtype=np.float32)
    seam=samples[-overlap:]*(1-ramp)+samples[:overlap]*ramp
    loop=np.concatenate([samples[overlap:-overlap],seam])
    loop=loop[:len(loop)//16*16]
    # Deterministic triangular dither for the hardware's signed 8-bit PCM.
    rng=np.random.default_rng(20261007)
    dither=(rng.random(len(loop))-rng.random(len(loop)))/2
    pcm=np.clip(np.rint(loop*127+dither),-128,127).astype(np.int8)
    (out/(name+'-gba.pcm')).write_bytes(pcm.tobytes())
    with wave.open(str(out/(name+'-retro-loop.wav')),'wb') as w:
        w.setnchannels(1);w.setsampwidth(2);w.setframerate(rate)
        w.writeframes((pcm.astype('<i2')*256).tobytes())
    result.append({'name':name,'source':source.name,'source_sha256':hashlib.sha256(source.read_bytes()).hexdigest(),
                   'source_clip_seconds':seconds,'loop_seconds':len(pcm)/rate,'loop_crossfade_seconds':1.5,
                   'pcm_bytes':len(pcm),'sample_rate':rate,'channels':1,'pcm_bits':8,
                   'filters':filters,'pcm_sha256':hashlib.sha256(pcm.tobytes()).hexdigest()})
(out/'conversion.json').write_text(json.dumps(result,indent=2))
print(json.dumps(result,indent=2))
