"""Render a looping GIF of a stick-figure person dancing on a disco floor.

Usage:  py dancer.py [output.gif]
Requires Pillow (pip install pillow).
"""

import math
import sys

from PIL import Image, ImageDraw

SIZE = 480          # output width/height in pixels
SCALE = 2           # draw at 2x and downsample for smooth lines
FRAMES = 48         # frames per loop
FRAME_MS = 50       # 20 fps -> 2.4 s loop
BEATS = 4           # bounces per loop

# Body segment lengths (in output pixels)
TORSO, NECK, HEAD_R = 78, 14, 20
UPPER_ARM, FOREARM = 42, 40
THIGH, SHIN = 50, 50

FLOOR_COLORS = [(255, 64, 129), (124, 77, 255), (0, 229, 255),
                (118, 255, 3), (255, 214, 0), (255, 109, 0)]


def limb(origin, angle, length):
    """Point at `length` from `origin`; angle 0 points straight down, positive swings right."""
    x, y = origin
    return x + math.sin(angle) * length, y + math.cos(angle) * length


def pose(t):
    """Joint positions for loop phase t in [0, 1)."""
    p = 2 * math.pi * t
    beat = 2 * math.pi * BEATS * t

    bounce = 9 * (1 - math.cos(beat)) / 2
    hip = (SIZE / 2 + 18 * math.sin(p), 300 + bounce)
    lean = 0.14 * math.sin(p)
    neck = limb(hip, math.pi + lean, TORSO)
    head = limb(neck, math.pi + lean * 1.5, NECK + HEAD_R)

    # Right arm points up and sweeps (disco point); left arm pumps at the hip.
    r_shoulder = 2.45 + 0.45 * math.sin(p)
    r_elbow = limb(neck, r_shoulder, UPPER_ARM)
    r_hand = limb(r_elbow, r_shoulder + 0.25, FOREARM)
    l_shoulder = -0.55 - 0.45 * math.sin(beat / 2)
    l_elbow = limb(neck, l_shoulder, UPPER_ARM)
    l_hand = limb(l_elbow, l_shoulder - 1.4 - 0.5 * math.sin(beat / 2), FOREARM)

    # Legs alternate knee lifts on the beat.
    lift_r = max(0.0, math.sin(beat / 2))
    lift_l = max(0.0, -math.sin(beat / 2))
    r_thigh = 0.28 + 1.0 * lift_r
    r_knee = limb(hip, r_thigh, THIGH)
    r_foot = limb(r_knee, r_thigh - 1.5 * lift_r, SHIN)
    l_thigh = -0.28 - 1.0 * lift_l
    l_knee = limb(hip, l_thigh, THIGH)
    l_foot = limb(l_knee, l_thigh + 1.5 * lift_l, SHIN)

    return {
        "hip": hip, "neck": neck, "head": head,
        "limbs": [(neck, r_elbow, r_hand), (neck, l_elbow, l_hand),
                  (hip, r_knee, r_foot), (hip, l_knee, l_foot)],
    }


def draw_background(d, t):
    s = SCALE
    d.rectangle([0, 0, SIZE * s, SIZE * s], fill=(18, 12, 38))
    # Light-up floor: a grid of tiles whose colors cycle each beat.
    beat_idx = int(t * BEATS * 2)
    tile, top = 60, 360
    for row in range((SIZE - top) // tile + 1):
        for col in range(SIZE // tile):
            color = FLOOR_COLORS[(row * 3 + col + beat_idx) % len(FLOOR_COLORS)]
            dim = 0.55 if (row + col + beat_idx) % 2 else 1.0
            color = tuple(int(c * dim) for c in color)
            x0, y0 = col * tile, top + row * tile
            d.rectangle([x0 * s + 2, y0 * s + 2, (x0 + tile) * s - 2, (y0 + tile) * s - 2], fill=color)
    # Mirror ball and sparkles.
    cx, cy, r = SIZE / 2, 46, 22
    d.line([cx * s, 0, cx * s, (cy - r) * s], fill=(160, 160, 170), width=2 * s)
    d.ellipse([(cx - r) * s, (cy - r) * s, (cx + r) * s, (cy + r) * s], fill=(200, 205, 220))
    for i in range(10):
        a = 2 * math.pi * (i / 10 + t)
        sx, sy = cx + math.cos(a) * 150, 150 + math.sin(a) * 60
        if (i + beat_idx) % 3 == 0:
            d.ellipse([(sx - 3) * s, (sy - 3) * s, (sx + 3) * s, (sy + 3) * s], fill=(255, 255, 255))


def draw_figure(d, body):
    s = SCALE
    ink, w = (250, 250, 255), 9 * s

    def line(a, b):
        d.line([a[0] * s, a[1] * s, b[0] * s, b[1] * s], fill=ink, width=w, joint="curve")

    def dot(c, r):
        d.ellipse([(c[0] - r) * s, (c[1] - r) * s, (c[0] + r) * s, (c[1] + r) * s], fill=ink)

    # Shadow under the dancer.
    hx = body["hip"][0]
    d.ellipse([(hx - 55) * s, 408 * s, (hx + 55) * s, 424 * s], fill=(0, 0, 0))

    line(body["hip"], body["neck"])
    for a, b, c in body["limbs"]:
        line(a, b)
        line(b, c)
        for joint in (a, b, c):
            dot(joint, 4.5)
    dot(body["head"], HEAD_R)


def render(path="dancer.gif"):
    frames = []
    for i in range(FRAMES):
        t = i / FRAMES
        img = Image.new("RGB", (SIZE * SCALE, SIZE * SCALE))
        d = ImageDraw.Draw(img)
        draw_background(d, t)
        draw_figure(d, pose(t))
        frames.append(img.resize((SIZE, SIZE), Image.LANCZOS).quantize(colors=128))
    frames[0].save(path, save_all=True, append_images=frames[1:],
                   duration=FRAME_MS, loop=0, optimize=True)
    print(f"Wrote {len(frames)} frames to {path}")


if __name__ == "__main__":
    render(sys.argv[1] if len(sys.argv) > 1 else "dancer.gif")
