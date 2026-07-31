#!/usr/bin/env python3
"""
Generate animated profile banner SVGs (dark.svg & light.svg) for GitHub README.
Converts a source image into pixel-block ASCII art and embeds it into a terminal-
style SVG panel with animated SYSTEM.INFO section.

Usage:
    python3 generate_banner.py <image_path> [output_dir]
"""
import sys, os, math, random, html

# ─── Try importing Pillow ───
try:
    from PIL import Image
except ImportError:
    print("Pillow is required. Install with: pip install Pillow", file=sys.stderr)
    sys.exit(1)

# ═══════════════════════════════════════════════════════════════
# PROFILE DATA — edit here to change info
# ═══════════════════════════════════════════════════════════════
PROFILE = {
    "email":        "simocv00@42network",
    "pill_email":   "simocv00@student.42.fr",
    "subject":      "Mohamed ELAYYADY",
    "role":         "Backend Developer",
    "origin":       "Beni Mellal, Morocco",
    "education":    "42 Network",
    "status":       "Building + Learning + Shipping",
    "toolchain":    "Vim, Git, Docker, Make, GDB",
    "core_lang":    "C, C++, Python",
    "core_frontend":"—",
    "core_backend": "Unix Sockets, REST APIs",
    "core_database":"PostgreSQL",
    "core_infra":   "Docker, Linux, Git, Make",
    "mail":         "simocv00@student.42.fr",
    "portfolio":    "coming soon",
    "linkedin":     "mohamed-el-ayyady",
    "github":       "@simocv00",
    "facebook":     "",  # empty = skip
}

# ═══════════════════════════════════════════════════════════════
# THEMES
# ═══════════════════════════════════════════════════════════════
THEMES = {
    "dark": {
        "BG": "#070B16", "PANEL_BG": "#0A101F", "PANEL_GRAD_TOP": "#0A101F",
        "PANEL_GRAD_BOT": "#0C1426", "BAR": "#0B1222",
        "CYAN": "#22D3EE", "VIOLET": "#A78BFA", "VIOLET2": "#7C3AED",
        "EMERALD": "#10B981", "RED": "#F87171",
        "TEXT": "#F8FAFC", "MUTED": "#94A3B8", "DIM": "#475569",
        "DOTS": "rgba(148,163,184,0.35)",
        "PILL_BG": "#4C1D95", "PILL_TEXT": "#E9D5FF",
        "LINE": "rgba(255,255,255,0.10)",
        "BORDER_GLOW": "#22D3EE",
        "GRAD_COLORS": ["#7C3AED", "#22D3EE", "#10B981"],
        "ASCII_COLORS": ["#60A5FA", "#A78BFA", "#22D3EE"],
        "ART_PANEL_STROKE": "rgba(34,211,238,0.35)",
        "ART_PANEL_FILL": "#0A101F",
        "ART_GLOW_STROKE": "#22D3EE",
    },
    "light": {
        "BG": "#F0F4F8", "PANEL_BG": "#FFFFFF", "PANEL_GRAD_TOP": "#FFFFFF",
        "PANEL_GRAD_BOT": "#F8FAFC", "BAR": "#F1F5F9",
        "CYAN": "#0891B2", "VIOLET": "#7C3AED", "VIOLET2": "#7C3AED",
        "EMERALD": "#059669", "RED": "#DC2626",
        "TEXT": "#0F172A", "MUTED": "#475569", "DIM": "#94A3B8",
        "DOTS": "rgba(100,116,139,0.30)",
        "PILL_BG": "#EDE9FE", "PILL_TEXT": "#5B21B6",
        "LINE": "rgba(0,0,0,0.08)",
        "BORDER_GLOW": "#0891B2",
        "GRAD_COLORS": ["#7C3AED", "#0891B2", "#059669"],
        "ASCII_COLORS": ["#1E40AF", "#6D28D9", "#0E7490"],
        "ART_PANEL_STROKE": "rgba(8,145,178,0.35)",
        "ART_PANEL_FILL": "#FFFFFF",
        "ART_GLOW_STROKE": "#0891B2",
    },
}

# ═══════════════════════════════════════════════════════════════
# SVG LAYOUT
# ═══════════════════════════════════════════════════════════════
W, H = 1180, 610
FONT = "ui-monospace,SFMono-Regular,Menlo,Consolas,'Liberation Mono',monospace"
ART_X, ART_Y, ART_W, ART_H = 36, 84, 400, 492
# pixel block size in the SVG
BLOCK = 1
# target grid for ASCII art (within the art panel)
GRID_W, GRID_H = 300, 340
# margins inside art panel for the pixel grid
GRID_OFFSET_X, GRID_OFFSET_Y = 50, 86

def esc(s):
    return html.escape(str(s), quote=True)

# ═══════════════════════════════════════════════════════════════
# IMAGE → PIXEL BLOCKS
# ═══════════════════════════════════════════════════════════════

def image_to_blocks(image_path, grid_w, grid_h, num_layers=20):
    """
    Convert an image to a set of pixel-block layers for SVG rendering.
    Each layer is a list of (x, y) coords. Layers are revealed sequentially
    with opacity animations to create a 'materializing' effect.
    """
    img = Image.open(image_path).convert("L")  # grayscale
    # Resize to grid
    img = img.resize((grid_w, grid_h), Image.LANCZOS)

    # Collect all 'dark enough' pixels (these will form the art)
    pixels = []
    for y in range(grid_h):
        for x in range(grid_w):
            brightness = img.getpixel((x, y))
            # Lower brightness = darker = we want to draw it
            # Use threshold to pick up details
            if brightness < 180:
                # weight: darker pixels are more important
                weight = 1.0 - (brightness / 255.0)
                pixels.append((x, y, weight))

    # Sort by weight (darkest first) then shuffle within weight bands
    # to create a natural reveal effect
    random.seed(42)  # reproducible
    random.shuffle(pixels)
    # Sort partially by weight to ensure darkest appear early
    pixels.sort(key=lambda p: -p[2])

    # Split into layers
    layers = [[] for _ in range(num_layers)]
    for i, (x, y, w) in enumerate(pixels):
        layer_idx = i % num_layers
        layers[layer_idx].append((x, y))

    return layers


def blocks_to_svg_paths(layers, offset_x, offset_y, scale_x=1.24, scale_y=1.45):
    """
    Convert pixel block layers into SVG path elements with staggered animations.
    Uses <path> with M...h1v1h-1z patterns (same as original).
    """
    parts = []
    for i, layer in enumerate(layers):
        if not layer:
            continue
        begin = 0.20 + i * 0.04  # stagger animation start
        # Build path data: each pixel is a 1x1 rect
        # Sort by y then x for efficient path construction
        layer_sorted = sorted(layer, key=lambda p: (p[1], p[0]))

        # Group consecutive horizontal pixels
        path_cmds = []
        j = 0
        while j < len(layer_sorted):
            x, y = layer_sorted[j]
            # Find consecutive run
            run = 1
            while j + run < len(layer_sorted) and layer_sorted[j + run] == (x + run, y):
                run += 1
            if run == 1:
                path_cmds.append(f"M{x} {y}h1v1h-1z")
            else:
                path_cmds.append(f"M{x} {y}h{run}v1h-{run}z")
            j += run

        path_d = "".join(path_cmds)
        parts.append(
            f'<g opacity="0"><animate attributeName="opacity" values="0;1" '
            f'dur="0.9s" begin="{begin:.2f}s" fill="freeze" calcMode="spline" '
            f'keyTimes="0;1" keySplines=".4 0 .2 1"/>'
            f'<path d="{path_d}"/></g>'
        )

    # Wrap with transform and fill
    return parts


def build_ascii_art_section(image_path, theme):
    """Build the complete ASCII art section of the SVG."""
    t = THEMES[theme]
    layers = image_to_blocks(image_path, GRID_W, GRID_H, num_layers=20)
    svg_paths = blocks_to_svg_paths(layers, GRID_OFFSET_X, GRID_OFFSET_Y)

    parts = []
    # Art panel label
    parts.append(f'<text x="38" y="74" font-size="10" letter-spacing="3" fill="{t["DIM"]}">VISUAL.MAP</text>')
    # Art panel border glow
    parts.append(
        f'<rect x="{ART_X}" y="{ART_Y}" width="{ART_W}" height="{ART_H}" rx="10" '
        f'fill="none" stroke="{t["ART_GLOW_STROKE"]}" stroke-width="2" opacity="0.45" filter="url(#glow3)"/>'
    )
    # Art panel fill
    parts.append(
        f'<rect x="{ART_X}" y="{ART_Y}" width="{ART_W}" height="{ART_H}" rx="10" '
        f'fill="{t["ART_PANEL_FILL"]}" stroke="{t["ART_PANEL_STROKE"]}"/>'
    )

    # Pixel art group with transform
    parts.append(
        f'<g transform="translate({GRID_OFFSET_X},{GRID_OFFSET_Y}) scale(1.2400,1.4471)" '
        f'fill="{t["VIOLET"]}" shape-rendering="crispEdges">'
    )
    # Add the animated phase-in → then switch to gradient fill
    parts.append(f'<set attributeName="opacity" to="0" begin="3.2s"/>')

    for path_svg in svg_paths:
        parts.append(path_svg)

    parts.append('</g>')

    # Second copy with gradient fill (appears after phase-in completes)
    parts.append(
        f'<g transform="translate({GRID_OFFSET_X},{GRID_OFFSET_Y}) scale(1.2400,1.4471)" '
        f'fill="url(#asciiGrad)" shape-rendering="crispEdges" opacity="0">'
        f'<animate attributeName="opacity" values="0;1" dur="1.2s" begin="3.2s" fill="freeze" '
        f'calcMode="spline" keyTimes="0;1" keySplines=".4 0 .2 1"/>'
    )
    # Combine all paths without animation
    for layer in layers:
        if not layer:
            continue
        layer_sorted = sorted(layer, key=lambda p: (p[1], p[0]))
        path_cmds = []
        j = 0
        while j < len(layer_sorted):
            x, y = layer_sorted[j]
            run = 1
            while j + run < len(layer_sorted) and layer_sorted[j + run] == (x + run, y):
                run += 1
            if run == 1:
                path_cmds.append(f"M{x} {y}h1v1h-1z")
            else:
                path_cmds.append(f"M{x} {y}h{run}v1h-{run}z")
            j += run
        parts.append(f'<path d="{"".join(path_cmds)}"/>')
    parts.append('</g>')

    # Corner brackets around art panel
    parts.append(f'<path d="M 50 84 L 36 84 L 36 98" fill="none" stroke="{t["CYAN"]}" stroke-width="2" opacity="0.8"/>')
    parts.append(f'<path d="M 422 84 L 436 84 L 436 98" fill="none" stroke="{t["CYAN"]}" stroke-width="2" opacity="0.8"/>')
    parts.append(f'<path d="M 50 576 L 36 576 L 36 562" fill="none" stroke="{t["CYAN"]}" stroke-width="2" opacity="0.8"/>')
    parts.append(f'<path d="M 422 576 L 436 576 L 436 562" fill="none" stroke="{t["CYAN"]}" stroke-width="2" opacity="0.8"/>')

    return "\n".join(parts)


def build_system_info(theme):
    """Build the SYSTEM.INFO text panel."""
    t = THEMES[theme]
    p = PROFILE
    parts = []

    # Header
    parts.append(f'<text x="470" y="106" font-size="13" letter-spacing="2" fill="{t["CYAN"]}" filter="url(#txtGlow)">SYSTEM.INFO</text>')
    parts.append(f'<line x1="566" y1="102" x2="1061" y2="102" stroke="{t["LINE"]}"/>')
    parts.append(
        f'<text x="1125" y="106" text-anchor="end" font-size="12" fill="{t["RED"]}" font-weight="700">'
        f'<tspan>&#9679;</tspan> LIVE<animate attributeName="opacity" values="1;0.25;1" dur="1.6s" repeatCount="indefinite"/></text>'
    )

    # Email pill
    parts.append(f'<g opacity="0"><animate attributeName="opacity" from="0" to="1" dur="0.5s" begin="0.6s" fill="freeze"/>')
    parts.append(f'<rect x="470" y="122" width="245" height="20" rx="4" fill="{t["PILL_BG"]}"/>')
    parts.append(f'<text x="479" y="136" font-size="14" font-weight="700" fill="{t["PILL_TEXT"]}">{esc(p["pill_email"])}</text>')
    parts.append(f'<line x1="725" y1="130" x2="1125" y2="130" stroke="{t["LINE"]}"/>')
    parts.append('</g>')

    # Info rows
    rows = [
        ("Subject",       p["subject"],       0.90),
        ("Role",          p["role"],           1.02),
        ("Origin",        p["origin"],         1.14),
        ("Education",     p["education"],      1.26),
        ("Status",        p["status"],         1.38),
        ("ToolChain",     p["toolchain"],      1.50),
    ]
    y_pos = 162
    for label, value, begin in rows:
        dots = "." * max(5, 60 - len(label) - len(value))
        parts.append(_info_row(label, value, dots, y_pos, begin, t))
        y_pos += 23

    # Core section (after a small gap)
    y_pos += 8
    core_rows = [
        ("Core.Lang",     p["core_lang"],      1.72),
        ("Core.Frontend", p["core_frontend"],  1.84),
        ("Core.Backend",  p["core_backend"],   1.96),
        ("Core.Database", p["core_database"],  2.08),
        ("Core.Infra",    p["core_infra"],     2.20),
    ]
    for label, value, begin in core_rows:
        dots = "." * max(5, 60 - len(label) - len(value))
        parts.append(_info_row(label, value, dots, y_pos, begin, t))
        y_pos += 23

    # Contact separator
    y_pos += 8
    parts.append(
        f'<g opacity="0"><animate attributeName="opacity" from="0" to="1" dur="0.4s" begin="2.42s" fill="freeze"/>'
        f'<text x="470" y="{y_pos}" font-size="14" textLength="655" lengthAdjust="spacingAndGlyphs" xml:space="preserve">'
        f'<tspan fill="{t["MUTED"]}">- Contact </tspan>'
        f'<tspan fill="{t["DOTS"]}">---------------------------------------------------------------------</tspan>'
        f'</text></g>'
    )
    y_pos += 23

    # Contact rows
    contact_rows = [
        ("Grid.Mail",     p["mail"],           2.54),
        ("Grid.Portfolio", p["portfolio"],      2.66),
        ("Grid.LinkedIn", p["linkedin"],        2.78),
        ("Grid.GitHub",   p["github"],          2.90),
    ]
    if p.get("facebook"):
        contact_rows.append(("Grid.Facebook", p["facebook"], 3.02))

    for label, value, begin in contact_rows:
        dots = "." * max(5, 60 - len(label) - len(value))
        parts.append(_info_row(label, value, dots, y_pos, begin, t))
        y_pos += 23

    # Footer message
    y_pos += 8
    parts.append(
        f'<g opacity="0"><animate attributeName="opacity" from="0" to="1" dur="0.5s" begin="3.34s" fill="freeze"/>'
        f'<text x="470" y="{y_pos}" font-size="14" fill="{t["MUTED"]}">'
        f'&#9656; More about me &amp; projects below in README &#8595; '
        f'<tspan fill="{t["CYAN"]}">&#9608;<animate attributeName="fill-opacity" values="1;0;1" dur="1s" repeatCount="indefinite"/></tspan>'
        f'</text></g>'
    )

    return "\n".join(parts)


def _info_row(label, value, dots, y, begin, t):
    return (
        f'<g opacity="0"><animate attributeName="opacity" from="0" to="1" dur="0.4s" begin="{begin:.2f}s" fill="freeze"/>'
        f'<animateTransform attributeName="transform" type="translate" values="-8 0;0 0" dur="0.4s" begin="{begin:.2f}s" fill="freeze"/>'
        f'<text x="470" y="{y}" font-size="14" textLength="655" lengthAdjust="spacingAndGlyphs" xml:space="preserve">'
        f'<tspan fill="{t["CYAN"]}">{esc(label)} </tspan>'
        f'<tspan fill="{t["DOTS"]}">{dots}</tspan>'
        f'<tspan fill="{t["TEXT"]}" font-weight="600"> {esc(value)}</tspan>'
        f'</text></g>'
    )


def build_svg(image_path, theme="dark"):
    """Build the complete SVG banner."""
    t = THEMES[theme]
    p = PROFILE
    gc = t["GRAD_COLORS"]
    ac = t["ASCII_COLORS"]

    svg = []
    svg.append(
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" '
        f'font-family="{FONT}" role="img" aria-label="{esc(p["subject"])} — profile.sh --live">'
    )

    # Defs
    svg.append('<defs>')
    # Accent gradient (animated)
    svg.append(
        f'<linearGradient id="accent" x1="0" y1="0" x2="1" y2="0">'
        f'<stop offset="0" stop-color="{gc[0]}"><animate attributeName="stop-color" values="{gc[0]};{gc[1]};{gc[2]};{gc[0]}" dur="10s" repeatCount="indefinite"/></stop>'
        f'<stop offset="0.5" stop-color="{gc[1]}"><animate attributeName="stop-color" values="{gc[1]};{gc[2]};{gc[0]};{gc[1]}" dur="10s" repeatCount="indefinite"/></stop>'
        f'<stop offset="1" stop-color="{gc[2]}"><animate attributeName="stop-color" values="{gc[2]};{gc[0]};{gc[1]};{gc[2]}" dur="10s" repeatCount="indefinite"/></stop>'
        f'</linearGradient>'
    )
    # ASCII gradient
    svg.append(
        f'<linearGradient id="asciiGrad" x1="0" y1="0" x2="0" y2="520" gradientUnits="userSpaceOnUse">'
        f'<stop offset="0" stop-color="{ac[0]}"/>'
        f'<stop offset="0.45" stop-color="{ac[1]}"/>'
        f'<stop offset="1" stop-color="{ac[2]}"/>'
        f'<animateTransform attributeName="gradientTransform" type="translate" values="0 -120; 0 120; 0 -120" dur="9s" repeatCount="indefinite"/>'
        f'</linearGradient>'
    )
    # Panel gradient
    svg.append(f'<linearGradient id="panelGrad" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="{t["PANEL_GRAD_TOP"]}"/><stop offset="1" stop-color="{t["PANEL_GRAD_BOT"]}"/></linearGradient>')
    # Filters
    svg.append('<filter id="glow8" x="-60%" y="-60%" width="220%" height="220%"><feGaussianBlur stdDeviation="8"/></filter>')
    svg.append('<filter id="glow3" x="-60%" y="-60%" width="220%" height="220%"><feGaussianBlur stdDeviation="3"/></filter>')
    svg.append('<filter id="txtGlow" x="-30%" y="-30%" width="160%" height="160%"><feGaussianBlur stdDeviation="0.9" result="b"/><feMerge><feMergeNode in="b"/><feMergeNode in="SourceGraphic"/></feMerge></filter>')
    svg.append('<clipPath id="winClip"><rect x="2" y="2" width="1176" height="606" rx="18"/></clipPath>')
    svg.append('</defs>')

    # Background
    svg.append(f'<rect x="2" y="2" width="1176" height="606" rx="18" fill="{t["BG"]}"/>')
    svg.append('<g clip-path="url(#winClip)">')
    svg.append(f'<rect x="2" y="2" width="1176" height="606" fill="url(#panelGrad)"/>')

    # Title bar
    svg.append(f'<rect x="2" y="2" width="1176" height="46" fill="{t["BAR"]}"/>')
    svg.append(f'<line x1="2" y1="48" x2="1178" y2="48" stroke="{t["LINE"]}"/>')
    svg.append('<circle cx="30" cy="25.0" r="5.5" fill="#ff5f56"/>')
    svg.append('<circle cx="50" cy="25.0" r="5.5" fill="#ffbd2e"/>')
    svg.append('<circle cx="70" cy="25.0" r="5.5" fill="#27c93f"/>')
    svg.append(f'<text x="590.0" y="29.0" text-anchor="middle" font-size="12" fill="{t["MUTED"]}">{esc(p["email"])} - % ./profile.sh --live</text>')

    # ASCII Art section
    svg.append(build_ascii_art_section(image_path, theme))

    # System Info section
    svg.append(build_system_info(theme))

    # Close clip group
    svg.append('</g>')

    # Outer border glow
    svg.append(f'<rect x="3" y="3" width="1174" height="604" rx="17" fill="none" stroke="url(#accent)" stroke-width="3" opacity="0.55" filter="url(#glow8)"/>')
    svg.append(f'<rect x="3" y="3" width="1174" height="604" rx="17" fill="none" stroke="url(#accent)" stroke-width="1.6"/>')

    svg.append('</svg>')
    return "\n".join(svg)


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(f"Usage: {sys.argv[0]} <image_path> [output_dir]", file=sys.stderr)
        sys.exit(1)

    image_path = sys.argv[1]
    outdir = sys.argv[2] if len(sys.argv) > 2 else "."

    if not os.path.exists(image_path):
        print(f"Image not found: {image_path}", file=sys.stderr)
        sys.exit(1)

    os.makedirs(outdir, exist_ok=True)

    for theme, fname in (("dark", "dark.svg"), ("light", "light.svg")):
        print(f"Generating {fname} ({theme} theme)...")
        svg = build_svg(image_path, theme)
        path = os.path.join(outdir, fname)
        with open(path, "w") as f:
            f.write(svg)
        print(f"  → {path} ({len(svg) // 1024} KB)")

    print("Done!")
