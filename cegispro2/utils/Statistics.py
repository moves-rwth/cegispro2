import attr
import time
from typing import Any, BinaryIO, Dict, Optional
from pysmt.shortcuts import simplify
from cegispro2.expectations.Expectation import Expectation
from cegispro2.expectations.Guard import Guard
from cegispro2.synthesis.Property import Property
from cegispro2.parsing.parser import parse_probably_property_into_cegispro_property
import re

@attr.s
class Timer:
    """
    A timer keeps a total time in seconds and allows starting and stopping it to
    increment the values.
    """

    _elapsed: float = attr.ib(default=0.0)
    _timer_start: Optional[float] = attr.ib(default=None)
    """The start time returned from time.perf_counter()."""
    def start_timer(self):
        assert self._timer_start is None, "cannot start timer twice without stopping in between"
        self._timer_start = time.perf_counter()

    def stop_timer(self):
        end = time.perf_counter()
        assert self._timer_start is not None, "cannot stop timer that is not running"
        self._elapsed += end - self._timer_start
        self._timer_start = None

    @property
    def value(self) -> float:
        """Return the current value of this timer, including running timer values."""
        extra = time.perf_counter(
        ) - self._timer_start if self._timer_start is not None else 0
        return self._elapsed + extra

    def __getstate__(self) -> float:
        return self.value

    def __setstate__(self, value: float):
        self._elapsed = value
        self._timer_start = None

    def __str__(self) -> str:
        return f"{round(self.value, 2)} s"


def _make_running_timer() -> Timer:
    timer = Timer()
    timer.start_timer()
    return timer


@attr.s
class Statistics:

    program: str = attr.ib()
    post: str = attr.ib()
    prop: str = attr.ib()
    distance: int = attr.ib()

    num_ctis: int = attr.ib(default=None)
    num_template_refinements: int = attr.ib(default=None)
    num_template_expressions: int = attr.ib(default=None)

    parse_time: Timer = attr.ib(factory=Timer)
    inductivity_check_time: Timer = attr.ib(factory=Timer)
    template_instantiation_time: Timer = attr.ib(factory=Timer)
    template_refinement_time: Timer = attr.ib(factory=Timer)

    total_time: Timer = attr.ib(factory=_make_running_timer)


    def __str__(self):
        lines = [
            "------- Statistics (%s, post: %s, prop: %s) -------" % (self.program, self.post, self.prop), f"Total time = {self.total_time}",
            f"Parse time = {self.parse_time}",
            f"Inductivity check time = {self.inductivity_check_time}",
            f"Template instantiation time = {self.template_instantiation_time}",
            f"Template refinement time = {self.template_refinement_time}",
            "",
            f"Number CTIs = {self.num_ctis}",
            f"Number template refinements = {self.num_template_refinements}",
            f"Number template expressions = {self.num_template_expressions}",
        ]

        try:
            lines.append(f"Inductive Invariant = {self.inductive_invariant}")
        except:
            pass

        return "\n".join(lines)

    def extract_bound_for_initialstates(self):
        bounds = []
        if self.initialstates == "":
            self.bound = None
        else:
            prop = parse_probably_property_into_cegispro_property(self.initialstates)
            guard = prop.guard_linexp_pairs[0][0]
            for (guard2,linexp2) in self.inductive_invariant.guard_linexp_pairs:
                conj = Guard.AND(guard, guard2)
                if conj.is_sat():
                    bounds.append(linexp2)

            if len(bounds) == 0:
                raise Exception("Initial states did not match any guard.")
            elif len(bounds) ==1:
                b = re.sub("ToReal\(([A-Za-z0-9_]+)\)", "\\1", str(simplify(bounds[0].pysmt_expression).serialize()))
                self.bound = b
            else:
                b = re.sub("ToReal\(([A-Za-z0-9_]+)\)", "\\1", str(simplify(bounds[0].pysmt_expression).serialize()))
                self.bound = "max{ " + b
                for i in range(1,len(bounds)):
                    b = re.sub("ToReal\(([A-Za-z0-9_]+)\)", "\\1",
                               str(simplify(bounds[i].pysmt_expression).serialize()))
                    self.bound += ", " + b
                self.bound += " }"
            print(self.bound)