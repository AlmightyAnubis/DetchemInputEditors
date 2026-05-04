import copy
import os.path

from GeneralUtil import ThermalDataReader
from MechanismEditorPackage import global_vars


def save_file(save_content):
    if save_content == "copy" or save_content == "overwrite":
        lines = copy.deepcopy(global_vars.file_prefix)
        reactions = global_vars.reactions
        for category in reactions:
            lines.append("**** " + category + "\n")
            for reaction in reactions[category]:
                add_reaction_to_line(reaction, lines)
                if reaction.is_reversible:
                    reaction = reaction.reverse_reaction
                    add_reaction_to_line(reaction, lines)

        lines.append("END\n")
        lines.append("-" * 72)

        filename = global_vars.dir_name
        name = os.path.basename(filename)
        path = os.path.dirname(filename)
        if save_content == "copy":
            filename = os.path.join(path, "adjust.json")
            file = open(filename, "r")
            content = file.read()
            file.close()
            path = os.path.join(path, "adjusted_mech")
            os.makedirs(path, exist_ok=True)
            filename = os.path.join(path, "adjust.json")
            file = open(filename, "w")
            file.write(content)
            file.close()
        filename = os.path.join(path, name)
        file = open(filename, 'w')
        file.writelines(lines)
        file.close()
        filename = os.path.join(path, "Thermdata.txt")
        ThermalDataReader.write_thermdata_file(filename, global_vars.thermalDataMap)


def add_reaction_to_line(reaction, lines):
    line = ""
    if reaction.is_stick:
        if reaction.is_disabled:
            lines.append("*STICK\n")
        else:
            lines.append("STICK\n")
    if reaction.is_disabled:
        line += "*"
    for educt in reaction.educts:
        for i in range(reaction.educts[educt]):
            line += str(educt).ljust(8)
            line += "+"
    line = line[:-1]
    line += ">"
    for product in reaction.products:
        for i in range(reaction.products[product]):
            line += str(product).ljust(8)
            line += "+"
    line = line[:-1]
    line = line.ljust(45)

    A_k = reaction.get_A_k(raw=True)
    if not reaction.is_stick:
        # Mol/cm2 -> Mol/m2 and Mol/cm3 -> Mol/m3
        A_k = A_k * 100**reaction.exponent
    beta_k = reaction.get_beta_k(raw=True)
    # kJ/mol -> J/mol
    E_k = reaction.E_k / 1e3

    line += "{:10.3E}".format(A_k).rjust(10)
    line += "{:.4f}".format(beta_k).rjust(7)
    line += "{:10G}".format(E_k).rjust(10)
    line += "\n"
    lines.append(line)
    orders = reaction.orders
    for key, value in orders.items():
        line = "$"
        line += key
        line = line.ljust(55)
        line += "{:7G}".format(value)
        if key in reaction.epsilon:
            line += "{:10G}".format(reaction.epsilon[key])
            reaction.epsilon.pop(key)
        else:
            line += "{:10G}".format(0)
            line += "\n"
        lines.append(line)
    for key, value in reaction.epsilon.items():
        line = "$"
        line += key
        line = line.ljust(55)
        line += "{:7G}".format(0)
        line += "{:10G}".format(value)
        line += "\n"
        lines.append(line)