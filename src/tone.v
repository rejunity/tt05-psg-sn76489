module tone #( parameter COUNTER_BITS = 10 ) (
    input  wire clk,
    input  wire reset,

    input  wire [COUNTER_BITS-1:0]  compare,

    output wire out
);
    reg [COUNTER_BITS-1:0] counter;
    reg state;

    // always @(posedge clk) begin
    //     if (reset) begin
    //         counter <= 1;
    //         state <= 0;
    //     end else begin
    //         if (counter == 1) begin
    //             counter <= compare;         // reset counter
    //             state <= ~state;            // flip output state
    //         end else counter <= counter - 1'b1;
                
    //     end
    // end

    always @(posedge clk) begin
        if (reset) begin
            counter <= 0;
            state <= 0;
        end else begin
            if (counter == 0) begin
                counter <= compare - 1'b1;  // reset counter
                state <= ~state;            // flip output state
            end else
                counter <= counter - 1'b1;
        end
    end

    assign out = state;
endmodule
