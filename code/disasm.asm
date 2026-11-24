
./build/firmware.ino.elf:     file format elf32-avr


Disassembly of section .text:

00000000 <__vectors>:
   0:	14 c0       	rjmp	.+40     	; 0x2a <__ctors_end>
   2:	21 c0       	rjmp	.+66     	; 0x46 <__bad_interrupt>
   4:	20 c0       	rjmp	.+64     	; 0x46 <__bad_interrupt>
   6:	1f c0       	rjmp	.+62     	; 0x46 <__bad_interrupt>
   8:	1e c0       	rjmp	.+60     	; 0x46 <__bad_interrupt>
   a:	1d c0       	rjmp	.+58     	; 0x46 <__bad_interrupt>
   c:	1c c0       	rjmp	.+56     	; 0x46 <__bad_interrupt>
   e:	1b c0       	rjmp	.+54     	; 0x46 <__bad_interrupt>
  10:	1a c0       	rjmp	.+52     	; 0x46 <__bad_interrupt>
  12:	19 c0       	rjmp	.+50     	; 0x46 <__bad_interrupt>
  14:	18 c0       	rjmp	.+48     	; 0x46 <__bad_interrupt>
  16:	17 c0       	rjmp	.+46     	; 0x46 <__bad_interrupt>
  18:	16 c0       	rjmp	.+44     	; 0x46 <__bad_interrupt>
  1a:	15 c0       	rjmp	.+42     	; 0x46 <__bad_interrupt>
  1c:	14 c0       	rjmp	.+40     	; 0x46 <__bad_interrupt>
  1e:	13 c0       	rjmp	.+38     	; 0x46 <__bad_interrupt>
  20:	12 c0       	rjmp	.+36     	; 0x46 <__bad_interrupt>
  22:	11 c0       	rjmp	.+34     	; 0x46 <__bad_interrupt>
  24:	10 c0       	rjmp	.+32     	; 0x46 <__bad_interrupt>
  26:	0f c0       	rjmp	.+30     	; 0x46 <__bad_interrupt>
  28:	0e c0       	rjmp	.+28     	; 0x46 <__bad_interrupt>

0000002a <__ctors_end>:
  2a:	11 24       	eor	r1, r1
  2c:	1f be       	out	0x3f, r1	; 63
  2e:	cf ed       	ldi	r28, 0xDF	; 223
  30:	cd bf       	out	0x3d, r28	; 61

00000032 <__do_clear_bss>:
  32:	20 e0       	ldi	r18, 0x00	; 0
  34:	a0 e6       	ldi	r26, 0x60	; 96
  36:	b0 e0       	ldi	r27, 0x00	; 0
  38:	01 c0       	rjmp	.+2      	; 0x3c <.do_clear_bss_start>

0000003a <.do_clear_bss_loop>:
  3a:	1d 92       	st	X+, r1

0000003c <.do_clear_bss_start>:
  3c:	ab 3a       	cpi	r26, 0xAB	; 171
  3e:	b2 07       	cpc	r27, r18
  40:	e1 f7       	brne	.-8      	; 0x3a <.do_clear_bss_loop>
  42:	02 d0       	rcall	.+4      	; 0x48 <main>
  44:	39 c0       	rjmp	.+114    	; 0xb8 <_exit>

00000046 <__bad_interrupt>:
  46:	dc cf       	rjmp	.-72     	; 0x0 <__vectors>

00000048 <main>:
*/

  // Use the Millis Timer for fast PWM (unless it doesn't have an output).
  #if (TIMER_TO_USE_FOR_MILLIS == 0)
    #if defined(WGM01) // if Timer0 has PWM
      TCCR0A = (1<<WGM01) | (1<<WGM00);
  48:	83 e0       	ldi	r24, 0x03	; 3
  4a:	80 bf       	out	0x30, r24	; 48
    #endif
    #if defined(TCCR0B) //The x61 has a wacky Timer0!
      TCCR0B = (MillisTimer_Prescale_Index << CS00);
  4c:	83 bf       	out	0x33, r24	; 51
    TCCR1A = 1<<WGM10;
    TCCR1B = (1<<WGM12) | (MillisTimer_Prescale_Index << CS10);
  #endif

  // this needs to be called before setup() or some functions won't work there
  sei();
  4e:	78 94       	sei
                cli();
    *reg &= ~bit;
    *out |= bit;
    SREG = oldSREG;
  } else {
    uint8_t oldSREG = SREG;
  50:	8f b7       	in	r24, 0x3f	; 63
                cli();
  52:	f8 94       	cli
    *reg |= bit;
  54:	88 9a       	sbi	0x11, 0	; 17
    SREG = oldSREG;
  56:	8f bf       	out	0x3f, r24	; 63
  if (timer != NOT_ON_TIMER) turnOffPWM(timer);

  out = portOutputRegister(port);

  if (val == LOW) {
    uint8_t oldSREG = SREG;
  58:	8f b7       	in	r24, 0x3f	; 63
    cli();
  5a:	f8 94       	cli
    *out &= ~bit;
  5c:	90 98       	cbi	0x12, 0	; 18
    SREG = oldSREG;
  5e:	8f bf       	out	0x3f, r24	; 63
  60:	e0 e6       	ldi	r30, 0x60	; 96
  62:	f0 e0       	ldi	r31, 0x00	; 0

inline void my_memset(uint8_t* dest, uint8_t value, uint8_t bytes)
{
    while (0 != bytes)
    {
        *dest = value;
  64:	11 92       	st	Z+, r1
}


inline void my_memset(uint8_t* dest, uint8_t value, uint8_t bytes)
{
    while (0 != bytes)
  66:	30 e0       	ldi	r19, 0x00	; 0
  68:	eb 3a       	cpi	r30, 0xAB	; 171
  6a:	f3 07       	cpc	r31, r19
  6c:	d9 f7       	brne	.-10     	; 0x64 <main+0x1c>
/*0.4us - 0 bit | 0.8us - 1 bit*/
inline void leds_show()
{
    uint8_t i = 0, j = 0, led = 0;
    const uint8_t* led_p = (const uint8_t*)leds;
    uint8_t oldSREG = SREG;
  6e:	2f b7       	in	r18, 0x3f	; 63

    cli(); //Disable INT
  70:	f8 94       	cli
    PORTA &= ~(1 << PA0);
  72:	d8 98       	cbi	0x1b, 0	; 27
  74:	e0 e6       	ldi	r30, 0x60	; 96
  76:	f0 e0       	ldi	r31, 0x00	; 0

    for (; i < sizeof(leds); ++i, ++led_p)
    {
        led = *led_p;
  78:	91 91       	ld	r25, Z+
  7a:	88 e0       	ldi	r24, 0x08	; 8
        for(j=0; j < 8; ++j, led <<= 1)
        {
            if (led & 0x80)
            {
                PORTA |= (1 << PA0);
  7c:	d8 9a       	sbi	0x1b, 0	; 27
    for (; i < sizeof(leds); ++i, ++led_p)
    {
        led = *led_p;
        for(j=0; j < 8; ++j, led <<= 1)
        {
            if (led & 0x80)
  7e:	97 ff       	sbrs	r25, 7
  80:	14 c0       	rjmp	.+40     	; 0xaa <main+0x62>
            {
                PORTA |= (1 << PA0);
                __builtin_avr_delay_cycles(T1H);
  82:	32 e0       	ldi	r19, 0x02	; 2
  84:	3a 95       	dec	r19
  86:	f1 f7       	brne	.-4      	; 0x84 <main+0x3c>
                PORTA &= ~(1 << PA0);
  88:	d8 98       	cbi	0x1b, 0	; 27
                __builtin_avr_delay_cycles(T1L);
  8a:	00 c0       	rjmp	.+0      	; 0x8c <main+0x44>
  8c:	00 c0       	rjmp	.+0      	; 0x8e <main+0x46>
    PORTA &= ~(1 << PA0);

    for (; i < sizeof(leds); ++i, ++led_p)
    {
        led = *led_p;
        for(j=0; j < 8; ++j, led <<= 1)
  8e:	99 0f       	add	r25, r25
  90:	81 50       	subi	r24, 0x01	; 1
  92:	a1 f7       	brne	.-24     	; 0x7c <main+0x34>
    uint8_t oldSREG = SREG;

    cli(); //Disable INT
    PORTA &= ~(1 << PA0);

    for (; i < sizeof(leds); ++i, ++led_p)
  94:	80 e0       	ldi	r24, 0x00	; 0
  96:	eb 3a       	cpi	r30, 0xAB	; 171
  98:	f8 07       	cpc	r31, r24
  9a:	71 f7       	brne	.-36     	; 0x78 <main+0x30>
                PORTA &= ~(1 << PA0);
                __builtin_avr_delay_cycles(T0L);
            }            
        }
    }
    PORTA &= ~(1 << PA0);
  9c:	d8 98       	cbi	0x1b, 0	; 27
    SREG = oldSREG; // Also Enable INT
  9e:	2f bf       	out	0x3f, r18	; 63
    __builtin_avr_delay_cycles(FOOTER_CYCLES);
  a0:	35 ed       	ldi	r19, 0xD5	; 213
  a2:	3a 95       	dec	r19
  a4:	f1 f7       	brne	.-4      	; 0xa2 <main+0x5a>
  a6:	00 00       	nop
  a8:	e2 cf       	rjmp	.-60     	; 0x6e <main+0x26>
                __builtin_avr_delay_cycles(T1L);
            }
            else
            {
                PORTA |= (1 << PA0);
                __builtin_avr_delay_cycles(T0H);
  aa:	00 c0       	rjmp	.+0      	; 0xac <main+0x64>
                PORTA &= ~(1 << PA0);
  ac:	d8 98       	cbi	0x1b, 0	; 27
                __builtin_avr_delay_cycles(T0L);
  ae:	32 e0       	ldi	r19, 0x02	; 2
  b0:	3a 95       	dec	r19
  b2:	f1 f7       	brne	.-4      	; 0xb0 <main+0x68>
  b4:	00 00       	nop
  b6:	eb cf       	rjmp	.-42     	; 0x8e <main+0x46>

000000b8 <_exit>:
  b8:	f8 94       	cli

000000ba <__stop_program>:
  ba:	ff cf       	rjmp	.-2      	; 0xba <__stop_program>
