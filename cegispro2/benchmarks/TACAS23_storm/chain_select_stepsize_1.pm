dtmc

const N= 10000000;

module grid

	c : [0..1] init 0;
	x : [0..N] init 0;
	step : [0..10] init 0;

	[] (step = 0) -> (0.1): (step'=1) + 0.1: (step'=2) + 0.1: (step'=3) + 0.1: (step'=4) + 0.1: (step'=5) + 0.1: (step'=6) + 0.1: (step'=7) + 0.1: (step'=8) + 0.1: (step'=9) + 0.1: (step'=10);

	[] (0<step & step<=2 & c=0 & x<N) -> (0.0000001):(c'=1) + (0.9999999):(x'=x+step);
	[] (2<step & step<=4 & c=0 & x<N) -> (0.0000002):(c'=1) + (0.9999998):(x'=x+step);
	[] (4<step & step<=6 & c=0 & x<N) -> (0.0000003):(c'=1) + (0.9999997):(x'=x+step);
	[] (6<step & step<=8 & c=0 & x<N) -> (0.0000004):(c'=1) + (0.9999996):(x'=x+step);
	[] (8<step & step<=10 & c=0 & x<N) -> (0.0000005):(c'=1) + (0.9999995):(x'=x+step);


endmodule


label "goal" = c=1;