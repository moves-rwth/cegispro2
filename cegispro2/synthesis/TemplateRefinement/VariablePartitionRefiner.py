from cegispro2.synthesis.TemplateRefinement.VariablePartitionTemplateRefiner import VariablePartitionTemplateRefiner
from pysmt.shortcuts import TRUE, And, GE, LT, Int, Implies, Real, Symbol, INT, ToReal
from cegispro2.synthesis.synthesis_utils import *
from cegispro2.expectations.Expectation import Expectation
import itertools

logger = logging.getLogger("cegispro2")

class VariablePartitionRefiner(VariablePartitionTemplateRefiner):
    """
    Variable-partition.
    """
    def __init__(self, variables, char_fun, property, options, statistics):
        super(VariablePartitionRefiner, self).__init__(variables,char_fun,property,options,statistics)

        # we keep as list of template variables (type:int) for every program variable
        self.progvar_to_tempvar ={var : [] for var in self.variables}
        self.refinement_level = 0
        self.partitionfactor = Int(options.partitionfactor)
        self.distance_constant = options.distance

    def get_initial_constraint_for_template(self, template):

        if self.options.use_motzkin:
            raise Exception("Motzkin for safety and non-negativity cannot be used for the variable partition refiner.")

        if self.refinement_level > 0:
            # ensure that, for every program variable, template variables will be non-negative and form a strict chain to ensure that instances are in gnf
            resulting_formulas = []
            for var in self.variables:
                resulting_formulas += [GE(temp_var, Int(0)) for temp_var in self.progvar_to_tempvar[var]] + [LT(self.progvar_to_tempvar[var][i], self.progvar_to_tempvar[var][i+1]) for i in range(len(self.progvar_to_tempvar[var]) -1)]
            self.template_var_constraint = resulting_formulas
            return resulting_formulas
        else:
            self.template_var_constraint = [TRUE()]
            return [TRUE()]


    def get_refined_template(self, old_template, ctis, last_cti, f, phi_f):

        self.refinement_level += 1
        # we add a new template variable for every program variable
        for var in self.variables:
            new_symbol = Symbol("BND_%s_%s" % (str(var), str(self.refinement_level)), INT)
            self.progvar_to_tempvar[var].append(new_symbol)
            self.guard_template_variables .append(new_symbol)


        var_to_guards = []
        for var in self.variables:
            cur_var_to_guards = []
            var_to_coeff = {varr: (Real(1) if varr == var else Real(0)) for varr in self.variables}
            for i in range(len(self.progvar_to_tempvar[var])):
                if i==0:
                    cur_var_to_guards .append(Guard.SINGLETON(self.variables, LinearInequality.LEQ(
                        LinearExpression(var_to_coeff, Real(0)),
                        LinearExpression.get_constant_expression(self.variables,
                                                                 ToReal(Times(self.partitionfactor, self.progvar_to_tempvar[var][i]))))))
                if i>0:
                    guard = Guard.SINGLETON(self.variables, LinearInequality.LT(
                        LinearExpression.get_constant_expression(
                            self.variables, ToReal(
                                Times(self.partitionfactor,self.progvar_to_tempvar[var][i - 1]))), LinearExpression(var_to_coeff, Real(0))))

                    cur_var_to_guards.append(Guard.AND(guard, Guard.SINGLETON(self.variables, LinearInequality.LEQ(
                        LinearExpression(var_to_coeff, Real(0)),
                        LinearExpression.get_constant_expression(
                            self.variables, ToReal(
                                Times(self.partitionfactor,self.progvar_to_tempvar[var][i])))))))

                if i == len(self.progvar_to_tempvar[var]) - 1:
                    cur_var_to_guards.append(Guard.SINGLETON(self.variables, LinearInequality.LT(LinearExpression.get_constant_expression(
                        self.variables, ToReal(
                            Times(self.partitionfactor,self.progvar_to_tempvar[var][i]))), LinearExpression(var_to_coeff, Real(0)))))

            var_to_guards.append(cur_var_to_guards)

        #update template variable constraints
        self.get_initial_constraint_for_template(None)

        guards_to_conjoin = []
        for combination in itertools.product(*var_to_guards):
            guard = Guard.TRUE(self.variables)
            for g in combination:
                guard = Guard.AND(guard, g)
            guards_to_conjoin.append(guard)



        guards_with_template = []
        for (guard, linexp) in self.options.initial_template.guard_templatelinexp_pairs:
            for guard2 in guards_to_conjoin:
                if is_sat(self.template_var_constraint + [guard.pysmt_expression, guard2.pysmt_expression]):
                    conj = Guard.AND(guard,guard2)
                    guards_with_template.append(conj)

        new_template = ExpectationTemplate(self.variables, guards_with_template, self.char_fun.terminate_guards_linexp_pairs)
        #logger.debug("New template:")
        #logger.info(new_template)
        return new_template