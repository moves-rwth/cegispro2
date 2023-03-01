from pysmt.shortcuts import And, GE, Int, INT, Real, Symbol, Equals, Plus, REAL, LT, StrToInt, TRUE
from cegispro2.inequalities.LinearInequality import LinearInequality
from cegispro2.expressions.LinearExpression import LinearExpression
from cegispro2.expectations.Expectation import Expectation
from cegispro2.expectations.ExpectationTemplate import ExpectationTemplate
from cegispro2.solving.Solver import *
from cegispro2.expectations.Guard import Guard
import logging
import itertools

logger = logging.getLogger("cegispro2")

class CharacteristicFunctional():
    """
    Represents a wp-characteristic functional in guarded normal form:
    [guard_execute_1]*((prob,subs) + ... + (prob,subs)) + ... + [guard_execute_n]*((prob,subs) + ... (prob,subs))
    + [guard_term_1]*(linexp) + ... + [guard_term_n]*(linexp)

    where the guards partition the state space.
    """

    def __init__(self, variables, variables_to_bounds, execute_guard_prob_sub_pairs, terminate_guard_linexp_pairs):
        """
        :param variables: A list of variables
        :param execute_guard_prob_sub_pairs: A list of pairs (guard, list_of_pairs_prob_sub)
        :param terminate_guard_linexp_pairs: A list of pairs (guard, linexp)
        """

        self.variables = variables
        self.variables_to_bounds = variables_to_bounds
        self.execute_guard_prob_sub_pairs = execute_guard_prob_sub_pairs
        self.terminate_guards_linexp_pairs = terminate_guard_linexp_pairs

        self.pysmt_execute_guard_prob_sub_pairs = [(pair[0].pysmt_expression, pair[1]) for pair in self.execute_guard_prob_sub_pairs]
        self.pysmt_terminate_guards_linexp_pairs = [(pair[0].pysmt_expression, pair[1]) for
                                                   pair in self.terminate_guards_linexp_pairs]
        logger.debug("\nCharacteristic Functional:")
        logger.debug(self)
        #logger.debug("\nChecking whether characteristic functional is in gnf. This is expensive.")
        #self.check_gnf()
        logger.debug("\nChecking whether updates always yield non-negative result.")
        if not self.check_updates_yield_nonnegative_result():
            raise Exception("All assignments in the program must yield a non-negative result.")

        #self.check_all_probs_add_to_one()


    def check_all_probs_add_to_one(self):
        """

        :return: True iff all probabilities in all commmands add up to 1.
        """
        for (_, prob_sub_pairs) in self.execute_guard_prob_sub_pairs:
            assert (is_sat([Equals(Plus([pair[0] for pair in prob_sub_pairs]), Real(1))]))

    def check_gnf(self):
        """

        :return: True iff the characteristic functional is in gnf.
        """

        variables_nat = And([GE(var, Int(0)) for var in self.variables])

        list_of_all_guards = [pair[0] for pair in self.execute_guard_prob_sub_pairs] + [pair[0] for pair in self.terminate_guards_linexp_pairs]
        guards_as_pysmt = [guard.pysmt_expression for guard in list_of_all_guards]

        for i in range(len(guards_as_pysmt)):
            for j in range(len(guards_as_pysmt)):
                if i<j:
                    model = get_model([variables_nat, guards_as_pysmt[i], guards_as_pysmt[j]])

                    if model != None:
                        print("The following two guards overlap (%s, %s):" % (i,j))
                        print(guards_as_pysmt[i].serialize())
                        print(guards_as_pysmt[j].serialize())
                        print(model)
                        raise Exception("Characteristic functional is not in GNF")

        model = get_model([variables_nat, And([Guard.NEG(guard, False).pysmt_expression for guard in list_of_all_guards])])
        if not model == None:
            raise Exception("Characteristic functional does not partition the state space: %s" % model)


    def check_updates_yield_nonnegative_result(self):
        """

        :return: True iff every guard ensures that every updates yields a non-negative result.
        """

        variables_nat = And([GE(var, Int(0)) for var in self.variables])
        for (pysmt_guard, prob_sub_pairs) in self.pysmt_execute_guard_prob_sub_pairs:
            for prob_sub_pair in prob_sub_pairs:
                sub = prob_sub_pair[1]
                for var in self.variables:
                    if var in sub:
                        if is_sat([variables_nat, pysmt_guard, LT(sub[var].pysmt_expression, Real(0))]):
                            print("Update %s can be negative." % str(sub[var]))
                            return False

        return True



    def apply_expectation_old(self, exp):
        """

        :param exp: The expectation we apply to this characteristic functional.
        :return: Phi(exp) in gnf, where Phi is this characteristic functional.
        """
        #print("applying expectation")
        assert(exp.variables == self.variables)

        new_guard_linexp_pairs = []
        variables_nat = And([GE(var, Int(0)) for var in self.variables])

        for (guard, prob_sub_pairs) in self.execute_guard_prob_sub_pairs:

            substituted_exps = [exp.substitute(pair[1]) for pair in prob_sub_pairs]

            list_of_list_of_pairs = [exp.guard_linexp_pairs for exp in substituted_exps]

            for combination in itertools.product(*list_of_list_of_pairs):

                if is_sat([variables_nat, guard.pysmt_expression] + [guard.pysmt_expression for (guard,_) in combination]):
                    new_guard = guard
                    for (cur_guard, _) in combination:
                        conj = new_guard.conjoin(cur_guard, False)
                        new_guard = conj if not new_guard.equals(conj) else new_guard

                    #new_guard.prune_unsat_disjuncts()
                    #construct linear expression (weighted sum)
                    cur = LinearExpression.get_constant_expression(self.variables, Real(0))
                    for i in range(len(prob_sub_pairs)):
                        prob = prob_sub_pairs[i][0]
                        lin_exp = combination[i][1]
                        cur = cur.add(lin_exp.multiply(prob))

                    new_guard_linexp_pairs.append((new_guard, cur))

        logger.debug("Number guard_linexp_pairs: %s" % len(new_guard_linexp_pairs))
        new_guard_linexp_pairs = new_guard_linexp_pairs + self.terminate_guards_linexp_pairs
        #print(len(new_guard_linexp_pairs))
        #print("and create applied expectation")
        res = Expectation(self.variables, new_guard_linexp_pairs)
        #print("Result of applying: %s" % str(res))
        return res



    def apply_expectation(self, exp, prune_unsat_guards_early = True, substitute_helpers_back_to_normals = False, helpvar_to_var = None):
        """

        :param exp: The expectation we apply to this characteristic functional.
        :param prune_unsat_guards_early: Whether to prune unsat guards. Way more efficient, but might be impossible if nonlinearity is unvoled.
        :param substitute_helpers_back_to_normals: Whether to use helpvar_to_var to substitute every helpvar by its corresponding var after applying the loop substitutions.
        :param helpvar_to_var: See substitute_helpers_back_to_normals.
        :return: Phi(exp) in gnf, where Phi is this characteristic functional.
        """
        #print("applying expectation")
        assert(exp.variables == self.variables)

        #print("applying %s" % str(exp))

        new_guard_linexp_pairs = []
        variables_nat = And([GE(var, Int(0)) for var in self.variables])


        totalcount = 0
        prunecount = 0

        for (guard, prob_sub_pairs) in self.execute_guard_prob_sub_pairs:
            #logger.debug("consider guard %s" % str(guard))
            substituted_exps = [exp.substitute(pair[1]) for pair in prob_sub_pairs]
            # stores for every expectation the current guard_linexp_pair to consider
            index_list = [0 for i in range(len(substituted_exps))]
            current_exp = 0

            cur_formulas = [variables_nat, guard.pysmt_expression]
            while True:
                totalcount += 1

                cur_guard_linexp = substituted_exps[current_exp].guard_linexp_pairs[index_list[current_exp]]
                cur_formulas.append(cur_guard_linexp[0].pysmt_expression.substitute(helpvar_to_var) if substitute_helpers_back_to_normals else
                                    cur_guard_linexp[0].pysmt_expression)


                if (not prune_unsat_guards_early) or is_sat(cur_formulas):
                    # There are two cases: If the current_exp is the last exp in substitued_exp, we found a combination that we have to add
                    if current_exp == len(index_list) - 1:
                        # if current_exp is the last expectation in the list ..
                        new_guard = guard.flatten_side_condition()
                        for (cur_guard, _) in [substituted_exps[i].guard_linexp_pairs[index_list[i]] for i in range(len(index_list))]:
                            new_guard = new_guard.conjoin(cur_guard.flatten_side_condition(), False)

                        if substitute_helpers_back_to_normals:
                            new_guard = new_guard.instantiate(helpvar_to_var)


                        new_linexp = LinearExpression.get_constant_expression(self.variables, Real(0))
                        for i in range(len(prob_sub_pairs)):
                            prob = prob_sub_pairs[i][0]
                            lin_exp = substituted_exps[i].guard_linexp_pairs[index_list[i]][1]
                            new_linexp = new_linexp.add(lin_exp.multiply(prob))

                        if substitute_helpers_back_to_normals:
                            new_linexp = new_linexp.instantiate(helpvar_to_var)

                        new_guard_linexp_pairs.append((new_guard, new_linexp))

                    else:
                        #otherwise we just increase current_exp
                        current_exp = current_exp + 1
                        continue

                prunecount += 1

                #if not current_exp == len(index_list) - 1:
                #    logger.debug("prune")
                #    print("PRUNE! current_exp = %s ,   last_index = %s" % (current_exp, len(substituted_exps) -1))


                cur_formulas.pop()
                found_new_indizes = False
                while not found_new_indizes:
                    if index_list[current_exp] < len(substituted_exps[current_exp].guard_linexp_pairs) -1:
                        # There is still an index to process in current_exp
                        found_new_indizes = True
                        index_list[current_exp] = index_list[current_exp] + 1
                    else:
                        # There is no more index to process
                        if current_exp == 0:
                            break
                        else:
                            cur_formulas.pop()
                            index_list[current_exp] = 0
                            current_exp = current_exp - 1

                if not found_new_indizes:
                    break

        #logger.debug("pruned %s out of %s" % (prunecount, totalcount))
        #logger.debug("Number guard_linexp_pairs: %s" % len(new_guard_linexp_pairs))
        new_guard_linexp_pairs = new_guard_linexp_pairs + self.terminate_guards_linexp_pairs
        #print("and create applied expectation")
        #print(len(new_guard_linexp_pairs))
        res = Expectation(self.variables, new_guard_linexp_pairs)
        #print("Result of applying: %s" % str(res))
        #assert (res.check_gnf() == True)
        return res


    def get_initial_expectation_template(self):
        """

        :return: Returns the canonical ExpectationTemplate originating form this functional.
        """
        return ExpectationTemplate(self.variables, [guard for (guard,prob_sub_pair) in self.execute_guard_prob_sub_pairs],
                                   self.terminate_guards_linexp_pairs)


    def is_inductive(self, exp):
        """

        :param exp:
        :return: True if Phi(exp) <= exp
        """

        return Expectation.check_leq(self.apply_expectation(exp), exp)

    def is_coinductive(self, exp):
        """

        :param exp:
        :return: True if Phi(exp) <= exp
        """

        return Expectation.check_geq(self.apply_expectation(exp), exp)

    def get_list_of_states_satisfying_loop_guard(self):
        """
        Notice that this terminates only if the loop ist finite-state.
        :return: A list of dicts from variables to PySMT values representing all states satisfying the loop guard.
        """

        vars_nat_valued = And([GE(var, Int(0)) for var in self.variables])
        exclude_formula = TRUE()
        guard_formula = And([guard for (guard, _) in self.pysmt_execute_guard_prob_sub_pairs])
        res = []

        model = get_model([And([vars_nat_valued, exclude_formula, guard_formula])])

        while model is not None:
            res.append({var: model[var] for var in self.variables})
            exclude_formula = And([exclude_formula, Not(And([Equals(var, model[var]) for var in self.variables]))])
            model = get_model([And(vars_nat_valued, exclude_formula, guard_formula)])

        return res

    def __str__(self):
        res = ""
        for (guard, prob_sub_pairs) in self.execute_guard_prob_sub_pairs:
            res += "[" + str(guard) + "] * ("
            for (prob, sub) in prob_sub_pairs:
                res += str(prob) + "*" + "f[" + str({var:str(sub[var]) for var in sub}) + "] + "
            res = res[:-2]
            res += "\n+"

        for (guard, linexp) in self.terminate_guards_linexp_pairs:
            res += " [" + str(guard) + "] * (" + str(linexp)+ ") + "

        res = res[:-2]
        return res

