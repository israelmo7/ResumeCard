#!/usr/bin/env python3
"""Generate side-by-side wrong-board vs correct-2313A DIP pinout SVG."""

from __future__ import annotations

import csv
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "pinout_compare.svg"
PIN_MAP = ROOT / "pin_map.csv"

PITCH = 28
ROW = 90
PAD_W, PAD_H = 52, 20
BODY_W = 70
LEFT_X = 80
RIGHT_X = 420
TOP_Y = 110


def dip_xy(pin: int, origin_x: float) -> tuple[float, float]:
    if pin <= 10:
        return origin_x, TOP_Y + (pin - 1) * PITCH
    return origin_x + BODY_W + ROW, TOP_Y + (20 - pin) * PITCH


def short_label(name: str) -> str:
    name = name.replace("PA2/~RESET", "RESET").replace("~RESET", "RESET")
    if "/" in name:
        parts = name.split("/")
        # Prefer functional name when present
        for p in parts:
            if p in {"RESET", "RXD", "TXD", "MOSI", "MISO", "SCK", "GND", "VCC"}:
                return p
        return parts[0]
    return name


def main() -> None:
    rows = list(csv.DictReader(PIN_MAP.open()))
    board = {int(r["board_u1_pad"]): r for r in rows}
    mcu = {int(r["mcu_pin_attiny2313a"]): r for r in rows}

    # Color groups
    def color_for(signal: str) -> str:
        s = signal.upper()
        if s in {"VCC", "PWR"}:
            return "#c0392b"
        if s == "GND":
            return "#2c3e50"
        if s == "RESET":
            return "#8e44ad"
        if s in {"RXD", "TXD"}:
            return "#2980b9"
        if s in {"MOSI", "MISO", "SCK"}:
            return "#16a085"
        if s == "DIN":
            return "#e67e22"
        if s.startswith("R") or s == "BTN":
            return "#27ae60"
        if s.startswith("C"):
            return "#1abc9c"
        return "#7f8c8d"

    w, h = 720, 460
    parts: list[str] = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}">',
        "<defs>",
        '<marker id="arrow" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="6" markerHeight="6" orient="auto-start-reverse">',
        '<path d="M 0 0 L 10 5 L 0 10 z" fill="#666"/>',
        "</marker>",
        "</defs>",
        '<rect width="100%" height="100%" fill="#f7f4ef"/>',
        '<text x="360" y="28" text-anchor="middle" font-family="Georgia, serif" font-size="20" fill="#1a1a1a">ATtiny2313A Pinout Mismatch</text>',
        '<text x="360" y="48" text-anchor="middle" font-family="ui-sans-serif, system-ui, sans-serif" font-size="12" fill="#555">Board U1 (as laid out) vs datasheet-correct DIP-20 — same signals, pad numbers shifted by 2</text>',
    ]

    def draw_chip(origin_x: float, title: str, subtitle: str, lookup: dict, key_field: str, bad: bool) -> None:
        # body
        bx = origin_x + 10
        by = TOP_Y - 8
        bh = 9 * PITCH + PAD_H + 16
        fill = "#fdecea" if bad else "#eaf7ea"
        stroke = "#c0392b" if bad else "#1e8449"
        parts.append(
            f'<rect x="{bx}" y="{by}" width="{BODY_W + ROW - 20}" height="{bh}" rx="6" fill="{fill}" stroke="{stroke}" stroke-width="2"/>'
        )
        # notch
        cx = bx + (BODY_W + ROW - 20) / 2
        parts.append(f'<path d="M {cx - 12} {by} A 12 12 0 0 0 {cx + 12} {by}" fill="none" stroke="{stroke}" stroke-width="2"/>')
        parts.append(
            f'<text x="{cx}" y="{by - 22}" text-anchor="middle" font-family="ui-sans-serif, system-ui, sans-serif" font-size="14" font-weight="700" fill="{stroke}">{title}</text>'
        )
        parts.append(
            f'<text x="{cx}" y="{by - 8}" text-anchor="middle" font-family="ui-sans-serif, system-ui, sans-serif" font-size="11" fill="#666">{subtitle}</text>'
        )

        for pin in range(1, 21):
            row = lookup[pin]
            signal = row["signal"]
            name = short_label(row["mcu_pin_name"] if key_field == "mcu" else row["board_net"] if row["board_net"] != "PWR" else "VCC")
            if key_field == "board":
                # show board net / signal
                name = short_label(row["signal"] if row["signal"] != "BTN" else "BTN/PA1")
                if row["signal"] == "DIN":
                    name = "DIN/PA0"
            else:
                name = short_label(row["mcu_pin_name"])
            x, y = dip_xy(pin, origin_x)
            # left column labels outside left; right column outside right
            if pin <= 10:
                pad_x = x - PAD_W
                label_x = pad_x - 6
                anchor = "end"
                pin_tx = pad_x + 8
                sig_tx = pad_x + PAD_W - 6
                sig_anchor = "end"
            else:
                pad_x = x
                label_x = pad_x + PAD_W + 6
                anchor = "start"
                pin_tx = pad_x + PAD_W - 8
                sig_tx = pad_x + 6
                sig_anchor = "start"
            col = color_for(signal)
            parts.append(
                f'<rect x="{pad_x}" y="{y}" width="{PAD_W}" height="{PAD_H}" rx="3" fill="#fff" stroke="{col}" stroke-width="1.5"/>'
            )
            parts.append(
                f'<text x="{pin_tx}" y="{y + 14}" text-anchor="{"start" if pin <= 10 else "end"}" font-family="ui-monospace, monospace" font-size="10" fill="#333">{pin}</text>'
            )
            parts.append(
                f'<text x="{sig_tx}" y="{y + 14}" text-anchor="{sig_anchor}" font-family="ui-sans-serif, system-ui, sans-serif" font-size="10" font-weight="600" fill="{col}">{name}</text>'
            )

    draw_chip(LEFT_X, "YOUR BOARD U1", "wrong pad order (as manufactured)", board, "board", True)
    draw_chip(RIGHT_X, "ATtiny2313A", "correct datasheet pinout", mcu, "mcu", False)

    # Center legend / shift callout
    parts.append(
        '<rect x="255" y="180" width="150" height="110" rx="8" fill="#fff" stroke="#bbb" stroke-width="1"/>'
    )
    parts.append(
        '<text x="330" y="205" text-anchor="middle" font-family="ui-sans-serif, system-ui, sans-serif" font-size="12" font-weight="700" fill="#333">2-pin cyclic shift</text>'
    )
    parts.append(
        '<text x="330" y="228" text-anchor="middle" font-family="ui-monospace, monospace" font-size="11" fill="#555">MCU pin N</text>'
    )
    parts.append(
        '<text x="330" y="248" text-anchor="middle" font-family="ui-sans-serif, system-ui, sans-serif" font-size="18" fill="#c0392b">↓</text>'
    )
    parts.append(
        '<text x="330" y="270" text-anchor="middle" font-family="ui-monospace, monospace" font-size="11" fill="#555">Board pad ((N-3) mod 20)+1</text>'
    )

    # Example mappings
    examples = [(1, 19, "RESET"), (10, 8, "GND"), (20, 18, "VCC"), (5, 3, "DIN")]
    ey = 420
    parts.append(
        f'<text x="360" y="{ey - 18}" text-anchor="middle" font-family="ui-sans-serif, system-ui, sans-serif" font-size="12" fill="#333">Examples — adapter reconnects these:</text>'
    )
    x = 40
    for mcu_p, board_p, sig in examples:
        col = color_for(sig)
        parts.append(
            f'<rect x="{x}" y="{ey - 10}" width="155" height="28" rx="4" fill="#fff" stroke="{col}" stroke-width="1.2"/>'
        )
        parts.append(
            f'<text x="{x + 77}" y="{ey + 8}" text-anchor="middle" font-family="ui-monospace, monospace" font-size="11" fill="#222">'
            f"MCU {mcu_p} → Board {board_p}  {sig}</text>"
        )
        x += 170

    parts.append("</svg>")
    OUT.write_text("\n".join(parts) + "\n")
    print(f"Wrote {OUT}")


if __name__ == "__main__":
    main()
