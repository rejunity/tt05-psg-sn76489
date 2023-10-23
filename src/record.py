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

def load_sn76489_bin(filename, verbose=False):
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

def load_vgm(filename, verbose=False):
    f = open(filename, mode="rb")
    data = f.read()
    f.close()
    vgm_data = vgmparse.Parser(data)
    print(vgm_data.metadata)

    playback_rate = vgm_data.metadata['rate']
    clock_rate = vgm_data.metadata['sn76489_clock']
    seconds = vgm_data.metadata['total_samples'] / 44100
    frames = int(seconds * playback_rate)

    # see https://vgmrips.net/wiki/VGM_Specification#Commands for command descriptions
    CMD_SN76489 = 0x50
    CMD_WAIT_PERIOD = 0x61
    CMD_WAIT_60 = 0x62
    CMD_WAIT_50 = 0x63
    CMD_EOF = 0x66
    WAIT_PERIOD_60 = 735 # samples to wait at 60Hz with 44100 sampling rate
    WAIT_PERIOD_50 = 882 # samples to wait at 50Hz with 44100 sampling rate

    # setup commands according to playback rate
    if (playback_rate == 50):
        CMD_WAIT = CMD_WAIT_50
        WAIT_PERIOD = WAIT_PERIOD_50
    elif (playback_rate == 60):
        CMD_WAIT = CMD_WAIT_60
        WAIT_PERIOD = WAIT_PERIOD_60
    else:
        CMD_WAIT = -1
        WAIT_PERIOD = 44100 // playback_rate

    jagged = []
    frame = []
    total_wait = 0
    for i, item in enumerate(vgm_data.command_list):
        cmd = int.from_bytes(item['command'], 'little')
        data = int.from_bytes(item['data'], 'little') if item['data'] != None else 0
        if (cmd == CMD_SN76489):
            frame.append(data)
        elif cmd == CMD_WAIT or cmd == CMD_WAIT_PERIOD or cmd == CMD_EOF:
            total_wait += (WAIT_PERIOD if cmd == CMD_WAIT else data)

            jagged.append(bytes(frame))
            frame = []

            if cmd == CMD_WAIT_PERIOD:
                assert data >= WAIT_PERIOD
                assert data % WAIT_PERIOD == 0
                for n in range(data // WAIT_PERIOD - 1):
                    jagged.append(bytes([]))
        else:
            raise AssertionError("Unsupported command by SN76489")
    assert frame == []
    assert WAIT_PERIOD*(len(jagged)-1) >= total_wait or total_wait <= WAIT_PERIOD*len(jagged)
    return jagged, playback_rate, clock_rate

@cocotb.test()
async def play_and_record_wav(dut):
    max_time = -1
    max_time = 20
    max_time = 5

    # vgm_filename = "../music/DonkeyKongJunior-ingame.bbc50hz.vgm"
    # vgm_filename = "../music/1942.bbc50hz.vgm"
    # vgm_filename = "../music/CrazeeRider-title.bbc50hz.vgm"
    vgm_filename = "../music/MISSION76496.bbc50hz.vgm"
    # vgm_filename = "../music/MISSION76496.ntsc60hz.vgm"

    music, playback_rate, clock_rate = load_vgm(vgm_filename)
    if True: # test against bin files
        try:
            raw_sn76489_filename = vgm_filename.rstrip('.vgm') + ".sn76489.bin"
            music_raw, playback_rate_raw = load_sn76489_bin(raw_sn76489_filename)
        except:
            try:
                raw_sn76489_filename = vgm_filename.rstrip('.vgm') + ".bin"
                music_raw, playback_rate_raw = load_sn76489_bin(raw_sn76489_filename)        
            except:
                music_raw = music
                playback_rate_raw = playback_rate

        assert playback_rate_raw == playback_rate
        for packet_vgm, packet_raw in zip(music, music_raw):
            assert packet_vgm == packet_raw

        if len(music) != len(music_raw):
            cutoff = min(len(music), len(music_raw))
            print(f'WARNING: packet count differs, VGM has {len(music)} while BIN has {len(music_raw)}!!!')
            print(music[cutoff:-1])
            print('---  tail of ^^^^^ VGM vs RAW BIN vvvvv  --- ')
            print(music_raw[cutoff:-1])
            non_empty_packets = list(filter(lambda packet: packet != b'', music[cutoff:-1]))
            assert len(non_empty_packets) == 0
            non_empty_packets = list(filter(lambda packet: packet != b'', music_raw[cutoff:-1]))
            assert len(non_empty_packets) == 0


    wave_file = [f"../output/{os.path.basename(vgm_filename).rstrip('.vgm')}.cocotb.{ch}.wav" for ch in ["master", "tone0", "tone1", "tone2", "noise"]]
    def get_sample(dut, channel):
        # try:
            if channel == 0:
                return int(dut.uo_out.value) << 7
            else:
                return int(dut.tt_um_rejunity_sn76489_uut.chan[channel-1].attenuation.out.value)
        # finally:
            # return 0
    print(vgm_filename, "->", wave_file)
    print(f"VGM playback rate: {playback_rate}, clock: {clock_rate}, frames: {len(music)}" )
    
    master_clock = clock_rate // 16
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

    await ClockCycles(dut.clk, 16)
