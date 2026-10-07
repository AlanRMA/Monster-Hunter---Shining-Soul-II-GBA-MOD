"""Convert the title theme to native signed 8-bit PCM with a smooth sample loop."""
from pathlib import Path
import subprocess,numpy as np,wave,json,hashlib
P=Path(__file__).resolve().parents[2];OUT=P/'audio/converted'
source=P/'audio/sources/menu-Fj4o3q659Z4.wav';rate=10512;seconds=96
filters='highpass=f=70,lowpass=f=4300,loudnorm=I=-18:TP=-2:LRA=11'
raw=subprocess.check_output(['/opt/homebrew/bin/ffmpeg','-v','error','-i',str(source),'-t',str(seconds),
    '-af',filters,'-ac','1','-ar',str(rate),'-f','f32le','pipe:1'])
samples=np.frombuffer(raw,dtype='<f4').copy();overlap=int(rate*1.5)
ramp=np.linspace(0,1,overlap,dtype=np.float32)
seam=samples[-overlap:]*(1-ramp)+samples[:overlap]*ramp
loop=np.concatenate([samples[overlap:-overlap],seam]);loop=loop[:len(loop)//16*16]
rng=np.random.default_rng(20261007);dither=(rng.random(len(loop))-rng.random(len(loop)))/2
pcm=np.clip(np.rint(loop*127+dither),-128,127).astype(np.int8)
(OUT/'MENU-gba.pcm').write_bytes(pcm.tobytes())
with wave.open(str(OUT/'MENU-retro-loop.wav'),'wb') as w:
    w.setnchannels(1);w.setsampwidth(2);w.setframerate(rate);w.writeframes((pcm.astype('<i2')*256).tobytes())
report={'name':'MENU','url':'https://www.youtube.com/watch?v=Fj4o3q659Z4',
        'source_sha256':hashlib.sha256(source.read_bytes()).hexdigest(),'source_clip_seconds':seconds,
        'loop_seconds':len(pcm)/rate,'loop_crossfade_seconds':1.5,'pcm_bytes':len(pcm),
        'sample_rate':rate,'channels':1,'pcm_bits':8,'preview_container_bits':16,'filters':filters,
        'pcm_sha256':hashlib.sha256(pcm.tobytes()).hexdigest()}
(OUT/'menu-conversion.json').write_text(json.dumps(report,indent=2));print(json.dumps(report,indent=2))
