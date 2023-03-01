# cegispro2: Counterexample Guided Inductive Synthesis (of Inductive Invariants) for Probabilistic Programs

`cegispro2` is the tool to our TACAS'23 paper _"Probabilistic Program Verification via Inductive Synthesis of Inductive Invariants"_,
employing a CEGIS-style invariant synthesis techniques to solve the following problems:
Given a probabilistic loop C = while(b){body}, cegispro2 verifies:

- `wp[C](f) <= g` by synthesizing superinvariants
- `ert[C](0) < infty` (universal positive almost-sure termination) by synthesizing ert-superinvariants (cf. Weakest Precondition Reasoning for Expected Run-Times of Probabilistic Programs, Kaminski et al., ESOP'16
- `g <= wp[C](f)` by applying the inductive proof rule by Hark et al. (cf. Aiming Low Is Harder, Hark et al., POPL'20), i.e., by synthesizing subinvariants, proving UPAST, and by verifying conditional difference boundedness.


## Contents

 1. Installation
 2. Usage
 3. Accepted Syntax for Loops
 4. License

## 1. Installation


We use [poetry](https://github.com/python-poetry/poetry) for dependency management.
See [here](https://python-poetry.org/docs/) for installation instructions for poetry.

In the root directory of this repository, run `poetry install` to install the dependencies in a new virtual environment.

We used [z3](https://github.com/Z3Prover/z3) 4.8.17 for our experiments.
To install this version of z3, first run `poetry shell` to enter the virtual environment, then run `pip3 z3-solver==4.8.17`. You are now ready to run cegispro2.

## 2. Usage

cegispro2 is a Python 3 application using [pysmt](https://github.com/pysmt/pysmt) and [probably](https://github.com/Philipp15b/probably).
probably is a library built at the Software Modeling and Verification Group of RWTH Aachen to parse and work with pGCL programs and expectations.
Its internals are [quite extensively documented](https://philipp15b.github.io/probably/), so if there are questions about the input language of cegispro2, you might want to look there.

In the root directory of this repository, run `poetry shell` to enter the virtual environment. cegispro2 can then be run via 

`python3 -m cegispro2.cmd PROGRAM --post POST --prop PROP --invarianttype TYPE --templaterefiner TEMP`

where
- PROGRAM is a path to a pgcl program parsed by the tool Probably (https://philipp15b.github.io/probably/) (you can find numerous examples in the directories cegispro2/cegispro2/benchmarks/TACAS23_storm, cegispro2/cegispro2/benchmarks/TACAS23_ABSYNTH, cegispro2/cegispro2/benchmarks/TACAS23_EXIST)
- POST is a postexpectation in Disjoint Normal Form (run python3 -m cegispro2.cmd --help for more info). Examples are given in the first lines of the files contained in the above directories.
- PROP is a property (specifies the bound that is to be proven, run python3 -m cegispro2.cmd --help for more info). Examples are given in the first lines of the files contained in the above directories.
- TYPE is either super, sub, or past 
- templaterefiner is either inductivity, fixed, or variable (cf. Appendix D of our paper and run python3 -m cegispro2.cmd --help for more info)
- Additionally, if --invarianttype sub is set, you can set --cdb to synthesize a subinvariant which is conditionally difference bounded (cf. Aiming Low Is Harder, Hark et al., POPL'20).


## 3. Accepted Syntax for Loops

Parsing of pGCL programs and expectations is done by the [probably](https://philipp15b.github.io/probably/) library.
There are many examples in the `benchmarks` directory.

An excerpt from the [Lark](https://github.com/lark-parser/lark) grammar for pGCL programs used in the probably library:
```
declaration: "nat" var bounds? -> nat

bounds: "[" expression "," expression "]"

instruction: "skip"                                      -> skip
           | "while" "(" expression ")" block            -> while
           | "if" "(" expression ")" block "else"? block -> if
           | var ":=" rvalue                             -> assign
           | block "[" expression "]" block              -> choice
           | "tick" "(" expression ")"                   -> tick

rvalue: "unif" "(" expression "," expression ")" -> uniform
      | expression

literal: "true"  -> true
       | "false" -> false
       | INT     -> nat
       | FLOAT   -> float
       | "∞"     -> infinity
       | "\infty" -> infinity
```

Expressions in programs and expectations can be built from the following operators, grouped by precedence:

1. `||`, `&`
2. `<=`, `<`, `=`
3. `+`, `-`
4. `*`, `:`
5. `/`
6. `not `, `( ... )`, `[ ... ]`, `literal`, `var`

Whitespace is generally ignored.

## 8. License

We provide cegispro2 under the Apache-2.0 license (see `LICENSE` file).

