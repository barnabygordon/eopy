import numpy as np
from skimage.morphology import disk
from skimage.filters import rank
from skimage.transform import resize

from eopy.image import Image


def sfim(msi: Image, pan: Image, filter_size: int = None) -> Image:
    """ SFIM (Smoothing Filter-Based Intensity Modulation)
    J.G. Liu (1999) Smoothing Filter-based Intensity Modulation: a spectral preserve
    image fusion technique for improving spatial details
    """

    if not filter_size:
        filter_size = pan.geotransform.pixel_width // msi.geotransform.pixel_width

    smooth_pan = rank.mean(pan.pixels, disk(filter_size))

    output_shape = (pan.height, pan.width, msi.band_count)
    msi_upsampled = pan.apply(lambda x: resize(msi.pixels, output_shape, preserve_range=True))

    bands = []
    for band in msi_upsampled:

        numerator = band.pixels * pan.pixels
        bands.append(band.apply(lambda x: np.divide(numerator, smooth_pan, out=np.zeros_like(numerator), where=smooth_pan != 0)))

    return Image.stack(bands)
