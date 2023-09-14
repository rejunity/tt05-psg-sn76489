
module attenuation #( parameter CONTROL_BITS = 4, parameter VOLUME_BITS = 15 ) (
    input  wire in,
    input  wire [CONTROL_BITS-1:0] control,
    output reg  [VOLUME_BITS-1:0] out
);
    always @(*) begin
        localparam REDUCE_ = (15 - VOLUME_BITS);
        localparam REDUCE  = REDUCE_ >= 0 ? REDUCE_ : 0;
        `define ATLEAST1(i) (i>0 ? i : 1)
        case(in ? control : -1) // if in == 0, output is made 0 via default branch in case statement
            // out = 0x7fff; // MAX_OUTPUT
            // out /= 1.258925412; // = 10 ^ (2/20) = 2dB
            0:  out = `ATLEAST1(32767 >> REDUCE);
            1:  out = `ATLEAST1(26028 >> REDUCE);
            2:  out = `ATLEAST1(20675 >> REDUCE);
            3:  out = `ATLEAST1(16422 >> REDUCE);
            4:  out = `ATLEAST1(13045 >> REDUCE);
            5:  out = `ATLEAST1(10362 >> REDUCE);
            6:  out = `ATLEAST1( 8231 >> REDUCE);
            7:  out = `ATLEAST1( 6568 >> REDUCE);
            8:  out = `ATLEAST1( 5193 >> REDUCE);
            9:  out = `ATLEAST1( 4125 >> REDUCE);
            10: out = `ATLEAST1( 3277 >> REDUCE);
            11: out = `ATLEAST1( 2603 >> REDUCE);
            12: out = `ATLEAST1( 2067 >> REDUCE);
            13: out = `ATLEAST1( 1642 >> REDUCE);
            14: out = `ATLEAST1( 1304 >> REDUCE);
            default:
                out = 0;
        endcase
        `undef ATLEAST1
    end
endmodule

