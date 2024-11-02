# Arguments that can be passed to this test suite:
#   SEL == 0                :: standard SN76489 master clock divider /16
#   SEL == 1                :: old SN94624/SN76494  no clock divider
#   SEL == 2                ::                         clock divider /128
#
#   MASTER_CLOCK            :: custom master clock in Hz, default is 4_000_000
#   CHIP_INTERNAL_CLOCK_DIV :: custom clock divider, default is 16
#
# Examples running this script:
#   make                    :: run with default parameters
#   make SEL=1              :: run without clock divider, fastest!
#   make MASTER_CLOCK=3579545 :: run tests with chip clocked at NTSC frequency

# Useful helper functions to communicate with the chip under simulation
#   await reset(dut)
#   await set_volume(dut, channel=0, volume=15)
#   await set_tone(dut, channel=0, frequency=440)
#   await set_noise(dut, white=True, divider=512)
#   await write(dut, data=1111_0000)              # write data directly on the data bus of the chip, holds /WE low


import os
import cocotb
from cocotb.clock import Clock
from cocotb.triggers import RisingEdge, FallingEdge, Timer, ClockCycles

# MASTER_CLOCK = 3_579_545 # NTSC frequency of SN as used in Sega Master System,    0xFE = 440 Hz
# MASTER_CLOCK = 3_546_895 # PAL                 ---- // ----
MASTER_CLOCK = 4_000_000 # 4 MHz frequency of SN as used in BBC Micro,              0x11C = 440 Hz
CHIP_INTERNAL_CLOCK_DIV = 16


@cocotb.test()
async def test_silence(dut):
    await reset(dut)

    await set_silence(dut)
    await assert_output(dut, constant=True, period=16)
    assert get_output(dut) <= ZERO_VOLUME

    await done(dut)

@cocotb.test()
async def test_output_amplitudes(dut):
    await reset(dut)

    for chan in '123':
        dut._log.info(f"record output amplitudes from Channel {chan}")
        amplitudes = await record_amplitude_table(dut, chan)
        dut._log.info(f"output amplitudes are: {amplitudes}")

        # validate that volume increases with every step
        prev_volume = -1
        for step, vol in enumerate(amplitudes):
            assert vol > prev_volume or (prev_volume == vol and step < 4)
            prev_volume = vol

    await done(dut)

@cocotb.test()
async def test_tone_1(dut):
    await reset(dut)

    await set_silence(dut)
    await set_volume(dut, 0, 15)
    await set_tone(dut, 0, period=1)

    await assert_output(dut, period=1)

    await done(dut)

@cocotb.test()
async def test_tone_frequencies_on_all_channels(dut):
    await reset(dut)

    for chan in '123':
        await set_silence(dut)
        await set_volume(dut, chan, 15)
        for n in range(1, 8, 1):
            dut._log.info(f"test Tone {chan} with period {n}")
            await set_tone(dut, chan, period=n)
            await assert_output(dut, period=n)

    await done(dut)

@cocotb.test()
async def test_tone_440hz(dut):
    await reset(dut)

    await set_silence(dut)
    await set_volume(dut, 0, 15)
    await set_tone(dut, 0, frequency=440)

    await assert_output(dut, frequency=440)

    await done(dut)

@cocotb.test()
async def test_tone_max(dut):
    await reset(dut)

    await set_silence(dut)
    await set_volume(dut, 0, 15)
    await set_tone(dut, 0, period=0) # effectively acts like period 1024

    await assert_output(dut, period=1024)

    await done(dut)

@cocotb.test()
async def test_rapid_register_change_does_not_affect_frequency(dut):
    await reset(dut)

    dut._log.info("Start tone with the long period")
    await set_silence(dut)
    await set_volume(dut, 0, 15)
    await set_tone(dut, 0, period=32)
    
    dut._log.info("Set shortest tone, should be ignored until long period finishes")
    await ClockCycles(dut.clk, CHIP_INTERNAL_CLOCK_DIV * 2)
    await set_tone(dut, 0, period=1) # this tone setting should be ignored until the whole wave cycle with long period finishes

    period_longer_than_1 = 16   # expect period higher than 1, but somewhat shorter than the long period
                                # some time already have passed from the start of the tone with the long period
    await assert_output(dut, period=period_longer_than_1, constant=True)

    await done(dut)

@cocotb.test()
async def test_tone_change_while_another_tone_is_playing(dut):
    await reset(dut)

    long_period = 32
    dut._log.info("Start tone with the long period")
    await set_silence(dut)
    await set_volume(dut, 0, 15)
    await set_tone(dut, 0, period=long_period)
    
    dut._log.info("Almost immediatelly set the shortest tone")
    await ClockCycles(dut.clk, CHIP_INTERNAL_CLOCK_DIV * 2)
    await set_tone(dut, 0, period=1)

    dut._log.info("Wait for the long period to finish until short tone starts")
    await ClockCycles(dut.clk, long_period * 2 * CHIP_INTERNAL_CLOCK_DIV)

    await assert_output(dut, period=1)

    await done(dut)

PERIODIC_NOISE_FREQUENCY_DIVISION_FACTOR = 15   # in periodic mode LFSR register has 1 of out 15 bits set and rotated
WHITE_NOISE_FREQUENCY_DIVISION_FACTOR = 8       # empirically found this factor, need to validate!

@cocotb.test()
async def test_periodic_noise_via_tone3(dut):
    await reset(dut)

    await set_silence(dut)
    await set_volume(dut, 'noise', 15)
    await set_tone(dut, "3", period=1)
    await set_noise_via_tone3(dut, white=False) # periodic noise
    await assert_output(dut, period=1*PERIODIC_NOISE_FREQUENCY_DIVISION_FACTOR, noise=True)

    await done(dut)

@cocotb.test()
async def test_white_noise_via_tone3(dut):
    await reset(dut)

    await set_silence(dut)
    await set_volume(dut, 'noise', 15)
    await set_tone(dut, "3", period=1)
    await set_noise_via_tone3(dut, white=True) # white noise
    await assert_output(dut, period=1*WHITE_NOISE_FREQUENCY_DIVISION_FACTOR, noise=True)

    await done(dut)

@cocotb.test()  
async def test_periodic_noise_frequencies_via_tone3(dut):
    await reset(dut)

    await set_silence(dut)
    await set_volume(dut, 'noise', 15)
    for n in range(2, 8, 1):
        dut._log.info(f"test 'periodic' noise with period {n} set via Channel 3")
        await set_tone(dut, "3", period=n)
        await set_noise_via_tone3(dut, white=False) # restarts noise
        await assert_output(dut, period=n*PERIODIC_NOISE_FREQUENCY_DIVISION_FACTOR, noise=True)

    await done(dut)

@cocotb.test()
async def test_white_noise_frequencies_via_tone3(dut):
    await reset(dut)

    await set_silence(dut)
    await set_volume(dut, 'noise', 15)
    for n in range(2, 8, 1):
        dut._log.info(f"test 'white' noise with period {n} set via Channel 3")
        await set_tone(dut, "3", period=n)
        await set_noise_via_tone3(dut, white=True) # restarts noise
        await assert_output(dut, period=n*WHITE_NOISE_FREQUENCY_DIVISION_FACTOR, noise=True)

    await done(dut)

@cocotb.test()
async def test_periodic_noise_via_divider(dut):
    await reset(dut)

    await set_silence(dut)
    await set_volume(dut, 'noise', 15)
    for n in [16, 32, 64]:
        dut._log.info(f"test 'periodic' noise with divider {n}")
        await set_noise(dut, period=n, white=False) # periodic noise
        await assert_output(dut, period=n*PERIODIC_NOISE_FREQUENCY_DIVISION_FACTOR, noise=True)

    await done(dut)

@cocotb.test()
async def test_white_noise_via_divider(dut):
    await reset(dut)

    await set_silence(dut)
    await set_volume(dut, 'noise', 15)
    for n in [16, 32, 64]:
        dut._log.info(f"test 'white' noise with divider {n}")
        await set_noise(dut, period=n, white=True) # white noise
        await assert_output(dut, period=n*WHITE_NOISE_FREQUENCY_DIVISION_FACTOR, noise=True)

    await done(dut)

@cocotb.test()
async def test_master_output_is_clamped_at_the_top(dut):
    await reset(dut)

    for chan in '123':
        await set_tone(dut, chan, period=1)
    for chan in '1234':
        await set_volume(dut, chan, 15)    
    await set_noise_via_tone3(dut, white=False) # reset noise
    await ClockCycles(dut.clk, CHIP_INTERNAL_CLOCK_DIV * 2 * (PERIODIC_NOISE_FREQUENCY_DIVISION_FACTOR - 2))
    await ClockCycles(dut.clk, CHIP_INTERNAL_CLOCK_DIV)
    await ClockCycles(dut.clk, 2)

    master_0 = get_output(dut)
    try: # can not be run in Gate Level tests
        phase_0 = \
            internal.tone[0].gen.out == 1 and \
            internal.tone[1].gen.out == 1 and \
            internal.tone[2].gen.out == 1 and \
            internal.noise[0].gen.out == 1
    except:
        phase_0 = True

    await ClockCycles(dut.clk, CHIP_INTERNAL_CLOCK_DIV)

    master_1 = get_output(dut)
    try: # can not be run in Gate Level tests
        phase_1 = \
            internal.tone[0].gen.out == 1 and \
            internal.tone[1].gen.out == 1 and \
            internal.tone[2].gen.out == 1 and \
            internal.noise[0].gen.out == 1
    except:
        phase_1 = False

    assert phase_0 ^ phase_1
    assert (master_0 >= MAX_MASTER_VOLUME or master_1 >= MAX_MASTER_VOLUME)

    await done(dut)


# @cocotb.test()
# async def test_noise_restarts(dut):
#     await reset(dut)

#     await done(dut)


# @cocotb.test()
async def test_psg(dut):

    dut._log.info("start")
    clock = Clock(dut.clk, 10, units="us")
    cocotb.start_soon(clock.start())

    dut._log.info("reset")
    dut.rst_n.value = 0
    await ClockCycles(dut.clk, 10)
    dut.rst_n.value = 1

    print_chip_state(dut)

    dut._log.info("init")
    for val in [
        # attenuation
        0b1_00_1_1110,  # channel 0
        0b1_01_1_1111,  # channel 1
        0b1_10_1_1111,  # channel 2
        0b1_11_1_1110,  # channel 3
        # frequency
        0b1_00_0_0001,  # tone 0
        0b1_01_0_0001,  # tone 1
        0b1_10_0_0001,  # tone 2
        # noise
        0b1_11_0_0111,  # noise 0
    ]:
        dut.ui_in.value = val
        await ClockCycles(dut.clk, 1)    
    print_chip_state(dut)

    dut._log.info("warmup 4 cycles")
    await ClockCycles(dut.clk, 1)
    print_chip_state(dut)
    await ClockCycles(dut.clk, 1)
    print_chip_state(dut)
    await ClockCycles(dut.clk, 1)
    print_chip_state(dut)
    await ClockCycles(dut.clk, 1)
    print_chip_state(dut)
    
    dut._log.info("warmup 1018 cycles")
    await ClockCycles(dut.clk, 0x400-6)
    print_chip_state(dut)
    
    dut._log.info("warmup last 2 cycles")
    await ClockCycles(dut.clk, 1)
    print_chip_state(dut)
    await ClockCycles(dut.clk, 1)
    print_chip_state(dut)

    dut._log.info("test freq 1")
    dut.ui_in.value = 0b1_00_0_0001     # tone 0 <- 1
    for i in range(8):
        print_chip_state(dut)
        await ClockCycles(dut.clk, 1)

    dut._log.info("test freq 0")
    dut.ui_in.value = 0b1_00_0_0000     # tone 0 <- 0
    for i in range(16):
        print_chip_state(dut)
        await ClockCycles(dut.clk, 1)

    dut._log.info("clock x64 speedup")
    for i in range(32):
        print_chip_state(dut)
        await ClockCycles(dut.clk, 64)

    dut._log.info("done")


### UTILS #####################################################################

SEL = 1
SEL = os.environ.get("SEL", SEL)

if SEL == 1 or SEL == "1" or SEL == "01":
    MASTER_CLOCK = 250_000
    CHIP_INTERNAL_CLOCK_DIV = 1
elif SEL == 2 or SEL == "2" or SEL == "10":
    MASTER_CLOCK = 32_000_000
    CHIP_INTERNAL_CLOCK_DIV = 128

if SEL == 0 or SEL == "":
    try:
        MASTER_CLOCK = int(os.environ.get("MASTER_CLOCK", MASTER_CLOCK))
    except:
        if os.environ.get("MASTER_CLOCK", "") == "NTSC":
            MASTER_CLOCK = 3_579_545
        pass
    try:
        CHIP_INTERNAL_CLOCK_DIV = int(os.environ.get("CHIP_INTERNAL_CLOCK_DIV", CHIP_INTERNAL_CLOCK_DIV))
    except:
        pass

ZERO_VOLUME = 2 # int(0.2 * 256) # SN might be outputing low constant DC as silence instead of complete 0V
MAX_MASTER_VOLUME = 255
MAX_CHANNEL_VOLUME = MAX_MASTER_VOLUME/4

def print_chip_state(dut):
    try:
        internal = dut.tt_um_rejunity_sn76489_uut
        print(
            "W" if dut.uio_in.value & 1 == 0 else " ",
            dut.ui_in.value, ">||",
            '{:1d}'.format(int(internal.latch_control_reg.value)), "!",
            '{:4d}'.format(int(internal.tone[0].gen.compare.value)),
            '{:4d}'.format(int(internal.tone[0].gen.counter.value)),
                        "|#|" if internal.tone[0].gen.out == 1 else "|-|", # "|",
            '{:4d}'.format(int(internal.tone[1].gen.compare.value)),
            '{:4d}'.format(int(internal.tone[1].gen.counter.value)),
                        "|#|" if internal.tone[1].gen.out == 1 else "|-|",  #"|",
            '{:4d}'.format(int(internal.tone[2].gen.compare.value)),
            '{:4d}'.format(int(internal.tone[2].gen.counter.value)),
                        "|#|" if internal.tone[2].gen.out == 1 else "|-|",  #"!",
            "R" if internal.noise[0].gen.reset_lfsr == 1 else " ",
            "w" if internal.noise[0].gen.is_white_noise == 1 else "p",
            ["16", "32", "64", "T3"][internal.noise[0].gen.control.value & 3],
            '{:3d}'.format(int(internal.noise[0].gen.counter)),
            internal.noise[0].gen.trigger.value,
            ">" if internal.noise[0].gen.trigger_edge == 1 else " ",
            internal.noise[0].gen.lfsr.value, ">>",
            '{:3d}'.format(int(dut.uo_out.value >> 1)),
                        "@" if dut.uo_out[0].value == 1 else ".")
    except:
       print(dut.ui_in.value, ">", dut.uo_out.value)

# 0b1111_1111
INPUT_ON_RESET          = 0
BIDIRECTIONAL_ON_RESET  = 0b1111_1111 # Emulate pull-ups on BIDIRECTIONAL pins
if CHIP_INTERNAL_CLOCK_DIV == 128:
    WRITE_ENABLED  = 0b11111_10_0 # SEL = 2 :: clock div 128 ; /WE = 0 :: writes enabled
    WRITE_DISABLED = 0b11111_10_1 # SEL = 2 :: clock div 128 ; /WE = 1 :: writes disabled
elif CHIP_INTERNAL_CLOCK_DIV == 1:
    WRITE_ENABLED  = 0b11111_01_0 # SEL = 1 :: no clock div ; /WE = 0 :: writes enabled
    WRITE_DISABLED = 0b11111_01_1 # SEL = 1 :: no clock div ; /WE = 1 :: writes disabled
else:
    WRITE_ENABLED  = 0 # /WE = 0, writes enabled
    WRITE_DISABLED = 1 # /WE = 1, writes disabled


CMD_FREQUENCY  = 0b1000_0000
CMD_NOISE      = 0b1110_0000
CMD_ATTENUATOR = 0b1001_0000

async def reset(dut):
    master_clock = MASTER_CLOCK
    cycle_in_nanoseconds = 1e9 // master_clock
    dut._log.info(f"start @{MASTER_CLOCK/1e+6}Mhz, /{CHIP_INTERNAL_CLOCK_DIV}, cycle length {cycle_in_nanoseconds}ns");
    clock = Clock(dut.clk, cycle_in_nanoseconds, units="ns")
    cocotb.start_soon(clock.start())

    dut.ui_in.value =   INPUT_ON_RESET
    dut.uio_in.value =  BIDIRECTIONAL_ON_RESET 

    dut._log.info("reset")
    dut.rst_n.value = 0
    await ClockCycles(dut.clk, 10)
    dut.rst_n.value = 1

    dut.rst_n.value = 1    

async def done(dut):
    dut._log.info("DONE!")

def get_output(dut):
    return int(dut.uo_out.value)

async def get_max_output(dut, period=1):
    if period == 0:
        period = 1024
    max_val = -1
    for n in range(period * 2):
        await ClockCycles(dut.clk, CHIP_INTERNAL_CLOCK_DIV)
        max_val = max(max_val, get_output(dut))
    return max_val

async def record_amplitude_table(dut, channel):
    channel = channel_index(channel)
    assert channel != 3 # can't record amplitude from Noise channel right now 
    await set_silence(dut)
    await set_tone(dut, 0, period=1)
    amplitudes = []
    for vol in range(16):
        dut.uio_in.value = WRITE_ENABLED
        dut.ui_in.value = CMD_ATTENUATOR | (channel << 5) | (15 - vol)
        amplitudes.append(await get_max_output(dut))
    await set_silence(dut)
    return amplitudes

def channel_index(channel):
    if channel == '1' or channel == 'A' or channel == 'a':
        channel = 0
    elif channel == '2' or channel == 'B' or channel == 'b':
        channel = 1
    elif channel == '3' or channel == 'C' or channel == 'c':
        channel = 2
    elif channel == '4' or channel == 'N' or channel == 'noise':
        channel = 3
    assert 0 <= channel and channel <= 3
    return channel


async def write(dut, data):
    dut.uio_in.value = WRITE_ENABLED
    dut.ui_in.value = data
    await ClockCycles(dut.clk, 1)
    print_chip_state(dut)

async def flush(dut):
    dut.uio_in.value = WRITE_DISABLED
    await ClockCycles(dut.clk, 1)
    print_chip_state(dut)

async def set_tone(dut, channel, frequency=-1, period=-1):
    channel = channel_index(channel)
    if frequency > 0:
        period = MASTER_CLOCK // (CHIP_INTERNAL_CLOCK_DIV * 2 * frequency)
    assert 0 <= channel and channel <= 3
    assert 0 <= period and period <= 1023
    if CHIP_INTERNAL_CLOCK_DIV == 1:
        # never set frequency to 0 when chip is running without a clock divider
        # when chip has no clock divider, the internal counter will starts counting down immediately
        # and wrap around to 0x3ff period!
        await write(dut, CMD_FREQUENCY | (channel << 5) | ((period | 1) & 15))
        await write(dut, period >> 4)
        await write(dut, CMD_FREQUENCY | (channel << 5) | (period & 15))
    else:
        await write(dut, CMD_FREQUENCY | (channel << 5) | (period & 15))
        await write(dut, period >> 4)
    await flush(dut)

async def set_noise_via_tone3(dut, white=True):
    white = 1 if white else 0
    await write(dut, CMD_NOISE | (white << 2) | 0b11)
    await flush(dut)

async def set_noise(dut, white=True, frequency=-1, period=-1, divider=-1):
    white = 1 if white else 0
    if frequency > 0:
        period = MASTER_CLOCK // (CHIP_INTERNAL_CLOCK_DIV * 2 * frequency)
    if period == 0:
        period = 1
    noise_control = -1
    if divider == 0 or divider == 16 * CHIP_INTERNAL_CLOCK_DIV * 2 or period == 16:
        noise_control = 0
    elif divider == 1 or divider == 32 * CHIP_INTERNAL_CLOCK_DIV * 2 or period == 32:
        noise_control = 1
    elif divider == 2 or divider == 64 * CHIP_INTERNAL_CLOCK_DIV * 2 or period == 64:
        noise_control = 2
    assert 0 <= noise_control and noise_control < 3
    await write(dut, CMD_NOISE | (white << 2) | noise_control)
    await flush(dut)

async def set_silence(dut):
    for ch in range(4):
        await set_volume(dut, ch, 0)

async def set_volume(dut, channel, vol=0):
    channel = channel_index(channel)
    assert 0 <= channel and channel <= 3
    assert 0 <= vol     and vol <= 15
    print(channel, vol)
    await write(dut, CMD_ATTENUATOR | (channel << 5) | (15 - vol))
    await flush(dut)

async def assert_output(dut, frequency=-1, period=-1, constant=False, noise=False, v0 = ZERO_VOLUME, v1 = MAX_CHANNEL_VOLUME):
    if frequency > 0:
        period = MASTER_CLOCK // (CHIP_INTERNAL_CLOCK_DIV * 2 * frequency)
    if period == 0:
        period = 1
    assert 0 < period and period <= 1024
    cycles_to_collect_data = int(period * CHIP_INTERNAL_CLOCK_DIV)
    if constant:
        max_error = 0
        pulses_to_collect = 0
    else:
        max_error = 0.15 if noise else 0.01
        pulses_to_collect = 16 if noise else 2
        cycles_to_collect_data *= pulses_to_collect * 2

    mid_volume = (v0 + v1) // 2
    state_changes = 0
    clocks_to_step = CHIP_INTERNAL_CLOCK_DIV//2 if CHIP_INTERNAL_CLOCK_DIV >= 2 and CHIP_INTERNAL_CLOCK_DIV%2 == 0 else 1
    for i in range(cycles_to_collect_data//clocks_to_step):
        last_state = get_output(dut) > mid_volume
        await ClockCycles(dut.clk, clocks_to_step)
        # print_chip_state(dut)
        new_state = get_output(dut) > mid_volume
        if last_state != new_state:
            state_changes += 1

    time_passed_to_collect_data = cycles_to_collect_data / MASTER_CLOCK
    measured_frequency = (state_changes / 2) / time_passed_to_collect_data
    frequency = MASTER_CLOCK / (CHIP_INTERNAL_CLOCK_DIV * 2 * period)

    if not constant:
        noise = "noisie" if noise else ""
        if frequency > 1000:
            dut._log.info(f"expected {noise} frequency {frequency/1000:4.3f} KHz and measured {measured_frequency/1000:4.3f} KHz")
        else:
            dut._log.info(f"expected {noise} frequency {frequency:3.2f} Hz and measured {measured_frequency:3.2f} Hz")
        assert frequency * (1.0-max_error) <= measured_frequency and measured_frequency <= frequency * (1.0+max_error)

    pulses_to_collect2 = pulses_to_collect*2
    assert pulses_to_collect2 * (1.0-max_error) <= state_changes and state_changes <= pulses_to_collect2 * (1.0+max_error)
