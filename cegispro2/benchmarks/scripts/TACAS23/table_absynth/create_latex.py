import csv
import pickle
from os.path import exists

prefix = "/Users/kevinbatz/Desktop/Arbeit/kevinbatz/Projects/InvSysCegis/cegispro2/cegispro2/benchmarks/TACAS23_ABSYNTH/"
pickledir = "/Users/kevinbatz/Desktop/Arbeit/kevinbatz/Projects/InvSysCegis/cegispro2/cegispro2/benchmarks/TACAS23_ABSYNTH/results_cegispro"
cegisprodir = "/Users/kevinbatz/Desktop/Arbeit/kevinbatz/Projects/InvSysCegis/cegispro2/"
timeout = 10*60 # 10 min TO


#absynth_benchmarks =  #["bayesian_network.imp.pgcl",
absynth_benchmarks = ["bayesian_network.imp.pgcl", "ber.imp.pgcl", "cowboy_duel.imp.pgcl",  "C4B_t09.imp.pgcl", "C4B_t13.imp.pgcl", "C4B_t19.imp.pgcl", "C4B_t61.imp.pgcl",
                    "condand.imp.pgcl", "coupon.imp.pgcl", "fcall.imp.pgcl", "filling_vol.imp.pgcl", "geo.imp.pgcl",
                    "linear01.imp.pgcl", "trapped_miner.imp.pgcl", "no_loop.imp.pgcl", "prdwalk.imp.pgcl", "prseq.imp.pgcl", "prspeed.imp.pgcl",
                    "race.imp.pgcl", "rejection_sampling.imp.pgcl", "rfind_mc.imp.pgcl","rfind_lv.imp.pgcl", "rdseql.imp.pgcl", "rdspeed.imp.pgcl", "sprdwalk.imp.pgcl"]

absynth_benchmarks = [bench.split(".pgcl")[0] for bench in absynth_benchmarks]


MOTO_tick = 500
ERR_tick = 1300
typestring = "dtmc"

file = open('benchmarks/TACAS23_ABSYNTH/scatter_absynth.csv', 'w', newline='\n')
csvwriter = csv.writer(file, delimiter=';', quotechar = '|', quoting=csv.QUOTE_MINIMAL)
csvwriter.writerow(["benchmark", "Type", "cegis", "absynth"])

# Create the csv file containing the runtimes
for bench in absynth_benchmarks:
    print("Bench: %s" % bench)
    # check if cegis statistics pickle exsists
    path = prefix + "results_cegispro/" + bench + ".pgcl.pickle"
    if exists(path):
        with open(path, 'rb') as pickle_file:
            statistics = pickle.load(pickle_file)
            cegispro_res = str(statistics.total_time).split(" ")[0]

    else:
        cegispro_res = MOTO_tick


    # search for the entry in the results
    absynth_res = ERR_tick
    with open(prefix + 'results_absynth/result.doc') as file:
        results_string = file.read()
        results_string = results_string.split("------------------------------------")
        count = 0
        for i in range(1,len(results_string),2):
            if results_string[i].splitlines()[1] == bench:
                try:
                    print("found %s = %s:" % (results_string[i].splitlines()[1], bench))
                    print(results_string[i+1].split("Total runtime: "))
                    time = results_string[i+1].split("Total runtime: ")[1].split("s")[0]
                    absynth_res = time
                except Exception:
                    absynth_res = ERR_tick
                break


    csvwriter.writerow([bench, typestring, cegispro_res, absynth_res])

    print("\n\n\n")

file.close()