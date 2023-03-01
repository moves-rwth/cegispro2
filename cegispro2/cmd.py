import click
from cegispro2.parsing.parser import *
from cegispro2.synthesis.CEGIS import CEGIS
from cegispro2.synthesis.OneShotSynthesizer import OneShotSynthesizer
import os
from cegispro2.utils.Statistics import Statistics
from cegispro2.utils.Options import Options
from cegispro2.synthesis.TemplateRefinement.InductivityRefiner import InductivityRefiner
from cegispro2.synthesis.TemplateRefinement.VariablePartitionRefiner import VariablePartitionRefiner
from cegispro2.synthesis.TemplateRefinement.SplitFiniteStateSpaceRefiner import SplitFiniteStateSpaceRefiner
from cegispro2.synthesis.TemplateRefinement.HyperplaneRefiner import HyperplanePartitionRefiner
from cegispro2.expectations.ExpectationTemplate import ExpectationTemplate
from cegispro2.expectations.Expectation import Expectation
from pysmt.shortcuts import reset_env
import pickle
from pathlib import Path

logger = logging.getLogger("cegispro2")

@click.argument('program', type=click.Path(exists=True))
@click.option('--post', type=click.STRING,
              help="The post-expectation. The postexpectation must be in disjoint normal form, i.e., of the form [guard_1]*expr + ... [guard_n]*expr such that the guard_i partition the state space.")
@click.option('--prop',
              type=click.STRING,
              help="The upper bound on the weakest preexpectation that is to be verified. Must be of the form [guard_1]*expr + ... [guard_n]*expr. The guard_i must be mutually exclusive. Every state that does not satisfy any guard is implicitly assigned infinity (for upper bounds) or 0 (for lower bounds).")
@click.option('--template',
              type = click.STRING,
              default = "",
              help="The (initial) template as a comma separated list of probably guards partitioning the loop guard. If empty, the template will be read off the syntax of the loop.")
@click.option('--validate/--novalidate',
              default = False,
              help="Whether to validate that the inductive invariant is (1) in gnf (2) safe (3) non-negative and (3) inductive and whether (4) the representation of the characteristic functional Phi is in disjoint normal form.")
@click.option('--verifier',
              type = click.Choice(['distance', 'optimization']),
              default = 'distance',
              help="Whether to use the cooperative verifier via increasing distance or via OMT. In our TACAS paper, we only use the distance-verifier.")
@click.option(
    '--distance',
    type=click.INT,
    default = 1,
    help="The constant the distance constraint is multiplied with and divided by, respectively.")
@click.option(
    '--templaterefiner',
    type=click.Choice(['variable', 'fixed', 'inductivity', 'hyperplane']),
    default="inductivity",
    help=
    "Which template refiner to use. 'variable' produces non-fixed partition templates (cf.\ column Dynamic in Table 2), 'fixed' produces fixed-partition templates and can be used only for finite-state programs (those programs for which every variable is assigned a range of values),and inductivity produces fixed-partition templates guided by the last partially inductive candidate the inner CEGIS loop produced."
)
@click.option(
    '--partitionfactor',
    type=click.INT,
    default = 1,
    help="A factor determining the search space for the variable template refiner.")
@click.option(
    '--usemotzkin/--nousemotzkin',
    default = False,
    help="NOT SUPPORTED. We do not consider this in our TACAS paper. Whether to use Motzkin's transposition theorem to ensure welldefinedness and safety.")
@click.option(
    '--optimizing-synthesizer/--nooptimizing-synthesizer',
    default = False,
    help = "Whether to use an optimizing synthesizer. We do not conisider this in our TACAS paper."
)
@click.option('--debuglog/--nodebuglog',
              default = False,
              help ="Determining the logging mode.")
@click.option('--exporttemplate/--noexporttemplate',
              default = False,
              help ="Wheter to print the final expectation template as a comma separated probably string.")
@click.option('--oneshot/--nooneshot',
              default = False,
              help = "NOT SUPPORTTED. If true, a one-shot solver using Motzkin's transposition theorem is used to find an inductive instance of the template. Note: We then solve a relaxation of the problem assuming that the program variables are real-valued.")
@click.option('--invarianttype',
              type=click.Choice(['sub', 'super', 'past']),
              default="super",
              help = "Which type of invariant to generate. We remark that sub-invariants I <= Phi(I) do not necessarily yield lower bounds on lfp Phi. A sufficient criterion is (1) post is 1-bounded *and* 2-the loop terminates UAST. past tries to synthesize an ert-superinvariant for proving PAST: ignores post and prop and sets post =0.")
@click.option('--cdb/--nocdb',
              default = False,
              help = "Whether to ensure conditional difference boundedness in case we are synthesizing a sub-invariant.")
@click.option('--safestatistics',
              default = '',
              help = "The directory the statistics shall be stored in. Leave empty if you don't want the statistics to be stored.")
@click.option('--initialstates',
              default = '',
              help="An expectation of the form [phi]. If set, the part of the inductive invariant satisfying phi is stored as a string in statistics.bound.")
def _main(program, post, prop, template, validate, verifier, distance, templaterefiner, partitionfactor, usemotzkin,
          optimizing_synthesizer, debuglog, exporttemplate, oneshot, invarianttype, cdb, safestatistics, initialstates):

    _setup_logger("log.txt", logging.DEBUG if debuglog else logging.INFO, logging.DEBUG if debuglog else logging.INFO)

    if usemotzkin or oneshot:
        raise Exception("Using Motzkin's Transposition Theorem or the Oneshot Solver is currently not supported")

    with open(program, 'r') as program_file:
        program_code = program_file.read()
        filename = os.path.basename(program_file.name)

    # ------------- Set up options and statistics objects ------------
    print(filename)
    options = Options()
    distance = int(distance)
    options.distance = distance
    options.optimizing_synthesizer = optimizing_synthesizer


    options.verifier = verifier
    if options.verifier == 'optimization':
        options.distance = 1
    elif options.verifier == 'distance':
        pass
    else:
        raise Exception("Unkown verifier type")

    options.verifier = verifier

    if invarianttype == "super":
        options.past = False
        options.cdb = False # Never care about cdb if we synthesize super invariants
        options.invarianttype = invarianttype
    elif invarianttype == "sub":
        options.past = False
        options.cdb = cdb
        options.invarianttype = invarianttype
        if oneshot:
            raise Exception("Using motzkin/oneshot synthesis for *sub*invariants is currently not supported.")
    elif invarianttype == "past":
        options.past = True
        options.cdb = False
        logger.debug("Trying to prove PAST ...")
        prop = ""  # means we want an inductive invariant I with I < infty
        post = "0" # post for ert is 0
        options.invarianttype = "super"
    else:
        raise Exception("Unkown invariant type.")


    statistics = Statistics(filename, post, prop, distance)
    statistics.program = filename
    statistics.cdb = options.cdb
    statistics.past = options.past
    statistics.parse_time.start_timer()
    statistics.initialstates = initialstates
    options.program_code = program_code
    options.post = post
    options.use_motzkin = usemotzkin


    # Returns a wp- or an ert-characteristic functional depending on past.
    charfun = parse_program_and_postexp_into_charfun(options)
    property = parse_probably_property_into_cegispro_property(prop)

    if not property.check_guards_are_mutually_exclusive():
        raise Exception("Guards occurring in the property must be mutually exclusive: %s " % str(property))
    statistics.parse_time.stop_timer()

    statistics.prop = property
    statistics.post = post
    statistics.distance = distance


    if template == "":
        options.initial_template = charfun.get_initial_expectation_template()
    else:
        template_guards = comma_separated_string_of_probably_guards_to_list_of_cegispro_guards(charfun.variables, template)
        options.initial_template = ExpectationTemplate(charfun.variables, template_guards, charfun.terminate_guards_linexp_pairs)

    if not options.initial_template.check_gnf() == True:
        raise Exception("The Boolean expressions occuring in the initial template do not partition the loop guard. Do the guards appearing in the post partition the state space?")

    logger.debug("initial template:")
    logger.debug(options.initial_template)


    options.usemotzkin = usemotzkin
    options.partitionfactor = partitionfactor

    statistics.found_inductive_invariant = False

    if oneshot:
        statistics.templatestring = options.initial_template.template_guards_as_comma_separated_pysmt_string()
        synth = OneShotSynthesizer(charfun, options.initial_template, property, validate)
        statistics.num_template_expressions = len(options.initial_template.guard_templatelinexp_pairs)
        if synth.synthesize() == None:
            statistics.total_time.stop_timer()
            raise Exception("No inductive instance of the template by one-shot solving.")

    else:
        if templaterefiner == 'inductivity':
            options.templateRefiner = InductivityRefiner(charfun.variables, charfun, property, options, statistics)
        elif templaterefiner == 'variable':
            options.templateRefiner = VariablePartitionRefiner(charfun.variables, charfun, property, options, statistics)

            if options.optimizing_synthesizer:
                raise Exception("Optimizing synthesizer is not supported for the variable template refiner.")

            if exporttemplate:
                logger.info("Cannot export template for VariablePartitionRefiner.")
                exporttemplate = False
        elif templaterefiner == 'fixed':
            options.templateRefiner = SplitFiniteStateSpaceRefiner(charfun.variables, charfun, property, options, statistics)
        elif templaterefiner == 'hyperplane':
            options.templateRefiner = HyperplanePartitionRefiner(charfun.variables, charfun, property, options,
                                                                   statistics)
        else:
            raise Exception("Undefined template refiner.")

        options.exporttemplate = exporttemplate
        options.validate = validate

        cegis = CEGIS(charfun.variables, charfun, property, options, statistics)
        cegis.synthesize()

        statistics.extract_bound_for_initialstates()

    statistics.total_time.stop_timer()



    print(statistics)
    if exporttemplate:
        print("Template = " + statistics.templatestring)

    if safestatistics != '':
        try:
            pickle_statistics(safestatistics, filename, statistics)
        except Exception as ex:
            print("Unable to save statistics: %s" % str(ex))




def _setup_logger(logfile, cmd_loglevel, file_loglevel):
    logger = logging.getLogger("cegispro2")
    logger.setLevel(cmd_loglevel)

    # create file handler which logs even debug messages
    fh = logging.FileHandler(logfile)
    fh.setLevel(file_loglevel)
    # create console handler with a higher log level
    ch = logging.StreamHandler()
    ch.setLevel(cmd_loglevel)
    # create formatter and add it to the handlers
    fileformatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    consoleformatter = logging.Formatter('%(name)s: %(message)s')

    ch.setFormatter(consoleformatter)
    fh.setFormatter(fileformatter)
    # add the handlers to logger
    logger.addHandler(ch)
    logger.addHandler(fh)


def pickle_statistics(path, filename, statistics):
    #print(path + "/" + filename)
    with open(path + filename + ".pickle", "wb") as handle:
        pickle.dump(statistics, handle)






main = click.command()(_main)
if __name__ == "__main__":
    main()