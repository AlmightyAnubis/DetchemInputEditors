import math
import tkinter.messagebox
from tkinter import messagebox
from typing import Callable

from MechanismEditorPackage import global_vars
from MechanismEditorPackage.Interfaces import Checkable, SelfFixing, EditorAdjusted
from GeneralUtil import ThermalDataReader
from GeneralUtil.MaterialData import Species
from GeneralUtil.Nat_Constants import R
from MechanismEditorPackage.adjust_util.logarrhenius import logArrheniusTerm

reaction_counter = 0

def get_reaction_counter():
    global reaction_counter
    reaction_counter += 1
    return reaction_counter

class Reaction(Checkable, SelfFixing, EditorAdjusted):

    educts: dict[str,int]
    products: dict[str,int]
    orders: dict[str,float]
    epsilon: dict[str,float]
    _A_k = 0
    _beta_k = 0
    _E_k = 0
    old_A_k = 0
    old_beta_k = 0
    old_E_k = 0
    is_stick = False
    is_reversible = False
    _reverse_reaction = None
    is_disabled = False
    category = ""
    weight = 1
    is_adjustable = True
    is_required = False
    exponent = -2
    reaction_id: int = None
    temperature_independent_term: float = None


    def no_show(self) -> list[str]:
        elements = list()
        elements.append("old_A_k")
        elements.append("old_beta_k")
        elements.append("old_E_k")
        elements.append("_reverse_reaction")
        elements.append("reaction_id")
        elements.append("exponent")
        elements.append("is_required")
        elements.append("is_adjustable")
        elements.append("temperature_independent_term")
        return elements

    def no_edit(self) -> list[str]:
        elements = list()
        return elements

    def __init__(self, category:str, educts=None, products=None, A_k = 0, beta_k = 0, E_k = 0, is_stick = False, is_reversible = False, is_disabled = False):
        from MechanismEditorPackage import global_vars
        self.reaction_id = get_reaction_counter()
        self.orders = {}
        self.epsilon = {}
        if products is None:
            products = {}
        if educts is None:
            educts = {}
        self.educts = educts
        self.products = products
        self._A_k = A_k
        self._beta_k = beta_k
        self._E_k = E_k
        self.is_stick = is_stick
        self.is_reversible = is_reversible
        self.is_disabled = is_disabled
        self.category = category
        self.is_adjustable = True
        self.weight = 1.0
        if self.is_reversible:
            reverse_reaction = Reaction(category,products,educts,A_k,beta_k,E_k,False,False,is_disabled)
            self._reverse_reaction = reverse_reaction
        if is_stick:
            gas = None
            cfactor = 1
            self.weight = 4.0
            for spec in educts:
                species = global_vars.species[spec]
                if not species.is_adsorpt():
                    if gas is None:
                        gas = species
                    else:
                        print("Error in Stick Reaction:", str(self))
                        raise AssertionError("Multiple Gas Species in Stick Reaction")
                else:
                    cfactor *= (species.gamma) ** self.educts[spec]


            if gas is None:
                print("Error in Stick Reaction:",str(self))
                raise AssertionError("Stick Reaction is missing gas species")
            # g/mol -> kg/mol
            weight = gas.get_weight()/1e3

            self.temperature_independent_term = \
                math.sqrt(R / 2 / math.pi / weight) / cfactor
        self.update_old_values()

    @property
    def name(self):
        return "R" + str(self.reaction_id)

    @property
    def reverse_reaction(self):
        return self._reverse_reaction

    @reverse_reaction.setter
    def reverse_reaction(self, value):
        self.is_reversible = True
        self._reverse_reaction = value
        value.educts = self.products
        value.products = self.educts


    def update_old_values(self, has_parent=False):
        self.old_A_k = self.A_k
        self.old_beta_k = self.beta_k
        self.old_E_k = self.E_k
        if self.is_reversible and not has_parent:
            self._reverse_reaction.update_old_values(True)

    def set_adjustable(self, value):
        self.is_adjustable = value

    def set_weight(self, weight):
        self.weight = weight

    def __str__(self):
        text = ""
        for key, value in self.educts.items():
            text += str(value) + str(key) + " + "
        text= text[:-3]
        text = text.ljust(25)
        if self.is_reversible:
            text = text + " <-> "
        else:
            text = text + " -> "
        for key, value in self.products.items():
            text += str(value) + str(key) + " + "
        text= text[:-3]
        text= text.ljust(55)
        text += " | "
        text = text.ljust(60)
        text= text + "{:10.3E}".format(self._A_k).rjust(10) + "   "
        beta_str = "{:g}".format(self._beta_k)
        text= text + beta_str.rjust(7) + "   "
        text= text + "{:g}".format(self.E_k).rjust(10) + "   "
        if self.is_stick:
            text= text + "stick"
        text = text.ljust(105)
        if self.is_disabled:
            text= text + "disabled"
        text = text.ljust(120)
        return text

    def check(self) -> bool:
        total_spec = 0
        for key, value in self.educts.items():
            total_spec += value
        for key, value in self.products.items():
            total_spec += value
        if total_spec > 5:
            tkinter.messagebox.showinfo(title="Reaction Error", message="Reduce number of educts and products to 5")
            return False
        if self.is_stick and (self._A_k>1 or self._A_k<0):
            tkinter.messagebox.showinfo(title="Reaction Error", message="Stick Factor needs to be between 0 and 1")
            return False
        return True

    def fix(self) -> None:
        self.educts = {k: v for k, v in self.educts.items() if v>0}
        self.products = {k: v for k, v in self.products.items() if v>0}
        self.epsilon = {k: v for k, v in self.epsilon.items() if v!=0}
        self.orders = {k: v for k, v in self.orders.items() if v!=0}
        if self.is_reversible:
            self.reverse_reaction.educts = self.products
            self.reverse_reaction.products = self.educts
            self.reverse_reaction.category = self.category

    @property
    def A_k(self):
        if self.is_stick:
            return self._A_k * self.temperature_independent_term
        return self._A_k

    def get_A_k(self, raw= False):
        if raw: return self._A_k
        if self.is_stick:
            return self._A_k * self.temperature_independent_term
        return self._A_k

    def set_A_k(self, value, raw= False):
        if raw: self._A_k = value
        else: self.A_k = value

    @A_k.setter
    def A_k(self, value):
        if self.is_stick:
            self._A_k=value/self.temperature_independent_term
        else:
            self._A_k = value

    @property
    def beta_k(self):
        if self.is_stick:
            return self._beta_k + 0.5
        return self._beta_k

    def get_beta_k(self, raw= False):
        if raw: return self._beta_k
        if self.is_stick:
            return self._beta_k + 0.5
        return self._beta_k

    def set_beta_k(self, value, raw= False):
        if raw: self._beta_k = value
        else: self.beta_k = value

    @beta_k.setter
    def beta_k(self, value):
        if self.is_stick:
            self._beta_k = value - 0.5
        else:
            self._beta_k = value

    @property
    def E_k(self):
        if self.is_stick:
            return self._E_k
        return self._E_k

    def get_E_k(self, raw= False):
        if raw: return self._E_k
        if self.is_stick:
            return self._E_k
        return self._E_k

    def set_E_k(self, value, raw= False):
        if raw: self._E_k = value
        else: self.E_k = value

    @E_k.setter
    def E_k(self, value):
        if self.is_stick:
            self._E_k = value
        else:
            self._E_k = value

    def get_logkf(self):
        try:
            return logArrheniusTerm(math.log(self.A_k), self.beta_k, -self.E_k / R)
        except ValueError as e:
            messagebox.showerror("Math Error","Reaction with Problem:\n" + str(self))
            raise ValueError(e)

    def Kp2Kc(self, T):
        K = 1.0
        for s, stoic in self.educts.items():
            spec = ThermalDataReader.find_species(s, global_vars.thermalDataMap)
            K /= (spec.c0(T)) ** stoic
        for s, stoic in self.products.items():
            spec = ThermalDataReader.find_species(s, global_vars.thermalDataMap)
            K *= (spec.c0(T)) ** stoic
        return K

    def sum_F(self,generic_function:Callable[[Species],float]):
        value=0
        for s,stoic in list(self.educts.items()):
            spec = ThermalDataReader.find_species(s, global_vars.thermalDataMap)
            value -= stoic*generic_function(spec)
        for s,stoic in list(self.products.items()):
            spec = ThermalDataReader.find_species(s, global_vars.thermalDataMap)
            value += stoic*generic_function(spec)
        return value

    def deltaG_const(self, T):
        func = lambda s: s.G_const(T)
        return self.sum_F(func)

    def deltaG_RT_adjustable(self):
        return self.sum_F(lambda s : s.G_adjustable())

    def kf(self,T):
        return self.A_k * T ** self.beta_k * math.exp(-self.E_k/R/T)

    def kf_old(self,T):
        return self.old_A_k * T ** self.old_beta_k * math.exp(-self.old_E_k/R/T)

    def get_surface_stoic(self):
        L=[(s,stoic) for s,stoic in list(self.products.items())]
        L+= [(s,-stoic) for s,stoic in list(self.educts.items())]
        d=dict()
        for s,stoic in L:
            spec = ThermalDataReader.find_species(s, global_vars.thermalDataMap)
            if spec.is_adsorpt():
                if s in d:
                    d[s]+=stoic
                else:
                    d[s]=stoic
        return d



