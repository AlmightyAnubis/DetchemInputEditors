import copy
from tkinter import messagebox

from MechanismEditorPackage import Reaction_Class
from MechanismEditorPackage import global_vars
from MechanismEditorPackage.adjust_util.AdjustData import AdjustDataHolder, TemperatureRange
from GeneralUtil.MaterialData import Species
from GeneralUtil.TextModifiers import bcolors
from MechanismEditorPackage.adjust_util.linear import find_dependents
from MechanismEditorPackage.adjust_util.logarrhenius import *


class AdjustClass(object):

    def __init__(self):
        self.outfilename = "chem.adjust"
        self.old2new = dict()
        self.cov = dict()


    @property
    def adjust_data(self):
        return self._adjust_data

    @adjust_data.setter
    def adjust_data(self, adjust_data: AdjustDataHolder):
        self._adjust_data = adjust_data
        temps = adjust_data.T_ref_value
        if len(temps) < 1:
            print(bcolors.WARNING + "WARNING: No reference temperatures found. Using 300 - 1000 K" + bcolors.ENDC)
            temps = TemperatureRange(300,1001,50)
        self.T_ref = []
        self.T_min = 20000
        self.T_max = 0
        for temp in temps:
            self.T_ref.extend(list(range(temp.T_min, temp.T_max + 1, temp.T_step)))
            self.T_min = min(self.T_min, temp.T_min)
            self.T_max = max(self.T_max, temp.T_max)

    # def read_mechanism(self, infilename, flagweight=1):
    #     # read input file (CHEMINP format)
    #     try:
    #         self.infile = inp.inpfile(infilename)
    #         self.slist = adjust_util.species.SpeciesList(self.infile["SPECIES"])
    #         self.mech = mechanism.SurfaceMechanism(self.infile["MECHANISM"]["SURFACE"], self.slist)
    #     except AssertionError:
    #         print("ERROR reading file", infilename)
    #         print("file must be in CHEMINP format")
    #         raise RuntimeError
    #     # default weights
    #     self.weight = dict()
    #     self.adjustable = dict()
    #     for reac in self.mech.reactions():
    #         w = 1
    #         self.adjustable[reac] = True
    #         if reac.cflag == "*":
    #             if flagweight > 0:
    #                 w = flagweight
    #             else:
    #                 self.adjustable[reac] = False
    #         if isinstance(reac, mechanism.StickSReaction): w *= 4
    #         self.weight[reac] = w



    def read_Tref(self, adjust_inp):
        Tref_inp = adjust_inp["TREF"]
        if Tref_inp:
            self.T_ref = [float(i) for i in Tref_inp.word_iterator()]
        else:
            self.T_ref = []
        if len(self.T_ref) < 2:
            print("WARNING: No reference temperatures found. Using 300 - 1000 K")
            self.T_ref = [float(i) for i in range(300, 1001, 50)]
        self.T_min = min(self.T_ref)
        self.T_max = max(self.T_ref)
        if len(self.T_ref) == 2:
            self.T_ref = [self.T_min + (self.T_max - self.T_min) * i / 20.
                          for i in range(21)]

    def read_cov(self, adjust_inp):
        self.cov = dict()
        cov_inp = adjust_inp["COV"]
        if cov_inp:
            spec = ""
            dep = ""
            for i in cov_inp.word_iterator():
                if i[0] == "$":
                    dep = i[1:]
                else:
                    spec = i
                    dep = i
                if spec != "":
                    try:
                        self.cov[dep].add(spec)
                    except:
                        self.cov[dep] = {spec}
                else:
                    print("ERROR in section <COV> of adjust.inp")
                    print("section must start with a species name, not with a dependency ($)")
                    raise RuntimeError

    def adjust_rates(self):
        # for each pair of reversible reactions set up an equation like
        # log(kf)+xf -log(kr)-xr = log(Kc/Kp) - deltaG(T)/RT
        # deltaG(T)/RT = sum_gas(nu_i * g_i(T)/RT) + sum_surf(nu_i * y_i)
        # xf,xr,y_i are terms of type logArrheniusTerm
        # all given functions are fitted by a logArrheniusTerm

        LES = algebra.LinearEquationSystem()
        reversible_eqs: list[Reaction_Class.Reaction] = list()
        reverses = list()
        non_reversible_eqs = list()
        for category, reactions in global_vars.reactions.items():
            for reaction in reactions:
                if reaction.reverse_reaction is not None:
                    if reaction not in reverses:
                        reversible_eqs.append(reaction)
                        reverses.append(reaction.reverse_reaction)
                else:
                    non_reversible_eqs.append(reaction)
        for freac in reversible_eqs:
            rreac = freac.reverse_reaction
            lterm = algebra.LinearCombination()
            lterm += freac.get_logkf() - rreac.get_logkf()
            if freac.is_adjustable:
                lterm += algebra.EquationVariable(freac)
                lterm -= algebra.EquationVariable(rreac)
            rterm = algebra.LinearCombination()
            rconst = dict()
            for T in self.T_ref:
                rconst[T] = (math.log(freac.Kp2Kc(T))
                             - freac.deltaG_const(T) / R / T)

            rterm += logArrheniusFit(rconst)
            rterm -= freac.deltaG_RT_adjustable()
            LES.add(lterm, rterm)

        ##        print ">>1"
        ##        print LES


        # eliminate thermodynamic unknowns (y_i)
        LES2 = algebra.LinearEquationSystem()
        print("Start elimination")
        while True:
            f = (lambda spec: False if not isinstance(spec, Species) else False if not spec.is_adsorpt else True)
            v = LES.variables(f)
            if len(v) == 0: break
            LES2.add(LES.eliminate(v[0], return_pivot=True))
        print("Finish elimination")
        ##        print ">>2"
        ##        print LES

        # minimize Phi=sum(w_i * ||x_i||^2) with x_i fulfilling equations in LES
        # x_i = a_i + b_i * ln(T) + c_i / T
        # ||x_i||^2 = Integral_Tmin^Tmax x_i(T)^2 dT

        MES = algebra.LinearEquationSystem()
        variables = LES.variables()  # these are the adjustable reactions
        I = lambda func: func(self.T_max) - func(self.T_min)
        Iaa = I(lambda T: T)  # Integral 1 dT
        Ibb = I(lambda T: T * math.log(T) ** 2 - 2 * T * math.log(T) + 2 * T)  # Integral ln^2(T) dT
        Icc = I(lambda T: -1. / T)  # Integral 1/T^2 dT
        Iab = 2 * I(lambda T: T * math.log(T) - T)  # Integral ln(T) dT
        Iac = 2 * I(lambda T: math.log(T))  # Integral 1/T dT
        Ibc = 2 * I(lambda T: math.log(T) ** 2 / 2)  # Integral ln(T)/T dT

        Lagrange = lambda v, name: sum([LES[i].coefficient(v) *
                                        algebra.EquationVariable(name + str(i))
                                        for i in range(len(LES))])
        Adict = dict()
        Bdict = dict()
        Cdict = dict()

        for v in variables:
            v: Reaction_Class.Reaction
            a = algebra.EquationVariable("a" + str(v))
            b = algebra.EquationVariable("b" + str(v))
            c = algebra.EquationVariable("c" + str(v))
            Adict[v] = a
            Bdict[v] = b
            Cdict[v] = c
            # d Phi/d a_i = 0
            MES.add(v.weight * (2 * a * Iaa + b * Iab + c * Iac) + Lagrange(v, "A"))
            # d Phi/d b_i = 0
            MES.add(v.weight * (2 * b * Ibb + a * Iab + c * Ibc) + Lagrange(v, "B"))
            # d Phi/d c_i = 0
            MES.add(v.weight * (2 * c * Icc + a * Iac + b * Ibc) + Lagrange(v, "C"))
        # split original equations by equating coefficients
        for eq in LES:
            eqa = eq.copy()
            eqa.c = eqa.c.a  # constant must be of type logArrheniusTerm
            eqa.replace(Adict, True)
            MES.add(eqa)
            eqb = eq.copy()
            eqb.c = eqb.c.b  # constant must be of type logArrheniusTerm
            eqb.replace(Bdict, True)
            MES.add(eqb)
            eqc = eq.copy()
            eqc.c = eqc.c.c  # constant must be of type logArrheniusTerm
            eqc.replace(Cdict, True)
            MES.add(eqc)

        ##        print ">>3"
        ##        print MES

        x = MES.solve()

        ##        print ">>4"
        ##        for i in x: print i,"\t",x[i]
        ##        print ">>5"
        ##        print LES2

        # new mechanism , linear equations for thermdata
        for reac in variables:
            reac: Reaction_Class.Reaction
            nreac = reac
            X = logArrheniusTerm(x["a" + str(reac)], x["b" + str(reac)], x["c" + str(reac)])
            LES2.replace({reac: X}, True)
            logkf = X + reac.get_logkf()
            A, beta, Ea = log2Arrhenius(logkf)
            nreac.E_k = Ea
            nreac.beta_k = beta
            if nreac.is_stick:
                term = nreac.temperature_independent_term
                if A/term>1 or A<0:
                    reac.weight *= 2
                    print("Incrementing weight for reaction <", end=' ')
                    print(str(reac), "> to", reac.weight)
                else:
                    nreac.A_k = A
            else:
                nreac.A_k = A


        # solve equations for thermdata

        ##        print ">>6"
        ##        print LES2

        y = LES2.solve()

        ##        print ">>7"
        ##        for i in y: print i,"\t",y[i]

        # use species with lowest cp as reference
        execution_counter = 0
        while True:
            if execution_counter > 1000:
                messagebox.showerror("Error", "Maximum number of iterations reached")
                return -1
            execution_counter -=- 1
            done = True
            cp0 = 0
            for s, term in list(y.items()):
                try:
                    cp = -term.coefficient().b
                except AttributeError:
                    continue
                if cp < cp0:
                    done = False
                    s0, term0, cp0 = s, term, cp
            if done: break
            s1 = term0.variables()[0]
            c1 = term0.coefficient(s1)
            term0 = term0 - c1 * algebra.EquationVariable(s1)
            term1 = (algebra.EquationVariable(s0) - term0)
            if c1 != 1:
                term1 /= float(c1)
            for s in y:
                y[s].replace({s1: term1}, True)

        ##            print ">>8"
        ##            for i in y: print i,"\t",y[i]

        # convert to tuples (cp/R,H0/R,S0/R) and change thermdata
        errors = []
        for i in y:
            try:
                i.set_adjusted(*log2therm(y[i].coefficient()))
            except AttributeError:
                errors.append(i)
        for i in errors:
            del y[i]

        for i in y:
            print("%8s   cp=%6.2f   H0=%8.0f   S0=%6.2f" % (str(i), i.cp(298.), i.H(298.), i.S(298.)))

        return 0

    def adjust_cov(self):
        # coverage dependencies ....
        for cov, cov_dependent_species in list(self.cov.items()):
            print("adjusting $" + cov)
            # set up linear equations for coverage dependent thermdata (eps_i)
            # epsilon_r-epsilon_f = sum (nu_i * eps_i)
            LES1 = algebra.LinearEquationSystem()
            LES2 = algebra.LinearEquationSystem()
            for freac, rreac in self.mech.reversibles():
                eq = self.mech.get_cov_equation(freac, rreac, cov, cov_dependent_species)
                if eq != None:
                    if not self.adjustable[freac] and not self.adjustable[rreac]:
                        LES1.add(eq)
                    else:
                        LES2.add(eq)

            # solve exact equations
            eps1 = LES1.solve()
            LES2.replace(eps1, True)

            # solve linear regression
            eps = LES2.linreg()

            # merge exact and approximated solutions
            for s, val in list(eps1.items()):
                if isinstance(val, algebra.LinearCombination):
                    eps[s] = val.replace(eps, False).coefficient()
                else:
                    eps[s] = val
            for s, val in list(eps.items()):
                s.all_data.set_adjusted_cov(cov, val)
                print("$" + cov + " of " + str(s) + " =", val)

            # new coverage dependencies in all reactions:
            for freac, rreac in self.mech.reversibles():
                # get old values of epsilon
                epsilon_f = freac.get_epsilon(cov)
                try:
                    epsilon_r = rreac.get_epsilon(cov)
                except:
                    epsilon_r = 0
                # calculate new delta_epsilon
                eq = freac.get_covdependency_equation(cov_dependent_species)
                if eq == 0:
                    if epsilon_r or epsilon_f:
                        print("WARNING: ")
                        print("Coverage dependency for species " + cov + " defined in equation")
                        print(freac.text(), " (or reverse),")
                        print("but no participing species was defined as coverage dependent")
                        print("Coverage dependency will be removed from adjusted mechanism")
                        print()
                    continue
                delta_epsilon = eq.replace(eps).coefficient()
                if not delta_epsilon: continue
                # add difference to the "nicer" side of equation
                if epsilon_f:
                    if not epsilon_r:
                        # forward reaction coverage dependent
                        epsilon_f = epsilon_r - delta_epsilon
                    else:
                        # find larger term
                        if abs(epsilon_f) >= abs(epsilon_r):
                            epsilon_f = epsilon_r - delta_epsilon
                        else:
                            epsilon_r = epsilon_f + delta_epsilon
                else:
                    if epsilon_r:
                        # reverse reaction coverage dependent
                        epsilon_r = epsilon_f + delta_epsilon
                    else:
                        # make epsilon positive
                        if delta_epsilon > 0:
                            epsilon_r = delta_epsilon
                        else:
                            epsilon_f = -delta_epsilon
                # add coverage dependency to new equations
                # TODO Remove comment
                # if epsilon_f:
                #     self.old2new[freac].cov.append(mechanism.CoverageDependency
                #                                    (spec=self.slist[cov], epsilon=epsilon_f))
                # if epsilon_r and rreac:
                #     self.old2new[rreac].cov.append(mechanism.CoverageDependency
                #                                    (spec=self.slist[cov], epsilon=epsilon_r))

    def adjust(self):
        self.old2new = copy.deepcopy(global_vars.reactions)
        for category in global_vars.reactions:
            for reaction in global_vars.reactions[category]:
                reaction.update_old_values()
        OK = False
        for count in range(5):
            print("Try: ",count)
            result = self.adjust_rates()
            if result >= 0:
                OK = True
                break
        self.adjust_cov()
        return OK

    def __str__(self):
        string = ""
        string += "T_ref: " + str(self.T_ref) + "\n"
        string += "T_max:" + str(self.T_max) + "\n"
        string += "Species: \n"
        for species in self.slist:
            string += str(species) + "\n"
        #string += "Reactions: \n"
        #for reac in self.mech.mlist:
        #    string += str(reac) + "\n"
        return string


def update_adjustables(gui):
    import ScrollableGui
    gui: ScrollableGui.ListGui
    wlist=[] # wdigets
    vlist=[] # vectors
    ulist=[] # fixed vectors

    reversible_eqs: list[Reaction_Class.Reaction] = list()
    reverses = dict()
    non_reversible_eqs = list()
    for category, reactions in global_vars.reactions.items():
        for reaction in reactions:
            if reaction.reverse_reaction is not None:
                if reaction not in reverses:
                    reversible_eqs.append(reaction)
                    reverses[reaction.reverse_reaction] = reaction
            else:
                non_reversible_eqs.append(reaction)
    for freac in reversible_eqs:
        rreac = freac.reverse_reaction

        if freac.is_adjustable:
            if not rreac.is_adjustable: # only freac is adjustable
                wlist.append(freac)
                vlist.append(freac.get_surface_stoic())
            else: # both reactions are adjustable, no need to check
                freac.is_required = False
                rreac.is_required = False
        else :
            if rreac.is_adjustable: # only rreac is adjustable
                wlist.append(rreac)
                vlist.append(rreac.get_surface_stoic())
            else : # none of the two is adjustable
                ulist.append(freac.get_surface_stoic())
    # find linear combinations
    ilist=find_dependents(ulist,vlist)
    # change status of widgets
    for dependent,w in zip(ilist,wlist):
        if dependent:
            w.is_required = True
            if w in reverses:
                gui.update_reaction_frame(reverses[w])
            else:
                gui.update_reaction_frame(w)
        else:
            w.is_required = False
