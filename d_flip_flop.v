// D Flip-Flop with asynchronous reset
module d_flip_flop (
    input wire d,      // Data input
    input wire clk,    // Clock input
    input wire rst,    // Asynchronous reset input (active high)
    output reg q       // Output
);

    // Always block triggered on positive edge of clock or positive edge of reset
    always @(posedge clk or posedge rst) begin
        if (rst) begin
            // Asynchronous reset: set output to 0
            q <= 1'b0;
        end else begin
            // On positive clock edge: output takes the value of input d
            q <= d;
        end
    end

endmodule

// Testbench for D Flip-Flop
module d_flip_flop_tb;

    // Testbench signals
    reg d, clk, rst;
    wire q;

    // Instantiate the D Flip-Flop
    d_flip_flop dff (
        .d(d),
        .clk(clk),
        .rst(rst),
        .q(q)
    );

    // Clock generation
    initial begin
        clk = 0;
        forever #5 clk = ~clk; // Generate a clock with 10ns period
    end

    // Test stimulus
    initial begin
        // Initialize inputs
        d = 0;
        rst = 0;

        // Apply reset
        #10 rst = 1;
        #10 rst = 0;

        // Test different input combinations
        #10 d = 1;
        #10 d = 0;
        #10 d = 1;

        // Apply reset again
        #10 rst = 1;
        #10 rst = 0;

        #10 d = 0;
        #10 d = 1;

        // End simulation
        #10 $finish;
    end

    // Monitor changes
    initial begin
        $monitor("Time=%0t clk=%b rst=%b d=%b q=%b", $time, clk, rst, d, q);
    end

endmodule
