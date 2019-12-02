from pytest import fixture, raises


@fixture
def image():
    import numpy as np
    from remotesensing.image import Image, Geotransform

    return Image(
        pixels=np.zeros((10, 10, 2)),
        geotransform=Geotransform(10, 10, 2, 2, 0, 0),
        projection='')


def test_index_with_slice(image):

    subset_image = image[0:5, 0:3, 1]
    assert subset_image.width == 5
    assert subset_image.height == 3
    assert subset_image.band_count == 1
    assert subset_image.geotransform != image.geotransform


def test_index_width_x_slice(image):

    subset_image = image[0:2, :, :]

    assert subset_image.width == 2
    assert subset_image.height == image.height
    assert subset_image.band_count == image.band_count
    assert subset_image.geotransform != image.geotransform


def test_index_with_y_slice(image):

    subset_image = image[:, 0:2, :]

    assert subset_image.height == 2
    assert subset_image.width == image.width
    assert subset_image.band_count == image.band_count
    assert subset_image.geotransform != image.geotransform


def test_width(image):
    assert image.width == 10


def test_height(image):
    assert image.height == 10


def test_band_count(image):

    assert image.band_count == 2


def test_band_count_returns_1_for_single_band_image(image):

    single_band_image = image[:, :, 0]

    assert single_band_image.band_count == 1
    assert single_band_image.pixels.ndim == 2


def test_shape(image):

    assert image.shape == (10, 10, 2)


def test_dtype(image):

    assert image.dtype == 'float64'


def test_epsg(image):

    assert image.epsg is None


def test_upsample(image):

    upsampled_image = image.upsample(2)

    assert upsampled_image.width == image.width * 2
    assert upsampled_image.height == image.height * 2


def test_stack_multiple_bands(image):

    stacked_image = image.stack([image, image])

    assert stacked_image.band_count == image.band_count * 2


def test_stack_single_bands(image):

    single_band_image = image[:, :, 0]
    stacked_image = image.stack([single_band_image, single_band_image])

    assert stacked_image.band_count == 2


def test_add_index(image):

    image_with_index = image.add_index(band_1=0, band_2=1)

    assert image_with_index.band_count == image.band_count + 1


def test_add_index_raises_warning_if_image_has_only_one_band(image):

    single_band_image = image[:, :, 0]

    with raises(UserWarning):
        _ = single_band_image.add_index(band_1=0, band_2=1)


def test_get_gdal_datatype_raises_unrecognised(image):

    with raises(UserWarning):
        _ = image._get_gdal_data_type('unknown')
