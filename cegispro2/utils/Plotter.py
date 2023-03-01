#from cegispro2.expectations.Expectation import Expectation
from mpl_toolkits.mplot3d import Axes3D
from scipy.interpolate import griddata
import matplotlib.pyplot as plt
import numpy as np
from fractions import Fraction
from cegispro2.solving.Solver import *
from pysmt.shortcuts import LE

def plot_expectation(exp, states):
    """
    Plot an expectation in one or two variables.

    :param exp: The expectation to plot.
    :param states: The states that shall be plotted. states is a lost of dicts from exp's vars to PySMT values.
    :return:
    """

    if len(exp.variables) != 2:
        raise Exception("We support plotting with 2-variabled expectations only.")

    xyztriples = []

    for state in states:
        xyztriples.append(tuple([int(str(state[var])) for var in exp.variables]) + tuple([Fraction(str(exp.evaluate_at_state(state)))]))

    plot_from_xyz_triples(exp.variables, xyztriples)

def plot_from_xyz_triples(variables, xyztriples):
    """
    This is essentially copied from https://stackoverflow.com/questions/21161884/plotting-a-3d-surface-from-a-list-of-tuples-in-matplotlib .
    :param xyztriples: A list of (x,y,z) triples.
    :return:
    """

    data = xyztriples
    x, y, z = zip(*data)
    z = list(map(float, z))
    grid_x, grid_y = np.mgrid[min(x):max(x):100j, min(y):max(y):100j]
    grid_z = griddata((x, y), z, (grid_x, grid_y), method='cubic')

    fig = plt.figure()
    ax = fig.gca(projection='3d')
    ax.plot_surface(grid_x, grid_y, grid_z, cmap=plt.cm.Spectral)

    ax.invert_xaxis()

    ax.set_xlabel("%s" % str(variables[0]))
    ax.set_ylabel("%s" % str(variables[1]))

    plt.show()


def plot_inductive_states(f, phi_f, states):
    """

    :param f:
    :param phi_f:
    :param states:
    :return:
    """

    fig = plt.figure()
    ax = fig.gca()

    #create x and y list
    x = []
    y = []

    for state in states:
        if is_sat([LE(phi_f.evaluate_at_state(state), f.evaluate_at_state(state))]):
            # Phi(f)[state] <= f[state] holds, add coordinates
            x.append(int(str(state[f.variables[0]])))
            y.append(int(str(state[f.variables[1]])))

    ax.scatter(x,y)
    ax.set_xlabel("%s" % str(f.variables[0]))
    ax.set_ylabel("%s" % str(f.variables[1]))

    plt.show()