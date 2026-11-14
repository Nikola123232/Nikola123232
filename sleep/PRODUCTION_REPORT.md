# Production report — "What Happens If You Don't Sleep for 7 Days?"

Output: `sleep/out/seven_days_without_sleep.mp4` — H.264 High, 1080x1920, 30 fps, 44.67 s, AAC 48 kHz stereo, 35.7 MB, 1340 frames decoded, integrated loudness -16.5 LUFS. ffprobe validation: `sleep/out/ffprobe_validation.json` (VALID).

Pipeline: Blender 5.3 (Cycles, CPU) -> Pillow/numpy compositor -> procedural audio + Kokoro TTS (am_michael) -> FFmpeg.
Scripts: `sleep/scripts/` (apt.py, brain.py, composite.py, audio.py, tts.py, assemble.py, sl/*). Blender projects: `sleep/blend/`. Narration: `sleep/audio/vo/narration.wav`. Subtitles: `sleep/audio/subtitles.srt`.

## Honest limitations
- The man is a fully procedural character (metaball body + armature), no downloaded assets. Proportions, blinking, breathing and tiredness work, but the face still looks stylised/doll-like up close; the framing mostly avoids full-frontal close-ups.
- Rendered at 720x1280 (CPU-only, adaptive sampling, OIDN denoise) and upscaled to 1080x1920, so fine detail is soft; some grain remains.
- Brain is a procedural, anatomically plausible but simplified cortex with illustrative activity pulses (not real imaging data). No neurons are shown dying.
- Audio was synthesised and level-checked by measurement (LUFS), not auditioned by ear.
- Narration timing differs slightly from the brief's draft; total length 44.7 s.
- Black segments detected at 2.0-2.3 s, 3.27-3.4 s, 21.4-21.57 s (microsleep dip), 44.4 s (end fade) are intentional (blink/cut/microsleep/ending).
- Git push to GitHub fails (403, Claude GitHub App not installed on the repo); work is committed locally.

## Scientific grounding
Sleep loss impairs attention, working memory, judgement and mood; microsleeps occur in drowsy people; hallucination-like perceptual distortions and paranoia-type symptoms are reported after prolonged wakefulness, but symptoms and timing vary widely between people. The day timeline is a narrative device, not a guaranteed outcome. Sources are listed in `sleep/STORYBOARD.md`.
