import cocotb
from cocotb.clock import Clock
from cocotb.triggers import RisingEdge, FallingEdge, Timer, ClockCycles

def print_chip_state(dut):
    try:
        internal = dut.tt_um_rejunity_sn76489_uut
        print(
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
            dut.uo_out.value)
    except:
        print(dut.uo_out.value)

@cocotb.test()
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
    # tones init
    # dut.ui_in.value = 0b1001_1110 # attn[0] <= 4'b1110;
    # await ClockCycles(dut.clk, 1)
    # dut.ui_in.value = 0b1011_1110
    # await ClockCycles(dut.clk, 1)
    # dut.ui_in.value = 0b1101_1110
    # await ClockCycles(dut.clk, 1)
    # dut.ui_in.value = 0b1111_1110
    # await ClockCycles(dut.clk, 1)
    # dut.ui_in.value = 0b1000_0011 # freq[0] <= 3
    # await ClockCycles(dut.clk, 1)
    # dut.ui_in.value = 0b1010_0001 # freq[1] <= 1
    # await ClockCycles(dut.clk, 1)
    # dut.ui_in.value = 0b1100_0000 # freq[2] <= 0
    # await ClockCycles(dut.clk, 1)
    # # noise init
    # dut.ui_in.value = 0b1110_0111 # noise[0] <=  3'b111
    # await ClockCycles(dut.clk, 1)
                                    # attenuation
    dut.ui_in.value = 0b1001_1111   # channel 0
    await ClockCycles(dut.clk, 1)
    dut.ui_in.value = 0b1011_1111   # channel 1
    await ClockCycles(dut.clk, 1)
    dut.ui_in.value = 0b1101_1111   # channel 2
    await ClockCycles(dut.clk, 1)
    dut.ui_in.value = 0b1111_1111   # channel 3
    await ClockCycles(dut.clk, 1)
                                    # frequency
    dut.ui_in.value = 0b1000_0001   # tone 0
    await ClockCycles(dut.clk, 1)
    dut.ui_in.value = 0b1010_0001   # tone 1
    await ClockCycles(dut.clk, 1)
    dut.ui_in.value = 0b1100_0001   # tone 2
    await ClockCycles(dut.clk, 1)

    dut.ui_in.value = 0b1110_0111 # noise[0] <=  3'b111
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
    dut.ui_in.value = 0b1000_0001 # freq[0] <= 1
    for i in range(8):
        print_chip_state(dut)
        await ClockCycles(dut.clk, 1)

    dut._log.info("test freq 0")
    dut.ui_in.value = 0b1000_0000 # freq[0] <= 0
    for i in range(16):
        print_chip_state(dut)
        await ClockCycles(dut.clk, 1)

    dut._log.info("clock x64 speedup")
    for i in range(32):
        print_chip_state(dut)
        await ClockCycles(dut.clk, 64)

    dut._log.info("done")
