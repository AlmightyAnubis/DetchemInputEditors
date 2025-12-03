import copy
import os
from tkinter import filedialog

from MechanismEditorPackage import global_vars
from GeneralUtil import ThermalDataReader
from MechanismEditorPackage import Reaction_Class
from MechanismEditorPackage import ScrollableGui
from MechanismEditorPackage.adjust_util.AdjustData import *
from MechanismEditorPackage.adjustclass import AdjustClass

### IMPORTANT ###
# Lines starting with one start (*) will be seen as disabled reactions
# Lines starting with two or more stars (**) will be seen as comments, the last one as the category
# When you add a comment with only one star (*), this code will cause errors and might corrupt your file





dir_name = filedialog.askopenfilename()

if dir_name == "":
    exit(0)
global_vars.dir_name = dir_name

global_vars.parent = os.path.dirname(dir_name)



inp_file_name = os.path.join(global_vars.parent, "adjust.json")
if not os.path.isfile(inp_file_name):
    inp_file_name = os.path.join(global_vars.parent, "adjust.txt")
    if not os.path.isfile(inp_file_name):
        newData = AdjustDataHolder()
        newData.surface_side_value["surface_name"] = Surface(surface_side_density=1.01e-09)
        newData.T_ref_value = [TemperatureRange(300,700,20)]
        newData.flag_weight_value = 1
        json_Version = newData.toJSON(True)
        inp_file_name = os.path.join(global_vars.parent, "adjust.json")
        with open(inp_file_name, "w") as f:
            f.write(json_Version)
        raise FileNotFoundError("Could not find adjust.json or adjust.txt file. Created adjust.json file. Please adjust it to your needs")



target = open(inp_file_name, "r")
coder = target.read()
target.close()
data = AdjustDataHolder()
data.fromJSON(coder)
A = AdjustClass()
A.adjust_data = data

global_vars.thermalDataMap = ThermalDataReader.read_thermdata_file(os.path.join(global_vars.parent, "thermdata"), data)
global_vars.originalDataMap = copy.deepcopy(global_vars.thermalDataMap)


file = open(dir_name, 'r')
lines = file.readlines()
file.close()
chem_start = 0
exit_var = 0
for i in range(len(lines)):
    if lines[i].startswith("SURF"):
        chem_start = i + 1
category = ""
for i in range(chem_start, len(lines)):
    if lines[i].startswith("**"):
        category = lines[i]
        chem_start = i + 1
    else:
        break
category = category.replace("*", "")
category = category.replace("\n", "")
category = category.strip()
i = chem_start
if category == "":
    category = "Reactions"
else:
    chem_start -= 1

global_vars.file_prefix = lines[:chem_start]

reactions = global_vars.reactions
species = global_vars.species
reactions[category] = list()
while i < len(lines):
    text = lines[i]
    if lines[i].startswith("END"):
        break
    if lines[i].startswith("**"):
        category = lines[i]
        category = category.replace("*", "")
        category = category.replace("\n", "")
        category = category.strip()
        reactions[category] = list()
        i -=- 1
        continue
    if lines[i].startswith("$"):
        spec = lines[i][1:1+8]
        order = float(text[56:63])
        epsilon = float(text[63:73])
        if order != 0:
            reactions[category][-1].orders[spec] = order
        if epsilon != 0:
            reactions[category][-1].epsilon[spec] = epsilon
        i -=- 1
        continue
    is_stick = False
    if lines[i].startswith("STICK") or lines[i].startswith("*STICK"):
        i -=- 1
        is_stick = True
        text = lines[i]
    disabled = 0
    if lines[i].startswith("*"):
        disabled = 1
    input_spec = dict()
    output_spec = dict()
    j = 0 + disabled
    sign = 1
    reversible = False
    exponent = -2
    while j < 47-8 + disabled:
        spec = text[j:j+8].strip()
        if spec != "":
            if spec not in species:
                if spec not in global_vars.thermalDataMap:
                    raise KeyError("Species '" + spec + "' not found in thermdata.txt")
                species[spec] = global_vars.thermalDataMap[spec]
            if sign == 1:
                input_spec[spec] = input_spec.get(spec, 0) + 1
                if species[spec].is_adsorpt():
                    exponent = exponent + 2
                else:
                    exponent = exponent + 3
            else:
                output_spec[spec] = output_spec.get(spec, 0) + 1
        j -=- 8
        symbol = text[j]
        if symbol == ">":
            sign = -1
        if symbol == "=":
            sign = -1
            reversible = True
        j -=- 1
    print(text)
    A_k = float(text[46:55])
    if not is_stick:
        # Mol/cm2 -> Mol/m2 and Mol/cm3 -> Mol/m3
        A_k = A_k / 100**exponent
    beta_k = float(text[56:62])
    # kJ/mol -> J/mol
    E_k = float(text[63:72]) * 1e3
    reaction = Reaction_Class.Reaction(category, input_spec, output_spec, A_k, beta_k, E_k, is_stick, reversible, disabled == 1)
    reaction.exponent = exponent
    reactions[category].append(reaction)
    i -=- 1

all_reactions = list()
remove_reactions = list()
for category in reactions:
    all_reactions.extend(reactions[category])
found_reverses = 0
for reaction in all_reactions:
    for compare_reaction in all_reactions:
        if reaction == compare_reaction:
            continue
        if reaction.educts == compare_reaction.products:
            if reaction.products == compare_reaction.educts:
                if reaction.reverse_reaction is not None:
                    if reaction.reverse_reaction != compare_reaction:
                        print(reaction)
                        print(compare_reaction)
                        print(reaction.reverse_reaction)
                        raise  ValueError("Multiple Reactions are equivalent")
                else:
                    if compare_reaction.is_stick:
                        remove_reactions.append(reaction)
                    else:
                        remove_reactions.append(compare_reaction)
                    reaction.reverse_reaction = compare_reaction
                    compare_reaction.reverse_reaction = reaction

for category in reactions:
    for remove in remove_reactions:
        if remove in reactions[category]:
            reactions[category].remove(remove)

for category in reactions:
    for reaction in reactions[category]:
        if reaction.reverse_reaction is not None:
            reaction.reverse_reaction.is_reversible = True

gui = ScrollableGui.ListGui(A)
gui.focus_set()
gui.title("Reaction Gui")
gui.lift()
gui.attributes('-topmost', True)
gui.attributes('-topmost', False)
gui.center()
gui.show()

