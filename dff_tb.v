`timescale 1ns/1ps

module dff_tb();
    reg clk, reset, d;
    wire q;

    // Instantiate the D flip-flop
    dff dut (
        .clk(clk),
        .reset(reset),
        .d(d),
        .q(q)
    );

    // Clock generation
    always begin
        #5 clk = ~clk;
    end

    // Testbench stimulus
    initial begin
        $dumpfile("dff_tb.vcd");
        $dumpvars(0, dff_tb);

        // Initialize signals
        clk = 0;
        reset = 1;
        d = 0;

        // Release reset
        #10 reset = 0;

        // Test case 1: Set D to 1
        #10 d = 1;

        // Test case 2: Set D to 0
        #10 d = 0;

        // Test case 3: Toggle D
        #10 d = 1;
        #10 d = 0;

        // Test case 4: Assert reset
        #10 reset = 1;
        #10 reset = 0;

        // Run for a few more cycles
        #20;

        $finish;
    end

    // Display changes
    always @(posedge clk) begin
        $display("Time=%0t: reset=%b, d=%b, q=%b", $time, reset, d, q);
    end
endmodule
