<!---

This file is used to generate your project datasheet. Please fill in the information below and delete any unused
sections.

You can also include images in this folder and reference them in the markdown. Each image must be less than
512 kb in size, and the combined size of all images must be less than 1 MB.
-->

## How it works

This Verilog implementation is a replica of the classical **[SN76489](https://en.wikipedia.org/wiki/Texas_Instruments_SN76489)** programmable sound generator.
With roughly a 1400 logic gates this design fits on a **single tile** of the TinyTapeout.

**The goals of this project**

1. closely replicate the behavior and eventually the complete **design of the original** SN76489
2. provide a readable and well documented code for educational and hardware **preservation** purposes
3. leverage the **modern fabrication** process

A significant effort was put into a thorough **test suite** for regression testing and validation against the original chip behavior.

**The future work**

The next step is to incorporate analog elements into the design to match the original SN76489 - DAC for each channel and an analog OpAmp for channel summation.

**Chip technical capabilities**

- **3 square wave** tone generators
- **1 noise** generator
- 2 types of noise: *white* and *periodic*
- Capable to produce a range of waves typically from **122 Hz** to **125 kHz**, defined by **10-bit** registers.
- **16** different volume levels

___Registers___ The behavior of the SN76489 is defined by 8 "registers" - 4 x 4 bit volume registers, 3 x 10 bit tone registers and 1 x 3 bit noise configuration register.

| Channel | Volume registers       | Tone & noise registers   |
|---------|------------------------|--------------------------|
| 0       | Channel #0 attenuation | Tone #0 frequency        |
| 1       | Channel #1 attenuation | Tone #1 frequency        |
| 2       | Channel #2 attenuation | Tone #2 frequency        |
| 3       | Channel #3 attenuation | Noise type and frequency |

___Square wave tone generators___ Square waves are produced by counting down the 10-bit counters. Each time the counter reaches the 0 it is reloaded with the corresponding value from the configuration register and
the output bit of the channel is flipped producing square waves.


___Noise generator___ Noise is produced with 15-bit [Linear-feedback Shift Register (LFSR)](https://en.wikipedia.org/wiki/Linear-feedback_shift_register) that flips the output bit pseudo randomly.
The shift rate of the LFSR register is controller either by one of the 3 hardcoded power-of-two dividers or output from the channel #2 tone generator is used.


___Attenuation___ Each of the four SN76489 channels have dedicated attenuation modules. The SN76489 has 16 steps of attenuation, each step is 2 dB and maximum possible attenuation is 28 dB.
Note that the attenuation definition is the opposite of volume / loudness. Attenuation of 0 means maximum volume.

Finally, all the 4 attenuated signals are summed up and are sent to the output pin of the chip.

**Historical use of the SN76489**

The SN76489 family of programmable sound generators was introduced by Texas Instruments in 1980. Variants of the SN76489 were used in a number of home computers, game consoles and arcade boards:

- home computers: [TI-99/4](https://en.wikipedia.org/wiki/TI-99/4A), [BBC Micro](https://en.wikipedia.org/wiki/BBC_Micro), [IBM PCjr](https://en.wikipedia.org/wiki/IBM_PCjr), [Sega SC-3000](https://en.wikipedia.org/wiki/SG-1000#SC-3000), [Tandy 1000](https://en.wikipedia.org/wiki/Tandy_1000)
- game consoles: [ColecoVision](https://en.wikipedia.org/wiki/ColecoVision), [Sega SG-1000](https://en.wikipedia.org/wiki/SG-1000), [Sega Master System](https://en.wikipedia.org/wiki/Master_System), [Game Gear](https://en.wikipedia.org/wiki/Game_Gear), [Neo Geo Pocket](https://en.wikipedia.org/wiki/Neo_Geo_Pocket) and [Sega Genesis](https://en.wikipedia.org/wiki/Sega_Genesis)
- arcade machines by Sega & Konami and would usually include 2 or 4 SN76489 chips

The SN76489 chip family competed with the similar [General Instrument AY-3-8910](https://en.wikipedia.org/wiki/General_Instrument_AY-3-8910).

**The original pinout of the SN76489AN**

```
               ,--._.--.
        D5  -->|1    16|<-- VCC
        D6  -->|2    15|<-- D4
        D7  -->|3    14|<-- CLOCK
     ready* <--|4    13|<-- D3
       /WE  -->|5    12|<-- D2
       /ce* -->|6    11|<-- D1
  AUDIO OUT <--|7    10|<-- D0
        GND ---|8     9|    not connected*
               `-------'
        * -- omitted from this Verilog implementation

```

**Difference from the original hardware**

This Verilog implementation is a completely digital and synchronous design that differs from the original SN76489 design which incorporated analog parts.

___Audio signal output___ While the original chip had integrated OpAmp to sum generated channels in analog fashion, this implementation does digital signal summation and digital output.
The module provides two alternative outputs for the generated audio signal:

1. digital 8-bit audio output suitable for external Digital to Analog Converter (DAC)
2. pseudo analog output through Pulse Width Modulation (PWM)

___Separate 4 channel output___ Outputs of all 4 channels are exposed along with the master output. This allows to validate and mix signals externally.
In contrast the original chip was limited to a single audio output pin due to the PDIP-16 package.

___No DC offset___ This implementation produces output 0/1 waveforms without DC offset.

___No /CE and READY pins___ Chip enable control pin **/CE** is omitted in this design for simplicity. The behavior is the same as if **/CE** is tied *low* and the chip is considered always enabled.

Unlike the original SN76489 which took 32 cycles to update registers, this implementation handles register writes in a single cycle and chip behaves as always **READY**.

___Synchronous reset and single phase clock___ The original design employed 2 phases of the clock for the operation of the registers. The original chip had no reset pin and would wake up to a random state.

To make it easier to synthesize and test on FPGAs this implementation uses single clock phase and synchronous reset for registers.

___A configurable clock divider___ was introduced in this implementation.

1. the original SN76489 with the master clock internally divided by 16. This classical chip was intended for PAL and NTSC frequencies. However in [BBC Micro](https://en.wikipedia.org/wiki/BBC_Micro) 4 MHz clock was employed.
2. SN94624/SN76494 variants without internal clock divider. These chips were intended for use with 250 to 500 KHz clocks.
3. high frequency clock configuration for TinyTapeout, suitable for a range between 25 MHz and 50 Mhz. In this configuration the master clock is internally divided by 128.


**The reverse engineered SN76489**

This implementation is based on the results from these reverse engineering efforts:

1. [Annotations and analysis](https://github.com/gchiasso/76489A-analysis) of a decapped SN76489A chip.
2. Reverse engineered [schematics](https://github.com/emu-russia/SEGAChips/tree/main/VDP/PSG) based on a decapped VDP chip from Sega Mega Drive which included a SN76496 variant.


## How to test

**Summary of commands to communicate with the chip**

The SN76489 is programmed by updating its internal registers via the data bus. Below is a short summary of the communication protocol of SN76489. Please consult [SN76489 Technical Manual](https://github.com/rejunity/tt05-psg-sn76489/blob/main/docs/SN76489AN_Manual.pdf) for more information.


| Command    | Description                     | Parameters                                    |
|------------|---------------------------------|-----------------------------------------------|
| `1cc0ffff` | Set tone fine frequency         | `f` - 4 low bits, `c` - channel #             |
| `00ffffff` | Follow up with coarse frequency | `f` - 6 high bits                             |      
| `11100bff` | Set noise type and frequency    | `b` - white/periodic, `f` - frequency control |
| `1cc1aaaa` | Set channel attenuation         | `a` - 4 bit attenuation, `c` - channel #      |

| NF1 | NF0 | Noise frequency control       |
|-----|-----|-------------------------------|
| 0   |   0 | Clock divided by 512          |
| 0   |   1 | Clock divided by 1024         |
| 1   |   0 | Clock divided by 2048         |
| 1   |   1 | Use channel #2 tone frequency |

___Write to SN76489___ Hold **/WE** low once data bus pins are set to the desired values.
Pull **/WE** high before setting different value on the data bus.

**Note frequency**

Use the following formula to calculate the 10-bit period value for a particular note :

$$ tone period_{cycles} = clock_{frequency} / (32_{cycles} * note_{frequency}) $$

For example 10-bit value that plays 440 Hz note on a chip clocked at 4 MHz would be:

$$ tone   period_{cycles} = 4000000 Hz / (32_{cycles} * 440 Hz) = 284 = 11C_{hex} $$ 

**An example to play a note accompanied with a lower volume noise**

| /WE |D7| D6/5 | D4..D0 | Explanation |
|-----|---|----|-------|--------------------------------------------------|
| 0   |`1`|`00`|`01100`| Set **channel #0** tone low 4-bits to $C_{hex} = 1100_{bin}$ |
| 0   |`0`|`00`|`10001`| Set **channel #0** tone high 6-bits to $11_{hex} = 010001_{bin}$ |
| 0   |`1`|`00`|`10000`| Set **channel #0** volume to **100%**, attenuation 4-bits are $0_{dec} = 0000_{bin}$ |
| 0   |`1`|`11`|`00100`| Set **channel #3** noise type to **white** and divider to **512** |
| 0   |`1`|`11`|`11000`| Set **channel #3** noise volume to **50%**, attenuation 4-bits are $8_{dec} = 1000_{bin}$ |



```
Timing diagram


CLK   ____      ____      ____      ____      ____      ____         
   __/    `____/    `____/    `____/    `____/    `____/    `___ ...
     |        |         |         |         |         |
     |        |         |         |         |         |

/WE _       __        __        __        __        _______
     `_____/  `______/  `______/  `______/  `______/   *
                                                       ^
D7..D0_______  ________  ________  ________  ________  |
   _/10001100  00010001  10010000  11100100  11111000`_|______
      chan#0    chan#0    chan#0    chan#3    chan#3   |
    tone=h??C   =h11C    atten=0    div=16    atten=8  |
      h011C = 440 Hz              /16 = ~1 Khz         |
                                 white noise           |
                                                       |
                                                 noise restarts
                                            after /WE goes high and
                                     there was a write to noise register

```

**Configurable clock divider**

Clock divider can be controlled through **SEL0** and **SEL1** control pins and allows to select between 3 chip variants.

| SEL1 | SEL0 | Description                        | Clock frequency|
|------|------|------------------------------------|----------------|
| 0    |    0 | SN76489 mode, clock divided by 16  | 3.5 .. 4.2 MHz |
| 1    |    1 |           -----//-----             | 3.5 .. 4.2 MHz |
| 0    |    1 | SN76494 mode, no clock divider     | 250 .. 500 kHZ |
| 1    |    0 | New mode for TT05, clock div. 128  |  25 .. 50  MHz |


| SEL1 | SEL0 | Formula to calculate the 10-bit tone period value for a note |
|------|------|--------------------------------------------------------------|
| 0    |    0 | $clock_{frequency} / (32_{cycles} * note_{frequency})$       |
| 1    |    1 | -----//-----                                                 |
| 0    |    1 | $clock_{frequency} / (2_{cycles} * note_{frequency})$        |
| 1    |    0 | $clock_{frequency} / (256_{cycles} * note_{frequency})$      |


**Some examples of music recorded from the chip simulation**

- [https://www.youtube.com/watch?v=ghBGasckpSY](Crazee Rider BBC Micro game)
- [https://www.youtube.com/watch?v=HXLAdA02I-w](MISSION76496 tune for Sega Master System)


## External hardware

DAC (for ex. Digilent R2R PMOD), RC filter, amplifier, speaker.

The data bus of the SN76489 chip has to be connected to microcontroller and receive a regular stream of commands.
The SN76489 produces audio output and has to be connected to a speaker. There are several ways how the overall schematics can be established.

___8-bit parallel output via DAC___ One option is to connect off the shelf data parallel Digital to Analog Converter (DAC)
for example [Digilent R2R Pmod](https://digilent.com/reference/pmod/pmodr2r/start) to the output pins and
route the resulting analog audio to piezo speaker or amplifier.

```
uController              SN76489
,---------.            ,---._.---. 
|         |    4 Mhz ->|CLK  SEL0|<-- 0
|    GPIOx|----------->|D0   SEL1|<-- 0
|    GPIOx|----------->|D1       |         ,----------.
|    GPIOx|----------->|D2   OUT0|-------->|LSB       |
|    GPIOx|----------->|D3   OUT1|-------->|          |  
|    GPIOx|----------->|D4   OUT2|-------->|   pDAC   |  Headphones
|    GPIOx|----------->|D5   OUT3|-------->|    or    |      or    
|    GPIOx|----------->|D6   OUT4|-------->| RESISTOR |    Buzzer    
|    GPIOx|----------->|D7   OUT5|-------->|  ladder  |         /|
|    GPIOx|----------->|/WE  OUT6|-------->|          |     .--/ |
`---------'            |     OUT7|-------->|MSB       |-----|    |
                       `---------'         `----------'     `--` |
                                                             |  `|
                                                             |
                                                        GND ---  
```

___AUDIO OUT through RC filter___ Another option is to use the Pulse Width Modulated (PWM) AUDIO OUT pin that combines 4 channels with the Resistor-Capacitor based low-pass filter or better the Operation Amplifier (Op-amp) & Capacitor based integrator:

```
uController              SN76489
,---------.            ,---._.---. 
|         |    4 Mhz ->|CLK  SEL0|<-- 0
|    GPIOx|----------->|D0   SEL1|<-- 0
|    GPIOx|----------->|D1       |
|    GPIOx|----------->|D2       |
|    GPIOx|----------->|D3       |          C1
|    GPIOx|----------->|D4       |     ,----||----.
|    GPIOx|----------->|D5       |     |          | 
|    GPIOx|----------->|D6       |     |  Op-amp  |        Speaker     
|    GPIOx|----------->|D7  AUDIO|     |   |X     |            /|
|    GPIOx|----------->|/WE  OUT |-----+---|-X    |   C2   .--/ |
`---------'            `---------'         |  }---+---||---|    |
                                        ,--|+/             `--` |
                                        |  |/               |  `|
                                        |                   |
                                   GND ---             GND ---  
```

___Separate channels through the Op-amp___ The third option is to externally combine 4 channels with the Operational Amplifier and low-pass filter:

```
uController              SN76489
,---------.            ,---._.---. 
|         |    4 Mhz ->|CLK  SEL0|<-- 0
|    GPIOx|----------->|D0   SEL1|<-- 0
|    GPIOx|----------->|D1       |
|    GPIOx|----------->|D2       |
|    GPIOx|----------->|D3       |           C1
|    GPIOx|----------->|D4       |      ,----||----.
|    GPIOx|----------->|D5  chan0|---.  |          | 
|    GPIOx|----------->|D6  chan1|---+  |  Op-amp  |        Speaker
|    GPIOx|----------->|D7  chan2|---+  |   |X     |            /|
|    GPIOx|----------->|/WE chan3|---+--+---|-X    |   C2   .--/ |
`---------'            `---------'          |  }---+---||---|    |
                                         ,--|+/             `--` |
                                         |  |/               |  `|
                                         |                   |
                                    GND ---             GND ---  
```

