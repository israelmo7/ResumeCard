# ResumeCard MCU Pinout Adapter

Small **DIP-20 remapping PCB** so a real **ATtiny2313A** can run on ResumeCard despite the main board’s U1 footprint pad order being shifted vs the datasheet.

## What it fixes

ResumeCard `U1` pad numbering is a **2-pin cyclic shift** from the ATtiny2313(A) DIP-20 datasheet. The nets on the main board are fine; seating a 2313A notch-to-notch on U1 puts power/GPIO on the wrong pins.

This adapter reconnects:

| ATtiny2313A pin (datasheet) | ResumeCard U1 pad |
| ---: | ---: |
| 1 (RESET) | 19 |
| 2 (PD0/RXD) | 20 |
| 3 (PD1/TXD) | 1 |
| 4 (PA1) | 2 |
| 5 (PA0 / LED DIN) | 3 |
| 6–9 (PD2–PD5) | 4–7 |
| 10 (GND) | 8 |
| 11 (PD6) | 9 |
| 12–17 (PB0–PB5) | 10–15 |
| 18–19 (PB6–PB7) | 16–17 |
| 20 (VCC) | 18 |

Full table: [`pin_map.csv`](pin_map.csv).

## Board layout

Side-by-side DIP-20 footprints on one 2-layer PCB:

- **J_BOARD** — plugs into ResumeCard `U1` (use a DIP socket on the main board, or solder long male headers into `J_BOARD` and mate carefully)
- **U_MCU** — solder the **ATtiny2313A** here (or a machined DIP socket)

Silkscreen marks `BOARD →` / `← MCU`, pin 1 notches, and `GND` / `VCC`.

## Recommended MCU

**ATtiny2313A** (DIP-20), 5 V capable, same pinout as ATtiny2313. Prefer 2313A over the older 2313.

## Assembly

1. On ResumeCard, fit a **DIP-20 socket** in `U1` if the MCU is not already hard-soldered the wrong way.
2. Solder the ATtiny2313A (or a socket) into **U_MCU** on this adapter — notch matches silkscreen pin 1.
3. Solder **male pin headers** into **J_BOARD**, pins pointing down to plug into ResumeCard’s U1 socket.
4. Plug adapter `J_BOARD` into ResumeCard `U1`.
5. Flash via the main board ISP header as usual.

**Power check before LEDs:** confirm continuity `adapter U_MCU pin 20 → board VCC` and `U_MCU pin 10 → board GND`, and that those are not swapped.

## Fabrication

Gerbers + drill are in [`production/`](production/) (`ResumeCard_MCU_Adapter.zip`).  
Typical JLCPCB/PCBWay 2-layer settings work (1.6 mm FR4, HASL or ENIG, 0.3 mm min drill OK).

Preview: [`preview.svg`](preview.svg)

**Before ordering:** open the Gerbers (or the KiCad PCB) in a viewer and confirm pad 1 notches, `VCC`/`GND`, and that `J_BOARD` pitch matches ResumeCard `U1`. These files were generated from `pin_map.csv` programmatically.

Regenerate exports:

```bash
python3 adapter/scripts/generate_adapter.py
```

## KiCad sources

Open [`ResumeCard_MCU_Adapter.kicad_pro`](ResumeCard_MCU_Adapter.kicad_pro) in KiCad 8/9 to edit the schematic/PCB.
