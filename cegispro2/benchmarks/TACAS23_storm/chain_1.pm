dtmc

const M = 10000;
const N= 100000000*M;

module grid

	c : [0..N] init 0;
	g : bool init false;

	[] (c < N) -> (0.000000000001): (g'=true) + 0.999999999999: (c'=c+1);

endmodule


label "goal" = g=true;
