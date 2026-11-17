#!/usr/bin/env python3
"""Generate ResumeCard ATtiny2313A pin-remap adapter Gerbers, drill, SVG, and KiCad PCB."""

from __future__ import annotations

import csv
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PROD = ROOT / "production"
PIN_MAP = ROOT / "pin_map.csv"

# DIP-20 geometry (mm), pin 1 at local (0,0), left column down, right column up
PITCH = 2.54
ROW = 7.62
PAD_R = 0.8
DRILL_R = 0.4
TRACE_W = 0.35

# Placement on board
BOARD_ORIGIN = (8.0, 6.0)  # J_BOARD pin 1
MCU_ORIGIN = (28.0, 6.0)  # U_MCU pin 1
EDGE_MARGIN = 2.0


def dip_local(pin: int) -> tuple[float, float]:
    if not 1 <= pin <= 20:
        raise ValueError(pin)
    if pin <= 10:
        return (0.0, (pin - 1) * PITCH)
    return (ROW, (20 - pin) * PITCH)


def load_map() -> list[dict[str, str]]:
    with PIN_MAP.open(newline="") as f:
        return list(csv.DictReader(f))


def board_outline() -> tuple[float, float, float, float]:
    xs, ys = [], []
    for origin in (BOARD_ORIGIN, MCU_ORIGIN):
        for pin in range(1, 21):
            lx, ly = dip_local(pin)
            xs.append(origin[0] + lx)
            ys.append(origin[1] + ly)
    return (
        min(xs) - EDGE_MARGIN - 1.0,
        min(ys) - EDGE_MARGIN - 1.0,
        max(xs) + EDGE_MARGIN + 1.0,
        max(ys) + EDGE_MARGIN + 1.0,
    )


# --- Gerber helpers (mm, absolute, 4.6) ---

def fmt(x: float) -> str:
    return f"{x * 1_000_000:0.0f}"


def gerber_header(name: str) -> list[str]:
    return [
        "%TF.GenerationSoftware,ResumeCard,adapter-generator,1.0*%",
        f"%TF.FileFunction,{name}*%",
        "%FSLAX46Y46*%",
        "%MOMM*%",
        "%LPD*%",
        "G01*",
        "%ADD10C,1.600000*%",  # pad flash
        "%ADD11C,0.350000*%",  # trace
        "%ADD12C,0.150000*%",  # silk
    ]


def flash_pad(x: float, y: float) -> str:
    return f"D10*{fmt(x)}X{fmt(y)}D03*"


def draw_line(x1: float, y1: float, x2: float, y2: float, aper: str = "D11") -> list[str]:
    return [
        f"{aper}*",
        f"X{fmt(x1)}Y{fmt(y1)}D02*",
        f"X{fmt(x2)}Y{fmt(y2)}D01*",
    ]


def route_points(board_pin: int, mcu_pin: int) -> list[tuple[float, float]]:
    """Simple 3-segment Manhattan-ish route between board pad and MCU pad."""
    bx = BOARD_ORIGIN[0] + dip_local(board_pin)[0]
    by = BOARD_ORIGIN[1] + dip_local(board_pin)[1]
    mx = MCU_ORIGIN[0] + dip_local(mcu_pin)[0]
    my = MCU_ORIGIN[1] + dip_local(mcu_pin)[1]
    # Mid channel between footprints
    mid_x = (BOARD_ORIGIN[0] + ROW + MCU_ORIGIN[0]) / 2.0
    # Stagger mid Y slightly by pin to reduce overlap
    stagger = ((mcu_pin - 1) % 10) * 0.15
    mid_y = (by + my) / 2.0 + (stagger if mcu_pin <= 10 else -stagger)
    return [(bx, by), (mid_x, by), (mid_x, my), (mx, my)]


def write_copper(path: Path, rows: list[dict[str, str]], layer_name: str, use_front_routes: bool) -> None:
    lines = gerber_header(layer_name)
    # Pads
    for origin in (BOARD_ORIGIN, MCU_ORIGIN):
        for pin in range(1, 21):
            lx, ly = dip_local(pin)
            lines.append(flash_pad(origin[0] + lx, origin[1] + ly))
    # Routes: odd MCU pins on F.Cu, even on B.Cu to reduce crossings
    for row in rows:
        mcu = int(row["mcu_pin_attiny2313a"])
        board = int(row["board_u1_pad"])
        front = (mcu % 2 == 1)
        if front != use_front_routes:
            continue
        pts = route_points(board, mcu)
        for a, b in zip(pts, pts[1:]):
            lines.extend(draw_line(a[0], a[1], b[0], b[1], "D11"))
    lines.append("M02*")
    path.write_text("\n".join(lines) + "\n")


def write_mask(path: Path, layer_name: str) -> None:
    lines = gerber_header(layer_name)
    # Slightly larger mask openings
    lines[6] = "%ADD10C,1.700000*%"
    for origin in (BOARD_ORIGIN, MCU_ORIGIN):
        for pin in range(1, 21):
            lx, ly = dip_local(pin)
            lines.append(flash_pad(origin[0] + lx, origin[1] + ly))
    lines.append("M02*")
    path.write_text("\n".join(lines) + "\n")


def write_silk(path: Path) -> None:
    lines = gerber_header("Legend,Top")
    xmin, ymin, xmax, ymax = board_outline()
    # Labels as simple line glyphs (approximate boxes + tick for pin 1)
    # Board pin1 marker
    bx, by = BOARD_ORIGIN
    mx, my = MCU_ORIGIN
    lines.extend(draw_line(bx - 1.2, by - 1.2, bx + 1.2, by - 1.2, "D12"))
    lines.extend(draw_line(mx - 1.2, my - 1.2, mx + 1.2, my - 1.2, "D12"))
    # Outline notches (pin 1 side)
    lines.extend(draw_line(bx - 1.5, by - 2.0, bx + ROW + 1.5, by - 2.0, "D12"))
    lines.extend(draw_line(mx - 1.5, my - 2.0, mx + ROW + 1.5, my - 2.0, "D12"))
    # Vertical separators / body outline hints
    lines.extend(draw_line(bx - 1.5, by - 2.0, bx - 1.5, by + 9 * PITCH + 2.0, "D12"))
    lines.extend(draw_line(bx + ROW + 1.5, by - 2.0, bx + ROW + 1.5, by + 9 * PITCH + 2.0, "D12"))
    lines.extend(draw_line(mx - 1.5, my - 2.0, mx - 1.5, my + 9 * PITCH + 2.0, "D12"))
    lines.extend(draw_line(mx + ROW + 1.5, my - 2.0, mx + ROW + 1.5, my + 9 * PITCH + 2.0, "D12"))
    # Board edge
    lines.extend(draw_line(xmin, ymin, xmax, ymin, "D12"))
    lines.extend(draw_line(xmax, ymin, xmax, ymax, "D12"))
    lines.extend(draw_line(xmax, ymax, xmin, ymax, "D12"))
    lines.extend(draw_line(xmin, ymax, xmin, ymin, "D12"))
    lines.append("M02*")
    path.write_text("\n".join(lines) + "\n")


def write_edge(path: Path) -> None:
    xmin, ymin, xmax, ymax = board_outline()
    lines = [
        "%TF.GenerationSoftware,ResumeCard,adapter-generator,1.0*%",
        "%TF.FileFunction,Profile,NP*%",
        "%FSLAX46Y46*%",
        "%MOMM*%",
        "%LPD*%",
        "G01*",
        "%ADD13C,0.100000*%",
        "D13*",
        f"X{fmt(xmin)}Y{fmt(ymin)}D02*",
        f"X{fmt(xmax)}Y{fmt(ymin)}D01*",
        f"X{fmt(xmax)}Y{fmt(ymax)}D01*",
        f"X{fmt(xmin)}Y{fmt(ymax)}D01*",
        f"X{fmt(xmin)}Y{fmt(ymin)}D01*",
        "M02*",
    ]
    path.write_text("\n".join(lines) + "\n")


def write_drill(path: Path) -> None:
    lines = [
        "M48",
        "; DRILL file {ResumeCard MCU adapter}",
        "; FORMAT={-:-/ absolute / metric / decimal}",
        "FMAT,2",
        "METRIC",
        "T1C0.800",
        "%",
        "G90",
        "G05",
        "T1",
    ]
    for origin in (BOARD_ORIGIN, MCU_ORIGIN):
        for pin in range(1, 21):
            lx, ly = dip_local(pin)
            x = origin[0] + lx
            y = origin[1] + ly
            lines.append(f"X{x:.3f}Y{y:.3f}")
    lines.append("M30")
    path.write_text("\n".join(lines) + "\n")


def write_svg(path: Path, rows: list[dict[str, str]]) -> None:
    xmin, ymin, xmax, ymax = board_outline()
    w, h = xmax - xmin, ymax - ymin
    scale = 8.0

    def tx(x: float, y: float) -> tuple[float, float]:
        return ((x - xmin) * scale, (y - ymin) * scale)

    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{w * scale:.0f}" height="{h * scale:.0f}" '
        f'viewBox="0 0 {w * scale:.1f} {h * scale:.1f}">',
        "<style>text{font-family:monospace;font-size:9px;fill:#222} .pad{fill:#c9a227;stroke:#333;stroke-width:0.5}"
        ".trace{fill:none;stroke:#d35400;stroke-width:1.2;opacity:0.85}"
        ".traceb{fill:none;stroke:#2980b9;stroke-width:1.2;opacity:0.85}"
        ".edge{fill:#e8f5e9;stroke:#1b5e20;stroke-width:1.5}</style>",
    ]
    x0, y0 = tx(xmin, ymin)
    x1, y1 = tx(xmax, ymax)
    parts.append(f'<rect class="edge" x="{x0}" y="{y0}" width="{x1 - x0}" height="{y1 - y0}" rx="2"/>')

    for row in rows:
        mcu = int(row["mcu_pin_attiny2313a"])
        board = int(row["board_u1_pad"])
        pts = route_points(board, mcu)
        d = "M " + " L ".join(f"{tx(x, y)[0]:.1f} {tx(x, y)[1]:.1f}" for x, y in pts)
        cls = "trace" if mcu % 2 else "traceb"
        parts.append(f'<path class="{cls}" d="{d}"/>')

    for label, origin in (("BOARD", BOARD_ORIGIN), ("MCU", MCU_ORIGIN)):
        for pin in range(1, 21):
            lx, ly = dip_local(pin)
            cx, cy = tx(origin[0] + lx, origin[1] + ly)
            parts.append(f'<circle class="pad" cx="{cx:.1f}" cy="{cy:.1f}" r="{PAD_R * scale:.1f}"/>')
            parts.append(f'<text x="{cx + 6:.1f}" y="{cy + 3:.1f}">{pin}</text>')
        ox, oy = tx(origin[0] + ROW / 2, origin[1] - 3.2)
        parts.append(f'<text x="{ox:.1f}" y="{oy:.1f}" text-anchor="middle">{label}</text>')

    parts.append(
        f'<text x="{(x0 + x1) / 2:.1f}" y="{y1 - 4:.1f}" text-anchor="middle">'
        "ResumeCard MCU adapter — orange F.Cu / blue B.Cu</text>"
    )
    parts.append("</svg>")
    path.write_text("\n".join(parts) + "\n")


def write_kicad_pcb(path: Path, rows: list[dict[str, str]]) -> None:
    """Minimal KiCad 8/9 PCB the user can open and re-route if desired."""
    xmin, ymin, xmax, ymax = board_outline()
    nets = []
    for i, row in enumerate(rows, start=1):
        nets.append(f'\t(net {i} "{row["signal"]}")')

    signal_to_net = {row["signal"]: i for i, row in enumerate(rows, start=1)}
    mcu_pin_net = {int(r["mcu_pin_attiny2313a"]): signal_to_net[r["signal"]] for r in rows}
    board_pin_net = {int(r["board_u1_pad"]): signal_to_net[r["signal"]] for r in rows}

    def fp_clean(ref: str, value: str, origin: tuple[float, float], which: str) -> str:
        pads = []
        for pin in range(1, 21):
            lx, ly = dip_local(pin)
            if which == "mcu":
                net_i = mcu_pin_net[pin]
                sig = next(r["signal"] for r in rows if int(r["mcu_pin_attiny2313a"]) == pin)
            else:
                net_i = board_pin_net[pin]
                sig = next(r["signal"] for r in rows if int(r["board_u1_pad"]) == pin)
            shape = "roundrect" if pin == 1 else "circle"
            extra = "\n\t\t\t(roundrect_rratio 0.25)" if pin == 1 else ""
            pads.append(
                f"""\t\t(pad "{pin}" thru_hole {shape}
\t\t\t(at {lx} {ly})
\t\t\t(size 1.6 1.6)
\t\t\t(drill 0.8)
\t\t\t(layers "*.Cu" "*.Mask")
\t\t\t(net {net_i} "{sig}"){extra}
\t\t)"""
            )
        body = "\n".join(pads)
        return f"""\t(footprint "Package_DIP:DIP-20_W7.62mm"
\t\t(layer "F.Cu")
\t\t(uuid {uuid_for(ref)})
\t\t(at {origin[0]} {origin[1]})
\t\t(property "Reference" "{ref}"
\t\t\t(at 3.81 -2.5 0)
\t\t\t(layer "F.SilkS")
\t\t\t(effects (font (size 1 1) (thickness 0.15)))
\t\t)
\t\t(property "Value" "{value}"
\t\t\t(at 3.81 26 0)
\t\t\t(layer "F.Fab")
\t\t\t(effects (font (size 1 1) (thickness 0.15)))
\t\t)
\t\t(attr through_hole)
{body}
\t)"""

    def uuid_for(ref: str) -> str:
        # Stable fake UUIDs for KiCad
        base = {"J1": "aaaaaaaa-bbbb-cccc-ddd1-000000000001", "U1": "aaaaaaaa-bbbb-cccc-ddd1-000000000002"}
        return base[ref]

    # Tracks
    tracks = []
    for row in rows:
        mcu = int(row["mcu_pin_attiny2313a"])
        board = int(row["board_u1_pad"])
        net_i = signal_to_net[row["signal"]]
        layer = "F.Cu" if mcu % 2 else "B.Cu"
        pts = route_points(board, mcu)
        for a, b in zip(pts, pts[1:]):
            tracks.append(
                f"""\t(segment
\t\t(start {a[0]:.3f} {a[1]:.3f})
\t\t(end {b[0]:.3f} {b[1]:.3f})
\t\t(width {TRACE_W})
\t\t(layer "{layer}")
\t\t(net {net_i})
\t)"""
            )

    content = f"""(kicad_pcb
\t(version 20240108)
\t(generator "ResumeCard adapter generator")
\t(generator_version "1.0")
\t(general
\t\t(thickness 1.6)
\t\t(legacy_teardrops no)
\t)
\t(paper "A4")
\t(layers
\t\t(0 "F.Cu" signal)
\t\t(31 "B.Cu" signal)
\t\t(32 "B.Adhes" user "B.Adhesive")
\t\t(33 "F.Adhes" user "F.Adhesive")
\t\t(34 "B.Paste" user)
\t\t(35 "F.Paste" user)
\t\t(36 "B.SilkS" user "B.Silkscreen")
\t\t(37 "F.SilkS" user "F.Silkscreen")
\t\t(38 "B.Mask" user)
\t\t(39 "F.Mask" user)
\t\t(44 "Edge.Cuts" user)
\t\t(45 "Margin" user)
\t\t(46 "B.CrtYd" user "B.Courtyard")
\t\t(47 "F.CrtYd" user "F.Courtyard")
\t\t(48 "B.Fab" user "B.Fabrication")
\t\t(49 "F.Fab" user "F.Fabrication")
\t)
\t(setup
\t\t(pad_to_mask_clearance 0.051)
\t\t(allow_soldermask_bridges_in_footprints no)
\t\t(pcbplotparams
\t\t\t(layerselection 0x00010fc_ffffffff)
\t\t\t(plot_on_all_layers_selection 0x0000000_00000000)
\t\t\t(disableapertmacros no)
\t\t\t(usegerberextensions no)
\t\t\t(usegerberattributes yes)
\t\t\t(usegerberadvancedattributes yes)
\t\t\t(creategerberjobfile yes)
\t\t\t(dashed_line_dash_ratio 12.000000)
\t\t\t(dashed_line_gap_ratio 3.000000)
\t\t\t(svgprecision 4)
\t\t\t(plotframeref no)
\t\t\t(mode 1)
\t\t\t(useauxorigin no)
\t\t\t(hpglpennumber 1)
\t\t\t(hpglpenspeed 20)
\t\t\t(hpglpendiameter 15.000000)
\t\t\t(pdf_front_fp_property_popups yes)
\t\t\t(pdf_back_fp_property_popups yes)
\t\t\t(dxfpolygonmode yes)
\t\t\t(dxfimperialunits yes)
\t\t\t(dxfusepcbnewfont yes)
\t\t\t(psnegative no)
\t\t\t(psa4output no)
\t\t\t(plotreference yes)
\t\t\t(plotvalue yes)
\t\t\t(plotfptext yes)
\t\t\t(plotinvisibletext no)
\t\t\t(sketchpadonline no)
\t\t\t(subtractmaskfromsilk no)
\t\t\t(outputformat 1)
\t\t\t(mirror no)
\t\t\t(drillshape 1)
\t\t\t(scaleselection 1)
\t\t\t(outputdirectory "production/")
\t\t)
\t)
\t(net 0 "")
{chr(10).join(nets)}
{fp_clean("J1", "TO_ResumeCard_U1", BOARD_ORIGIN, "board")}
{fp_clean("U1", "ATtiny2313A", MCU_ORIGIN, "mcu")}
{chr(10).join(tracks)}
\t(gr_rect
\t\t(start {xmin:.3f} {ymin:.3f})
\t\t(end {xmax:.3f} {ymax:.3f})
\t\t(stroke (width 0.1) (type solid))
\t\t(fill none)
\t\t(layer "Edge.Cuts")
\t)
\t(gr_text "BOARD ->"
\t\t(at {BOARD_ORIGIN[0] + ROW / 2:.3f} {BOARD_ORIGIN[1] - 3.5:.3f})
\t\t(layer "F.SilkS")
\t\t(effects (font (size 1.2 1.2) (thickness 0.18)))
\t)
\t(gr_text "<- MCU 2313A"
\t\t(at {MCU_ORIGIN[0] + ROW / 2:.3f} {MCU_ORIGIN[1] - 3.5:.3f})
\t\t(layer "F.SilkS")
\t\t(effects (font (size 1.2 1.2) (thickness 0.18)))
\t)
)
"""
    path.write_text(content)


def write_kicad_sch(path: Path, rows: list[dict[str, str]]) -> None:
    # Minimal schematic as documentation-friendly hierarchical notes via symbols as boxes is heavy;
    # emit a simple KiCad schematic with two connectors and labeled wires using hierarchical labels style.
    # For practicality, write a KiCad 8 schematic with no library deps: use graphical text + net labels only.
    texts = [
        "ResumeCard MCU Adapter",
        "J1 = board U1 pin order (shifted)",
        "U1 = ATtiny2313A datasheet pin order",
        "See pin_map.csv for connections",
    ]
    y = 25.4
    elems = []
    for t in texts:
        elems.append(
            f"""\t\t(text "{t}"
\t\t\t(exclude_from_sim no)
\t\t\t(at 25.4 {y} 0)
\t\t\t(effects (font (size 1.27 1.27)) (justify left bottom))
\t\t)"""
        )
        y += 5.08

    y = 55.0
    for row in rows:
        line = (
            f'{row["signal"]}: MCU pin {row["mcu_pin_attiny2313a"]} '
            f'({row["mcu_pin_name"]}) <-> Board pad {row["board_u1_pad"]} ({row["board_net"]})'
        )
        elems.append(
            f"""\t\t(text "{line}"
\t\t\t(exclude_from_sim no)
\t\t\t(at 25.4 {y} 0)
\t\t\t(effects (font (size 1.0 1.0)) (justify left bottom))
\t\t)"""
        )
        y += 3.5

    content = f"""(kicad_sch
\t(version 20231120)
\t(generator "ResumeCard adapter generator")
\t(generator_version "1.0")
\t(uuid aaaaaaaa-bbbb-cccc-ddd0-000000000010)
\t(paper "A4")
\t(title_block
\t\t(title "ResumeCard MCU Pinout Adapter")
\t\t(date "2026-11-17")
\t\t(rev "1")
\t\t(company "ResumeCard")
\t)
\t(lib_symbols)
\t(sheet_instances
\t\t(path "/"
\t\t\t(page "1")
\t\t)
\t)
{chr(10).join(elems)}
)
"""
    path.write_text(content)


def write_kicad_pro(path: Path) -> None:
    path.write_text(
        """{
  "board": {
    "design_settings": {
      "defaults": {},
      "diff_pair_dimensions": [],
      "drc_exclusions": [],
      "rules": {},
      "track_widths": [0.0, 0.35],
      "via_dimensions": []
    }
  },
  "meta": {
    "filename": "ResumeCard_MCU_Adapter.kicad_pro",
    "version": 1
  },
  "project": {
    "files": []
  },
  "sheets": [
    ["ResumeCard_MCU_Adapter.kicad_sch", "Root"]
  ],
  "text_variables": {}
}
"""
    )


def main() -> None:
    rows = load_map()
    assert len(rows) == 20
    PROD.mkdir(parents=True, exist_ok=True)

    write_copper(PROD / "ResumeCard_MCU_Adapter-F_Cu.gtl", rows, "Copper,L1,Top", True)
    write_copper(PROD / "ResumeCard_MCU_Adapter-B_Cu.gbl", rows, "Copper,L2,Bot", False)
    write_mask(PROD / "ResumeCard_MCU_Adapter-F_Mask.gts", "Soldermask,Top")
    write_mask(PROD / "ResumeCard_MCU_Adapter-B_Mask.gbs", "Soldermask,Bot")
    write_silk(PROD / "ResumeCard_MCU_Adapter-F_Silkscreen.gto")
    write_edge(PROD / "ResumeCard_MCU_Adapter-Edge_Cuts.gm1")
    write_drill(PROD / "ResumeCard_MCU_Adapter-PTH.drl")
    write_svg(ROOT / "preview.svg", rows)

    write_kicad_pro(ROOT / "ResumeCard_MCU_Adapter.kicad_pro")
    write_kicad_sch(ROOT / "ResumeCard_MCU_Adapter.kicad_sch", rows)
    write_kicad_pcb(ROOT / "ResumeCard_MCU_Adapter.kicad_pcb", rows)

    zip_path = PROD / "ResumeCard_MCU_Adapter.zip"
    with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        for p in sorted(PROD.iterdir()):
            if p.suffix.lower() in {".gtl", ".gbl", ".gts", ".gbs", ".gto", ".gm1", ".drl"}:
                zf.write(p, p.name)

    xmin, ymin, xmax, ymax = board_outline()
    print(f"Wrote adapter files to {ROOT}")
    print(f"Board size: {xmax - xmin:.2f} x {ymax - ymin:.2f} mm")
    print(f"Fab zip: {zip_path}")


if __name__ == "__main__":
    main()
