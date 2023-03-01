from cegispro2.synthesis.synthesis_utils import *
from pysmt.shortcuts import Symbol, INT

import logging

#!!!  Slows down everything. Turn this import off !!!
#from cegispro2.utils.Plotter import *

logger = logging.getLogger("cegispro2")

class CEGIS:

    def __init__(self, variables, char_fun, property, options,  statistics):
        """
        Goal: Find inductive invariant proving that the program + postexpectation represented by charfun satsifies spec
        :param variables: The set of variables occurring in the program.
        :param char_fun: The characteristic functional representing the given loop and postexpectation.
        :param property: The property (upper or lower bound) that is to be verified.
        """

        self.statistics = statistics
        self.variables = variables
        self.char_fun = char_fun
        self.property = property
        self.validate = options.validate
        self.ctis = []
        self.num_template_refinements = 0
        self.distance_constant = options.distance
        self.templateRefiner = options.templateRefiner
        self.exporttemplate = options.exporttemplate
        self.options = options
        #self.f_var = Symbol("f_1", REAL)
        #self.phi_f_var = Symbol("f_2", REAL)
        self.index_f_var = Symbol("index_f", INT)
        self.index_phi_f_var = Symbol("index_phi_f", INT)
        self.index_exp1_var = Symbol("index_exp1", INT)
        self.index_exp2_var = Symbol("index_exp2", INT)

        # --- For conditional difference boundedness
        if options.cdb:
            self.var_to_helpvar = {var : Symbol("%s_help" % str(var), INT) for var in variables}
            self.helpvar_to_var = {self.var_to_helpvar[var] : var for var in self.variables}


    def synthesize(self):
        """
        The outer CEGIS loop. Starts with initial template and keeps calling the inner loop and refining the template until we find an inductive invariant
        certifying the validity of the property under consideration.
        :return:
        """

        # We initialize with the standard template
        current_template = self.templateRefiner.get_initial_template()

        while(True):

            logger.debug("\n\nCurrent Template (Number template expressions: %s)" % (len(current_template.guard_templatelinexp_pairs)))
            current_template = self.make_inductive_or_refine(current_template)
            if current_template == True:
                break
            self.num_template_refinements += 1

    def make_inductive_or_refine(self, exp_temp):
        """
        :param exp_temp: An expectation template. We search for a safe inductive instance within the template.
        :return: True if we find a safe inductive instance within the template, or a refined template if we learn that
        no such safe inductive instace exists.
        """

        # We need phi_exp_temp for extracting constraints
        logger.debug("Applying template to characteristic functional ..")
        self.statistics.template_instantiation_time.start_timer()
        phi_exp_temp = self.char_fun.apply_expectation(exp_temp)
        logger.debug(".. dóne")

        cur_constraints = self.templateRefiner.get_initial_constraint_for_template(exp_temp)
        cur_constraints = cur_constraints + self.templateRefiner.get_constraints_from_existing_ctis(self.ctis, phi_exp_temp, exp_temp)

        # --- For conditional difference boundedness
        if self.options.cdb:
            exp_temp_delta = exp_temp.get_delta_expectation(self.var_to_helpvar)
            logger.debug("applying delta expectation to characteristic functional")
            phi_exp_temp_delta = self.char_fun.apply_expectation(exp_temp_delta, prune_unsat_guards_early = True, substitute_helpers_back_to_normals = True, helpvar_to_var = self.helpvar_to_var)
            logger.debug("done")
            cur_constraints += self.templateRefiner.get_cdb_constraints_from_existing_ctis(self.ctis, phi_exp_temp_delta)
        # ---


        # get first parameter valuation and first instance
        model = self.templateRefiner.synthesize_parameter_valuation(cur_constraints)
        if model is None:
            logger.debug(exp_temp)
        assert(model != None)

        logger.debug("Getting parameter valuation and instantiate template ..")
        parameter_valuation = exp_temp.get_parameter_valuation_from_sovler_model(model, self.templateRefiner.guard_template_variables)
        f = self.templateRefiner.instantiate_parameters(exp_temp, parameter_valuation)
        phi_f = self.templateRefiner.instantiate_parameters(phi_exp_temp, parameter_valuation)


        # --- For conditional difference boundedness
        if self.options.cdb:
            phi_f_delta = phi_exp_temp_delta.instantiate(parameter_valuation)
        # ---


        logger.debug(".. done")

        self.statistics.template_instantiation_time.stop_timer()

        distance = 1
        last_cti = None
        guard_of_last_cti = None

        #plot_inductive_states(f, phi_f, self.char_fun.get_list_of_states_satisfying_loop_guard())
        #plot_expectation(f, self.char_fun.get_list_of_states_satisfying_loop_guard())

        while(True):


            logger.debug("parameter valuation and instance:")
            #logger.debug(model)
            logger.debug(f)
            #logger.debug(model)
            res = self.templateRefiner.get_next_counterexample_state(f, phi_f, exp_temp, phi_exp_temp, last_cti, guard_of_last_cti, distance)


            #---- additionally check for conditional difference boundedness (if invarianttype is sub and there was no other cex)
            if self.options.cdb and res == None:
                res = self.templateRefiner.get_counterexample_to_conditional_difference_boundedness(phi_f_delta, distance, model[self.templateRefiner.pysmt_cdb_constant])
            # ---


            if res == None:
                print( "\n\n ----------------- Template instance is safely inductive (required %s CTIS and %s template refinements. Num template expressions: %s): -------------" % (len(self.ctis), self.num_template_refinements, len(exp_temp.guard_templatelinexp_pairs)))
                #print(exp_temp)
                #print(f)
                self.statistics.inductive_invariant = f

                if self.options.cdb:
                    print("Conditionally Difference Bounded by %s\n\n" % (model[self.templateRefiner.pysmt_cdb_constant]))

                #plot_expectation(f, self.char_fun.get_list_of_states_satisfying_loop_guard())

                if self.validate:
                    print("validate ...")
                    validate_inductive_invariant(self.char_fun, self.options, f, self.property)
                    print("... successful")

                self.statistics.num_ctis = len(self.ctis)
                self.statistics.num_template_refinements = self.num_template_refinements
                self.statistics.num_template_expressions = len(exp_temp.guard_templatelinexp_pairs)
                if self.exporttemplate:
                    self.statistics.templatestring = exp_temp.template_guards_as_comma_separated_pysmt_string()

                self.statistics.found_inductive_invariant = True
                return True

            (distance, state_and_info) = res
            (cti, guard_linexp_phi_exp_temp, guard_linexp_exp_temp) = state_and_info

            # Otherwise, if we found a cti,...
            logger.debug("\n")
            logger.debug("\n")
            logger.debug("\nNot inductive, counterexample (distance = %s):" % distance)
            logger.debug(cti)

            new_constraints = self.templateRefiner.get_constraint_from_counterexample_state(cti,exp_temp, phi_exp_temp,
                                                                                           guard_linexp_phi_exp_temp,
                                                                                           guard_linexp_exp_temp)


            # --- For conditional difference boundedness
            if self.options.cdb:
                new_constraints += self.templateRefiner.get_cdb_constraints(cti, phi_exp_temp_delta)
            # ---


            self.statistics.template_instantiation_time.start_timer()
            new_model = self.templateRefiner.synthesize_parameter_valuation(new_constraints + cur_constraints)
            self.statistics.template_instantiation_time.stop_timer()

            if new_model is None:
                #.. but cannot resolve it with the current template
                # ... and finally refine
                logger.debug("Refine template.")

                # splitting of guard with unresolbvable cti might not yield progress.
                # if there is no progress, try another index

                self.statistics.template_refinement_time.start_timer()
                new_template = self.templateRefiner.get_refined_template(exp_temp, self.ctis, cti, f, phi_f)
                self.statistics.template_refinement_time.stop_timer()
                return new_template
            else:
                #... or we can resolve the cti and get a new parameter valuation.
                self.statistics.template_instantiation_time.start_timer()
                model = new_model
                cur_constraints = cur_constraints + new_constraints
                last_cti=cti
                if guard_linexp_exp_temp is not None:
                    guard_of_last_cti = guard_linexp_exp_temp[0]
                else:
                    guard_of_last_cti = None
                self.ctis.append(cti)
                distance = distance * self.distance_constant

                parameter_valuation = exp_temp.get_parameter_valuation_from_sovler_model(model,self.templateRefiner.guard_template_variables)
                f = self.templateRefiner.instantiate_parameters(exp_temp, parameter_valuation)
                phi_f = self.templateRefiner.instantiate_parameters(phi_exp_temp, parameter_valuation)

                # --- For conditional difference boundedness
                if self.options.cdb:
                    phi_f_delta = phi_exp_temp_delta.instantiate(parameter_valuation)

                self.statistics.template_instantiation_time.stop_timer()
