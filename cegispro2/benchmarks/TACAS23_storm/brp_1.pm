dtmc


const maxx = 10;
const to_send = 8000000000;


module brp

	sent : [0..to_send] init 0;
	failed : [0..maxx] init 0;

	[] (failed<maxx & sent < to_send) -> 0.99 : (failed'=0)&(sent'=sent+1) + 0.01 : (failed'=failed+1);

endmodule



label "goal" = failed=maxx;

