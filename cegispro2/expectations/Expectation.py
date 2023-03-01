from pysmt.shortcuts import Real, And, GE, Int, LT, Implies, GT, get_env, Or, Equals, Minus
from cegispro2.inequalities.LinearInequality import LinearInequality
from cegispro2.expressions.LinearExpression import LinearExpression
from cegispro2.solving.Solver import *
from cegispro2.expectations.Guard import Guard
import logging

logger = logging.getLogger("cegispro2")

class Expectation:
    """
    We store expectations of the form [guard_1]*lin_exp1 + ... + [guard_n]*lin_expn where each
    guard_i is a conjenction of strict and non-strict linear inequalities. We assume expectations to be in guarded normal form, i.e.,
    the guard_i partition the state space.
    """

    def __init__(self, variables, guard_linexp_pairs):
        """
        :param variables: The list of variables the expectation contrains.
        :param guard_linexp_pairs: A list of pairs the form [(Guard, lin_exp)]
        """

        self.variables = variables
        self.guard_linexp_pairs = guard_linexp_pairs

        # Construct pysmt version of these pairs. Guards are replaced by their pysmt representation
        self.pysmt_guard_linexp_pairs = []

        for (guard, lin_exp) in self.guard_linexp_pairs:
            self.pysmt_guard_linexp_pairs.append((guard.pysmt_expression, lin_exp))

        self.vars_nat_valued = And([GE(var, Int(0)) for var in self.variables])
        #print("Checking whether Expectation is in GNF. This is expensive!")
        #self.check_gnf()
        #print("CAREFUL: NO CHECK WHETEHR EXPECTATION IS IN GNF")

    def __str__(self):
        out = ""

        for summand in self.guard_linexp_pairs:
            out += "[" + str(summand[0]) + "]"
            out += " * (" + str(summand[1]) + ") + "

        out = out[:-2]
        return out

    @staticmethod
    def pointwise_minimum(exp1, exp2):
        """

        :param exp1:
        :param exp2:
        :return: Returns the pointwise minimum as in the k-induction paper. The result will allways be in gnf again.
        """

        assert(exp1.variables == exp2.variables)

        new_guard_linexp_pairs = []

        for (guard1, linexp1) in exp1.guard_linexp_pairs:
             for (guard2, linexp2) in exp2.guard_linexp_pairs:

                # The case linexp1 <= linexp2:
                conj = Guard.AND(guard1, guard2)
                new_guard = Guard.AND(conj, Guard.SINGLETON(exp1.variables, LinearInequality.LEQ(linexp1, linexp2)), True)
                if new_guard.is_sat():
                    #new_guard = Expectation.prune_duplicates_in_guards(new_guard)
                    #new_guard = Expectation.prune_valid_inequalities(vars_nat_valued, new_guard)
                    new_guard_linexp_pairs.append((new_guard, linexp1))

                # The case linexp1 > linexp2:
                new_guard = Guard.AND(conj, Guard.SINGLETON(exp1.variables, LinearInequality.GT(linexp1, linexp2)), True)
                if new_guard.is_sat():
                    #new_guard = Expectation.prune_duplicates_in_guards(new_guard)
                    #new_guard = Expectation.prune_valid_inequalities(vars_nat_valued, new_guard)
                    new_guard_linexp_pairs.append((new_guard, linexp2))

        return Expectation(exp1.variables, new_guard_linexp_pairs)

    def check_gnf(self):
        """

        :return: True iff the guards partition the state space assuming all variables are Nat-valued.
        """

        # guards are disjoint
        for i in range(len(self.guard_linexp_pairs)):
            for j in range(len(self.guard_linexp_pairs)):
                if i < j:
                    if Guard.AND(self.guard_linexp_pairs[i][0], self.guard_linexp_pairs[j][0]).is_sat():
                        logger.debug("\n guards are not disjoint:")
                        logger.debug("%s" % str(self.guard_linexp_pairs[i][0]))
                        logger.debug("%s" % str(self.guard_linexp_pairs[j][0]))
                        return False

        # guards partition the statespace, i.e., there is no non-negative valuation of the program variables that does not satsify any guard
        if is_sat([self.vars_nat_valued, And([Not(pair[0]) for pair in self.pysmt_guard_linexp_pairs])]):
            logger.debug("guards do not partition the state space")
            return False

        return True

    def substitute(self, sub):
        """

        :param sub: A dict from variables to LinearExpressions
        :return: The expectation obtained from applying the substitution sub. Remains in GNF. Prune unsat guards.
        """

        new_guard_linexp_pairs = []
        for (guard, lin_exp) in self.guard_linexp_pairs:
            new_guard_linexp_pairs.append((guard.substitute(sub), lin_exp.substitute(sub)))

        return Expectation(self.variables, new_guard_linexp_pairs)

    def fast_instantiate(self, template_variable_valuation):
        """
        Substitutes the linexp only.
        :param template_variable_valuation:
        :return: Returns the expectation obtained form substituting every template variable in some coefficient by the given value.
        """
        return Expectation(self.variables, [(guard, linexp.instantiate(template_variable_valuation)) for (guard,linexp) in self.guard_linexp_pairs])

    def instantiate(self, template_variable_valuation):
        """

        :param template_variable_valuation:
        :return: Returns the expectation obtained form substituting every template variable in some coefficient by the given value.
        """
        return Expectation(self.variables, [(guard.instantiate(template_variable_valuation), linexp.instantiate(template_variable_valuation)) for (guard,linexp) in self.guard_linexp_pairs])

    @staticmethod
    def check_leq_syntactically_efficient(exp1, exp2, *additional_constraints):
        """

        :param self:
        :param exp1:
        :param exp2:
        :return: True if exp1 <= exp2 else (model s with exp1(s) > exp2(2), index of exp1_guard_linexp_pair, index of exp2_guard_linexp_pair
        """

        i_exp1 = get_env().formula_manager.get_symbol("index_exp1")
        i_exp2 = get_env().formula_manager.get_symbol("index_exp2")

        f1 = get_env().formula_manager.get_symbol("f_1")
        f2 = get_env().formula_manager.get_symbol("f_2")

        assert (exp1.variables == exp2.variables)

        formulas_f1 = exp1.get_pysmt_expression(f1,i_exp1)
        formulas_f2 = exp2.get_pysmt_expression(f2, i_exp2)

        formulas = formulas_f1 + formulas_f2 + [GT(f1, f2)]

        for additional_constraint in additional_constraints:
            if additional_constraint != None:
                formulas.append(additional_constraint)

        model = get_model([exp1.vars_nat_valued] + formulas)
        if model != None:
            return (model, int(str(model[i_exp1])), int(str(model[i_exp2])))

        return True

    @staticmethod
    def check_negated_rel(REL, exp1, exp2, *additional_constraints):
        """

        :param self:
        :param ineq:
        :param exp1:
        :param exp2:
        :return: True if not exists state s: exp1(s) rel exp2(s) (e.g., rel = GT or such an s otherwise
        """

        i_exp1 = get_env().formula_manager.get_symbol("index_exp1")
        i_exp2 = get_env().formula_manager.get_symbol("index_exp2")

        formulas = [
            Or([And([exp1.guard_linexp_pairs[i][0].pysmt_expression, exp2.guard_linexp_pairs[j][0].pysmt_expression,
                     REL(exp1.guard_linexp_pairs[i][1].pysmt_expression, exp2.guard_linexp_pairs[j][1].pysmt_expression),
                     Equals(i_exp1, Int(i)), Equals(i_exp2, Int(j))])
                for i in range(len(exp1.guard_linexp_pairs)) for j in range(len(exp2.guard_linexp_pairs))])]

        for additional_constraint in additional_constraints:
            if additional_constraint != None:
                formulas.append(additional_constraint)

        model = get_model([exp1.vars_nat_valued] + formulas)
        if model != None:
            return (model, int(str(model[i_exp1])), int(str(model[i_exp2])))

        return True

    @staticmethod
    def check_leq(exp1, exp2, *additional_constraints):
        """

        :param self:
        :param exp1:
        :param exp2:
        :return: True if exp1 <= exp2 else (model s with exp1(s) > exp2(2), index of exp1_guard_linexp_pair, index of exp2_guard_linexp_pair
        """

        return Expectation.check_negated_rel(GT, exp1, exp2, *additional_constraints)


    @staticmethod
    def check_leq_optimization(exp1, exp2, *additional_constraints):
        """
        Disregards additional_constraints for the moment!
        :param self:
        :param exp1:
        :param exp2:
        :return: True if exp1 <= exp2 else (model s with exp1(s) > exp2(2), index of exp1_guard_linexp_pair, index of exp2_guard_linexp_pair
        """

        i_exp1 = get_env().formula_manager.get_symbol("index_exp1")
        i_exp2 = get_env().formula_manager.get_symbol("index_exp2")
        diff = get_env().formula_manager.get_symbol("diff")

        #print("%s" % (len(exp1.guard_linexp_pairs) * len(exp2.guard_linexp_pairs)))
        #print(exp2)

        formulas = [And(exp1.vars_nat_valued, exp1.guard_linexp_pairs[i][0].pysmt_expression, exp2.guard_linexp_pairs[j][0].pysmt_expression,
                        GT(exp1.guard_linexp_pairs[i][1].pysmt_expression, exp2.guard_linexp_pairs[j][1].pysmt_expression),
                        Equals(diff, Minus(exp2.guard_linexp_pairs[j][1].pysmt_expression, exp1.guard_linexp_pairs[i][1].pysmt_expression)),
                        Equals(i_exp1, Int(i)), Equals(i_exp2, Int(j)))
                    for i in range(len(exp1.guard_linexp_pairs))
                    for j in range(len(exp2.guard_linexp_pairs))
                    if is_sat([And(exp1.vars_nat_valued, exp1.guard_linexp_pairs[i][0].pysmt_expression,
                                  exp2.guard_linexp_pairs[j][0].pysmt_expression,
                                  GT(exp1.guard_linexp_pairs[i][1].pysmt_expression,
                                     exp2.guard_linexp_pairs[j][1].pysmt_expression))])
                    ]

        # for additional_constraint in additional_constraints:
        #     if additional_constraint != None:
        #         formulas.append(additional_constraint)

        model = z3_check_sat_minimizing_var_check_formulae_separately(formulas, diff)
        if model != None:
            return (model, int(str(model[i_exp1])), int(str(model[i_exp2])))

        return True

    @staticmethod
    def check_geq_optimization(exp1, exp2, *additional_constraints):
        """
        Disregards additional_constraints for the moment!
        :param self:
        :param exp1:
        :param exp2:
        :return: True if exp1 >= exp2 else (model s with exp1(s) < exp2(2), index of exp1_guard_linexp_pair, index of exp2_guard_linexp_pair
        """

        i_exp1 = get_env().formula_manager.get_symbol("index_exp1")
        i_exp2 = get_env().formula_manager.get_symbol("index_exp2")
        diff = get_env().formula_manager.get_symbol("diff")

        #print("%s" % (len(exp1.guard_linexp_pairs) * len(exp2.guard_linexp_pairs)))
        #print(exp2)

        formulas = [And(exp1.vars_nat_valued, exp1.guard_linexp_pairs[i][0].pysmt_expression, exp2.guard_linexp_pairs[j][0].pysmt_expression,
                        LT(exp1.guard_linexp_pairs[i][1].pysmt_expression, exp2.guard_linexp_pairs[j][1].pysmt_expression),
                        Equals(diff, Minus(exp2.guard_linexp_pairs[j][1].pysmt_expression, exp1.guard_linexp_pairs[i][1].pysmt_expression)),
                        Equals(i_exp1, Int(i)), Equals(i_exp2, Int(j)))
                    for i in range(len(exp1.guard_linexp_pairs))
                    for j in range(len(exp2.guard_linexp_pairs))
                    if is_sat([And(exp1.vars_nat_valued, exp1.guard_linexp_pairs[i][0].pysmt_expression,
                                  exp2.guard_linexp_pairs[j][0].pysmt_expression,
                                  LT(exp1.guard_linexp_pairs[i][1].pysmt_expression,
                                     exp2.guard_linexp_pairs[j][1].pysmt_expression))])
                    ]

        # for additional_constraint in additional_constraints:
        #     if additional_constraint != None:
        #         formulas.append(additional_constraint)

        model = z3_check_sat_maximizing_var_check_formulae_separately(formulas, diff)
        if model != None:
            return (model, int(str(model[i_exp1])), int(str(model[i_exp2])))

        return True

    @staticmethod
    def check_geq(exp1, exp2, *additional_constraints):
        """

        :param self:
        :param exp1:
        :param exp2:
        :return: True if exp1 >= exp2 else (model s with exp1(s) < exp2(2), index of exp1_guard_linexp_pair, index of exp2_guard_linexp_pair
        """

        return Expectation.check_negated_rel(LT, exp1, exp2, *additional_constraints)

    def check_non_negativity(self, *additional_constraints):
        """

        :return: True if this expectation is non-negative everywhere, otherwise a solver (model, guard_linexp) representing a state where self is negative.
        """
        i_exp1 = get_env().formula_manager.get_symbol("index_exp1")
        formulas = [self.vars_nat_valued, Or(And(self.guard_linexp_pairs[i][0].pysmt_expression, LT(self.guard_linexp_pairs[i][1].pysmt_expression, Real(0)), Equals(i_exp1, Int(i))) for i in range(len(self.guard_linexp_pairs)))]
        for additional_constraint in additional_constraints:
            if additional_constraint != None:
                formulas.append(additional_constraint)
        model = get_model(formulas)
        if model != None:
            return (model, int(str(model[i_exp1])))

        return True

    def get_pysmt_expression(self, variable, index_variable):
        """

        :param variable:
        :return: a list of pysmt fomulas phi such that s \models phi iff s(variable) = self(s) assuming s is non-negative
        """
        return [Implies(self.guard_linexp_pairs[i][0].pysmt_expression,
                                  And(Equals(variable, self.guard_linexp_pairs[i][1].pysmt_expression),
                                      Equals(index_variable, Int(i))))
                          for i in range(len(self.guard_linexp_pairs))]


    def check_negated_rel_wrt_property(self, REL, property, *additional_constraints):
        """

        :param REL:
        :param property:
        :param additional_constraints:
        :return: True if not exists state s: self(s) REL property(s), else such an s.
        """

        i_exp1 = get_env().formula_manager.get_symbol("index_exp1")

        property_formula = Or([And(guard.pysmt_expression, self.guard_linexp_pairs[i][0].pysmt_expression,
                                   REL(self.guard_linexp_pairs[i][1].pysmt_expression, lin_exp.pysmt_expression),
                                   Equals(i_exp1, Int(i)))
                               for (guard, lin_exp) in property.guard_linexp_pairs
                               for i in range(len(self.guard_linexp_pairs))])

        to_check = [self.vars_nat_valued, property_formula]

        for additional_constraint in additional_constraints:
            if additional_constraint != None:
                to_check.append(additional_constraint)
        model = get_model(to_check)
        if model != None:
            return (model, int(str(model[i_exp1])))

        return True


    def check_safety(self, property, *additional_constraints):
        """

        :param property:
        :return: True if self <= property, else (s, linexp_of_property) with self[s] > linexp_of_property[s] for s in appropriate property guard.
        """
        return self.check_negated_rel_wrt_property(GT, property, *additional_constraints)


    def check_safety_superinvariant(self, property, *additional_constraints):
        """

        :param property:
        :return: True if self <= property, else (s, linexp_of_property) with self[s] > linexp_of_property[s] for s in appropriate property guard.
        """
        return self.check_negated_rel_wrt_property(GT, property, *additional_constraints)


    def check_safety_subinvariant(self, property, *additional_constraints):
        """

        :param property:
        :return: True if self >= property, else (s, linexp_of_property) with self[s] > linexp_of_property[s] for s in appropriate property guard.
        """
        return self.check_negated_rel_wrt_property(LT, property, *additional_constraints)


    def get_constantification(self, var_to_helpervariables):
        """
        Helper function for conditional difference boundedness. Substitutes every variable by it's helper variable, thereby
        turning this expectation into a constant one.
        :param var_to_helpervariables: A dict from the linear expression's variables to helper variables.
        :return:
        """

        new_guard_linexp = [(guard.get_constantification(var_to_helpervariables), linexp.get_constantification(var_to_helpervariables))
                            for (guard, linexp) in self.guard_linexp_pairs]
        res = Expectation(self.variables, new_guard_linexp)
        #logger.debug("constructed constantificaiton: %s" % str(res))
        return res

    def get_delta_expectation(self, var_to_helpervariabels):
        """
        Helper function for conditional difference boundedness. Returns an expectaton representing |self - self(\sigma)| where \sigma is represented by the helpervariables.
        :param var_to_helpervariabels:
        :return:
        """
        new_guard_linexp = []
        consted_exp = self.get_constantification(var_to_helpervariabels)

        for (guard, linexp) in self.guard_linexp_pairs:
            for (cguard, clinexp) in consted_exp.guard_linexp_pairs:
                # There are two cases we need to cover:
                conj_guard = Guard.AND(guard, cguard)


                #Case 1: [phi and psi and e_i <= a_j] * (a_j - e_i)
                #new_guard = Guard.AND(conj_guard, Guard.SINGLETON(self.variables, LinearInequality.LEQ(linexp, clinexp)))
                new_guard = conj_guard.copy()
                new_guard.side_condition = Guard.SINGLETON(self.variables, LinearInequality.LEQ(linexp, clinexp))
                new_linexp = clinexp.add(linexp.multiply(Real(-1)))
                new_guard_linexp.append((new_guard, new_linexp))

                #Case 2: [phi and psi and e_i > a_j] * (e_i - a_j)
                #new_guard = Guard.AND(conj_guard,
                #                          Guard.SINGLETON(self.variables, LinearInequality.GT(linexp, clinexp)))
                new_guard = conj_guard.copy()
                new_guard.side_condition = Guard.SINGLETON(self.variables, LinearInequality.GT(linexp, clinexp))
                new_linexp = linexp.add(clinexp.multiply(Real(-1)))
                new_guard_linexp.append((new_guard, new_linexp))


        return Expectation(self.variables, new_guard_linexp)

    def guards_as_comma_separated_pysmt_strings(self):

        begin = True
        res = ""
        for (guard, _) in self.guard_linexp_pairs:
            if begin:
                begin = False
                res = guard.as_probably_string()
            else:
                res += "," + guard.as_probably_string()

        return res

    def evaluate_at_state(self, state):
        """

        :param state: A state, i.e., a dict from variables to PySMT values.
        :return: The (PySMT) value of self at state.
        """

        diff = get_env().formula_manager.get_symbol("diff")

        state_formula = And([Equals(var, state[var]) for var in self.variables])

        # abuse diff value for the variable storing the value self evaluates to

        for (guard, linexp) in self.guard_linexp_pairs:
            formula = And([guard.pysmt_expression, state_formula, Equals(diff, linexp.pysmt_expression)])
            model = get_model([formula])

            if model is not None:
                return model[diff]