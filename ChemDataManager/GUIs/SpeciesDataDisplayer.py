from collections.abc import Callable

from ChemDataManager import global_vars, ConfigHandler
from ChemDataManager.GUIs import DataEditor
from GeneralUtil import TextModifiers
from GeneralUtil.CenterGui import CenterWindow
import tkinter as tk


class SpeciesDisplay(CenterWindow):

    chem_checks: list[tk.Checkbutton]
    therm_checks: list[tk.Checkbutton]

    def __init__(self, parent, species_name: str):
        super().__init__(parent)

        self.species = global_vars.chemData[species_name]
        self.species_name = species_name
        self.chem_checks = list()
        self.therm_checks = list()
        row = 0
        column = 0
        #title = tk.Label(self, text=species_name, font=("Arial", 20))

        title = TextModifiers.generate_spec_text(self,species_name,20)

        title.grid(row=row, column=0, sticky='nsew')
        row -=- 1

        chemFrame = tk.Frame(self)
        chemFrame.grid(row=row, column=0, sticky='nsew', padx=10, pady=10)
        row -= - 1

        self.load_chem_frame(chemFrame)
        self.update_chem_checks()

        thermFrame = tk.Frame(self)
        thermFrame.grid(row=row, column=0, sticky='nsew', padx=10, pady=10)
        row -= - 1

        self.load_therm_frame(thermFrame)
        self.update_therm_checks()

        confirm_btn = tk.Button(self, text="Confirm", command=self.destroy)
        confirm_btn.grid(row=row, column=0, sticky='nsew', padx=10, pady=10)
        row -= - 1

        self.bind('<Escape>', lambda e:self.destroy())
        self.center()

    def focus_action(self, e: tk.Event):
        btn: tk.Checkbutton = e.widget
        if btn.cget("state") == "disabled":
            return
        btn.toggle()
        btn.invoke()


    def update_chem_checks(self, c= None):
        pair = global_vars.selected_data[self.species_name]
        if c is not None:
            idx = self.chem_checks.index(c)
            if self.species[0][idx] == pair[0]:
                pair = (None, pair[1])
            else:
                pair = (self.species[0][idx], pair[1])
            global_vars.selected_data[self.species_name] = pair
        for idx in range(len(self.chem_checks)):
            if self.species[0][idx] == pair[0]:
                self.chem_checks[idx].select()
            else:
                self.chem_checks[idx].deselect()

    def load_chem_frame(self, chemFrame):
        chemDataTitle = tk.Label(chemFrame, text="Transport Data", font=("Arial", 16), anchor=tk.W)
        chemDataTitle.grid(row=0, column=0, columnspan=2, sticky='nsew')
        column = 3
        label = tk.Label(chemFrame, text="geometry", anchor=tk.E, width=10)
        column = self.add_label(column, label, 0)
        label = tk.Label(chemFrame, text="molar_mass", anchor=tk.E, width=10)
        column = self.add_label(column, label, 0)
        label = tk.Label(chemFrame, text="lj potential", anchor=tk.E, width=10)
        column = self.add_label(column, label, 0)
        label = tk.Label(chemFrame, text="lj collision", anchor=tk.E, width=10)
        column = self.add_label(column, label, 0)
        label = tk.Label(chemFrame, text="dipole_moment", anchor=tk.E, width=15)
        column = self.add_label(column, label, 0)
        label = tk.Label(chemFrame, text="polarizability", anchor=tk.E, width=10)
        column = self.add_label(column, label, 0)
        label = tk.Label(chemFrame, text="rrc number", anchor=tk.E, width=10)
        column = self.add_label(column, label, 0)
        label = tk.Label(chemFrame, text="comment_chem", anchor=tk.W)
        column = self.add_label(column, label, 0)
        divider = tk.Frame(chemFrame, bg="black", height=1)
        divider.grid(row=1, column=0, columnspan=column, sticky='nsew')
        line = 2

        def open_editor(chem_data):
            DataEditor.MolDataDisplayer(self, chem_data).show()
            for child in chemFrame.winfo_children():
                child.destroy()
            self.chem_checks = list()
            self.load_chem_frame(chemFrame)

        for chemData in self.species[0]:
            column = 0
            source = global_vars.libData[chemData.source]
            click_effect = lambda e, c=chemData: open_editor(c)


            checker = tk.Checkbutton(chemFrame)
            checker.bind("<KeyRelease-Return>",click_effect)  # For Enter key release
            checker.config(command=lambda c=checker: self.update_chem_checks(c))
            checker.config(text=str(source.creation_date.year), anchor=tk.W)
            self.chem_checks.append(checker)
            column = self.add_label(column, checker, line)

            author = source.author
            if len(source.author) > 20:
                author = source.author[:17] + "..."
            label = tk.Label(chemFrame, text=author, width=16, anchor=tk.W)
            column = self.add_label(column, label, line)
            column -= - 1
            label = tk.Label(chemFrame, text=chemData.geometry, anchor=tk.E)

            column = self.add_label(column, label, line, click_effect)
            label = tk.Label(chemFrame, text="{:g}".format(chemData.molar_mass), anchor=tk.E)
            column = self.add_label(column, label, line, click_effect)
            label = tk.Label(chemFrame, text=chemData.lennard_jones_potential, anchor=tk.E)
            column = self.add_label(column, label, line, click_effect)
            label = tk.Label(chemFrame, text=chemData.lennard_jones_collision, anchor=tk.E)
            column = self.add_label(column, label, line, click_effect)
            label = tk.Label(chemFrame, text=chemData.dipole_moment, anchor=tk.E)
            column = self.add_label(column, label, line, click_effect)
            label = tk.Label(chemFrame, text=chemData.polarizability, anchor=tk.E)
            column = self.add_label(column, label, line, click_effect)
            label = tk.Label(chemFrame, text=chemData.rotational_relaxation_collision_number, anchor=tk.E)
            column = self.add_label(column, label, line, click_effect)
            label = tk.Label(chemFrame, text=chemData.comment_chem, anchor=tk.W)
            column = self.add_label(column, label, line, click_effect)
            line -= - 1
        divider = tk.Frame(chemFrame, bg="black", width=1)
        divider.grid(row=0, column=2, rowspan=line, sticky='nsew')

    def update_therm_checks(self, c= None):
        pair = global_vars.selected_data[self.species_name]
        if c is not None:
            idx = self.therm_checks.index(c)
            if self.species[1][idx] == pair[1]:
                pair = (pair[0], None)
            else:
                pair = (pair[0], self.species[1][idx])
            global_vars.selected_data[self.species_name] = pair
        for idx in range(len(self.therm_checks)):
            if self.species[1][idx] == pair[1]:
                self.therm_checks[idx].select()
            else:
                self.therm_checks[idx].deselect()


    def load_therm_frame(self, thermFrame):
        chemDataTitle = tk.Label(thermFrame, text="Therm Data", font=("Arial", 16), anchor=tk.W)
        chemDataTitle.grid(row=0, column=0, columnspan=2, sticky='nsew')
        column = 3
        line = 0
        label = tk.Label(thermFrame, text="State", anchor=tk.W)
        column = self.add_label(column, label, line)
        label = tk.Label(thermFrame, text="Composition", anchor=tk.W)
        column = self.add_label(column, label, line)
        label = tk.Label(thermFrame, text="Graph", anchor=tk.W)
        column = self.add_label(column, label, line)
        divider = tk.Frame(thermFrame, bg="black", height=1)
        divider.grid(row=1, column=0, columnspan=column, sticky='nsew')
        line = 2

        def open_editor(therm_data):
            DataEditor.ThermDataDisplayer(self, therm_data).show()
            for child in thermFrame.winfo_children():
                child.destroy()
            self.therm_checks = list()
            self.load_therm_frame(thermFrame)

        for chemData in self.species[1]:
            column = 0
            source = global_vars.libData[chemData.source]
            click_effect = lambda e, c=chemData: open_editor(c)

            checker = tk.Checkbutton(thermFrame)
            checker.bind("<KeyRelease-Return>",click_effect)  # For Enter key release
            checker.config(command=lambda c=checker: self.update_therm_checks(c))
            checker.config(text=str(source.creation_date.year), anchor=tk.W)
            self.therm_checks.append(checker)
            column = self.add_label(column, checker, line)

            author = source.author
            if len(source.author) > 20:
                author = source.author[:17] + "..."
            label = tk.Label(thermFrame, text=author, width=16, anchor=tk.W)
            column = self.add_label(column, label, line)



            column -= - 1
            label = tk.Label(thermFrame, text=chemData.state, anchor=tk.W)
            column = self.add_label(column, label, line, click_effect)
            comp = ""
            for atom, count in chemData.atoms.items():
                comp += atom + ":" + str(count) + ";"
            comp = comp[:-1]
            label = tk.Label(thermFrame, text=comp, anchor=tk.W)
            column = self.add_label(column, label, line, click_effect)
            line -= - 1

        divider = tk.Frame(thermFrame, bg="black", width=1)
        divider.grid(row=0, column=2, rowspan=line, sticky='nsew')

    def add_label(self, column, label, line, click_effect:Callable= None):
        if click_effect is not None:
            label.config(cursor = "pencil")
        label.grid(row=line, column=column, sticky='nsew')
        label.bind("<Button-1>", click_effect)
        column -= - 1
        return column

    def destroy(self):
        ConfigHandler.update_config()
        super().destroy()

