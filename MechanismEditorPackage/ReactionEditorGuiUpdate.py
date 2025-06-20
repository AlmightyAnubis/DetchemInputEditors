import tkinter
from tkinter import messagebox, simpledialog
from typing import Any

from MechanismEditorPackage import Config, global_vars
from GeneralUtil.CenterGui import CenterWindow
from MechanismEditorPackage.Reaction_Class import Reaction
from GeneralUtil import ThermalDataReader


class ReactionEditorGui(CenterWindow):

    entry_vars: dict[str,tkinter.Variable] = {}
    reaction: Reaction

    events: list[tuple[str,Any]] = list()


    def __init__(self, parent, to_edit: Reaction):
        super().__init__(master = parent)
        self.entry_vars = {}
        self.reaction = to_edit

        self.generate_fields(self.reaction)
        self.bind("<Control-z>", lambda event: self.undo())
        self.update()

    def undo(self) -> None:
        if self.events:
            last = self.events.pop(-1)
            self.entry_vars[last[0]].set(last[1])
            self.events.pop(-1)

    def generate_fields(self, reaction):
        i = 0
        self.grid_columnconfigure((0,2), weight=1)
        self.grid_rowconfigure((2), weight=1)
        educts = reaction.educts
        products = reaction.products
        category = reaction.category

        category_frame = tkinter.Frame(self)
        category_frame.grid(row = i, column = 0, sticky = tkinter.NSEW)
        i -=- 1
        category_label = tkinter.Label(category_frame, text = "Category:")
        category_label.grid(row = 0, column = 0, sticky = tkinter.NSEW)

        def update_category(reac: Reaction, var):
            try:
                old_value = reaction.category
                reac.category = var.get()
                self.events.append(("category" , old_value))
            except tkinter.TclError:
                pass

        variable = tkinter.StringVar()
        self.entry_vars["category"] = variable
        variable.set(category)
        category_entry = tkinter.Entry(category_frame, textvariable = variable)
        variable.trace_add("write", lambda a, b, c, var=variable, reac=reaction: update_category(reac, var))
        category_entry.grid(row = 0, column = 1, sticky = tkinter.NSEW)



        educts_frame = tkinter.Frame(self, background="lightblue")
        educts_frame.grid(row=i, column=0, sticky='nsew')
        educts_frame.grid_columnconfigure(list(range(10)), weight=1)
        self.put_species_on_frame(educts, educts_frame, "lightblue")

        text = "->"
        if reaction.is_reversible:
            text = "<->"
        arrow_label = tkinter.Label(self, text=text, font=('Arial', Config.text_size))
        arrow_label.grid(row=i, column=1, sticky='nsew')

        products_frame = tkinter.Frame(self, background="bisque")
        products_frame.grid(row=i, column=2, sticky='nsew')
        products_frame.grid_columnconfigure(list(range(10)), weight=1)
        self.put_species_on_frame(products, products_frame, "bisque")
        i -= - 1

        hline = tkinter.Frame(self, background="black", height=2)
        hline.grid(row=i, column=0, columnspan = 3, sticky='nsew')
        i -=- 1


        forward_frame = tkinter.Frame(self, background="lightblue", borderwidth=5)
        forward_frame.grid(row=i, column=0, sticky='nsew')
        forward_frame.grid_columnconfigure(1, weight=1)
        prefix = "_fwd"
        line = self.add_general_reaction_parameter(forward_frame, reaction, prefix, "lightblue")

        is_stick_label = tkinter.Label(forward_frame, text="Stick Reaction:", background="lightblue",
                                       font=('Arial', Config.text_size), anchor=tkinter.W)
        is_stick_label.grid(row=line, column=0, sticky='nsew')
        variable = tkinter.IntVar()
        self.entry_vars["is_stick" + prefix] = variable
        variable.set(reaction.is_stick)

        def toggle_stick(reac: Reaction, var):
            reac.is_stick = not reac.is_stick
            var.set(reac.is_stick)

        is_stick_btn = tkinter.Button(forward_frame, textvariable=variable,
                                      command=lambda reac=reaction, var=variable: toggle_stick(reac, var),
                                      font=('Arial', Config.text_size - 2))
        is_stick_btn.grid(row=line, column=1, sticky='nsew')
        line -= - 1

        backward_frame = tkinter.Frame(self, background="bisque", borderwidth=5)
        backward_frame.grid(row=i, column=2, sticky='nsew')
        if reaction.is_reversible:
            self.add_general_reaction_parameter(backward_frame, reaction.reverse_reaction, "_bwd", "bisque")
        i -= - 1

        hline = tkinter.Frame(self, background="black", height=2)
        hline.grid(row=i, column=0, columnspan = 3,pady=(0,5) , sticky='nsew')
        i -=- 1

    def add_general_reaction_parameter(self, frame, reaction, prefix, color):
        line = 0
        text = "A:"
        if reaction.is_stick:
            text = "S:"
        ak_label = tkinter.Label(frame, text=text, background=color, font=('Arial', Config.text_size),
                                 anchor=tkinter.W)
        ak_label.grid(row=line, column=0, sticky='nsew')
        variable = tkinter.DoubleVar()
        self.entry_vars["A" + prefix] = variable
        variable.set(reaction.get_A_k(True))

        def update_A(reac: Reaction, var):
            try:
                old_value = reaction.get_A_k(True)
                reac.set_A_k(var.get(), True)
                self.events.append(("A" + prefix, old_value))
            except tkinter.TclError:
                pass

        ak_edit = tkinter.Entry(frame, textvariable=variable, font=('Arial', Config.text_size - 2))
        variable.trace_add("write", lambda a, b, c, var=variable, reac=reaction: update_A(reac, var))
        ak_edit.grid(row=line, column=1, sticky='nsew')
        line -= - 1
        beta_label = tkinter.Label(frame, text="beta:", background=color,
                                   font=('Arial', Config.text_size), anchor=tkinter.W)
        beta_label.grid(row=line, column=0, sticky='nsew')
        variable = tkinter.DoubleVar()
        self.entry_vars["beta" + prefix] = variable
        variable.set(reaction.get_beta_k(True))

        def update_beta(reac: Reaction, var):
            try:
                old_value = reaction.get_beta_k(True)
                reac.set_beta_k(var.get(), True)
                self.events.append(("beta" + prefix, old_value))
            except tkinter.TclError:
                pass

        beta_edit = tkinter.Entry(frame, textvariable=variable, font=('Arial', Config.text_size - 2))
        variable.trace_add("write", lambda a, b, c, var=variable, reac=reaction: update_beta(reac, var))
        beta_edit.grid(row=line, column=1, sticky='nsew')
        line -= - 1
        E_A_label = tkinter.Label(frame, text="E_A:", background=color, font=('Arial', Config.text_size),
                                  anchor=tkinter.W)
        E_A_label.grid(row=line, column=0, sticky='nsew')
        variable = tkinter.DoubleVar()
        self.entry_vars["E_A" + prefix] = variable
        variable.set(reaction.get_E_k(True))

        def update_EA(reac: Reaction, var):
            try:
                old_value = reaction.get_E_k(True)
                reac.set_E_k(var.get(), True)
                self.events.append(("E_A" + prefix, old_value))
            except tkinter.TclError:
                pass

        E_A_edit = tkinter.Entry(frame, textvariable=variable, font=('Arial', Config.text_size - 2))
        variable.trace_add("write", lambda a, b, c, var=variable, reac=reaction: update_EA(reac, var))
        E_A_edit.grid(row=line, column=1, sticky='nsew')
        line -= - 1

        epsilon = reaction.epsilon
        epsilon_frame = tkinter.Frame(frame, background=color, borderwidth=2, relief="groove")
        epsilon_frame.grid_columnconfigure(1,weight=1)
        epsilon_label = tkinter.Label(epsilon_frame, text="Epsilon", background=color, font=('Arial', Config.text_size))
        epsilon_label.grid(row=0, column=0, sticky='nsew')


        def add_epsilon(eps):
            name = simpledialog.askstring("Species","Species for epsilon", parent=self)
            if name == "":
                return
            try:
                ThermalDataReader.find_species(name, global_vars.thermalDataMap)
                eps[name] = 0
                for child in self.winfo_children():
                    child.destroy()
                self.generate_fields(self.reaction)
            except NameError:
                messagebox.showerror("Species not found", "Species not found")
            finally:
                self.focus_set()

        epsilon_add_btn = tkinter.Button(epsilon_frame, text="+", command=lambda eps=epsilon:add_epsilon(eps))
        epsilon_add_btn.grid(row=0, column=1, sticky='nsew')
        ep_line = 1
        for ep in epsilon:
            sub_ep_label = tkinter.Label(epsilon_frame, text=ep, background=color, font=('Arial', Config.text_size), anchor=tkinter.W)
            sub_ep_label.grid(row=ep_line, column=0, sticky='nsew')
            variable = tkinter.DoubleVar()
            self.entry_vars["epsilon_" + ep + prefix] = variable
            variable.set(epsilon[ep])
            def update_eps(reac: Reaction, var, eps):
                try:
                    old_value = reac.epsilon[eps]
                    reaction.epsilon[eps] = var.get()
                    self.events.append(("epsilon_" + eps + prefix, old_value))
                except tkinter.TclError:
                    pass
            sub_ep_edit = tkinter.Entry(epsilon_frame, textvariable=variable)
            variable.trace_add("write",lambda a,b,c,reac=reaction, var = variable, eps=ep: update_eps(reac, var, eps))

            sub_ep_edit.grid(row=ep_line, column=1, sticky='nsew')

            def remove_epsilon(eps):
                epsilon.pop(eps)
                for child in self.winfo_children():
                    child.destroy()
                self.generate_fields(self.reaction)

            sub_ep_rem_btn = tkinter.Button(epsilon_frame, text="-", command=lambda eps= ep: remove_epsilon(eps))
            sub_ep_rem_btn.grid(row=ep_line, column=2, sticky='nsew')
            ep_line -=- 1

        epsilon_frame.grid(row=line, column=0, columnspan=2, sticky='nsew')
        line -=- 1






        return line


    # educts: dict[str, int]
    # products: dict[str, int]
    # orders: dict[str, float]
    # epsilon: dict[str, float]
    # _A_k = 0
    # _beta_k = 0
    # _E_k = 0
    # old_A_k = 0
    # old_beta_k = 0
    # old_E_k = 0
    # is_stick = False
    # is_reversible = False
    # _reverse_reaction = None
    # is_disabled = False
    # category = ""
    # weight = 1
    # is_adjustable = True
    # is_required = False
    # exponent = -2
    # reaction_id: int = None
    # temperature_independent_term: float = None

    def put_species_on_frame(self, educts, educts_frame, color):
        last_plus = None
        col = 0
        for educt in educts:
            for i in range(educts[educt]):
                label = tkinter.Label(educts_frame, text=educt, font=('Arial', Config.text_size), background=color)
                label.bind("<Button-1>", lambda e, ed=educt: self.remove_reactants(educts, ed))
                label.grid(row=0, column=col, sticky='nsew')
                col += 1
                label = tkinter.Label(educts_frame, text="+", font=('Arial', Config.text_size), background=color)
                label.grid(row=0, column=col, sticky='nsew')
                last_plus = label
                col += 1
        if last_plus is not None:
            last_plus.grid_forget()
            col -= 1
        add_btn = tkinter.Button(educts_frame, text="+", font=('Arial', Config.text_size), background=color, command= lambda:self.add_reactants(educts))
        add_btn.grid(row=0, column=col)
        return last_plus

    def add_reactants(self, educts):
        species_name = simpledialog.askstring("Species Name", "Species Name: ", parent=self)
        if len(species_name) > 8:
            tkinter.messagebox.showerror("Error", "Name too long, max 8 characters", parent=self)
            return
        try:
            ThermalDataReader.find_species(species_name, global_vars.thermalDataMap)
            if species_name in educts:
                educts[species_name] += 1
            else:
                educts[species_name] = 1

            educts = self.reaction.educts
            products = self.reaction.products

            total_spec = 0
            for educt in educts:
                total_spec += educts[educt]
            for product in products:
                total_spec += products[product]
            if total_spec > 5:
                messagebox.showerror("Error", "Too many species in reaction. Please limit them to 5", parent=self)

            for child in self.winfo_children():
                child.destroy()
            self.generate_fields(self.reaction)
        except NameError:
            messagebox.showerror("Species Name Not Found", "Species Name Not Found")
        finally:
            self.focus_set()


    def remove_reactants(self, educts, educt):
        result = messagebox.askyesno("Remove species","Do you really want to remove " + educt, parent=self)
        self.focus_set()
        if result:
            educts[educt] -= 1
            if educts[educt] == 0:
                educts.pop(educt)
            for child in self.winfo_children():
                child.destroy()
            self.generate_fields(self.reaction)

    def show(self):
        self.wm_deiconify()
        self.wait_window()
        self.reaction.fix()

