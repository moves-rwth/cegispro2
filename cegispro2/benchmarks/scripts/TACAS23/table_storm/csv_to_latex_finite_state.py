import csv
import os


MOTO_TICK = str(10000)
typestring = "dtmc"


def find_storm_entries(prog, count):
    sfile = 'results_storm.csv'

    __location__ = os.path.realpath(
        os.path.join(os.getcwd(), os.path.dirname(__file__)))

    results = dict()

    storm = {}
    storm['dd'] = None
    storm['sp'] = None

    storm_num = {}
    storm_num['dd'] = None
    storm_num['sp'] = None

    with open(os.path.join(__location__, sfile), 'r') as csvfile:
        datareader = csv.reader(csvfile)
        for row in datareader:
            #print("searching for %s " % ('CAV22_storm/' + str(prog) + "_" + str(count) + ".pm"))
            if row[1] == 'TACAS23_storm/' + str(prog) + "_" + str(count) + ".pm":
                time = row[2]
                time_num = time

                if time != 'timeout' and time != 'memout' and time != 'error':
                    time_num = str(int(round(float(time.split('ms')[0])/1000,0)))

                    time = str(int(round(float(time.split('ms')[0])/1000,0)))
                    time_num = "1" if time == "0" else time_num
                    time = "{<}1" if time == "0" else time
                    time= ("{\\scriptsize $%s$}" % time)


                if row[3] == 'dd':
                    storm['dd'] = time
                    storm_num['dd'] = time_num
                else:
                    storm['sp'] = time
                    storm_num['sp'] = time_num


    if storm['dd'] is None:
        storm['dd'] = "NA"
        storm_num['dd'] = "NA"
    if storm['sp'] is None:
        storm['sp'] = "NA"
        storm_num['sp'] = "NA"

    return (storm, storm_num)



def results_to_latex(results):

    file = open('scatter_finite_state.csv', 'w', newline='\n')
    csvwriter = csv.writer(file, delimiter=';', quotechar = '|', quoting=csv.QUOTE_MINIMAL)
    csvwriter.writerow(["benchmark", "Type", "cegis", "storm"])

    res = "\\begin{tabular}{lc||rr||r|rrrr|rrrr|rrrr}\n"
    res += "&   \multicolumn{1}{c}{}& \multicolumn{2}{c}{\headername{storm}} & \multicolumn{1}{c}{} & \multicolumn{12}{c}{\headername{\\tool}}  \\\\ \n  "
    res += " &   & && & \multicolumn{4}{c|}{\headername{induct.-guided}} & \multicolumn{4}{c|}{\headername{static}} & \multicolumn{4}{c}{\headername{variable}}  \\\\ \n  "
    # ctis,expr,total,verif,synth
    res += "Prog & $|S|$   & {\headername{sp}} & {\headername{dd}} & {\headername{best}} & {\\footnotesize $|S'|$} &{\\footnotesize $|\inv|$} &  {\\footnotesize $\\text{t}_\\text{s}$\%} & {\\footnotesize t} & {\\footnotesize $|S'|$} & {\\footnotesize $|\inv|$ } & {\\footnotesize $\\text{t}_\\text{s}$\%}  & {\\footnotesize t } & {\\footnotesize $|S'|$} & {\\footnotesize $|\inv|$ } & {\\footnotesize $\\text{t}_\\text{s}$\%}  & {\\footnotesize t  } \\\\ \n  "
    res += "\midrule\midrule"
    for prog in results:
        res += "\multirow{%s}{*}{\\footnotesize{%s}}" % (len(results[prog]), (prog.replace("_", "").split("/"))[1].split(".")[0])


        #print(prog)
        count = 1
        for prop in results[prog]:
            csv_row = []
            #res += " & $" + prop + "$ & "
            res += " & "

            prop = results[prog][prop]
            csv_row.append("%s_%s" % ((prog.split('/')[1]).split('.')[0], str(count)))
            csv_row.append(typestring)

            (storm, storm_num) = find_storm_entries((prog.split('/')[1]).split('.')[0], count)
            res += " & " + ("{\\scriptsize %s}" % storm['sp']) + "&" + ("{\\scriptsize %s}" % storm['dd'])

            # if (storm_num['sp'] == 'timeout' or storm_num['sp'] == 'memout' or storm_num['sp'] == 'NA' or storm_num['sp'] == 'error') \
            #         and (storm_num['dd'] == 'timeout' or storm_num['sp'] == 'dd' or storm_num['sp'] == 'NA'):
            #     csv_row.append(MOTO_TICK)
            # else:
            #     if (storm_num['sp'] != 'timeout' or storm_num['sp'] != 'memout' or storm_num['sp'] != 'NA') \
            #             and (storm_num['dd'] == 'timeout' and storm_num['sp'] == 'dd' and storm_num['sp'] == 'NA'):
            #         csv_row.append(storm_num['sp'])
            #     elif (storm_num['sp'] == 'timeout' and storm_num['sp'] == 'memout' and storm_num['sp'] == 'NA') \
            #             and (storm_num['dd'] != 'timeout' and storm_num['sp'] != 'dd' and storm_num['sp'] != 'NA'):
            #         csv_row.append(storm_num['dd'])
            #     else:

            count += 1

            # nums = prop['ind_motz']
            # for i in range(1, len(nums)):
            #     if nums[0] == 'safely inductive':
            #         res += "&" +  nums[i]
            #     else:
            #         res += "&" +  "{\\scriptsize %s}" % nums[0]

            if prop['cegisbest'] is not None:
                prop['cegisbest'] = "{\\scriptsize ${<}1$}" if prop['cegisbest'] == 0 else ("{\\scriptsize $%s$}" % str(prop['cegisbest']))
                csv_row.append(prop['cegisbest'])
            else:
                csv_row.append(MOTO_TICK)

            try:

                csv_row.append(storm_num['sp'] if int(storm_num['sp']) <= int(storm_num['dd']) else storm_num['dd'])

            except Exception:
                try:
                    int(storm_num['sp'])
                    csv_row.append(storm_num['sp'])
                except Exception:
                    try:
                        int(storm_num['dd'])
                        csv_row.append(storm_num['dd'])
                    except Exception:
                        #print("except")
                        csv_row.append(MOTO_TICK)


            res += "&" + ("--" if prop['cegisbest'] is None else "{\\scriptsize %s}" % str(prop['cegisbest']))
            nums = prop['ind_nomotz']
            for i in range(1, len(nums)):
                #if nums[0] == 'safely inductive':
                res += "&" + nums[i]
                #else:
                #    res += "&" + "{\\scriptsize %s}" % nums[0]

            # nums = prop['fix_motz']
            # for i in range(1, len(nums)):
            #     if nums[0] == 'safely inductive':
            #         res += "&" + nums[i]
            #     else:
            #         res += "&" + "{\\scriptsize %s}" % nums[0]

            nums = prop['fix_nomotz']
            for i in range(1, len(nums)):
                #if nums[0] == 'safely inductive':
                res += "&" + nums[i]
                #else:
                #    res += "&" + "{\\scriptsize %s}" % nums[0]

            nums = prop['var']
            for i in range(1, len(nums)):
                #if nums[0] == 'safely inductive':
                res += "&" + nums[i]
                #else:
                #    res += "&" + "{\\scriptsize %s}" % nums[0]

            res += "\\\\ \n"
            csvwriter.writerow(csv_row)

        res += "% \n" + "\midrule  \n"


    res += "\\end{tabular}"

    file.close()

    return res.replace("timeout", "TO").replace("memout", "MO").replace("error", "--")




file = 'results_finite_state.csv'

__location__ = os.path.realpath(
    os.path.join(os.getcwd(), os.path.dirname(__file__)))

results = dict()

with open(os.path.join(__location__, file), 'r') as csvfile:
    datareader = csv.reader(csvfile)
    for row in datareader:

        if row[1] == 'example_file' or row[1] == "":
            continue

        #1=file, 3=prop, 4=result,  5=#ctis, 7=#expr, 8=total, 10=verif_time,11=synth_time,14=motz,refiner=16
        if row[1] not in results:
            props = dict()
        else:
            props = results[row[1]]


        if row[3] not in props:
            prop = dict()
            #prop['ind_motz'] = None
            prop['ind_nomotz'] = None
            #prop['fix_motz'] = None
            prop['fix_nomotz'] = None
            prop['var'] = None
            prop['storm_sp'] = None
            prop['storm_dd'] = None
            prop['cegisbest'] = None
        else:
            prop = props[row[3]]

        #ctis,expr,total,verif,synth

        res = row[4]
        ctis = row[5]
        sizet = row[7] #+1 for [neg guard]*post
        v = row[11]
        t = row[8]

        if res == 'safely inductive':
            v = str(int(round(float(v)/float(t)*100,0)))
            t = str(int(round(float(t), 0)))

            prop['cegisbest'] = int(round(float(t),0)) if prop['cegisbest']==None or prop['cegisbest'] > float(t) else prop['cegisbest']
            sizet = str(int(sizet)+1)

            t = "{<}1" if t == "0" else t
            data = [res, "{\\scriptsize $%s$}" % ctis, "{\\scriptsize $%s$}" % sizet, "{\\scriptsize $%s$}" % v,
                    "{\\scriptsize $%s$}" % t]
        else:

            data = ["--","--", "--", "--", "{\\scriptsize %s}" % res]

        refiner = row[16]
        motz = True if row[14] == 'yes' else False

        #if refiner == 'inductivity' and motz:
        #    prop['ind_motz'] = data

        if refiner == 'inductivity' and not motz:
            prop['ind_nomotz'] = data

        #if refiner == 'fixed' and motz:
        #    prop['fix_motz'] = data

        if refiner == 'fixed' and not motz:
            prop['fix_nomotz'] = data

        if refiner == "variable":
            prop['var'] = data

        #print(prop)
        props[row[3]] = prop
        results[row[1]] = props

    print(results_to_latex(results))




