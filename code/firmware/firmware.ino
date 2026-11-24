#include <Arduino.h>
#define RGB 3
#define G 0
#define R 1
#define B 2
#define T1H 6
#define T1L 4
#define T0H 2
#define T0L 7
#define FOOTER_CYCLES 640

static const uint8_t NUM_LEDS = 25;
static uint8_t leds[NUM_LEDS][RGB];  //   grb

static const uint8_t WS2812_PIN = PA0;

inline void leds_clear();
inline void leds_set(uint8_t idx, uint8_t r, uint8_t g, uint8_t b);
inline void leds_show();
inline void my_memset(uint8_t* dest, uint8_t value, uint8_t bytes);

void setup()
{
    pinMode(WS2812_PIN, OUTPUT);
    digitalWrite(WS2812_PIN, LOW);

    leds_clear();
}

void loop()
{
    leds_show();
}

inline void leds_clear()
{
    my_memset((uint8_t*)leds, 0, sizeof(leds));
}
inline void leds_set(uint8_t idx, uint8_t r, uint8_t g, uint8_t b)
{
    leds[idx][B] = b;
    leds[idx][G] = g;
    leds[idx][R] = r;

}
/*0.4us - 0 bit | 0.8us - 1 bit*/
inline void leds_show()
{
    uint8_t i = 0, j = 0, led = 0;
    const uint8_t* led_p = (const uint8_t*)leds;
    uint8_t oldSREG = SREG;

    cli(); //Disable INT
    PORTA &= ~(1 << PA0);

    for (; i < sizeof(leds); ++i, ++led_p)
    {
        led = *led_p;
        for(j=0; j < 8; ++j, led <<= 1)
        {
            if (led & 0x80)
            {
                PORTA |= (1 << PA0);
                __builtin_avr_delay_cycles(T1H);
                PORTA &= ~(1 << PA0);
                __builtin_avr_delay_cycles(T1L);
            }
            else
            {
                PORTA |= (1 << PA0);
                __builtin_avr_delay_cycles(T0H);
                PORTA &= ~(1 << PA0);
                __builtin_avr_delay_cycles(T0L);
            }            
        }
    }
    PORTA &= ~(1 << PA0);
    SREG = oldSREG; // Also Enable INT
    __builtin_avr_delay_cycles(FOOTER_CYCLES);
}


inline void my_memset(uint8_t* dest, uint8_t value, uint8_t bytes)
{
    while (0 != bytes)
    {
        *dest = value;
        ++dest;
        --bytes;
    }
}
