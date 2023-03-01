from pysmt.shortcuts import Times, Symbol, INT, Real, Plus, simplify, ToReal, EqualsOrIff,get_env, Minus
from cegispro2.solving.Solver import *
from fractions import Fraction

class LinearExpression:
    """
    Stores a dict from PySmt Variables x_1,...,x_n to their real coefficients plus an absolute real value.
    """

    def __init__(self, var_to_coeff, abs):
        self.var_to_coeff = var_to_coeff
        self.abs = abs

        self.pysmt_expression = Plus([Times(var_to_coeff[key], ToReal(key)) for key in var_to_coeff] + [abs])

    def add(self, lin_exp):
        """
        :param lin_exp: Add lin_exp to this linear expression
        :return: The linear expression obtained from adding this linear expression to lin_exp
        """

        new_var_to_coeff = dict()

        for key in lin_exp.var_to_coeff:
            new_var_to_coeff[key] = simplify(Plus(self.var_to_coeff[key], lin_exp.var_to_coeff[key]))

        new_abs = simplify(Plus(self.abs, lin_exp.abs))
        return LinearExpression(new_var_to_coeff, new_abs)

    # def subtract(self, lin_exp):
    #     """
    #     :param lin_exp: Add lin_exp to this linear expression
    #     :return: The linear expression obtained from adding this linear expression to lin_exp
    #     """
    #
    #     new_var_to_coeff = dict()
    #
    #     for key in lin_exp.var_to_coeff:
    #         new_var_to_coeff[key] = simplify(Minus(self.var_to_coeff[key], lin_exp.var_to_coeff[key]))

    #    new_abs = simplify(Minus(self.abs, lin_exp.abs))
    #    return LinearExpression(new_var_to_coeff, new_abs)

    def set_abs(self, val):
        self.abs = val
        self.pysmt_expression = Plus([Times(self.var_to_coeff[key], ToReal(key)) for key in self.var_to_coeff] + [self.abs])

    def multiply(self, real_constant):
        """
        :param real_constant:
        :return: The linear expression obtained from multiplying this linear expression by real_constant
        """

        new_var_to_coeff = self.var_to_coeff.copy()
        for key in new_var_to_coeff:
            new_var_to_coeff[key] = simplify(Times(real_constant, new_var_to_coeff[key]))

        new_abs = simplify(Times(real_constant, self.abs))

        return LinearExpression(new_var_to_coeff, new_abs)

    def substitute(self, var_to_linexp):
        """

        :param var_to_linexp: A dict from PySmt variables to LinearExpressions. If for some variable var no linear expression is given, the identity substition for that
        variable is applied.
        :return: The linear expression obtained from substituting every variable in keys of var_to_linexp by the corresponding linear expression
        """

        new_var_to_coeff = {key: Real(0) for key in self.var_to_coeff}
        new_abs = self.abs

        for key in self.var_to_coeff:
            cur_coefficient = self.var_to_coeff[key]
            # Take identitiy substitution of key by default
            key_is_substituted_by = var_to_linexp.get(key, LinearExpression({i:Real(1) if i==key else Real(0) for i in self.var_to_coeff}, Real(0)))

            # now go through the linear_expression key is substituted by and add it accordingly to the new linear expression
            for var in key_is_substituted_by.var_to_coeff:
                new_var_to_coeff[var] = simplify(Plus(new_var_to_coeff[var], Times(cur_coefficient, key_is_substituted_by.var_to_coeff[var])))

            new_abs = simplify(Plus(new_abs, Times(cur_coefficient, key_is_substituted_by.abs)))

        return LinearExpression(new_var_to_coeff, new_abs)


    def instantiate(self, template_variable_valuation):
        """

        :param template_variable_valuation:
        :return: Returns the linear expression obtained form substituting every template variable in some coefficient by the given value.
        """
        return LinearExpression({var : simplify(LinearExpression.fast_substitute(self.var_to_coeff[var], template_variable_valuation)) for var in self.var_to_coeff},
                                simplify(LinearExpression.fast_substitute(self.abs,template_variable_valuation)))


    def get_constantification(self, var_to_helpervariables):
        """
        Helper function for conditional difference boundedness. Substitutes every variable by it's helper variable, thereby
        turning this linear expression into a constant one.

        Careful: After de-constantification by back-substituting aux vars, var_to_coeff is no longer appropriate.
        :param var_to_helpervariables: A dict from the linear expression's variables to helper variables.
        :return:
        """

        new_abs = Plus([LinearExpression.fast_substitute(self.abs, var_to_helpervariables)] + [Times(self.var_to_coeff[var], ToReal(var_to_helpervariables[var])) for var in self.var_to_coeff])
        new_var_to_coeff = {var : Real(0) for var in self.var_to_coeff}
        return LinearExpression(new_var_to_coeff, new_abs)

    def equals(self, other):
        return EqualsOrIff(self.pysmt_expression, other.pysmt_expression)

    def equals_syntactically(self, linexp):
        return self.abs == linexp.abs and self.var_to_coeff == linexp.var_to_coeff

    @staticmethod
    def get_constant_expression(variables, constant):
        return LinearExpression({var:Real(0) for var in variables}, constant)


    def __str__(self):
        out = ""
        for key in self.var_to_coeff:
            if self.var_to_coeff[key] != Real(0):
                out += (str(simplify(self.var_to_coeff[key])) + "*" if not self.var_to_coeff[key] == Real(1) else "") + str(key) + " +"

        if self.abs != Real(0):
            out += str(simplify(self.abs))
        else:
            out = out[:-2]

        if out == "":
            out = "0"
        return out

    @staticmethod
    def fast_substitute(formula, sub):
        return get_env().substituter.walk(formula, substitutions=sub)

    def as_probably_string(self):
        """

        :return: A string representation of this linear expression which is parsable by probably
        """

        res = ""
        begin = True
        for var in self.var_to_coeff:
            coeff = Fraction(str(self.var_to_coeff[var]))
            if coeff != 0:
                if begin:
                    res = str(coeff) + "*" + str(var) if coeff >=0 else (" (0 - %s" % str(abs(coeff))) + "*" + str(var) + ")"
                    begin = False
                else:
                    res += " + " + (str(coeff) + "*" + str(var) if coeff >=0 else (" (0 - %s" % str(abs(coeff))) + "*" + str(var) + ")")


        coeff = Fraction(str(self.abs))
        if begin or coeff !=0:
            res += (" + " if not begin else "") + (str(coeff) if coeff >= 0 else (" (0 - %s)" % str(abs(coeff))))

        return res

    def all_coefficients_int(self):
        """

        :return: True iff all coefficients and the absolute values are integers
        """
        return is_pysmt_real_int(self.abs) and all(is_pysmt_real_int(self.var_to_coeff[var])for var in self.var_to_coeff)

    def is_constant_expression(self):
        """

        :return: True iff all coefficients except for the absolute part are equal to Real(0).
        """

        return all([self.var_to_coeff[var] == Real(0) for var in self.var_to_coeff])

def is_pysmt_real_int(pysmt_real):
    """

    :param pysmt_real: True iff pysmt_real represents an integer
    :return:
    """

    return Fraction(str(pysmt_real)).denominator == 1