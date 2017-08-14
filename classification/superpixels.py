from skimage.segmentation import slic

from image import Image


class Superpixels:
    def __init__(self, image: Image, n_segments: int=100, compactness: float=10.,
                 sigma: int=0, enforce_connectivity: bool=True):
        self.image = image.pixels
        self.geotransform = image.geotransform
        self.projection = image.projection
        self.epsg = image.epsg
        self.n_segments = n_segments
        self.compactness = compactness
        self.sigma = sigma
        self.enforce_connectivity = enforce_connectivity
        self.superpixels = self._extract_superpixels()

    def _extract_superpixels(self):
        if self.image.ndim > 2:
            multichannel = True
        else:
            multichannel = False
        segments = slic(self.image, n_segments=self.n_segments, compactness=self.compactness, sigma=self.sigma,
                        multichannel=multichannel, enforce_connectivity=self.enforce_connectivity)

        return segments
