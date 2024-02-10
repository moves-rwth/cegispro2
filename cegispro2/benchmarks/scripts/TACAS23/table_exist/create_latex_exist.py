import csv
import pickle
from os.path import exists

exist_benchmarks = ["BiasDir1_0",
                    "BiasDir1_1",
                    "BiasDir2_0",
                    "BiasDir2_1",
                    "BiasDir3_0",
                    "BiasDir3_1",
                    "Bin01_0",
                    "Bin02_0",
                    "Bin03_0",
                    "Bin11_0",
                    "Bin11_1",
                    "Bin12_0",
                    "Bin12_1",
                    "Bin13_0",
                    "Bin13_1",
                    "Bin21_0",
                    "Detm1_0",
                    "Detm1_1",
                    "Duel1_0",
                    "Duel2_0",
                    "Fair1_0",
                    "Fair1_1",
                    "Gambler01_0",
                    "Geo01_0",
                    "Geo01_1",
                    "Geo01_2",
                    "Geo11_0",
                    "Geo21_0",
                    "GeoAr01_0",
                    "GeoAr01_1",
                    "LinExp1_0",
                    "LinExp1_1",
                    "PrinSys1_0",
                    "RevBin1_0",
                    "RevBin1_1",
                    "Sum01_0",
                    "Mart1_0",
                    "Mart1_1"]
prefix = "/Users/kevinbatz/Desktop/Arbeit/kevinbatz/Projects/InvSysCegis/cegispro2/cegispro2/benchmarks/TACAS23_EXIST/"


MOTO_tick = 500
ERR_tick = 900
typestring = "unsound"

file = open('benchmarks/TACAS23_EXIST/scatter_exist_unsound.csv', 'w', newline='\n')
csvwriter = csv.writer(file, delimiter=';', quotechar = '|', quoting=csv.QUOTE_MINIMAL)
csvwriter.writerow(["benchmark", "Type", "cegis", "exist"])

# Create the csv file containing the runtimes
for bench in exist_benchmarks:
    print("\n\n\n %s" % bench)

    # check if cegis statistics pickle exsists
    path = prefix + "results_cegispro/" + bench + ".pgcl.pickle"
    if exists(path):
        with open(path, 'rb') as pickle_file:
            statistics = pickle.load(pickle_file)
            cegispro_res = str(statistics.total_time).split(" ")[0]
            print("inductive invariant: %s" % statistics.inductive_invariant)
    else:
        cegispro_res = MOTO_tick

    print('cegis: %s' % cegispro_res)

    # search for the entry in the results
    exist_res = MOTO_tick
    # check if file exists
    path = prefix + "results_exist/" + bench + "-sub.csv"
    if exists(path):
        with open(path) as file:
            csvr = csv.reader(file, delimiter= ",")
            for row in csvr:
                if row[0] == bench + "_0":
                    #print(row[1])
                    if row[1].find("not able") == -1:
                        exist_res = row[7]
                        break
                    else:
                        print("unable to find invariant: %s" % bench)
    else:
        print("not exists for exists:%s" % bench)

    print("exist: %s" % exist_res)

    csvwriter.writerow([bench, typestring, cegispro_res, exist_res])

file.close()





file = open('benchmarks/TACAS23_EXIST/scatter_exist_cegis_sound_unsound.csv', 'w', newline='\n')
csvwriter = csv.writer(file, delimiter=';', quotechar = '|', quoting=csv.QUOTE_MINIMAL)
csvwriter.writerow(["benchmark", "Type", "cegisunsound", "cegissound"])



print("\n\n\n: now for sound:")

# now for the sound instances
typestring = "sound"
for bench in exist_benchmarks:

    print("\n\n for %s:" % bench)
    # check if cegis statistics pickle exsists
    path = prefix + "results_cegispro_past/" + bench + ".pgcl.pickle"
    if exists(path):
        with open(path, 'rb') as pickle_file:
            statistics = pickle.load(pickle_file)
            print(str(statistics.total_time).split(" ")[0])
            cegispro_res_sound = float(str(statistics.total_time).split(" ")[0])
            print("past time: %s" % str(cegispro_res))
        path = prefix + "results_cegispro_cdb/" + bench + ".pgcl.pickle"
        if exists(path):
            with open(path, 'rb') as pickle_file:
                statistics = pickle.load(pickle_file)
                print(str(statistics.total_time).split(" ")[0])
                cegispro_res_sound += float(str(statistics.total_time).split(" ")[0])
                print("cdb time: %s" % str(cegispro_res))
        else:
            cegispro_res_sound = MOTO_tick

    else:
        cegispro_res_sound = MOTO_tick


    print('Result cegis sound: %s' % str(cegispro_res_sound))

    # check if cegis statistics pickle exsists
    path = prefix + "results_cegispro/" + bench + ".pgcl.pickle"
    if exists(path):
        with open(path, 'rb') as pickle_file:
            statistics = pickle.load(pickle_file)
            cegispro_res_unsound = str(statistics.total_time).split(" ")[0]
    else:
        cegispro_res_unsound = MOTO_tick

    print('Result cegis unsound: %s' % cegispro_res)





    csvwriter.writerow([bench, typestring, str(cegispro_res_unsound), str(cegispro_res_sound)])



file.close()