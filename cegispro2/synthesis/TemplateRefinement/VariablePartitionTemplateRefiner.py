from cegispro2.synthesis.TemplateRefinement.TemplateRefiner import TemplateRefiner
from pysmt.shortcuts import TRUE, And, GE, LT, Int, Implies, Real, Symbol, INT, ToReal
from cegispro2.synthesis.synthesis_utils import *
from cegispro2.expectations.Expectation import Expectation
import itertools

logger = logging.getLogger("cegispro2")

class VariablePartitionTemplateRefiner(TemplateRefiner):
    """
    Fixed-partition.
    Refinement strategy that obtains a new template by splitting the last instance of the current template into inductive and non-inductive parts.
    """
    def __init__(self, variables, char_fun, property, options, statistics):
        super(VariablePartitionTemplateRefiner, self).__init__(variables,char_fun,property,options, statistics)

        self.instantiate_parameters = Expectation.instantiate
        self.synthesize_parameter_valuation = get_model
        if options.optimizing_synthesizer:
            raise Exception("Optimizing synthesizer is not supported for the variable template refiner.")

    def get_next_counterexample_state(self, f, phi_f, exp_temp, phi_exp_temp, last_cti, guard_of_last_cti, distance):
        """

        :param f:
        :param phi_f:
        :param last_cti:
        :param guard_index_of_last_cti:
        :param distance:
        :return: A tupel (new_distance, (s, *additional_info)) with s a state such that Phi(f)[s] > f[s] or f[s] < 0 or f[s] > property[s], or None if there is no such s.
        """
        # we have to check inductivity, safety, and non-negativity
        while True:
            double_distance_constraint = None
            if distance > 1:
                double_distance_constraint = get_double_distance_constraint(self.variables, last_cti, distance)

            last_cti_constraint = None
            # if guard_of_last_cti != None:
            #    last_cti_constraint = guard_of_last_cti.pysmt_expression

            self.statistics.inductivity_check_time.start_timer()

            # check for inductivity
            was_inductivity = False
            state_and_info = self.inductivity_check(phi_f, f, double_distance_constraint)
            if state_and_info == True:
                # if no cti, check for safety
                state_and_info = self.check_safety(f, self.property, double_distance_constraint)
                if state_and_info == True:
                    # check non-negativity
                    state_and_info = f.check_non_negativity(double_distance_constraint)

                    if not state_and_info == True:
                        logger.debug("cex type: non-negativity")
                    pass
                else:
                    logger.debug("cex type: safety")
            else:
                was_inductivity = True
                logger.debug("cex type: cti")

            self.statistics.inductivity_check_time.stop_timer()

            if state_and_info == True:
                # If there is no cti ...
                if double_distance_constraint == None:
                    # ... and there was no distance constraint, then we have an inductive invariant
                    if guard_of_last_cti == None:
                        return None
                    else:
                        logger.debug("No counterexample state. Reset guard_index_constraint.")
                        guard_of_last_cti = None
                        continue
                else:
                    # .... otherwise, we search for a cti with less distance
                    logger.debug("no counterexample state. Divide distance")
                    distance = distance // self.distance_constant
                    continue

            if was_inductivity:
                (cti, index_guard_linexp_phi_f, index_guard_linexp_f) = state_and_info
                logger.debug("Guard index f= %s" % index_guard_linexp_f)
                return (distance, (cti, phi_f.guard_linexp_pairs[index_guard_linexp_phi_f], f.guard_linexp_pairs[
                    index_guard_linexp_f]))  # we do not need the additional information for this type of template refinement
            else:
                (cex, _) = state_and_info
                return (distance, (cex, None, None))

    def get_constraint_from_counterexample_state(self, cti, exp_temp, phi_exp_temp, guard_linexp_phi_exp_temp,
                                                 guard_linexp_exp_temp):

        # Check whether we have a full model
        # for var in self.variables:
        #     if var not in cti:
        #         raise Exception("We need full solver models.")

        formulae = []
        var_to_val = {var: cti[var] for var in self.variables}

        state_formula = And([Equals(var, cti[var]) for var in self.variables])

        for (guard, linexp) in exp_temp.guard_templatelinexp_pairs:

            if is_sat([guard.pysmt_expression, state_formula] + self.template_var_constraint):
                # inductivity
                for (guard2, linexp2) in phi_exp_temp.guard_linexp_pairs:
                    if is_sat([guard2.pysmt_expression, state_formula] + self.template_var_constraint):
                        lhs = And(guard.pysmt_expression, guard2.pysmt_expression).substitute(var_to_val).simplify()
                        rhs = self.constraint_inequality(linexp2, linexp).pysmt_expression.substitute(
                            var_to_val).simplify()
                        formulae.append(Implies(lhs, rhs))

                # non-negativity
                lhs = guard.pysmt_expression.substitute(var_to_val).simplify()
                rhs = LinearInequality.LEQ(LinearExpression.get_constant_expression(self.variables, Real(0)),
                                           linexp).pysmt_expression.substitute(var_to_val).simplify()
                formulae.append(Implies(lhs, rhs))

                # safety
                for (guard2, linexp2) in self.property.guard_linexp_pairs:
                    if is_sat([guard2.pysmt_expression, state_formula]):
                        lhs = guard.pysmt_expression.substitute(var_to_val).simplify()
                        rhs = self.constraint_inequality(linexp, linexp2).pysmt_expression.substitute(
                            var_to_val).simplify()
                        formulae.append(Implies(lhs, rhs))

        # logger.debug('Constraint: %s' % new_constraint.serialize())

        return formulae

    def get_constraints_from_existing_ctis(self, ctis, phi_exp_temp, exp_temp):
        res = []
        for cti in ctis:
            res += self.get_constraint_from_counterexample_state(cti, exp_temp, phi_exp_temp, None, None)
        return res
