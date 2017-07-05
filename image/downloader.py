from osgeo import gdal

from image import LandsatSceneID
from image import Image

LANDSAT_8_BANDS = [
    'coastal', 'blue', 'green', 'red', 'nir', 'swir_1',
    'swir_2', 'pan', 'cirrus', 'tirs_1', 'tirs_2']
LANDSAT_8_LOOKUP_BAND = {
    'coastal': 'B1', 'blue': 'B2', 'green': 'B3', 'red': 'B4',
    'nir': 'B5', 'swir_1': 'B6', 'swir_2': 'B7', 'pan': 'B8',
    'cirrus': 'B9', 'tirs_1': 'B10', 'tirs_2': 'B11'}


class Downloader:
    def download_landsat8_band(self, scene_id: LandsatSceneID, band):
        url = 'https://landsat-pds.s3.amazonaws.com/L8/{path}/{row}/{scene_id}/{scene_id}_{band}.TIF'.format(
            path=scene_id.path,
            row=scene_id.row,
            band=LANDSAT_8_LOOKUP_BAND[band],
            scene_id=scene_id.string)

        image_dataset = gdal.Open('/vsicurl/{}'.format(url))

        return Image(image_dataset)
