module noise #( parameter LFSR_BITS = 15, LFSR_TAP0 = 0, LFSR_TAP1 = 1, parameter COUNTER_BITS = 10) (
    input  wire clk,
    input  wire reset,
    input  wire reset_lfsr,

    input  wire [COUNTER_BITS-1:0]  compare,
    input  wire is_white_noise,

    output wire  out
);

    reg [COUNTER_BITS-1:0] counter;
    reg [LFSR_BITS-1:0] lfsr;

    // For the SMS (1 and 2), Genesis and Game Gear, the tapped bits are bits 0 and 3 ($0009), fed back into bit 15.
    // For the SG-1000, OMV, SC-3000H, BBC Micro and Colecovision, the tapped bits are bits 0 and 1 ($0003), fed back into bit 14.
    // For the Tandy 1000, the tapped bits are bits 0 and 4 ($0011), fed back into bit 14.
    always @(posedge clk) begin
        if (reset) begin
            counter <= 0;
            lfsr <= 1'b1 << (LFSR_BITS-1);
        end else if (reset_lfsr) begin
            lfsr <= 1'b1 << (LFSR_BITS-1);
        end else begin
            if (counter == 0) begin
                counter <= compare - 1'b1;  // reset counter
                if (is_white_noise) begin
                    lfsr <= {lfsr[LFSR_TAP0] ^ lfsr[LFSR_TAP1], lfsr[LFSR_BITS-1:1]};
                end else begin
                    lfsr <= {lfsr[LFSR_TAP0]                  , lfsr[LFSR_BITS-1:1]};
                end
            end else
                counter <= counter - 1'b1;
        end
    end

    assign out = lfsr[0];
endmodule

module noise_control_decoder #( parameter COUNTER_BITS = 10 ) (
    input  wire [2:0] control,
    input  wire [COUNTER_BITS-1:0] tone_freq,

    output reg [COUNTER_BITS-1:0] noise_freq,
    output reg noise_type
);
    // Noise 3 bit control register format: {FB, NF0, NF1}
    // NF0, NF1: Noise Generator Frequency Control
    // FB: Noise Feedback Control
    always @(*) begin
        // NF0, NF1 bits
        case(control[1:0])
            2'b00:  noise_freq = 32;    // =  512/16
            2'b01:  noise_freq = 64;    // = 1024/16
            2'b10:  noise_freq = 128;   // = 2048/16
            2'b11:                      // = tone_freq*2
                    noise_freq = {tone_freq[COUNTER_BITS-2:0], 1'b0};
        endcase
        // FB bit
        noise_type = control[2];
    end
endmodule
