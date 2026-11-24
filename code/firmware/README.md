# ResumeCard firmware — LED smoke test

Minimal sketch to prove the **ATtiny2313A → WS2812B** path works.

## What you should see

1. On reset: **LED index 0** glows dim **red** for ~0.8 s  
2. Then a dim **chase** across all 25 LEDs, cycling **red → green → blue**

If colors are swapped (e.g. you ask for red and get green), check GRB order / DIN.  
If nothing lights: adapter, 8 MHz fuses, DIN on PA0, power.

## Requirements

- **MCU pinout adapter** from [`adapter/`](../../adapter/) — do not seat a bare 2313A in U1  
- Clock: **8 MHz** internal, **CKDIV8 disabled**  
- Toolchain: Arduino IDE + [ATTinyCore](https://github.com/SpenceKonde/ATTinyCore)  
- Board: ATtiny2313 / ATtiny2313A  
- Flash via **ISP** (USBasp, Arduino as ISP, …) on J2  

## Brightness

`SMOKE_LEVEL` is ~28/255. Do not run full-white on all 25 LEDs from USB without measuring current.

## Timing note

Bitbang is **inline AVR asm** on `PORTA`/`PA0`. A C `if` around `PORTA |=` lets GCC hoist the rising edge and break 0-bit timing — see comments in `firmware.ino`.
