import numpy as np
from PIL import Image
def diffuse(img, mask, iters=400):
    """Laplace/diffusion inpaint: img float (H,W,3), mask bool (H,W). Multi-scale init then Jacobi relaxation."""
    a = img.copy(); H, W = mask.shape
    m = mask.copy()
    # init: nearest known along rows (linear interpolation per row), fallback to column
    out = a.copy()
    for y in np.where(mask.any(1))[0]:
        xs = np.where(mask[y])[0]; ok = np.where(~mask[y])[0]
        if len(ok) == 0: continue
        for c in range(3): out[y, xs, c] = np.interp(xs, ok, a[y, ok, c])
    for _ in range(iters):
        p = np.pad(out, ((1, 1), (1, 1), (0, 0)), mode="edge")
        avg = (p[:-2, 1:-1] + p[2:, 1:-1] + p[1:-1, :-2] + p[1:-1, 2:]) / 4.0
        out[m] = avg[m]
    return out
