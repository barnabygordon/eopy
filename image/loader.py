import os
import numpy as np

from osgeo import gdal

from image import Image
from image.geotransform import Geotransform
from image.sensor import Landsat8


class Loader:
    """ For loading imagery locally from standardised folder structures """
    @classmethod
    def load_landsat8(cls, image_folder: str, band_list: [str]) -> Image:
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
        for i, band in enumerate(band_list):
            file_name = [file for file in file_list if 'B{}.TIF'.format(landsat8.band_number(band)) in file][0]
            filepath = os.path.join(image_folder, file_name)
            images.append(Image.load(filepath, band_labels={band: i+1}))

        if len(images) > 1:
            return Image.stack(images)
        else:
            return images[0]

    @classmethod
    def load_aster_hdf(cls, filename: str) -> (Image, Image, Image):
        aster_vnir_labels = [
            'VNIR_Swath:ImageData1', 'VNIR_Swath:ImageData2', 'VNIR_Swath:ImageData3N']
        aster_swir_labels = [
            'SWIR_Swath:ImageData4', 'SWIR_Swath:ImageData5', 'SWIR_Swath:ImageData6',
            'SWIR_Swath:ImageData7', 'SWIR_Swath:ImageData8', 'SWIR_Swath:ImageData9']
        aster_tir_labels = [
            'TIR_Swath:ImageData10', 'TIR_Swath:ImageData11', 'TIR_Swath:ImageData12',
            'TIR_Swath:ImageData13', 'TIR_Swath:ImageData14']

        hdf_dataset = gdal.Open(filename)
        subdataset = [subdataset[0] for subdataset in hdf_dataset.GetSubDatasets()]

        vnir, swir, tir = [cls.build_aster_image(labels, subdataset) for labels in
                           [aster_vnir_labels, aster_swir_labels, aster_tir_labels]]

        return vnir, swir, tir

    @staticmethod
    def build_aster_image(subdataset_labels, subdataset_list):
        image_list = []
        for label in subdataset_labels:
            subdataset = [subdataset for subdataset in subdataset_list if label in subdataset][0]
            image_dataset = gdal.Open(subdataset)
            geotransform = Geotransform(image_dataset.GetGeoTransform())
            projection = image_dataset.GetProjection()
            image_list.append(image_dataset.ReadAsArray())

        image_array = np.array(image_list).transpose(1, 2, 0)
        return Image(image_array, geotransform, projection)
