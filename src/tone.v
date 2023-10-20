
// https://www.smspower.org/forums/17191-SG1000HardwareQuestions#103500
// Posted: Sun Sep 16, 2018 5:03 pm
//
// Frequency value of $000 produces (MCLK / 32) / $400 output frequency on TI 
// PSG while on VDP it produces (MCLK / 32) / $001. Volume and frequency writes 
// do not reset the phase of tone channels but frequency writes will reset phase 
// of noise channel. It is possible to keep noise channel output permanently low 
// by writing into frequency register. All writes take effect immediately.

// https://github.com/dnotq/sn76489_audio/blob/master/rtl/sn76489_audio.vhd
// This also demonstrates why changing the tone period will not take effect
// until the next cycle of the counter.  Interestingly, the same counter is
// used in the AY-3-8910 and YM-2149, only slightly modified to count up
// (actually, in silicon both up and down counters are present
// simultaneously) and reset on a >= period condition.

module tone #( parameter COUNTER_BITS = 10 ) (
    input  wire clk,
    input  wire enable,
    input  wire reset,

    input  wire [COUNTER_BITS-1:0]  compare,

    output wire out
);
    reg [COUNTER_BITS-1:0] counter;
    reg state;

    // always @(posedge clk) begin
    //     if (reset) begin
    //         counter <= 0;
    //         state <= 0;
    //     end else begin
    //         if (enable)
    //             counter <= counter - 1'b1;
    //     end
    // end

    // always @(negedge clk) begin
    //     if (!reset)
    //         if (enable && counter == 0) begin
    //             counter <= compare;         // reset counter
    //             state <= ~state;            // flip output state
    //         end
    // end


    always @(posedge clk) begin
        if (reset) begin
            counter <= 0;
            state <= 0;
        end else begin
            if (enable)
                if (counter == 0) begin
                    counter <= compare - 1'b1;  // reset counter
                    state <= ~state;            // flip output state
                end else
                    counter <= counter - 1'b1;
        end
    end

    assign out = state;
endmodule
