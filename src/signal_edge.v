module signal_edge(
    input  wire clk,
    input  wire reset,
    input  wire signal,
    output wire on_posedge,
    output wire on_negedge,
    output wire on_edge
);
    reg previous_signal_state_0;
    reg previous_signal_state_1;
    always @(posedge clk) begin
        if (reset) begin
            previous_signal_state_0 <= 0; // tested in posedge, init to 0 to prevent missing the first positive edge after reset
            previous_signal_state_1 <= 1; // tested in negedge,               --- // ---               negative edge after reset
        end else begin
            previous_signal_state_0 <= signal;
            previous_signal_state_1 <= signal;
        end
    end
    
    assign on_edge    = on_posedge | on_negedge;
    assign on_posedge = (previous_signal_state_0 != signal &&  signal);
    assign on_negedge = (previous_signal_state_1 != signal && !signal);
endmodule
