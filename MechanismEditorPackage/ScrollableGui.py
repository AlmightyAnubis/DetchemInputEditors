import math
import os
import tkinter
import tkinter.messagebox
from tkinter import *
from tkinter.scrolledtext import ScrolledText

from MechanismEditorPackage import Config, Text_Util
from MechanismEditorPackage import EditorGui
from MechanismEditorPackage import ReactionEditorGuiUpdate
from MechanismEditorPackage import global_vars
from GeneralUtil.CenterGui import CenterRootWindow
from MechanismEditorPackage.Reaction_Class import Reaction
from MechanismEditorPackage.SpeciesDisplay import SpeciesDisplayGUI
from MechanismEditorPackage.Widgets import StatusBarWidget
from MechanismEditorPackage.adjustclass import AdjustClass, update_adjustables


class ListGui(CenterRootWindow):

    listbox: ScrolledText = None
    reaction_mapper : dict[str,tuple[str,int, dict[str,StatusBarWidget|Label]]] = {}
    reverse_mapper: dict[Reaction|str, str] = {}
    placeholder = 'Search'
    save_content = "non"
    hidden_categorys :list[str] = list()
    search_var: tkinter.StringVar = None

    def __init__(self, adjust: AdjustClass):
        super().__init__()

        self.adjust_obj = adjust
        self.grid_rowconfigure(2, weight=1)
        self.grid_columnconfigure(3, weight=1)

        text_size = Config.text_size

        width = 30
        search_var = tkinter.StringVar()
        self.search_var = search_var
        search_var.set("Search")
        search_bar = tkinter.Entry(self, textvariable=search_var, fg="gray", width=width, font=("Arial", text_size-2))
        search_bar.grid(column=0, row=0, pady = (5,0), padx = 5, sticky="w")
        search_var.trace("w", lambda name,index,mode: self.update_search())

        help_label = tkinter.Label(self, text="\'*:\' Fuzzy Search" + "\n"  + "\'e:\' Search in Educts" + "\n"  + "\'p:\' Search in Products", anchor=tkinter.W, justify=tkinter.LEFT, font=("Arial", text_size))
        help_label.grid(column=0, row=1, columnspan=2, sticky="w")

        def update_adjust(adjust_object: AdjustClass) -> None:
            adjust_data = adjust_object.adjust_data
            EditorGui.UniversalEditorGui(self,adjust_data).show()
            adjust_object.adjust_data = adjust_data
            adjust_config = os.path.join(global_vars.parent, "adjust.json")
            target = open(adjust_config, "w")
            target.write(adjust_data.toJSON(pretty=True))
            target.close()


        edit_adjust_btn = tkinter.Button(self,text="Edit Adjust Data (use careful)",command=lambda :update_adjust(adjust), width=width, font=("Arial", text_size))
        edit_adjust_btn.grid(column=1, row=0, pady = (5,0), padx = 5, sticky="ew")

        species_btn = tkinter.Button(self,text="Show species data",command=lambda :SpeciesDisplayGUI(self, self.adjust_obj).center().show(), width=width, font=("Arial", text_size))
        species_btn.grid(column=1, row=1, pady = (5,0), padx = 5, sticky="ew")

        # Secures the placement of all other elements
        space_frame = tkinter.Frame(self)
        space_frame.grid(column=3, row=0, sticky="ew")

        new_btn = tkinter.Button(self,text="New Reaction (WIP)",command=self.add_reaction, width=width, font=("Arial", text_size+4), state=tkinter.DISABLED)
        new_btn.grid(column=4, row=0, pady = (5,0), padx = 5, rowspan = 2, sticky="nwse")


        def erase(event=None):
            if search_bar.get() == self.placeholder:
                search_bar.delete(0, 'end')
                search_bar.config(fg="black")
        def add(event=None):
            if search_bar.get() == '':
                search_bar.insert(0, self.placeholder)
                search_bar.config(fg="gray")

        search_bar.bind('<FocusIn>', erase)
        search_bar.bind('<FocusOut>', add)

        self.container = Frame(self, relief=tkinter.RIDGE, borderwidth=3)
        self.container.grid(row=2, column=0, columnspan = 5, sticky='nsew')
        self.container.grid_rowconfigure(0, weight=1)
        self.container.grid_columnconfigure(0, weight=1)

        self.listbox = ScrolledText(self.container, state=DISABLED, relief=FLAT, bg= self.container["background"], cursor = "arrow")

        self.listbox.grid(row=0, column=0, pady = 5, sticky='nsew')
        self.listbox.bind_all('<MouseWheel>', self.scroll)

        self.container = Frame(self.listbox)
        self.listbox.window_create('1.0', window=self.container, padx=5, pady=5, stretch=1)

        #for x in range(100):
        #    listNodes.insert(END, str(x))

        i = 0
        def hide_category(event=None, category=None):
            if category == None:
                return
            if category in self.hidden_categorys:
                self.hidden_categorys.remove(category)
            else:
                self.hidden_categorys.append(category)
            self.update_search()

        for reaction_category in global_vars.reactions:
            header_label = tkinter.Label(self.container, name="header:" + reaction_category, text=(" V " + str(reaction_category)).ljust(160,"-"), fg="gray", font=("Arial", (
                        Config.text_size * 5) // 4, "bold"), anchor=tkinter.W)
            self.reaction_mapper[str(header_label)] = (reaction_category, -1, dict())
            self.reverse_mapper[reaction_category] = str(header_label)
            header_label.bind("<Button-1>", lambda event, cat = reaction_category: hide_category(event, cat))
            header_label.grid(row=i, column=0, columnspan=3, sticky='nsew')
            i -=- 1
            for j in range(len(global_vars.reactions[reaction_category])):
                reaction_frame = tkinter.Frame(self.container, name="frame:" + reaction_category+ ":" + str(j))
                widgets = self.add_reaction_to_frame(global_vars.reactions[reaction_category][j], reaction_frame)
                self.reaction_mapper[str(reaction_frame)] = (reaction_category, j, widgets)
                self.reverse_mapper[global_vars.reactions[reaction_category][j]] = str(reaction_frame)
                reaction_frame.grid(row=i, column=0, sticky='nsew')
                i -=- 1

        save_btn = tkinter.Button(self, text="Save as copy", command=lambda: Text_Util.save_file("copy"), width=width, font=("Arial", text_size))
        save_btn.grid(row=3, column=0, padx = 5, pady = 5, sticky='nsw')

        overwrite_btn = tkinter.Button(self, text="Overwrite", command=lambda:Text_Util.save_file("overwrite"), width=width, font=("Arial", text_size))
        overwrite_btn.grid(row=3, column=1, padx = 5, pady = 5, sticky='nsw')

        def run_adjust():
            self.adjust_obj.adjust()
            for reaction_category in global_vars.reactions:
                for j in range(len(global_vars.reactions[reaction_category])):
                    self.update_reaction_values(global_vars.reactions[reaction_category][j])

        adjust_btn = tkinter.Button(self, text="Adjust", command=lambda: run_adjust(), width=width, font=("Arial", text_size))
        adjust_btn.grid(row=3, column=2, padx = 5, pady = 5, sticky='nsw')

        close_btn = tkinter.Button(self, text="Close (Don't Save)", command=lambda: self.ask_destroy(), width=width, font=("Arial", text_size))
        close_btn.grid(row=3, column=4, padx = 5, pady = 5, sticky='nse')

    def scroll(self, event):
        current_view = self.listbox.yview()
        self.listbox.yview_moveto(current_view[0] + event.delta/120 * (-1) * 0.01)




    def ask_destroy(self):
        answer = tkinter.messagebox.askokcancel("Don't save", "Are you sure you don't want to save?")
        if answer:
            self.destroy()


    def update_search(self):
        filter_txtstr = self.search_var.get()
        if filter_txtstr == self.placeholder:
            filter_txtstr = "*:"
        if filter_txtstr == "":
            filter_txtstr = "*:"
        for child in self.container.winfo_children():
            child.grid_forget()
        entry_nr = 0
        i = 0
        mode = ""
        if filter_txtstr.startswith("e:"):
            mode = "e"
            filter_txtstr = filter_txtstr.replace("e:", "", 1).strip().upper()
        elif filter_txtstr.startswith("p:"):
            mode = "p"
            filter_txtstr = filter_txtstr.replace("p:", "", 1).strip().upper()
        elif filter_txtstr.startswith("*:"):
            mode = "*"
            filter_txtstr = filter_txtstr.replace("*:", "", 1).strip().upper()


        for category in global_vars.reactions:
            hidden = category in self.hidden_categorys
            if hidden:
                text = (" > " + str(category)).ljust(160, "-")
            else:
                text = (" V " + str(category)).ljust(160, "-")
            header_label_name = self.reverse_mapper[category]
            header_label = self.container.nametowidget(header_label_name)
            header_label.config(text=text)
            header_label.grid(row=i, column=0, columnspan=3, sticky='nsew')
            i -=- 1
            if not hidden:
                for index in range(len(global_vars.reactions[category])):
                    text = str(global_vars.reactions[category][index])
                    reaction_frame_name = self.reverse_mapper[global_vars.reactions[category][index]]
                    reaction_frame = self.container.nametowidget(reaction_frame_name)
                    if mode == "e":
                        for educt in global_vars.reactions[category][index].educts:
                            if filter_txtstr == educt.strip().upper():
                                reaction_frame.grid(row=i, column=0, sticky='nsew')
                                i -=- 1
                                break
                    elif mode == "p":
                        for product in global_vars.reactions[category][index].products:
                            if filter_txtstr == product.strip().upper():
                                reaction_frame.grid(row=i, column=0, sticky='nsew')
                                i -=- 1
                                break
                    elif mode == "*":
                        if filter_txtstr in text.upper():
                            reaction_frame.grid(row=i, column=0, sticky='nsew')
                            i -=- 1
                    else:
                        flag = True
                        for educt in global_vars.reactions[category][index].educts:
                            if filter_txtstr.strip().upper() == educt.strip().upper():
                                reaction_frame.grid(row=i, column=0, sticky='nsew')
                                i -=- 1
                                flag = False
                                break
                        if flag:
                            for product in global_vars.reactions[category][index].products:
                                if filter_txtstr.strip().upper() == product.strip().upper():
                                    reaction_frame.grid(row=i, column=0, sticky='nsew')
                                    i -=- 1
                                    break

    # def update_reaction_frame(self, reverse):
    #     reaction_frame_name = self.reverse_mapper.pop(reverse)
    #     frame = self.container.nametowidget(reaction_frame_name)
    #     (reaction_category, j, widgets) = self.reaction_mapper.pop(reaction_frame_name)
    #     for child in frame.winfo_children():
    #         child.destroy()
    #     widgets = self.add_reaction_to_frame(reverse, frame,
    #                                          Config.text_size)
    #     self.reaction_mapper[str(frame)] = (reaction_category, j, widgets)
    #     self.reverse_mapper[reverse] = str(frame)

    def update_data(self):
        mover = list()
        for category in global_vars.reactions.keys():
            for i in range(len(global_vars.reactions[category])):
                if global_vars.reactions[category][i].category != category:
                    mover.append((category, global_vars.reactions[category][i].category, global_vars.reactions[category][i]))
        for move in mover:
            if move[1] not in global_vars.reactions.keys():
                global_vars.reactions[move[1]] = list()
            global_vars.reactions[move[1]].append(move[2])
            global_vars.reactions[move[0]].remove(move[2])
        to_pop = list()
        for category in global_vars.reactions.keys():
            if len(global_vars.reactions[category]) == 0:
                to_pop.append(category)
        for pop in to_pop:
            global_vars.reactions.pop(pop)

        for child in self.container.winfo_children():
            child.destroy()
        self.reverse_mapper.clear()
        self.reverse_mapper.clear()

        def hide_category(event=None, category=None):
            if category == None:
                return
            if category in self.hidden_categorys:
                self.hidden_categorys.remove(category)
            else:
                self.hidden_categorys.append(category)
            self.update_search()

        i = 0
        for reaction_category in global_vars.reactions:
            header_label = tkinter.Label(self.container, name="header:" + reaction_category, text=str(reaction_category).ljust(160,"-"), fg="gray", font=("Arial", (
                        Config.text_size * 5) // 4, "bold"), anchor=tkinter.W)
            self.reaction_mapper[str(header_label)] = (reaction_category, -1, dict())
            self.reverse_mapper[reaction_category] = str(header_label)
            header_label.bind("<Button-1>", lambda event, cat = reaction_category: hide_category(event, cat))
            header_label.grid(row=i, column=0, columnspan=3, sticky='nsew')
            i -=- 1
            for j in range(len(global_vars.reactions[reaction_category])):
                reaction_frame = tkinter.Frame(self.container, name="frame:" + reaction_category+ ":" + str(j))
                widgets = self.add_reaction_to_frame(global_vars.reactions[reaction_category][j], reaction_frame)
                self.reaction_mapper[str(reaction_frame)] = (reaction_category, j, widgets)
                self.reverse_mapper[global_vars.reactions[reaction_category][j]] = str(reaction_frame)
                reaction_frame.grid(row=i, column=0, sticky='nsew')
                i -=- 1


    def show(self):
        self.wm_deiconify()
        self.wait_window()

    def add_reaction(self):
        firstKey = list(global_vars.reactions.keys())[0]
        reaction = Reaction(category=firstKey, is_reversible=True)
        global_vars.reactions[firstKey].append(reaction)

        j = global_vars.reactions[firstKey].index(reaction)
        reaction_frame = tkinter.Frame(self.container, name="frame:" + firstKey + ":" + str(j))
        widgets = self.add_reaction_to_frame(reaction, reaction_frame)
        self.reaction_mapper[str(reaction_frame)] = (firstKey, j, widgets)
        self.reverse_mapper[reaction] = str(reaction_frame)

        EditorGui.UniversalEditorGui(self, reaction).show()
        self.update_data()
        self.update_search()

    no_garbage_collector = list()

    def add_reaction_to_frame(self, reaction, frame):
        text_size = Config.text_size
        widgets = dict()
        i = 0
        label = tkinter.Label(frame, text=reaction.name, anchor=tkinter.E, width=4)
        label.grid(row=0, column=i, sticky=tkinter.NSEW)
        i -= - 1
        adjustable = tkinter.IntVar()
        adjustable.set(reaction.is_adjustable)
        self.no_garbage_collector.append(adjustable)
        state = tkinter.NORMAL
        if reaction.is_required:
            state = tkinter.DISABLED
        box = tkinter.Checkbutton(frame, variable=adjustable,disabledforeground="green", state=state)
        def toggle_btn(reac: Reaction):
            reac.is_adjustable = not reac.is_adjustable
            update_adjustables(self)
            self.update_reaction_frame(reaction)
        adjustable.trace_add('write', lambda a,b,c, reac = reaction: toggle_btn(reac))
        box.grid(row = 0, column = i, sticky=tkinter.NSEW)
        i -=- 1

        def update_weight(reac: Reaction, var):
            try:
                reac.weight = var.get()
            except tkinter.TclError:
                pass
        variable = tkinter.DoubleVar()
        self.no_garbage_collector.append(variable)
        variable.set(reaction.weight)

        weight_entry = tkinter.Entry(frame, font=('Arial', text_size), width=5, textvariable=variable)
        variable.trace_add('write', lambda a,b,c,reac = reaction,var = variable: update_weight(reac, var))
        weight_entry.grid(row = 0, column = i, sticky=tkinter.NSEW)
        i -=- 1
        self.add_species_label(reaction, frame, reaction.educts, i, text_size)
        i -= - 1
        if reaction.is_reversible:
            text = "<->"
        else:
            text = "->"
        label = tkinter.Label(frame, text=text, width=3,anchor=tkinter.E, font=("Arial", text_size), cursor = "pencil")
        label.bind("<Button-1>", lambda event, r = reaction: self.edit_reaction(r))
        label.grid(row=0, column=i, sticky=tkinter.NSEW)
        i -= - 1
        self.add_species_label(reaction, frame, reaction.products, i, text_size)
        i -= - 1
        label = tkinter.Frame(frame, width=10)
        label.grid(row=0, column=i, sticky=tkinter.NSEW)
        i -= - 1
        label = tkinter.Frame(frame, width=1, bg="black")
        label.grid(row=0, column=i, sticky=tkinter.NSEW)
        i -= - 1
        label = tkinter.Frame(frame, width=10)
        label.grid(row=0, column=i, sticky=tkinter.NSEW)
        i -= - 1


        if reaction.is_stick:
            title = "S=" + "{:10.2E}".format(reaction.get_A_k(True))
        else:
            title = "A=" + "{:10.2E}".format(reaction.get_A_k(True))
        label = tkinter.Label(frame, text=title, width=12,anchor=tkinter.E, font=("Arial", text_size), borderwidth=1, cursor = "bottom_left_corner",activebackground="gray")
        label.bind("<Button-1>", lambda event, reac=reaction: self.show_graph(reac))
        label.grid(row=0, column=i, sticky=tkinter.NSEW)
        widgets["A_k_label"] = label
        i -= - 1
        value = 0
        if reaction.old_A_k != 0:
            value = math.log10(reaction.A_k/reaction.old_A_k)
        if reaction.is_stick:
            value = math.log(reaction.A_k/reaction.old_A_k) / math.log(2.)
        status = StatusBarWidget(frame, text_size*5,value)
        status.grid(row=0, column=i, sticky=tkinter.NS)
        widgets["A_k_status"] = status
        i -= - 1
        label = tkinter.Label(frame, text="{:.4f}".format(reaction.get_beta_k(True)), width=10, anchor=tkinter.E, font=("Arial", text_size), cursor ="bottom_left_corner", activebackground="gray")
        label.bind("<Button-1>", lambda event, reac=reaction: self.show_graph(reac))
        label.grid(row=0, column=i, sticky=tkinter.NSEW)
        widgets["beta_k_label"] = label
        i -= - 1
        status = StatusBarWidget(frame, text_size * 5, reaction.beta_k - reaction.old_beta_k)
        status.grid(row=0, column=i, sticky=tkinter.NS)
        widgets["beta_k_status"] = status
        i -= - 1
        label = tkinter.Label(frame, text="{:10.2F}".format(reaction.E_k*1e-3), width=10,anchor=tkinter.E, font=("Arial", text_size), cursor = "bottom_left_corner",activebackground="gray")
        label.bind("<Button-1>", lambda event, reac=reaction: self.show_graph(reac))
        label.grid(row=0, column=i, sticky=tkinter.NSEW)
        widgets["E_k_label"] = label
        i -= - 1
        status = StatusBarWidget(frame, text_size*5,(reaction.E_k-reaction.old_E_k)/1e3/5.)
        status.grid(row=0, column=i, sticky=tkinter.NS)
        widgets["E_k_status"] = status
        i -= - 1
        label = tkinter.Frame(frame, width=1, bg="black")
        label.grid(row=0, column=i, sticky=tkinter.NSEW)
        i -= - 1
        if reaction.reverse_reaction is not None:
            reverse = reaction.reverse_reaction
            label = tkinter.Frame(frame, width=10)
            label.grid(row=0, column=i, sticky=tkinter.NSEW)
            i -= - 1

            adjustable_r = tkinter.IntVar()
            adjustable_r.set(reverse.is_adjustable)
            self.no_garbage_collector.append(adjustable_r)
            state = tkinter.NORMAL
            if reverse.is_required:
                state = tkinter.DISABLED
            box = tkinter.Checkbutton(frame, variable=adjustable_r, disabledforeground="green", state=state)
            adjustable_r.trace_add('write', lambda a,b,c, reac=reverse: toggle_btn(reac))
            box.grid(row=0, column=i, sticky=tkinter.NSEW)
            i -= - 1

            variable = tkinter.DoubleVar()
            self.no_garbage_collector.append(variable)
            variable.set(reverse.weight)
            weight_entry = tkinter.Entry(frame, font=('Arial', text_size), width=5, textvariable=variable)
            variable.trace_add('write', lambda a, b, c, reac=reverse, var=variable: update_weight(reac, var))
            weight_entry.grid(row=0, column=i, sticky=tkinter.NSEW)
            i -= - 1
            title = "{:10.2E}".format(reverse.get_A_k(True))
            if reverse.is_stick:
                title = "S=" + title
            else:
                title = "A=" + title
            label = tkinter.Label(frame, text=title, width=12, anchor=tkinter.E, font=("Arial", text_size),
                                  borderwidth=1, cursor="bottom_left_corner", activebackground="gray")
            label.bind("<Button-1>", lambda event, reac=reverse: self.show_graph(reac))
            label.grid(row=0, column=i, sticky=tkinter.NSEW)
            widgets["r_A_k_label"] = label
            i -= - 1
            value = 0
            if reverse.old_A_k != 0:
                value = math.log10(reverse.A_k / reverse.old_A_k)
            if reverse.is_stick:
                value = math.log(reverse.A_k / reverse.old_A_k) / math.log(2.)
            status = StatusBarWidget(frame, text_size * 5, value)
            status.grid(row=0, column=i, sticky=tkinter.NS)
            widgets["r_A_k_status"] = status
            i -= - 1
            label = tkinter.Label(frame, text="{:.4F}".format(reverse.get_beta_k(True)), width=10, anchor=tkinter.E,
                                  font=("Arial", text_size), cursor="bottom_left_corner", activebackground="gray")
            label.bind("<Button-1>", lambda event, reac = reverse: self.show_graph(reac))
            label.grid(row=0, column=i, sticky=tkinter.NSEW)
            widgets["r_beta_k_label"] = label
            i -= - 1
            status = StatusBarWidget(frame, text_size * 5, reverse.beta_k - reverse.old_beta_k)
            status.grid(row=0, column=i, sticky=tkinter.NS)
            widgets["r_beta_k_status"] = status
            i -= - 1
            label = tkinter.Label(frame, text="{:10.2F}".format(reverse.get_E_k(True) * 1e-3), width=10, anchor=tkinter.E,
                                  font=("Arial", text_size), cursor="bottom_left_corner", activebackground="gray")
            label.bind("<Button-1>", lambda event, reac=reverse: self.show_graph(reac))
            label.grid(row=0, column=i, sticky=tkinter.NSEW)
            widgets["r_E_k_label"] = label
            i -= - 1
            status = StatusBarWidget(frame, text_size * 5, (reverse.E_k - reverse.old_E_k) / 1e3 / 5.)
            status.grid(row=0, column=i, sticky=tkinter.NS)
            widgets["r_E_k_status"] = status
            i -= - 1
            label = tkinter.Frame(frame, width=1, bg="black")
            label.grid(row=0, column=i, sticky=tkinter.NSEW)
            i -= - 1

        return widgets

    def add_species_label(self, reaction, frame, species, i, text_size):
        text = ""
        for key, value in species.items():
            text += str(value) + str(key) + " + "
        text = text[:-3]
        label = tkinter.Label(frame, text=text, width=20, anchor=tkinter.W, font=("Arial", text_size), cursor = "pencil")
        label.bind("<Button-1>", lambda event,r= reaction: self.edit_reaction(r))
        label.grid(row=0, column=i, sticky=tkinter.NSEW)

    def edit_reaction(self, reaction):
        pre_cat = reaction.category
        ReactionEditorGuiUpdate.ReactionEditorGui(self, reaction).center().show()
        if pre_cat == reaction.category:
            self.update_reaction_frame(reaction)
        else:
            self.update_data()
        self.update_search()


    def update_reaction_frame(self, reverse):
        reaction_frame_name = self.reverse_mapper.pop(reverse)
        frame = self.container.nametowidget(reaction_frame_name)
        (reaction_category, j, widgets) = self.reaction_mapper.pop(reaction_frame_name)
        for child in frame.winfo_children():
            child.destroy()
        widgets = self.add_reaction_to_frame(reverse, frame)
        self.reaction_mapper[str(frame)] = (reaction_category, j, widgets)
        self.reverse_mapper[reverse] = str(frame)

    def update_reaction_values(self, reaction):
        reaction_frame_name = self.reverse_mapper.pop(reaction)
        frame = self.container.nametowidget(reaction_frame_name)
        (reaction_category, j, widgets) = self.reaction_mapper.pop(reaction_frame_name)

        if reaction.is_stick:
            title = "S=" + "{:10.2E}".format(reaction.get_A_k(True))
        else:
            title = "A=" + "{:10.2E}".format(reaction.get_A_k(True))
        label = widgets["A_k_label"]
        label.configure(text = title)
        value = 0
        if reaction.old_A_k != 0:
            value = math.log10(reaction.A_k/reaction.old_A_k)
        if reaction.is_stick:
            value = math.log(reaction.A_k/reaction.old_A_k) / math.log(2.)
        status = widgets["A_k_status"]
        status.set_size(value)

        label = widgets["beta_k_label"]
        label.configure(text="{:.4F}".format(reaction.get_beta_k(True)))

        status = widgets["beta_k_status"]
        status.set_size(reaction.beta_k - reaction.old_beta_k)

        label = widgets["E_k_label"]
        label.configure(text="{:10.2F}".format(reaction.E_k*1e-3))

        status = widgets["E_k_status"]
        status.set_size((reaction.E_k-reaction.old_E_k)/1e3/5.)

        if reaction.reverse_reaction is not None:
            reverse = reaction.reverse_reaction

            title = "{:10.2E}".format(reverse.get_A_k(True))
            if reverse.is_stick:
                title = "S=" + title
            else:
                title = "A=" + title
            label = widgets["r_A_k_label"]
            label.configure(text=title)

            value = 0
            if reverse.old_A_k != 0:
                value = math.log10(reverse.A_k / reverse.old_A_k)
            if reverse.is_stick:
                value = math.log(reverse.A_k / reverse.old_A_k) / math.log(2.)
            status = widgets["r_A_k_status"]
            status.set_size(value)

            label = widgets["r_beta_k_label"]
            label.configure(text="{:.4F}".format(reverse.get_beta_k(True)))

            status = widgets["r_beta_k_status"]
            status.set_size(reverse.beta_k - reverse.old_beta_k)

            label = widgets["r_E_k_label"]
            label.configure(text="{:10.2F}".format(reverse.E_k * 1e-3))

            status = widgets["r_E_k_status"]
            status.set_size((reverse.E_k - reverse.old_E_k) / 1e3 / 5.)

        self.reaction_mapper[str(frame)] = (reaction_category, j, widgets)
        self.reverse_mapper[reaction] = str(frame)

    def show_graph(self, reac: Reaction):
        top = Toplevel(bg="white")
        top.title(reac.name)
        canvas = Canvas(top, width=450, height=450, bg="white")
        canvas.grid(row=0, column=0, sticky=N + S + E + W)

        # canvas coordinate system
        X1, X2 = 40, 455
        Y1, Y2 = 430, 5

        # data
        Tref = self.adjust_obj.T_ref
        kf0 = [reac.kf(T) for T in Tref]
        kf1 = [reac.kf_old(T) for T in Tref]
        try:
            rreac = reac.reverse_reaction
            kf2 = [self.adjust_obj.old2new[rreac].kr(T) for T in Tref]
        except:
            kf2 = kf1

        x1 = 1. / max(Tref)
        x2 = 1. / min(Tref)
        y2 = math.log(max(kf0 + kf1 + kf2), 10)
        y1 = math.log(min(kf0 + kf1 + kf2), 10)

        # conversion functions
        XX = lambda x: int(X1 + (x - x1) / (x2 - x1) * (X2 - X1) + 0.5)
        YY = lambda y: int(Y1 + (y - y1) / (y2 - y1) * (Y2 - Y1) + 0.5)

        # create coordinate system
        T1 = int(min(Tref) / 100) * 100
        T2 = int(max(Tref) / 100 + 1) * 100
        lastX = X2 + 80
        for T in range(T1, T2, 100):
            X = XX(1. / T)
            canvas.create_line(X, Y1, X, Y2, dash=(1,))
            if abs(lastX - X) > 80:
                canvas.create_text(X, Y1 + 2, text="%i" % T, anchor=N)
                lastX = X
        lastY = Y1 + 40
        for y in range(int(y1), int(y2) + 1):
            mantissa = [1]
            if y2 - y1 < 3: mantissa = list(range(1, 10))
            for i in mantissa:
                Y = YY(y + math.log(i, 10))
                canvas.create_line(X1, Y, X2, Y, dash=(1,))
                if abs(lastY - Y) > 40:
                    canvas.create_text(X1 - 2, Y, text="%iE%i" % (i, y), anchor=E)
                    lastY = Y

        # create lines
        for kf, color in ((kf0, "blue"), (kf2, "green"), (kf1, "red")):
            coords = []
            for T, k in zip(Tref, kf):
                coords.append(XX(1. / T))
                coords.append(YY(math.log(k, 10)))
            canvas.create_line(fill=color, width=3, *coords)

        # create legend
        canvas.create_text(X2 - 20, Y2 + 20, fill="blue", text="before ADJUST", anchor=NE)
        canvas.create_text(X2 - 20, Y2 + 35, fill="red", text="after ADJUST", anchor=NE)
        canvas.create_text(X2 - 20, Y2 + 50, fill="green", text="therm. target", anchor=NE)

        top.mainloop()
        top.quit()



