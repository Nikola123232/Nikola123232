"""Timeline for the submarine-implosion short (30 fps, 1110 frames = 37.0 s). Shared by Blender, compositor and audio scripts."""
FPS = 30
NF = 1110
T = dict(h1=(1, 132), h2=(133, 249), desc=(250, 435), xs=(436, 624), imp=(625, 781), aft=(782, 1110))
F_BUCKLE0, F_FREEZE = 133, 146          # hull buckles quickly, then the action freezes while the camera pulls back
F_COLL = 689                            # implosion starts (full speed)
F_REAL_END = 700                        # end of the full-speed segment
F_REPLAY = (701, 781)                   # slow-motion replay (illustrative)
REPLAY_RATE = 0.1                       # replay plays 10x slower than the full-speed event
XS_ORIGIN = (1000.0, 0.0, 0.0)          # cross-section lives far from the ocean scene


def sstep(a, b, x):
    t = min(1.0, max(0.0, (x - a) / (b - a)))
    return t * t * (3 - 2 * t)


def scene_of(f):
    for k, (a, b) in T.items():
        if a <= f <= b: return k
    return "aft"


def tw(f):
    """Water-time in seconds: drives drifting particles. Freezes during the freeze-frame, slows in the replay / aftermath."""
    if f <= F_FREEZE: return f / 30.0
    if f < 250: return F_FREEZE / 30.0
    if f <= F_REAL_END: return f / 30.0
    base = F_REAL_END / 30.0
    if f <= F_REPLAY[1]: return base + (f - F_REAL_END) / 30.0 * REPLAY_RATE
    return base + (F_REPLAY[1] - F_REAL_END) / 30.0 * REPLAY_RATE + (f - F_REPLAY[1]) / 30.0 * 0.6


def tc(f):
    """Seconds since the collapse began (None before)."""
    if f < F_COLL: return None
    if f <= F_REAL_END: return (f - F_COLL) / 30.0
    if f <= F_REPLAY[1]: return (f - F_REPLAY[0]) / 30.0 * REPLAY_RATE        # replay restarts the event in slow motion
    return 0.9 + (f - F_REPLAY[1]) / 30.0 * 0.6


def dent(f):
    """Depth (m) of the local inward buckle in the hull."""
    if f < 250:
        if f <= 132: return 0.02 + 0.11 * sstep(1, 132, f)
        if f <= F_FREEZE: return 0.13 + 0.22 * sstep(F_BUCKLE0, F_FREEZE, f)
        return 0.35
    if f >= 625: return 0.04 + 0.08 * sstep(625, 688, f)
    return 0.0
