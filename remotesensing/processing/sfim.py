import numpy as np
from cv2 import resize
from tqdm import tqdm

from remotesensing.image import Image


class SFIM:
    """ (Smoothing Filter-Based Intensity Modulation)
    A class for fusing together images for pansharpening
    """
    @classmethod
    def calculate(cls, coarse_image: Image, fine_image: Image) -> Image:

        pan_smooth = fine_image.smooth()

        if coarse_image.band_count > 2:

            fused_pixels = np.zeros((fine_image.height, fine_image.width, coarse_image.band_count))
            fused = Image(fused_pixels, fine_image.geotransform, fine_image.projection)

            bands = []
            for pan_band, band in tqdm(zip(fused, coarse_image), total=fused.band_count, desc='Fusing images'):
                bands.append(pan_band.apply(lambda x: cls._fuse_images(band.pixels, fine_image.pixels, pan_smooth)))

            return fused.stack(bands)

        else:
            return fine_image.apply(lambda x: cls._fuse_images(coarse_image.pixels, x, pan_smooth))

    @staticmethod
    def _fuse_images(coarse_pixels: np.ndarray, fine_pixels: np.ndarray, smoothed_pan_image: np.ndarray) -> np.ndarray:

        resized_image = resize(coarse_pixels, fine_pixels.shape[::-1])
        return (resized_image * fine_pixels) / smoothed_pan_image
