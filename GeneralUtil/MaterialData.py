import math
from enum import Enum

import periodictable

from GeneralUtil import Errors
from GeneralUtil.Nat_Constants import R
from GeneralUtil.algebra import EquationVariable
from MechanismEditorPackage.adjust_util.AdjustData import AdjustDataHolder


class State(Enum):
   Gas = 1
   Liquid = 2
   Solid = 3
   Crystal = 4
   Unknown = 10

def convert_state(letter:str):
    if letter == "G":
        return State.Gas
    if letter == "L":
        return  State.Liquid
    if letter == "S":
        return State.Solid
    if letter == "C":
        return State.Crystal
    return State.Unknown

def reconvert_state(state: State):
        if state == State.Gas:
            return "G"
        if state == State.Liquid:
            return "L"
        if state == State.Solid:
            return "S"
        if state == State.Crystal:
            return "C"
        if state == State.Unknown:
            return "?"
        return "?"
    #raise NameError("Value \"" + letter + "\" not convertable")


p_norm=101325.0

class Species:
    _coefficient: list[float]
    _atoms: dict[periodictable.core.Isotope,float]
    _name:str
    _comment:str
    _T_min:float
    _T_max:float
    _T_switch:float
    _error = NameError("Value not defined")
    _surface:str = None
    _gamma:float = None
    _c_0:float = p_norm/R

    @property
    def name(self):
        return self._name

    def is_adsorpt(self):
        return self._surface is not None

    @property
    def surface(self):
        return self._surface

    def check_adsorpt(self, surfaces:dict[str, tuple[str, int]], data:AdjustDataHolder):
        found = False
        for surface in surfaces.keys():
            if surface == self._name:
                s = surfaces[surface]
                self._surface = s[0]
                self._gamma = data.surface_side_value[self._surface].surface_side_density/s[1]
                found = True
                break
        if not found:
            for surface in surfaces.keys():
                if surface in self._name:
                    s = surfaces[surface]
                    self._surface = s[0]
                    self._gamma = data.surface_side_value[self._surface].surface_side_density/s[1]
                    break

    @property
    def gamma(self):
        # mol/cm^2 -> mol/m^2
        return self._gamma*1e4

    def c0(self, T=None):
        if self._surface is None:
            return self._c_0/T
        else:
            return self._gamma


    def __hash__(self):
        return hash(self._name)

    def __gt__(self, other):
        return self._name > other.name

    def __ge__(self, other):
        return self._name >= other.name

    def __le__(self, other):
        return self._name <= other.name

    def __eq__(self, other):
        if type(other) is type(self):
            return self._name == other.name
        return False

    def __ne__(self, other):
        return not self == other


    def __init__(self, name: str, state:State):
        self._name = name
        self.state = state
        self._coefficient = []
        self._atoms = dict()

    @property
    def comment(self):
        return self._comment

    @comment.setter
    def comment(self, comment):
        self._comment = comment

    def __str__(self):
        return self._name

    def add_atom(self, isotop:periodictable.core.Isotope,number:int):
        self._atoms[isotop] = number

    def get_atoms(self):
        return self._atoms

    def get_weight(self):
        total_weight = 0
        isotop: periodictable.core.Isotope
        for isotop in self._atoms.keys():
            total_weight += isotop.mass * self._atoms[isotop]
        return total_weight

    def get_temp_coefficients(self, T: float):
        if T>self._T_max:
            raise Errors.OutOfBoundError("temperature", T, self._T_min, self._T_max)
        if T<self._T_min:
            raise Errors.OutOfBoundError("temperature", T, self._T_min, self._T_max)
        a = self._coefficient[7:14]
        if T > self.get_temp_switch():
            a = self._coefficient[:7]
        return a

    def get_cp(self, T: float):
        a = self.get_temp_coefficients(T)
        c_p = (a[0] + a[1] * T + a[2] * T ** 2 + a[3] * T ** 3 + a[4] * T ** 4) * R
        return c_p


    def get_h(self, T: float):
        a = self.get_temp_coefficients(T)
        h = (a[5] + a[0] * T + a[1] / 2 * T ** 2 + a[2] / 3 * T ** 3 + a[3] / 4 * T ** 4 + a[4] / 5 * T ** 5) * R
        return h

    def get_s(self, T: float):
        a = self.get_temp_coefficients(T)
        s = (a[6] + a[0] * math.log(T) + a[1] * T + a[2] / 2 * T ** 2 + a[3] / 3 * T ** 3 + a[4] / 4 * T ** 4) * R
        return s

    def get_g(self,T: float):
        return self.get_h(T)-T*self.get_s(T)

    def add_coefficient(self, value):
        self._coefficient.append(value)

    def get_coefficients(self):
        return self._coefficient

    def set_temp_min(self, T_min:float):
        self._T_min = T_min

    def set_temp_max(self, T_max:float):
        self._T_max = T_max

    def set_temp_switch(self, T_switch:float):
        self._T_switch = T_switch

    def get_temp_min(self):
        if self._T_min is None:
            raise self._error
        return self._T_min

    def get_temp_max(self):
        if self._T_max is None:
            raise self._error
        return self._T_max

    def get_temp_switch(self):
        if self._T_switch is None:
            raise self._error
        return self._T_switch


    def G_const(self,T):
        if self.is_adsorpt():
            return 0
        return self.get_g(T)

    def G_adjustable(self):
        if self.is_adsorpt():
            return EquationVariable(self)
        return 0


