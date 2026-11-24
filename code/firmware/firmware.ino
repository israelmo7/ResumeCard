/*
 * ResumeCard smoke test — ATtiny2313A + 25x WS2812B
 *
 * Requires:
 *   - Pinout adapter (board U1 pad order is shifted vs datasheet)
 *   - 8 MHz system clock (internal osc, CKDIV8 OFF)
 *   - ATTinyCore / Arduino, board: ATtiny2313(A)
 *
 * DIN is PA0 (datasheet pin 5) after the adapter.
 * Frame order is GRB. Brightness kept low for USB current.
 */

#include <Arduino.h>
#include <avr/io.h>

#define NUM_LEDS 25
#define G 0
#define R 1
#define B 2

/* Dim smoke-test level (~10%). Raise carefully — 25 LEDs at full white is ~1.5 A. */
#define SMOKE_LEVEL 28

/* WS2812 latch / reset: >50 us. 640 cycles @ 8 MHz = 80 us. */
#define RESET_CYCLES 640

static uint8_t leds[NUM_LEDS][3];

static void leds_clear(void);
static void leds_set(uint8_t idx, uint8_t r, uint8_t g, uint8_t b);
static void leds_show(void);
static void ws2812_send_byte(uint8_t data);
static void smoke_pattern(uint8_t step);

void setup(void)
{
    /* PA0 = DIN. Use DDR/PORT directly so we match the asm bitbang port. */
    DDRA |= (1 << PA0);
    PORTA &= ~(1 << PA0);

    leds_clear();
    /* Fixed first-pixel check: dim red on LED 0 (chain index 0 = D5 on the PCB). */
    leds_set(0, SMOKE_LEVEL, 0, 0);
    leds_show();
    delay(800);
}

void loop(void)
{
    static uint8_t step = 0;
    smoke_pattern(step++);
    leds_show();
    delay(120);
}

static void leds_clear(void)
{
    for (uint8_t i = 0; i < NUM_LEDS; ++i) {
        leds[i][G] = 0;
        leds[i][R] = 0;
        leds[i][B] = 0;
    }
}

static void leds_set(uint8_t idx, uint8_t r, uint8_t g, uint8_t b)
{
    if (idx >= NUM_LEDS) {
        return;
    }
    leds[idx][G] = g;
    leds[idx][R] = r;
    leds[idx][B] = b;
}

/*
 * Dim chase: one lit LED walks 0..24.
 * Color cycles R -> G -> B so channel order (GRB) is obvious if wired wrong.
 */
static void smoke_pattern(uint8_t step)
{
    const uint8_t idx = step % NUM_LEDS;
    const uint8_t phase = (step / NUM_LEDS) % 3;

    leds_clear();
    if (phase == 0) {
        leds_set(idx, SMOKE_LEVEL, 0, 0); /* red */
    } else if (phase == 1) {
        leds_set(idx, 0, SMOKE_LEVEL, 0); /* green */
    } else {
        leds_set(idx, 0, 0, SMOKE_LEVEL); /* blue */
    }
}

/*
 * WS2812 bitbang @ 8 MHz on PORTA0.
 *
 * Structure (critical):
 *   sbi HIGH
 *   if bit==0 -> cbi immediately          (short T0H)
 *   if bit==1 -> wait a few cycles, cbi   (long T1H)
 *
 * Do NOT express this as C if/else around PORTA |= — GCC will hoist sbi
 * before the branch and stretch T0H until 0-bits look like 1-bits.
 *
 * Approximate highs at 8 MHz (1 cyc = 0.125 us):
 *   0: sbi(2) + sbrc fall-through(1) + cbi start  ≈ 0.35–0.5 us
 *   1: sbi(2) + sbrc skip(2) + rjmp.+0(2) + nop(1) + cbi ≈ 0.8–1.0 us
 * Low time is filled by path padding + loop overhead; WS2812 tolerates longer lows.
 */
static void ws2812_send_byte(uint8_t data)
{
    asm volatile(
        "ldi  r25, 8              \n" /* 8 bits MSB first */
        "1:                       \n"
        "sbi  %[port], %[pin]     \n" /* HIGH */
        "sbrc %[data], 7          \n" /* skip rjmp if bit7 set */
        "rjmp 2f                  \n" /* bit == 1 */
        /* ---- bit 0: fall early ---- */
        "cbi  %[port], %[pin]     \n"
        "rjmp .+0                 \n" /* T0L pad */
        "nop                      \n"
        "rjmp 3f                  \n"
        /* ---- bit 1: stretch high ---- */
        "2:                       \n"
        "rjmp .+0                 \n"
        "nop                      \n"
        "cbi  %[port], %[pin]     \n"
        "nop                      \n" /* T1L pad (loop also adds low time) */
        "3:                       \n"
        "lsl  %[data]             \n"
        "dec  r25                 \n"
        "brne 1b                  \n"
        : [data] "+r"(data)
        : [port] "I"(_SFR_IO_ADDR(PORTA)), [pin] "I"(PA0)
        : "r25");
}

static void leds_show(void)
{
    const uint8_t *p = (const uint8_t *)leds;
    uint8_t old_sreg = SREG;

    cli();
    for (uint8_t i = 0; i < (uint8_t)sizeof(leds); ++i) {
        ws2812_send_byte(p[i]);
    }
    PORTA &= ~(1 << PA0);
    SREG = old_sreg;
    __builtin_avr_delay_cycles(RESET_CYCLES);
}
