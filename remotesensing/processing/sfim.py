import numpy as np
from tqdm import tqdm
from skimage.morphology import disk
from skimage.filters import rank
from skimage.transform import resize

from remotesensing.image import Image


class SFIM:
    """ (Smoothing Filter-Based Intensity Modulation)
    A class for fusing together images for pansharpening
    """

    @classmethod
    def calculate(cls, coarse: Image, fine: Image, filter_size: int = None) -> Image:

        if not filter_size:
            filter_size = fine.geotransform.pixel_width // coarse.geotransform.pixel_width

        smooth_pan = rank.mean(fine.pixels, disk(filter_size))

        output_shape = (fine.height, fine.width, coarse.band_count)
        msi_upsampled = fine.apply(lambda x: resize(coarse.pixels, output_shape, preserve_range=True))

        bands = []
        for band in msi_upsampled:

            numerator = band.pixels * fine.pixels
            bands.append(band.apply(lambda x: np.divide(numerator, smooth_pan, out=np.zeros_like(numerator), where=smooth_pan != 0)))

        return Image.stack(bands)
