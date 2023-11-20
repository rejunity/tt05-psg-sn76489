/* verilator lint_off WIDTH */

// For the SMS (1 and 2), Genesis and Game Gear, the tapped bits are bits 0 and 3 ($0009), fed back into bit 15.
// For the SG-1000, OMV, SC-3000H, BBC Micro and Colecovision, the tapped bits are bits 0 and 1 ($0003), fed back into bit 14.
// For the Tandy 1000, the tapped bits are bits 0 and 4 ($0011), fed back into bit 14.    
module noise #(parameter LFSR_BITS = 15, LFSR_TAP0 = 0, LFSR_TAP1 = 1) (
    input  wire clk,
    input  wire enable,
    input  wire reset,
    input  wire restart_noise,

    input  wire [2:0] control,
    input  wire driven_by_tone,

    output wire  out
);
    // SEE: Manual, "2. Noise Generator"
    // NF0/NF1 bits
    // Shift rates 512, 1024, 2048 are defined assuming global division by 32 as in "1. Tone Generator"
    localparam SHIFT_RATE_0 = 16; // 16 <= N / 512 /32
    localparam SHIFT_RATE_1 = 32; // 32 <= N /1024 /32
    localparam SHIFT_RATE_2 = 64; // 64 <= N /2048 /32
    localparam SHIFT_RATE_MAX = SHIFT_RATE_2;

    // Noise Feedback Control - "FB" bit
    wire is_white_noise = control[2];

    // Noise Frequency Control - "NF0, NF1" bits
    reg trigger;
    always @(*) begin
        case(control[1:0])
            2'b00:  trigger = counter[$clog2(SHIFT_RATE_0)];
            2'b01:  trigger = counter[$clog2(SHIFT_RATE_1)];
            2'b10:  trigger = counter[$clog2(SHIFT_RATE_2)];
            2'b11:  trigger = driven_by_tone;
        endcase
    end

    reg [$clog2(SHIFT_RATE_MAX):0] counter;
    always @(posedge clk) begin
        if (reset)
            counter <= 0;
        else
            if (enable)
                counter <= counter + 1'b1;
    end

    wire trigger_edge;
    signal_edge signal_edge(
        .clk(clk),
        .reset(reset),
        .signal(trigger),
        .on_posedge(trigger_edge)
    );

    wire reset_lfsr = reset | restart_noise;
    reg [LFSR_BITS-1:0] lfsr;
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
