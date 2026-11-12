"""Shared timeline: video frame -> real (physical) time with slow-motion ramps, and car kinematics.
Global video frames 1..1800 at 30 fps. Scenes 1, 2 and 6 share one continuous physical world."""
import math

FPS = 30
V0 = 300 / 3.6          # 83.33 m/s
LANE_Y = -3.0
T_SNAP = 8.55           # rear snaps loose (real s)
T_IMP_TARGET = 10.95    # approximate real impact time
SLIDE_DECEL = 11.0      # m/s^2 (~1.4 g sliding with locked tyres)
CRUSH = 3.2             # m of combined barrier + structure crush during impact


def rate(tau):
    """Playback rate (real seconds per video second) at video time tau."""
    if tau < 10.6:
        return 1.0
    if tau < 11.0:
        u = (tau - 10.6) / 0.4
        return 1.0 + (0.15 - 1.0) * (u * u * (3 - 2 * u))
    if tau < 14.4:
        return 0.15
    if tau < 15.2:
        u = (tau - 14.4) / 0.8
        return 0.15 + (1.0 - 0.15) * (u * u * (3 - 2 * u))
    return 1.0


_real_cache = {}


def real_time(frame):
    """Real time (s) at video frame (1-based). Integrated numerically (sub-steps)."""
    if frame in _real_cache:
        return _real_cache[frame]
    tau_end = (frame - 1) / FPS
    n = max(1, int(tau_end * 600))
    t = 0.0
    dt = tau_end / n if n else 0
    for i in range(n):
        t += rate((i + 0.5) * dt) * dt
    _real_cache[frame] = t
    return t


def _integrate_pre(t_end, dt=1 / 2000):
    """Integrate longitudinal motion before impact. Returns x, v."""
    x, v, t = 0.0, V0, 8.0
    if t_end <= 8.0:
        return V0 * (t_end - 8.0), V0
    while t < t_end - 1e-9:
        h = min(dt, t_end - t)
        a = 0.0
        if t > T_SNAP:
            a = -SLIDE_DECEL
        elif t > 8.35:
            a = -30.0  # hard braking just before the snap
        v = max(0.0, v + a * h)
        x += v * h
        t += h
    return x, v


X_IMP, V_IMP = _integrate_pre(T_IMP_TARGET)
IMPACT_DUR = 2 * CRUSH / V_IMP          # constant-ish deceleration pulse duration
PEAK_G = V_IMP / IMPACT_DUR / 9.81 * 1.4  # peak ~1.4x average


def yaw_at(t):
    """Car yaw (rad, +CCW nose toward +Y) before/through impact."""
    if t < T_SNAP:
        return 0.0
    if t < T_IMP_TARGET:
        u = (t - T_SNAP) / (T_IMP_TARGET - T_SNAP)
        # quick snap then steady slide angle with small oscillation
        return math.radians(36) * (1 - math.exp(-4.0 * u)) / (1 - math.exp(-4.0)) + math.radians(3) * math.sin(u * 7)
    # impact rotates the car further, then settles
    u = min(1.0, (t - T_IMP_TARGET) / 0.6)
    y_imp = math.radians(36) + math.radians(3) * math.sin(7)
    return y_imp + math.radians(22) * (1 - (1 - u) ** 3)


def car_state(t):
    """Return dict(x, y, yaw, v, pitch, roll, z) of car origin (rear-axle centre on ground) at real time t."""
    if t <= T_IMP_TARGET:
        x, v = _integrate_pre(t)
        drift = 0.0
        if t > T_SNAP:
            u = t - T_SNAP
            drift = -0.9 * u * u  # sliding toward the outside
        return dict(x=x, y=LANE_Y + drift, yaw=yaw_at(t), v=v, pitch=0.0, roll=0.0, z=0.0)
    # impact phase: the nose contact point N is driven into the barrier (crush) then rebounds slightly;
    # the car pivots about N as it yaws (rear swings toward the barrier).
    dtv = t - T_IMP_TARGET
    base = car_state(T_IMP_TARGET)
    LF = 4.75
    nx0 = base["x"] + LF * math.cos(base["yaw"])
    ny0 = base["y"] + LF * math.sin(base["yaw"])
    if dtv < IMPACT_DUR:
        u = dtv / IMPACT_DUR
        s = CRUSH * (1 - (1 - u) ** 2)
        v = V_IMP * (1 - u)
        pitch = math.radians(-5.0) * math.sin(math.pi * u)  # rear lifts slightly
        roll = math.radians(3.0) * math.sin(math.pi * u)
        z = 0.06 * math.sin(math.pi * u)
    else:
        w = dtv - IMPACT_DUR
        s = CRUSH - 0.3 * (1 - math.exp(-w * 4.0))
        v = 0.0
        roll = 0.0
        z = 0.0
        pitch = math.radians(1.5) * math.exp(-w * 5) * math.sin(w * 18)
    yaw = yaw_at(t)
    nx = nx0 + s
    ny = ny0 - 0.5 * min(1.0, dtv / 0.6)
    return dict(x=nx - LF * math.cos(yaw), y=ny - LF * math.sin(yaw), yaw=yaw, v=v, pitch=pitch, roll=roll, z=z)


def front_x(state, length_front=4.95):
    """World x of the nose tip given state (yaw-adjusted)."""
    return state["x"] + math.cos(state["yaw"]) * length_front


# Barrier face position: where the nose reaches at impact
_s = car_state(T_IMP_TARGET)
BARRIER_X = _s["x"] + math.cos(_s["yaw"]) * 4.75 + abs(math.sin(_s["yaw"])) * 0.98 * 0.5 + 0.05
CORNER_X = BARRIER_X - 78.0


def global_frame(scene_start, local):
    return scene_start + local


if __name__ == "__main__":
    print("X_IMP", X_IMP, "V_IMP", V_IMP, "km/h", V_IMP * 3.6, "dur", IMPACT_DUR, "peak g", PEAK_G)
    print("barrier", BARRIER_X, "corner", CORNER_X)
    for f in [241, 300, 318, 330, 340, 350, 360, 380, 400, 438, 460, 540]:
        t = real_time(f)
        print(f, round(t, 3), {k: round(v, 3) for k, v in car_state(t).items()})
