from cegispro2.synthesis.synthesis_utils import *
from cegispro2.solving.Solver import *
from cegispro2.expectations.Guard import Guard
from pysmt.shortcuts import Symbol, INT

class OneShotSynthesizer:


    def __init__(self, char_fun, exp_temp, property, validate):
        """

        :param variables: The list of program variables.
        :param char_fun: The characteristic functional representing the program.
        :param exp_temp: The expectation template for which we want to synthesize a safe inductive instance.
        :param property:  A specification is a list of pairs (ineqs, linexp). Semantics: for all program states s: s \models ineqs => wp[C](post)[s] <= linexp[s]
        """

        self.variables = char_fun.variables

        assert(char_fun.variables == exp_temp.variables)

        self.char_fun = char_fun
        self.exp_temp = exp_temp
        self.applied_exp_temp = self.char_fun.apply_expectation(exp_temp)
        self.property = property
        self.validate = validate
        self.index_f_var = Symbol("index_f", INT)
        self.index_phi_f_var = Symbol("index_phi_f", INT)
        self.index_exp1_var = Symbol("index_exp1", INT)
        self.index_exp2_var = Symbol("index_exp2", INT)

    def synthesize(self):
        """

        :return: None if no safe inductive instance of the template can be computed by means of motzkin's transposition theorem,
         otherwise a dict from template parameters to valuations.
        """
        constraints = []

        # -------------- Encode Inductivity
        for (guard1, linexp) in self.applied_exp_temp.guard_linexp_pairs:
            for (guard2, linexp2) in self.exp_temp.guard_linexp_pairs:
                conjoined = Guard.AND(guard1, guard2)

                if conjoined.is_sat():
                    # We need a constraint for the states in pysmt_guards
                    # for these states, we want linexp <= linexp2 to hold.
                    conjoined = conjoined.replace_strict_by_nonstrict_inequalities_if_possible()
                    to_be_implied = LinearInequality.LEQ(linexp, linexp2)
                    constraints.append(get_motzkin_constraints(self.variables, conjoined, to_be_implied))


        # -------------- Encode Safety
        constraints = constraints + get_safety_motzkin_constraints(self.exp_temp, self.property, self.variables, True)

        # -------------- Encode Non-negativity
        constraints = constraints + get_nonnegativity_motzkin_constraints(self.exp_temp, self.variables, strict_to_nonstrict=True)

        # Construct dict from template variable to valuation
        model = get_model(constraints)
        if model == None:
            print("There is no inductive instance by one-shot solving using Motzkin's transposition theorem over real-valued program variables.")
            return None

        valuations = self.exp_temp.get_parameter_valuation_from_sovler_model(model)
        print("\n\n-------- Safe inductive instance of the template ------------")

        if self.validate:
            safe_inductive_invariant = self.exp_temp.fast_instantiate(valuations)
            raise Exception("adapt validate (gets option object now)")
            validate_inductive_invariant(self.char_fun, safe_inductive_invariant, self.property)

        return valuations



