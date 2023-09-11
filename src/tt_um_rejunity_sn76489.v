`default_nettype none

module tt_um_rejunity_sn76489 #( parameter NUM_VOICES = 3 ) (
    input  wire [7:0] ui_in,    // Dedicated inputs - connected to the input switches
    output wire [7:0] uo_out,   // Dedicated outputs - connected to the 7 segment display
    input  wire [7:0] uio_in,   // IOs: Bidirectional Input path
    output wire [7:0] uio_out,  // IOs: Bidirectional Output path
    output wire [7:0] uio_oe,   // IOs: Bidirectional Enable path (active high: 0=input, 1=output)
    input  wire       ena,      // will go high when the design is enabled
    input  wire       clk,      // clock
    input  wire       rst_n     // reset_n - low to reset
);
    assign uo_out[7:0] = {8{1'b0}};
    assign uio_oe[7:0] = {8{1'b1}}; // Bidirectional path set to output
    assign uio_out[7:0] = {8{1'b0}};
    wire reset = ! rst_n;

    always @(posedge clk) begin
        if (reset) begin
        end else begin
        end
    end

    genvar i;
    generate
        for (i = 0; i < NUM_VOICES; i = i + 1) begin
        end
    endgenerate

    wire snd_out;
    assign snd_out = 0;
    assign uo_out[0] = snd_out;


endmodule
