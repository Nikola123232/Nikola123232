"""Re-mix from saved stems (music, sfx, narration) with adjustable levels; no re-synthesis."""
import numpy as np, soundfile as sf, sys
from scipy import signal
R="/home/user/Nikola123232/"; SR=48000
MUS=float(sys.argv[1]); SFX=float(sys.argv[2])
mus,_=sf.read(R+"audio/music/music.wav"); sfx,_=sf.read(R+"audio/sfx/sfx.wav")
vo,vsr=sf.read(R+"audio/vo/narration.wav"); vo=signal.resample_poly(vo,SR,vsr)
N=len(mus); vo=np.pad(vo,(0,max(0,N-len(vo))))[:N]
env=np.convolve(np.abs(vo),np.ones(int(.25*SR))/int(.25*SR),'same')
duck=1-0.65*np.clip(env/(env.max()*.25),0,1)
duck=np.convolve(duck,np.ones(int(.2*SR))/int(.2*SR),'same')
mix=mus*MUS*duck[:,None]+sfx*SFX*(0.5+0.5*duck)[:,None]
mix[:,0]+=vo*0.95; mix[:,1]+=vo*0.95
t=np.arange(N)/SR; mix*=np.clip((N/SR-t)/0.6,0,1)[:,None]
mix/=np.abs(mix).max()/0.95
sf.write(R+"audio/mix_v2.wav",mix.astype(np.float32),SR)
