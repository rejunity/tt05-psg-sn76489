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
