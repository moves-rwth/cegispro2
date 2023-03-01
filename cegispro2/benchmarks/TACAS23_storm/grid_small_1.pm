dtmc

const N = 10;
const M = 10;

module grid

	a : [0..N] init 0;
	b : [0..M] init 0;

	[] (a < N & b < M) -> (0.5): (a'=a+1) + (0.5) : (b'=b+1);

endmodule


label "goal" = a<N&b>=M;

