from cegispro2.synthesis.TemplateRefinement.FixedPartitionTemplateRefiner import FixedPartitionTemplateRefiner
from cegispro2.synthesis.synthesis_utils import *
from cegispro2.expectations.Expectation import Expectation
from fractions import Fraction
from pysmt.shortcuts import TRUE
import itertools
from math import floor, ceil

class SplitFiniteStateSpaceRefiner(FixedPartitionTemplateRefiner):
    """
    Fixed-partition.
    Refinement strategy that obtains a new template by splitting the last instance of the current template into inductive and non-inductive parts
    """
    def __init__(self, variables, char_fun, property, options, statistics):
        super(SplitFiniteStateSpaceRefiner, self).__init__(variables,char_fun,property,options,statistics)


        # For this refinement, we need to have bounds for all of the variables
        self.var_to_bounds = char_fun.variables_to_bounds
        if not all(var in self.var_to_bounds for var in variables):
            raise Exception("Finite state space splitting requires bounds for each variable.")

        self.num_partitionings = 1
        self.use_motzkin = options.use_motzkin
        self.distance_constant = options.distance

    def get_initial_constraint_for_template(self, template):
        # Since guards do not contain template variables, we can constrain both safety and non-negativity via motzkin
        if self.use_motzkin:
            return get_safety_motzkin_constraints(template, self.property, self.variables, constraint_inequality=self.constraint_inequality) \
                   + get_nonnegativity_motzkin_constraints(template, self.variables)
        else:
            return [TRUE()]

    def get_refined_template(self, old_template, ctis, last_cti, f, phi_f):

        self.num_partitionings += 1

        var_to_guards = []
        for var in self.variables:
            (l,u) = self.var_to_bounds[var]

            num_parts = min(u-l, self.num_partitionings)

            cur_var_to_guards = []
            var_to_coeff = {varr: (Real(1) if varr == var else Real(0)) for varr in self.variables}
            for i in range(1,num_parts+1):
                if i == 1:
                    # [var <= l + (u-l)/numparts]
                    cur_var_to_guards.append(Guard.SINGLETON(self.variables, LinearInequality.LEQ(
                        LinearExpression(var_to_coeff, Real(0)),
                        LinearExpression.get_constant_expression(self.variables, Real(floor(l + Fraction(u-l, num_parts))))
                    )))

                else:
                    # [var > l + (i-1)*(u-l)/numparts]
                    cur_guard = Guard.SINGLETON(self.variables, LinearInequality.GT(
                        LinearExpression(var_to_coeff, Real(0)),
                        LinearExpression.get_constant_expression(self.variables, Real(floor(l + Fraction((i-1)*(u - l), num_parts))))
                    ))

                    if i < num_parts:
                        cur_guard = cur_guard.AND(cur_guard,
                                              Guard.SINGLETON(self.variables, LinearInequality.LEQ(
                                                  LinearExpression(var_to_coeff, Real(0)),
                                                  LinearExpression.get_constant_expression(self.variables, Real(
                                                      floor(l + Fraction(i * (u - l), num_parts))))
                                              )))
                    cur_var_to_guards.append(cur_guard)


            var_to_guards.append(cur_var_to_guards)


        guards_to_conjoin = []
        for combination in itertools.product(*var_to_guards):
            guard = Guard.TRUE(self.variables)
            for g in combination:
                guard = Guard.AND(guard, g)
            guards_to_conjoin.append(guard)

        guards_with_template = []
        for (guard, linexp) in self.options.initial_template.guard_templatelinexp_pairs:
            for guard2 in guards_to_conjoin:
                if is_sat([guard.pysmt_expression, guard2.pysmt_expression]):
                    conj = Guard.AND(guard, guard2)
                    guards_with_template.append(conj)

        new_template = ExpectationTemplate(self.variables, guards_with_template,
                                           self.char_fun.terminate_guards_linexp_pairs)
        #logger.debug("New template:")
        #logger.debug(new_template)
        #print(new_template)
        return new_template