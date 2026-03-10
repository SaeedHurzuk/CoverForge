#!/usr/bin/env python3
"""
Spotify Playlist Cover Generator
Generates bold, unique, elegant playlist artwork from a playlist name.

Usage:
  python3 spotify_cover_gen.py "Playlist Name"
  python3 spotify_cover_gen.py "Playlist Name" --theme neon
  python3 spotify_cover_gen.py "Playlist Name" --theme all --output ./covers/
  python3 spotify_cover_gen.py "Playlist Name" --pattern carbon
  python3 spotify_cover_gen.py "Playlist Name" --font ~/Downloads/Poppins/
  python3 spotify_cover_gen.py --list-themes
  python3 spotify_cover_gen.py --list-patterns
"""

import sys
import math
import hashlib
import random
import argparse
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont, ImageFilter
import numpy as np

# ==============================================================================
# Constants
# ==============================================================================
SIZE = 3000

FALLBACK_BOLD_PATHS = [
    "~/.fonts/truetype/google-fonts/Poppins-Bold.ttf",
    "~/.fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
    "~/.fonts/truetype/liberation/LiberationSans-Bold.ttf",
    "~/.fonts/truetype/freefont/FreeSansBold.ttf",
]
FALLBACK_LIGHT_PATHS = [
    "~/.fonts/truetype/google-fonts/Poppins-Light.ttf",
    "~/.fonts/truetype/google-fonts/Poppins-Regular.ttf",
    "~/.fonts/truetype/dejavu/DejaVuSans.ttf",
    "~/.fonts/truetype/liberation/LiberationSans-Regular.ttf",
]

# Also check system-wide paths as fallback
SYSTEM_BOLD_PATHS = [
    "/usr/share/fonts/truetype/google-fonts/Poppins-Bold.ttf",
    "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
    "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
    "/usr/share/fonts/truetype/freefont/FreeSansBold.ttf",
]
SYSTEM_LIGHT_PATHS = [
    "/usr/share/fonts/truetype/google-fonts/Poppins-Light.ttf",
    "/usr/share/fonts/truetype/google-fonts/Poppins-Regular.ttf",
    "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
    "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf",
]

BOLD_SUFFIXES  = ["Bold", "Black", "Heavy", "ExtraBold", "800", "900", "700"]
LIGHT_SUFFIXES = ["Light", "Thin", "Regular", "300", "100", "200"]

# ==============================================================================
# Patterns
# ==============================================================================
PATTERNS = [
    "carbon",    # carbon fibre weave
    "hexgrid",   # honeycomb hex grid
    "scanlines", # CRT horizontal scanlines
    "plasma",    # sine-wave plasma field
    "circuit",   # circuit board traces
    "starfield", # deep space bokeh
    "waves",     # concentric ripple rings
    "shatter",   # broken glass voronoi
    "mesh",      # grid mesh with nodes
]

PATTERN_DESCRIPTIONS = {
    "carbon":    "Carbon fibre weave texture",
    "hexgrid":   "Honeycomb hex grid overlay",
    "scanlines": "CRT-style horizontal scanlines",
    "plasma":    "Smooth sine-wave plasma field",
    "circuit":   "Circuit board traces and nodes",
    "starfield": "Deep space bokeh starfield",
    "waves":     "Concentric ripple rings",
    "shatter":   "Broken glass / Voronoi shatter",
    "mesh":      "Geometric grid mesh with nodes",
}


def pattern_from_name(name):
    """Pick a pattern deterministically from the playlist name."""
    seed = seed_from_name(name)
    # Use different bits than the palette selection
    return PATTERNS[(seed >> 8) % len(PATTERNS)]


# ==============================================================================
# Themes
# ==============================================================================
THEMES = {
    "auto": {},
    "crimson": {
        "name": "Void Crimson",
        "bg":      (8, 4, 12),
        "accent1": (220, 30, 60),
        "accent2": (255, 80, 20),
        "mid":     (140, 10, 40),
        "glow":    (255, 40, 80),
        "text":    (255, 245, 245),
        "sub":     (200, 180, 185),
    },
    "neon": {
        "name": "Glacier Neon",
        "bg":      (4, 8, 20),
        "accent1": (0, 210, 255),
        "accent2": (0, 120, 255),
        "mid":     (0, 60, 140),
        "glow":    (80, 230, 255),
        "text":    (240, 250, 255),
        "sub":     (160, 200, 230),
    },
    "gold": {
        "name": "Obsidian Gold",
        "bg":      (10, 8, 4),
        "accent1": (255, 185, 20),
        "accent2": (200, 120, 0),
        "mid":     (100, 60, 5),
        "glow":    (255, 210, 80),
        "text":    (255, 248, 230),
        "sub":     (210, 190, 150),
    },
    "violet": {
        "name": "Violet Dusk",
        "bg":      (8, 4, 18),
        "accent1": (180, 60, 255),
        "accent2": (80, 20, 200),
        "mid":     (100, 30, 160),
        "glow":    (210, 100, 255),
        "text":    (248, 240, 255),
        "sub":     (190, 170, 220),
    },
    "forest": {
        "name": "Forest Pulse",
        "bg":      (4, 12, 8),
        "accent1": (20, 220, 100),
        "accent2": (0, 160, 80),
        "mid":     (10, 80, 40),
        "glow":    (80, 255, 150),
        "text":    (235, 255, 245),
        "sub":     (160, 210, 185),
    },
    "rust": {
        "name": "Rust & Ice",
        "bg":      (12, 8, 6),
        "accent1": (255, 100, 50),
        "accent2": (180, 220, 255),
        "mid":     (120, 50, 20),
        "glow":    (255, 140, 90),
        "text":    (255, 250, 245),
        "sub":     (210, 200, 195),
    },
    "rose": {
        "name": "Midnight Rose",
        "bg":      (10, 4, 8),
        "accent1": (255, 60, 140),
        "accent2": (200, 20, 80),
        "mid":     (120, 10, 60),
        "glow":    (255, 110, 180),
        "text":    (255, 240, 248),
        "sub":     (210, 175, 195),
    },
    "chrome": {
        "name": "Arctic Chrome",
        "bg":      (6, 8, 12),
        "accent1": (180, 200, 255),
        "accent2": (100, 130, 220),
        "mid":     (50, 70, 130),
        "glow":    (220, 235, 255),
        "text":    (245, 248, 255),
        "sub":     (180, 190, 215),
    },
    "solar": {
        "name": "Solar Flare",
        "bg":      (12, 6, 0),
        "accent1": (255, 160, 0),
        "accent2": (255, 60, 0),
        "mid":     (160, 40, 0),
        "glow":    (255, 200, 60),
        "text":    (255, 252, 235),
        "sub":     (230, 200, 160),
    },
    "abyss": {
        "name": "Deep Abyss",
        "bg":      (2, 4, 14),
        "accent1": (40, 60, 255),
        "accent2": (0, 20, 180),
        "mid":     (10, 20, 100),
        "glow":    (80, 100, 255),
        "text":    (230, 235, 255),
        "sub":     (160, 170, 220),
    },
    "sakura": {
        "name": "Sakura Mist",
        "bg":      (14, 6, 10),
        "accent1": (255, 150, 180),
        "accent2": (220, 80, 130),
        "mid":     (140, 40, 80),
        "glow":    (255, 190, 210),
        "text":    (255, 245, 250),
        "sub":     (220, 190, 205),
    },
    "toxic": {
        "name": "Toxic Lime",
        "bg":      (4, 10, 2),
        "accent1": (160, 255, 0),
        "accent2": (80, 200, 0),
        "mid":     (40, 100, 0),
        "glow":    (200, 255, 60),
        "text":    (245, 255, 230),
        "sub":     (185, 220, 160),
    },
    "cyberpunk": {
        "name": "Cyberpunk",
        "bg":      (5, 2, 15),
        "accent1": (255, 0, 180),
        "accent2": (0, 240, 255),
        "mid":     (100, 0, 80),
        "glow":    (255, 60, 200),
        "text":    (255, 245, 255),
        "sub":     (200, 180, 230),
    },
    "matte": {
        "name": "Matte Black",
        "bg":      (10, 10, 12),
        "accent1": (210, 210, 215),
        "accent2": (140, 140, 148),
        "mid":     (30, 30, 34),
        "glow":    (255, 255, 255),
        "text":    (240, 240, 240),
        "sub":     (160, 160, 165),
    },
}

AUTO_POOL = [k for k in THEMES if k != "auto"]


# ==============================================================================
# Font Resolution
# ==============================================================================
def _expand(path_str):
    return Path(path_str).expanduser()


def _find_font_in_dir(directory, suffixes):
    d = Path(directory).expanduser()
    candidates = list(d.glob("*.ttf")) + list(d.glob("*.otf"))
    for suffix in suffixes:
        for c in candidates:
            if suffix.lower() in c.stem.lower():
                return str(c)
    return str(candidates[0]) if candidates else None


def resolve_fonts(font_arg):
    if font_arg is None:
        all_bold  = FALLBACK_BOLD_PATHS  + SYSTEM_BOLD_PATHS
        all_light = FALLBACK_LIGHT_PATHS + SYSTEM_LIGHT_PATHS
        bold  = next((str(p) for raw in all_bold  if _expand(raw).exists() for p in [_expand(raw)]), None)
        light = next((str(p) for raw in all_light if _expand(raw).exists() for p in [_expand(raw)]), None)
        if not bold:
            raise FileNotFoundError(
                "No font found. Install fonts to ~/.fonts/ or pass --font.\n"
                "  Download Poppins (free): https://fonts.google.com/specimen/Poppins\n"
                "  Place at: ~/.fonts/truetype/google-fonts/Poppins-Bold.ttf"
            )
        return bold, light or bold

    p = Path(font_arg).expanduser()
    if p.is_dir():
        bold  = _find_font_in_dir(p, BOLD_SUFFIXES)
        light = _find_font_in_dir(p, LIGHT_SUFFIXES)
        if not bold:
            raise FileNotFoundError(f"No .ttf/.otf fonts found in: {font_arg}")
        return bold, light or bold

    if p.is_file():
        bold = str(p)
        sibling = _find_font_in_dir(str(p.parent), LIGHT_SUFFIXES)
        light = sibling if sibling and sibling != bold else bold
        return bold, light

    raise FileNotFoundError(f"Font path not found: {font_arg}")


# ==============================================================================
# Palette
# ==============================================================================
def seed_from_name(name):
    return int(hashlib.md5(name.encode()).hexdigest(), 16)


def get_palette(name, theme_key):
    if theme_key != "auto":
        return THEMES[theme_key]
    return THEMES[AUTO_POOL[seed_from_name(name) % len(AUTO_POOL)]]


# ==============================================================================
# Drawing Helpers
# ==============================================================================
def lerp_color(c1, c2, t):
    return tuple(int(c1[i] + (c2[i] - c1[i]) * t) for i in range(3))


def add_alpha(color, alpha):
    return (*color[:3], int(alpha))


def draw_radial_gradient(arr, cx, cy, r_inner, r_outer, color, intensity=1.0):
    H, W = arr.shape[:2]
    ys, xs = np.ogrid[:H, :W]
    dist = np.sqrt((xs - cx) ** 2 + (ys - cy) ** 2)
    t = np.where(
        (dist < r_outer) & (dist > r_inner),
        1.0 - np.clip((dist - r_inner) / max(r_outer - r_inner, 1), 0, 1),
        0.0
    ) ** 2.2 * intensity
    for ch, val in enumerate(color):
        arr[:, :, ch] += t * val


def draw_arc_stroke(draw, cx, cy, radius, start_deg, end_deg, color, width=8):
    box = [cx - radius, cy - radius, cx + radius, cy + radius]
    draw.arc(box, start=start_deg, end=end_deg, fill=color, width=width)


def to_image(arr):
    return Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8), "RGBA")


# ==============================================================================
# Pattern Engines
# ==============================================================================

def pattern_carbon(size, palette, rng, matte=False):
    """Carbon fibre weave: alternating cell highlights like woven strands."""
    cell = max(30, size // 80)
    arr  = np.zeros((size, size, 4), dtype=np.float32)
    ys, xs = np.mgrid[:size, :size]

    cx_idx = (xs // cell) % 2
    cy_idx = (ys // cell) % 2
    px = (xs % cell).astype(np.float32) / cell
    py = (ys % cell).astype(np.float32) / cell

    is_even = (cx_idx + cy_idx) % 2 == 0
    highlight = np.where(is_even,
                         np.sin(px * math.pi) ** 2.5,
                         np.sin(py * math.pi) ** 2.5)

    # Edge darkening within each cell for depth
    edge = np.minimum(
        np.minimum(px, 1.0 - px),
        np.minimum(py, 1.0 - py)
    ) * 4.0
    edge = np.clip(edge, 0, 1)

    if matte:
        # Matte mode: high contrast weave -- dark cells stay black, bright peaks pop
        # Add a base grey layer so the weave reads as actual texture, not just glow
        grey_base = edge * 0.18
        fibre_shine = highlight * edge
        # Two-tone: dark strand body + bright highlight peak
        strand_body = np.clip(fibre_shine * 0.4, 0, 1)
        strand_peak = np.clip((fibre_shine - 0.6) * 2.5, 0, 1)  # only top 40% lights up
        col = palette["accent1"]
        col2 = palette["glow"]
        # Body: warm dark grey tinted with accent
        arr[:, :, 0] = grey_base * 40 + strand_body * col[0] * 0.6
        arr[:, :, 1] = grey_base * 40 + strand_body * col[1] * 0.6
        arr[:, :, 2] = grey_base * 40 + strand_body * col[2] * 0.6
        arr[:, :, 3] = np.clip(grey_base * 180 + strand_body * 160, 0, 255)
        # Bright peak overlay using glow colour
        peak_arr = np.zeros((size, size, 4), dtype=np.float32)
        peak_arr[:, :, 0] = col2[0] * strand_peak
        peak_arr[:, :, 1] = col2[1] * strand_peak
        peak_arr[:, :, 2] = col2[2] * strand_peak
        peak_arr[:, :, 3] = strand_peak * 230
        base_img = to_image(arr)
        peak_img = to_image(peak_arr)
        return Image.alpha_composite(base_img, peak_img)
    else:
        highlight = highlight * edge * 0.55
        col = palette["accent1"]
        arr[:, :, 0] = col[0] * highlight
        arr[:, :, 1] = col[1] * highlight
        arr[:, :, 2] = col[2] * highlight
        arr[:, :, 3] = highlight * 180
        return to_image(arr)


def pattern_hexgrid(size, palette, rng, matte=False):
    """Honeycomb hex grid: glowing cell borders."""
    img  = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    r    = max(40, size // 55)      # hex radius
    h    = r * math.sqrt(3)
    col  = palette["accent1"]
    col2 = palette["accent2"]
    if matte:
        # Matte: crisp bright edges + vivid cell fills + inner glow layer
        alpha_edge = 220
        alpha_glow = 55
        line_w = max(4, size // 600)
    else:
        alpha_edge = 90
        alpha_glow = 30
        line_w = max(2, size // 1000)

    row = 0
    y   = 0.0
    while y - r < size:
        x_off = (r * 1.5) if row % 2 else 0.0
        x = x_off
        while x - r < size:
            pts = [
                (x + r * math.cos(math.radians(60 * i + 30)),
                 y + r * math.sin(math.radians(60 * i + 30)))
                for i in range(6)
            ]
            t = (x / size + y / size) / 2
            edge_col = lerp_color(col, col2, t % 1.0)
            # Glow fill
            draw.polygon(pts, fill=add_alpha(edge_col, alpha_glow))
            # Edge stroke
            draw.polygon(pts, outline=add_alpha(edge_col, alpha_edge), width=line_w)
            x += r * 3.0
        y  += h / 2
        row += 1

    if matte:
        # Add a soft blur copy of the edges as a neon glow halo
        glow_layer = img.filter(ImageFilter.GaussianBlur(radius=max(4, size // 400)))
        img = Image.alpha_composite(glow_layer, img)

    return img


def pattern_scanlines(size, palette, rng):
    """CRT scanlines: tight horizontal lines with slight brightness variation."""
    arr  = np.zeros((size, size, 4), dtype=np.float32)
    ys   = np.arange(size, dtype=np.float32)
    gap  = max(6, size // 400)

    # Alternating bright / dark rows
    mask = ((ys % gap) < max(1, gap // 3)).astype(np.float32)
    # Gentle sine shimmer along y
    shimmer = (np.sin(ys / size * math.pi * 6) * 0.3 + 0.7)
    intensity = mask * shimmer * 0.18

    col = palette["text"]
    arr[:, :, 0] = col[0] * intensity[:, None]
    arr[:, :, 1] = col[1] * intensity[:, None]
    arr[:, :, 2] = col[2] * intensity[:, None]
    arr[:, :, 3] = intensity[:, None] * 200
    return to_image(arr)


def pattern_plasma(size, palette, rng):
    """Plasma field: multi-frequency sine waves creating iridescent blobs."""
    # Work at reduced resolution then upscale for speed
    small = size // 6
    ys, xs = np.mgrid[:small, :small]
    nx = xs.astype(np.float32) / small
    ny = ys.astype(np.float32) / small

    a1 = rng.uniform(2, 5)
    a2 = rng.uniform(2, 5)
    a3 = rng.uniform(1, 3)
    ox = rng.uniform(0, math.pi * 2)
    oy = rng.uniform(0, math.pi * 2)

    field = (
        np.sin(nx * a1 * math.pi * 2 + ox) +
        np.sin(ny * a2 * math.pi * 2 + oy) +
        np.sin((nx + ny) * a3 * math.pi * 2) +
        np.sin(np.sqrt(nx**2 + ny**2) * math.pi * 4)
    ) / 4.0  # range roughly -1..1
    field = (field + 1) / 2  # 0..1

    col1 = np.array(palette["accent1"], dtype=np.float32)
    col2 = np.array(palette["accent2"], dtype=np.float32)
    col3 = np.array(palette["mid"],     dtype=np.float32)

    t1 = field[:, :, None]
    t2 = np.sin(field * math.pi)[:, :, None]
    blended = col1 * t1 + col2 * (1 - t1) * t2 + col3 * (1 - t2) * (1 - t1)

    arr = np.zeros((small, small, 4), dtype=np.float32)
    arr[:, :, :3] = blended
    arr[:, :, 3]  = (field * 0.5 + 0.1) * 160  # semi-transparent
    small_img = to_image(arr)
    return small_img.resize((size, size), Image.BILINEAR)


def pattern_circuit(size, palette, rng):
    """Circuit board: right-angle traces with via dots and pads."""
    img  = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    grid   = max(60, size // 45)
    cols_n = size // grid + 2
    rows_n = size // grid + 2
    col1   = palette["accent1"]
    col2   = palette["accent2"]
    lw     = max(2, size // 600)

    # Build random trace graph on grid
    nodes = set()
    for _ in range(int(cols_n * rows_n * 0.4)):
        gx = rng.randint(0, cols_n - 1)
        gy = rng.randint(0, rows_n - 1)
        nodes.add((gx, gy))

    nodes = list(nodes)
    rng.shuffle(nodes)
    drawn_edges = set()

    for (gx, gy) in nodes:
        # Try to connect to 1-3 neighbours
        dirs = [(1, 0), (0, 1), (-1, 0), (0, -1)]
        rng.shuffle(dirs)
        for dx, dy in dirs[:rng.randint(1, 3)]:
            nx2, ny2 = gx + dx, gy + dy
            if (nx2, ny2) in set(map(tuple, [list(n) for n in nodes])):
                edge = tuple(sorted([(gx, gy), (nx2, ny2)]))
                if edge not in drawn_edges:
                    drawn_edges.add(edge)
                    t = ((gx + gy) / (cols_n + rows_n))
                    edge_col = lerp_color(col1, col2, t % 1.0)
                    alpha = rng.randint(80, 160)
                    x1, y1 = gx * grid, gy * grid
                    x2, y2 = nx2 * grid, ny2 * grid
                    draw.line([(x1, y1), (x2, y2)],
                              fill=add_alpha(edge_col, alpha), width=lw)

    # Draw via circles at nodes
    via_r = max(4, lw * 3)
    for (gx, gy) in nodes:
        x, y = gx * grid, gy * grid
        t = (gx + gy) / (cols_n + rows_n)
        dot_col = lerp_color(col1, col2, t % 1.0)
        alpha = rng.randint(120, 220)
        draw.ellipse([x - via_r, y - via_r, x + via_r, y + via_r],
                     fill=add_alpha(dot_col, alpha))

    return img


def pattern_starfield(size, palette, rng):
    """Deep space bokeh: layered stars with soft glow halos."""
    # Work at half res for the glow layer, then upscale -- much faster
    half = size // 2
    base = Image.new("RGBA", (half, half), (0, 0, 0, 0))
    draw = ImageDraw.Draw(base)
    col1 = palette["glow"]
    col2 = palette["accent1"]
    col3 = palette["text"]

    star_configs = [
        (500, 1,  2,  col3, 180, 255),   # tiny bright pinpoints
        (140, 2,  5,  col2, 130, 200),   # medium
        (50,  5,  14, col1,  80, 160),   # large bokeh discs
    ]
    for count, r_min, r_max, col, a_min, a_max in star_configs:
        for _ in range(count):
            cx = rng.randint(0, half)
            cy = rng.randint(0, half)
            r  = rng.randint(r_min, r_max)
            alpha = rng.randint(a_min, a_max)
            draw.ellipse([cx - r, cy - r, cx + r, cy + r],
                         fill=add_alpha(col, alpha))

    # Soft bokeh blur on the large-star layer then composite
    blurred = base.filter(ImageFilter.GaussianBlur(radius=half // 80))
    return blurred.resize((size, size), Image.BILINEAR)


def pattern_waves(size, palette, rng):
    """Concentric ripple rings emanating from 2-3 off-center origins."""
    arr = np.zeros((size, size, 4), dtype=np.float32)
    ys, xs = np.mgrid[:size, :size]

    origins = [
        (rng.randint(size // 6, 5 * size // 6),
         rng.randint(size // 6, 5 * size // 6))
        for _ in range(rng.randint(2, 3))
    ]
    col1 = np.array(palette["accent1"], dtype=np.float32)
    col2 = np.array(palette["accent2"], dtype=np.float32)

    spacing = size // 16
    for i, (ox, oy) in enumerate(origins):
        dist = np.sqrt((xs - ox).astype(np.float32)**2 +
                       (ys - oy).astype(np.float32)**2)
        # Sine rings, decaying with distance
        wave = np.sin(dist / spacing * math.pi * 2) ** 2
        decay = np.exp(-dist / (size * 0.55))
        intensity = wave * decay * 0.35
        col = col1 if i % 2 == 0 else col2
        for ch, v in enumerate(col):
            arr[:, :, ch] += v * intensity
        arr[:, :, 3] += intensity * 180

    return to_image(arr)


def pattern_shatter(size, palette, rng):
    """Voronoi shatter: glowing cell edges like broken glass or crystal."""
    # Low-res voronoi then upscale
    small = size // 8
    n_pts = rng.randint(18, 35)
    pts_x = np.array([rng.randint(0, small) for _ in range(n_pts)], dtype=np.float32)
    pts_y = np.array([rng.randint(0, small) for _ in range(n_pts)], dtype=np.float32)

    ys, xs = np.mgrid[:small, :small]
    xs_f = xs.astype(np.float32)
    ys_f = ys.astype(np.float32)

    # Distance to nearest and second-nearest center
    dists = np.sqrt((xs_f[:, :, None] - pts_x[None, None, :])**2 +
                    (ys_f[:, :, None] - pts_y[None, None, :])**2)
    dists_sorted = np.sort(dists, axis=2)
    d1 = dists_sorted[:, :, 0]
    d2 = dists_sorted[:, :, 1]

    # Edge = difference between two nearest is small
    edge = np.exp(-((d2 - d1) ** 2) / (small * 0.008))
    nearest = np.argmin(dists, axis=2)

    col1 = np.array(palette["accent1"], dtype=np.float32)
    col2 = np.array(palette["accent2"], dtype=np.float32)
    col_glow = np.array(palette["glow"], dtype=np.float32)

    t = (nearest.astype(np.float32) / n_pts)
    arr = np.zeros((small, small, 4), dtype=np.float32)
    # Faint cell fill
    for ch in range(3):
        arr[:, :, ch] = col1[ch] * t + col2[ch] * (1 - t)
    arr[:, :, 3] = t * 25 + 5
    # Bright edges
    for ch in range(3):
        arr[:, :, ch] += col_glow[ch] * edge * 0.9
    arr[:, :, 3] += edge * 200

    small_img = to_image(arr)
    return small_img.resize((size, size), Image.BILINEAR)


def pattern_mesh(size, palette, rng):
    """Geometric grid mesh: fine lines with glowing intersection nodes."""
    img  = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    spacing = max(80, size // 32)
    col1  = palette["accent1"]
    col2  = palette["accent2"]
    lw    = max(1, size // 1200)
    node_r = max(3, size // 600)

    for x in range(0, size + spacing, spacing):
        t = x / size
        c = lerp_color(col1, col2, t)
        draw.line([(x, 0), (x, size)], fill=add_alpha(c, 35), width=lw)

    for y in range(0, size + spacing, spacing):
        t = y / size
        c = lerp_color(col1, col2, t)
        draw.line([(0, y), (size, y)], fill=add_alpha(c, 35), width=lw)

    # Intersection nodes
    for x in range(0, size + spacing, spacing):
        for y in range(0, size + spacing, spacing):
            t = (x + y) / (size * 2)
            c = lerp_color(col1, col2, t % 1.0)
            # Vary node size for depth
            r = node_r + rng.randint(-1, 2)
            r = max(1, r)
            alpha = rng.randint(80, 180)
            draw.ellipse([x - r, y - r, x + r, y + r],
                         fill=add_alpha(c, alpha))

    return img


def build_pattern_layer(size, palette, rng, style, matte=False):
    """Dispatch to the correct pattern engine."""
    # carbon and hexgrid have first-class matte support
    if style == "carbon":
        return pattern_carbon(size, palette, rng, matte=matte)
    if style == "hexgrid":
        return pattern_hexgrid(size, palette, rng, matte=matte)
    dispatch = {
        "scanlines": pattern_scanlines,
        "plasma":    pattern_plasma,
        "circuit":   pattern_circuit,
        "starfield": pattern_starfield,
        "waves":     pattern_waves,
        "shatter":   pattern_shatter,
        "mesh":      pattern_mesh,
    }
    fn = dispatch.get(style)
    if fn is None:
        return Image.new("RGBA", (size, size), (0, 0, 0, 0))
    return fn(size, palette, rng)


# ==============================================================================
# Base Layers
# ==============================================================================
def build_background(size, palette, rng, matte=False):
    arr = np.zeros((size, size, 4), dtype=np.float32)
    if matte:
        # Flat near-black -- no glows, no colour bleed, pattern does all the work
        bg = (10, 10, 12)
    else:
        bg = palette["bg"]
    arr[:, :, 0], arr[:, :, 1], arr[:, :, 2], arr[:, :, 3] = bg[0], bg[1], bg[2], 255
    if not matte:
        positions = [
            (rng.randint(size // 4, 3 * size // 4), rng.randint(size // 4, 3 * size // 4)),
            (rng.randint(0, size // 3),              rng.randint(0, size // 3)),
            (rng.randint(2 * size // 3, size),       rng.randint(2 * size // 3, size)),
        ]
        glow_data = [
            (palette["mid"],     0.40, size * 0.65),
            (palette["accent2"], 0.25, size * 0.50),
            (palette["accent1"], 0.20, size * 0.40),
        ]
        for (gx, gy), (gc, gi, gr) in zip(positions, glow_data):
            draw_radial_gradient(arr, gx, gy, 0, gr, gc, intensity=gi)
    return to_image(arr)


def build_geometry(size, palette, rng):
    img  = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    for _ in range(5):
        r  = rng.randint(size // 4, int(size * 0.75))
        cx = rng.randint(-r // 2, size + r // 2)
        cy = rng.randint(-r // 2, size + r // 2)
        col = rng.choice([palette["accent1"], palette["accent2"], palette["mid"]])
        draw.ellipse([cx-r, cy-r, cx+r, cy+r], fill=add_alpha(col, rng.randint(12, 35)))

    for i in range(8):
        col    = lerp_color(palette["accent1"], palette["accent2"], i / 7)
        angle  = rng.uniform(-60, 60)
        length = size * 1.5
        mx = rng.randint(size // 4, 3 * size // 4)
        my = rng.randint(size // 4, 3 * size // 4)
        dx = math.cos(math.radians(angle)) * length / 2
        dy = math.sin(math.radians(angle)) * length / 2
        draw.line([(mx-dx, my-dy), (mx+dx, my+dy)],
                  fill=add_alpha(col, rng.randint(30, 80)),
                  width=rng.randint(2, 7))

    arc_configs = [
        (size * 0.42, size * 0.55, palette["accent1"], 0.75, 220, 6, 14),
        (size * 0.28, size * 0.36, palette["accent2"], 0.55, 160, 4,  9),
        (size * 0.18, size * 0.22, palette["glow"],    0.85, 120, 3,  6),
    ]
    for (r_min, r_max, col, op, span, wmin, wmax) in arc_configs:
        for _ in range(rng.randint(2, 4)):
            radius = int(rng.uniform(r_min, r_max))
            cx = rng.randint(int(size * 0.2), int(size * 0.8))
            cy = rng.randint(int(size * 0.2), int(size * 0.8))
            sa = rng.randint(0, 360)
            ea = sa + rng.randint(int(span * 0.5), span)
            draw_arc_stroke(draw, cx, cy, radius, sa, ea,
                            add_alpha(col, rng.randint(int(255*op*0.5), int(255*op))),
                            width=rng.randint(wmin, wmax))

    for _ in range(12):
        r  = rng.randint(4, 22)
        cx = rng.randint(60, size - 60)
        cy = rng.randint(60, size - 60)
        col = rng.choice([palette["glow"], palette["accent1"], palette["text"]])
        draw.ellipse([cx-r, cy-r, cx+r, cy+r],
                     fill=add_alpha(col, rng.randint(120, 255)))

    cx = size // 2 + rng.randint(-100, 100)
    cy = size // 2 + rng.randint(-80,  80)
    orb = np.zeros((size, size, 4), dtype=np.float32)
    draw_radial_gradient(orb, cx, cy, 0, int(size * 0.32), palette["glow"], intensity=0.55)
    img = Image.alpha_composite(img, to_image(orb))
    return img


def build_grain(size, intensity=14):
    rng   = np.random.default_rng(42)
    noise = rng.integers(0, intensity, (size, size), dtype=np.uint8)
    rgba  = np.zeros((size, size, 4), dtype=np.uint8)
    rgba[:, :, :3] = noise[:, :, None]
    rgba[:, :, 3]  = noise
    return Image.fromarray(rgba, "RGBA")


def build_vignette(size, strength=0.68):
    arr    = np.zeros((size, size, 4), dtype=np.float32)
    cy, cx = size / 2, size / 2
    ys, xs = np.ogrid[:size, :size]
    dist   = np.sqrt(((xs - cx) / cx) ** 2 + ((ys - cy) / cy) ** 2)
    arr[:, :, 3] = np.clip((dist - 0.55) / 0.55, 0, 1) ** 1.6 * strength * 255
    return to_image(arr)


# Valid text positions
TEXT_POSITIONS = [
    "bottom-left",   "bottom-center",   "bottom-right",
    "center-left",   "center",          "center-right",
    "top-left",      "top-center",      "top-right",
]

# Short aliases
TEXT_POSITION_ALIASES = {
    "bl": "bottom-left",   "bc": "bottom-center",  "br": "bottom-right",
    "cl": "center-left",   "c":  "center",          "cr": "center-right",
    "tl": "top-left",      "tc": "top-center",      "tr": "top-right",
    # Spotify-style
    "bottom": "bottom-left", "top": "top-left", "middle": "center",
}


def resolve_text_position(raw):
    """Normalise any alias or full name to a canonical key."""
    key = raw.lower().strip()
    return TEXT_POSITION_ALIASES.get(key, key)


def build_text_layer(size, name, palette, font_bold_path, font_light_path,
                     position="bottom-left"):
    """
    position is one of TEXT_POSITIONS:
      bottom-left / bottom-center / bottom-right
      center-left / center        / center-right
      top-left    / top-center    / top-right
    """
    img  = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    margin = int(size * 0.09)
    max_w  = size - 2 * margin
    upper  = name.upper()

    # Vertical zone: top / center / bottom
    v_zone = "bottom"
    if position.startswith("top"):
        v_zone = "top"
    elif position.startswith("center") or position == "center":
        v_zone = "center"

    # Horizontal alignment: left / center / right
    h_align = "left"
    if position.endswith("center") or position == "center":
        h_align = "center"
    elif position.endswith("right"):
        h_align = "right"

    # -- Find best font size --
    font_size = int(size * 0.16)
    font = None
    lines = []
    while font_size >= int(size * 0.055):
        font  = ImageFont.truetype(font_bold_path, font_size)
        words = upper.split()
        lines, cur = [], ""
        for word in words:
            test = (cur + " " + word).strip()
            if draw.textbbox((0, 0), test, font=font)[2] <= max_w:
                cur = test
            else:
                if cur:
                    lines.append(cur)
                cur = word
        if cur:
            lines.append(cur)
        if len(lines) <= 3:
            break
        font_size -= 10

    lh  = draw.textbbox((0, 0), "A", font=font)[3]
    gap = int(lh * 0.22)
    total_h = len(lines) * lh + (len(lines) - 1) * gap

    # Decoration metrics
    bar_h       = max(6, int(size * 0.006))
    bar_gap     = int(size * 0.025)   # space between bar and text block
    label_size  = max(28, int(size * 0.020))
    label_gap   = int(size * 0.012)
    deco_h      = bar_h + bar_gap + label_size + label_gap  # total above text

    # -- Vertical anchor for the text block --
    if v_zone == "bottom":
        block_top = size - margin - int(size * 0.04) - total_h
    elif v_zone == "top":
        # Decoration sits BELOW text for top positions
        block_top = margin + int(size * 0.04)
    else:  # center
        # Centre the text block + decoration vertically
        full_h    = deco_h + total_h
        block_top = (size - full_h) // 2 + deco_h

    # -- Horizontal x for each line --
    def line_x(line_text):
        lw = draw.textbbox((0, 0), line_text, font=font)[2]
        if h_align == "left":
            return margin
        elif h_align == "right":
            return size - margin - lw
        else:  # center
            return (size - lw) // 2

    # -- Draw text lines --
    so = max(3, font_size // 50)
    for i, line in enumerate(lines):
        y  = block_top + i * (lh + gap)
        x  = line_x(line)
        draw.text((x + so, y + so), line, font=font, fill=(0, 0, 0, 160))
        draw.text((x, y),           line, font=font, fill=add_alpha(palette["text"], 255))

    # -- Accent bar position --
    bar_w = int(size * 0.25)
    if v_zone == "bottom" or v_zone == "center":
        bar_y = block_top - bar_gap - bar_h
    else:  # top: bar goes below text
        bar_y = block_top + total_h + bar_gap

    # Horizontal start of bar matches text alignment
    if h_align == "left":
        bar_x = margin
    elif h_align == "right":
        bar_x = size - margin - bar_w
    else:
        bar_x = (size - bar_w) // 2

    # Draw gradient bar (left-to-right always, direction doesn't flip)
    for px in range(bar_w):
        col = lerp_color(palette["accent1"], palette["accent2"], px / bar_w)
        draw.line([(bar_x + px, bar_y), (bar_x + px, bar_y + bar_h)],
                  fill=add_alpha(col, 230))

    # -- "PLAYLIST" label --
    try:
        label_font = ImageFont.truetype(font_light_path, label_size)
    except Exception:
        label_font = font

    label_text = "PLAYLIST"
    label_w    = draw.textbbox((0, 0), label_text, font=label_font)[2]

    if v_zone in ("bottom", "center"):
        label_y = bar_y - label_size - label_gap
    else:  # top: label below bar
        label_y = bar_y + bar_h + label_gap

    if h_align == "left":
        label_x = margin
    elif h_align == "right":
        label_x = size - margin - label_w
    else:
        label_x = (size - label_w) // 2

    draw.text((label_x, label_y), label_text,
              font=label_font, fill=add_alpha(palette["accent1"], 180))
    return img


# ==============================================================================
# Main Generator
# ==============================================================================
def safe_slug(text):
    return "".join(c if c.isalnum() or c in "_-" else "_"
                   for c in text.strip()).strip("_")


def generate_cover(playlist_name, theme_key="auto", pattern_key="auto",
                   font_bold=None, font_light=None, output_path=None,
                   matte=False, text_pos="bottom-left"):
    if not playlist_name.strip():
        raise ValueError("Playlist name cannot be empty.")

    rng       = random.Random(seed_from_name(playlist_name))
    palette   = get_palette(playlist_name, theme_key)
    pat_style = pattern_from_name(playlist_name) if pattern_key == "auto" else pattern_key

    matte_label = "  [MATTE]" if matte else ""
    text_pos    = resolve_text_position(text_pos)
    print(f"  > Playlist : '{playlist_name}'")
    print(f"  > Theme    : {palette.get('name', theme_key)}{matte_label}")
    print(f"  > Pattern  : {pat_style}  ({PATTERN_DESCRIPTIONS.get(pat_style, '')})")
    print(f"  > Text pos : {text_pos}")
    print(f"  > Font     : {font_bold}")

    canvas = build_background(SIZE, palette, rng, matte=matte).convert("RGBA")
    canvas = Image.alpha_composite(canvas, build_pattern_layer(SIZE, palette, rng, pat_style, matte=matte))
    canvas = Image.alpha_composite(canvas, build_geometry(SIZE, palette, rng))
    canvas = Image.alpha_composite(canvas, build_grain(SIZE))
    # Softer vignette in matte mode so pattern stays visible at edges
    canvas = Image.alpha_composite(canvas, build_vignette(SIZE, strength=0.45 if matte else 0.68))
    canvas = Image.alpha_composite(canvas, build_text_layer(
        SIZE, playlist_name, palette, font_bold, font_light or font_bold,
        position=text_pos))

    name_slug    = safe_slug(playlist_name)
    theme_slug   = theme_key if theme_key != "auto" else safe_slug(
        palette.get("name", "auto")).lower()
    pattern_slug  = f"_{pat_style}" if pattern_key != "auto" else ""
    matte_suffix  = "_matte" if matte else ""
    pos_suffix    = f"_{text_pos.replace('-', '_')}" if text_pos != "bottom-left" else ""
    default_filename = f"{name_slug}_{theme_slug}{pattern_slug}{pos_suffix}{matte_suffix}.png"

    if output_path is None:
        output_path = default_filename
    else:
        out = Path(output_path)
        if out.suffix == "" or out.is_dir():
            out.mkdir(parents=True, exist_ok=True)
            output_path = str(out / default_filename)
        else:
            out.parent.mkdir(parents=True, exist_ok=True)
            output_path = str(out)

    canvas.convert("RGB").save(output_path, "PNG")
    print(f"  OK Saved -> {output_path}  ({SIZE}x{SIZE}px)")
    return Path(output_path)


# ==============================================================================
# CLI
# ==============================================================================
def list_themes():
    print("\n  Available themes:\n")
    print(f"  {'KEY':<12}  DESCRIPTION")
    print(f"  {'-'*12}  {'-'*30}")
    for key, data in THEMES.items():
        label = (data.get("name", "Auto") if data
                 else "Auto -- chosen by hashing the playlist name")
        print(f"  {key:<12}  {label}")
    print()


def list_patterns():
    print("\n  Available patterns:\n")
    print(f"  {'KEY':<12}  DESCRIPTION")
    print(f"  {'-'*12}  {'-'*40}")
    print(f"  {'auto':<12}  Auto -- chosen by hashing the playlist name")
    for key in PATTERNS:
        print(f"  {key:<12}  {PATTERN_DESCRIPTIONS[key]}")
    print()


def main():
    parser = argparse.ArgumentParser(
        description="Generate a bold Spotify playlist cover image.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
font help:
  Fonts are loaded from ~/.fonts/ first, then system paths.
  To use a custom font, pass a file or directory:
    --font ~/Downloads/Poppins/           (auto-selects bold + light)
    --font ~/fonts/Raleway-Black.ttf      (single file)

  Download Poppins (free): https://fonts.google.com/specimen/Poppins
  Place at: ~/.fonts/truetype/google-fonts/

examples:
  python3 spotify_cover_gen.py "Late Night Drive"
  python3 spotify_cover_gen.py "Chill Vibes"       --theme neon
  python3 spotify_cover_gen.py "Night City"         --theme cyberpunk --pattern carbon
  python3 spotify_cover_gen.py "Night City"         --theme cyberpunk --pattern carbon  --matte
  python3 spotify_cover_gen.py "Night City"         --theme gold      --pattern hexgrid --matte
  python3 spotify_cover_gen.py "Night City"         --theme matte --text-pos center
  python3 spotify_cover_gen.py "Night City"         --theme neon  --text-pos top-right
  python3 spotify_cover_gen.py "Night City"         --text-pos br
  python3 spotify_cover_gen.py "Night City"         --theme all --output ./covers/
  python3 spotify_cover_gen.py --list-themes
  python3 spotify_cover_gen.py --list-patterns
        """,
    )
    parser.add_argument("name",            nargs="?",        help="Playlist name")
    parser.add_argument("--theme",   "-t", default="auto",   metavar="THEME",
                        help="Color theme key or 'all'. See --list-themes.")
    parser.add_argument("--pattern", "-p", default="auto",   metavar="PATTERN",
                        help="Pattern style or 'auto'. See --list-patterns.")
    parser.add_argument("--font",    "-f", default=None,     metavar="PATH",
                        help="Font file or directory.")
    parser.add_argument("--output",  "-o", default=None,     metavar="PATH",
                        help="Output file or directory (created if missing).")
    parser.add_argument("--text-pos", "-x", default="bottom-left", metavar="POS",
                        help="Text block position. Options: bottom-left (default), "
                             "bottom-center, bottom-right, center-left, center, "
                             "center-right, top-left, top-center, top-right. "
                             "Short aliases: bl, bc, br, cl, c, cr, tl, tc, tr.")
    parser.add_argument("--matte",  "-m", action="store_true",
                        help="Matt black background: kills all glows, pattern pops. "
                             "Best with --pattern carbon or --pattern hexgrid.")
    parser.add_argument("--list-themes",   action="store_true",
                        help="Print all theme keys and exit.")
    parser.add_argument("--list-patterns", action="store_true",
                        help="Print all pattern keys and exit.")

    args = parser.parse_args()

    if args.list_themes:
        list_themes()
        sys.exit(0)
    if args.list_patterns:
        list_patterns()
        sys.exit(0)

    if not args.name:
        parser.print_help()
        sys.exit(1)

    if args.theme != "all" and args.theme not in THEMES:
        print(f"\n  ERROR: Unknown theme '{args.theme}'. Run --list-themes.\n")
        sys.exit(1)

    valid_patterns = ["auto"] + PATTERNS
    if args.pattern not in valid_patterns:
        print(f"\n  ERROR: Unknown pattern '{args.pattern}'. Run --list-patterns.\n")
        sys.exit(1)

    resolved_pos = resolve_text_position(args.text_pos)
    if resolved_pos not in TEXT_POSITIONS:
        valid = ", ".join(TEXT_POSITIONS)
        print(f"\n  ERROR: Unknown text position '{args.text_pos}'.\n"
              f"  Valid: {valid}\n"
              f"  Aliases: bl, bc, br, cl, c, cr, tl, tc, tr\n")
        sys.exit(1)

    try:
        font_bold, font_light = resolve_fonts(args.font)
    except FileNotFoundError as e:
        print(f"\n  ERROR: Font not found: {e}\n")
        sys.exit(1)

    if args.theme == "all":
        theme_keys = [k for k in THEMES if k != "auto"]
        print(f"\n  Generating all {len(theme_keys)} themes for '{args.name}'...\n")
    else:
        theme_keys = [args.theme]
        print()

    output_arg = args.output
    if len(theme_keys) > 1 and output_arg is not None:
        if Path(output_arg).suffix != "":
            print("  ERROR: --theme all requires --output to be a directory.\n")
            sys.exit(1)

    for theme_key in theme_keys:
        generate_cover(
            playlist_name=args.name,
            theme_key=theme_key,
            pattern_key=args.pattern,
            font_bold=font_bold,
            font_light=font_light,
            output_path=output_arg,
            matte=args.matte,
            text_pos=resolved_pos,
        )

    print()
    if len(theme_keys) > 1:
        print(f"  Done -- {len(theme_keys)} covers generated.")
    print()


if __name__ == "__main__":
    main()
