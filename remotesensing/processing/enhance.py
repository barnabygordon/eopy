import numpy as np
from typing import Tuple

from remotesensing.image import Image


def linear(image: Image, contrast: float, brightness: float) -> Image:

    return image.apply(lambda x: contrast * x + brightness)


def bcet(image: Image, value_range: Tuple[int, int] = (0, 1), clip: float = 0., window: slice = None) -> Image:
    ''' BCET (Balanced Contrast Enhancement Technique)
    G.J. Liu (1990) Balance contrast enhancement technique and its application in image colour composition
    '''

    L, H = value_range
    E = H / 2

    bands = []
    for band in image:

        pixels = band.pixels[window] if window else band.pixels

        l0 = np.nanmin(pixels)
        h0 = np.nanmax(pixels)
        e = np.nanmean(pixels)

        l = l0 + (clip * (h0-l0))
        h = h0 - (clip * (h0-l0))

        s = np.nanmean(pixels**2)

        b = (h**2 * (E - L) - s * (H - L) + l**2 * (H - E)) / (2 * (h * (E - L) - e * (H - L) + l * (H - E)))
        a = (H - L) / ((h - l) * (h + l - 2 * b))
        c = L - a * (l - b)**2

        bands.append(band.apply(lambda x: a * (x - b)**2 + c))

    bcet_image = Image.stack(bands)

    bcet_image.pixels[~np.isnan(bcet_image.pixels) > H] = H
    bcet_image.pixels[~np.isnan(bcet_image.pixels) < L] = L

    return bcet_image


def dds(image: Image, k: float = 0.6) -> Image:
    ''' DDS (Direct Decorrelation Stretch)
    J.G. Liu & McM Moore (1995) Direct decorrelation stretch technique for RGB colour composition
    '''

    x = np.nanmin(image.pixels, axis=2)

    return Image.stack([band.apply(lambda i: i - (k * x)) for band in image])
