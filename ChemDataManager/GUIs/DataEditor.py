import math
import tkinter as tk
from tkinter import filedialog

import matplotlib
import numpy
import numpy as np
from PIL.XbmImagePlugin import xbm_head
from matplotlib import pyplot as plt
from matplotlib.axes import Axes
from matplotlib.backend_bases import MouseEvent, Event

from matplotlib.backends._backend_tk import NavigationToolbar2Tk
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure
from matplotlib.lines import Line2D

from ChemDataManager import global_vars, Omega_Table
from ChemDataManager.ChemDataFormat import ChemData
from ChemDataManager.GUIs import SourceDataDisplayer
from GeneralUtil import Nat_Constants, MaterialData
from GeneralUtil.CenterGui import CenterWindow
from GeneralUtil.Errors import OutOfBoundError
from GeneralUtil.MaterialData import Species


class MolDataDisplayer(CenterWindow):

    variables: list = []

    self_diff: tuple[list[float],list[float]]
    viscosity: tuple[list[float],list[float]]
    heat_conductivity: tuple[list[float],list[float]]
    plot: Axes
    chem_data: ChemData
    limits = (300,5000)
    toolbar: tk.Label = None
    ref: list[Line2D] = None

    active_plot: tuple[list[float],list[float]] = None


    def __init__(self, master, chem_data: ChemData):
        super().__init__(master)
        self.chem_data = chem_data
        source = global_vars.libData[self.chem_data.source]
        self.source = source
        row = 0
        label = tk.Label(self, text="Transport Data", font=("Arial", 20))
        label.grid(row=row, column=0, columnspan=4)
        row -=- 1
        label = tk.Label(self, text="Source:", anchor=tk.W)
        label.grid(row=row, column=0, sticky=tk.EW)
        author = source.author
        if len(source.author) > 20:
            author = source.author[:17] + "..."
        edit = tk.Label(self, text=str(source.creation_date.year) + " " + author, cursor = "pencil")

        edit.bind("<Button-1>", lambda event: select_source(self, self.chem_data.source))
        edit.grid(row=row, column=1, sticky=tk.EW)
        row -=- 1
        self.add_property(row,"geometry", var = tk.IntVar())
        row -=- 1
        self.add_property(row,"molar_mass", "gray")
        row -=- 1
        self.add_property(row,"lennard_jones_potential")
        row -=- 1
        self.add_property(row,"lennard_jones_collision")
        row -=- 1
        self.add_property(row,"dipole_moment")
        row -=- 1
        self.add_property(row,"polarizability")
        row -=- 1
        self.add_property(row,"rotational_relaxation_collision_number")
        row -=- 1


        x:list[float] = []
        self_diff:list[float] = []
        viscosity:list[float] = []
        heat_conductivity:list[float] = []

        self.self_diff = (x, self_diff)
        self.viscosity = (x, viscosity)
        self.heat_conductivity = (x, heat_conductivity)

        self.calculate_values()
        plot1: Axes

        plot_frame = tk.Frame(self)

        self.create_plot(plot_frame)

        btn_frame = tk.Frame(self)
        btn_frame.grid_rowconfigure(list(range(3)), weight=1)
        btn_frame.grid_columnconfigure(list(range(3)), weight=1)
        btn_frame.grid(row=row, column=0, columnspan=2, sticky=tk.EW)
        row -=- 1
        vis_btn = tk.Button(btn_frame, text="Viscosity", command=lambda: self.plot_array(self.viscosity))
        vis_btn.grid(row=0, column=0, sticky=tk.EW, padx=5, pady=5)
        diff_btn = tk.Button(btn_frame, text="Diffusion", command=lambda: self.plot_array(self.self_diff))
        diff_btn.grid(row=0, column=1, sticky=tk.EW, padx=5, pady=5)
        diff_btn = tk.Button(btn_frame, text="Heat Conductivity", command=lambda: self.plot_array(self.heat_conductivity))
        diff_btn.grid(row=0, column=2, sticky=tk.EW, padx=5, pady=5)



        spacer = tk.Frame(self)
        spacer.grid(row=row, column=1, sticky=tk.NS)
        self.grid_rowconfigure(row, weight=1)

        spacer = tk.Frame(self, width=30)
        spacer.grid(row=1, column=2)

        plot_frame.grid(row=1, column=3, rowspan=row, sticky=tk.NSEW)
        row -= - 1

        confirm_btn = tk.Button(self, text="Confirm", command=self.destroy)
        confirm_btn.grid(row=row, column=0, columnspan = 4, sticky='nsew', padx=10, pady=10)
        row -= - 1
        self.bind('<Escape>', lambda e: self.destroy())
        self.center()

    def plot_array(self, array):
        self.active_plot = array
        self.calculate_values()
        self.clear_plot()
        self.ref = self.plot.plot([0, 0], [0, 0])

        all_zero = all([v == 0 for v in array[1]])
        if all_zero:
            self.plot.set_title("Missing Thermdata, select one to proceed")
        else:
            self.plot.set_title("")
        x = np.array(array[1])
        selected = x != -1

        x = np.extract(selected, array[0])
        y = np.extract(selected, array[1])

        self.plot.plot(x, y)
        set_xstep_size(self.plot,self.limits[0],self.limits[1])
        self.plot.set_xlim(self.limits[0] - 50,self.limits[1] + 50)
        self.plot.figure.canvas.draw()


    def add_property(self, row, text, color = "black", var: tk.Variable = None):
        title = text.split("_")
        for i in range(len(title)):
            title[i] = title[i].capitalize()
        title = " ".join(title)
        title += ": "
        label = tk.Label(self, text=title, anchor=tk.W)
        label.grid(row=row, column=0, sticky=tk.EW)
        dict_version = self.chem_data.__dict__
        if var is None:
            var = tk.DoubleVar()
        var.set(dict_version[text])
        edit = tk.Entry(self, textvariable=var, justify=tk.RIGHT, fg=color)
        edit.grid(row=row, column=1, sticky=tk.EW)
        def set_value(var,text,e):
            dict_version = self.chem_data.__dict__
            if e.get() != "":
                dict_version[text] = var.get()

        var.trace_add("write", lambda a,b,c,v=var,t=text, e=edit: set_value(var,t,e))

    def show_current_value(self, event:MouseEvent) -> None:
        x = event.xdata
        if x is None:
            return
        x_lim = self.plot.get_xlim()
        y_lim = self.plot.get_ylim()
        self.ref[0].set_data([x,x], [y_lim[0], y_lim[1]])
        self.plot.set_xlim(x_lim)
        self.plot.set_ylim(y_lim)
        self.plot.figure.canvas.draw()

        if self.active_plot is None:
            return
        x_data = np.array(self.active_plot[0])
        idx = np.argmax(x_data > x)
        y_data = np.array(self.active_plot[1])
        y = y_data[idx]
        self.toolbar.configure(text="x= {:g} y={:g}".format(x,y))

    def create_plot(self, parent):
        # the figure that will contain the plot
        fig = Figure(figsize=(5, 5),
                     dpi=100)
        # adding the subplot
        self.plot = plot1 = fig.subplots()
        self.ref = self.plot.plot([0, 0], [0, 0])
        # plotting the graph
        plot1.ticklabel_format(axis='y', scilimits=[-3, 3])
        plot1.grid(True)
        # creating the Tkinter canvas
        # containing the Matplotlib figure
        canvas = FigureCanvasTkAgg(fig, master=parent)
        canvas.draw()
        canvas.mpl_connect(
            'motion_notify_event', self.show_current_value)

        # placing the canvas on the Tkinter window
        canvas.get_tk_widget().pack()

        self.toolbar = tk.Label(parent, text="x: y: ", anchor=tk.CENTER)
        self.toolbar.pack(side=tk.TOP, fill=tk.BOTH)

        # Add import btn
        import_btn = tk.Button(parent,text="Compare Experimental Data", command=lambda: import_data(self,self.plot))
        import_btn.pack(expand=True, fill=tk.Y)



    def clear_plot(self):
        self.plot.clear()
        self.plot.ticklabel_format(axis='y', scilimits=[-3, 3])
        self.plot.grid(True)


    def calculate_values(self):
        x:list[float] = self.self_diff[0]
        self_diff:list[float] = self.self_diff[1]
        viscosity:list[float] = self.viscosity[1]
        heat_conductivity: list[float] = self.heat_conductivity[1]

        if self.chem_data.species not in global_vars.selected_data:
            heat_conductivity.append(0)
        data = global_vars.selected_data[self.chem_data.species][1]
        spec = None
        if data is not None:
            spec = Species(data.species, state=MaterialData.convert_state(data.state))
            spec.set_temp_max(data.high_temperature)
            spec.set_temp_min(data.low_temperature)
            spec.set_temp_switch(data.jump_temperature)
            for coefficient in data.coefficients:
                spec.add_coefficient(coefficient)


        x.clear()
        self_diff.clear()
        viscosity.clear()
        heat_conductivity.clear()

        M = self.chem_data.molar_mass
        if M==-1:
            M = 10
        M /= 1e3

        p = 101325.0  # Pa
        col = self.chem_data.lennard_jones_collision * 1e-10
        epsilon = self.chem_data.lennard_jones_potential * Nat_Constants.k_b
        omega_table = numpy.array(Omega_Table.omega_table)
        T_star_0 = Nat_Constants.k_b * 298 / epsilon
        f_Z_0 = 1 + math.pi ** 1.5 / 2 / math.sqrt(T_star_0) + (math.pi ** 2 / 4 + 2) / T_star_0 + (math.pi / T_star_0) ** 1.5
        for T in range(self.limits[0],self.limits[1],50):
            rho = p*M/(Nat_Constants.R*T)
            T_star =Nat_Constants.k_b * T/epsilon

            bool_var = omega_table[:,1]<T_star
            target_line_nr = len(omega_table[bool_var,1])-1
            target_line_nr = min(target_line_nr, len(omega_table[:,1])-2)
            target_line = omega_table[target_line_nr,:]
            next_line = omega_table[target_line_nr+1,:]
            dipol = Nat_Constants.debye * self.chem_data.dipole_moment
            delta = dipol**2/(8*math.pi*Nat_Constants.epsilon *epsilon*col**3)
            mult_vec = numpy.array([1,delta**1,delta**2,delta**3,delta**4])

            omega11_1 = numpy.sum(numpy.multiply(mult_vec, target_line[2:7]))
            omega11_2 = numpy.sum(numpy.multiply(mult_vec, next_line[2:7]))
            omega22_1 = numpy.sum(numpy.multiply(mult_vec, target_line[7:]))
            omega22_2 = numpy.sum(numpy.multiply(mult_vec, next_line[7:]))
            T1_star = target_line[1]
            T2_star = next_line[1]

            omega11 = omega11_1+(omega11_2-omega11_1)/(T2_star-T1_star)*(T_star-T1_star)
            omega22 = omega22_1 + (omega22_2 - omega22_1) / (T2_star - T1_star) * (T_star - T1_star)

            x.append(float(T))
            self_diff.append(3 / 8 * math.sqrt(math.pi * Nat_Constants.N_A * (Nat_Constants.k_b * T) ** 3 / M) / (p * math.pi * col ** 2 * omega11))
            viscosity.append(5 / 16 * math.sqrt(math.pi * M * Nat_Constants.k_b * T / Nat_Constants.N_A) / (math.pi * col ** 2 * omega22))

            cV_tra = 1.5 * Nat_Constants.R
            cV_rot = 0
            if self.chem_data.geometry > 0:
                cV_rot = (self.chem_data.geometry+1)/2*Nat_Constants.R

            f_Z = 1+ math.pi**1.5/2/math.sqrt(T_star)+(math.pi**2/4+2)/T_star+(math.pi/T_star)**1.5
            Z_rot = self.chem_data.rotational_relaxation_collision_number * f_Z_0/f_Z
            f_vib = rho*self_diff[-1]/viscosity[-1]
            A = 5/2 - f_vib
            B = Z_rot+2/math.pi*(5/3*cV_rot/Nat_Constants.R+f_vib)
            f_tra = 2.5*(1-2/math.pi*cV_rot/cV_tra*A/B)
            f_rot = f_vib*(1+2/math.pi*A/B)

            if spec is None:
                heat_conductivity.append(0)
                continue
            try:
                cV = spec.get_cp(T) * Nat_Constants.R
            except OutOfBoundError:
                heat_conductivity.append(-1)
                continue
            cV_vib = cV - cV_tra - cV_rot
            heat_conductivity.append(viscosity[-1] /M * (f_tra * cV_tra + f_rot * cV_rot + f_vib * cV_vib))





class ThermDataDisplayer(CenterWindow):

    variables: list = []

    material: MaterialData.Species = None

    cp: tuple[list[float],list[float]] = None
    H: tuple[list[float],list[float]] = None
    S: tuple[list[float],list[float]] = None
    plot: Axes = None
    toolbar: tk.Label = None
    ref: list[Line2D] = None

    active_plot: tuple[list[float],list[float]] = None

    #atoms: dict[str, int]
    #coefficients: list[float]

    def __init__(self, master, chem_data: ChemData):
        super().__init__(master)
        self.chem_data = chem_data
        self.material = MaterialData.Species(self.chem_data.species,MaterialData.convert_state(self.chem_data.state))
        for coef in self.chem_data.coefficients:
            self.material.add_coefficient(coef)
        self.material.set_temp_max(self.chem_data.high_temperature)
        self.material.set_temp_min(self.chem_data.low_temperature)
        self.material.set_temp_switch(self.chem_data.jump_temperature)

        source = global_vars.libData[self.chem_data.source]
        self.source = source
        row = 0
        label = tk.Label(self, text="Thermodynamic Data", font=("Arial", 20))
        label.grid(row=row, column=0, columnspan=4)
        row -=- 1
        label = tk.Label(self, text="Source:", anchor=tk.W)
        label.grid(row=row, column=0, sticky=tk.EW)
        author = source.author
        if len(source.author) > 20:
            author = source.author[:17] + "..."
        edit = tk.Label(self, text=str(source.creation_date.year) + " " + author, cursor = "pencil")
        edit.bind("<Button-1>", lambda event: select_source(self, self.chem_data.source))
        edit.grid(row=row, column=1, sticky=tk.EW)
        row -=- 1
        self.add_property(row,"state", var = tk.StringVar())
        row -=- 1
        if self.chem_data.comment_therm is None:
            self.chem_data.comment_therm = ""
        self.add_property(row,"comment_therm", var = tk.StringVar())
        row -=- 1
        self.add_property(row,"low_temperature")
        row -=- 1
        self.add_property(row,"high_temperature")
        row -=- 1
        self.add_property(row,"jump_temperature")
        row -=- 1
        spacer = tk.Frame(self, height=20)
        spacer.grid(row=row, column=1, sticky=tk.NS)
        row -= - 1

        for idx in range(len(self.chem_data.coefficients)):
            label = tk.Label(self, text="Coefficient " + str(idx+1) + ":", anchor=tk.W)
            label.grid(row=row, column=0, sticky=tk.EW)
            var = tk.DoubleVar()
            var.set(self.chem_data.coefficients[idx])
            edit = tk.Entry(self, textvariable=var, justify=tk.RIGHT)
            edit.grid(row=row, column=1, sticky=tk.EW)

            def set_value(v, i, e):
                if e.get() != "":
                    self.chem_data.coefficients[i] = v.get()

            var.trace_add("write", lambda a, b, c, v=var, i= idx,e=edit: set_value(v, i, e))
            row -=- 1
            if idx == 6:
                spacer = tk.Frame(self, height=5)
                spacer.grid(row=row, column=1, sticky=tk.NS)
                row -= - 1

        x: list[float] = []
        cp:list[float] = []
        H:list[float] = []
        S:list[float] = []
        self.cp = (x, cp)
        self.H = (x, H)
        self.S = (x, S)

        self.calculate_values()
        plot1: Axes

        plot_frame = tk.Frame(self)

        self.create_plot(plot_frame)

        btn_frame = tk.Frame(self)
        btn_frame.grid_rowconfigure(list(range(3)), weight=1)
        btn_frame.grid_columnconfigure(list(range(3)), weight=1)
        btn_frame.grid(row=row, column=0, columnspan=2, sticky=tk.EW)
        row -=- 1
        vis_btn = tk.Button(btn_frame, text="Heat Capacity", command=lambda: self.plot_array(self.cp))
        vis_btn.grid(row=0, column=0, sticky=tk.EW, padx=5, pady=5)
        diff_btn = tk.Button(btn_frame, text="Enthalpie", command=lambda: self.plot_array(self.H))
        diff_btn.grid(row=0, column=1, sticky=tk.EW, padx=5, pady=5)
        diff_btn = tk.Button(btn_frame, text="Enthropie", command=lambda: self.plot_array(self.S))
        diff_btn.grid(row=0, column=2, sticky=tk.EW, padx=5, pady=5)



        spacer = tk.Frame(self)
        spacer.grid(row=row, column=1, sticky=tk.NS)
        self.grid_rowconfigure(row, weight=1)

        spacer = tk.Frame(self, width=30)
        spacer.grid(row=1, column=2)

        plot_frame.grid(row=1, column=3, rowspan=row, sticky=tk.NSEW)
        row -= - 1

        confirm_btn = tk.Button(self, text="Confirm", command=self.destroy)
        confirm_btn.grid(row=row, column=0, columnspan = 4, sticky='nsew', padx=10, pady=10)
        row -= - 1
        self.bind('<Escape>', lambda e: self.destroy())
        self.center()

    def plot_array(self, array):
        self.active_plot = array
        self.material = MaterialData.Species(self.chem_data.species,MaterialData.convert_state(self.chem_data.state))
        for coef in self.chem_data.coefficients:
            self.material.add_coefficient(coef)
        self.material.set_temp_max(self.chem_data.high_temperature)
        self.material.set_temp_min(self.chem_data.low_temperature)
        self.material.set_temp_switch(self.chem_data.jump_temperature)
        self.calculate_values()
        self.clear_plot()
        self.ref = self.plot.plot([0, 0], [0, 0])
        self.plot.plot(array[0], array[1])
        set_xstep_size(self.plot,min(array[0]),max(array[0]))
        self.plot.figure.canvas.draw()




    def add_property(self, row, text, color = "black", var: tk.Variable = None):
        title = text.split("_")
        for i in range(len(title)):
            title[i] = title[i].capitalize()
        title = " ".join(title)
        title += ": "
        label = tk.Label(self, text=title, anchor=tk.W)
        label.grid(row=row, column=0, sticky=tk.EW)
        dict_version = self.chem_data.__dict__
        if var is None:
            var = tk.DoubleVar()
        var.set(dict_version[text])
        edit = tk.Entry(self, textvariable=var, justify=tk.RIGHT, fg=color)
        edit.grid(row=row, column=1, sticky=tk.EW)
        def set_value(var,text,e):
            dict_version = self.chem_data.__dict__
            if e.get() != "":
                dict_version[text] = var.get()

        var.trace_add("write", lambda a,b,c,v=var,t=text, e=edit: set_value(var,t,e))

    def show_current_value(self, event:MouseEvent) -> None:
        x = event.xdata
        if x is None:
            return
        x_lim = self.plot.get_xlim()
        y_lim = self.plot.get_ylim()
        self.ref[0].set_data([x,x], [y_lim[0], y_lim[1]])
        self.plot.set_xlim(x_lim)
        self.plot.set_ylim(y_lim)
        self.plot.figure.canvas.draw()

        if self.active_plot is None:
            return
        x_data = np.array(self.active_plot[0])
        idx = np.argmax(x_data > x)
        y_data = np.array(self.active_plot[1])
        y = y_data[idx]
        self.toolbar.configure(text="x= {:g} y={:g}".format(x,y))


    def create_plot(self, parent):
        # the figure that will contain the plot
        fig = Figure(figsize=(5, 5),
                     dpi=100)
        # adding the subplot
        self.plot = plot1 = fig.subplots()
        self.ref = self.plot.plot([0, 0], [0, 0])
        # plotting the graph
        plot1.ticklabel_format(axis='y', scilimits=[-3, 3])
        plot1.grid(True)
        # creating the Tkinter canvas
        # containing the Matplotlib figure
        canvas = FigureCanvasTkAgg(fig, master=parent)
        canvas.draw()
        canvas.mpl_connect(
            'motion_notify_event', self.show_current_value)

        # placing the canvas on the Tkinter window
        canvas.get_tk_widget().pack()

        self.toolbar = tk.Label(parent, text="x: y: ", anchor=tk.CENTER)
        self.toolbar.pack(side=tk.TOP, fill=tk.BOTH)

        # Add import btn
        import_btn = tk.Button(parent,text="Compare Experimental Data",  command=lambda: import_data(self,self.plot))
        import_btn.pack(expand=True, fill=tk.Y)



    def clear_plot(self):
        self.plot.clear()
        self.plot.ticklabel_format(axis='y', scilimits=[-3, 3])
        self.plot.grid(True)


    def calculate_values(self):
        x: list[float] = self.cp[0]
        cp:list[float] = self.cp[1]
        H:list[float] = self.H[1]
        S:list[float] = self.S[1]
        x.clear()
        cp.clear()
        H.clear()
        S.clear()
        for T in range(int(self.material.get_temp_min()),int(self.material.get_temp_max()),50):
            x.append(T)
            cp.append(self.material.get_cp(T))
            H.append(self.material.get_h(T))
            S.append(self.material.get_s(T))


def set_xstep_size(plot, lower, upper):
    step_pot = math.log10(abs(upper - lower)) - 0.8
    step_size = round(10 ** step_pot / (10 ** math.floor(step_pot))) * 10 ** math.floor(step_pot)
    plot.set_xticks(np.arange(lower, upper + 1, step_size))

def import_data(parent, plot):
    file_name = filedialog.askopenfilename(parent=parent)
    if file_name=="":
        return
    file = open(file_name)
    data = file.readlines()
    file.close()
    x = list()
    y= list()
    for line in data:
        line = line.strip("\n")
        split_line = line.split(";")
        x.append(float(split_line[0]))
        y.append(float(split_line[1]))
    max_delta_x = max(min(x)*0.2,max(x)*0.1)
    max_delta_y = max(min(y)*0.2, max(y)*0.1)
    plot.set_xlim(min(x)- max_delta_x, max(x)+max_delta_x)
    plot.set_ylim(min(y)-max_delta_y, max(y) + max_delta_y)
    plot.scatter(x, y, marker='x', c='r')
    set_xstep_size(plot,min(x)- max_delta_x, max(x)+max_delta_x)
    plot.figure.canvas.draw()

def select_source(parent, source_id):
    displayer = SourceDataDisplayer.SourceDisplay(parent, source_id)
    displayer.show()