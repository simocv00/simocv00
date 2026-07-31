#!/usr/bin/env python3
"""
Generate animated profile banner SVGs (dark.svg & light.svg) for GitHub README.
"""
import sys, os, html

try:
    from PIL import Image
except ImportError:
    print("Pillow is required. Install with: pip3 install Pillow", file=sys.stderr)
    sys.exit(1)

# ═══════════════════════════════════════════════════════════════
# PROFILE DATA
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
}

# ═══════════════════════════════════════════════════════════════
# THEMES
# ═══════════════════════════════════════════════════════════════
THEMES = {
    "dark": {
        "BG": "#070B16", "PANEL_GRAD_TOP": "#0A101F",
        "PANEL_GRAD_BOT": "#0C1426", "BAR": "#0B1222",
        "CYAN": "#22D3EE", "VIOLET": "#A78BFA", "VIOLET2": "#7C3AED",
        "EMERALD": "#10B981", "RED": "#F87171",
        "TEXT": "#F8FAFC", "MUTED": "#94A3B8", "DIM": "#475569",
        "DOTS": "rgba(148,163,184,0.35)",
        "PILL_BG": "#4C1D95", "PILL_TEXT": "#E9D5FF",
        "LINE": "rgba(255,255,255,0.10)",
        "GRAD_COLORS": ["#7C3AED", "#22D3EE", "#10B981"],
        "ASCII_COLORS": ["#60A5FA", "#A78BFA", "#22D3EE"],
        "ART_PANEL_STROKE": "rgba(34,211,238,0.35)",
        "ART_PANEL_FILL": "#0A101F",
        "ART_GLOW_STROKE": "#22D3EE",
    },
    "light": {
        "BG": "#F0F4F8", "PANEL_GRAD_TOP": "#FFFFFF",
        "PANEL_GRAD_BOT": "#F8FAFC", "BAR": "#F1F5F9",
        "CYAN": "#0891B2", "VIOLET": "#7C3AED", "VIOLET2": "#7C3AED",
        "EMERALD": "#059669", "RED": "#DC2626",
        "TEXT": "#0F172A", "MUTED": "#475569", "DIM": "#94A3B8",
        "DOTS": "rgba(100,116,139,0.30)",
        "PILL_BG": "#EDE9FE", "PILL_TEXT": "#5B21B6",
        "LINE": "rgba(0,0,0,0.08)",
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
GRID_W, GRID_H = 300, 340
GRID_OFFSET_X, GRID_OFFSET_Y = 50, 86
SCALE_X, SCALE_Y = 1.2400, 1.4471

def esc(s):
    return html.escape(str(s), quote=True)


# ═══════════════════════════════════════════════════════════════
# IMAGE → PATH DATA
# ═══════════════════════════════════════════════════════════════

def image_to_layers(image_path, grid_w, grid_h, num_layers=20):
    """Convert image to run-length encoded layers mapped top-to-bottom for animation."""
    img = Image.open(image_path).convert("L")
    img = img.resize((grid_w, grid_h), Image.LANCZOS)

    pixels = []
    for y in range(grid_h):
        for x in range(grid_w):
            # Since the character in the source image is light on dark,
            # we draw the light pixels. A threshold of 100 works well to capture the detail.
            if img.getpixel((x, y)) > 100:
                pixels.append((x, y))

    print(f"  Total pixels to draw: {len(pixels)} / {grid_w * grid_h}")

    # Distribute pixels into layers from top to bottom to replicate the original animation effect.
    layers = [[] for _ in range(num_layers)]
    for x, y in pixels:
        # Strictly use Y coordinate to determine layer for that scanner sweep effect
        layer_idx = int((y / grid_h) * num_layers)
        layer_idx = min(layer_idx, num_layers - 1)
        layers[layer_idx].append((x, y))

    return layers, pixels


def layer_to_path_data(layer):
    """Convert a layer of (x,y) pixels to SVG path data using run-length encoding.
    This creates long horizontal blocks which animate quickly and smoothly."""
    if not layer:
        return ""
    # Sort by y then x
    sorted_px = sorted(layer, key=lambda p: (p[1], p[0]))

    cmds = []
    i = 0
    while i < len(sorted_px):
        x, y = sorted_px[i]
        # Find horizontal run of consecutive pixels
        run = 1
        while (i + run < len(sorted_px) and
               sorted_px[i + run][1] == y and
               sorted_px[i + run][0] == x + run):
            run += 1
        
        if run == 1:
            cmds.append(f"M{x} {y}h1v1h-1z")
        else:
            cmds.append(f"M{x} {y}h{run}v1h-{run}z")
        i += run

    return "".join(cmds)


def build_ascii_art_section(image_path, theme):
    """Build the complete ASCII art section of the SVG."""
    t = THEMES[theme]
    # Original used exactly 20 layers
    layers, all_pixels = image_to_layers(image_path, GRID_W, GRID_H, num_layers=20)

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

    # ── Phase 1: Solid color top-to-bottom sweeping reveal ──
    parts.append(
        f'<g transform="translate({GRID_OFFSET_X},{GRID_OFFSET_Y}) scale({SCALE_X},{SCALE_Y})" '
        f'fill="{t["VIOLET"]}" shape-rendering="crispEdges">'
    )
    # Hide this group at 3.2s (gradient version takes over)
    parts.append(f'<set attributeName="opacity" to="0" begin="3.2s"/>')

    for i, layer in enumerate(layers):
        if not layer:
            continue
        # The original staggered the begin time by exactly 0.03s for 20 layers starting at 0.20s
        begin = 0.20 + i * 0.03
        path_d = layer_to_path_data(layer)
        if path_d:
            parts.append(
                f'<g opacity="0"><animate attributeName="opacity" values="0;1" '
                f'dur="0.9s" begin="{begin:.2f}s" fill="freeze" calcMode="spline" '
                f'keyTimes="0;1" keySplines=".4 0 .2 1"/>'
                f'<path d="{path_d}"/></g>'
            )

    parts.append('</g>')

    # ── Phase 2: Gradient-fill version (fades in at 3.2s) ──
    all_path_data = layer_to_path_data(all_pixels)
    parts.append(
        f'<g transform="translate({GRID_OFFSET_X},{GRID_OFFSET_Y}) scale({SCALE_X},{SCALE_Y})" '
        f'fill="url(#asciiGrad)" shape-rendering="crispEdges" opacity="0">'
        f'<animate attributeName="opacity" values="0;1" dur="1.2s" begin="3.2s" fill="freeze" '
        f'calcMode="spline" keyTimes="0;1" keySplines=".4 0 .2 1"/>'
        f'<path d="{all_path_data}"/>'
        f'</g>'
    )

    # Corner brackets
    for (x1, y1, x2, y2, x3, y3) in [
        (50, 84, 36, 84, 36, 98),
        (422, 84, 436, 84, 436, 98),
        (50, 576, 36, 576, 36, 562),
        (422, 576, 436, 576, 436, 562),
    ]:
        parts.append(
            f'<path d="M {x1} {y1} L {x2} {y2} L {x3} {y3}" '
            f'fill="none" stroke="{t["CYAN"]}" stroke-width="2" opacity="0.8"/>'
        )

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
        parts.append(_info_row(label, value, y_pos, begin, t))
        y_pos += 23

    # Core section
    y_pos += 8
    core_rows = [
        ("Core.Lang",     p["core_lang"],      1.72),
        ("Core.Frontend", p["core_frontend"],  1.84),
        ("Core.Backend",  p["core_backend"],   1.96),
        ("Core.Database", p["core_database"],  2.08),
        ("Core.Infra",    p["core_infra"],     2.20),
    ]
    for label, value, begin in core_rows:
        parts.append(_info_row(label, value, y_pos, begin, t))
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
        ("Grid.Mail",      p["mail"],      2.54),
        ("Grid.Portfolio",  p["portfolio"], 2.66),
        ("Grid.LinkedIn",   p["linkedin"],  2.78),
        ("Grid.GitHub",     p["github"],    2.90),
    ]
    for label, value, begin in contact_rows:
        parts.append(_info_row(label, value, y_pos, begin, t))
        y_pos += 23

    # Footer
    y_pos += 8
    parts.append(
        f'<g opacity="0"><animate attributeName="opacity" from="0" to="1" dur="0.5s" begin="3.34s" fill="freeze"/>'
        f'<text x="470" y="{y_pos}" font-size="14" fill="{t["MUTED"]}">'
        f'&#9656; More about me &amp; projects below in README &#8595; '
        f'<tspan fill="{t["CYAN"]}">&#9608;<animate attributeName="fill-opacity" values="1;0;1" dur="1s" repeatCount="indefinite"/></tspan>'
        f'</text></g>'
    )

    return "\n".join(parts)


def _info_row(label, value, y, begin, t):
    # Auto-generate dots to fill the space
    total_chars = 65
    used = len(label) + len(value) + 2  # +2 for spaces
    dots = "." * max(5, total_chars - used)
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

    # ── Defs ──
    svg.append('<defs>')
    svg.append(
        f'<linearGradient id="accent" x1="0" y1="0" x2="1" y2="0">'
        f'<stop offset="0" stop-color="{gc[0]}"><animate attributeName="stop-color" values="{gc[0]};{gc[1]};{gc[2]};{gc[0]}" dur="10s" repeatCount="indefinite"/></stop>'
        f'<stop offset="0.5" stop-color="{gc[1]}"><animate attributeName="stop-color" values="{gc[1]};{gc[2]};{gc[0]};{gc[1]}" dur="10s" repeatCount="indefinite"/></stop>'
        f'<stop offset="1" stop-color="{gc[2]}"><animate attributeName="stop-color" values="{gc[2]};{gc[0]};{gc[1]};{gc[2]}" dur="10s" repeatCount="indefinite"/></stop>'
        f'</linearGradient>'
    )
    svg.append(
        f'<linearGradient id="asciiGrad" x1="0" y1="0" x2="0" y2="520" gradientUnits="userSpaceOnUse">'
        f'<stop offset="0" stop-color="{ac[0]}"/><stop offset="0.45" stop-color="{ac[1]}"/><stop offset="1" stop-color="{ac[2]}"/>'
        f'<animateTransform attributeName="gradientTransform" type="translate" values="0 -120; 0 120; 0 -120" dur="9s" repeatCount="indefinite"/>'
        f'</linearGradient>'
    )
    svg.append(f'<linearGradient id="panelGrad" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="{t["PANEL_GRAD_TOP"]}"/><stop offset="1" stop-color="{t["PANEL_GRAD_BOT"]}"/></linearGradient>')
    svg.append('<filter id="glow8" x="-60%" y="-60%" width="220%" height="220%"><feGaussianBlur stdDeviation="8"/></filter>')
    svg.append('<filter id="glow3" x="-60%" y="-60%" width="220%" height="220%"><feGaussianBlur stdDeviation="3"/></filter>')
    svg.append('<filter id="txtGlow" x="-30%" y="-30%" width="160%" height="160%"><feGaussianBlur stdDeviation="0.9" result="b"/><feMerge><feMergeNode in="b"/><feMergeNode in="SourceGraphic"/></feMerge></filter>')
    svg.append('<clipPath id="winClip"><rect x="2" y="2" width="1176" height="606" rx="18"/></clipPath>')
    svg.append('</defs>')

    # ── Background & chrome ──
    svg.append(f'<rect x="2" y="2" width="1176" height="606" rx="18" fill="{t["BG"]}"/>')
    svg.append('<g clip-path="url(#winClip)">')
    svg.append(f'<rect x="2" y="2" width="1176" height="606" fill="url(#panelGrad)"/>')
    svg.append(f'<rect x="2" y="2" width="1176" height="46" fill="{t["BAR"]}"/>')
    svg.append(f'<line x1="2" y1="48" x2="1178" y2="48" stroke="{t["LINE"]}"/>')
    svg.append('<circle cx="30" cy="25.0" r="5.5" fill="#ff5f56"/>')
    svg.append('<circle cx="50" cy="25.0" r="5.5" fill="#ffbd2e"/>')
    svg.append('<circle cx="70" cy="25.0" r="5.5" fill="#27c93f"/>')
    svg.append(f'<text x="590.0" y="29.0" text-anchor="middle" font-size="12" fill="{t["MUTED"]}">{esc(p["email"])} - % ./profile.sh --live</text>')

    # ── ASCII art ──
    svg.append(build_ascii_art_section(image_path, theme))

    # ── System info ──
    svg.append(build_system_info(theme))

    # ── Close & borders ──
    svg.append('</g>')
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
        svg_content = build_svg(image_path, theme)
        path = os.path.join(outdir, fname)
        with open(path, "w") as f:
            f.write(svg_content)
        print(f"  → {path} ({len(svg_content) // 1024} KB)")

    print("Done!")
