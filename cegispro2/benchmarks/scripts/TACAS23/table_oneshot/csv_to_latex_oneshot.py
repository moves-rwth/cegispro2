import csv


def results_to_latex(results):
    res = "\\begin{tabular}{l|c||r|rrrr|rrrr|rrrr|rrrr|rrrr|rrrr}\n"

    res += "prog & $\sizeof{\\temp}$ & \multicolumn{1}{c}{one-shot} & \multicolumn{24}{c}{cegis} \\\\ \n  "
    res += "& & & \multicolumn{8}{c}{d=1} & \multicolumn{8}{c}{d=2} & \multicolumn{8}{c}{d=8}  \\\\ \n  "
    res += "& & & \multicolumn{4}{c}{motz} & \multicolumn{4}{c}{nomotz} & \multicolumn{4}{c}{motz} & \multicolumn{4}{c}{nomotz} & \multicolumn{4}{c}{motz} & \multicolumn{4}{c}{nomotz} \\\\ \n  "
    # ctis,expr,total,verif,synth
    res += "& & t & \#c & v & s & t & \#c & v & s & t & \#c  & v & s & t & \#c  & v & s & t & \#c  & v & s & t & \#c &  v & s & t \\\ \n  "

    for prog in results:
        res += (prog.replace("_", "").split("/"))[1].split(".")[0]
        #print(prog)
        for prop in results[prog]:
            #res += " & $" + prop + "$ & "
            prop = results[prog][prop]

            res += " & " + prop["template_size"]
            nums = prop['one_shot']
            for i in range(1, len(nums)):
                if nums[0] == 'safely inductive':
                    res += "&" +  nums[i]
                else:
                    res += "&" +  "{\\scriptsize %s}" % nums[0]

            nums = prop['1_motz']
            for i in range(1, len(nums)):
                if nums[0] == 'safely inductive':
                    res += "&" + nums[i]
                else:
                    res += "&" + "{\\scriptsize %s}" % nums[0]

            nums = prop['1_nomotz']
            for i in range(1, len(nums)):
                if nums[0] == 'safely inductive':
                    res += "&" + nums[i]
                else:
                    res += "&" + "{\\scriptsize %s}" % nums[0]

            nums = prop['2_motz']
            for i in range(1, len(nums)):
                if nums[0] == 'safely inductive':
                    res += "&" + nums[i]
                else:
                    res += "&" + "{\\scriptsize %s}" % nums[0]

            nums = prop['2_nomotz']
            for i in range(1, len(nums)):
                if nums[0] == 'safely inductive':
                    res += "&" + nums[i]
                else:
                    res += "&" + "{\\scriptsize %s}" % nums[0]

            nums = prop['8_motz']
            for i in range(1, len(nums)):
                if nums[0] == 'safely inductive':
                    res += "&" + nums[i]
                else:
                    res += "&" + "{\\scriptsize %s}" % nums[0]

            nums = prop['8_nomotz']
            for i in range(1, len(nums)):
                if nums[0] == 'safely inductive':
                    res += "&" + nums[i]
                else:
                    res += "&" + "{\\scriptsize %s}" % nums[0]

            res += "\\\\ \n"

        res += "% \n" + "\phantom{a} \\\\ \n"


    res += "\\end{tabular}"

    return res.replace("timeout", "TO").replace("memout", "MO").replace("error", "--")


file = 'results_oneshot.csv'

results = dict()

with open(file, 'r') as csvfile:
    datareader = csv.reader(csvfile)
    for row in datareader:

        if row[1] == 'example_file':
            continue

        #1=file, 3=prop, 4=result,  5=#ctis, 7=#expr, 8=total, 10=verif_time,11=synth_time,14=motz,refiner=16, 21=inductive template
        if row[1] not in results:
            props = dict()
        else:
            props = results[row[1]]


        if row[3] not in props:
            prop = dict()
            prop["template_size"] = None
            prop['one_shot'] = None
            prop['1_motz'] = None
            prop['1_nomotz'] = None
            prop['2_motz'] = None
            prop['2_nomotz'] = None
            prop['8_motz'] = None
            prop['8_nomotz'] = None
        else:
            prop = props[row[3]]

        #res,ctis,total,verif,synth
        data = [row[4], "{\\scriptsize $%s$}" % row[5],"{\\scriptsize $%s$}" % row[10],"{\\scriptsize $%s$}" % row[11], "{\\scriptsize $%s$}" % row[8]]

        if row[4] == 'safely inductive':
            prop['template_size'] = str(len(row[21].split(','))+1)

        distance = str(row[18])
        motz = True if row[14] == 'yes' else False

        oneshot= True if row[13] == 'yes' else False
        print(row[1] + "    " + row[4] + "   " + distance + "   " + str(motz) + "   " + row[14])
        if oneshot:
            prop['one_shot'] = [row[4],row[8]]
        else:
            if distance == '1' and motz:
                print(row[1])
                prop['1_motz'] = data

            if distance == '1' and not motz:
                prop['1_nomotz'] = data

            if distance == '2' and motz:
                prop['2_motz'] = data

            if distance == '2' and not motz:
                prop['2_nomotz'] = data

            if distance == '8' and motz:
                prop['8_motz'] = data

            if distance == '8' and not motz:
                prop['8_nomotz'] = data


        #print(prop)
        props[row[3]] = prop
        results[row[1]] = props

    print(results_to_latex(results))


