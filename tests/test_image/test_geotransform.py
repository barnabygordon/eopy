from pytest import fixture


@fixture
def geo_transform():
    from remotesensing.image.geotransform import Geotransform

    return Geotransform(
        upper_left_x=0, upper_left_y=0,
        pixel_width=0, pixel_height=0,
        rotation_x=0, rotation_y=0)


def test_from_tuple():
    from remotesensing.image.geotransform import Geotransform

    tuple = (100, 1, 0, 200, 1, 0)
    geo_transform = Geotransform.from_tuple(tuple)

    assert geo_transform.upper_left_x == tuple[0]
    assert geo_transform.upper_left_y == tuple[3]
    assert geo_transform.pixel_width == tuple[1]
    assert geo_transform.pixel_height == tuple[5]


def test_to_tuple(geo_transform):

    assert geo_transform.tuple == (geo_transform.upper_left_x, geo_transform.pixel_width,
                                   geo_transform.rotation_x, geo_transform.upper_left_y,
                                   geo_transform.rotation_y, geo_transform.pixel_height)


def test_scale(geo_transform):

    scaled = geo_transform.scale(factor=2)

    assert scaled.upper_left_x == geo_transform.upper_left_x
    assert scaled.upper_left_y == geo_transform.upper_left_y
    assert scaled.pixel_height == geo_transform.pixel_height // 2
    assert scaled.pixel_width == geo_transform.pixel_width // 2


def test_subset(geo_transform):

    subset = geo_transform.subset(x=5, y=5)

    assert subset.upper_left_x == 0
    assert subset.upper_left_y == 0
