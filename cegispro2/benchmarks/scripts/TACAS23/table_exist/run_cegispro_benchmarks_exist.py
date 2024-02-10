import signal
import subprocess


prefix = "/Users/kevinbatz/Desktop/Arbeit/kevinbatz/Projects/InvSysCegis/cegispro2/cegispro2/benchmarks/TACAS23_EXIST/"
pickledir = "/Users/kevinbatz/Desktop/Arbeit/kevinbatz/Projects/InvSysCegis/cegispro2/cegispro2/benchmarks/TACAS23_EXIST/results_cegispro"
cegisprodir = "/Users/kevinbatz/Desktop/Arbeit/kevinbatz/Projects/InvSysCegis/cegispro2/"

overall_prefix = "/Users/kevinbatz/Desktop/Arbeit/kevinbatz/Projects/InvSysCegis/cegispro2"
#overall_prefix = "/home/cegis/Desktop/cegispro2"
#prefix = overall_prefix + "/cegispro2/benchmarks/TACAS23_EXIST/"
#pickledir = overall_prefix + "/cegispro2/benchmarks/TACAS23_EXIST/results_cegispro"
#cegisprodir = overall_prefix + "/"

#timeout = 10*60 # 10 min TO
timeout = 5*60 # 20 sec

exist_benchmarks = [(prefix + "BiasDir1_0.pgcl", "x", "[not (x=y)]*x+[x=y]*0"),
                    (prefix + "BiasDir1_1.pgcl", "x", "[x=y]*0.5+[not (x=y)]*0"),
                    (prefix + "BiasDir2_0.pgcl", "x", "[not (x=y)]*x+[x=y]*0"),
                    (prefix + "BiasDir2_1.pgcl", "x", "[x=y]*0.5+[not (x=y)]*0"),
                    (prefix + "BiasDir3_0.pgcl", "x", "[not (x=y)]*x+[x=y]*0"),
                    (prefix + "BiasDir3_1.pgcl", "x", "[x=y]*0.5+[not (x=y)]*0"),
                    (prefix + "Bin01_0.pgcl", "x", "x"),
                    (prefix + "Bin02_0.pgcl", "x", "x"),
                    (prefix + "Bin03_0.pgcl", "x", "x"),
                    (prefix + "Bin11_0.pgcl", "x", "x"),
                    (prefix + "Bin11_1.pgcl", "x", "[n<M]*(x+0.5*M-0.5*n) + [not (n<M)]*x"),
                    (prefix + "Bin12_0.pgcl", "x", "x"),
                    (prefix + "Bin12_1.pgcl", "x", "[n<M]*(x+0.1*M-0.1*n) + [not (n<M)]*x"),
                    (prefix + "Bin13_0.pgcl", "x", "x"),
                    (prefix + "Bin13_1.pgcl", "x", "[n<M]*(x+0.9*M-0.9*n) + [not (n<M)]*x"),
                    (prefix + "Bin21_0.pgcl", "x", "x"),
                    (prefix + "Detm1_0.pgcl", "count", "count"),
                    (prefix + "Detm1_1.pgcl", "count", "[x<=10]*(count + 1) + [10 < x]*count"),
                    (prefix + "Duel1_0.pgcl", "t", "[c=1 & t<=1 & c<= 1]*(1 - (15/19)*c)"),
                    (prefix + "Duel2_0.pgcl", "t", "[c=1 & t<=1 & c<= 1]*(1 - (5/11)*c)"),
                    (prefix + "Fair1_0.pgcl", "count", "count"),
                    (prefix + "Fair1_1.pgcl", "count", "[c1 + c2 = 0]*(1+count) + [not (c1 + c2 = 0)]*count"),
                    (prefix + "Gambler01_0.pgcl", "z", "z"),
                    (prefix + "Geo01_0.pgcl", "z", "z"),
                    (prefix + "Geo01_1.pgcl", "z", "[flip=0]*0.5"),
                    (prefix + "Geo01_2.pgcl", "z", "[flip=0]*(z+0.5) + [not (flip=0)]*z"),
                    (prefix + "Geo11_0.pgcl", "z", "z"),
                    (prefix + "Geo21_0.pgcl", "z", "z"),
                    (prefix + "GeoAr01_0.pgcl", "x", "x"),
                    (prefix + "GeoAr01_1.pgcl", "x", "[not (z=0)]*(x + y) + [z=0]*x"),
                    (prefix + "LinExp1_0.pgcl", "z", "[0<n]*(2*n) + [not (0<n)]*z"),
                    (prefix + "LinExp1_1.pgcl", "z", "[0<n]*(z+2) + [not (0<n)]*z"),
                    (prefix + "PrinSys1_0.pgcl", "[x=2] + [not (x=2)]*0", "[x=2]"),
                    (prefix + "RevBin1_0.pgcl", "z", "[0<x]*(x+z)+[not (0<x)]*z"),
                    (prefix + "RevBin1_1.pgcl", "z", "z"),
                    (prefix + "Sum01_0.pgcl", "x", "[0<n]*(x+0.5*n*0.5)+[not (0<n)]*x"),
                    (prefix + "Mart1_0.pgcl", "rounds", "rounds"),
                    (prefix + "Mart1_1.pgcl", "rounds", "[0<b]*(1+rounds)+[not (0<b)]*rounds")
                    ]






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

    for (prog, post, prop) in exist_benchmarks:
        #program, post, prop, template, validate, verifier, distance, templaterefiner,
        #partitionfactor, usemotzkin, optimizing_synthesizer, debuglog, exporttemplate, oneshot, invarianttype, cdb):
        #run_with_to(100, cegis, [prog, post, prop, "", False, "distance", 1, "inductivity", 1, False, False, False, False, False, "sub", False, pickledir])

        print("Benchmark %s     -- post= %s  -- prop = %s " % (prog,post,prop))

        to_exec = ("cd "+ cegisprodir + "; poetry run " \
                  + 'cegispro2 ' \
                    '"%s" ' \
                    '--post "%s" ' \
                    '--prop "%s" ' \
                    '--template "" --novalidate --verifier distance --distance 1 --templaterefiner inductivity --nousemotzkin --nodebuglog --invarianttype sub ' \
                    '--nocdb --safestatistics "' + prefix + 'results_cegispro/"') % (prog, post, prop)

        try:
            #subprocess.call(act_venv_string + "; " + to_exec , shell = True, timeout = timeout)
            subprocess.call(to_exec, shell=True, timeout=timeout)
        except Exception:
            print("TO!")

        print("\n\n")


    # Now for the runs with cdb:
    for (prog, post, prop) in exist_benchmarks:
        #program, post, prop, template, validate, verifier, distance, templaterefiner,
        #partitionfactor, usemotzkin, optimizing_synthesizer, debuglog, exporttemplate, oneshot, invarianttype, cdb):
        #run_with_to(100, cegis, [prog, post, prop, "", False, "distance", 1, "inductivity", 1, False, False, False, False, False, "sub", False, pickledir])

        print("CDB Benchmark %s     -- post= %s  -- prop = %s " % (prog,post,prop))

        to_exec = ("cd "+ cegisprodir + "; poetry run " \
                  + 'cegispro2 ' \
                    '"%s" ' \
                    '--post "%s" ' \
                    '--prop "%s" ' \
                    '--template "" --novalidate --verifier distance --distance 1 --templaterefiner inductivity --nousemotzkin --nodebuglog --invarianttype sub ' \
                    '--cdb --safestatistics "' + prefix + 'results_cegispro_cdb/"') % (prog, post, prop)

        try:
            subprocess.call(act_venv_string + "; " + to_exec , shell = True, timeout = timeout)
        except Exception:
            print("TO")

        print("\n\n")

    # Now for the PAST runs:
    for (prog, post, prop) in exist_benchmarks:
        # program, post, prop, template, validate, verifier, distance, templaterefiner,
        # partitionfactor, usemotzkin, optimizing_synthesizer, debuglog, exporttemplate, oneshot, invarianttype, cdb):
        # run_with_to(100, cegis, [prog, post, prop, "", False, "distance", 1, "inductivity", 1, False, False, False, False, False, "sub", False, pickledir])

        print("PAST Benchmark %s     -- post= %s  -- prop = %s " % (prog, post, prop))

        to_exec = ("cd "+ cegisprodir + "; poetry run " \
                  + 'cegispro2 ' \
                         '"%s" ' \
                         '--post "%s" ' \
                         '--prop "%s" ' \
                         '--template "" --novalidate --verifier distance --distance 1 --templaterefiner inductivity --nousemotzkin --nodebuglog --invarianttype past ' \
                         '--nocdb --safestatistics "' + prefix + 'results_cegispro_past/"') % (prog, post, prop)

        try:
            subprocess.call(act_venv_string + "; " + to_exec, shell=True, timeout=timeout)
        except Exception:
            print("TO!")
        print("\n\n")





def run_exist_benchmarks():
    # now for running exist ..
    # idea: take everz cegispro2 benchmark, remove the ".pgcl", write existdir/program_list.txt so that it contains exactly the name of the program, run exist ..

    print("\n\n\n Now Exist:")
    existprefix = "/home/cegis/Desktop/Exist"

    for (prog, post, prop) in exist_benchmarks:
        name = prog.split(".")[0].split('/')[-1]
        print(name)

        # edit program_list
        file = open(existprefix + "/program_list.txt", 'w')
        file.write(name)
        file.close()
        print(existprefix)
        try:
            subprocess.call(
                'conda init && bash -l -c ". /home/cegis/anaconda3/etc/profile.d/conda.sh && conda activate exist && conda env list && cd ' + existprefix + '&& conda activate exist && python main.py --sub yes"',
                shell=True, timeout=timeout)
        except Exception:
            print("TO!")
        print("\n\n")





run_cegis_benchmarks()
#run_exist_benchmarks()












