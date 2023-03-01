from pysmt.shortcuts import Or, And, GE, Int, Real,EqualsOrIff, TRUE
from cegispro2.solving.Solver import *
from cegispro2.inequalities.LinearInequality import LinearInequality
from cegispro2.expressions.LinearExpression import LinearExpression

class Guard:
    """
    A guard datastructure in disjunctive normal form. (Use for motzkin or oneshot)
    """

    def __init__(self, variables, list_of_list_of_ineqs, prune_unsat_disjuncts = False, side_condition = None):
        """

        :param variables: The variables containing in the inequalities
        :param list_of_list_of_ineqs: Representing the formula in disjunctive normal form
        :param prune_unsat_disjuncts: Whether to delete disjuncts which are equivalent to false.
        :param side_condition: Possibly another Guard. This guard does however not occur in self's pysmt_expression. Calling flatten_side_condition will return a new Guard
        with no side conditions, where self's side conditions are moved into to the list_of_list_of ineqs. This is basically for optimizing the pruning in CharacteristicFunctional.apply_expectation.
        Node: Side conditions are simply disregarded when conjoining Guards. Only substitution preserves them.
        """


        self.variables = variables
        self.list_of_list_of_ineqs = list_of_list_of_ineqs

        if prune_unsat_disjuncts:
            self.prune_unsat_disjuncts()

        self.side_condition = side_condition
        self._pysmt_expression = None

    @property
    def pysmt_expression(self):
        if self._pysmt_expression is None:
            self.update_pysmt_expression()
        return self._pysmt_expression

    def flatten_side_condition(self):
        """

        :return: A new Guard without side condition, where self's side condition has been merged into the DNF representation or self, if there is no side_condition.
        """
        if self.side_condition == None:
            return self
        else:
            return Guard.AND(self, self.side_condition)

    def copy(self):
        return Guard(self.variables, self.list_of_list_of_ineqs, prune_unsat_disjuncts = False)

    def prune_unsat_disjuncts(self):
        pass

    def update_pysmt_expression(self):
        self._pysmt_expression = And([Or([ineq.pysmt_expression for ineq in list]) for list in self.list_of_list_of_ineqs])

    def conjoin(self, guard, prune_unsat_conjuncts = True):
        return Guard.AND(self, guard, prune_unsat_conjuncts)

    def get_constantification(self, var_to_helpervariables):
        """
        Helper function for conditional difference boundedness. Substitutes every variable by it's helper variable, thereby
        turning this Guard into a constant one.
        :param var_to_helpervariables: A dict from the linear expression's variables to helper variables.
        :return:
        """
        new_list_of_list_of_ineqs = [[ineq.get_constantification(var_to_helpervariables) for ineq in list] for list in self.list_of_list_of_ineqs]
        return Guard(self.variables, new_list_of_list_of_ineqs)

    @staticmethod
    def TRUE(variables):
        #return Guard.SINGLETON(variables, LinearInequality.LEQ(LinearExpression.get_constant_expression(variables, Real(0)),
        #                                                       LinearExpression.get_constant_expression(variables, Real(0))))

        return Guard(variables, [[]])
    @staticmethod
    def FALSE(variables):
        return Guard(variables, [])

    @staticmethod
    def AND(guard1, guard2, prune_unsat_conjuncts = False):
        return Guard(guard1.variables, [a+b for a in guard1.list_of_list_of_ineqs for b in guard2.list_of_list_of_ineqs], prune_unsat_conjuncts)

    @staticmethod
    def OR(guard1, guard2, prune_unsat_conjuncts = False):
        return Guard(guard1.variables, guard1.list_of_list_of_ineqs + guard2.list_of_list_of_ineqs, prune_unsat_conjuncts)

    @staticmethod
    def NEG(guard1, prune_unsat_conjuncts = False):

        if len(guard1.list_of_list_of_ineqs) ==0:
            # guard is false
            zero_exp = LinearExpression.get_constant_expression(guard1.variables, Real(0))
            return Guard(guard1.variables, [[LinearInequality.LEQ(zero_exp, zero_exp)]]) # True

        result = Guard(guard1.variables, [[ineq.negate()] for ineq in guard1.list_of_list_of_ineqs[0]])
        for i in range(1,len(guard1.list_of_list_of_ineqs)):
            result = Guard.AND(result, Guard(guard1.variables, [[ineq.negate()] for ineq in guard1.list_of_list_of_ineqs[i]]), prune_unsat_conjuncts)

        return result

    @staticmethod
    def SINGLETON(variables, ineq):
        return Guard(variables, [[ineq]])

    def equals(self, guard):
        if len(self.list_of_list_of_ineqs) != len(guard.list_of_list_of_ineqs):
            return False

        for i in range(len(self.list_of_list_of_ineqs)):
            list1 = self.list_of_list_of_ineqs[i]
            list2 = guard.list_of_list_of_ineqs[i]
            if len(list1) != len(list2):
                return False
            for j in range(len(list1)):
                if not list1[j].equals(list2[j]):
                    return False
        return True

    def equals_syntactically(self, guard):
        if len(self.list_of_list_of_ineqs) != len(guard.list_of_list_of_ineqs):
            return False

        for i in range(len(self.list_of_list_of_ineqs)):
            list1 = self.list_of_list_of_ineqs[i]
            list2 = guard.list_of_list_of_ineqs[i]
            if len(list1) != len(list2):
                return False

            if not all(list1[i].equals_syntactically(list2[i]) for i in range(len(list1))):
                return False

        return True

    def is_sat(self):
        return is_sat([GE(var, Int(0)) for var in self.variables] + [self.pysmt_expression])

    def substitute(self, var_to_linexp):
        return Guard(self.variables, [[ineq.substitute(var_to_linexp) for ineq in list] for list in self.list_of_list_of_ineqs], prune_unsat_disjuncts=False,
                     side_condition=self.side_condition.substitute(var_to_linexp) if self.side_condition is not None else None)

    def instantiate(self, template_variable_valuation):
        return Guard(self.variables, [[ineq.instantiate(template_variable_valuation) for ineq in list] for list in self.list_of_list_of_ineqs])

    def replace_strict_by_nonstrict_inequalities_if_possible(self):
        return Guard(self.variables, [[ineq.to_nonstrict_inequality_if_possible_and_has_effect() for ineq in list] for list in self.list_of_list_of_ineqs])

    def __str__(self):
        res = ""
        if len(self.list_of_list_of_ineqs) >0:
            for list in self.list_of_list_of_ineqs:
                res += " ("
                if len(list)>0:
                    for conj in list:
                        res += str(conj) + " & "
                    res = res[:-2]
                else:
                    res += "true"
                res += ") |"

            res = res[:-2]
        else:
            res = "false"
        return res


    def prune_duplicate_disjuncts(self):

        new_list_of_list_of_ineqs = []

        for list_of_ineqs in self.list_of_list_of_ineqs:
            formula = And([ineq.pysmt_expression for ineq in list_of_ineqs])
            equiv = False
            for list_of_ineqs2 in new_list_of_list_of_ineqs:
                formula2 = And([ineq.pysmt_expression for ineq in list_of_ineqs2])
                if (not is_sat([formula, Not(formula2)])) and (not is_sat([Not(formula), formula2])) :
                    # equivalent
                    equiv = True
                    break

            if not equiv:
                new_list_of_list_of_ineqs.append(list_of_ineqs)

        return Guard(self.variables, new_list_of_list_of_ineqs)


    def prune_duplicate_conjuncts(self):
        new_list_of_list_of_ineqs = []
        for list_of_ineqs in self.list_of_list_of_ineqs:

            new_list_of_ineqs = []
            for ineq in list_of_ineqs:
                equiv = False
                for ineq2 in new_list_of_ineqs:
                    if (not is_sat([ineq.pysmt_expression, Not(ineq2.pysmt_expression)])) \
                            and (not (is_sat([Not(ineq.pysmt_expression), ineq2.pysmt_expression]))):
                        # equivalent)
                        equiv = True
                        break

                if not equiv:
                    new_list_of_ineqs.append(ineq)

            new_list_of_list_of_ineqs.append(new_list_of_ineqs)

        return Guard(self.variables, new_list_of_list_of_ineqs)

    def as_probably_string(self):
        if len(self.list_of_list_of_ineqs) ==0:
            return "false"

        res = ""
        begin = True
        for list in self.list_of_list_of_ineqs:
            if begin:
                res += "( "
                begin = False
            else:
                res += " || ( "

            if len(list) == 0:
                res += "true"
            else:
                begin2 = True
                for conj in list:
                    if begin2:
                        begin2 = False
                        res += conj.as_probably_string()
                    else:
                        res += " & " + conj.as_probably_string()

            res += " )"

        return res