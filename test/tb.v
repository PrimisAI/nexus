`timescale 1ns/1ps

module counter_tb;

reg clk;
reg reset;
wire [3:0] count;

// Instantiate the counter
counter uut (
    .clk(clk),
    .reset(reset),
    .count(count)
);

// Clock generation
always begin
    #5 clk = ~clk;
end

// Testbench stimulus
initial begin
    // Dump waves
    $dumpfile("waveform.vcd");
    $dumpvars(0, counter_tb);

    // Initialize inputs
    clk = 0;
    reset = 1;

    // Reset the counter
    #10 reset = 0;

    // Run for some cycles
    #100;

    // Add some print statements
    $display("Simulation finished. Final count: %b", count);

    // Finish the simulation
    $finish;
end

// Add a monitor to print count changes
initial begin
    $monitor("At time %t, count = %b", $time, count);
end

endmodule