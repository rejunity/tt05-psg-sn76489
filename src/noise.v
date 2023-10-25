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
    reg [COUNTER_BITS-1:0] noise_freq;
    always @(posedge clk) begin
        // NF0, NF1 bits
        case(control[1:0])
            // SEE: Manual, "2. Noise Generator"
            // Shift rates 512, 1024, 2048 are defined assuming global division by 32 as in "1. Tone Generator"
            2'b00:  noise_freq <= 16; // N/512  = N / 16 (master clk divider) / 2 (trigger flip-flop) / 16
            2'b01:  noise_freq <= 32; // N/1024 = N / 16 (master clk divider) / 2 (trigger flip-flop) / 32
            2'b10:  noise_freq <= 64; // N/2048 = N / 16 (master clk divider) / 2 (trigger flip-flop) / 32
            2'b11:  noise_freq <= tone_freq;
        endcase
        // FB bit
        is_white_noise <= control[2];
    end

    wire trigger;
    tone #(.COUNTER_BITS(COUNTER_BITS)) tone (
        .clk(clk),
        .enable(enable),
        .reset(reset),
        .compare(noise_freq),
        .out(trigger));

    wire trigger_edge;
    signal_edge signal_edge(
        .clk(clk),
        .reset(reset),
        .signal(trigger),
        .on_posedge(trigger_edge)
    );

    // @TODO: posedge detection like in AY
    // @TODO: mux divider for /32, /64, /128
    // @TODO: use tone 3 flipflop instead of full counter here based on https://github.com/gchiasso/76489A-analysis

    reg is_white_noise;
    reg reset_lfsr;
    reg [LFSR_BITS-1:0] lfsr;
    assign reset_lfsr = reset | restart_noise;
    always @(posedge clk) begin
        if (reset_lfsr)
            lfsr <= 1'b1 << (LFSR_BITS-1);
        else begin
            if (trigger_edge) begin
                if (is_white_noise) begin
                    lfsr <= {lfsr[LFSR_TAP0] ^ lfsr[LFSR_TAP1], lfsr[LFSR_BITS-1:1]};
                end else begin
                    lfsr <= {lfsr[LFSR_TAP0]                  , lfsr[LFSR_BITS-1:1]};
                end
            end
        end
    end

    assign out = lfsr[0];
endmodule
