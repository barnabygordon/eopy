import os
from osgeo import gdal

from image.sensor import Landsat8
from image import Image


class Loader:
    """ For loading imagery locally from standardised folder structures """
    @staticmethod
    def load_landsat8(image_folder: str, band_list: [str]) -> Image:
        """ Load landsat-8 imagery from USGS Earthexplorer download folder
        :param image_folder: Path to the folder containing image bands
        :param band_list: List of bands to be loaded
        :return: A stacked Image object of the requested bands
        """
        landsat8 = Landsat8()
        resolutions = [landsat8.band_resolution(band) for band in band_list]
        assert len(set(resolutions)) == 1, "All bands must have the same resolution."

        file_list = os.listdir(image_folder)
        images = []
        for band in band_list:
            landsat8.band_number(band)
            file_name = [file for file in file_list if 'B{}.TIF'.format(landsat8.band_number(band)) in file][0]
            filepath = os.path.join(image_folder, file_name)

            images.append(Image(gdal.Open(filepath)))

        stack, image_dataset = Image.stack(images)
        save_path = os.path.join(image_folder, 'LS8_{}.tif'.format(''.join(band_list)))
        Image.save(stack, image_dataset, filepath=save_path)

        return Image(gdal.Open(save_path))
