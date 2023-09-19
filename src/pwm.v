// A first-order sigma-delta modulator
// It resembles a PWM, but actually is a PDM (Pulse Density Modulation)
// https://en.wikipedia.org/wiki/Pulse-density_modulation
// 
// Implementaion based on https://www.fpga4fun.com/PWM_DAC_2.html

module pwm #( parameter VALUE_BITS = 8 ) (
    input  wire clk,
    input  wire reset,

    input  wire [VALUE_BITS-1:0]  value,

    output wire out
);
    localparam ACCUMULATOR_BITS = VALUE_BITS + 1;
    reg [ACCUMULATOR_BITS-1:0] accumulator;

    always @(posedge clk) begin
        if (reset) begin
            accumulator <= 0;
        end else begin
            // greater the value, the more often accumulator overflows
            // every time the accumulator overflows, PDM outputs 1
            accumulator <= accumulator[VALUE_BITS-1:0] + value;
        end
    end

    assign out = accumulator[ACCUMULATOR_BITS-1]; // an overflow bit of the accumulator is the output of PDM
endmodule
