from PIL import Image, ImageDraw, ImageFont
import os

W, H = 1200, 630
OUT = '/opt/data/projet/nature-detective/assets/cover.png'

def font(sz, bold=True):
    for p in ['/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf' if bold else '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',
              '/usr/share/fonts/dejavu/DejaVuSans-Bold.ttf']:
        if os.path.exists(p):
            return ImageFont.truetype(p, sz)
    return ImageFont.load_default()

img = Image.new('RGB', (W, H), '#1b4332')
d = ImageDraw.Draw(img)

# layered "forest" triangles
for i, col in enumerate(['#2d6a4f', '#40916c', '#52b788', '#74c69d']):
    base = 260 + i * 90
    step = 150 - i * 15
    for x in range(-100, W + 100, step):
        h = 190 - i * 25
        d.polygon([(x, base), (x + step // 2, base - h), (x + step, base)], fill=col)
d.rectangle([0, 560, W, H], fill='#95d5b2')

# sun
d.ellipse([950, 60, 1090, 200], fill='#ffd166')

# magnifier
d.ellipse([105, 320, 305, 520], outline='#f8f9f0', width=16)
d.line([270, 485, 360, 575], fill='#f8f9f0', width=22)
d.ellipse([130, 345, 280, 495], fill='#b7e4c7')

f1 = font(96); f2 = font(40); f3 = font(30, bold=False)
d.text((400, 300), 'Nature Detective', font=f1, fill='#ffffff')
d.text((405, 415), 'Open-weight AI that gets kids', font=f2, fill='#ffd166')
d.text((405, 465), 'off the screen and into the woods.', font=f2, fill='#ffd166')
d.text((405, 545), 'Gemma 3 · local inference · zero cloud · zero data leaves the device', font=f3, fill='#d8f3dc')

img.save(OUT)
print('saved', OUT, img.size)
