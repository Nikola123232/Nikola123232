"""Original textures: fictional sponsor boards, crowd, TecPro print. All brands are invented."""
from PIL import Image, ImageDraw, ImageFont, ImageFilter
import random, numpy as np
random.seed(3)
A = "/home/user/Nikola123232/assets"
anton = A + "/fonts/Anton-Regular.ttf"
boards = [("VELOCITY", (8, 20, 60), (255, 255, 255)), ("APEX ENERGY", (230, 30, 40), (255, 255, 255)),
          ("NOVA FUEL", (255, 200, 0), (20, 20, 20)), ("TORQUE", (20, 20, 20), (255, 90, 10)),
          ("KINETIC", (0, 140, 120), (255, 255, 255)), ("PITLANE", (255, 255, 255), (10, 40, 120)),
          ("SPEEDLINE", (90, 20, 160), (255, 220, 40)), ("ORBIT TYRES", (15, 15, 15), (255, 230, 0))]
W, H = 512, 96
strip = Image.new("RGB", (W * len(boards), H))
for i, (txt, bg, fg) in enumerate(boards):
    im = Image.new("RGB", (W, H), bg); d = ImageDraw.Draw(im)
    f = ImageFont.truetype(anton, 70)
    tw = d.textlength(txt, font=f)
    d.text(((W - tw) / 2, 4), txt, font=f, fill=fg)
    strip.paste(im, (i * W, 0))
strip.save(A + "/textures/boards.png")
# crowd: seats rows with randomly coloured spectators
cw, ch = 1024, 512
crowd = np.zeros((ch, cw, 3), np.uint8)
crowd[:] = (40, 40, 48)
img = Image.fromarray(crowd); d = ImageDraw.Draw(img)
pal = [(230, 60, 50), (240, 240, 240), (30, 60, 160), (250, 200, 30), (20, 20, 20), (240, 120, 40), (60, 150, 70), (200, 170, 140), (120, 80, 60)]
for row in range(16):
    y = row * 32
    d.rectangle([0, y + 26, cw, y + 31], fill=(70, 72, 80))
    for x in range(0, cw, 9):
        if random.random() < 0.85:
            c = random.choice(pal)
            d.ellipse([x, y + 6, x + 7, y + 13], fill=random.choice([(230, 190, 160), (190, 140, 100), (120, 80, 50)]))
            d.rectangle([x - 1, y + 13, x + 8, y + 26], fill=c)
img.save(A + "/textures/crowd.png")
# TecPro block print
tp = Image.new("RGB", (256, 128), (20, 60, 200)); d = ImageDraw.Draw(tp)
tp2 = Image.new("RGB", (256, 128), (220, 30, 30))
for t in (tp, tp2):
    dd = ImageDraw.Draw(t)
    for k in range(4):
        dd.rectangle([0, 20 + k * 28, 256, 22 + k * 28], fill=(0, 0, 0))
tp.save(A + "/textures/tecpro_blue.png"); tp2.save(A + "/textures/tecpro_red.png")
print("ok")
