from pysmt.shortcuts import Solver, Not, get_env, And, to_smtlib, Equals, Min, Int, Or, Max
from pysmt.logics import QF_UFLIRA
from pysmt.logics import QF_LRA
from pysmt.solvers.z3 import Z3Model
import z3
import logging

logger = logging.getLogger("cegispro2")
#solver = Solver("z3", QF_UFLIRA)
solver = Solver("z3", QF_UFLIRA)

z3_optimizer = z3.Optimize()

pysmt_to_z3_variables = dict()

def get_model(formulas):

    #return z3_check_sat_minimizing_var(formulas, "diff")

    if solver.solve(formulas):
        model = solver.get_model()
        #solver.reset_assertions()
        return model
    else:
        #solver.reset_assertions()
        return None


def is_sat(formulas):
    return solver.solve(formulas)
    # solver.add_assertion(formula)
    #
    # if solver.solve():
    #     solver.reset_assertions()
    #     return True
    # else:
    #     solver.reset_assertions()
    #     return False


def is_valid(formula):
    solver.add_assertion(Not(formula))

    if not solver.solve():
        solver.reset_assertions()
        return True
    else:
        solver.reset_assertions()
        return False


def z3_check_sat_minimizing_var(formulas, variable_to_minimize):
    """

    :param formulas:
    :param variable_to_maximize:
    :return: A model satifying formulas maximizing variable_to_maximize if formulas are satisfiable, None otherwise
    """

    lib = get_smtlib_string(And(formulas))
    lib += " (minimize %s)" % str(variable_to_minimize)

    return z3_execute_query_and_get_result(lib)


def z3_check_sat_maximizing_var(formulas, variable_to_maximize):
    """

    :param formulas:
    :param variable_to_maximize:
    :return: A model satifying formulas maximizing variable_to_maximize if formulas are satisfiable, None otherwise
    """

    lib = get_smtlib_string(And(formulas))
    lib += " (maximize %s)" % str(variable_to_maximize)

    return z3_execute_query_and_get_result(lib)


def z3_check_sat_minimizing_var_check_formulae_separately(formulas, variable_to_minimize):
    """
    Huge queries to the optimization solver can be slow. Exploit that expectations are in DNF and split into multiple queries.

    :param formulas:
    :param variable_to_maximize:
    :return: A model minimizing variable_to_maximize under all models of each formula in formulas, none if none of the formulae is satisfiable.
    """
    #print("Num formulae: %s" % len(formulas))

    models = [z3_check_sat_minimizing_var([formula], variable_to_minimize) for formula in formulas]

    #missuse as index var:
    ind = get_env().formula_manager.get_symbol("index_exp1")
    #missuse as variable keeping track of the minimum
    diff = get_env().formula_manager.get_symbol("diff")

    # Filter models:
    models = [model for model in models if model is not None]
    #print("Davon sat: %s" % len(models))
    if len(models) == 0:
        return None

    min_formula = Equals(diff, Min([model[variable_to_minimize] for model in models]))
    index_formula = Or([And([Equals(diff, models[i][variable_to_minimize]), Equals(ind, Int(i))]) for i in range(len(models))])

    index_model = get_model([min_formula, index_formula])

    if index_model == None:
        raise Exception("index model was unsat.")
    else:
        return models[int(str(index_model[ind]))]

def z3_check_sat_maximizing_var_check_formulae_separately(formulas, variable_to_maximize):
    """
    Huge queries to the optimization solver can be slow. Exploit that expectations are in DNF and split into multiple queries.

    :param formulas:
    :param variable_to_maximize:
    :return: A model minimizing variable_to_maximize under all models of each formula in formulas, none if none of the formulae is satisfiable.
    """
    #print("Num formulae: %s" % len(formulas))

    models = [z3_check_sat_maximizing_var([formula], variable_to_maximize) for formula in formulas]

    #missuse as index var:
    ind = get_env().formula_manager.get_symbol("index_exp1")
    #missuse as variable keeping track of the minimum
    diff = get_env().formula_manager.get_symbol("diff")

    # Filter models:
    models = [model for model in models if model is not None]
    #print("Davon sat: %s" % len(models))
    if len(models) == 0:
        return None

    max_formula = Equals(diff, Max([model[variable_to_maximize] for model in models]))
    index_formula = Or([And([Equals(diff, models[i][variable_to_maximize]), Equals(ind, Int(i))]) for i in range(len(models))])

    index_model = get_model([max_formula, index_formula])

    if index_model == None:
        raise Exception("index model was unsat.")
    else:
        return models[int(str(index_model[ind]))]


def z3_execute_query_and_get_result(smtlib_string):
    """

    :param smtlib_string:
    :return:
    """

    #z3_optimizer.reset()

    z3_optimizer.push()
    z3_optimizer.from_string(smtlib_string)
    res = z3_optimizer.check()

    if res == z3.sat:
        model = Z3Model(get_env(), z3_optimizer.model())
        z3_optimizer.pop()
        return model
    elif res == z3.unsat:
        z3_optimizer.pop()
        return None
    else:
        raise Exception("optimization solver returned unkown")



def get_smtlib_string(formula):

    #res = "(set-logic QF_UFLIRA) "
    res = "" # TODO: set logid?
    # produce variable declarations
    for symb in get_env().formula_manager.get_all_symbols():
        if symb.get_type().is_real_type():
            res += "(declare-const %s %s) " % (symb, "Real")

        elif symb.get_type().is_int_type():
            res += "(declare-const %s %s) " % (symb, "Int")

        else:
            raise Exception("unhandled type : %s" % symb.get_type())

    return res + (" (assert " + to_smtlib(formula) + ")")



