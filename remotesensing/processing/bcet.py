import numpy as np
from tqdm import tqdm

from remotesensing.image import Image


class BCET:
    """ Balanced Contrast Enhancement Technique """
    @staticmethod
    def calculate(image: Image, L: float = 0., H: float = 1., E: float = 0.5, clip: float = 0.) -> Image:

        bcet_image = np.zeros(image.shape)
        for i in tqdm(range(image.band_count), total=image.band_count, desc='Calculating bands'):
            x = image[i].pixels

            l0 = np.ma.min(x)
            h0 = np.ma.max(x)
            e = np.ma.mean(x)

            l = l0 + (clip * (h0-l0))
            h = h0 - (clip * (h0-l0))

            L = L
            H = H
            E = E

            s = np.ma.mean(x**2)

            b = (h**2 * (E - L) - s * (H - L) + l**2 * (H - E)) / (2 * (h * (E - L) - e * (H - L) + l * (H - E)))
            a = (H - L) / ((h - l) * (h + l - 2 * b))
            c = L - a * (l - b)**2

            bcet_image[:, :, i] = a * (x - b)**2 + c

        bcet_image[bcet_image > H] = H
        bcet_image[bcet_image < L] = L

        return Image(bcet_image, image.geotransform, image.projection, band_labels=image.band_labels, metadata=image.metadata)
