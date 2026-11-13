# WHAT IF YOU FELL INTO A VOLCANO? (60 s, 1080x1920, 30 fps)

Final file: `volcano/out/what_if_you_fell_into_a_volcano.mp4`

## Environment (inspected before building)
Blender 5.3.0 (`bpy` module from PyPI), Cycles on 4 CPU cores (no GPU), 15 GB RAM, FFmpeg 6.1, Kokoro v1.0 neural TTS (voice `am_michael`).
Asset sites (Poly Haven, Sketchfab, blender.org) are blocked by the network policy, so **every 3D model is procedural / original**.

## Frame map and narration (frames are 1-based, 30 fps)
| Scene | Frames | Time | Script | Narration (start s) |
|---|---|---|---|---|
| 1 Hook: already falling | 1-60 | 0:00-0:02 | `v12.py` | "What if you fell into a volcano?" (0.12) |
| 2 Frozen above the lava, orbit | 61-150 | 0:02-0:05 | `v12.py` | "You might be dead before you even touch the lava." (2.10) + text BEFORE YOU TOUCH IT?! |
| 3 The fall | 151-420 | 0:05-0:14 | `v3.py` | "As you fall deeper into the crater..." (5.20) |
| 4 Skin: radiant heat, 1st/2nd/3rd degree burns | 421-750 | 0:14-0:25 | `v4.py` | "Exposed lava can reach temperatures above a thousand degrees Celsius..." (14.20) |
| 5 Airways: mouth -> trachea -> bronchi -> lungs | 751-1110 | 0:25-0:37 | `v5.py` | "Breathing hot gases can injure your airways..." (25.20) |
| 6 Contact in extreme slow motion (non-graphic) | 1111-1470 | 0:37-0:49 | `v6.py` | "If you reached the lava, the contact would cause catastrophic burns. But you wouldn't simply sink into it like water." (37.20) |
| 7 Water vs lava (density, viscosity) | 1471-1680 | 0:49-0:56 | `v7.py` | "Lava is much denser and usually far more viscous than water..." (48.30) |
| 8 Pull-away, fade to black | 1681-1800 | 0:56-1:00 | `v8.py` | "And in some volcanic conditions, the heat or gases could kill you before you ever touched the lava." (55.00) |

On-screen text: `BEFORE YOU TOUCH IT?!` (f73-150), `EXTREME HEAT` (f436-540), `DANGEROUS GASES` (f774-884), `LAVA ≠ WATER` (f1476-1680), plus anatomy labels and HUDs.

## Pipeline
| Stage | Tool | Files |
|---|---|---|
| Narration + word timings + subtitles | Kokoro TTS | `scripts/tts.py` -> `audio/vo/narration.wav`, `words.json`, `audio/subtitles.srt` |
| Character (rig, suit, head, skeleton, organs) | Blender Python | `scripts/vol/human.py` (+ `scripts/f1/anatomy.py`) |
| Crater, lava shader, smoke, embers, debris, dynamic surfaces | Blender Python | `scripts/vol/world.py` |
| Airway model (mouth to alveoli) | Blender Python | `scripts/vol/airway.py` |
| Scenes | Blender Cycles (CPU) | `scripts/v12.py v3.py v4.py v5.py v6.py v7.py v8.py` |
| Sound design + music + mix | numpy/scipy | `scripts/audio.py` |
| Heat haze, bloom, grade, HUD, labels, captions, transitions | Pillow/numpy | `scripts/composite.py` |
| Encode, loudness normalisation, mux, validation | FFmpeg/FFprobe | `scripts/assemble.py` |

## Scientific notes
* Lava temperature is quoted only as "above 1,000 °C" (basaltic lava is typically ~1,000-1,200 °C).
* Radiant heat can burn without contact; severity depends on temperature, distance, duration, airflow. The video does not claim death before contact is inevitable ("in some volcanic conditions").
* Gases: hot gas inhalation injures the airway lining; toxic or oxygen-poor air can cause loss of consciousness.
* Skin: epidermis / dermis / hypodermis with follicle, sweat gland, vessels, nerve endings; burn depth 1st (reddening), 2nd (blisters), 3rd (full thickness). No gore.
* Lava: density ≈ 2,600 kg/m³ (basalt) vs water 1,000; viscosity ≈ 10²-10⁵ Pa·s vs water 0.001 Pa·s. A body (≈985 kg/m³) floats high on lava and does not sink; a steel sphere sinks fast in water, slowly in lava.
