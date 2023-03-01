from pysmt.shortcuts import REAL, Real, And, GE, Equals, Plus, Times, Minus, Or, FreshSymbol, get_env, Ite, Int
from cegispro2.inequalities.LinearInequality import LinearInequality
from cegispro2.expressions.LinearExpression import LinearExpression
from cegispro2.solving.Solver import *
from cegispro2.expectations.Guard import Guard
from cegispro2.expectations.ExpectationTemplate import ExpectationTemplate

from fractions import Fraction


import logging

logger = logging.getLogger("cegispro2")

def get_motzkin_constraints(variables, guard, to_be_implied):
    """
    Returns an LRA-formula constraints equivalent to:
      for all states s: s\models inequalities_on_lhs  implies   to_be_implied

    :param inequalities_on_lhs: The guard on the left-hand side of the implication.
    :param to_be_implied: The linear inequality that is to be implied by the inequalities_on_lhs.
    :return: an LRA formula as described above.
    """

    constraints = []



    for list_ineqs in guard.list_of_list_of_ineqs:
        list_ineqs = list_ineqs  + get_vars_are_nats_constraints(variables)

        lambda_0 = get_new_motzkin_symbol()
        # for every inequalitiy i, we need a lambda_i
        lambda_i = [get_new_motzkin_symbol() for i in range(len(list_ineqs))]

        # Motzkin variables must be non-negative
        ge_constraints = [GE(var, Real(0)) for var in lambda_i + [lambda_0]]

        first_disjunct_constraints = []
        # Compute first disjunct lambda_m+k+1>0 and coeff_1 = sum ... and rhs_of_inequality
        for var in variables:
            first_disjunct_constraints.append(Equals(to_be_implied.linear_expression.var_to_coeff[var],
                                                     Plus([Times(lambda_i[i],
                                                                 list_ineqs[i].linear_expression.var_to_coeff[var])
                                                           for i in range(len(list_ineqs))])))

        # Multiplications by -1 are necessary to bring the constraints in the Ax + b <=/< 0 normal form
        # now for the absolute part
        first_disjunct_constraints.append(Equals(Times(Real(-1), to_be_implied.rhs),
                                                 Minus(Plus([Times(lambda_i[i],
                                                                   Times(Real(-1), list_ineqs[i].rhs))
                                                             for i in range(len(list_ineqs))]), lambda_0)))

        second_disjunct_constraints = []
        # Compute second disjunct lambda_m+k+1=0 and 0 = sum ... and 1=
        for var in variables:
            second_disjunct_constraints.append(Equals(Real(0),
                                                      Plus([Times(lambda_i[i],
                                                                  list_ineqs[i].linear_expression.var_to_coeff[
                                                                      var]) for i in range(len(list_ineqs))])))

        # now for the absolute part
        second_disjunct_constraints.append(Equals(Real(1),
                                                  Minus(Plus([Times(lambda_i[i],
                                                                    Times(Real(-1), list_ineqs[i].rhs))
                                                              for i in range(len(list_ineqs))]), lambda_0)))

        constraints.append(And(*ge_constraints, Or(And(first_disjunct_constraints), And(second_disjunct_constraints))))

    return And(constraints)


def get_new_motzkin_symbol():
    """

    :return: Returns a fresh motzkin variable
    """
    return FreshSymbol(REAL)


def get_safety_motzkin_constraints(exp_temp, spec, variables, strict_to_nonstrict = False, constraint_inequality = LinearInequality.LEQ):
    """
    TODO
    :param exp_temp:
    :param spec:
    :param vars_are_nats:
    :return:
    """
    res = []

    for (guard1, linexp) in exp_temp.guard_linexp_pairs:
          for (guard2, linexp_on_rhs) in spec.guard_linexp_pairs:
            conjoined = Guard.AND(guard1, guard2)
            #pysmt_guards = And([ineq.pysmt_expression for ineq in all_guards])
            if conjoined.is_sat():
                conjoined.prune_unsat_disjuncts()
                if strict_to_nonstrict:
                    conjoined = conjoined.replace_strict_by_nonstrict_inequalities_if_possible()

                to_be_implied = constraint_inequality(linexp, linexp_on_rhs)
                res.append(get_motzkin_constraints(variables, conjoined, to_be_implied))
    return res


def get_nonnegativity_motzkin_constraints(exp_temp, variables, strict_to_nonstrict = False):

    res=[]
    for (guard, linexp) in exp_temp.guard_templatelinexp_pairs:
        res.append(get_motzkin_constraints(variables, guard.replace_strict_by_nonstrict_inequalities_if_possible() if strict_to_nonstrict else guard,
                                           LinearInequality.GEQ(linexp,LinearExpression.get_constant_expression(variables,Real(0)))))
    return res


def get_vars_are_nats_constraints(variables):
    vars_are_nats = []
    for var in variables:
        exp_dict = {}
        for cur_var in variables:
            if cur_var == var:
                exp_dict[cur_var] = Real(1)
            else:
                exp_dict[cur_var] = Real(0)

        vars_are_nats.append(LinearInequality.GEQ(LinearExpression(exp_dict, Real(0)),
                                                  LinearExpression.get_constant_expression(variables, Real(0))))

    return vars_are_nats


def validate_inductive_invariant(charfun, options, inductive_invariant, property):
    charfun.check_gnf()
    logger.debug("Checking non-negativity")
    assert (inductive_invariant.check_non_negativity() == True)
    logger.debug("Checking guarded normal form")
    assert (inductive_invariant.check_gnf() == True)

    if options.invarianttype == "super":
        logger.debug("Checking inductivity")
        assert(charfun.is_inductive(inductive_invariant) == True)
        logger.debug("Checking safety")
        assert(inductive_invariant.check_safety_superinvariant(property) == True)

    elif options.invarianttype == "sub":
        logger.debug("Checking coinductivity")
        assert (charfun.is_coinductive(inductive_invariant) == True)
        logger.debug("Checking safety")
        assert (inductive_invariant.check_safety_subinvariant(property) == True)

    else:
        raise Exception("unkown invariant type")





def get_double_distance_constraint(variables, last_cti, distance):
    """
    TODO
    :param last_cti:
    :param distance:
    :return:
    """

    new_distance = Plus([Ite(GE(Minus(var, last_cti[var]), Int(0)),
                             Minus(var, last_cti[var]),
                             Minus(last_cti[var], var)) for var in variables])

    double_distance_constraint = GE(new_distance, Int(int(distance)))
    return double_distance_constraint




def extract_new_template_by_splitting_guard(f, phi_f, index_of_guard, char_fun):
    """
    TODO
    :param current_temp:
    :param f:
    :param phi_f:
    :return:
    """

    # TODO: Could it suffice to only go through the loop_execute guards?
    guard_linexp_pairs = [f.guard_linexp_pairs[i] for i in range(len(f.guard_linexp_pairs)) if i != index_of_guard]

    (guard, linexp) = f.guard_linexp_pairs[index_of_guard]
    for (guard2, linexp2) in phi_f.guard_linexp_pairs:

        # The case linexp1 <= linexp2:
        conj = Guard.AND(guard, guard2)
        new_guard = Guard.AND(conj, Guard.SINGLETON(f.variables, LinearInequality.LEQ(linexp, linexp2)), False)
        if new_guard.is_sat():
            # new_guard = Expectation.prune_duplicates_in_guards(new_guard)
            # new_guard = Expectation.prune_valid_inequalities(vars_nat_valued, new_guard)
            new_guard.prune_unsat_disjuncts()
            guard_linexp_pairs.append((new_guard, linexp))

        # The case linexp1 > linexp2:
        new_guard = Guard.AND(conj, Guard.SINGLETON(f.variables, LinearInequality.GT(linexp, linexp2)), False)
        if new_guard.is_sat():
            # new_guard = Expectation.prune_duplicates_in_guards(new_guard)
            # new_guard = Expectation.prune_valid_inequalities(vars_nat_valued, new_guard)
            new_guard.prune_unsat_disjuncts()
            guard_linexp_pairs.append((new_guard, linexp2))


    #TODO. optimize. this can be faster
    new_guards_with_template = []
    new_guard_linexp_pairs = []
    for (guard, linexp) in guard_linexp_pairs:
        # if guard belongs to loop execute of the characteristic functional, it must be templated
        found = False
        for (guard2,_) in char_fun.execute_guard_prob_sub_pairs:
            new_guard = Guard.AND(guard, guard2)
            if new_guard.is_sat():
                new_guards_with_template.append(guard)
                found = True
                break
        if not found:
            new_guard_linexp_pairs.append((guard,linexp))


    new_template = ExpectationTemplate(char_fun.variables, new_guards_with_template, new_guard_linexp_pairs)
    #print("Checking whether new template is in gnf (this is expensive)")
    #new_template.check_gnf()
    #print(str(new_template))
    return new_template


