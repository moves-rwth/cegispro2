import logging
from cegispro2.solving.Solver import *
from probably.pgcl.parser import parse_pgcl, parse_expectation
from pysmt.shortcuts import Symbol, INT, get_env, Real, And, GE, Int, Times, TRUE
from probably.pgcl.wp import LoopExpectationTransformer, one_loop_wp_transformer
from probably.pgcl.simplify import SnfExpectationTransformer, normalize_expectation_transformer, normalize_expectation, SnfExpectationTransformerProduct
from probably.pgcl.ast import *
from probably.pgcl.syntax import check_is_linear_program
from probably.pgcl.check import CheckFail
from typing import List, Tuple, Union, Dict
from cegispro2.utils.Options import Options
from cegispro2.inequalities.LinearInequality import LinearInequality
from cegispro2.expressions.LinearExpression import LinearExpression
from cegispro2.expectations.Guard import Guard
from cegispro2.expectations.CharacteristicFunctional import CharacteristicFunctional
from cegispro2.expectations.ErtCharacteristicFunctional import ErtCharacteristicFunctional
from cegispro2.synthesis.Property import Property
from itertools import product
#import parser
logger = logging.getLogger("cegispro2")

last_program = None
modC = set()

def parse_program_and_postexp_into_charfun(options):

    logger.debug("Parsing program: \n %s" % options.program_code)
    logger.debug("\n with postexpectation: \n %s" % options.post)

    program = parse_pgcl(options.program_code)
    global last_program
    last_program = program
    if not check_is_linear_program(program) == None:
        raise Exception("Program must be linear.")

    (variables, variables_to_bounds) = get_variables(program)

    probably_wp_transformer = one_loop_wp_transformer(program, program.instructions)
    probably_summation_nf = SnfLoopExpectationTransformer(program, probably_wp_transformer)

    execute_guard_prob_sub_pairs = get_execute_guard_prob_sub_pairs(variables, probably_wp_transformer, probably_summation_nf)
    terminate_guard_linexp_pairs = get_terminate_guard_linexp_pairs(variables, program, probably_summation_nf, options.post)

    if not options.past:
        char_fun = CharacteristicFunctional(variables, variables_to_bounds, execute_guard_prob_sub_pairs, terminate_guard_linexp_pairs)
    else:
        char_fun = ErtCharacteristicFunctional(variables, variables_to_bounds, execute_guard_prob_sub_pairs,
                                            terminate_guard_linexp_pairs)

    return char_fun

def get_terminate_guard_linexp_pairs(variables, program, probably_summation_nf, postexpectation):

    negated_loop_guard = probably_guard_to_cegispro_guard(variables, probably_summation_nf.done)
    probably_postexpectation = parse_expectation(postexpectation)
    flattened_postexpectation = normalize_expectation_simple(program, probably_postexpectation)

    if type(flattened_postexpectation) == CheckFail:
        raise Exception("CheckFail.")

    postexpectation_guard_linexp_pairs = [(probably_guard_to_cegispro_guard(variables, probably_guard).conjoin(negated_loop_guard),
                                           probably_linear_expression_to_cegispro_linear_expression(variables, probably_linexp)) for probably_guard, probably_linexp in flattened_postexpectation]

    # Probably somehow treats [phi]*(x+y) as [phi]*x + [phi]*y, so we have to merge these kinds of summands
    postexpectation_guard_linexp_pairs = merge_pairs_with_equal_guards(postexpectation_guard_linexp_pairs)
    return postexpectation_guard_linexp_pairs

def merge_pairs_with_equal_guards(guard_linexp_pairs):
    # Probably somehow treats [phi]*(x+y) as [phi]*x + [phi]*y, so we have to merge these kinds of summands
    # new_pairs = []
    # while len(guard_linexp_pairs) > 0:
    #     (guard1, linexp1) = guard_linexp_pairs[0]
    #     del guard_linexp_pairs[0]
    #     for i in range(0, len(guard_linexp_pairs)):
    #         (guard2, linexp2) = guard_linexp_pairs[i]
    #         if guard1.equals(guard2):
    #             (guard1, linexp1) = (guard1, linexp1.add(linexp2))
    #             del guard_linexp_pairs[i]
    #             break
    #     new_pairs.append((guard1, linexp1))
    #
    # return new_pairs


    while True:
        merged = False

        for i in range(0,len(guard_linexp_pairs)):
            (g1, l1) =  guard_linexp_pairs.pop(i)
            for j in range(i,len(guard_linexp_pairs)):
                (g2, l2) = guard_linexp_pairs.pop(j)
                if g1.equals(g2):
                    pair = (g1, l1.add(l2))
                    guard_linexp_pairs.append(pair)
                    merged = True
                    break
                guard_linexp_pairs.insert(j, (g2,l2))
            if merged:
                break
            guard_linexp_pairs.insert(i, (g1, l1))
        if not merged:
            break

    return guard_linexp_pairs


def get_variables(program):
    variables = []
    variables_to_bounds = dict()

    for name,type in program.variables.items():
        bounds = type.bounds
        if type != NatType(bounds=bounds):
            raise Exception("Every variable must be of type nat.")
        else:
            var = Symbol(name, INT)
            variables.append(var)

            if bounds is not None:
                lower = bounds.lower
                upper = bounds.upper
                if not isinstance(lower.value, int) or not isinstance(upper.value, int) or not lower.value >=0 or not upper.value >=0:
                    raise Exception("Bounds of nat-typed variables must be non-negative integers.")

                variables_to_bounds[var] = (lower.value, upper.value)

    logger.debug("Variables: %s" % variables)
    return (variables, variables_to_bounds)


# def get_execute_guard_prob_sub_pairs_old(variables, probably_wp_transformer, probably_summation_nf, fastparse):
#     env = get_env()
#
#     probably_guards, probably_probs, probably_subs, probably_ticks = zip(*probably_summation_nf.body_tuples())
#
#     #for i in range(len(probably_guards)):
#     #    print("%s    %s    %s " % (probably_guards[i], probably_probs[i], probably_subs[i]))
#
#     logger.debug("Parsing guard_probsubpairs. Ignoring ticks for the moment.")
#
#     # Probably guards -> lists of linear inequalities
#     cegispro_guards = [probably_guard_to_cegispro_guard(variables, probably_guard) for probably_guard in probably_guards]
#
#     #aggregate equals guards and create (guard, [prob_sub_pairs)] list.
#     guard_prob_sub_pairs = []
#     cegispro_guards_copy = cegispro_guards.copy()
#     while len(cegispro_guards) >0:
#         cur_guard = cegispro_guards[0]
#         cur_prob_sub_list = []
#
#         for i in range(len(cegispro_guards_copy)):
#             guard = cegispro_guards_copy[i]
#             # look for guards equal to cur_guard
#             if cur_guard.equals_syntactically(guard):
#                 #cur_guard is equal to guard
#                 probably_prob = probably_probs[i]
#                 probably_sub = probably_subs[i]
#                 prob = Real(probably_probability_to_fraction(probably_prob))
#                 sub = {}
#                 for var, key in probably_sub.items():
#                     sub[env.formula_manager.get_symbol(var)] = probably_linear_expression_to_cegispro_linear_expression(variables, key)
#
#                 cur_prob_sub_list.append((prob, sub))
#                 cegispro_guards.remove(guard)
#         guard_prob_sub_pairs.append((cur_guard, cur_prob_sub_list))
#
#     if not fastparse:
#         #bring into gnf
#         vars_nat_valued = And([GE(var, Int(0)) for var in variables])
#
#         new_guard_prob_sub_pairs = []
#         logger.debug("Checking %s prob-sub combinations .." % 2**len(guard_prob_sub_pairs))
#         for bin_seq in product([True, False], repeat=len(guard_prob_sub_pairs)):
#             cur_guard = Guard.TRUE(variables)
#             negated_guard = Guard.TRUE(variables)
#             cur_prob_sub_pairs = []
#
#             for i in range(len(guard_prob_sub_pairs)):
#                 if bin_seq[i]:
#                     cur_guard = Guard.AND(cur_guard, guard_prob_sub_pairs[i][0])
#                     cur_prob_sub_pairs = cur_prob_sub_pairs + guard_prob_sub_pairs[i][1]
#                 else:
#                     negated_guard = Guard.AND(negated_guard, Guard.NEG(guard_prob_sub_pairs[i][0]))
#
#             if is_sat([vars_nat_valued, cur_guard.pysmt_expression, negated_guard.pysmt_expression]) and len(cur_prob_sub_pairs) >0:
#                 new_guard_prob_sub_pairs.append((cur_guard.prune_duplicate_disjuncts().prune_duplicate_conjuncts(), cur_prob_sub_pairs))
#         logger.debug(".. done")
#
#     else:
#         new_guard_prob_sub_pairs = guard_prob_sub_pairs
#
#     return new_guard_prob_sub_pairs





def get_execute_guard_prob_sub_pairs(variables, probably_wp_transformer, probably_summation_nf):
    env = get_env()

    probably_guards, probably_probs, probably_subs, probably_ticks = zip(*probably_summation_nf.body_tuples())

    #for i in range(len(probably_guards)):
    #    print("%s    %s    %s " % (probably_guards[i], probably_probs[i], probably_subs[i]))

    logger.debug("Parsing guard_probsubpairs. Ignoring ticks for the moment.")

    # Probably guards -> lists of linear inequalities
    cegispro_guards = [probably_guard_to_cegispro_guard(variables, probably_guard) for probably_guard in probably_guards]

    #aggregate equals guards and create (guard, [prob_sub_pairs)] list.
    guard_prob_sub_pairs = []
    cegispro_guards_copy = cegispro_guards.copy()
    while len(cegispro_guards) >0:
        cur_guard = cegispro_guards[0]
        cur_prob_sub_list = []

        for i in range(len(cegispro_guards_copy)):
            guard = cegispro_guards_copy[i]
            # look for guards equal to cur_guard
            if cur_guard.equals_syntactically(guard):
                #cur_guard is equal to guard
                probably_prob = probably_probs[i]
                probably_sub = probably_subs[i]
                prob = Real(probably_probability_to_fraction(probably_prob))
                sub = {}
                for var, key in probably_sub.items():
                    sub[env.formula_manager.get_symbol(var)] = probably_linear_expression_to_cegispro_linear_expression(variables, key)
                cur_prob_sub_list.append((prob, sub))
                cegispro_guards.remove(guard)
        guard_prob_sub_pairs.append((cur_guard, cur_prob_sub_list))


    #bring into gnf
    vars_nat_valued = [GE(var, Int(0)) for var in variables]
    #
    # new_guard_prob_sub_pairs = []
    # logger.debug("Checking %s prob-sub combinations .." % 2**len(guard_prob_sub_pairs))
    # for bin_seq in product([True, False], repeat=len(guard_prob_sub_pairs)):
    #     cur_guard = Guard.TRUE(variables)
    #     negated_guard = Guard.TRUE(variables)
    #     cur_prob_sub_pairs = []
    #
    #     for i in range(len(guard_prob_sub_pairs)):
    #         if bin_seq[i]:
    #             cur_guard = Guard.AND(cur_guard, guard_prob_sub_pairs[i][0])
    #             cur_prob_sub_pairs = cur_prob_sub_pairs + guard_prob_sub_pairs[i][1]
    #         else:
    #             negated_guard = Guard.AND(negated_guard, Guard.NEG(guard_prob_sub_pairs[i][0]))
    #
    #     if is_sat([vars_nat_valued, cur_guard.pysmt_expression, negated_guard.pysmt_expression]) and len(cur_prob_sub_pairs) >0:
    #         new_guard_prob_sub_pairs.append((cur_guard.prune_duplicate_disjuncts().prune_duplicate_conjuncts(), cur_prob_sub_pairs))
    # logger.debug(".. done")

    #for (guard, prob) in guard_prob_sub_pairs:
    #    print(" %s %s " % (str(guard), prob))

    logger.debug("The modified variables are: %s" % str(modC))
    res = get_guard_prob_sub_gnf(guard_prob_sub_pairs, 0, [TRUE()], [], [], vars_nat_valued, variables)
    return res


def get_guard_prob_sub_gnf(guard_prob_sub_pairs, current_index, current_formula, current_guardindex_truthvalue_list, current_prob_sub_pairs, vars_nat_valued, variables):
    if current_index == len(guard_prob_sub_pairs):
        if len(current_prob_sub_pairs) > 0:
            guard = Guard.TRUE(variables)
            for i in range(len(guard_prob_sub_pairs)):
                if current_guardindex_truthvalue_list[i] == 1:
                    guard = Guard.AND(guard, guard_prob_sub_pairs[i][0])# if current_guardindex_truthvalue_list[i] == 1 else Guard.AND(guard, Guard.NEG(guard_prob_sub_pairs[i][0]))
            return [(guard.prune_duplicate_disjuncts().prune_duplicate_conjuncts(), current_prob_sub_pairs)]
        else:
            return []

    new_formula_true = current_formula + [guard_prob_sub_pairs[current_index][0].pysmt_expression]
    new_formula_false = current_formula + [Not(guard_prob_sub_pairs[current_index][0].pysmt_expression)]

    res = []
    if is_sat(vars_nat_valued + new_formula_true):
        res = res + get_guard_prob_sub_gnf(guard_prob_sub_pairs, current_index + 1, new_formula_true, current_guardindex_truthvalue_list + [1],
                                           current_prob_sub_pairs + guard_prob_sub_pairs[current_index][1], vars_nat_valued, variables)

    if is_sat(vars_nat_valued + new_formula_false):
        res = res + get_guard_prob_sub_gnf(guard_prob_sub_pairs, current_index + 1, new_formula_false, current_guardindex_truthvalue_list + [0],
                                           current_prob_sub_pairs, vars_nat_valued, variables)
    return res

def parse_probably_property_into_cegispro_property(property):

    logger.debug("Parsing upper bound ...")

    if property == "":
        return Property([])

    probably_postexpectation = parse_expectation(property)
    flattened_postexpectation = normalize_expectation_simple(last_program, probably_postexpectation)

    (variables, variables_to_bounds) = get_variables(last_program)

    property_guard_linexp_pairs = [
        (probably_guard_to_cegispro_guard(variables, probably_guard),
         probably_linear_expression_to_cegispro_linear_expression(variables, probably_linexp)) for
        probably_guard, probably_linexp in flattened_postexpectation]

    #for p in property_guard_linexp_pairs:
    #    print("%s   %s" % (str(p[0]), str(p[1])))

    property_guard_linexp_pairs = merge_pairs_with_equal_guards(property_guard_linexp_pairs)

    #print("\n\n")
    #for p in property_guard_linexp_pairs:
    #    print("%s   %s" % (str(p[0]), str(p[1])))


    prop = Property(property_guard_linexp_pairs)
    logger.debug(prop)

    return prop


def comma_separated_string_of_probably_guards_to_list_of_cegispro_guards(variables, string : str):
    strings = string.split(",")
    return [probably_guard_to_cegispro_guard(variables, parse_expectation(s)) for s in strings]



def probably_probability_to_fraction(prob):
    if isinstance(prob, BinopExpr):
        if prob.operator == Binop.TIMES:
            return probably_probability_to_fraction(prob.lhs) * probably_probability_to_fraction(prob.rhs)
        elif prob.operator == Binop.MINUS:
            return probably_probability_to_fraction(prob.lhs) - probably_probability_to_fraction(prob.rhs)
        else:
            raise Exception("Invalid probability: %s" % prob)
    elif isinstance(prob, FloatLitExpr):
        return prob.to_fraction()
    else:
        raise Exception("Invalid probability: %s" % prob)

def probably_guard_to_cegispro_guard(variables, probably_guard):
    """
    Takes a probably Boolean expression and returns a list of list of linearinequalities which is to be interpreted
    as the DNF representation of probably_guard
    :param variables:
    :param probably_guard:
    :param negate:
    :return:
    """

    if isinstance(probably_guard, BinopExpr):
        if probably_guard.operator == Binop.AND:
            return Guard.AND(probably_guard_to_cegispro_guard(variables, probably_guard.lhs),
                             probably_guard_to_cegispro_guard(variables, probably_guard.rhs))

        if probably_guard.operator == Binop.OR:
            return Guard.OR(probably_guard_to_cegispro_guard(variables, probably_guard.lhs),
                             probably_guard_to_cegispro_guard(variables, probably_guard.rhs))

        if probably_guard.operator == Binop.LEQ:
            return Guard.SINGLETON(variables, LinearInequality.LEQ(probably_linear_expression_to_cegispro_linear_expression(variables, probably_guard.lhs),
                                                                   probably_linear_expression_to_cegispro_linear_expression(variables, probably_guard.rhs)))

        if probably_guard.operator == Binop.EQ:
            return Guard.AND(Guard.SINGLETON(variables, LinearInequality.LEQ(probably_linear_expression_to_cegispro_linear_expression(variables, probably_guard.lhs),
                                                                   probably_linear_expression_to_cegispro_linear_expression(variables, probably_guard.rhs))),
                             Guard.SINGLETON(variables, LinearInequality.GEQ(
                                 probably_linear_expression_to_cegispro_linear_expression(variables,
                                                                                          probably_guard.lhs),
                                 probably_linear_expression_to_cegispro_linear_expression(variables,
                                                                                          probably_guard.rhs))))

        if probably_guard.operator == Binop.LE:
            return Guard.SINGLETON(variables, LinearInequality.LT(
                probably_linear_expression_to_cegispro_linear_expression(variables, probably_guard.lhs),
                probably_linear_expression_to_cegispro_linear_expression(variables, probably_guard.rhs)))

        else:
            raise Exception("We allow linear inequalities involvong <= and < only. > and >= is TODO in probably. %s" % probably_guard)

    elif isinstance(probably_guard, UnopExpr) and probably_guard.operator == Unop.NEG:
        return Guard.NEG(probably_guard_to_cegispro_guard(variables, probably_guard.expr))

    elif isinstance(probably_guard, UnopExpr) and probably_guard.operator == Unop.IVERSON:
        return probably_guard_to_cegispro_guard(variables, probably_guard.expr)

    elif isinstance(probably_guard, BoolLitExpr):
        if probably_guard.value == True:
            return Guard.TRUE(variables)
        elif probably_guard.value == False:
            return Guard.FALSE(variables)
        else:
            raise Exception("Unkown expression value.")
    else:
        print(probably_guard)
        raise Exception("Unexpected expression: %s" % probably_guard)


def probably_linear_expression_to_cegispro_linear_expression(variables, probably_linear_expression):
    env = get_env()

    if isinstance(probably_linear_expression, BinopExpr):

        if probably_linear_expression.operator == Binop.PLUS:
            return probably_linear_expression_to_cegispro_linear_expression(variables,
                                                                            probably_linear_expression.lhs).add(
                probably_linear_expression_to_cegispro_linear_expression(variables,
                                                                         probably_linear_expression.rhs))

        elif probably_linear_expression.operator == Binop.MINUS:
            return probably_linear_expression_to_cegispro_linear_expression(variables, probably_linear_expression.lhs).add(probably_linear_expression_to_cegispro_linear_expression(variables, probably_linear_expression.rhs).multiply(Real(-1)))

        elif probably_linear_expression.operator == Binop.TIMES:

            lhs = probably_linear_expression_to_cegispro_linear_expression(variables, probably_linear_expression.lhs)
            rhs = probably_linear_expression_to_cegispro_linear_expression(variables, probably_linear_expression.rhs)

            if not (lhs.is_constant_expression() or rhs.is_constant_expression()):
                raise Exception("For multiplications, at least one of the expressions must be constant: %s" % probably_linear_expression)
            else:
                if lhs.is_constant_expression():
                    return LinearExpression({var: Times(rhs.var_to_coeff[var], lhs.abs)  for var in rhs.var_to_coeff}, Times(rhs.abs, lhs.abs))
                else:
                    return LinearExpression({var: Times(lhs.var_to_coeff[var], rhs.abs) for var in lhs.var_to_coeff},
                                            Times(rhs.abs, lhs.abs))


            #if not((isinstance(probably_linear_expression.lhs, NatLitExpr) or isinstance(probably_linear_expression.lhs,FloatLitExpr)) and isinstance(probably_linear_expression.rhs, VarExpr)):
            #    raise Exception("Only products of the form constant*var are allowed: %s" % probably_linear_expression)
            #else:
            #    return LinearExpression({var: (Real(probably_linear_expression.lhs.to_fraction() if isinstance(probably_linear_expression.lhs, FloatLitExpr) #FloatLit
            #                                        else probably_linear_expression.lhs.value)) #NatLit
            #                             if var == env.formula_manager.get_symbol(probably_linear_expression.rhs.var) else Real(0) for var in variables}, Real(0))

        else:
            raise Exception("Unexpected expression. %s" % probably_linear_expression)

    elif isinstance(probably_linear_expression, NatLitExpr):
        return LinearExpression.get_constant_expression(variables, Real(probably_linear_expression.value))

    elif isinstance(probably_linear_expression, FloatLitExpr):
        return LinearExpression.get_constant_expression(variables, Real(probably_linear_expression.to_fraction()))

    elif isinstance(probably_linear_expression, VarExpr):
        modC.add(env.formula_manager.get_symbol(probably_linear_expression.var))
        return LinearExpression({var: (Real(1) #NatLit
                                         if var == env.formula_manager.get_symbol(probably_linear_expression.var) else Real(0)) for var in variables}, Real(0))

    else:
        raise Exception("Unexpected expression.: %s" % probably_linear_expression)





class SnfLoopExpectationTransformer:
    """Wrap probably's loop expectation transformer with a normalized expectation in the body."""

    body: SnfExpectationTransformer = attr.ib()
    done: Expr = attr.ib()

    def __init__(self, program: Program,
                 transformer: LoopExpectationTransformer):
        assert len(
            transformer.init) == 0, "initial assignments are not allowed"
        self.body = normalize_expectation_transformer(program,
                                                      transformer.body)
        self.done = transformer.done

    def body_tuples(
            self) -> List[Tuple[Expr, Expr, Dict[Var, Expr], TickExpr]]:
        return [(value.guard, value.prob, value.subst, value.ticks)
                for value in self.body]

    def __str__(self) -> str:
        return f"lam 𝐹. lfp 𝑋. {self.body} + {self.done} * 𝐹"


@attr.s
class SimpleNormalizedExpectation:

    _pairs: List[Tuple[Expr, Expr]] = attr.ib()

    def __repr__(self) -> str:
        return repr(self._pairs)

    def __str__(self) -> str:
        pairs = (f'[{guard}] * {expr_str_parens(prob)}'
                 for guard, prob in self._pairs)
        return f'{" + ".join(pairs)}'

    def __iter__(self):
        return iter(self._pairs)

    def __getitem__(self, index):
        return self._pairs[index]


def normalize_expectation_simple(
        program: Program,
        expr: Expr) -> Union[SimpleNormalizedExpectation, CheckFail]:
    """
    Returns the normalized expectation consisting of a guard and a probability expression.
    It is assumed no tick expressions occur in ``expr``.
    """
    normalized = normalize_expectation(program, expr)
    if isinstance(normalized, CheckFail):
        return normalized

    def unwrap_value(
            value: SnfExpectationTransformerProduct) -> Tuple[Expr, Expr]:
        assert value.subst is None
        assert value.ticks.is_zero()
        return (value.guard, value.prob)

    return SimpleNormalizedExpectation(list(map(unwrap_value, normalized)))
