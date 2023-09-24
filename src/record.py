import cocotb
from cocotb.clock import Clock
from cocotb.triggers import RisingEdge, FallingEdge, Timer, ClockCycles

import numpy as np
from scipy.io.wavfile import write

def print_chip_state(dut):
    try:
        internal = dut.tt_um_rejunity_sn76489_uut
        print(
            '{:2d}'.format(int(internal.chan[0].attenuation.control.value)),
            '{:4d}'.format(int(internal.tone[0].gen.compare.value)),
            '{:4d}'.format(int(internal.tone[0].gen.counter.value)),
                        "|#|" if internal.tone[0].gen.out == 1 else "|-|", # "|",
            '{:2d}'.format(int(internal.chan[1].attenuation.control.value)),
            '{:4d}'.format(int(internal.tone[1].gen.compare.value)),
            '{:4d}'.format(int(internal.tone[1].gen.counter.value)),
                        "|#|" if internal.tone[1].gen.out == 1 else "|-|",  #"|",
            '{:2d}'.format(int(internal.chan[2].attenuation.control.value)),
            '{:4d}'.format(int(internal.tone[2].gen.compare.value)),
            '{:4d}'.format(int(internal.tone[2].gen.counter.value)),
                        "|#|" if internal.tone[2].gen.out == 1 else "|-|",  #"!",
            '{:2d}'.format(int(internal.chan[3].attenuation.control.value)),
            internal.noise[0].gen.control.value,
            internal.noise[0].gen.reset_lfsr.value,
            '{:4d}'.format(int(internal.noise[0].gen.tone.compare.value)),
            '{:4d}'.format(int(internal.noise[0].gen.tone.counter.value)),
                        ">" if internal.noise[0].gen.tone.out == 1 else " ",
            internal.noise[0].gen.lfsr.value, ">>",
            '{:3d}'.format(int(dut.uo_out.value)),
                        "@" if dut.uo_out[0].value == 1 else ".")
    except:
        print(dut.uo_out.value)

def load_music(filename, verbose=False):
    f = open(filename, mode="rb")
    data = f.read()
    f.close()
    print(filename, len(data))
    print("header size: ", data[0], "playback rate: ", data[1], "packets: ", data[2] + 256*data[3], "minutes: ", data[4], "seconds: ", data[5]);
    playback_rate = data[1]
    packets = data[2] + 256*data[3]
    offset = data[0] + 1
    print("titles size:", data[offset], "title: ", data[offset + 1: offset + 1 + data[offset]])
    offset += data[offset] + 1
    print("author size:", data[offset], "author: ", data[offset + 1: offset + 1 + data[offset]])
    offset += data[offset] + 1

    # cut the header
    data = data[offset:len(data)]
    offset = 0

    jagged = []
    for i in range(packets):
        jagged.append(data[offset+1:offset+1+data[offset]])
        if verbose: print("packet", i, "size:", data[offset], "data: ", jagged[-1])
        offset += data[offset] + 1
    if verbose: print(packets, offset, len(data), int(data[offset]), int(data[-1]))
    assert data[offset    ] == 0x00
    assert data[offset + 1] == 0xff

    assert packets == len(jagged)
    return jagged, playback_rate

@cocotb.test()
async def play_and_record_wav(dut):
    samples = []
    # raw_sn76489_stream = "../music/DonkeyKongJunior-ingame.bbc50hz.bin"
    raw_sn76489_stream = "../music/1942.bbc50hz.sn76489.bin"
    # raw_sn76489_stream = "../music/CrazeeRider-title.bbc50hz.sn76489.bin"
    music, playback_rate = load_music(raw_sn76489_stream)

    master_clock = 4_000_000 // 16
    fps = playback_rate
    cycles_per_frame = master_clock / fps
    cycle_in_nanoseconds = 1e9 / master_clock # 1 / 4Mhz / nanosecond

    sampling_rate = 44100
    nanoseconds_per_sample = 1e9 / sampling_rate
    cycles_per_sample = nanoseconds_per_sample / cycle_in_nanoseconds
    print("cycle in nanoseconds", cycle_in_nanoseconds, "cycles per frame:", cycles_per_frame, "cycles per wav sample", cycles_per_sample)
    print("1 sec check:", fps * cycles_per_frame * cycle_in_nanoseconds / 1e9, "samples check", 1e9 / (cycles_per_sample * cycle_in_nanoseconds))

    dut._log.info("start")
    clock = Clock(dut.clk, cycle_in_nanoseconds, units="ns")
    # clock = Clock(dut.clk, 10, units="us")
    cocotb.start_soon(clock.start())

    dut._log.info("reset")
    dut.rst_n.value = 0
    await ClockCycles(dut.clk, 10)
    dut.rst_n.value = 1
    print_chip_state(dut)

    dut._log.info("record")

    samples = []
    n = 0
    for frame in music:
        cur_time = cocotb.utils.get_sim_time(units="ns")
        print("---", n, len(samples), "---", [format(d, '08b') for d in frame], "---", "time in ms:", format(cur_time/1e6, "5.3f"),)
        for val in frame:
            dut.ui_in.value = val
            await ClockCycles(dut.clk, 1)
            print_chip_state(dut)

        #ns = cycles_per_frame * cycle_in_nanoseconds while ns > 0:

        # i = cycles_per_frame - len(frame)
        # carry = 0
        # while i > 0:
        #     i -= int(cycles_per_sample + carry)
        #     await ClockCycles(dut.clk, int(cycles_per_sample + carry))
        #     carry = cycles_per_sample + carry - int(cycles_per_sample + carry)
        #     samples.append(int(dut.uo_out.value) * 32)
        #     assert int(dut.uo_out.value) * 32 < 65535
        #     assert int(dut.uo_out.value) * 32 >= 0
        # print_chip_state(dut)


        while cocotb.utils.get_sim_time(units="ns") < cur_time + (1e9 / fps):
            await Timer(nanoseconds_per_sample, units="ns", round_mode="round")
            samples.append(int(dut.uo_out.value) * 64)
        print_chip_state(dut)

        # for i in range(int(cycles_per_frame / cycles_per_sample)):
        #     await ClockCycles(dut.clk, int(cycles_per_sample))
            
        #     # samples.append(int(dut.uo_out.value & 0xfe) << 8)
        #     samples.append(int(dut.uo_out.value) * 64)
        #     assert int(dut.uo_out.value) * 64 < 65535
        #     assert int(dut.uo_out.value) * 64 >= 0
        # print_chip_state(dut)

        if n < fps:
            n += 1
        else:            
            write('test.wav', sampling_rate, np.int16(samples))
            n = 0

    await ClockCycles(dut.clk, 1)
