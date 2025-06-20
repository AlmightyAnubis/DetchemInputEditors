
import tkinter as tk
from tkinter import messagebox, filedialog

from ChemDataManager import ConfigHandler

from ChemDataManager import global_vars, ReadData, ReadExternalFile
from ChemDataManager.GUIs import CommitGui
from ChemDataManager.GUIs.SourceDataDisplayer import SourceDisplay
from ChemDataManager.GUIs.SpeciesDataDisplayer import SpeciesDisplay
from GeneralUtil import SelectionDialog
from GeneralUtil.CenterGui import CenterRootWindow


class ListGui(CenterRootWindow):

    box: tk.Listbox
    filter_var: tk.StringVar

    def __init__(self, parent):
        super().__init__(parent)

        self.grid_columnconfigure(4,weight=1)
        self.grid_rowconfigure(2,weight=1)
        title = tk.Label(self, text="Chemical Data Manager", font=("Arial", 20))
        title.grid(row=0, column=0, columnspan = 7, sticky=tk.NSEW, padx=5, pady=5)

        self.filter_var = tk.StringVar()
        searchbar = tk.Entry(self, textvariable=self.filter_var, font=("Arial", 16))
        self.filter_var.trace("w",lambda a,b,c: self.update_selection())
        searchbar.grid(row=1, column=0, columnspan = 5, sticky=tk.NSEW, padx=5, pady=5)
        info_box = tk.Label(self, text="Use \"*:\" to use fuzzy search", font=("Arial", 16))
        info_box.grid(row=1, column=5, columnspan = 2, sticky=tk.NSEW, padx=5, pady=5)

        data = ReadData.readChemData()
        lib_data = ReadData.readLibData()
        global_vars.chemData = data
        global_vars.libData = lib_data

        global_vars.selected_data = {}
        for spec, info in data.items():
            global_vars.selected_data[spec] = (None, None)

        try:
            ConfigHandler.load_config()
        except Exception as e:
            print(e)

        self.load_element_display()

        export_button = tk.Button(self,text="Import Simulation File", font=("Arial", 12), command=lambda :self.import_file())
        export_button.grid(row=3, column=0, sticky=tk.EW, padx=5, pady=5)
        export_button = tk.Button(self,text="Export Simulation Files", font=("Arial", 12), command=lambda :self.export_file())
        export_button.grid(row=3, column=1, sticky=tk.EW, padx=5, pady=5)
        upload_button = tk.Button(self,text="Save Changes Locally", font=("Arial", 12), command=lambda :self.save_locally())
        upload_button.grid(row=3, column=2, sticky=tk.EW, padx=5, pady=5)
        upload_button = tk.Button(self,text="Upload Changes", font=("Arial", 12), command=lambda :self.save_online())
        upload_button.grid(row=3, column=3, sticky=tk.EW, padx=5, pady=5)

        def clear_selection():
            answer = messagebox.askokcancel("Clear Data","Are you sure you want to clear the entire selection?")
            if answer!=tk.YES:
                return
            for spec in global_vars.selected_data.keys():
                global_vars.selected_data[spec] = (None, None)
            ConfigHandler.update_config()
            self.update_selection()

        clear_button = tk.Button(self,text="Clear Selection", font=("Arial", 12), width=10, command=clear_selection)
        clear_button.grid(row=3, column=5, sticky=tk.EW, padx=5, pady=5)
        close_button = tk.Button(self,text="Close", font=("Arial", 12), width=10, command=lambda :self.destroy())
        close_button.grid(row=3, column=6, sticky=tk.EW, padx=5, pady=5)

        self.center()


    def move_selection(self, event: tk.Event, delta: int):
        cur = self.box.curselection()[0] + delta
        cur = max(0, cur)
        if 0 <= cur < self.box.size():
            event.widget.selection_clear(0, tk.END)
            event.widget.select_set(cur)

    def focus_selection(self, event: tk.Event):
        if not self.box.curselection():
            event.widget.select_set(0)


    def load_element_display(self):
        self.box = tk.Listbox(self, selectmode=tk.SINGLE, font=("Arial", 16))
        self.box.bind('<Up>', lambda e:self.move_selection(e,-1))
        self.box.bind('<Down>',lambda e: self.move_selection(e,1))
        self.box.bind('<Return>', lambda event: self.open_data())
        self.box.bind('<Double-1>', lambda event: self.open_data())
        self.box.bind('<FocusIn>', self.focus_selection)
        self.box.grid(row=2, column=0, columnspan=7, sticky=tk.NSEW, padx=10)
        self.update_selection()


    def import_file(self):
        answer = SelectionDialog.GeneralDialog("Choose type of import file:", ["thermdata", "moldata"]).center().show()
        if answer == "":
            return

        dir_name = filedialog.askopenfilename()
        if dir_name == "":
            return

        display = SourceDisplay(self)
        display.show()
        id = display.selected_id

        if answer == "thermdata":
            answer = ReadExternalFile.read_thermdata(dir_name,id)
            for spec in global_vars.chemData.keys():
                if spec not in global_vars.selected_data.keys():
                    global_vars.selected_data[spec] = (None, None)
            if answer>=0:
                messagebox.showinfo("Thermal Data Imported", "Thermal Data >" + dir_name + "< successfully Imported")
        if answer == "moldata":
            answer = ReadExternalFile.read_moldata(dir_name,id)
            for spec in global_vars.chemData.keys():
                if spec not in global_vars.selected_data.keys():
                    global_vars.selected_data[spec] = (None, None)
            if answer >= 0:
                messagebox.showinfo("Molecular Data Imported", "Molecular Data >" + dir_name + "< successfully Imported")
        self.load_element_display()

    def export_file(self):
        folder = filedialog.askdirectory()
        if folder == "":
            return
        ReadExternalFile.write_thermdata(folder)
        ReadExternalFile.write_moldata(folder)

        messagebox.showinfo("Data Exported", "Data exported to >" + folder + "< successfully")

    def save_locally(self):
        ReadData.writeChemData(global_vars.chemData)
        ReadData.writeLibData(global_vars.libData)

    def save_online(self):
        CommitGui.CommitHandler(self).show()

    def open_data(self):
        selected = self.box.curselection()[0]
        selected_str: str = self.box.get(selected)
        displayer = SpeciesDisplay(self, selected_str.split("\t")[1])
        displayer.show()
        if len(self.children) != 0:
            self.update_selection()
        self.box.selection_clear(0, tk.END)
        self.box.select_set(selected)
        self.box.activate(selected)
        self.box.see(selected)

    def update_selection(self):
        data = global_vars.chemData
        selection = global_vars.selected_data
        self.box.delete(0, tk.END)
        filter_text = self.filter_var.get()
        filter_text = filter_text.lower()
        fuzzy = False
        if filter_text == "":
            fuzzy = True
        if filter_text.startswith("*:"):
            fuzzy = True
            filter_text = filter_text.replace("*:","")

        for spec, info in data.items():
            if fuzzy:
                if filter_text not in spec.lower():
                    continue
            else:
                if filter_text != spec.lower():
                    continue
            color = "black"
            if spec not in selection:
                spec_string = "□\t"
            else:
                select = selection[spec]
                if select == (None, None):
                    spec_string = "☐\t"
                elif select[0] is None:
                    spec_string = "🌡\t"
                    color = "red"
                elif select[1] is None:
                    spec_string = "〰\t"
                    color = "blue"
                else:
                    spec_string = "✓\t"
                    color = "green"
            self.box.insert(tk.END, spec_string + spec)
            self.box.itemconfig(tk.END, foreground=color)




    def show(self):
        self.wm_deiconify()
        self.wait_window()

    def destroy(self):
        super().destroy()
        ConfigHandler.update_config()



gui = ListGui(None)
gui.focus_set()
gui.title("Reaction Gui")
gui.lift()
gui.attributes('-topmost', True)
gui.attributes('-topmost', False)
gui.update()
gui.center()
gui.show()
