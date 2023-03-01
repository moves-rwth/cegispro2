from cegispro2.synthesis.TemplateRefinement.FixedPartitionTemplateRefiner import FixedPartitionTemplateRefiner
from pysmt.shortcuts import TRUE, And, GE, LT, Int, Implies, Real, Symbol, INT, ToReal
from cegispro2.synthesis.synthesis_utils import *
from cegispro2.expectations.Expectation import Expectation
import itertools

logger = logging.getLogger("cegispro2")

class HyperplanePartitionRefiner(FixedPartitionTemplateRefiner):
    """
    Fixed-partition.
    """
    def __init__(self, variables, char_fun, property, options, statistics):
        super(HyperplanePartitionRefiner, self).__init__(variables,char_fun,property,options,statistics)

        # we keep as list of template variables (type:int) for every program variable
        self.partitionfactor = Int(options.partitionfactor)
        self.distance_constant = options.distance

        # maintain current template (with templated guards) and phi(template)
        self.current_template = self.get_initial_template()
        self.phi_current_template = self.char_fun.apply_expectation(self.current_template)

        self.refinement_level = 0
        # we have to keep track of template variabls occurring in the guards
        self.guard_template_variables = []


    def get_initial_constraint_for_template(self, template):

        if self.options.use_motzkin:
            raise Exception(
                    "Motzkin for safety and non-negativity cannot be used for the variable partition refiner.")

        return [TRUE()]



    def get_refined_template(self, old_template, ctis, last_cti, f, phi_f):

        #append last cti to the CEGIS list of ctis
        # TODO: Test whether the cegis loop sees this

        #TODO: this cti needs to be appended
        ctis.append(last_cti)

        logger.debug("OLD meta-template:")
        logger.debug(str(self.current_template))
        logger.debug("OLD applied charfun:")
        logger.debug(str(self.phi_current_template))
        logger.debug("\n\n")

        instance = self.instance_for_current_template(ctis)

        while instance == None:
            # we need to refine further
            self.refinement_level += 1

            new_templated_guards = []

            #split every templated guard in self.current_template into two new guards by means of a new linear inequality
            for i in range(len(self.current_template.guard_templatelinexp_pairs)):
                guard = self.current_template.guard_templatelinexp_pairs[i][0]

                # for the new inequality, we need one coefficient for every variable and one for the absolute part
                # the name of each variable will be coeff_varname_refinement_level_guard_index
                var_to_coeff = {}

                for var in self.variables:
                    symb = Symbol("COEFF_%s_%s_%s" % (str(var), str(self.refinement_level), str(i)), REAL)
                    var_to_coeff[var] = symb
                    self.guard_template_variables.append(symb)

                abs = Symbol("COEFF_abs_%s_%s" % (str(self.refinement_level), str(i)), REAL)
                self.guard_template_variables.append(abs)

                linexp = LinearExpression(var_to_coeff, abs)

                # linexp <= 0
                lineq_leq0 = LinearInequality.LEQ(linexp, LinearExpression.get_constant_expression(self.variables, Real(0)))
                #linexp > 0
                lineq_gt0 = lineq_leq0.negate()

                guard_to_conjoin1 = Guard(self.variables, [[lineq_leq0]])
                guard_to_conjoin2 = Guard(self.variables, [[lineq_gt0]])

                new_templated_guards.append(Guard.AND(guard, guard_to_conjoin1))
                new_templated_guards.append(Guard.AND(guard, guard_to_conjoin2))


            #logger.debug("OLD meta-template:")
            #logger.debug(str(self.current_template))
            #logger.debug("OLD applied charfun:")
            #logger.debug(str(self.phi_current_template))
            #logger.debug("\n\n")

            # creates new template variables for the linexp even though this might not be necessary
            self.current_template = ExpectationTemplate(self.variables, new_templated_guards, self.char_fun.terminate_guards_linexp_pairs)
            self.phi_current_template = self.char_fun.apply_expectation(self.current_template, False)

            logger.debug("New meta-template:")
            logger.debug(str(self.current_template))
            logger.debug("applied charfun:")
            logger.debug(str(self.phi_current_template))
            logger.debug("\n\n")

            # update self.current_template and self.phi_current_temaplte
            # update guard template variables!

            instance = self.instance_for_current_template(ctis)


        # we found a new template resolving all ctis
        logger.debug("\n\n there is an instance in this template")
        logger.debug(instance)
        logger.debug("\n\n")
        return instance


    def instance_for_current_template(self, ctis):
        """

        :param ctis:
        :return: None if the current template does not admit an instance resolving ctis. Otherwise, an Expectation*templat* admitting a partiall inductive instance is returned.
        """

        # TODO: Caching!!! This can be done way more efficiently
        # TODO: optmize substitution etc.
        # TODO: solver incrementality might help a lot
        formulae = []

        diff = get_env().formula_manager.get_symbol("diff")

        for i in range(len(ctis)):
            cti = ctis[i]

            var_to_val = {var: cti[var] for var in self.variables}

            #logger.debug("\n\n Current cti: %s" % var_to_val)

            for (guard1, linexp1) in self.current_template.guard_templatelinexp_pairs:

                #logger.debug("Current guard of tempalte: %s" % guard1)
                subst_guard1 = guard1.pysmt_expression.substitute(var_to_val)
                #logger.debug("Current substituted guard of tempalte: %s" % subst_guard1)
                #input("")

                # inductivity
                #logger.debug("now inductivity")
                for (guard2, linexp2) in self.phi_current_template.guard_linexp_pairs:
                        #TODO: proper simplification?
                        #logger.debug("guard of phi_temp: %s" % guard2)

                        lhs = And(subst_guard1, guard2.pysmt_expression.substitute(var_to_val)).simplify()
                        rhs = self.constraint_inequality(linexp2, linexp1).pysmt_expression.substitute(var_to_val)

                        #if i == len(ctis) - 1:
                        #    rhs = And(rhs, Equals(diff, Minus(linexp1.pysmt_expression, linexp2.pysmt_expression).substitute(var_to_val)))

                        form = Implies(lhs, rhs).simplify()
                        #logger.debug("resulting formula: %s" % form)
                        formulae.append(form)
                        #input("")


                #logger.debug("now non-negativity")
                # non-negativity
                #lhs = guard1.pysmt_expression.substitute(var_to_val)
                rhs = LinearInequality.LEQ(LinearExpression.get_constant_expression(self.variables, Real(0)),
                                                   linexp1).pysmt_expression.substitute(var_to_val)
                form = Implies(subst_guard1, rhs).simplify()
                #logger.debug("resulting formula: %s" % form)
                formulae.append(form)

                #input("")

                #logger.debug("now safety")
                # safety
                for (guard2, linexp2) in self.property.guard_linexp_pairs:
                    #logger.debug("guard of safety: %s" % guard2)
                    #lhs = guard1.pysmt_expression.substitute(var_to_val).simplify()
                    #We can keep the lhs from above
                    rhs = self.constraint_inequality(linexp1, linexp2).pysmt_expression.substitute(
                            var_to_val).simplify()

                    form = Implies(And(subst_guard1, guard2.pysmt_expression.substitute(var_to_val)), rhs)
                    #logger.debug("resulting formula: %s" % form)
                    formulae.append(form)
                    #input("")


        #for formula in formulae:
        #    if formula != TRUE():
        #        logger.debug(formula.serialize())

        model = get_model(formulae)
        # TODO: this is for superinvariants only!
        #model = z3_check_sat_maximizing_var(formulae, diff)


        if model == None:
            return None

        # extract new templated guards
        parameter_valuation = self.current_template.get_parameter_valuation_from_sovler_model(model,
                                                                                 self.guard_template_variables)

        guards_with_template = [guard.instantiate(parameter_valuation) for (guard, _) in self.current_template.guard_templatelinexp_pairs]
        new_template = ExpectationTemplate(self.variables, guards_with_template, self.char_fun.terminate_guards_linexp_pairs)

        return new_template







