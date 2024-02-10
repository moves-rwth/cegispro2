import csv
import os




def results_to_latex(results):
    res = "\\begin{tabular}{lc||r||rrr|rrr}\n"
    #res += "& &  \multicolumn{1}{c}{} & \multicolumn{1}{c}{} & \multicolumn{12}{c}{cegispro2}  \\\\ \n  "
    res += " &   & \multicolumn{1}{c||}{\mono}  & \multicolumn{3}{c|}{\prepsynthesizer} & \multicolumn{3}{c}{plain} \\\\ \n  "
    # ctis,expr,total,verif,synth
    res += "Prog & {\\footnotesize $|T|$} & t &  {\\footnotesize $|S'|$}  &   {\\footnotesize $\\text{t}_\\text{s}$\%} & {\\footnotesize t} & {\\footnotesize $|S'|$} & {\\footnotesize $\\text{t}_\\text{s}$\%}  & {\\footnotesize t } \\\\ \n  "
    res += "\midrule\midrule"
    for prog in results:
        res += "\multirow{%s}{*}{\\footnotesize{%s}}" % (len(results[prog]), (prog.replace("_", "").split("/"))[1].split(".")[0])
        #print(prog)
        count = 1

        for prop in results[prog]:

            #res += " & $" + prop + "$ & "

            prop = results[prog][prop]
            res += "& %s & %s" % (prop['sizet'], prop['oneshot'][1])
            count += 1

            nums = prop['motz']
            for i in range(1, len(nums)):
                # if nums[0] == 'safely inductive':
                res += "&" + nums[i]
                # else:
                #    res += "&" + "{\\scriptsize %s}" % nums[0]

            #res += "&" + ("--" if prop['cegisbest'] is None else "{\\scriptsize %s}" % str(prop['cegisbest']))
            nums = prop['nomotz']
            for i in range(1, len(nums)):
                #if nums[0] == 'safely inductive':
                res += "&" + nums[i]
                #else:
                #    res += "&" + "{\\scriptsize %s}" % nums[0]


            res += "\\\\ \n"

        res += "% \n" + "\midrule  \n"


    res += "\\end{tabular}"

    return res.replace("timeout", "TO").replace("memout", "MO").replace("error", "--")




file = 'results_oneshot.csv'

__location__ = os.path.realpath(
    os.path.join(os.getcwd(), os.path.dirname(__file__)))

results = dict()

with open(os.path.join(__location__, file), 'r') as csvfile:
    datareader = csv.reader(csvfile)
    for row in datareader:

        if row[1] == 'example_file':
            continue

        #1=file, 3=prop, 4=result,  5=#ctis, 7=#expr, 8=total, 10=verif_time,11=synth_time,14=motz,refiner=16
        if row[1] not in results:
            props = dict()
        else:
            props = results[row[1]]

        if row[3] not in props:
            prop = dict()
            #prop['ind_motz'] = None
            prop['oneshot'] = None
            prop['motz'] = None
            prop['nomotz'] = None
            prop['sizet'] = None
        else:
            prop = props[row[3]]

        #ctis,expr,total,verif,synth

        res = row[4]
        ctis = row[5]
        sizet = row[7]
        v = row[11]
        t = row[8]
        oneshot = True if row[13] == 'yes' else False
        motzkin = True if row[14] == 'yes' else False

        if not oneshot:
            if res == 'safely inductive':
                v = str(int(round(float(v)/float(t)*100,0)))
                t = str(int(round(float(t), 0)))
                t = "{<}1" if t == "0" else t
                data = [res, "{\\scriptsize $%s$}" % ctis, "{\\scriptsize $%s$}" % v, "{\\scriptsize $%s$}" % t]
                sizet = str(int(sizet) + 1)
                prop['sizet'] = sizet
            else:
                data = [res, "--","--", "{\\scriptsize %s}" % res]

        if oneshot:
            if res == 'safely inductive':
                t = str(int(round(float(t), 0)))
                t = "{<}1" if t == "0" else t
                data = [res, "{\\scriptsize $%s$}" % t]
                sizet = str(int(sizet) + 1)
                prop['sizet'] = sizet
            else:
                data = [res, res]

        if oneshot:
            prop['oneshot'] = data
        elif motzkin:
            prop['motz'] = data
        elif not motzkin:
            prop['nomotz'] = data

        #print(prop)
        props[row[3]] = prop
        results[row[1]] = props

    print(results_to_latex(results))




