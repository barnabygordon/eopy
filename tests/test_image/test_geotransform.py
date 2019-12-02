from pytest import fixture


@fixture
def geotransform():
    from remotesensing.image.geotransform import Geotransform

    return Geotransform(
        upper_left_x=0, upper_left_y=0,
        pixel_width=0, pixel_height=0,
        rotation_x=0, rotation_y=0)


def test_from_tuple():
    from remotesensing.image.geotransform import Geotransform

    tuple = (100, 1, 0, 200, 1, 0)
    geotransform = Geotransform.from_tuple(tuple)

    assert geotransform.upper_left_x == tuple[0]
    assert geotransform.upper_left_y == tuple[3]
    assert geotransform.pixel_width == tuple[1]
    assert geotransform.pixel_height == tuple[5]


def test_to_tuple(geotransform):

    assert geotransform.tuple == (geotransform.upper_left_x, geotransform.pixel_width,
                                  geotransform.rotation_x, geotransform.upper_left_y,
                                  geotransform.rotation_y, geotransform.pixel_height)


def test_scale(geotransform):

    scaled = geotransform.scale(factor=2)

    assert scaled.upper_left_x == geotransform.upper_left_x
    assert scaled.upper_left_y == geotransform.upper_left_y
    assert scaled.pixel_height == geotransform.pixel_height // 2
    assert scaled.pixel_width == geotransform.pixel_width // 2


def test_subset(geotransform):

    subset = geotransform.subset(x=5, y=5)

    assert subset.upper_left_x == 0
    assert subset.upper_left_y == 0
