import numpy as np

from remotesensing.image import Image


def linear_stretch(image: Image, limit: float = 1, percentile: int = None, std: int = None) -> Image:

    bands = []
    for band in image:

        min_value, max_value = np.nanmin(band.pixels), np.nanmax(band.pixels)

        if percentile:
            min_value, max_value = np.nanpercentile(band.pixels, (percentile, 100 - percentile))

        elif std:
            mean, band_std = np.nanmean(band.pixels), np.nanstd(band.pixels)
            min_value, max_value = mean - std * band_std, mean + std * band_std

        if percentile or std:
            band = band.apply(lambda x: np.where(x > max_value, max_value, x))
            band = band.apply(lambda x: np.where(x < min_value, min_value, x))

        bands.append(band.normalise(output_range=(0, limit), current_range=(min_value, max_value)))

    if len(bands) == 1:
        return bands[0]

    return Image.stack(bands)


def bcet(image: Image, limit: float = 1, percentile: int = None, clip: float = 0., window: slice = None) -> Image:
    ''' BCET (Balanced Contrast Enhancement Technique)
    G.J. Liu (1990) Balance contrast enhancement technique and its application in image colour composition
    '''

    L, H = 0, limit
    E = H / 2

    bands = []
    for band in image:

        pixels = band.pixels[window] if window else band.pixels

        if percentile is not None:
            min_offset, max_offset = np.nanpercentile(pixels, (clip, 100 - clip))

        else:
            min_value, max_value = np.nanmin(pixels), np.nanmax(pixels)
            min_offset = clip * (max_value - min_value)
            max_offset = min_offset

        l = np.nanmin(pixels) + min_offset
        h = np.nanmax(pixels) - max_offset

        s = np.nanmean(pixels**2)
        e = np.nanmean(pixels)

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
