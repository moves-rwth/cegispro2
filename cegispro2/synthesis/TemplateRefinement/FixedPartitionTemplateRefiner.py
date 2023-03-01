from cegispro2.synthesis.TemplateRefinement.TemplateRefiner import TemplateRefiner
from cegispro2.synthesis.synthesis_utils import *
from cegispro2.expectations.Expectation import Expectation
from pysmt.shortcuts import TRUE

class FixedPartitionTemplateRefiner(TemplateRefiner):
    """
    Fixed-partition.
    Refinement strategy that obtains a new template by splitting the last instance of the current template into inductive and non-inductive parts.
    """
    def __init__(self, variables, char_fun, property, options, statistics):
        super(FixedPartitionTemplateRefiner, self).__init__(variables,char_fun,property,options, statistics)

        self.instantiate_parameters = Expectation.fast_instantiate

        self.optimization_constraint = TRUE()
        if options.optimizing_synthesizer:
            # Maximize for lower bounds, minimize for upper bounds.
            self.synthesize_parameter_valuation = (lambda constraints: z3_check_sat_maximizing_var(constraints + [self.optimization_constraint], self.diff_var)) if options.invarianttype == "sub" \
                else (lambda constraints: z3_check_sat_minimizing_var(constraints + [self.optimization_constraint], self.diff_var))
        else:
            self.synthesize_parameter_valuation = get_model


    def get_next_counterexample_state(self, f, phi_f, exp_temp, phi_exp_temp, last_cti, guard_of_last_cti, distance):
        # we need to check for inductivity only
        while True:

            # -------- Computable double distance constraint --------
            double_distance_constraint = None
            if distance > 1:
                double_distance_constraint = get_double_distance_constraint(self.variables, last_cti, distance)
            # --------------------------------------------------

            # -------- Check inductivity, safety, and well-definedness --------
            self.statistics.inductivity_check_time.start_timer()
            logger.debug("check inductivity")
            state_and_info = self.inductivity_check(phi_f, f, double_distance_constraint)
            was_cti = False

            # we need to check safety and well-definedness only if we do not use motzkin to ensure it
            if (not self.options.use_motzkin) and state_and_info == True:
                # we have to check non-negativity and safety
                logger.debug("check safety")
                state_and_info = self.check_safety(f, self.property, double_distance_constraint)
                if state_and_info == True:
                    # check non-negativity
                    logger.debug("check non-neg")
                    state_and_info = f.check_non_negativity(double_distance_constraint)

                    if not state_and_info == True:
                        logger.debug("cex type: non-negativity")
                    pass
                else:
                    logger.debug("cex type: safety")
            else:
                was_cti = True
            self.statistics.inductivity_check_time.stop_timer()

            # ----------------- Process result
            if state_and_info == True:
                # If there is no cti ...
                if double_distance_constraint == None:
                    # ... and there was no distance constraint, then we have an inductive invariant
                    return None
                else:
                    # .... otherwise, we search for a cti with less distance
                    logger.debug("no cti. Divide distance")
                    distance = distance // self.distance_constant
                    continue

            if was_cti:
                (cti, index_guard_linexp_phi_f, index_guard_linexp_f) = state_and_info
                to_return = (cti, phi_exp_temp.guard_linexp_pairs[index_guard_linexp_phi_f],
                             exp_temp.guard_linexp_pairs[index_guard_linexp_f])
            else:
                (cti, index_guard_linexp_f) = state_and_info
                to_return = (cti, None, exp_temp.guard_linexp_pairs[index_guard_linexp_f])

            return (distance, to_return)


    def get_constraint_from_counterexample_state(self, cti, exp_temp, phi_exp_temp, guard_linexp_phi_exp_temp,
                                                 guard_linexp_exp_temp):
        """

        :param cti: A map from program variables to valuations.
        :return: TODO
        """

        # Optimization: if guard_linexp_exp_temp is given, we need not search for it
        state_formula = And([Equals(var, cti[var]) for var in self.variables])
        if guard_linexp_exp_temp is not None:
            (_, linexp_exp_temp) = guard_linexp_exp_temp
        else:
            # search for the correct one
            for (guard, linexp) in exp_temp.guard_templatelinexp_pairs:
                if is_sat([guard.pysmt_expression, state_formula]):
                    guard_linexp_exp_temp = (guard, linexp)
                    (_, linexp_exp_temp) = guard_linexp_exp_temp
                    break

        # Optimization: if cti was a counterexmaple to induction, then guard_linexp_phi_exp_temp is given.
        if guard_linexp_phi_exp_temp is not None:
            (_, linexp_phi_exp_temp) = guard_linexp_phi_exp_temp
        else:
            # search for the correct one
            for (guard2, linexp2) in phi_exp_temp.guard_linexp_pairs:
                if is_sat([guard2.pysmt_expression, state_formula]):
                    linexp_phi_exp_temp = linexp2
                    break

        # inductivity
        var_to_val = {var: cti[var] for var in self.variables}
        constraint = self.constraint_inequality(linexp_phi_exp_temp, linexp_exp_temp)
        constraints = [constraint.pysmt_expression_from_substituting_cti(var_to_val)]

        if not self.options.use_motzkin:

            (guard, linexp) = guard_linexp_exp_temp
            # non-negativity
            constraints.append(LinearInequality.LEQ(LinearExpression.get_constant_expression(self.variables, Real(0)),
                                                    linexp).pysmt_expression.substitute(var_to_val).simplify())

            # safety
            for (guard2, linexp2) in self.property.guard_linexp_pairs:
                if is_sat([guard2.pysmt_expression, state_formula]):
                    constraints.append(
                        self.constraint_inequality(linexp, linexp2).pysmt_expression.substitute(var_to_val).simplify())

        if self.options.optimizing_synthesizer:
            # Optimize I(s)
            self.optimization_constraint = Equals(self.diff_var, linexp_exp_temp.pysmt_expression.substitute(var_to_val))

        return constraints

    def get_constraints_from_existing_ctis(self, ctis, phi_exp_temp, exp_temp):

        # TODO: can we do this more efficiently?

        logger.debug("Getting constraints from existsing ctis ..")

        index_f_formula = Or(
            [And(exp_temp.guard_templatelinexp_pairs[i][0].pysmt_expression, Equals(self.index_f_var, Int(i))) for i in
             range(len(exp_temp.guard_templatelinexp_pairs))])

        index_phi_f_formula = Or(
            [And(phi_exp_temp.guard_linexp_pairs[i][0].pysmt_expression, Equals(self.index_phi_f_var, Int(i))) for i in
             range(len(phi_exp_temp.guard_linexp_pairs))])

        constraintlist = []

        for cti in ctis:
            model = get_model(
                [index_f_formula, index_phi_f_formula] + [Equals(var, cti[var]) for var in self.variables])
            assert (model != None)
            index_guard_f = int(str(model[self.index_f_var]))
            index_guard_phi_f = int(str(model[self.index_phi_f_var]))
            constraintlist = constraintlist + self.get_constraint_from_counterexample_state(cti, exp_temp, phi_exp_temp,
                                                                                            phi_exp_temp.guard_linexp_pairs[
                                                                                                index_guard_phi_f],
                                                                                            exp_temp.guard_linexp_pairs[
                                                                                                index_guard_f])


        logger.debug(".. done")
        return constraintlist


