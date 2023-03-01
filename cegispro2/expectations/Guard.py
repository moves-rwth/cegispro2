from pysmt.shortcuts import Or, And, GE, Int, Real,EqualsOrIff, TRUE, FALSE, Implies, Iff
from cegispro2.solving.Solver import *
from cegispro2.inequalities.LinearInequality import LinearInequality
from cegispro2.expressions.LinearExpression import LinearExpression
import re

class Guard:
    """
    A guard datastructure in conjunctive normal form.
    """

    def __init__(self, variables, pysmt_expression, prune_unsat_disjuncts = False, side_condition = None):
        """

        :param variables: The variables containing in the inequalities
        :param list_of_list_of_ineqs: Representing the formula in disjunctive normal form
        :param prune_unsat_disjuncts: Whether to delete disjuncts which are equivalent to false.
        :param side_condition: Possibly another Guard. This guard does however not occur in self's pysmt_expression. Calling flatten_side_condition will return a new Guard
        with no side conditions, where self's side conditions are moved into to the list_of_list_of ineqs. This is basically for optimizing the pruning in CharacteristicFunctional.apply_expectation.
        Node: Side conditions are simply disregarded when conjoining Guards. Only substitution preserves them.
        """


        self.variables = variables

        if prune_unsat_disjuncts:
            self.prune_unsat_disjuncts()

        self.side_condition = side_condition
        self.pysmt_expression = pysmt_expression

    # @property
    # def pysmt_expression(self):
    #     if self._pysmt_expression is None:
    #         self.update_pysmt_expression()
    #     return self._pysmt_expression

    def flatten_side_condition(self):
        """

        :return: A new Guard without side condition, where self's side condition has been merged into the DNF representation or self, if there is no side_condition.
        """
        if self.side_condition == None:
            return self
        else:
            return Guard.AND(self, self.side_condition)

    def copy(self):
        return Guard(self.variables, self.pysmt_expression, prune_unsat_disjuncts = False, side_condition = self.side_condition)

    def prune_unsat_disjuncts(self):
        #outdate
        pass

    def conjoin(self, guard, prune_unsat_conjuncts = True):
        return Guard.AND(self, guard, prune_unsat_conjuncts)

    def get_constantification(self, var_to_helpervariables):
        """
        Helper function for conditional difference boundedness. Substitutes every variable by it's helper variable, thereby
        turning this Guard into a constant one.
        :param var_to_helpervariables: A dict from the linear expression's variables to helper variables.
        :return:
        """
        #new_list_of_list_of_ineqs = [[ineq.get_constantification(var_to_helpervariables) for ineq in list] for list in self.list_of_list_of_ineqs]
        return Guard(self.variables, LinearExpression.fast_substitute(self.pysmt_expression, var_to_helpervariables))

    @staticmethod
    def TRUE(variables):
        #return Guard.SINGLETON(variables, LinearInequality.LEQ(LinearExpression.get_constant_expression(variables, Real(0)),
        #                                                       LinearExpression.get_constant_expression(variables, Real(0))))

        return Guard(variables, TRUE())
    @staticmethod
    def FALSE(variables):
        return Guard(variables, FALSE())

    @staticmethod
    def AND(guard1, guard2, prune_unsat_conjuncts = False):
        return Guard(guard1.variables, And(guard1.pysmt_expression, guard2.pysmt_expression),
                     prune_unsat_conjuncts)

    @staticmethod
    def OR(guard1, guard2, prune_unsat_conjuncts = False):
        return Guard(guard1.variables, Or(guard1.pysmt_expression, guard2.pysmt_expression),
                     prune_unsat_conjuncts)

    @staticmethod
    def NEG(guard1, prune_unsat_conjuncts = False):
        return Guard(guard1.variables, Not(guard1.pysmt_expression), prune_unsat_conjuncts)


    @staticmethod
    def SINGLETON(variables, ineq):
        return Guard(variables, ineq.pysmt_expression)

    def equals(self, guard):
        return is_valid(Implies(And([GE(var, Int(0)) for var in self.variables]), Iff(self.pysmt_expression, guard.pysmt_expression)))

    def equals_syntactically(self, guard):
        return self.pysmt_expression == guard.pysmt_expression

    def is_sat(self):
        return is_sat([GE(var, Int(0)) for var in self.variables] + [self.pysmt_expression])

    def substitute(self, var_to_linexp):
        return Guard(self.variables, LinearExpression.fast_substitute(self.pysmt_expression, {var: var_to_linexp[var].pysmt_expression for var in var_to_linexp}), prune_unsat_disjuncts=False,
                     side_condition=self.side_condition.substitute(var_to_linexp) if self.side_condition is not None else None)

    def instantiate(self, template_variable_valuation):
        return Guard(self.variables, LinearExpression.fast_substitute(self.pysmt_expression, template_variable_valuation))

    def __str__(self):
        res = str(self.pysmt_expression.simplify().serialize())
        res = re.sub(r'(.*).0 ', r'\g<1>', res)
        res = re.sub(r'(.*)\.0\)', r'\g<1>', res)
        return re.sub(r'ToReal', r'', res)

    def prune_duplicate_disjuncts(self):
        return self

    def prune_duplicate_conjuncts(self):
        return self

    def as_probably_string(self):
        raise Exception("as_probably_string is currently not supported by guard")