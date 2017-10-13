import numpy as np


def wrap(phase):
    wrapped = np.mod(phase + np.pi, 2 * np.pi) - np.pi
    return wrapped
