`timescale 1ns/1ps

module d_flip_flop_tb;

reg clk, reset, d;
wire q;

d_flip_flop dff (
    .clk(clk),
    .reset(reset),
    .d(d),
    .q(q)
);

initial begin
    clk = 0;
    forever #5 clk = ~clk;
end

initial begin
    $dumpfile("d_flip_flop.vcd");
    $dumpvars(0, d_flip_flop_tb);

    $monitor("Time=%t, clk=%b, reset=%b, d=%b, q=%b", $time, clk, reset, d, q);

    reset = 1; d = 0;
    #10 reset = 0;

    #10 d = 1;
    #10 d = 0;
    #10 d = 1;
    #10 d = 0;

    #10 reset = 1;
    #10 reset = 0;

    #10 d = 1;
    #10 d = 0;

    #10 $finish;
end

endmodule
