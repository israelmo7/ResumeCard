
#include <FastLED.h>


#define LED_DATA_PIN (3)

#define UNUSED_LED (0xF8F8FF)
#define BASE_A     (CRGB::Yellow)
#define FOLLOWER_A (CRGB::Yellow) /*LightYellow*/
#define BASE_B     (0x0000FF) /*BLUE*/
#define FOLLOWER_B (0x8A2BE2) /*BlueViolet*/
#define BASE_C     (CRGB::Red)
#define FOLLOWER_C (CRGB::Red)

#define NON_VALUE  (-1)

#define ROWS (4)
#define COLUMNS (4)
#define LED_ROW (8)
#define LEDS_SIZE (LED_ROW * LED_ROW)

#define MAX_MOVES_RECORD (32)
#define HANDLERS_SIZE (2)
#define SUCCESS (1)

#define OPENNING_HANDLER (0)
#define TRAVELLING_HANDLER (1)

#define LED_BELOW(index) (index - 2 + (LED_ROW - (index % LED_ROW)) * 2)

static int moves[MAX_MOVES_RECORD] = {0};
static int size = 0;
static CRGB leds[LEDS_SIZE] = {0};
static CRGB bases[] = {BASE_A, BASE_B};
static int bases_size = 2;
char* keypad = "\3\2\1\0\8\4\9\0";

struct handler
{
    int (*_check_func)(int);
};

static struct handler chain[HANDLERS_SIZE];

static int CheckInt(int id);
static int CheckPath(int id); /* [1] for used | [0] for free | [2] for base color | [3] for following color | [4] for another base color | [5] for following color | ... */
static int CheckTarget(int id);
static void InitHandlers(struct handler chain[HANDLERS_SIZE]);
static int ReadSensor(void);
static void WriteLeds(void);
static void ShowLeds(void);
static int ReadSensorFAKE(void);
static void InitLeds(void);
static void HandleFirstMove(int target);
static void HandleNewMove(int target);

void setup() 
{
    /*
    char* runner = keypad;
    while (*runner)
    {
        pinMode(*runner, OUTPUT);
        ++runner;
    }
    while ((++runner, *runner))
    {
        pinMode(*runner, INPUT_PULLUP);
        ++runner;        
    }
*/
    FastLED.addLeds<WS2812B, LED_DATA_PIN, GRB>(leds, LEDS_SIZE);

    FastLED.clear();
    FastLED.show();
    delay(3000);
    Serial.begin(9600);

/*    
    pinMode(R1_PIN, OUTPUT);
    pinMode(R2_PIN, OUTPUT);
    pinMode(R3_PIN, OUTPUT);
    pinMode(R4_PIN, OUTPUT);

    pinMode(C1_PIN, INPUT_PULLUP);
    pinMode(C2_PIN, INPUT_PULLUP);
    pinMode(C3_PIN, INPUT_PULLUP);
    pinMode(C4_PIN, INPUT_PULLUP);
*/
    pinMode(LED_DATA_PIN, OUTPUT);

    InitHandlers(chain);
    InitLeds();
    FastLED.show();
}

void loop() 
{
    int status = !SUCCESS;
    int input = -1;

    if (IsntEnd())
    {
        do
        {
            input = ParallelToSerpentine(KeysToLeds(ReadSensorFAKE()), LED_ROW);
            status = chain[OPENNING_HANDLER]._check_func(input);
        }
        while (SUCCESS != status);

        HandleFirstMove(input);

        do
        {
            input = -1;
            while (-1 == input)
            {
                input = ParallelToSerpentine(KeysToLeds(ReadSensorFAKE()), LED_ROW);
            }
            status = chain[TRAVELLING_HANDLER]._check_func(input);

            if (status > 0)
            {
                HandleNewMove(input);
            }
            else if (status == -2)
            {
                moves[size++] = input;
            }
        }
        while (IsntEnd && status >= 0);

    }
    else
    {
        Serial.println("You did it!");
    }
}
/*
          number_of_buttons = X*Y
          number_of_pins = X+Y  
          X Rows
          Y Columns

          x=y=4
          8 pins and 16 buttons

          1 1       1 2       1 3       1 4
          2 1       2 2       2 3       2 4
          3 1       3 2       3 3       3 4
          4 1       4 2       4 3       4 4
         

         char or uint8 

         so the sensor Output will be int type after small proccessing of parsing 


*/
static int ParallelToSerpentine(int index, int size)
{
    int result = index;
    int row = index / size;
    int column = index % size;

    if (index == -1)
    {
            result = -1;
    }
    else if (row % 2 == 0)
    {
        result = size - column - 2;
        result += (size * row);
    }
    
    return (result);
}
static int KeysToLeds(int index)
{
    /*keys: 4x4 leds: 8x8 */

    int columns = 0;
    int rows    = -1;

    /*Now convert*/

    if (-1 != index)
    {
        columns = index % COLUMNS;;
        rows    = index / ROWS;

        rows *= 2;
        rows *= LED_ROW;
        columns *= 2;
    }

    return (rows + columns);
}
static int ReadSensor(void)
{
    int result = 0;      
    char* read_runner = keypad + ROWS + 1;
    char* write_runner = keypad;
    unsigned int i = 0, j = 0;
    
    for (i = 0; i < ROWS; ++i)
    {
        digitalWrite((int)*write_runner, LOW);
        read_runner = keypad + ROWS + 1;
        delay(1);
        for (j = 0; j < COLUMNS; ++j)
        {
            if (digitalRead((int)*read_runner) != 0)
            {
                result = i * COLUMNS + j;
            }
            ++read_runner;
            delay(1);

        }
        digitalWrite((int)*write_runner, HIGH);
        ++write_runner;
        delay(1);
    }

    return (result);
    /*
    int c1 = 0, c2 = 0, c3 = 0;
    static 
    digitalWrite(R1, HIGH);

    c1 = digitalRead(C1);
    c2 = digitalRead(C2);
    c3 = digitalRead(C3);

    digitalWrite(R1, LOW);
    digitalWrite(R2, HIGH);

    c1 = digitalRead(C1);
    c2 = digitalRead(C2);
    c3 = digitalRead(C3);

    digitalWrite(R2, LOW);
    digitalWrite(R3, HIGH);

    c1 = digitalRead(C1);
    c2 = digitalRead(C2);
    c3 = digitalRead(C3);

    digitalWrite(R3, LOW);
*/
}
int ReadSensorFAKE(void)
{
    int result = -1;

    if (Serial.available() > 0)
    { 
        result = Serial.parseInt();
        Serial.println(result);

        if (result < 0 || result >= ROWS*ROWS)
        {
            result = -1;
        }
    }
    /*should be 0 - ROWS*COLUMNS   when 0 means nothing change */
    return (result);
}

static void PrintMoves(void)
{
    unsigned int i = 0;

    for (i = 0; i < size; ++i)
    {
        Serial.print("move[");
        Serial.print(i, DEC);
        Serial.print("] = (");
        Serial.print(moves[i], DEC);
        Serial.println(")");
    
    }
}
static int DisableLed(int target)
{
    unsigned int i = 0, to_remove = 0;

    for (i = 0; i < size && (moves[i] != target); ++i);

    for (++i; i < size; ++i)
    {
        Serial.print("i = (");
        Serial.print(i, DEC);
        Serial.println(")");
        if (leds[moves[i]] == FOLLOWER_A || leds[moves[i]] == FOLLOWER_B || leds[moves[i]] == FOLLOWER_C)
        {
            WriteToLed(moves[i], UNUSED_LED);
        }
        ++to_remove;
    }

    size -= to_remove;


    return (!!to_remove);
}
void WriteToLed(int index, CRGB value)
{

    bool to_the_right = (index / LED_ROW) % 2 != 0;

    int index_a = index;
    int index_b = index + 1;
    int index_c = LED_BELOW(index);
    int index_d = index_c + 1;


    Serial.println("Writing leds in: ");
    Serial.println(index_a);
    Serial.println(index_b);
    Serial.println(index_c);
    Serial.println(index_d);
    Serial.println(" ..");

    leds[index_a] = value;
    leds[index_b] = value;
    leds[index_c] = value;
    leds[index_d] = value;
}
static void InitLeds(void)
{
    unsigned int i = 0;

    for (i = 0; i < LEDS_SIZE; ++i)
    {
        leds[i] = UNUSED_LED;
    }

    WriteToLed(ParallelToSerpentine(0, LED_ROW), BASE_A);
    WriteToLed(KeysToLeds(ParallelToSerpentine(12, ROWS)), BASE_A);

}
static char* LedToInt(CRGB val)
{
    char* result = "-1";

    if (val == UNUSED_LED)
    {
        result = "0";
    }
    else if (val == BASE_A)
    {
        result = "2";  
    }
    else if (val == FOLLOWER_A)
    {
        result = "3";         
    } 
    else if (val == BASE_B)
    {
        result = "4";  
    }
    else if (val == FOLLOWER_B)
    {
        result = "5";
    }  
    else if (val == BASE_C)
    {
        result = "6";
    }
    else if (val == FOLLOWER_C)
    {
        result = "7";
    }

    return (result);             
}
static void ShowLeds(void)
{
    unsigned int i = 0, j = 0;

    for (i = 0; i < LED_ROW; ++i)
    {
        for (j = 0; j < LED_ROW; ++j)
        {
            Serial.print("[");
            Serial.print(LedToInt(leds[i * LED_ROW + j]));
            Serial.print("] ");
        }
        Serial.println("");
    }
}
static void HandleFirstMove(int target)
{
/*  PrintMoves();*/
    ClearMoves();
    moves[size++] = target;
    FastLED.show();
}
static void ClearMoves()
{
    unsigned int i = 0;
    Serial.println("Start clean");

    for (i = 0; i < size; ++i)
    {
        Serial.println(moves[i], DEC);
        if ((leds[moves[i]] == FOLLOWER_A) || (leds[moves[i]] == FOLLOWER_B) || (leds[moves[i]] == FOLLOWER_C))
        {
            WriteToLed(moves[i], UNUSED_LED);
        }
    }
    size=0;
    Serial.println("End clean");

}
static CRGB BaseToFollower(CRGB b)
{
    CRGB f;

    if (b == BASE_A)
    {
        f = FOLLOWER_A;
    }
    else if (b == BASE_B)
    {
        f = FOLLOWER_B;
    }
    else
    {
        f = FOLLOWER_C;
    }

    return (f);
}
static void HandleNewMove(int target)
{
    if(0 == DisableLed(target))
    {
        Serial.println("Inside setting led");
        moves[size++] = target;
        WriteToLed(target, BaseToFollower(leds[moves[0]]));
    }
    PrintMoves();
    FastLED.show();
}
static int IsntEnd(void)
{
    int result = 0;
    unsigned int i = 0;

    if (size > 1 && (leds[moves[0]] == leds[moves[size - 1]]))
    {
        for (i = 1; i < size; ++i)
        {
            WriteToLed(moves[i], leds[moves[0]]);
        }
        size = 0;
        for (i = 0; i < bases_size; ++i)
        {
            if (bases[i] == leds[moves[0]])
            {
                bases[i] = NON_VALUE; break;
            }
        }
    }
    /*
    for (i = 0; i < LEDS_SIZE; ++i)
    {
        result += (leds[i] == UNUSED_LED) ? 1 : 0;
    }*/
    for (i = 0; i < bases_size; ++i)
    {
        result += ((bases[i] != NON_VALUE) ? 1 : 0);
    }
    return (!!result);
}
static int CheckInt(int id)
{
    int exit_code = 0;
    if (-1 != id)
    {
        unsigned int i = 0;
        for (i = 0; i < (bases_size); ++i)
        {
            if (leds[id] == bases[i])
            {
                exit_code = 1;
                i = bases_size;
            }
        }
    }

    return(exit_code);
}
static bool IsItClose(int a, int b)
{
    int result = 0;

    result += (a == b + 2) ? 1 : 0;
    result += (b == a + 2) ? 1 : 0;
    result += (a == LED_BELOW(LED_BELOW(b))) ? 1 : 0;
    result += (b == LED_BELOW(LED_BELOW(a))) ? 1 : 0;

    return (0 != result);
}
static int CheckPath(int id) /* [1] for used | [0] for free | [2] for base color | [3] for following color | [4] for another base color | [5] for following color | ... */
{
    int exit_code = -1;

    Serial.print("moves[size-1] = (");
    Serial.print(moves[size-1], DEC);
    Serial.println(")");


    if (size > 0 && IsItClose(moves[size-1], id))
    {
        exit_code = 1;
    }


    if ((size > 0 && moves[0] == id))
    {
        exit_code = -1;
    }

    if (size > 0 && moves[size-1] == id)
    {
        exit_code = 0;
    }
    else if (size > 1 && leds[id] == leds[moves[0]] && id != moves[0])
    {
        exit_code = -2;
    }

    Serial.print("CheckPath_exitCode = (");
    Serial.print(exit_code, DEC);
    Serial.println(")");

    return (exit_code);
}
static void InitHandlers(struct handler chain[HANDLERS_SIZE])
{

    chain[OPENNING_HANDLER]._check_func   = CheckInt;
    chain[TRAVELLING_HANDLER]._check_func = CheckPath;
}