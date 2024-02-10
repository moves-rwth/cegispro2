import signal
from cegispro2.cmd import _main as cegis
import subprocess


prefix = "/Users/kevinbatz/Desktop/Arbeit/kevinbatz/Projects/InvSysCegis/cegispro2/cegispro2/benchmarks/TACAS23_ABSYNTH/"
pickledir = "/Users/kevinbatz/Desktop/Arbeit/kevinbatz/Projects/InvSysCegis/cegispro2/cegispro2/benchmarks/TACAS23_ABSYNTH/results_cegispro"
cegisprodir = "/Users/kevinbatz/Desktop/Arbeit/kevinbatz/Projects/InvSysCegis/cegispro2/"
timeout = 10*60 # 10 min TO


#absynth_benchmarks =  #["bayesian_network.imp.pgcl",
absynth_benchmarks = ['"bayesian_network.imp.pgcl" --initialstates "[0<n]"',
                      '"ber.imp.pgcl" --initialstates "[x<n]"',
                      '"cowboy_duel.imp.pgcl" --initialstates "[0<flag]"',
                      '"C4B_t09.imp.pgcl" --initialstates "[j<x]"',
                      '"C4B_t13.imp.pgcl" --initialstates "[0<x & phase=0]"',
                      '"C4B_t19.imp.pgcl" --initialstates "[phase=0 & 100<i]"',
                      '"C4B_t61.imp.pgcl" --initialstates "[phase=0 & 8<=l]"',
                    '"condand.imp.pgcl" --initialstates "[(0 < n & 0 < m)]"',
                      '"coupon.imp.pgcl" --initialstates "[i<5]"',
                      '"fcall.imp.pgcl" --initialstates "[x<n]"',
                      '"filling_vol.imp.pgcl" --initialstates "[volMeasured <= volToFill]"',
                      '"geo.imp.pgcl" --initialstates "[term=0]"',
                    '"linear01.imp.pgcl" --initialstates "[2<=x]"',
                      '"trapped_miner.imp.pgcl" --initialstates "[i < n & phase =0]"',
                      '"no_loop.imp.pgcl" --initialstates "[term=0]"',
                      '"prdwalk.imp.pgcl" --initialstates "[x<n]"',
                      '"prseq.imp.pgcl" --initialstates "[phase=0 & 2 < x-y]"',
                      '"prspeed.imp.pgcl" --initialstates "[x + 3 <= n]"',
                    '"race.imp.pgcl" --initialstates "[h <= t]"',
                      '"rejection_sampling.imp.pgcl" --initialstates "[0 < n & phase =0]"',
                      '"rfind_mc.imp.pgcl" --initialstates "[i<k & 0 < flag]"',
                      '"rfind_lv.imp.pgcl" --initialstates "[0 < flag]"',
                      '"rdseql.imp.pgcl" --initialstates "[0<x & phase=0]"',
                      '"rdspeed.imp.pgcl" --initialstates "[x + 3 <= n]"',
                      '"sprdwalk.imp.pgcl" --initialstates "[x < n]"']
print(len(absynth_benchmarks))

# for timeouts
def handler(signum, frame):
    print("TO")
    raise Exception("TO")



def run_with_to(to_in_secs, proc, arg_list):
    signal.signal(signal.SIGALRM, handler)
    signal.alarm(to_in_secs)

    try:
        proc(*arg_list)
    except Exception as ex:
        print('TO: %s' % str(ex))

    signal.alarm(0)





def run_cegis_benchmarks():
    act_venv_string = "source " + cegisprodir + "venv/bin/activate"

    for prog in absynth_benchmarks:
        #program, post, prop, template, validate, verifier, distance, templaterefiner,
        #partitionfactor, usemotzkin, optimizing_synthesizer, debuglog, exporttemplate, oneshot, invarianttype, cdb):
        #run_with_to(100, cegis, [prog, post, prop, "", False, "distance", 1, "inductivity", 1, False, False, False, False, False, "sub", False, pickledir])

        print("Benchmark %s (PAST)" % prog)

        to_exec = ("python3 " \
                  + cegisprodir \
                  + 'cegispro2/cmd.py ' \
                    '%s ' \
                    '--post "" ' \
                    '--prop "" ' \
                    '--template "" --novalidate --verifier distance --distance 1 --templaterefiner inductivity --nousemotzkin --nodebuglog --invarianttype past ' \
                    '--nocdb --safestatistics "' + prefix + 'results_cegispro/"') % (prefix + prog)

        try:
            subprocess.call(act_venv_string + "; " + to_exec , shell = True, timeout = timeout)
        except Exception:
            pass

        print("\n\n")

run_cegis_benchmarks()
