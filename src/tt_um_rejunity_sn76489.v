`default_nettype none

module tt_um_rejunity_sn76489 #( parameter NUM_TONES = 3, parameter NUM_NOISES = 1,
                                 parameter ATTENUATION_CONTROL_BITS = 4,
                                 parameter FREQUENCY_COUNTER_BITS = 10, 
                                 parameter NOISE_CONTROL_BITS = 3,
                                 parameter CHANNEL_OUTPUT_BITS = 8,
                                 parameter MASTER_OUTPUT_BITS = 7
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
    assign uio_oe[7:0] = {8{1'b1}}; // Bidirectional path set to output
    assign uio_out[7:0] = {8{1'b0}};
    wire reset = ! rst_n;

    wire [7:0] data;
    assign data = ui_in;

    // The SN76489 has 8 control "registers":
    // - 4 x 4 bit volume registers (attenuation)
    // - 3 x 10 bit tone registers  (frequency)
    // - 1 x 3 bit noise register
    localparam NUM_CHANNELS = NUM_TONES + NUM_NOISES;    
    reg [ATTENUATION_CONTROL_BITS-1:0]  control_attn[NUM_CHANNELS-1:0];
    reg [FREQUENCY_COUNTER_BITS-1:0]    control_tone_freq[NUM_TONES-1:0];
    reg [NOISE_CONTROL_BITS-1:0]        control_noise[NUM_NOISES-1:0];
    reg [2:0] latch_control_reg;
    reg reset_noise;

    always @(posedge clk) begin
        if (reset) begin
            // control_attn[0] <= 4'b1;
            // control_attn[1] <= 4'b10;
            // control_attn[2] <= 4'b100;
            // control_attn[3] <= 4'b1000;
            control_attn[0] <= 4'b1110;
            control_attn[1] <= 4'b1110;
            control_attn[2] <= 4'b1110;
            control_attn[3] <= 4'b1110;
            control_tone_freq[0] <= 3;
            control_tone_freq[1] <= 1;
            control_tone_freq[2] <= 0;

            control_noise[0] <= 3'b111;

            latch_control_reg <= 0;
            reset_noise <= 0;
        end else begin
            reset_noise <= 0;
            if (data[7] == 1'b1) begin
                case(data[6:4])
                    3'b000 : control_tone_freq[0][3:0] <= data[3:0];
                    3'b010 : control_tone_freq[1][3:0] <= data[3:0];
                    3'b100 : control_tone_freq[2][3:0] <= data[3:0];
                    3'b110 : 
                        begin 
                            control_noise[0] <= data[2:0];
                            reset_noise <= 1;
                        end
                    3'b001 : control_attn[0] <= data[3:0];
                    3'b011 : control_attn[1] <= data[3:0];
                    3'b101 : control_attn[2] <= data[3:0];
                    3'b111 : control_attn[3] <= data[3:0];
                    default : begin end
                endcase
                latch_control_reg <= data[6:4];
            end else begin
                case(latch_control_reg)
                    3'b000 : control_tone_freq[0][9:4] <= data[5:0];
                    3'b010 : control_tone_freq[1][9:4] <= data[5:0];
                    3'b100 : control_tone_freq[2][9:4] <= data[5:0];
                    3'b001 : control_attn[0] <= data[3:0];
                    3'b011 : control_attn[1] <= data[3:0];
                    3'b101 : control_attn[2] <= data[3:0];
                    3'b111 : control_attn[3] <= data[3:0];
                    default : begin end
                endcase
            end
        end
    end

    wire                           channels [NUM_CHANNELS-1:0];
    wire [CHANNEL_OUTPUT_BITS-1:0] volumes  [NUM_CHANNELS-1:0];

    genvar i;
    generate
        for (i = 0; i < NUM_TONES; i = i + 1) begin
            tone #(.COUNTER_BITS(FREQUENCY_COUNTER_BITS)) tone (
                .clk(clk),
                .reset(reset),
                .compare(control_tone_freq[i]),
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

            noise #(.COUNTER_BITS(FREQUENCY_COUNTER_BITS)) noise (
                .clk(clk),
                .reset(reset),
                .reset_lfsr(reset_noise),
                .compare(noise_freq),
                .is_white_noise(noise_type),
                .out(channels[NUM_TONES+i])
                );
        end

        for (i = 0; i < NUM_CHANNELS; i = i + 1) begin
            attenuation #(.VOLUME_BITS(CHANNEL_OUTPUT_BITS)) attenuation (
                .in(channels[i]),
                .control(control_attn[i]),
                .out(volumes[i])
                );
        end
    endgenerate

    // sum up all the channels, clamp to the highest value when overflown
    localparam OVERFLOW_BITS = $clog2(NUM_CHANNELS);
    localparam ACCUMULATOR_BITS = CHANNEL_OUTPUT_BITS + OVERFLOW_BITS;
    wire [ACCUMULATOR_BITS-1:0] master;
    assign master = (volumes[0] + volumes[1] + volumes[2] + volumes[3]);
    assign uo_out = (master[ACCUMULATOR_BITS-1 -: OVERFLOW_BITS] == 0) ? master[CHANNEL_OUTPUT_BITS-1 -: MASTER_OUTPUT_BITS] : {MASTER_OUTPUT_BITS{1'b1}};
    
endmodule
