from pysmt.shortcuts import Real, simplify, Times, Minus, LE, LT, EqualsOrIff
from cegispro2.expressions.LinearExpression import LinearExpression
from cegispro2.solving.Solver import *
from fractions import Fraction

class LinearInequality:
    """
    Represents a (strict or non-strict) linear inequality of the form linear_expression <= rhs, where
    the absolute value of linear_expression is 0 by convention.
    """

    def __init__(self, linear_expression, rhs, is_strict: bool):

        self.linear_expression = linear_expression

        if self.linear_expression.abs != Real(0):
            raise Exception("The absolute value of the linear expression in a linear inequality must be 0.")

        self.rhs = rhs
        self.is_strict = is_strict

        self.pysmt_expression = LT(self.linear_expression.pysmt_expression, self.rhs) if self.is_strict\
                                else LE(self.linear_expression.pysmt_expression, self.rhs)

    def negate(self):
        """
        :return: Returns the linear inequality obtained from negating this inequality
        """

        # We negate a linear inequality by multiplying lhs and rhs by -1 and by flipping the sign

        new_linexp = self.linear_expression.multiply(Real(-1))
        new_rhs = simplify(Times(Real(-1), self.rhs))

        return LinearInequality(new_linexp, new_rhs, not self.is_strict)

    def substitute(self, var_to_linexp):
        """

        :param var_to_linexp: A dict from PySmt variables to LinearExpressions.
        :return: The linear inequality obtained from substituting every variable in keys of var_to_linexp by the corresponding linear expression):
        """

        new_linexp = self.linear_expression.substitute(var_to_linexp)
        new_rhs = simplify(Minus(self.rhs, new_linexp.abs))

        new_linexp.set_abs(Real(0))

        return LinearInequality(new_linexp, new_rhs, self.is_strict)


    def instantiate(self, template_variable_valuation):
        """

        :param template_variable_valuation:
        :return: Returns the linear inequality obtained form substituting every template variable in some coefficient by the given value.
        """
        #print("substituting %s by %s yields     %s" % (str(self.rhs), template_variable_valuation, str(simplify(LinearExpression.fast_substitute(self.rhs, template_variable_valuation)))))
        return LinearInequality(self.linear_expression.instantiate(template_variable_valuation), simplify(LinearExpression.fast_substitute(self.rhs, template_variable_valuation)), self.is_strict)

    @staticmethod
    def LEQ(linexp1, linexp2):
        """

        :param linexp1:
        :param linexp2:
        :return: returns the linear inequality representing linexp1 <= linexp2
        """

        new_linexp_dict = dict()
        new_abs = None

        for key in linexp1.var_to_coeff:
            new_linexp_dict[key] = simplify(Minus(linexp1.var_to_coeff[key], linexp2.var_to_coeff[key]))

        new_linexp = LinearExpression(new_linexp_dict, Real(0))
        new_rhs = simplify(Times(Real(-1), Minus(linexp1.abs, linexp2.abs)))

        return LinearInequality(new_linexp, new_rhs, False)


    def pysmt_expression_from_substituting_cti(self, cti):
        return self.pysmt_expression.substitute(cti)


    def get_constantification(self, var_to_helpervariables):
        """
        Helper function for conditional difference boundedness. Substitutes every variable by it's helper variable, thereby
        turning this linear inequality into a constant one.
        :param var_to_helpervariables: A dict from the linear expression's variables to helper variables.
        :return:
        """

        #This linear expression consits of an absolute part only. all other
        consted_linexp = self.linear_expression.get_constantification(var_to_helpervariables)
         # Now set new_rhs = self.rhs - consted_linexp.abs and new_linexp to zero
        new_rhs = Minus(self.rhs, consted_linexp.abs)
        new_linexp = LinearExpression.get_constant_expression([var for var in var_to_helpervariables], Real(0))
        return LinearInequality(new_linexp, new_rhs, self.is_strict)

    @staticmethod
    def LT(linexp1, linexp2):
        """

        :param linexp1:
        :param linexp2:
        :return: returns the linear inequality representing linexp1 < linexp2
        """
        new_linexp_dict = dict()

        for key in linexp1.var_to_coeff:
            new_linexp_dict[key] = simplify(Minus(linexp1.var_to_coeff[key], linexp2.var_to_coeff[key]))

        new_linexp = LinearExpression(new_linexp_dict, Real(0))
        new_rhs = simplify(Times(Real(-1), Minus(linexp1.abs, linexp2.abs)))

        return LinearInequality(new_linexp, new_rhs, True)

    @staticmethod
    def GT(linexp1, linexp2):
        """

        :param linexp1:
        :param linexp2:
        :return: returns the linear inequality representing linexp1 > linexp2
        """

        res = LinearInequality.LEQ(linexp1, linexp2)
        res = res.negate()
        return res

    @staticmethod
    def GEQ(linexp1, linexp2):
        """

        :param linexp1:
        :param linexp2:
        :return: returns the linear inequality representing linexp1 >= linexp2
        """

        res = LinearInequality.LT(linexp1, linexp2)
        res = res.negate()
        return res


    def __str__(self):
        return str(self.linear_expression) + (" < " if self.is_strict else " <= ") + str(simplify(self.rhs))

    def equals(self, other):
        return is_valid(self.linear_expression.equals(other.linear_expression) & EqualsOrIff(self.rhs, other.rhs))

    def equals_syntactically(self, ineq):
        if ineq.is_strict != self.is_strict:
            return False

        return self.rhs == ineq.rhs and self.linear_expression.equals_syntactically(ineq.linear_expression)

    def as_probably_string(self):
        """

        :return: A string representation of this linear expression which is parsable by probably
        """
        res = self.linear_expression.as_probably_string()
        res += " < " if self.is_strict else " <= "
        coeff = Fraction(str(self.rhs))
        res += (str(coeff) if coeff >= 0 else ("(0 - %s)" % str(abs(coeff))))
        return res


    def to_nonstrict_inequality_if_possible_and_has_effect(self):
        """

        :return: An equivalent non-strict inequality if all coefficients of the linear inequality on the left-hand side and the rhs are integers,
        """

        if (not self.is_strict) or (not self.rhs.is_real_constant()) or (not self.linear_expression.all_coefficients_int()) or(not is_pysmt_real_int(self.rhs)):
            return self
        else:
            # if the rhs is an integer, we subtract 1 and turn the strict into a non-strict inequality
            return LinearInequality(self.linear_expression, simplify(Minus(self.rhs, Real(1))), False)

def is_pysmt_real_int(pysmt_real):
    """

    :param pysmt_real: True iff pysmt_real represents an integer
    :return:
    """

    return Fraction(str(pysmt_real)).denominator == 1






