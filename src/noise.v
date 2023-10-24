/* verilator lint_off WIDTH */

// For the SMS (1 and 2), Genesis and Game Gear, the tapped bits are bits 0 and 3 ($0009), fed back into bit 15.
// For the SG-1000, OMV, SC-3000H, BBC Micro and Colecovision, the tapped bits are bits 0 and 1 ($0003), fed back into bit 14.
// For the Tandy 1000, the tapped bits are bits 0 and 4 ($0011), fed back into bit 14.    
module noise #( parameter LFSR_BITS = 15, LFSR_TAP0 = 0, LFSR_TAP1 = 1, parameter COUNTER_BITS = 10 ) (
    input  wire clk,
    input  wire enable,
    input  wire reset,
    input  wire restart_noise,

    input  wire [2:0] control,
    input  wire [COUNTER_BITS-1:0] tone_freq,

    output wire  out
);
    localparam MASTER_CLOCK = 16;
    localparam TONE_DIV_2 = 2;

    reg [COUNTER_BITS-1:0] noise_freq;
    always @(posedge clk) begin
        // NF0, NF1 bits
        case(control[1:0])
            2'b00:  noise_freq <= 512 /MASTER_CLOCK/TONE_DIV_2;
            2'b01:  noise_freq <= 1024/MASTER_CLOCK/TONE_DIV_2;
            2'b10:  noise_freq <= 2048/MASTER_CLOCK/TONE_DIV_2;
            2'b11:  noise_freq <= tone_freq;
        endcase
        // FB bit
        is_white_noise <= control[2];
    end

    wire noise_trigger;
    tone #(.COUNTER_BITS(COUNTER_BITS)) tone (
        .clk(clk),
        .enable(enable),
        .reset(reset),
        .compare(noise_freq),
        .out(noise_trigger));

    // @TODO: posedge detection like in AY
    // @TODO: mux divider for /32, /64, /128
    // @TODO: use tone 3 flipflop instead of full counter here based on https://github.com/gchiasso/76489A-analysis

    reg is_white_noise;
    reg reset_lfsr;
    reg [LFSR_BITS-1:0] lfsr;
    assign reset_lfsr = reset | restart_noise;
    always @(posedge noise_trigger, posedge reset_lfsr) begin
        if (reset_lfsr) begin
            lfsr <= 1'b1 << (LFSR_BITS-1);
        end else begin
            if (is_white_noise) begin
                lfsr <= {lfsr[LFSR_TAP0] ^ lfsr[LFSR_TAP1], lfsr[LFSR_BITS-1:1]};
            end else begin
                lfsr <= {lfsr[LFSR_TAP0]                  , lfsr[LFSR_BITS-1:1]};
            end
        end
    end

    assign out = lfsr[0];
endmodule
