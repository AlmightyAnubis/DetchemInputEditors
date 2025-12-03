from periodictable import formulas, core


class ChemData():
    ID: int
    species: str
    source: int
    data_type: str
    geometry: int
    molar_mass: float
    mass_approx= False
    lennard_jones_potential: float
    lennard_jones_collision: float
    dipole_moment: float
    polarizability: float
    rotational_relaxation_collision_number: float
    comment_chem: str
    atoms: dict[str, int]
    state: str
    comment_therm: str
    low_temperature: float
    high_temperature: float
    jump_temperature: float
    coefficients: list[float]

    def __init__(self, ID:int):
        self.ID = ID
        self.atoms = {}
        self.coefficients = []

    def approx_molar_mass(self):
        if self.molar_mass == -1:
            try:
                if len(self.atoms) == 0:
                    self.mass_approx = True
                    formula_representation = formulas.parse_formula(self.species)
                    self.molar_mass = formula_representation.mass
                    self.atoms = formula_representation.atoms

                else:
                    table = core.default_table(None)
                    self.molar_mass = 0
                    for atom in self.atoms:
                        iso = table.isotope(atom)
                        self.molar_mass += iso.mass * self.atoms[atom]
            except Exception as e:
                print(e)
                self.molar_mass = -1
                print("Could not convert name <",self.species,"> to chemical formular to calculate molar mass. Assuming molar mass is 10 in calculations.")



    def __str__(self):
        content = str(self.ID) + ": {name:" + str(self.species) + ","
        if hasattr(self, "data_type"):
            content += "type:" + str(self.data_type)
        content += "}"
        return content






