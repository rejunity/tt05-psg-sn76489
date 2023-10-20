import cocotb
from cocotb.clock import Clock
from cocotb.triggers import RisingEdge, FallingEdge, Timer, ClockCycles

MASTER_CLOCK = 4_000_000 # 4 MHz frequency of SN as used in BBC Micro,          0x11C = 440 Hz
# MASTER_CLOCK = 3_579_545 # PAL frequency of SN as used in Sega Master System,  0xFE = 440 Hz
CHIP_INTERNAL_CLOCK_DIV = 16

ZERO_VOLUME = 2 # int(0.2 * 256) # SN might be outputing low constant DC as silence instead of complete 0V
MAX_VOLUME = 255/4

def print_chip_state(dut):
    # try:
        internal = dut.tt_um_rejunity_sn76489_uut
        print(
            "W" if dut.uio_in.value == 0 else " ",
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
            internal.noise[0].gen.control.value,
            internal.noise[0].gen.reset_lfsr.value,
            '{:4d}'.format(int(internal.noise[0].gen.tone.compare.value)),
            '{:4d}'.format(int(internal.noise[0].gen.tone.counter.value)),
                        ">" if internal.noise[0].gen.tone.out == 1 else " ",
            internal.noise[0].gen.lfsr.value, ">>",
            '{:3d}'.format(int(dut.uo_out.value >> 1)),
                        "@" if dut.uo_out[0].value == 1 else ".")
    # except:
    #    print(dut.ui_in.value, ">", dut.uo_out.value)


async def reset(dut):
    master_clock = MASTER_CLOCK # // 16
    cycle_in_nanoseconds = 1e9 // master_clock # 1 / 4Mhz / nanosecond
    dut._log.info("start")
    clock = Clock(dut.clk, cycle_in_nanoseconds, units="ns")
    cocotb.start_soon(clock.start())

    dut.ui_in.value =           0
    dut.uio_in.value =          0b1111_1111 # Emulate pull-ups on BIDIRECTIONAL pins

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
        dut.uio_in.value = 0                        # /WE = 0, writes enabled
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
    dut.uio_in.value = 0                            # /WE = 0, writes enabled
    dut.ui_in.value = data
    await ClockCycles(dut.clk, 1)
    print_chip_state(dut)

async def flush(dut):
    dut.uio_in.value = 1                            # /WE = 1, writes disabled
    await ClockCycles(dut.clk, 1)
    print_chip_state(dut)

CMD_FREQUENCY  = 0b1000_0000
CMD_ATTENUATOR = 0b1001_0000

async def set_tone(dut, channel, frequency=-1, period=-1):
    channel = channel_index(channel)
    if frequency > 0:
        period = MASTER_CLOCK // (CHIP_INTERNAL_CLOCK_DIV * 2 * frequency)
    assert 0 <= channel and channel <= 3
    assert 0 <= period and period <= 1023
    await write(dut, CMD_FREQUENCY | (channel << 5) | (period & 15))
    await write(dut, period >> 4)
    await flush(dut)

# async def set_noise(dut, frequency=-1, period=-1):
#     if frequency > 0:
#         period = MASTER_CLOCK // (CHIP_INTERNAL_CLOCK_DIV * 2 * frequency)
#     assert 0 <= period and period <= 31
#     await set_register(dut, 6, period & 31)                     # Noise: set period

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

async def assert_output(dut, frequency=-1, period=-1, constant=False, noise=False, v0 = ZERO_VOLUME, v1 = MAX_VOLUME):
    if frequency > 0:
        period = MASTER_CLOCK // (CHIP_INTERNAL_CLOCK_DIV * 2 * frequency)
        print ()
    if period == 0:
        period = 1
    if noise: # NOTE: noise effectively produces signal at half the frequency of the timer due to 50% probability that consecutive samples will be equal
        frequency=frequency/2
        period=period*2
    assert 0 < period and period <= 1023
    cycles_to_collect_data = int(period * CHIP_INTERNAL_CLOCK_DIV)
    if constant:
        max_error = 0
        pulses_to_collect = 0
    else:
        max_error = 0.15 if noise else 0.01
        pulses_to_collect = 64 if noise else 2
        cycles_to_collect_data *= pulses_to_collect * 2
    
    mid_volume = (v0 + v1) // 2
    state_changes = 0
    for i in range(cycles_to_collect_data//8):
        last_state = get_output(dut) > mid_volume
        await ClockCycles(dut.clk, 8)
        # print_chip_state(dut)
        new_state = get_output(dut) > mid_volume
        if last_state != new_state:
            state_changes += 1

    # print(period, cycles_to_collect_data, state_changes)

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


### TESTS

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

# @cocotb.test()
# async def test_tones_with_volume(dut):
#     await reset(dut)

#     await set_mixer(dut, tones_on='ABC')                        # Mixer: disable noises, enable all tones

#     for chan in 'ABC':
#         dut._log.info(f"Tone on Channel {chan}")
#         await set_volume(dut, chan, 15)                         # Channel A/B/C: set volume to max
#         await assert_output(dut, period=0)                      # default tone frequency after reset should be 0
        
#         dut._log.info("Silence")
#         await set_volume(dut, chan, 0)                          # Channel A/B/C: set volume to 0
#         await assert_constant_output(dut, 256)

#     await done(dut)

@cocotb.test()
async def test_tone(dut):
    await reset(dut)

    await set_silence(dut)
    await set_volume(dut, 0, 15)
    await set_tone(dut, 0, period=1)

    await assert_output(dut, period=1)

    await done(dut)

@cocotb.test()
async def test_tone_frequencies(dut):
    await reset(dut)

    for chan in '123':
        await set_silence(dut)
        await set_volume(dut, chan, 15)
        for n in range(1, 8, 1):
            dut._log.info(f"test Tone {chan} with period {n}")
            await set_tone(dut, chan, period=n)
            await assert_output(dut, period=n)

    await done(dut)

    # dut._log.info("test tone with the maximum period of 4095")
    # await set_tone(dut, 'A', period=4095)                       # Tone A: set period to max
    # await assert_output(dut, period=4095)



@cocotb.test()
async def test_tone_440hz(dut):
    await reset(dut)

    dut._log.info("silence all except Channel 1 with maximum volume")
    await set_silence(dut)
    await set_volume(dut, 0, 15)
    await set_tone(dut, 0, frequency=440)

    await assert_output(dut, frequency=440)

    await done(dut)


# @cocotb.test()
# async def test_tone_frequencies(dut):
#     await reset(dut)

#     dut._log.info("enable tone on Channel A with maximum volume")
#     await set_mixer(dut, tones_on='A')                          # Mixer: only Channel A tone is enabled
#     await set_volume(dut, 'A', 15)                              # Channel A: no envelope, set channel to maximum volume

#     dut._log.info("test tone with period 0 (default after reset)")
#     await assert_output(dut, period=0)                          # default tone frequency after reset should be 0

#     for n in range(0, 8, 1):
#         dut._log.info(f"test tone period {n}")
#         await set_tone(dut, 'A', period=n)                      # Tone A: set period to n
#         await assert_output(dut, period=n)

#     dut._log.info("test tone with the maximum period of 4095")
#     await set_tone(dut, 'A', period=4095)                       # Tone A: set period to max
#     await assert_output(dut, period=4095)

#     await done(dut)

# @cocotb.test()
# async def test_rapid_tone_frequency_change(dut):
#     await reset(dut)

#     dut._log.info("enable tone on Channel A with maximum volume")
#     await set_mixer(dut, tones_on='A')                          # Mixer: only Channel A tone is enabled
#     await set_volume(dut, 'A', 15)                              # Channel A: no envelope, set channel to maximum volume

#     dut._log.info("set tone with the maximum period of 4095")
#     await set_tone(dut, 'A', period=4095)                       # Tone A: set period to max

#     dut._log.info("wait just a bit, wait is much shorter than the current tone period")
#     await ClockCycles(dut.clk, 512)

#     dut._log.info("quickly change tone period to 255 by reseting coarse period to 0 and keeping fine period at 255")
#     await set_register(dut,  1, 0b0000_0000)                    # Tone A: set coarse period to 0, fine period is still 255
#     await assert_output(dut, period=255)

#     dut._log.info("wait just a bit, wait is much shorter than the current tone period")
#     await ClockCycles(dut.clk, 128)

#     for n in range(10, 0, -1):
#         dut._log.info(f"test tone period {n}")
#         await set_tone(dut, 'A', period=n)                      # Tone A: set period to n
#         await assert_output(dut, period=n)

#     await done(dut)

# @cocotb.test()
# async def test_noise_is_initialised_to_period_0_after_reset(dut):
#     await reset(dut)

#     dut._log.info("enable tone on Channel A with maximum volume")
#     await set_mixer(dut, noises_on='A')                         # Mixer: only noise on Channel A is enabled
#     await set_volume(dut, 'A', 15)                              # Channel A: no envelope, set channel to maximum volume

#     dut._log.info("test if noise period is 0 after reset")
#     await assert_output(dut, period=0, noise=True)

#     await done(dut)

# @cocotb.test()
# async def test_noise_frequencies(dut):
#     await reset(dut)

#     dut._log.info("enable noise on Channel A with maximum volume")
#     await set_mixer(dut, noises_on='A')                         # Mixer: only noise on Channel A is enabled
#     await set_volume(dut, 'A', 15)                              # Channel A: no envelope, set channel to maximum volume

#     for n in range(0, 8, 1):
#         dut._log.info(f"test noise period {n}")
#         await set_noise(dut,     period=n)                      # Noise: set period to n
#         await assert_output(dut, period=n, noise=True)

#     dut._log.info("test noise with the maximum period of 31")
#     await set_noise(dut,     period=31)                         # Noise: set period to max
#     await assert_output(dut, period=31, noise=True)

    await done(dut)

@cocotb.test()
async def test_noise_restarts(dut):
    await reset(dut)

    await done(dut)


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
