# Production report: "What If You Fell Into a Volcano?"

**Deliverable:** `volcano/out/what_if_you_fell_into_a_volcano.mp4`
ffprobe-verified: H.264 High, 1080x1920, 30 fps, 60.000 s, 1800 decoded frames, AAC 48 kHz stereo, 84.9 MB. Only black frames: the intended fade-out at 59.70-59.97 s. Integrated loudness about -15 LUFS.

## Other deliverables
| Item | Path |
|---|---|
| Blender projects (one per script, scenes 1-8) | `volcano/blend/v12.blend v3 v4 v5 v6 v7 v8` |
| Python scripts (scene, character, world, airway, audio, composite, assemble) | `volcano/scripts/` |
| Narration audio (+ word timings) | `volcano/audio/vo/narration.wav`, `words.json` |
| Subtitles | `volcano/audio/subtitles.srt` (burned-in animated captions are in the video) |
| Sound effects / music / full mix stems | `volcano/audio/sfx.wav`, `music.wav`, `mix.wav` |
| Storyboard + frame map | `volcano/STORYBOARD.md` |
| 5-second hook preview | `volcano/previews/hook_5s_preview.mp4` |

## How it was rendered
Blender 5.3 (`bpy`), Cycles on **4 CPU cores, no GPU**. 3D frames are rendered at **720x1280 with 12 samples (3.5 s cap/frame, OIDN denoise), then upscaled to 1080x1920** and sharpened; all text, HUDs and captions are drawn at full 1080x1920. Total about 1800 frames x 7-9 s. Heat haze, bloom, grade, film grain, dissolves and the fade are done in the compositor (Pillow/numpy). FFmpeg does the encode, loudness normalisation (-14 LUFS target), mux and ffprobe checks.

## Limitations (honest list)
1. **No downloaded assets.** Poly Haven / Sketchfab / blender.org are blocked in this sandbox, so *every* model is original and procedural: character, crater, lava, skin section, airway, tanks. The character has a modelled head (face, ears, eyes, hair), a hi-vis coverall with reflective bands, a full articulated skeleton, organs and brain, but it is **stylised, not a photo-real scanned human**. Faces are cartoon-like, the hairline is slightly jagged, and the shoulder deformation shows small mesh creases when the arms are raised.
2. **Resolution.** 3D at 720x1280 upscaled (see above); a native 1080x1920 render would be sharper and take about 3-4x longer (set `CYCLES_TIME_LIMIT=0` and `res=(1080,1920)` in `vol/util.py`).
3. **Voice** is a neural TTS (Kokoro `am_michael`), natural but not a human performance. The last two narration lines are slightly faster (1.3x) to fit their windows. Lines 3-5 end earlier than their scenes, leaving a few seconds of music/SFX only.
4. **I could not listen to the audio** (no audio device); levels and timing were verified by measurement (LUFS, waveform/spectrogram), not by ear. Music/SFX are synthesised and may sound more synthetic than a produced track.
5. **Physics is stylised but grounded**: fall speed, slow-motion, viscous ripples and density behaviour are plausible, not a fluid simulation. The Scene 6/7 liquid-surface ripples are driven by a Python frame handler, so opening those `.blend` files and rendering needs the matching script (the handler is not saved in the `.blend`).
6. Scene 4 (face close-up) places the face behind the caption area, so captions overlap it. Scene 5 bronchial tunnel section was shortened because wall surfaces looked flat at that scale; the bronchial tree is shown from outside through translucent lungs instead.
7. Scientific values shown on screen are typical: water 1,000 kg/m³ and 0.001 Pa·s, basaltic lava ~2,600 kg/m³ and ~10²-10⁵ Pa·s. Real lava varies with composition and temperature.
