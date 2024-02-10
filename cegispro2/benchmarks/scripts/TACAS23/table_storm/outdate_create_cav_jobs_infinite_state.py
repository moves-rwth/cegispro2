import os

__location__ = os.path.realpath(
    os.path.join(os.getcwd(), os.path.dirname(__file__)))

jobs_input = open(os.path.join(__location__, "jobs_input_infinite_state.txt"), 'r')
jobs_output = open(os.path.join(__location__, "jobs_output_infinite_state.txt"), 'w+')

input = jobs_input.readlines()
output = []
for line in input:
    line = line.replace("\n", "")
    output.append(line + " --distance 2 --novalidate --noexporttemplate --templaterefiner inductivity --nousemotzkin\n")
    output.append(line + " --distance 2 --novalidate --noexporttemplate --templaterefiner inductivity --usemotzkin\n")
    #output.append(line + " --distance 2 --novalidate --noexporttemplate --templaterefiner fixed --nousemotzkin\n")
    #output.append(line + " --distance 2 --novalidate --noexporttemplate --templaterefiner fixed --usemotzkin\n")
    output.append(line + " --distance 2 --novalidate --noexporttemplate --templaterefiner variable\n")

jobs_output.writelines(output)
jobs_input.close()
jobs_output.close()