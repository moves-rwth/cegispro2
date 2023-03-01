from cegispro2.solving.Solver import *
from pysmt.shortcuts import And

class Property:
    """
    A specification stores a list of pairs (ineqs, linexp). Semantics: for all program states s: s \models ineqs => wp[C](post)[s] <= linexp[s]
    """

    def __init__(self, guard_linexp_pairs):
        """
        :param list_of_ineqs_linexp_pairs: A list of pairs (ineqs, linexp) with semantics as described above.
        """

        self.guard_linexp_pairs = guard_linexp_pairs

    def __str__(self):
        out = ""

        for summand in self.guard_linexp_pairs:
            out = "[" + str(summand[0]) + "]"
            out += " * (" + str(summand[1]) + ") + "

        out = out[:-2]
        return out

    def check_guards_are_mutually_exclusive(self):
        for i in range(len(self.guard_linexp_pairs)):
            for j in range(i+1,len(self.guard_linexp_pairs)):
                if is_sat([self.guard_linexp_pairs[i][0].pysmt_expression, self.guard_linexp_pairs[j][0].pysmt_expression]):
                    return False

        return True

