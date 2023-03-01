from pysmt.shortcuts import Symbol, INT, TRUE, REAL, GE, And, Or, GT, LE, Real, Implies
from cegispro2.expectations.Expectation import Expectation
from cegispro2.inequalities.LinearInequality import LinearInequality
from cegispro2.solving.Solver import *

class TemplateRefiner():
    """
    Abstract class representing a template refiner. There are essentially two types of template refiners:
    Fixed-partition template refiners generate templates where template variables do not occur in the guards.
    Variable-partition template refiners do not impose this restriction.
    """
    def __init__(self, variables, char_fun, property, options, statistics):

        self.variables = variables
        self.char_fun = char_fun
        self.property = property
        self.distance_constant = options.distance
        #self.distance_constant = distance_constant
        #self.initial_template = initial_template

        self.options = options
        self.statistics = statistics
        self.index_f_var = Symbol("index_f", INT)
        self.index_phi_f_var = Symbol("index_phi_f", INT)
        self.diff_var = Symbol("diff", REAL)
        self.instantiate_parameters = Expectation.instantiate
        self.guard_template_variables = []

        if options.invarianttype == "super":

            if options.verifier == 'optimization':
                self.inductivity_check = Expectation.check_leq_optimization
            elif options.verifier == 'distance':

                self.inductivity_check = Expectation.check_leq
            else:
                raise Exception("Unkown verifier type.")

            self.check_safety = Expectation.check_safety_superinvariant
            self.constraint_inequality = LinearInequality.LEQ

        elif options.invarianttype == "sub":

            if options.verifier == 'optimization':
                self.inductivity_check = Expectation.check_geq_optimization
            elif options.verifier == 'distance':

                self.inductivity_check = Expectation.check_geq
            else:
                raise Exception("Unkown verifier type.")

            self.check_safety = Expectation.check_safety_subinvariant
            self.constraint_inequality = LinearInequality.GEQ


            #--- for conditional difference boundedness
            if options.cdb:
                self.loop_guard_formula = Or([guard.pysmt_expression for (guard, _) in char_fun.execute_guard_prob_sub_pairs])
                self.pysmt_cdb_constant = Symbol('cdb_constant', REAL)
            #---


        else:
            raise Exception("Unkown invariant type")




    def get_initial_template(self):
        return self.options.initial_template

    def get_initial_constraint_for_template(self, template):
        pass

    def get_next_counterexample_state(self, f, phi_f, exp_temp, phi_exp_temp, last_cti, guard_of_last_cti, distance):
        """

        :param f: The candidate invarinat f.
        :param phi_f: Phi(f)
        :param last_cti: The last obtained counterexample.
        :param guard_index_of_last_cti: The index of the guard in exp_temp last_cti belongs to.
        :param distance: The current distance.
        :return: A tupel (new_distance, (s, *additional_info)) with s a state such that Phi(f)[s] > f[s] or f[s] < 0 or f[s] > property[s], or None if there is no such s.
        """
        pass

    def get_constraint_from_counterexample_state(self, cti, exp_temp, phi_exp_temp,  guard_linexp_phi_exp_temp, guard_linexp_exp_temp):
        """

        :param cti: The counterexample whose validity is to be asserted.
        :param exp_temp: The current template.
        :param phi_exp_temp: Phi(exp_temp)
        :param guard_linexp_phi_exp_temp: For inductivity and fixed refiner: The (guard,linexp) pair of Phi(exp_temp) such that cti belongs to guard.
        :param guard_linexp_exp_temp: The (guard,linexp) pair such that cti belongs to guard.
        :return: The constraints ensuring that the next candidate will be valid at cti.
        """
        pass


    def get_constraints_from_existing_ctis(self, ctis, phi_exp_temp, exp_temp):
        """

        :param ctis: A list of counterexamples.
        :param phi_exp_temp:
        :param exp_temp:
        :return: The constraints ensuring that the next candidate will be valid at all counterexamples in ctis.
        """
        pass

    def get_refined_template(self, old_template, ctis, last_cti, f, phi_f):
        """

        :param old_template:
        :param ctis:
        :param last_cti:
        :param f:
        :param phi_f:
        :return: A refined old_template.
        """
        pass

    def get_counterexample_to_conditional_difference_boundedness(self, phi_f_delta, distance, constant):
        """

        :param phi_f_delta:
        :return: None if phi_f_delta <= constnat else model with phi_f_delta[model] > constant
        """

        var_nat = [GE(var, Int(0)) for var in self.variables]
        cex_formula = Or([And([guard.pysmt_expression, GT(linexp.pysmt_expression, constant)])
                          for (guard, linexp) in phi_f_delta.guard_linexp_pairs])

        # check exists s: [loop guard]*wp[body](|I - I(s)|)(s) > c
        model = get_model(var_nat + [cex_formula] + [self.loop_guard_formula])

        if model == None:
            return None
        else:
            logger.debug("Counterexample to c.d.b. (current c.d.b. constant = %s)" % str(constant))
            return (distance, (model, None, None))
                           #state none   none  = state_and_info

    def get_cdb_constraints(self, cex, phi_exp_temp_delta):
        """

        :param cex:
        :param phi_exp_temp_delta:
        :return: Constraints ensuring that for the next instance I of exp_temp it holds that I is cbd at cex.
        """
        res = []
        state_formula = And([Equals(var, cex[var]) for var in self.variables])
        subs = {var : cex[var] for var in self.variables}
        for (guard, linexp) in phi_exp_temp_delta.guard_linexp_pairs:
            if is_sat([guard.pysmt_expression, state_formula]):
                res.append(Implies(guard.pysmt_expression.substitute(subs), LE(linexp.pysmt_expression.substitute(subs),
                          self.pysmt_cdb_constant)))

        assert(len(res) != 0)
        return res


    def get_cdb_constraints_from_existing_ctis(self, cexs, phi_exp_temp_delta):
        """

        :param cexs:
        :param phi_exp_temp_delta:
        :return: Constraints ensuring that the next instance I of exp_temp is cbd for all cex in cexs.
        """

        res = [GE(self.pysmt_cdb_constant, Real(0))]
        for cex in cexs:
            res += self.get_cdb_constraints(cex, phi_exp_temp_delta)
        return res

