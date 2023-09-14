import cocotb
from cocotb.clock import Clock
from cocotb.triggers import RisingEdge, FallingEdge, Timer, ClockCycles



@cocotb.test()
async def test_psg(dut):

    dut._log.info("start")
    clock = Clock(dut.clk, 10, units="us")
    cocotb.start_soon(clock.start())

    dut._log.info("reset")
    dut.rst_n.value = 0
    await ClockCycles(dut.clk, 10)
    dut.rst_n.value = 1

    dut._log.info("init")
    # tones
    dut.ui_in.value = 0b1001_1110 # attn[0] <= 4'b1110;
    await ClockCycles(dut.clk, 1)
    dut.ui_in.value = 0b1011_1110
    await ClockCycles(dut.clk, 1)
    dut.ui_in.value = 0b1101_1110
    await ClockCycles(dut.clk, 1)
    dut.ui_in.value = 0b1111_1110
    await ClockCycles(dut.clk, 1)
    dut.ui_in.value = 0b1000_0011 # freq[0] <= 3;
    await ClockCycles(dut.clk, 1)
    dut.ui_in.value = 0b1010_0001 # freq[1] <= 1;
    await ClockCycles(dut.clk, 1)
    dut.ui_in.value = 0b1100_0000 # freq[2] <= 0;
    await ClockCycles(dut.clk, 1)
    # noise
    dut.ui_in.value = 0b1110_0111 # noise[0] <=  3'b111;
    await ClockCycles(dut.clk, 1)
            

    dut._log.info("run")
    for i in range(32):
        await ClockCycles(dut.clk, 1)
        print(
            #dut.tt_um_rejunity_sn76489_uut.noise.lfsr.value,
            #dut.uio_out.value,
            dut.uo_out.value)

    dut._log.info("clock x32 speedup")
    for i in range(32):
        await ClockCycles(dut.clk, 32)
        print(
            #dut.tt_um_rejunity_sn76489_uut.noise.lfsr.value,
            #dut.uio_out.value,
            dut.uo_out.value)

    dut._log.info("done")
