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

// function [7:0] sum (input [7:0] a, b);
//     begin
//         sum = a + b;
//     end
// endfunction

module tt_um_rejunity_sn76489 #( parameter NUM_TONES = 3, parameter NUM_NOISES = 1,
                                 parameter ATTENUATION_CONTROL_BITS = 4,
                                 parameter FREQUENCY_COUNTER_BITS = 10, 
                                 parameter NOISE_CONTROL_BITS = 3,
                                 parameter CHANNEL_OUTPUT_BITS = 4
                                 
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
    localparam NUM_CHANNELS = NUM_TONES + NUM_NOISES;    
    reg [ATTENUATION_CONTROL_BITS-1:0]  control_attn[NUM_CHANNELS-1:0];
    reg [FREQUENCY_COUNTER_BITS-1:0]    control_tone_freq[NUM_TONES-1:0];
    reg [NOISE_CONTROL_BITS-1:0]        control_noise[NUM_NOISES-1:0];

    always @(posedge clk) begin
        if (reset) begin
            control_attn[0] <= 4'b1;
            control_attn[1] <= 4'b10;
            control_attn[2] <= 4'b100;
            control_attn[3] <= 4'b1000;

            control_tone_freq[0] <= 3;
            control_tone_freq[1] <= 1;
            control_tone_freq[2] <= 0;

            control_noise[0] <= 3'b111;
        end else begin
        end
    end

    wire [CHANNEL_OUTPUT_BITS-1:0] channels [NUM_CHANNELS-1:0];

    genvar i;
    generate
        for (i = 0; i < NUM_TONES; i = i + 1) begin
            tone #(.COUNTER_BITS(FREQUENCY_COUNTER_BITS), .VALUE_BITS(CHANNEL_OUTPUT_BITS)) tone (
                .clk(clk),
                .reset(reset),
                .compare(control_tone_freq[i]),
                .value(control_attn[i]),
                .out(channels[i])
                );
        end

        for (i = 0; i < NUM_NOISES; i = i + 1) begin
            wire noise_type;
            wire [FREQUENCY_COUNTER_BITS-1:0] noise_freq;
            noise_control_decoder #(.COUNTER_BITS(FREQUENCY_COUNTER_BITS)) noise_control_decoder (
                .control(control_noise[i]),
                .tone_freq(control_tone_freq[NUM_TONES-1]), // last tone 
                .noise_type(noise_type),
                .noise_freq(noise_freq)
                );

            noise #(.COUNTER_BITS(FREQUENCY_COUNTER_BITS), .VALUE_BITS(CHANNEL_OUTPUT_BITS)) noise (
                .clk(clk),
                .reset(reset),
                //.reset_lfsr( TODO )
                .compare(noise_freq),
                .is_white_noise(noise_type),
                .value(control_attn[3]),
                .out(channels[NUM_TONES+i])
                );
        end
    endgenerate

    assign uo_out = channels[0] + channels[1] + channels[2] + channels[3];

endmodule
