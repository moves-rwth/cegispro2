from cegispro2.synthesis.TemplateRefinement.FixedPartitionTemplateRefiner import FixedPartitionTemplateRefiner
from cegispro2.synthesis.synthesis_utils import *
from cegispro2.expectations.Expectation import Expectation
from pysmt.shortcuts import TRUE

class InductivityRefiner(FixedPartitionTemplateRefiner):
    """
    Fixed-partition.
    Refinement strategy that obtains a new template by splitting the last instance of the current template into inductive and non-inductive parts.
    """
    def __init__(self, variables, char_fun, property, options, statistics):
        super(InductivityRefiner, self).__init__(variables,char_fun,property,options, statistics)



    def get_initial_constraint_for_template(self, template):
        # Since guards do not contain template variables, we can constrain both safety and non-negativity via motzkin
        if self.options.use_motzkin:
            return get_safety_motzkin_constraints(template, self.property, self.variables, constraint_inequality=self.constraint_inequality) \
                          + get_nonnegativity_motzkin_constraints(template, self.variables)
        else:
            return [TRUE()]

    def get_refined_template(self, old_template, ctis, last_cti, f, phi_f):

        longest_template = None
        longest_template_length = None
        for i in range(len(old_template.guard_templatelinexp_pairs)):
            new_template = extract_new_template_by_splitting_guard(f, phi_f, i, self.char_fun)
            len_of_new_template = len(new_template.guard_templatelinexp_pairs)

            if len(new_template.guard_templatelinexp_pairs) > len(old_template.guard_templatelinexp_pairs) and (
                    longest_template_length == None or len_of_new_template > longest_template_length):
                longest_template_length = len_of_new_template
                longest_template = new_template

        assert (longest_template is not None)
        assert (len(longest_template.guard_templatelinexp_pairs) > len(old_template.guard_templatelinexp_pairs))

        return longest_template


