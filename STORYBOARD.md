# F1 Crash Short: Production Plan and Storyboard

**Title:** WHAT HAPPENS TO YOUR BODY IF YOU CRASH AN F1 CAR AT 300 KM/H?
**Format:** 1080×1920 (9:16), 30 fps, about 60 s (1800 frames), H.264 + AAC MP4
**Output:** `out/final_f1_crash_short.mp4`

## Pipeline

| Stage | Tool | Script |
|---|---|---|
| Narration (neural TTS, Kokoro v1.0 `am_michael`) | kokoro-onnx | `scripts/tts.py` |
| 3D assets (car, track, driver, anatomy, safety systems) | Blender 5.3 `bpy` | `scripts/f1lib.py` |
| Shots 1–6, animation + render | Blender Cycles (CPU) | `scripts/scene*.py` |
| SFX + music (procedurally synthesised) | numpy | `scripts/audio.py` |
| Subtitles, HUD, callouts, transitions, grade, upscale | Pillow + numpy | `scripts/composite.py` |
| Mux and encode | FFmpeg | `scripts/assemble.py` |

### Environment constraints and trade-offs
* There's no GPU. Rendering runs on 4 CPU cores. EEVEE only runs through Mesa llvmpipe, at about 14 s per frame. Cycles at full 1080×1920 takes about 21 s per frame even for trivial scenes.
* **Decision:** Cycles renders at an internal **720×1280** with 10–12 samples, adaptive sampling, a **5 s per-frame sampling cap** and OpenImageDenoise. It's then upscaled with Lanczos and an unsharp mask to 1080×1920. All 2D overlays (subtitles, labels, HUD, titles) are drawn at full 1080×1920, so text stays crisp.
  * Trade-off: the 3D imagery is a little softer than a native 1080p render, and motion-blurred backgrounds show slight denoiser blotchiness. Re-rendering at full resolution needs no code changes (`render_settings(res=(1080,1920))`, `CYCLES_TIME_LIMIT=0`) and would take about 3–4× longer.
* Asset sites (Poly Haven, Sketchfab, blender.org) are blocked by the network policy. **All 3D models are therefore built procedurally in Python**: lofted cross-sections, airfoil extrusions, lathed tyres, skin-modifier bodies and curve-built ribs. None of them are primitive placeholders.
* Music and SFX are synthesised from scratch in numpy (engine harmonics with Doppler, impact layers, whooshes, heartbeat, cinematic pulse bed). That makes them original and royalty-free.

## Narration timeline (seconds)

| # | Window | Line |
|---|---|---|
| 1 | 0.3 – 8 | What would actually happen to your body if you crashed a Formula One car at three hundred kilometers per hour? |
| 2 | 8.3 – 18 | At this speed, the danger isn't just the impact. It's how quickly your body is forced to stop. |
| 3 | 18.3 – 33 | Your seat belts restrain your body, but your brain and internal organs can still experience dangerous forces. Severe crashes can cause concussions, neck injuries, or internal trauma. |
| 4 | 33.3 – 45 | And your head and neck are especially vulnerable. That's why Formula One drivers wear specialized helmets and head-and-neck restraints. |
| 5 | 45.3 – 56 | Modern Formula One cars are designed to absorb crash energy, while multiple safety systems work together to protect the driver. |
| 6 | 56.1 – 60 | At three hundred kilometers per hour, survival depends on how the crash happens. |

## Shot list

### Scene 1: 0:00–0:08 (f 1–240) "Flat out"
* 1A (0–3.5 s): Low tracking camera just above the asphalt, front-three-quarter view. The car passes the camera at 300 km/h, wheels spin with motion blur, and kerbs and boards streak past.
* 1B (3.5–8 s): Side tracking shot, low and long lens, slowly orbiting to a rear three-quarter view. HUD speedometer reads 300 KM/H. Hook title at the top.

### Scene 2: 0:08–0:18 (f 241–540) "Loss of control"
* 2A (8–11.5 s): Chase cam from behind. The rear steps out (oversteer snap) and the car yaws about 35° and slides across the run-off toward the TecPro barrier.
* 2B (11.5–15 s): Side view in slow motion (time ramp). The car hits the barrier at an angle. The front wing and nose tip shear away, a wheel tether stretches, carbon shards and sparks fly, the TecPro blocks compress, and the car decelerates over about 1 m of crush. HUD: speed drops from 214 to 0 km/h and a G-meter spikes to "50+ g".
* 2C (15–18 s): Dust settles and the camera pushes toward the cockpit, the halo and the driver's helmet. A white flash bridges into Scene 3.

### Scene 3: 0:18–0:33 (f 541–990) "Inside the body"
* Dark "x-ray studio". The cockpit tub is rendered as ghost carbon. The driver is seated in the real driving posture (reclined, legs raised).
* The skin fades to a translucent fresnel shell, revealing the skeleton (skull, 24 vertebrae, 24 ribs, sternum, clavicles, scapulae, pelvis, limbs), brain, heart, lungs, liver, stomach, kidneys and intestines.
* The deceleration pulse plays twice in slow motion. Speed-lines on the floor stop abruptly. The harness holds the torso, while the organs and brain lag a few millimetres (damped oscillation, no deformation gore).
* Arrows: red "DECELERATION" (opposite to travel); yellow "INERTIA" on the brain, heart and abdomen; blue "HARNESS" at the shoulders and hips.
* Callouts: BRAIN, HEART, LUNGS, LIVER, CERVICAL SPINE. Camera: slow orbit and push from a wide 3/4 view to a torso close-up.

### Scene 4: 0:33–0:45 (f 991–1350) "Head and neck"
* 4A: Close-up of the helmet and translucent head: skull, brain, cerebrospinal-fluid gap. Rapid deceleration: the brain shifts slightly forward. A soft glow at the front (coup) and back (contrecoup) marks the regions at risk.
* 4B: Neck. Cervical vertebrae flex under the head's inertia, and a red stress highlight appears on the neck.
* 4C: The HANS device is highlighted on the shoulders and its tethers catch the helmet. The flexion is visibly reduced and the stress highlight turns green.

### Scene 5: 0:45–0:56 (f 1351–1680) "Survival systems": exploded view
* Dark studio with a reflective floor and a slow orbit. The components fly into place around the driver, each with a callout:
  survival cell (carbon monocoque), front/side/rear energy-absorbing crash structures, six-point harness, HANS device, halo, helmet.

### Scene 6: 0:56–1:00 (f 1681–1800) "Survival by design"
* Back at the crash site, golden-hour light. The intact survival cell, the halo and the driver are safe. The camera cranes up and out, and the final title card reads **SURVIVAL BY DESIGN**.

## Audio
* VO −14 LUFS-ish target, ducking music under narration.
* SFX: engine (harmonics of firing frequency, Doppler pass-by), tyre screech, impact (sub thump + carbon crack + debris rattle), slow-mo whoosh, heartbeat and low drone in the anatomy scenes, UI blips for callouts, a riser into the final title.

## Implementation notes
* `scripts/f1/core.py`: material library (livery shader in car-local coordinates, carbon twill, x-ray/reveal shaders), loft/tube/lathe/airfoil builders, camera helpers.
* `scripts/f1/car.py`: car built from 16 lofted monocoque sections, 8 sidepod sections, NACA-4 wing elements, lathed 18" tyres with compound bands, wishbone suspension, halo and mirrors.
* `scripts/f1/track.py`: 1.4 km straight into a 60 m-radius left-hander with kerbs, asphalt run-off, three-row TecPro barrier, walls with fictional sponsor boards, catch fencing, grandstands and trees.
* `scripts/f1/anatomy.py`: armature-rigged metaball skin; 24 vertebrae with discs; 12 rib pairs with costal cartilage; sternum, clavicles, scapulae, pelvis and long bones; brain with procedural gyri; heart, lungs, liver, stomach, kidneys, intestines and vessels.
* `scripts/f1/gear.py`: helmet, HANS with Stretch-To tethers, six-point harness, seat.
* `scripts/f1/story.py`: one physical timeline with a slow-motion time ramp. Slide at 1.1 g, then impact at about 183 km/h with 3.2 m of crush, so the deceleration pulse peaks at about 58 g. That's comparable to documented F1 crash peaks of roughly 50–67 g.
* `scripts/f1/crash.py`: ballistic debris with ground bounces, spark pool, smoke and dust, TecPro chain compression, progressive skid marks.
* Each shot has its own camera bound by timeline markers, and keys extend ±2 frames, so motion blur never smears across cuts.
