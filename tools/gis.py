from image import Geotransform


def world_to_pixel(x: float, y: float, geotransform: Geotransform) -> (int, int):
    x = int((x - geotransform.upper_left_x) / geotransform.pixel_width)
    y = int((y - geotransform.upper_left_y) / geotransform.pixel_width)

    return x, -y


def pixel_to_world(x: int, y: int, geotransform: Geotransform) -> (float, float):
    x2 = (y * geotransform.pixel_width) + geotransform.upper_left_y
    y2 = (x * geotransform.pixel_width) + geotransform.upper_left_x

    return x2, y2
