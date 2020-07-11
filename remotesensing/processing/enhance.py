import numpy as np

from remotesensing.image import Image


def bcet(image: Image, L: float = 0., H: float = 1., E: float = 0.5, clip: float = 0., window: slice = None) -> Image:

    bands = []
    for band in image:

        if window:
            pixels = band.pixels[window]
        else:
            pixels = band.pixels

        l0 = np.ma.min(pixels)
        h0 = np.ma.max(pixels)
        e = np.ma.mean(pixels)

        l = l0 + (clip * (h0-l0))
        h = h0 - (clip * (h0-l0))

        L = L
        H = H
        E = E

        s = np.ma.mean(pixels**2)

        b = (h**2 * (E - L) - s * (H - L) + l**2 * (H - E)) / (2 * (h * (E - L) - e * (H - L) + l * (H - E)))
        a = (H - L) / ((h - l) * (h + l - 2 * b))
        c = L - a * (l - b)**2

        bands.append(band.apply(lambda x: a * (x - b)**2 + c))

    bcet_image = image.stack(bands)

    bcet_image.pixels[bcet_image.pixels > H] = H
    bcet_image.pixels[bcet_image.pixels < L] = L

    return bcet_image
