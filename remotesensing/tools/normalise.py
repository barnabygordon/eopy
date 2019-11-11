import numpy as np


def normalise(image: np.ndarray) -> np.ndarray:
    """ normalise an image array to 0-1 """
    image_min = np.nanmin(image)
    image_max = np.nanmax(image)
    return (image - image_min) / (image_max - image_min)
