dtmc

const min_probe = 100000000;
const max_probe = 200000000;


module zero_conf

	start : bool;
	established_ip: bool;
	num_probes: [min_probe..max_probe];
	cur_probe : [0..max_probe];

	[] (start = true & established_ip = false) -> (0.5): (start'=false) + (0.5) : (start'=false)&(established_ip'=true);
	[] (start = false & established_ip = false & cur_probe < num_probes) -> (0.999999999):(cur_probe'=cur_probe + 1) + (1-0.999999999):(start'=true)&(cur_probe'=0);

endmodule

init (cur_probe = 0 & start = true & established_ip = false & cur_probe= 0) endinit
label "goal" = established_ip=true;

