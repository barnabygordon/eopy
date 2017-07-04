from image import Geotransform


def world_to_pixel(x: float, y: float, geotransform: Geotransform) -> (int, int):
    x = int((x - geotransform.upper_left_x) / geotransform.pixel_width)
    y = int((y - geotransform.upper_left_y) / geotransform.pixel_width)

    return x, -y
