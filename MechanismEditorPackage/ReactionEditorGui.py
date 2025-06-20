import copy
import tkinter
import tkinter.messagebox
import tkinter.simpledialog

from MechanismEditorPackage import Interfaces
from MechanismEditorPackage import Reaction_Class
from GeneralUtil.CenterGui import CenterWindow
from MechanismEditorPackage.Interfaces import Checkable, SelfFixing


class UniversalEditorGui(CenterWindow):

    entry_vars: dict[str,tkinter.Variable] = {}
    reaction: Reaction_Class.Reaction

    def __init__(self, to_edit: Reaction_Class.Reaction):
        super().__init__(None)
        if not isinstance(to_edit, Interfaces.EditorAdjusted):
            raise TypeError("to_edit must inherit the type Interfaces.EditorAdjusted")
        self.entry_vars = {}
        self.reaction = to_edit
        self.focus_set()
        self.generate_fields(self.reaction, self, self.reaction.no_edit(),self.reaction.no_show())
        self.update()

    def generate_fields(self, obj: Reaction_Class.Reaction, parent, no_edit: list[str], no_show: list[str], add_save_btn = True):
        dict_version = obj.__dict__
        parent.grid_columnconfigure(1, weight=1)
        i = 0
        for key, value in dict_version.items():
            if key in no_show:
                continue
            state = tkinter.NORMAL
            if key in no_edit:
                state = tkinter.DISABLED
            if key == "is_adjustable" and obj.is_required:
                state = tkinter.DISABLED
            if type(value) == dict:
                frame = tkinter.Frame(parent, name=key.lower(), borderwidth=2, relief=tkinter.RIDGE)
                frame.grid(column=0, row=i, columnspan=2, sticky="nsew", pady=2)
                frame.grid_columnconfigure(1, weight=1)
                sub_dict: dict
                sub_dict = dict_version[key]
                label = tkinter.Label(frame, text=key.lower(), font=("FixedSys", 12, "bold"), width=20, anchor=tkinter.W)
                label.grid(column=0, row=0, columnspan=1, sticky="w")
                add_btn = tkinter.Button(frame, text="+", command=lambda d=value: self.add(d), state=state)
                add_btn.grid(column=1, row=0, sticky="ew")
                j = 1
                min_width = 0
                for value in sub_dict.values():
                    min_width = max(min_width, len(str(value)))

                for dict_key, dict_value in sub_dict.items():
                    sub_element = sub_dict[dict_key]
                    can_json = getattr(sub_element, "toJSON", None)
                    if callable(can_json):
                        sub_element = can_json()
                    label = tkinter.Label(frame, text="  " + dict_key, font=("FixedSys", 12), width=20, anchor=tkinter.W)
                    label.grid(column=0, row=j, sticky="nsew")
                    self.entry_vars[str(obj.reaction_id) + ":" + key + ":" + dict_key] = getVar(sub_element)
                    entry = tkinter.Entry(frame, textvariable=self.entry_vars[str(obj.reaction_id) + ":" + key + ":" + dict_key], state=state, width=min_width)
                    entry.grid(column=1, row=j, sticky="nsew")
                    rem_btn = tkinter.Button(frame, text="-", command=lambda k=dict_key, d=dict_version[key]: self.remove_entry(d, k))
                    rem_btn.grid(column=2, row=j, sticky="nsew")
                    j -= - 1
            elif type(value) == list:
                frame = tkinter.Frame(parent, name=key.lower(), borderwidth=2, relief=tkinter.RIDGE)
                frame.grid(column=0, row=i, columnspan=2, sticky="nsew", pady=2)
                frame.grid_columnconfigure(1, weight=1)
                sub_list: list
                sub_list = dict_version[key]
                label = tkinter.Label(frame, text=key, font=("FixedSys", 12, "bold"), width=20, anchor=tkinter.W)
                label.grid(column=0, row=0, columnspan=1, sticky="w")
                add_btn = tkinter.Button(frame, text="+", command=lambda d=value: self.add(d), state=state)
                add_btn.grid(column=1, row=0, sticky="ew")
                j = 1
                for sub_element in sub_list:
                    can_json = getattr(sub_element, "toJSON", None)
                    if callable(can_json):
                        sub_element = can_json()
                    label = tkinter.Label(frame, text="  " + str(j-1), font=("FixedSys", 12), width=20,
                                          anchor=tkinter.W)
                    label.grid(column=0, row=j, sticky="nsew")
                    self.entry_vars[str(obj.reaction_id) + ":" + key + ":" + str(j-1)] = getVar(sub_element)
                    self.entry_vars[str(obj.reaction_id) + ":" + key + ":" + str(j-1)].set(sub_element)
                    entry = tkinter.Entry(frame, textvariable=self.entry_vars[str(obj.reaction_id) + ":" + key + ":" + str(j-1)], state=state)
                    entry.grid(column=1, row=j, sticky="nsew")
                    rem_btn = tkinter.Button(frame, text="-",
                                             command=lambda k=key + ":" + str(j-1), d=dict_version[key]: self.remove_entry(d, k))
                    rem_btn.grid(column=2, row=j, sticky="nsew")
                    j -= - 1
            elif type(value) == bool:
                sub_bool = dict_version[key]
                text = key
                if text.startswith("is_"):
                    text = text[3:]
                label = tkinter.Label(parent, text=text, font=("FixedSys", 12), width=20, anchor=tkinter.W)
                label.grid(column=0, row=i, sticky="w")
                self.entry_vars[str(obj.reaction_id) + ":" + key] = tkinter.BooleanVar()
                self.entry_vars[str(obj.reaction_id) + ":" + key].set(sub_bool)
                entry = tkinter.Button(parent, text="On" if self.entry_vars[str(obj.reaction_id) + ":" + key].get() else "Off", state=state)
                entry.config(command=lambda k=str(obj.reaction_id) + ":" + key,btn= entry: self.update_btn(k, btn))
                entry.grid(column=1, row=i, sticky="nsew")
            elif type(value) == float:
                sub_float = dict_version[key]
                text = key
                if key == "_A_k":
                    if obj.is_stick:
                        text = "S_0"
                    else:
                        text = "A_k"
                label = tkinter.Label(parent, text=text + " (float)", font=("FixedSys", 12), width=20, anchor=tkinter.W)
                label.grid(column=0, row=i, sticky="w")
                self.entry_vars[str(obj.reaction_id) + ":" + key] = tkinter.DoubleVar()
                self.entry_vars[str(obj.reaction_id) + ":" + key].set("{:g}".format(sub_float))
                entry = tkinter.Entry(parent, textvariable=self.entry_vars[str(obj.reaction_id) + ":" + key], state=state)
                entry.grid(column=1, row=i, sticky = "nsew")
            elif type(value) == int:
                sub_int = dict_version[key]
                label = tkinter.Label(parent, text=key + " (int)", font=("FixedSys", 12), width=20, anchor=tkinter.W)
                label.grid(column=0, row=i, sticky="w")
                self.entry_vars[str(obj.reaction_id) + ":" + key] = tkinter.IntVar()
                self.entry_vars[str(obj.reaction_id) + ":" + key].set(sub_int)
                entry = tkinter.Entry(parent, textvariable=self.entry_vars[str(obj.reaction_id) + ":" + key], state=state)
                entry.grid(column=1, row=i, sticky = "nsew")
            elif type(value) == str:
                sub_str = dict_version[key]
                label = tkinter.Label(parent, text=key + " (str)", font=("FixedSys", 12), width=20, anchor=tkinter.W)
                label.grid(column=0, row=i, sticky="w")
                self.entry_vars[str(obj.reaction_id) + ":" + key] = tkinter.StringVar()
                self.entry_vars[str(obj.reaction_id) + ":" + key].set(sub_str)
                entry = tkinter.Entry(parent, textvariable=self.entry_vars[str(obj.reaction_id) + ":" + key], state=state)
                entry.grid(column=1, row=i, sticky = "nsew")
            else:
                frame = tkinter.Frame(parent, name=key, borderwidth=2, relief=tkinter.RIDGE)
                frame.grid(column=0, row=i, columnspan=2, sticky="nsew", pady=2)
                frame.grid_columnconfigure(1, weight=1)
                sub_dict: dict
                sub_dict = dict_version[key].__dict__
                label = tkinter.Label(frame, text=key, font=("FixedSys", 12, "bold"), anchor=tkinter.W)
                label.grid(column=0, row=0, columnspan=1, sticky="w")
                add_btn = tkinter.Button(frame, text="+", command=lambda d=value: self.add(d), state=state)
                add_btn.grid(column=1, row=0, sticky="ew")
                j = 1
                for dict_key, dict_value in sub_dict.items():
                    sub_element = sub_dict[dict_key]
                    can_json = getattr(sub_element, "toJSON", None)
                    if callable(can_json):
                        sub_element = can_json()
                    label = tkinter.Label(frame, text="  " + dict_key, font=("FixedSys", 12), width=20,
                                          anchor=tkinter.W)
                    label.grid(column=0, row=j, sticky="nsew")
                    self.entry_vars[str(obj.reaction_id) + ":" + key + ":" + dict_key] = getVar(sub_element)
                    self.entry_vars[str(obj.reaction_id) + ":" + key + ":" + dict_key].set(sub_element)
                    entry = tkinter.Entry(frame, textvariable=self.entry_vars[str(obj.reaction_id) + ":" + key + ":" + dict_key], state=state)
                    entry.grid(column=1, row=j, sticky="nsew")
                    rem_btn = tkinter.Button(frame, text="-",
                                             command=lambda k=dict_key, d=dict_version[key]: self.remove_entry(d, k))
                    rem_btn.grid(column=2, row=j, sticky="nsew")
                    j -= - 1

            i -= - 1
        if isinstance(obj, Reaction_Class.Reaction):
            reaction: Reaction_Class.Reaction = obj
            if reaction.is_reversible:
                reverse = reaction.reverse_reaction
                frame = tkinter.Frame(self, height=20)
                frame.grid(column=0, row=i, sticky="w")
                i -= - 1

                label = tkinter.Label(self, text="Reverse Reaction", font=("FixedSys", 14, "bold"), width=20, anchor=tkinter.W)
                label.grid(column=0, row=i, sticky="w")
                i -=- 1
                frame = tkinter.Frame(self, name="reverse_reaction".lower(), borderwidth=5, relief=tkinter.RIDGE, bg="lightgray")
                frame.grid(column=0, row=i, columnspan=2, sticky="nsew", pady=2)
                frame.grid_columnconfigure(1, weight=1)
                i -= - 1
                no_show.append("products")
                no_show.append("educts")
                no_show.append("is_reversible")
                no_show.append("category")
                j = self.generate_fields(reverse, frame, no_edit, no_show, False)
                i += j
        if add_save_btn:
            save_btn = tkinter.Button(self, text="Save", command=self.save)
            save_btn.grid(row=i, column=0, sticky='nsew')
            close_btn = tkinter.Button(self, text="Cancel (Don't Save)", command=lambda: self.ask_destroy())
            close_btn.grid(row=i, column=1, sticky='nsew')
            i -=- 1
        return i

    def ask_destroy(self):
        self.destroy()

    def save(self):
        dupe = copy.deepcopy(self.reaction)
        dict_version = self.read_entrys(dupe)
        if self.reaction.reverse_reaction is not None:
            reverse_dupe = dict_version["_reverse_reaction"]
            self.read_entrys(reverse_dupe)

        if isinstance(dupe, Checkable):
            check: Checkable = dupe
            if check.check():
                dict_version = self.read_entrys(self.reaction)
                if self.reaction.reverse_reaction is not None:
                    reverse_dupe = dict_version["_reverse_reaction"]
                    if isinstance(reverse_dupe, Reaction_Class.Reaction):
                        check: Reaction_Class.Reaction = reverse_dupe
                        if check.check():
                            self.read_entrys(check)
                            self.destroy()
                            return
                        return
                    tkinter.messagebox.showerror("Error", "Data type of reverse reaction for Editor not supported")
                else:
                    self.destroy()
                    return
            return
        tkinter.messagebox.showerror("Error", "Data type for Editor not supported")

    def read_entrys(self, dupe: Reaction_Class.Reaction):
        dict_version = dupe.__dict__
        forward_id = str(dupe.reaction_id) + ":"
        for key, value in dict_version.items():
            if type(value) == dict:
                types1 = set(type(k) for k in value.values())
                instanced = ""
                can_json = ""
                main_type = str.__class__
                if len(types1) == 1:
                    main_type = types1.pop()
                    can_json = getattr(main_type, "fromJSON", None)
                value = dict()
                dict_version[key] = value
                sub_key_list = [k for k in self.entry_vars.keys() if k.split(":")[1] == key]
                sub_key_list = [k for k in sub_key_list if k.split(":")[0] == str(self.reaction.reaction_id)]
                for combi_key in sub_key_list:
                    sub_key = combi_key.split(":")[2]
                    sub_element = self.entry_vars[combi_key].get()
                    if callable(can_json):
                        instanced = copy.deepcopy(main_type)
                        instanced.fromJSON(sub_element)
                        sub_element = instanced
                    value[sub_key] = sub_element
                continue
            if type(value) == list:
                types1 = set(type(k) for k in value)
                instanced = ""
                can_json = ""
                main_type = str.__class__
                if len(types1) == 1:
                    main_type = types1.pop()
                    can_json = getattr(main_type, "fromJSON", None)

                value = list()
                dict_version[key] = value
                sub_key_list = [k for k in self.entry_vars.keys() if k.split(":")[1] == key]
                sub_key_list = [k for k in sub_key_list if k.split(":")[0] == str(self.reaction.reaction_id)]
                for combi_key in sub_key_list:
                    sub_element = self.entry_vars[combi_key].get()
                    if callable(can_json):
                        instanced = copy.deepcopy(main_type)
                        instanced.fromJSON(sub_element)
                        sub_element = instanced
                    value.append(sub_element)
                continue

            if forward_id + key in self.entry_vars:
                sub_element = self.entry_vars[forward_id + key].get()
                can_json = getattr(value, "fromJSON", None)
                if callable(can_json):
                    value.can_json(sub_element)
                    sub_element = value
                setattr(dupe, key, sub_element)
        if isinstance(dupe, SelfFixing):
            dupe.fix()
        return dict_version

    def show(self):
        self.wm_deiconify()
        self.wait_window()

    def add(self, d):
        name = tkinter.simpledialog.askstring("Set name", "Name", parent=self)
        if len(name) > 8:
            tkinter.messagebox.showerror("Error", "Name too long, max 8 characters")
            return
        else:
            d[name] = 0
        for widget in self.winfo_children():
            widget.destroy()
        self.entry_vars.clear()
        self.generate_fields(self.reaction, self, self.reaction.no_edit(),self.reaction.no_show())

    def remove_entry(self, sub_dict, sub_key):
        if sub_key in sub_dict:
            sub_dict.pop(sub_key)
        for widget in self.winfo_children():
            widget.destroy()
        self.entry_vars.clear()
        self.generate_fields(self.reaction, self, self.reaction.no_edit(), self.reaction.no_show())

    def update_btn(self, key, btn):
        self.entry_vars[key].set(not self.entry_vars[key].get())
        btn.configure(text="On" if self.entry_vars[key].get() else "Off")
        btn.update()

def getVar(fieldElement):
    if type(fieldElement) == dict:
        var = tkinter.StringVar()
        var.set(str(fieldElement))
        return var
    elif type(fieldElement) == list:
        var = tkinter.StringVar()
        var.set(str(fieldElement))
        return var
    elif type(fieldElement) == bool:
        var = tkinter.BooleanVar()
        var.set(fieldElement)
        return var
    elif type(fieldElement) == float:
        var = tkinter.DoubleVar()
        var.set(fieldElement)
        return var
    elif type(fieldElement) == int:
        var = tkinter.IntVar()
        var.set(fieldElement)
        return  var
    elif type(fieldElement) == str:
        var = tkinter.StringVar()
        var.set(fieldElement)
        return  var
    else:
        var = tkinter.StringVar()
        var.set(fieldElement)
        return var

