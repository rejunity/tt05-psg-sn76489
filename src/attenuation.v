// The datasheet defines 16 attenuation steps that are -2.0dB apart, ranging from 0 dB at step 0
// to a maximum attenuation of -28dB at step 14. Step 15 is a complete silence.
// 7 bit is enough to represent SN attenuation levels as unique numbers

/* verilator lint_off REALCVT */
module attenuation #( parameter CONTROL_BITS = 4, parameter VOLUME_BITS = 14 ) (
    input  wire in,
    input  wire [CONTROL_BITS-1:0] control,
    output reg  [VOLUME_BITS-1:0] out
);
    localparam real MAX_VOLUME = (1 << VOLUME_BITS) - 1;
    `define ATLEAST1(i) ($rtoi(i)>1 ? $rtoi(i) : 1)
    always @(*) begin
        case(in ? control : 15) // if in == 0, output is forced to 0 
            // each bit of attenuation corresponds to 2dB
            // 2dB = 10^(-0.1) = 0.79432823
            0:  out =           MAX_VOLUME;
            1:  out = `ATLEAST1(MAX_VOLUME * 0.79432823);
            2:  out = `ATLEAST1(MAX_VOLUME * 0.63095734);
            3:  out = `ATLEAST1(MAX_VOLUME * 0.50118723);
            4:  out = `ATLEAST1(MAX_VOLUME * 0.39810717);
            5:  out = `ATLEAST1(MAX_VOLUME * 0.31622777);
            6:  out = `ATLEAST1(MAX_VOLUME * 0.25118864);
            7:  out = `ATLEAST1(MAX_VOLUME * 0.19952623);
            8:  out = `ATLEAST1(MAX_VOLUME * 0.15848932);
            9:  out = `ATLEAST1(MAX_VOLUME * 0.12589254);
            10: out = `ATLEAST1(MAX_VOLUME * 0.10000000);
            11: out = `ATLEAST1(MAX_VOLUME * 0.07943282);
            12: out = `ATLEAST1(MAX_VOLUME * 0.06309573);
            13: out = `ATLEAST1(MAX_VOLUME * 0.05011872);
            14: out = `ATLEAST1(MAX_VOLUME * 0.03981072);
                default:
                    out = 0;
        endcase
        `undef ATLEAST1
    end
endmodule

