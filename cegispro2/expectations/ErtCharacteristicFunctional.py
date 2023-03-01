from cegispro2.expectations.CharacteristicFunctional import CharacteristicFunctional
from cegispro2.expectations.Expectation import Expectation
from cegispro2.expectations.ExpectationTemplate import ExpectationTemplate
from cegispro2.solving.Solver import *
from cegispro2.expressions.LinearExpression import LinearExpression
from pysmt.shortcuts import Real

class ErtCharacteristicFunctional(CharacteristicFunctional):
    """
    The Ert-Characteristic functional is obtained from the wp-characteristic functional by adding 1.
    Existence of super-invariants I with I < infty imply UPAST.
    """

    def __init__(self, variables, variables_to_bounds, execute_guard_prob_sub_pairs, terminate_guard_linexp_pairs):
        super().__init__(variables, variables_to_bounds, execute_guard_prob_sub_pairs, terminate_guard_linexp_pairs)

        self.terminate_guards_linexp_pairs_plus_one = []
        for (guard,linexp) in self.terminate_guards_linexp_pairs:
            self.terminate_guards_linexp_pairs_plus_one .append(
                (guard, linexp.add(LinearExpression.get_constant_expression(self.variables, Real(1)))))

    def get_initial_expectation_template(self):
        """

        :return: Returns the canonical ExpectationTemplate originating form this functional.
        """
        return ExpectationTemplate(self.variables, [guard for (guard,prob_sub_pair) in self.execute_guard_prob_sub_pairs],
                                   self.terminate_guards_linexp_pairs_plus_one)

    def apply_expectation(self, exp, prune_unsat_guards_early = True, substitute_helpers_back_to_normals = False, helpvar_to_var = None):


        #Can be more efficient my modifying apply_expectation more directly
        wp_exp = super().apply_expectation(exp, prune_unsat_guards_early, substitute_helpers_back_to_normals, helpvar_to_var)

        ert_guard_linexp = []
        for (guard, linexp) in wp_exp.guard_linexp_pairs:
            ert_guard_linexp.append((guard, linexp.add(LinearExpression.get_constant_expression(self.variables, Real(1)))))

        ert_exp = Expectation(self.variables, ert_guard_linexp)
        return ert_exp