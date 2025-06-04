import json
import pathlib

from ChemDataManager import global_vars


def update_config():
    print("Updating config")
    config_file = open('ChemDataManager/config.json', 'w')
    config_ob = dict()
    config_ob["author"] = global_vars.author
    config_ob["university"] = global_vars.university
    config_ob["email"] = global_vars.email
    current_selection = global_vars.selected_data

    # spec, type(mol/therm), source
    selection_stored: dict[str, (int|None, int|None)] = dict()
    for spec,value in current_selection.items():
        key_1 = None
        key_2 = None
        if value[0] is not None:
            key_1 = value[0].source
        if value[1] is not None:
            key_2 = value[1].source
        if key_1 is not None or key_2 is not None:
            selection_stored[spec] = (key_1, key_2)


    config_ob["default_selection"] = selection_stored
    config = json.dumps(config_ob, indent=4)
    config_file.write(config)
    config_file.close()

def load_config():
    print("Loading config")
    path = "ChemDataManager/config.json"
    path = pathlib.Path(path).absolute()
    try:
        config_file = open(path, 'r')
    except FileNotFoundError:
        config_file = open(path, 'x')
        config_file.close()
        return

    config = json.load(config_file)
    config_file.close()
    global_vars.author = config['author']
    global_vars.university = config['university']
    global_vars.email = config['email']
    if 'default_selection' in config:
        all_data = global_vars.chemData
        selection = global_vars.selected_data
        stored_selection: dict[str, (int|None, int|None)] = config['default_selection']
        for spec_key,value in stored_selection.items():
            reg_data = all_data[spec_key]
            if value[0] is not None:
                if reg_data[0] is not None:
                    for spec in reg_data[0]:
                        if spec.source == value[0]:
                            selection[spec_key] = (spec, selection[spec_key][1])
                            break
            if value[1] is not None:
                if reg_data[1] is not None:
                    for spec in reg_data[1]:
                        if spec.source == value[1]:
                            selection[spec_key] = (selection[spec_key][0], spec)






