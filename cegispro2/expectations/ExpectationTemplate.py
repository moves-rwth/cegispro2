from cegispro2.expectations.Expectation import Expectation
from cegispro2.expressions.LinearExpression import LinearExpression
from cegispro2.inequalities.LinearInequality import LinearInequality
from pysmt.shortcuts import REAL, Symbol, Real, INT, FreshSymbol

#from cegispro2.expectations.CharacteristicFunctional import CharacteristicFunctional

class ExpectationTemplate(Expectation):
    """
    An ExpectationTemplate is an Expectation where (some of) the coefficients occurring in the linear expressions (outside the guards)
    are real-valued parameters.
    """

    # For distinguished variable names
    varname_counter = 0

    def __init__(self, variables, guards_with_template, guard_linexp_pairs):

        self.guard_templatelinexp_pairs = []
        self.template_variables = []
        for guard in guards_with_template:
            lin_exp = LinearExpression({var : self.add_variable(str(var) + "_" + str(ExpectationTemplate.varname_counter)) for var in variables}, self.add_variable("abs_" + str(ExpectationTemplate.varname_counter)))
            self.guard_templatelinexp_pairs.append((guard, lin_exp))

            ExpectationTemplate.varname_counter += 1

        super().__init__(variables, self.guard_templatelinexp_pairs + guard_linexp_pairs)


    def add_variable(self, name):
        """
        Creates a new real-valued template variable
        :param name: The name of the new variable.
        :return:
        """
        symbol = Symbol(name, REAL)
        self.template_variables.append(symbol)
        return symbol


    def get_parameter_valuation_from_sovler_model(self, model, additional_template_variables = []):
        return {var: model[var] for var in self.template_variables + additional_template_variables}

    def template_guards_as_comma_separated_pysmt_string(self):
        """

        :return: The guards from the guard_templatelinexp_pairs as a comma separated pysmt string
        """
        begin = True
        res = ""
        for (guard, _) in self.guard_templatelinexp_pairs:
            if begin:
                begin = False
                res = guard.as_probably_string()
            else:
                res += "," + guard.as_probably_string()

        return res