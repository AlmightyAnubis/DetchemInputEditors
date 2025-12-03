import os.path
import random

import periodictable

from GeneralUtil.MaterialData import Species, State, convert_state, reconvert_state
from MechanismEditorPackage.adjust_util.AdjustData import AdjustDataHolder

defaultMapping: dict[str,str]

issuetracker = dict()
issuetracker["missing value"] = []
issuetracker["formation error"] = []
issuetracker["chem. error"] = []
lineCounter = 0

def read_thermdata_file(file_name: str, ad_data:AdjustDataHolder = None) -> dict[str, Species]:
    global lineCounter, defaultMapping, issuetracker
    target: dict[str, Species] = dict()
    if not os.path.isfile(file_name):
        if not os.path.isfile(file_name + ".txt"):
            raise FileNotFoundError("Could not find file " + file_name)
        else:
            file_name = file_name + ".txt"
    file = open(file_name, "r")

    surfaces: dict[str, tuple[str, int]] = dict()
    if ad_data is not None:
        for key,surface in ad_data.surface_side_value.items():
            surfaces[key] = (key , 1)
            for special in surface.special_surface_species:
                surfaces[special] = (key, surface.special_surface_species[special])


    lines = file.readlines()
    while 1 == 1:
        line = lines[lineCounter]
        lineCounter += 1
        if line.startswith("THERMO"):
            file.readline()
            lineCounter += 1
            break
        if lineCounter>= len(lines):
            lineCounter = 0
            break

    table = periodictable.core.default_table(None)
    while 1 == 1:
        if lineCounter >= len(lines):
            break
        if lines[lineCounter].startswith("!"):
            lineCounter +=1
            continue
        header = lines[lineCounter]
        header = header.replace("\n", "")
        if header.startswith("END"):
            break
        lineCounter += 1
        if header is None:
            break
        if len(header) == 0:
            break
        name = header[0:8].strip()
        species = Species(name, convert_state(header[44]))
        comment = header[8:24]
        species.comment = comment
        temp_list = header[45:].split()
        try:
            species.set_temp_min(float(temp_list[0]))
            species.set_temp_max(float(temp_list[1]))
            species.set_temp_switch(float(temp_list[2]))
        except ValueError:
            issuetracker["formation error"].append(lineCounter)
            print("Could not read temperature for " + name + " Received \"" + header[45:] + "\"")

        for i in range(24, 44, 5):
            data = header[i:i + 5].split()
            try:
                atom = data[0]  # atom name
                if atom == "0.":            # no more atoms listed
                    break
                n = int(float(data[1]))  # sometimes numbers are floats
            except IndexError:
                continue
            except Exception as error:
                issuetracker["chem. error"].append(lineCounter)
                print("Exception occurred for " + name + ":", error)
                continue
            atom = atom.capitalize()
            if atom == "E": # ignore electrons
                continue
            try:
                if n: species.add_atom(table.isotope(atom), n)
            except:
                print("Could not convert \"" + atom + "\" from " + name)

        for section in range(3):
            line = lines[lineCounter]
            lineCounter += 1
            for i in range(5):
                try:
                    value = float(line[15 * i:15 * (i + 1)])
                    species.add_coefficient(value)
                except ValueError:
                    # Catch Double Values for example 0.10431658D+02
                    try:
                        value = float(line[15 * i:15 * (i + 1)].replace("D", "E").replace("E ","E"))
                        species.add_coefficient(value)
                    except ValueError:
                        if not(i==4 and section==2):
                            print("Error in data for " + name + " - Received at line " + str(lineCounter) + " for value " + str(i + 1) + ": " + line[15 * i:15 * (
                                    i + 1)].replace("D", "E"))
                        issuetracker["missing value"].append(lineCounter)
                        species.add_coefficient(None)

        if ad_data is not None:
            species.check_adsorpt(surfaces, ad_data)
        target[name] = species
    file.close()
    defaultMapping = dict()
    return target

def write_thermdata_file(file_name: str, target: dict[str, Species] ) -> bool:
    file = open(file_name, "w")

    lines = list()
    for key, spec in target.items():
        line = list("".ljust(180))
        line[0:8] = list(str(spec).ljust(8))
        line[8:24] = spec.comment

        for i in range(24, 44, 5):
            line[i + 4] = str(0)
        i = 24
        for atom in spec.get_atoms().keys():
            name = str(atom)
            nr = str(spec.get_atoms()[atom])
            content = name.ljust(5 - len(nr))
            content += nr
            line[i:i + 5] = content
            i += 5
        line[48:58] = "{:10.2F}".format(spec.get_temp_min()).rjust(10)
        line[58:68] = "{:10.2F}".format(spec.get_temp_max()).rjust(10)
        line[68:76] = "{:8.2F}".format(spec.get_temp_switch()).rjust(8)
        line[44] = reconvert_state(spec.state)
        line[79] = "1"
        lines.append("".join(line).ljust(180))

        line = ""
        i = 0
        nr = 2
        for coef in spec.get_coefficients():
            if coef is not None:
                line += "{:15.8E}".format(coef)
            else:
                line += " " * 15
            i += 1
            if i >= 5:
                line = line.ljust(79)
                line = line + str(nr)
                if random.Random().random()*100<0.1:
                    line = line + "    Das sieht aber ganz falsch aus."
                elif random.Random().random()*100<0.1:
                    line = line + "    Bist du dir sicher?"
                elif random.Random().random()*100<0.1:
                    line = line + "    Lass dich nicht verunsichern."
                elif random.Random().random()*100<0.1:
                    line = line + "    Wer das liest, kontrolliert die Dateinen."
                line = line.ljust(180)
                lines.append(line)
                line = ""
                i = 0
                nr += 1
        if line != "":
            line = list(line.ljust(120))
            line[79] = "4"
            lines.append("".join(line))

    file.write("\n".join(lines))
    file.close()
    return True


def find_species(species:str, dictionary: dict[str, Species]) -> Species:
    global defaultMapping
    values: Species
    error = NameError("Species not found")
    values = dictionary.get(species, Species("", State.Unknown))
    if str(values) == "":
        if species in defaultMapping:
            return dictionary[str(defaultMapping[species])]
        alternativ = [x for x in dictionary.keys() if x.upper().startswith(species.upper())]
        if len(alternativ) > 0:
            print("Did not find:", species,"\nDid you mean: ")
            for chem in range(len(alternativ)):
                print(chem,":",alternativ[chem])
            answer = input("Enter number of wanted chemical:")
            if answer == "": answer = "0"
            if answer.isdecimal():
                try:
                    defaultMapping[species] = alternativ[int(answer)]
                    species = str(alternativ[int(answer)])
                except:
                    raise error
            else:
                raise error
        else:
            raise error
    return  dictionary[species]






