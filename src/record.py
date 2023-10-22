import cocotb
from cocotb.clock import Clock
from cocotb.triggers import RisingEdge, FallingEdge, Timer, ClockCycles

import os
import numpy as np
from scipy.io.wavfile import write

# https://github.com/cdodd/vgmparse
# sudo pip install -e git+https://github.com/cdodd/vgmparse.git#egg=vgmparse
import vgmparse

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

    # vgm_file_data = open(raw_sn76489_stream.rstrip('.sn76489.bin')+".vgm", 'rb').read()

def load_vgm(filename, verbose=False):
    f = open(filename, mode="rb")
    data = f.read()
    f.close()
    # print(filename, len(data))
    # print("header size: ", data[0], "playback rate: ", data[1], "packets: ", data[2] + 256*data[3], "minutes: ", data[4], "seconds: ", data[5]);
    # vgm_file_data = open(raw_sn76489_stream.rstrip('.sn76489.bin')+".vgm", 'rb').read()
    vgm_data = vgmparse.Parser(data)
    print (vgm_data.metadata)
    print (vgm_data.command_list[:16])

    playback_rate = vgm_data.metadata['rate']
    clock_rate = vgm_data.metadata['sn76489_clock']

    # @TODO: extract SN packets

    return None, playback_rate, clock_rate

@cocotb.test()
async def play_and_record_wav(dut):
    max_time = -1
    max_time = 20
    max_time = 1

    # raw_sn76489_stream = "../music/DonkeyKongJunior-ingame.bbc50hz.bin"
    # raw_sn76489_stream = "../music/1942.bbc50hz.sn76489.bin"
    # raw_sn76489_stream = "../music/CrazeeRider-title.bbc50hz.sn76489.bin"
    raw_sn76489_stream = "../music/MISSION76496.bbc50hz.sn76489.bin"
    music, playback_rate = load_music(raw_sn76489_stream)
    vgm_file_data, _, _ = load_vgm(raw_sn76489_stream.rstrip('.sn76489.bin')+".vgm")
    wave_file = [f"../output/{os.path.basename(raw_sn76489_stream).rstrip('.bin')}.2.{ch}.wav" for ch in ["master", "tone0", "tone1", "tone2", "noise"]]
    def get_sample(dut, channel):
        # try:
            if channel == 0:
                return int(dut.uo_out.value) << 7
            else:
                return int(dut.tt_um_rejunity_sn76489_uut.chan[channel-1].attenuation.out.value)
        # finally:
            # return 0

    print(raw_sn76489_stream, "->", wave_file)


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

    dut._log.info("record " + str(max_time) + " sec")
    # music = music[(60+45)*50:-1]
    # music = music[:300]

    n = 0
    samples = [[] for ch in wave_file]
    for frame in music:
        cur_time = cocotb.utils.get_sim_time(units="ns")
        if max_time > 0 and max_time * 1e9 <= cur_time:
            for ch, data in enumerate(samples):
                write(wave_file[ch], sampling_rate, np.int16(data))
            break

        print("---", n, len(samples[0]), "---", [format(d, '08b') for d in frame], "---", "time in ms:", format(cur_time/1e6, "5.3f"),)
        for val in frame:
            dut.ui_in.value = val
            dut.uio_in.value = 0                # /WE = 0, writes enabled
            await ClockCycles(dut.clk, 1)
            print_chip_state(dut)
        dut.uio_in.value = 1                    # /WE = 1, writes disabled

        while cocotb.utils.get_sim_time(units="ns") < cur_time + (1e9 / fps):
            await Timer(nanoseconds_per_sample, units="ns", round_mode="round")
            for channel, data in enumerate(samples):
                sample = get_sample(dut, channel)
                assert sample >= 0
                assert sample <= 32767
                if True:
                    sample *= 2
                    sample -= 32767
                    sample = -32767 if sample < -32767 else sample
                    sample =  32767 if sample > 32767 else sample
                assert np.int16(sample) == sample
                data.append(sample)

        print_chip_state(dut)

        if n < fps:
            n += 1
        else:            
            for ch, data in enumerate(samples):
                write(wave_file[ch], sampling_rate, np.int16(data))
            n = 0

    await ClockCycles(dut.clk, 1)
