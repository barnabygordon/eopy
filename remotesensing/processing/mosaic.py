from typing import List
import numpy as np

from remotesensing.image import Image, Geotransform
from remotesensing.tools import gis


class Mosaic:

    def mosaic(self, images: List[Image]) -> Image:

        assert len(set([image.epsg for image in images])) == 1, 'Images must have the same EPSG'
        assert len(set([image.band_count for image in images])) == 1, 'Images must have the same number of bands'
        assert len(set([image.geotransform.pixel_width for image in images])) == 1, 'Images must have the same resolution'

        base = self._construct_empty_array(images)
        geotransform = self._find_new_geotransform([image.geotransform for image in images])
        mosaic = self._paint_images_onto_base(base, images, geotransform)

        return Image(
            pixels=mosaic,
            geotransform=geotransform,
            projection=images[0].projection,
            no_data_value=images[0].no_data_value
        )

    def _paint_images_onto_base(self, base: np.ndarray, images: List[Image], geotransform: Geotransform) -> np.ndarray:

        for image in images:

            x, y = gis.world_to_pixel(image.geotransform.upper_left_x, image.geotransform.upper_left_y, geotransform)
            subset = np.full(base.shape, np.nan)
            subset[y:y + image.height, x:x + image.width] = image.pixels

            if images[0].band_count > 1:
                base = np.nanmean([subset, base], axis=0)
            else:
                base = np.nanmean([subset, base])

        return base

    def _construct_empty_array(self, images: List[Image]) -> np.ndarray:

        ulx_min = min([image.geotransform.upper_left_x for image in images])
        uly_min = min([image.geotransform.upper_left_y + image.shape[0] * image.geotransform.pixel_height for image in images])
        ulx_max = max([image.geotransform.upper_left_x + image.shape[1] * image.geotransform.pixel_width for image in images])
        uly_max = max([image.geotransform.upper_left_y for image in images])

        geotransform = self._find_new_geotransform([image.geotransform for image in images])

        _, y_min = gis.world_to_pixel(ulx_min, uly_min, geotransform)
        x_max, _ = gis.world_to_pixel(ulx_max, uly_max, geotransform)

        return np.full((y_min, x_max, images[0].band_count), np.nan)

    def _find_new_geotransform(self, geotransforms: List[Geotransform]) -> Geotransform:

        upper_left_x = min([geotransform.upper_left_x for geotransform in geotransforms])
        upper_left_y = max([geotransform.upper_left_y for geotransform in geotransforms])

        return Geotransform(
            upper_left_x=upper_left_x, upper_left_y=upper_left_y,
            pixel_width=geotransforms[0].pixel_width, pixel_height=geotransforms[0].pixel_height,
            rotation_x=geotransforms[0].rotation_x, rotation_y=geotransforms[0].rotation_y
        )
