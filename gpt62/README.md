# GPT-6.2 Is Here. What Actually Changed?

A 5:23 tech-news explainer (1920×1080, 30 fps). Everything is generated here: the script, the voiceover, the motion graphics, the music and the SFX.

**Deliverables (in `out/`)**
- `GPT-6.2_Astra_vs_Sol.mp4`: the final video, H.264 + AAC, loudness-normalized to -14 LUFS.
- `GPT-6.2_Astra_vs_Sol.srt`: captions, built from the same phrase timings as the burned-in captions.

## Pipeline

| Step | File | Notes |
|---|---|---|
| Script (locked) | `scripts/script_data.py` | Display text, cue tags, pauses, and spoken substitutions (e.g. "Sol" is spoken as "Soul", and "44.2" as "forty-four point two"). |
| Voiceover | `scripts/tts.py` | Kokoro v1.0 neural TTS (`af_heart`, speed 0.9), synthesized sentence by sentence. Writes `public/vo.wav` and `src/timeline.json` with measured line times and estimated word times. |
| Captions | `scripts/captions.py` | Chunks the timeline into phrases. Writes `src/captions.json` (burned in) and `out/*.srt`. |
| Animation | `src/` (Remotion 4) | Every shot keys off narration cues (`cue()`, `word()` in `src/lib.tsx`). Change the script and re-run the TTS, and the animation re-times itself. |
| Music + SFX | `scripts/audio.py` | Original numpy synthesis: an A-minor pad, a soft pulse, whooshes, ticks and reveals. Placed at the same cue times and side-chain ducked under the VO. |
| Mux | `scripts/mux.sh` | Two-pass loudnorm, then muxes onto the picture. |

```bash
# needs ../.ttsenv (kokoro-onnx, soundfile, scipy) and ../assets/tts/kokoro-v1.0.onnx + voices-v1.0.bin
../.ttsenv/bin/python scripts/tts.py && python3 scripts/captions.py && ../.ttsenv/bin/python scripts/audio.py
npm install && npx remotion studio src/index.ts          # live preview
npx remotion render src/index.ts Main out/video_noaudio.mp4 --muted --concurrency=4 --crf=18
./scripts/mux.sh
```

## Scenes (`src/scenes/`)
`Cold` (split-screen reveal) → `Launch` (cards expand into workloads, then API pricing) → `Bench` (what FrontierCode measures, max-effort dials, score chart with a zoom on the 0.4-point gap, a separate cost-per-task graphic, the source excerpt, caveats) → `Web` (light design canvas: wireframe → site → phone/rounds/checks → **Sol**) → `Bug` (dark code graph: red trace across connected files, repro matrix, the silent wrong fix → **Astra**, with a Sol→Astra handoff) → `Slides` (studio desk: notes → deck is fine with **Sol**; then a strict template plus a 40-page report and spreadsheet → **Astra**) → `Verdict` (task columns, the switch rule, the closing line).

## Facts used and how they were checked
I verified these on 2026-11-19 through web search. Multiple outlets agree. **openai.com itself was blocked by this environment's network policy, so I couldn't read the primary page directly.**
- Launch: GPT-6.2 Astra and GPT-6.2 Sol, November 17, 2026. Astra is pitched for the hardest professional work, and Sol for everyday work.
- FrontierCode 2.0 (run by Cognition; it grades whether maintainers would merge the change), both at max effort: Astra **44.2** at **$5.97/task**, Sol **43.8** at **$1.29/task**. That's a 0.4-point gap at about 1/5 the cost. On screen, this is labelled "OpenAI-reported" and "cost per task on this benchmark".
- API list prices per 1M tokens: Astra $8 in / $40 out, Sol $2 / $10.
- The highlighted "source excerpt" shows the claim **as quoted in coverage**, and it's labelled that way on screen. Check the wording against the primary page before publishing.
- The bakery, checkout-bug and slide-deck scenes are labelled "Illustrative example" throughout. They're not live tests.
