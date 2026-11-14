# What Happens If You Don't Sleep for 7 Days? (44.6 s, 1080x1920, 30 fps)

Final file: `sleep/out/seven_days_without_sleep.mp4`

## Narration (Kokoro TTS, `am_michael`, speed 1.02), measured spoken times
| Line | Spoken (s) | Text |
|---|---|---|
| hook | 1.90-6.32 | After days without sleep, your brain can start showing you things that aren't there. |
| hook2 | 6.72-9.03 | But that's not even the first thing that goes wrong. |
| 24 h | 9.63-16.51 | After 24 hours awake, your attention, judgment, and reaction time can become seriously impaired. |
| 48 h | 17.06-24.06 | By 48 hours, microsleeps can interrupt your awareness for a few seconds, sometimes without you realizing it. |
| 72 h | 24.61-30.55 | After several days, confusion, distorted perception, and even hallucinations can occur. |
| 7 d | 31.10-39.06 | By day seven, severe cognitive impairment and dangerous lapses in awareness could make ordinary activities unsafe. |
| end | 39.86-44.07 | And the frightening part? You may not fully realize how impaired you've become. |

The brief's hook lines (1.9 s + 4 s) overlap if spoken at the stated times, so line 1 starts at 1.9 s and line 2 follows at 6.7 s; later scenes shift by about 2.5 s. Total 1340 frames = 44.63 s.

## Frame map
| Shot | Frames | Time | Content |
|---|---|---|---|
| Hook 1 | 1-60 | 0:00-0:02 | Over-the-shoulder, he looks down at the laptop, raises his eyes; the double stands in front of the window. Room tone + clock only; music enters at 0.5 s |
| Hook 2 | 61-120 | 0:02-0:04 | His point of view: the room is empty. Restrained sub accent |
| Hook 3 | 121-190 | 0:04-0:06.3 | Push-in on the eye, pupil tracking, **iris wipe match cut** into the brain (f184-194) |
| Brain 0 | 191-290 | 0:06.3-0:09.6 | Pull back from the cortex to the whole brain (hook2 line) |
| 24 h brain | 291-380 | 0:09.7-0:12.6 | Visual -> parietal -> frontal -> motor route: fast reference pulse vs a delayed pulse (illustrative), label 24 HOURS |
| 24 h glass | 381-502 | 0:12.7-0:16.7 | The glass slips in slow motion, shatters; he reaches too late |
| 48 h desk | 503-620 | 0:16.7-0:20.6 | Typing, then an unresponsive stare; clock keeps ticking |
| 48 h microsleep | 621-690 | 0:20.7-0:23.0 | Lids sink, muffled room, dip to black, jolt back; the clock jumped 37 s |
| 48 h brain | 691-732 | 0:23.0-0:24.4 | Alertness activity stutters ~0.5 s and resumes (not "switched off") |
| 72 h hallway | 733-850 | 0:24.4-0:28.3 | He turns toward the hallway; a figure stands in the doorway |
| 72 h POV | 851-880 | 0:28.3-0:29.3 | The hallway is empty (only a coat rack). Room sound drops to silence |
| 72 h brain | 881-930 | 0:29.3-0:31.0 | Occipital cortex shows spontaneous activity with a weak incoming signal |
| 7 days | 931-1186 | 0:31.0-0:39.5 | Slow orbit, motionless, lapses (frame holds, dropouts), erratic clock, colder light |
| Ending | 1187-1340 | 0:39.5-0:44.6 | Back to the opening angle, empty room, he closes his eyes, fade to black |

## Pipeline
`scripts/tts.py` narration | `scripts/sl/man.py` character | `scripts/sl/room.py` apartment | `scripts/apt.py` apartment shots | `scripts/brain.py` brain shots | `scripts/audio.py` sound + music | `scripts/composite.py` finishing, subtitles | `scripts/assemble.py` encode/mux/validate.

## Scientific grounding (checked against sources)
* Perceptual disturbances progress to hallucinations with increasing time awake; large inter-individual variation; extreme studies are historical: Waters et al., *Frontiers in Psychiatry* 2018, https://pubmed.ncbi.nlm.nih.gov/30042701/
* Vigilant attention and reaction time worsen with sleep loss; lapses (microsleeps) increase: Lim & Dinges, *Ann NY Acad Sci* 2008, https://pubmed.ncbi.nlm.nih.gov/18591490/ ; Dorrian et al. (PVT chapter, Kushida 2005).
* The 24/48/72 h/7-day structure is a narrative device, not a universal prediction. The brain pulses are illustrative, not measured neural signals; no neurons are shown dying.
