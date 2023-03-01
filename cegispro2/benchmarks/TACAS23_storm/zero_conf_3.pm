dtmc

const num_probes = 100000000;

module zero_conf

	start : bool init true;
	established_ip: bool init false;
	cur_probe : [0..num_probes] init 0;

	[] (start = true & established_ip = false) -> (0.5): (start'=false) + (0.5) : (start'=false)&(established_ip'=true);
	[] (start = false & established_ip = false & cur_probe < num_probes) -> (0.999999999):(cur_probe'=cur_probe + 1) + (1-0.999999999):(start'=true)&(cur_probe'=0);

endmodule

label "goal" = established_ip=true;

