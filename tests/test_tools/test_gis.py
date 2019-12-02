from pytest import fixture

from remotesensing.tools import gis


@fixture
def geotransform():
    from remotesensing.image.geotransform import Geotransform

    return Geotransform(
        upper_left_x=100, upper_left_y=100,
        pixel_width=10, pixel_height=10,
        rotation_x=0, rotation_y=0)


def test_world_to_pixel(geotransform):

    x, y = gis.world_to_pixel(x=120, y=80, geotransform=geotransform)

    assert x == 2
    assert y == 2


def test_pixel_to_world(geotransform):

    x, y = gis.pixel_to_world(x=2, y=2, geotransform=geotransform)

    assert x == 120
    assert y == 120
