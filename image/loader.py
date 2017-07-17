import os
from osgeo import gdal

from image.sensor import Landsat8
from image import Image


class Loader:
    @staticmethod
    def load_landsat8(image_folder, band_list):
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
