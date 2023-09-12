`default_nettype none

// TODO: Attenuation table
// int volume_table[16]={
//   32767, 26028, 20675, 16422, 13045, 10362,  8231,  6568,
//    5193,  4125,  3277,  2603,  2067,  1642,  1304,     0
// };

// module attenuationLUT(index, value);
//     input [3:0] index;
//     output reg [15:0] value;
//     always @(index) begin
//         case (index)
//             0: value <= 0;
//             1: value <= 1304;
//             2: value <= 1642;
//              ...

module tone #( parameter COUNTER_BITS = 10, parameter VALUE_BITS = 4 ) (
    input  wire clk,
    input  wire reset,

    input  wire [COUNTER_BITS-1:0]  compare,
    input  wire [VALUE_BITS-1:0]    value,

    output reg  [VALUE_BITS-1:0]    out
);
    reg [COUNTER_BITS-1:0] counter;
    reg state;

    always @(posedge clk) begin
        if (reset) begin
            counter <= 0;
            state <= 0;
        end else begin
            if (counter == compare) begin
                counter <= 0;               // reset counter
                state <= ~state;            // flip output state
            end else
                counter <= counter + 1'b1;  // increment counter
        end
    end

    assign out = value & {VALUE_BITS{state}};
endmodule

module tt_um_rejunity_sn76489 #( parameter NUM_TONES = 3, parameter NUM_NOISES = 1,
                                 parameter ATTENUATION_CONTROL_BITS = 4,
                                 parameter TONE_FREQUENCY_BITS = 10, parameter TONE_BITS = 4,
                                 parameter NOISE_CONTROL_BITS = 3
) (
    input  wire [7:0] ui_in,    // Dedicated inputs - connected to the input switches
    output wire [7:0] uo_out,   // Dedicated outputs - connected to the 7 segment display
    input  wire [7:0] uio_in,   // IOs: Bidirectional Input path
    output wire [7:0] uio_out,  // IOs: Bidirectional Output path
    output wire [7:0] uio_oe,   // IOs: Bidirectional Enable path (active high: 0=input, 1=output)
    input  wire       ena,      // will go high when the design is enabled
    input  wire       clk,      // clock
    input  wire       rst_n     // reset_n - low to reset
);
    //assign uo_out[7:0] = {8{1'b0}};
    assign uio_oe[7:0] = {8{1'b1}}; // Bidirectional path set to output
    assign uio_out[7:0] = {8{1'b0}};
    wire reset = ! rst_n;

    // The SN76489 has 8 control "registers":
    // - 4 x 4 bit volume registers (attenuation)
    // - 3 x 10 bit tone registers  (frequency)
    // - 1 x 3 bit noise register
    reg [ATTENUATION_CONTROL_BITS-1:0]  control_attn[(NUM_TONES + NUM_NOISES)-1:0];
    reg [TONE_FREQUENCY_BITS-1:0]       control_tone_freq[NUM_TONES-1:0];
    reg [NOISE_CONTROL_BITS-1:0]        control_noise[NUM_NOISES-1:0];

    always @(posedge clk) begin
        if (reset) begin
            control_attn[0] = 4'b1;
            control_attn[1] = 4'b10;
            control_attn[2] = 4'b100;
            control_attn[3] = 4'b1000;

            control_tone_freq[0] = 0;
            control_tone_freq[1] = 1;
            control_tone_freq[2] = 2;

            control_noise[0] = 0;
        end else begin
        end
    end

    reg [TONE_BITS-1:0] tone_waves [NUM_TONES-1:0];

    genvar i;
    generate
        for (i = 0; i < NUM_TONES; i = i + 1) begin
            tone #(.COUNTER_BITS(TONE_FREQUENCY_BITS), .VALUE_BITS(TONE_BITS)) tone (
                .clk(clk),
                .reset(reset),
                .compare(control_tone_freq[i]),
                .value(control_attn[i]),
                .out(tone_waves[i])
                );
        end
    endgenerate

    assign uo_out = tone_waves[0] + tone_waves[1] + tone_waves[2];

endmodule
