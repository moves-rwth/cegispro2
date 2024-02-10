import click
import os
import subprocess
import shutil
import csv
from os.path import exists
import pickle

dirname = os.path.dirname(__file__)
filename = os.path.join(dirname, 'relative/path/to/file/you/want')

#overall_prefix = "/home/cegis/Desktop/cegispro2"
overall_prefix = dirname + "/../../../../../"


@click.option(
    '--run',
    type=click.Choice(['all', 'storm', 'absynth', 'exist', 'soundlower']),
    default="all",
    help = "Which benchmark set to run. 'all' runs all benchmarks. 'storm' runs benchmarks from Figure 4.a (and Table 2), 'absynth' runs benchmarks from Figure 4.b (and Table 3), 'exist' runs benchmarks from Figure 4.c (and Table 4), and 'soundlower' runs benchmarks From Figure 4.d sound bounds (also see column 'cegissound' in file scatter_soundlower.csv in the root directory of the artifact.)"
)
@click.option(
    '--specific',
    type = click.STRING,
    default = '',
    help = "For running specific benchmarks from Table 2 (comparison with storm) in case --run storm is set. Set this option to 'i.j' For runnning the benchmark from row i (starting with 0) and column j (j=0 is induct.-guided, j=1 is static, j=2 is dynamic)."
)
@click.option(
    '--selected/--noselected',
    default = True,
    help = "Whether to include benchmarks that time out. --selected runs only those benchmarks that do *not* timeout. --noselect runs all benchmarks."
)
@click.option(
    '--maxto',
    type=click.INT,
    default =  60 * 60 * 2,
    help="Specify a maximal timeout M in seconds. The timeout used for each benchmark B will be the minimum of M and the timeout used for the set of benchmarks B belongs to.")
def _main(run, specific, selected, maxto):

    #pickledir = overall_prefix + "cegispro2/benchmarks/scripts/TACAS23/AEC/pickles/exist/"
    pickledir = overall_prefix + "cegispro2/benchmarks/scripts/TACAS23/AEC/"

    if not exists(pickledir + "pickles"):
        os.mkdir(pickledir + "pickles")

    if not exists(pickledir + "pickles/absynth"):
        os.mkdir(pickledir + "pickles/absynth")

    if not exists(pickledir + "pickles/storm"):
        os.mkdir(pickledir + "pickles/storm")

    if not exists(pickledir + "pickles/exist"):
        os.mkdir(pickledir + "pickles/exist")

    if not exists(pickledir + "pickles/exist/cdb"):
        os.mkdir(pickledir + "pickles/exist/cdb")

    if not exists(pickledir + "pickles/exist/past"):
        os.mkdir(pickledir + "pickles/exist/past")

    if not exists(pickledir + "pickles/exist/sub"):
        os.mkdir(pickledir + "pickles/exist/sub")


    #print(dirname)
    if run == "all" or run == "exist":
        run_exist_benchmarks_unsound(selected, maxto)

    if run == "all" or run == "soundlower":
        run_exist_benchmarks_sound(selected, maxto)

    if run == "all" or run == "absynth":
        run_abysnth_benchmarks(selected, maxto)

    if run == "all" or run == "storm":
        if run == "all":
            run_storm_benchmarks(selected, maxto)
        else:
            specific_row = int(specific.split(".")[0])
            specific_column = int(specific.split(".")[1])
            run_storm_benchmarks(selected, maxto, specific_row, specific_column)




def run_exist_benchmarks_unsound(selected, maxto):

    print('---------------- Running EXIST Benchmarks (sub-invariants only) ---------------- ')

    timeout = min(5 * 60, maxto)  # 5 min TO according to table
    #timeout = 5

    prefix = overall_prefix + "cegispro2/benchmarks/TACAS23_EXIST/"
    act_venv_string = "source " + overall_prefix + "venv/bin/activate"
    pickledir = overall_prefix + "cegispro2/benchmarks/scripts/TACAS23/AEC/pickles/exist/"


    #delete all files in pickledir
    for f in os.listdir(pickledir + "sub"):
        os.remove(os.path.join(pickledir + "sub", f))

    exist_benchmarks = [("BiasDir1_0.pgcl", "x", "[not (x=y)]*x+[x=y]*0", True),
                        ("BiasDir1_1.pgcl", "x", "[x=y]*0.5+[not (x=y)]*0", True),
                        ("BiasDir2_0.pgcl", "x", "[not (x=y)]*x+[x=y]*0", True),
                        ("BiasDir2_1.pgcl", "x", "[x=y]*0.5+[not (x=y)]*0", True),
                        ("BiasDir3_0.pgcl", "x", "[not (x=y)]*x+[x=y]*0", True),
                        ("BiasDir3_1.pgcl", "x", "[x=y]*0.5+[not (x=y)]*0", True),
                        ("Bin01_0.pgcl", "x", "x", True),
                        ("Bin02_0.pgcl", "x", "x", True),
                        ("Bin03_0.pgcl", "x", "x", True),
                        ( "Bin11_0.pgcl", "x", "x", True),
                        ("Bin11_1.pgcl", "x", "[n<M]*(x+0.5*M-0.5*n) + [not (n<M)]*x", True),
                        ("Bin12_0.pgcl", "x", "x", True),
                        ("Bin12_1.pgcl", "x", "[n<M]*(x+0.1*M-0.1*n) + [not (n<M)]*x", True),
                        ("Bin13_0.pgcl", "x", "x", True),
                        ("Bin13_1.pgcl", "x", "[n<M]*(x+0.9*M-0.9*n) + [not (n<M)]*x", True),
                        ("Bin21_0.pgcl", "x", "x", True),
                        ("Detm1_0.pgcl", "count", "count", True),
                        ("Detm1_1.pgcl", "count", "[x<=10]*(count + 1) + [10 < x]*count", True),
                        ("Duel1_0.pgcl", "t", "[c=1 & t<=1 & c<= 1]*(1 - (15/19)*c)", True),
                        ("Duel2_0.pgcl", "t", "[c=1 & t<=1 & c<= 1]*(1 - (5/11)*c)", True),
                        ("Fair1_0.pgcl", "count", "count", True),
                        ("Fair1_1.pgcl", "count", "[c1 + c2 = 0]*(1+count) + [not (c1 + c2 = 0)]*count", True),
                        ("Gambler01_0.pgcl", "z", "z", True),
                        ("Geo01_0.pgcl", "z", "z", True),
                        ("Geo01_1.pgcl", "z", "[flip=0]*0.5", True),
                        ("Geo01_2.pgcl", "z", "[flip=0]*(z+0.5) + [not (flip=0)]*z", True),
                        ("Geo11_0.pgcl", "z", "z", True),
                        ("Geo21_0.pgcl", "z", "z", True),
                        ("GeoAr01_0.pgcl", "x", "x", True),
                        ("GeoAr01_1.pgcl", "x", "[not (z=0)]*(x + y) + [z=0]*x", True),
                        ("LinExp1_0.pgcl", "z", "[0<n]*(2*n) + [not (0<n)]*z", True),
                        ("LinExp1_1.pgcl", "z", "[0<n]*(z+2) + [not (0<n)]*z", True),
                        ("PrinSys1_0.pgcl", "[x=2] + [not (x=2)]*0", "[x=2]", True),
                        ("RevBin1_0.pgcl", "z", "[0<x]*(x+z)+[not (0<x)]*z", True),
                        ("RevBin1_1.pgcl", "z", "z", True),
                        ("Sum01_0.pgcl", "x", "[0<n]*(x+0.5*n*0.5)+[not (0<n)]*x", True),
                        ("Mart1_0.pgcl", "rounds", "rounds", False),
                        ("Mart1_1.pgcl", "rounds", "[0<b]*(1+rounds)+[not (0<b)]*rounds", False)
                        ]

    #open csv in truncating mode

    file = open(pickledir + "../../exist_sub.csv", "w")
    writer = csv.writer(file)
    writer.writerow(["Prog", "|S'|", "t"])

    for (prog, post, prop, select) in exist_benchmarks:
        #program, post, prop, template, validate, verifier, distance, templaterefiner,
        #partitionfactor, usemotzkin, optimizing_synthesizer, debuglog, exporttemplate, oneshot, invarianttype, cdb):
        #run_with_to(100, cegis, [prog, post, prop, "", False, "distance", 1, "inductivity", 1, False, False, False, False, False, "sub", False, pickledir])

        print("Benchmark %s     -- post= %s  -- prop = %s " % (prog,post,prop))

        #to_exec = ('cd "' + overall_prefix[:-1] + '"; python3 cegispro2/cmd.py ' \
        to_exec = ('cd "' + overall_prefix[:-1] + '"; python3 -m cegispro2.cmd ' \
                       + '"%s" ' \
                     '--post "%s" ' \
                     '--prop "%s" ' \
                     '--template "" --novalidate --verifier distance --distance 1 --templaterefiner inductivity --nousemotzkin --nodebuglog --invarianttype sub ' \
                     '--nocdb --safestatistics "' + pickledir + 'sub/"') % (prefix + prog, post, prop)

        try:
            if select or not selected:
                #subprocess.call(act_venv_string + "; " + to_exec , shell = True, timeout = timeout,executable='/bin/bash')
                subprocess.call(to_exec, shell=True, timeout=timeout, executable='/bin/bash')

            # on success, open pickle
            path = pickledir + "sub/" + prog + ".pickle"
            print(path)
            if exists(path):
                with open(path, 'rb') as pickle_file:
                    statistics = pickle.load(pickle_file)
                    cegispro_res_time = str(statistics.total_time).split(" ")[0]
                    cegispro_res_num_cits = str(statistics.num_ctis)
                    writer.writerow([prog, cegispro_res_time, cegispro_res_num_cits])
            else:
                writer.writerow([prog, "-", "MO/TO"])


        except Exception as e:
            writer.writerow([prog, "-", "MO/TO"])

        print("\n\n")


    file.close()


def run_exist_benchmarks_sound(selected, maxto):
    print('---------------- Running EXIST Benchmarks (sub-invariants with c.d.b. benchmarks + PAST benchmarks) ---------------- ')

    timeout = min(5 * 60, maxto)  # 5 min TO according to table
    #timeout = 5

    prefix = overall_prefix + "cegispro2/benchmarks/TACAS23_EXIST/"
    act_venv_string = "source " + overall_prefix + "venv/bin/activate"
    pickledir = overall_prefix + "cegispro2/benchmarks/scripts/TACAS23/AEC/pickles/exist/"

    # delete all files in pickledir
    for f in os.listdir(pickledir + "cdb"):
        os.remove(os.path.join(pickledir + "cdb", f))

    # delete all files in pickledir
    for f in os.listdir(pickledir + "past"):
        os.remove(os.path.join(pickledir + "past", f))

    exist_benchmarks = [("BiasDir1_0.pgcl", "x", "[not (x=y)]*x+[x=y]*0", True),
                        ("BiasDir1_1.pgcl", "x", "[x=y]*0.5+[not (x=y)]*0", True),
                        ("BiasDir2_0.pgcl", "x", "[not (x=y)]*x+[x=y]*0", True),
                        ("BiasDir2_1.pgcl", "x", "[x=y]*0.5+[not (x=y)]*0", True),
                        ("BiasDir3_0.pgcl", "x", "[not (x=y)]*x+[x=y]*0", True),
                        ("BiasDir3_1.pgcl", "x", "[x=y]*0.5+[not (x=y)]*0", True),
                        ("Bin01_0.pgcl", "x", "x", False),
                        ("Bin02_0.pgcl", "x", "x", False),
                        ("Bin03_0.pgcl", "x", "x", False),
                        ("Bin11_0.pgcl", "x", "x", True),
                        ("Bin11_1.pgcl", "x", "[n<M]*(x+0.5*M-0.5*n) + [not (n<M)]*x", True),
                        ("Bin12_0.pgcl", "x", "x", True),
                        ("Bin12_1.pgcl", "x", "[n<M]*(x+0.1*M-0.1*n) + [not (n<M)]*x", True),
                        ("Bin13_0.pgcl", "x", "x", True),
                        ("Bin13_1.pgcl", "x", "[n<M]*(x+0.9*M-0.9*n) + [not (n<M)]*x", True),
                        ("Bin21_0.pgcl", "x", "x", False),
                        ("Detm1_0.pgcl", "count", "count", True),
                        ("Detm1_1.pgcl", "count", "[x<=10]*(count + 1) + [10 < x]*count", True),
                        ("Duel1_0.pgcl", "t", "[c=1 & t<=1 & c<= 1]*(1 - (15/19)*c)", True),
                        ("Duel2_0.pgcl", "t", "[c=1 & t<=1 & c<= 1]*(1 - (5/11)*c)", True),
                        ("Fair1_0.pgcl", "count", "count", True),
                        ("Fair1_1.pgcl", "count", "[c1 + c2 = 0]*(1+count) + [not (c1 + c2 = 0)]*count", True),
                        ("Gambler01_0.pgcl", "z", "z", False),
                        ("Geo01_0.pgcl", "z", "z", True),
                        ("Geo01_1.pgcl", "z", "[flip=0]*0.5", False),
                        ("Geo01_2.pgcl", "z", "[flip=0]*(z+0.5) + [not (flip=0)]*z", True),
                        ("Geo11_0.pgcl", "z", "z", True),
                        ("Geo21_0.pgcl", "z", "z", True),
                        ("GeoAr01_0.pgcl", "x", "x", False),
                        ("GeoAr01_1.pgcl", "x", "[not (z=0)]*(x + y) + [z=0]*x", False),
                        ("LinExp1_0.pgcl", "z", "[0<n]*(2*n) + [not (0<n)]*z", False),
                        ("LinExp1_1.pgcl", "z", "[0<n]*(z+2) + [not (0<n)]*z", False),
                        ("PrinSys1_0.pgcl", "[x=2] + [not (x=2)]*0", "[x=2]", True),
                        ("RevBin1_0.pgcl", "z", "[0<x]*(x+z)+[not (0<x)]*z", True),
                        ("RevBin1_1.pgcl", "z", "z", True),
                        ("Sum01_0.pgcl", "x", "[0<n]*(x+0.5*n*0.5)+[not (0<n)]*x", False),
                        ("Mart1_0.pgcl", "rounds", "rounds", False),
                        ("Mart1_1.pgcl", "rounds", "[0<b]*(1+rounds)+[not (0<b)]*rounds", False)
                        ]

    for (prog, post, prop, select) in exist_benchmarks:
        # program, post, prop, template, validate, verifier, distance, templaterefiner,
        # partitionfactor, usemotzkin, optimizing_synthesizer, debuglog, exporttemplate, oneshot, invarianttype, cdb):
        # run_with_to(100, cegis, [prog, post, prop, "", False, "distance", 1, "inductivity", 1, False, False, False, False, False, "sub", False, pickledir])

        print("Benchmark %s     -- post= %s  -- prop = %s " % (prog, post, prop))

        # to_exec = ('cd "'+ overall_prefix[:-1] + '"; poetry run ' \
        #          + 'cegispro2 ' \
        #            '"%s" ' \
        #            '--post "%s" ' \
        #            '--prop "%s" ' \
        #            '--template "" --novalidate --verifier distance --distance 1 --templaterefiner inductivity --nousemotzkin --nodebuglog --invarianttype sub ' \
        #            '--nocdb --safestatistics "' + pickledir + '"') % (prog, post, prop)

        to_exec = ('cd "' + overall_prefix[:-1] + '"; python3 -m cegispro2.cmd ' \
                   + '"%s" ' \
                    '--post "%s" ' \
                    '--prop "%s" ' \
                    '--template "" --novalidate --verifier distance --distance 1 --templaterefiner inductivity --nousemotzkin --nodebuglog --invarianttype sub ' \
                    '--cdb --safestatistics "' + pickledir + 'cdb/"') % (prefix + prog, post, prop)

        try:
            if select or not selected:
                #subprocess.call(act_venv_string + "; " + to_exec, shell=True, timeout=timeout, executable='/bin/bash')
                subprocess.call(to_exec, shell=True, timeout=timeout, executable='/bin/bash')

        except Exception as e:
            print("TO! %s" % str(e))

        print("\n\n")


    for (prog, post, prop, select) in exist_benchmarks:
        # program, post, prop, template, validate, verifier, distance, templaterefiner,
        # partitionfactor, usemotzkin, optimizing_synthesizer, debuglog, exporttemplate, oneshot, invarianttype, cdb):
        # run_with_to(100, cegis, [prog, post, prop, "", False, "distance", 1, "inductivity", 1, False, False, False, False, False, "sub", False, pickledir])

        print("Benchmark %s     -- post= %s  -- prop = %s " % (prog, post, prop))

        # to_exec = ('cd "'+ overall_prefix[:-1] + '"; poetry run ' \
        #          + 'cegispro2 ' \
        #            '"%s" ' \
        #            '--post "%s" ' \
        #            '--prop "%s" ' \
        #            '--template "" --novalidate --verifier distance --distance 1 --templaterefiner inductivity --nousemotzkin --nodebuglog --invarianttype sub ' \
        #            '--nocdb --safestatistics "' + pickledir + '"') % (prog, post, prop)

        to_exec = ('cd "' + overall_prefix[:-1] + '"; python3 -m cegispro2.cmd ' \
                   + '"%s" ' \
                    '--post "%s" ' \
                         '--prop "%s" ' \
                         '--template "" --novalidate --verifier distance --distance 1 --templaterefiner inductivity --nousemotzkin --nodebuglog --invarianttype past ' \
                         '--nocdb --safestatistics "' + pickledir + 'past/"') % (prefix + prog, post, prop)

        try:
            if select or not selected:
                #subprocess.call(act_venv_string + "; " + to_exec, shell=True, timeout=timeout, executable='/bin/bash')
                subprocess.call(to_exec, shell=True, timeout=timeout, executable='/bin/bash')

        except Exception as e:
            print("TO! %s" % str(e))

        print("\n\n")



    file = open(pickledir + "../../exist_sound.csv", "w")
    writer = csv.writer(file)
    writer.writerow(["Prog", "t"])

    for (prog, prop, post, select) in exist_benchmarks:
        path = pickledir + "past/" + prog + ".pickle"
        #print(path)
        #path = prefix + "results_cegispro_past/" + bench + ".pgcl.pickle"
        if exists(path):
            with open(path, 'rb') as pickle_file:
                statistics = pickle.load(pickle_file)
                #print(str(statistics.total_time).split(" ")[0])
                cegispro_res_sound = float(str(statistics.total_time).split(" ")[0])
                #print("past time: %s" % str(cegispro_res_sound))
            path = pickledir + "cdb/" + prog + ".pickle"
            if exists(path):
                with open(path, 'rb') as pickle_file:
                    statistics = pickle.load(pickle_file)
                    #print(str(statistics.total_time).split(" ")[0])
                    cegispro_res_sound += float(str(statistics.total_time).split(" ")[0])
                    #print("cdb time: %s" % str(cegispro_res))
            else:
                cegispro_res_sound = "TO/MO"
                #print("n1")

        else:
            cegispro_res_sound = "MO/TO"
            #print("n2")

        writer.writerow([prog, str(cegispro_res_sound)])

    file.close()


def run_abysnth_benchmarks(selected, maxto):
    print(
        '---------------- Running PAST Benchmarks  ---------------- ')

    timeout = min(20 * 60, maxto)  # 5 min TO according to table

    prefix = overall_prefix + "cegispro2/benchmarks/TACAS23_ABSYNTH/"
    act_venv_string = "source " + overall_prefix + "venv/bin/activate"
    pickledir = overall_prefix + "cegispro2/benchmarks/scripts/TACAS23/AEC/pickles/"

    # delete all files in pickledir
    for f in os.listdir(pickledir + "absynth"):
        os.remove(os.path.join(pickledir + "absynth", f))

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

    file = open(pickledir + "../past.csv", "w")
    writer = csv.writer(file)
    writer.writerow(["Prog", "|S'|", "t", "bound"])

    for prog in absynth_benchmarks:
        # program, post, prop, template, validate, verifier, distance, templaterefiner,
        # partitionfactor, usemotzkin, optimizing_synthesizer, debuglog, exporttemplate, oneshot, invarianttype, cdb):
        # run_with_to(100, cegis, [prog, post, prop, "", False, "distance", 1, "inductivity", 1, False, False, False, False, False, "sub", False, pickledir])


        print("Benchmark %s  " % prog)

        # to_exec = ('cd "'+ overall_prefix[:-1] + '"; poetry run ' \
        #          + 'cegispro2 ' \
        #            '"%s" ' \
        #            '--post "%s" ' \
        #            '--prop "%s" ' \
        #            '--template "" --novalidate --verifier distance --distance 1 --templaterefiner inductivity --nousemotzkin --nodebuglog --invarianttype sub ' \
        #            '--nocdb --safestatistics "' + pickledir + '"') % (prog, post, prop)

        to_exec = ('cd "' + overall_prefix[:-1] + '"; python3 -m cegispro2.cmd ' \
                   + '%s ' \
                    '--post "" ' \
                    '--prop "" ' \
                    '--template "" --novalidate --verifier distance --distance 1 --templaterefiner inductivity --nousemotzkin --nodebuglog --invarianttype past ' \
                    '--nocdb --safestatistics "' + pickledir + 'absynth/"') % (prefix + prog)

        try:
            #subprocess.call(act_venv_string + "; " + to_exec , shell = True, timeout = timeout)
            subprocess.call(to_exec, shell=True, timeout=timeout)

            # on success, open pickle
            prog = prog.split('"')[1]
            path = pickledir + "absynth/" + prog + ".pickle"
            print(path)
            if exists(path):
                with open(path, 'rb') as pickle_file:
                    statistics = pickle.load(pickle_file)
                    cegispro_res_time = str(statistics.total_time).split(" ")[0]
                    cegispro_res_num_cits = str(statistics.num_ctis)
                    writer.writerow([prog, cegispro_res_num_cits, cegispro_res_time, statistics.bound])
            else:
                writer.writerow([prog, "-", "MO/TO", "-"])


        except Exception as e:
            print('TO (%s)' % str(e))
            writer.writerow([prog, "-", "MO/TO", "-"])

        print("\n\n")

    file.close()



def run_storm_benchmarks(selected, maxto, specific_row = None, specific_column = None):
    print("--------------------- Running Benchmarks for finite-state programs ------------------")
    storm_benchmarks = [
        ('cegispro2/benchmarks/TACAS23/bounded_rw_multi_step.pgcl ',
         '--post  "[x=200000] + [not (x=200000)]*0" --prop "[x=1]*0.4" --templaterefiner inductivity --nousemotzkin', True),

        ('cegispro2/benchmarks/TACAS23/bounded_rw_multi_step.pgcl ',
         '--post  "[x=200000] + [not (x=200000)]*0" --prop "[x=1]*0.4" --templaterefiner fixed --nousemotzkin', False),

        ('cegispro2/benchmarks/TACAS23/bounded_rw_multi_step.pgcl ',
         '--post  "[x=200000] + [not (x=200000)]*0" --prop "[x=1]*0.4" --templaterefiner variable --nousemotzkin', False),

        ('cegispro2/benchmarks/TACAS23/bounded_rw_multi_step.pgcl ',
         '--post  "[x=200000] + [not (x=200000)]*0" --prop "[x=1]*0.3" --templaterefiner inductivity --nousemotzkin', True),

        ('cegispro2/benchmarks/TACAS23/bounded_rw_multi_step.pgcl ',
         '--post  "[x=200000] + [not (x=200000)]*0" --prop "[x=1]*0.3" --templaterefiner fixed --nousemotzkin', False),

        ('cegispro2/benchmarks/TACAS23/bounded_rw_multi_step.pgcl ',
         '--post  "[x=200000] + [not (x=200000)]*0" --prop "[x=1]*0.3" --templaterefiner variable --nousemotzkin', False),

        ('cegispro2/benchmarks/TACAS23/bounded_rw_multi_step.pgcl ',
         '--post  "[x=200000] + [not (x=200000)]*0" --prop "[x=1]*0.2" --templaterefiner inductivity --nousemotzkin', False),

        ('cegispro2/benchmarks/TACAS23/bounded_rw_multi_step.pgcl ',
         '--post  "[x=200000] + [not (x=200000)]*0" --prop "[x=1]*0.2" --templaterefiner fixed --nousemotzkin', False),

        ('cegispro2/benchmarks/TACAS23/bounded_rw_multi_step.pgcl ',
         '--post  "[x=200000] + [not (x=200000)]*0" --prop "[x=1]*0.2" --templaterefiner variable --nousemotzkin', False),

        ('cegispro2/benchmarks/TACAS23/brp.pgcl ',
         '--post  "[failed=10] + [not (failed=10)]*0" --prop "[failed<=0 & sent<=0]*0.001" --templaterefiner inductivity --nousemotzkin', True),

        ('cegispro2/benchmarks/TACAS23/brp.pgcl ',
         '--post  "[failed=10] + [not (failed=10)]*0" --prop "[failed<=0 & sent<=0]*0.001" --templaterefiner fixed --nousemotzkin', True),

        ('cegispro2/benchmarks/TACAS23/brp.pgcl ',
         '--post  "[failed=10] + [not (failed=10)]*0" --prop "[failed<=0 & sent<=0]*0.001" --templaterefiner variable --nousemotzkin', False),

        ('cegispro2/benchmarks/TACAS23/brp.pgcl ',
         '--post  "[failed=10] + [not (failed=10)]*0" --prop "[failed<=0 & sent<=0]*0.0001" --templaterefiner inductivity --nousemotzkin', True),

        ('cegispro2/benchmarks/TACAS23/brp.pgcl ',
         '--post  "[failed=10] + [not (failed=10)]*0" --prop "[failed<=0 & sent<=0]*0.0001" --templaterefiner fixed --nousemotzkin', True),

        ('cegispro2/benchmarks/TACAS23/brp.pgcl ',
         '--post  "[failed=10] + [not (failed=10)]*0" --prop "[failed<=0 & sent<=0]*0.0001" --templaterefiner variable --nousemotzkin', False),

        ('cegispro2/benchmarks/TACAS23/brp.pgcl ',
         '--post  "[failed=10] + [not (failed=10)]*0" --prop "[failed<=0 & sent<=0]*0.00001" --templaterefiner inductivity --nousemotzkin', True),

        ('cegispro2/benchmarks/TACAS23/brp.pgcl ',
         '--post  "[failed=10] + [not (failed=10)]*0" --prop "[failed<=0 & sent<=0]*0.00001" --templaterefiner fixed --nousemotzkin', True),

        ('cegispro2/benchmarks/TACAS23/brp.pgcl ',
         '--post  "[failed=10] + [not (failed=10)]*0" --prop "[failed<=0 & sent<=0]*0.00001" --templaterefiner variable --nousemotzkin', False),

        ('cegispro2/benchmarks/TACAS23/brp_finite_family.pgcl ',
         '--post  "[failed=5] + [not (failed=5)]*0" --prop "[failed<=0 & sent<=0]*0.05" --templaterefiner inductivity --nousemotzkin', True),

        ('cegispro2/benchmarks/TACAS23/brp_finite_family.pgcl ',
         '--post  "[failed=5] + [not (failed=5)]*0" --prop "[failed<=0 & sent<=0]*0.05" --templaterefiner fixed --nousemotzkin', True),

        ('cegispro2/benchmarks/TACAS23/brp_finite_family.pgcl ',
         '--post  "[failed=5] + [not (failed=5)]*0" --prop "[failed<=0 & sent<=0]*0.05" --templaterefiner variable --nousemotzkin', True),

        ('cegispro2/benchmarks/TACAS23/brp_finite_family.pgcl ',
         '--post  "[failed=5] + [not (failed=5)]*0" --prop "[failed<=0 & sent<=0]*0.01" --templaterefiner inductivity --nousemotzkin', True),

        ('cegispro2/benchmarks/TACAS23/brp_finite_family.pgcl ',
         '--post  "[failed=5] + [not (failed=5)]*0" --prop "[failed<=0 & sent<=0]*0.01" --templaterefiner fixed --nousemotzkin', True),

        ('cegispro2/benchmarks/TACAS23/brp_finite_family.pgcl ',
         '--post  "[failed=5] + [not (failed=5)]*0" --prop "[failed<=0 & sent<=0]*0.01" --templaterefiner variable --nousemotzkin', False),

        ('cegispro2/benchmarks/TACAS23/brp_finite_family.pgcl ',
         '--post  "[failed=5] + [not (failed=5)]*0" --prop "[failed<=0 & sent<=0]*0.005" --templaterefiner inductivity --nousemotzkin', True),

        ('cegispro2/benchmarks/TACAS23/brp_finite_family.pgcl ',
         '--post  "[failed=5] + [not (failed=5)]*0" --prop "[failed<=0 & sent<=0]*0.005" --templaterefiner fixed --nousemotzkin', True),

        ('cegispro2/benchmarks/TACAS23/brp_finite_family.pgcl ',
         '--post  "[failed=5] + [not (failed=5)]*0" --prop "[failed<=0 & sent<=0]*0.005" --templaterefiner variable --nousemotzkin', False),

        ('cegispro2/benchmarks/TACAS23/chain.pgcl ',
         '--post  "[c=1] + [not (c=1)]*0" --prop "[c=0 & x=0]*0.8" --templaterefiner inductivity --nousemotzkin', True),

        ('cegispro2/benchmarks/TACAS23/chain.pgcl ',
         '--post  "[c=1] + [not (c=1)]*0" --prop "[c=0 & x=0]*0.8" --templaterefiner fixed --nousemotzkin', True),

        ('cegispro2/benchmarks/TACAS23/chain.pgcl ',
         '--post  "[c=1] + [not (c=1)]*0" --prop "[c=0 & x=0]*0.8" --templaterefiner variable --nousemotzkin', False),

        ('cegispro2/benchmarks/TACAS23/chain.pgcl ',
         '--post  "[c=1] + [not (c=1)]*0" --prop "[c=0 & x=0]*0.7" --templaterefiner inductivity --nousemotzkin', False),

        ('cegispro2/benchmarks/TACAS23/chain.pgcl ',
         '--post  "[c=1] + [not (c=1)]*0" --prop "[c=0 & x=0]*0.7" --templaterefiner fixed --nousemotzkin', True),

        ('cegispro2/benchmarks/TACAS23/chain.pgcl ',
         '--post  "[c=1] + [not (c=1)]*0" --prop "[c=0 & x=0]*0.7" --templaterefiner variable --nousemotzkin', False),

        ('cegispro2/benchmarks/TACAS23/chain.pgcl ',
         '--post  "[c=1] + [not (c=1)]*0" --prop "[c=0 & x=0]*0.641" --templaterefiner inductivity --nousemotzkin', False),

        ('cegispro2/benchmarks/TACAS23/chain.pgcl ',
         '--post  "[c=1] + [not (c=1)]*0" --prop "[c=0 & x=0]*0.641" --templaterefiner fixed --nousemotzkin', True),

        ('cegispro2/benchmarks/TACAS23/chain.pgcl ',
         '--post  "[c=1] + [not (c=1)]*0" --prop "[c=0 & x=0]*0.641" --templaterefiner variable --nousemotzkin', False),

        ('cegispro2/benchmarks/TACAS23/chain_select_stepsize.pgcl ',
         '--post  "[1<=c] + [c<1]*0" --prop "[c<=0 & x<=0 & step<=0]*0.7" --templaterefiner inductivity --nousemotzkin', True),

        ('cegispro2/benchmarks/TACAS23/chain_select_stepsize.pgcl ',
         '--post  "[1<=c] + [c<1]*0" --prop "[c<=0 & x<=0 & step<=0]*0.7" --templaterefiner fixed --nousemotzkin', True),

        ('cegispro2/benchmarks/TACAS23/chain_select_stepsize.pgcl ',
         '--post  "[1<=c] + [c<1]*0" --prop "[c<=0 & x<=0 & step<=0]*0.7" --templaterefiner variable --nousemotzkin', True),

        ('cegispro2/benchmarks/TACAS23/chain_select_stepsize.pgcl ',
         '--post  "[1<=c] + [c<1]*0" --prop "[c<=0 & x<=0 & step<=0]*0.6" --templaterefiner inductivity --nousemotzkin', False),

        ('cegispro2/benchmarks/TACAS23/chain_select_stepsize.pgcl ',
         '--post  "[1<=c] + [c<1]*0" --prop "[c<=0 & x<=0 & step<=0]*0.6" --templaterefiner fixed --nousemotzkin', True),

        ('cegispro2/benchmarks/TACAS23/chain_select_stepsize.pgcl ',
         '--post  "[1<=c] + [c<1]*0" --prop "[c<=0 & x<=0 & step<=0]*0.6" --templaterefiner variable --nousemotzkin', False),

        ('cegispro2/benchmarks/TACAS23/chain_select_stepsize.pgcl ',
         '--post  "[1<=c] + [c<1]*0" --prop "[c<=0 & x<=0 & step<=0]*0.55" --templaterefiner inductivity --nousemotzkin', False),

        ('cegispro2/benchmarks/TACAS23/chain_select_stepsize.pgcl ',
         '--post  "[1<=c] + [c<1]*0" --prop "[c<=0 & x<=0 & step<=0]*0.55" --templaterefiner fixed --nousemotzkin', True),

        ('cegispro2/benchmarks/TACAS23/chain_select_stepsize.pgcl ',
         '--post  "[1<=c] + [c<1]*0" --prop "[c<=0 & x<=0 & step<=0]*0.55" --templaterefiner variable --nousemotzkin', False),

        ('cegispro2/benchmarks/TACAS23/grid_big.pgcl ',
         '--post  "[a<1000 & 1000<=b] + [not (a<1000 & 1000<=b)]*0" --prop "[a<=0 & b<=0]*0.99" --templaterefiner inductivity --nousemotzkin', False),

        ('cegispro2/benchmarks/TACAS23/grid_big.pgcl ',
         '--post  "[a<1000 & 1000<=b] + [not (a<1000 & 1000<=b)]*0" --prop "[a<=0 & b<=0]*0.99" --templaterefiner fixed --nousemotzkin', False),

        ('cegispro2/benchmarks/TACAS23/grid_big.pgcl ',
         '--post  "[a<1000 & 1000<=b] + [not (a<1000 & 1000<=b)]*0" --prop "[a<=0 & b<=0]*0.99" --templaterefiner variable --nousemotzkin', False),

        ('cegispro2/benchmarks/TACAS23/grid_small.pgcl ',
         '--post  "[a<10 & 10<=b] + [not (a<10 & 10<=b)]*0" --prop "[a<=0 & b<=0]*0.8" --templaterefiner inductivity --nousemotzkin', True),

        ('cegispro2/benchmarks/TACAS23/grid_small.pgcl ',
         '--post  "[a<10 & 10<=b] + [not (a<10 & 10<=b)]*0" --prop "[a<=0 & b<=0]*0.8" --templaterefiner fixed --nousemotzkin', True),

        ('cegispro2/benchmarks/TACAS23/grid_small.pgcl ',
         '--post  "[a<10 & 10<=b] + [not (a<10 & 10<=b)]*0" --prop "[a<=0 & b<=0]*0.8" --templaterefiner variable --nousemotzkin', True),

        ('cegispro2/benchmarks/TACAS23/grid_small.pgcl ',
         '--post  "[a<10 & 10<=b] + [not (a<10 & 10<=b)]*0" --prop "[a<=0 & b<=0]*0.7" --templaterefiner inductivity --nousemotzkin', True),

        ('cegispro2/benchmarks/TACAS23/grid_small.pgcl ',
         '--post  "[a<10 & 10<=b] + [not (a<10 & 10<=b)]*0" --prop "[a<=0 & b<=0]*0.7" --templaterefiner fixed --nousemotzkin', True),

        ('cegispro2/benchmarks/TACAS23/grid_small.pgcl ',
         '--post  "[a<10 & 10<=b] + [not (a<10 & 10<=b)]*0" --prop "[a<=0 & b<=0]*0.7" --templaterefiner variable --nousemotzkin', True),

        ('cegispro2/benchmarks/TACAS23/zero_conf.pgcl ',
         '--post  "[established=1] + [not (established=1)]*0" --prop "[start=1 & established=0 & curprobe=0]*0.53" --templaterefiner inductivity --nousemotzkin', True),

        ('cegispro2/benchmarks/TACAS23/zero_conf.pgcl ',
         '--post  "[established=1] + [not (established=1)]*0" --prop "[start=1 & established=0 & curprobe=0]*0.53" --templaterefiner fixed --nousemotzkin', True),

        ('cegispro2/benchmarks/TACAS23/zero_conf.pgcl ',
         '--post  "[established=1] + [not (established=1)]*0" --prop "[start=1 & established=0 & curprobe=0]*0.53" --templaterefiner variable --nousemotzkin', True),

        ('cegispro2/benchmarks/TACAS23/zero_conf.pgcl ',
         '--post  "[established=1] + [not (established=1)]*0" --prop "[start=1 & established=0 & curprobe=0]*0.526" --templaterefiner inductivity --nousemotzkin', True),

        ('cegispro2/benchmarks/TACAS23/zero_conf.pgcl ',
         '--post  "[established=1] + [not (established=1)]*0" --prop "[start=1 & established=0 & curprobe=0]*0.526" --templaterefiner fixed --nousemotzkin', True),

        ('cegispro2/benchmarks/TACAS23/zero_conf.pgcl ',
         '--post  "[established=1] + [not (established=1)]*0" --prop "[start=1 & established=0 & curprobe=0]*0.526" --templaterefiner variable --nousemotzkin', True),

        ('cegispro2/benchmarks/TACAS23/zero_conf.pgcl ',
         '--post  "[established=1] + [not (established=1)]*0" --prop "[start=1 & established=0 & curprobe=0]*0.5251" --templaterefiner inductivity --nousemotzkin', False),

        ('cegispro2/benchmarks/TACAS23/zero_conf.pgcl ',
         '--post  "[established=1] + [not (established=1)]*0" --prop "[start=1 & established=0 & curprobe=0]*0.5251" --templaterefiner fixed --nousemotzkin', True),

        ('cegispro2/benchmarks/TACAS23/zero_conf.pgcl ',
         '--post  "[established=1] + [not (established=1)]*0" --prop "[start=1 & established=0 & curprobe=0]*0.5251" --templaterefiner variable --nousemotzkin', False),

        ('cegispro2/benchmarks/TACAS23/zero_conf_family.pgcl ',
         '--post  "[established=1] + [not (established=1)]*0" --prop "[start=1 & established=0 & curprobe=0]*0.6" --templaterefiner inductivity --nousemotzkin', True),

        ('cegispro2/benchmarks/TACAS23/zero_conf_family.pgcl ',
         '--post  "[established=1] + [not (established=1)]*0" --prop "[start=1 & established=0 & curprobe=0]*0.6" --templaterefiner fixed --nousemotzkin', True),

        ('cegispro2/benchmarks/TACAS23/zero_conf_family.pgcl ',
         '--post  "[established=1] + [not (established=1)]*0" --prop "[start=1 & established=0 & curprobe=0]*0.6" --templaterefiner variable --nousemotzkin', True),

        ('cegispro2/benchmarks/TACAS23/zero_conf_family.pgcl ',
         '--post  "[established=1] + [not (established=1)]*0" --prop "[start=1 & established=0 & curprobe=0]*0.555" --templaterefiner inductivity --nousemotzkin', False),

        ('cegispro2/benchmarks/TACAS23/zero_conf_family.pgcl ',
         '--post  "[established=1] + [not (established=1)]*0" --prop "[start=1 & established=0 & curprobe=0]*0.555" --templaterefiner fixed --nousemotzkin', True),

        ('cegispro2/benchmarks/TACAS23/zero_conf_family.pgcl ',
         '--post  "[established=1] + [not (established=1)]*0" --prop "[start=1 & established=0 & curprobe=0]*0.555" --templaterefiner variable --nousemotzkin', True),

        ('cegispro2/benchmarks/TACAS23/zero_conf_family.pgcl ',
         '--post  "[established=1] + [not (established=1)]*0" --prop "[start=1 & established=0 & curprobe=0]*0.553" --templaterefiner inductivity --nousemotzkin', False),

        ('cegispro2/benchmarks/TACAS23/zero_conf_family.pgcl ',
         '--post  "[established=1] + [not (established=1)]*0" --prop "[start=1 & established=0 & curprobe=0]*0.553" --templaterefiner fixed --nousemotzkin', True),

        ('cegispro2/benchmarks/TACAS23/zero_conf_family.pgcl ',
         '--post  "[established=1] + [not (established=1)]*0" --prop "[start=1 & established=0 & curprobe=0]*0.553" --templaterefiner variable --nousemotzkin', True),

    ]

    timeout = min(60 * 60 * 2, maxto)  # 5 min TO according to table
    act_venv_string = "source " + overall_prefix + "venv/bin/activate"
    pickledir = overall_prefix + "cegispro2/benchmarks/scripts/TACAS23/AEC/pickles/storm"

    if specific_row == None:
        # delete all directories in storms pickledir
        for root, dirs, files in os.walk(pickledir):
            for f in files:
                os.unlink(os.path.join(root, f))
            for d in dirs:
                shutil.rmtree(os.path.join(root, d))

        counter = 0
        for (prog, postprop, select) in storm_benchmarks:
            os.mkdir(pickledir + "/" + str(counter))
            counter += 1

        file = open(pickledir + "/../../storm.csv", "w")
        writer = csv.writer(file)
        writer.writerow(["Prog", "Induct.-Guided", "","", "", "Static", "", "", "", "Dynamic"])
        writer.writerow(["", "|S'|", "|I|" ,"t", "", "|S'|", "|I|" ,"t", "", "|S'|", "|I|" ,"t"])

        counter = 0
        columnoffset = 0
        for (prog, postprop, select) in storm_benchmarks:

            to_exec = ('cd "' + overall_prefix[:-1] + '"; python3 -m cegispro2.cmd ' \
                       + '%s ' \
                         '%s ' \
                         '--template "" --novalidate --verifier distance --distance 2 --nodebuglog --invarianttype super ' \
                         '--nocdb --safestatistics "' + pickledir + '/%s/"' ) % (overall_prefix + prog, postprop, str(counter))

            prog = prog.split("/")[3].split(" ")[0]

            if columnoffset == 0:
                if counter != 0:
                    writer.writerow(cur_row)
                cur_row = []
                cur_row.append(prog)
            else:
                cur_row.append("")


            try:
                if select or not selected:
                    #subprocess.call(act_venv_string + "; " + to_exec, shell=True, timeout=timeout)
                    subprocess.call(to_exec, shell=True, timeout=timeout)

                # on success, open pickle
                path = pickledir + ("/%s/" % str(counter)) + prog + ".pickle"
                print(path)
                if exists(path):
                    with open(path, 'rb') as pickle_file:
                        statistics = pickle.load(pickle_file)
                        cegispro_res_time = str(statistics.total_time).split(" ")[0]
                        cegispro_res_num_cits = str(statistics.num_ctis)
                        cur_row = cur_row + [cegispro_res_num_cits, str(statistics.num_template_expressions +1), cegispro_res_time]
                        #writer.writerow([prog, cegispro_res_time, cegispro_res_num_cits])
                else:
                    cur_row = cur_row + ["-", "-", "TO/MO"]


            except Exception as e:
                print("TO! (%s)" % str(e))
                cur_row = cur_row + ["-", "-", "TO/MO"]

            print("\n\n")


            counter += 1
            columnoffset = (columnoffset + 1) % 3


        if columnoffset == 0:
            if counter != 0:
                writer.writerow(cur_row)

        file.close()

    else:
        row_offset = specific_row * 3
        index = row_offset + specific_column

        (prog, postprop, select) = storm_benchmarks[index]

        to_exec = ('cd "' + overall_prefix[:-1] + '"; python3 -m cegispro2.cmd ' \
                   + '%s ' \
                     '%s ' \
                     '--template "" --novalidate --verifier distance --distance 2 --nodebuglog --invarianttype super ' \
                     '--nocdb') % (
                  overall_prefix + prog, postprop)
        subprocess.call(to_exec, shell=True, timeout=timeout)





main = click.command()(_main)
if __name__ == "__main__":
    main()