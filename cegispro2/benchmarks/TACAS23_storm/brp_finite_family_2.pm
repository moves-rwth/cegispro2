dtmc


const maxx = 5;
const max_sent = 8000000;


module brp

	sent : [0..max_sent];
	failed : [0..maxx];
	to_send : [0..max_sent];

	[] (failed<maxx & sent < to_send) -> 0.99 : (failed'=0)&(sent'=sent+1) + 0.01 : (failed'=failed+1);

endmodule

init sent = 0 & failed = 0 endinit

label "goal" = failed=maxx;

