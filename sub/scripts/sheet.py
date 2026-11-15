import sys
from PIL import Image
d, out = sys.argv[1], sys.argv[2]; ns = [int(x) for x in sys.argv[3:]]
ims = [Image.open(f"{d}/{n:04d}.png").convert("RGB") for n in ns]; w, h = ims[0].size
sc = min(1.0, 2000 / (w * len(ims))); W, H = int(w * sc), int(h * sc)
im = Image.new("RGB", (W * len(ims), H))
for i, a in enumerate(ims): im.paste(a.resize((W, H)), (i * W, 0))
im.save(out)
