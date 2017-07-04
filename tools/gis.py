from image import Geotransform
from pyproj import Proj, transform
from shapely.geometry import Polygon
from shapely.ops import transform as shapely_transform
from geojson import Feature
from functools import partial
import numpy as np
from PIL import Image as PILImage
from PIL import ImageDraw

WGS84_EPSG = 4326


def world_to_pixel(x: float, y: float, geotransform: Geotransform) -> (int, int):
    x = int((x - geotransform.upper_left_x) / geotransform.pixel_width)
    y = int((y - geotransform.upper_left_y) / geotransform.pixel_width)

    return x, -y


def pixel_to_world(x: int, y: int, geotransform: Geotransform) -> (float, float):
    x2 = (y * geotransform.pixel_width) + geotransform.upper_left_y
    y2 = (x * geotransform.pixel_width) + geotransform.upper_left_x

    return x2, y2


def transform_coordinate(x: float, y: float, in_epsg: int, out_epsg: int) -> (float, float):
    in_proj = Proj(init='epsg:{}'.format(in_epsg))
    out_proj = Proj(init='epsg:{}'.format(out_epsg))

    x2, y2 = transform(in_proj, out_proj, x, y)

    return x2, y2


def transform_polygon(polygon: Polygon, in_epsg: int, out_epsg: int) -> Polygon:
    projection = partial(
        transform,
        Proj(init='epsg:{}'.format(in_epsg)),
        Proj(init='epsg:{}'.format(out_epsg)))

    return shapely_transform(projection, polygon)


def wkt_to_geojson(polygon: Polygon, properties: dict=dict) -> Feature:
    return Feature(geometry=polygon, properties=properties)


def clip_image(image: np.ndarray, polygon: Polygon) -> np.ndarray:
    coordinates = np.array([(point[0], point[1]) for point in polygon.exterior.coords])

    mask_image = PILImage.new("L", (image.shape[1], image.shape[0]), 1)
    ImageDraw.Draw(mask_image).polygon(coordinates, 0)

    mask = np.array(mask_image)
    x_min, y_min = int(min(coordinates[:, 0])), int(min(coordinates[:, 1]))
    x_max, y_max = int(max(coordinates[:, 0])), int(max(coordinates[:, 1]))

    image_clip = image[y_min:y_max, x_min:x_max]
    mask_clip = mask[y_min:y_max, x_min: x_max]
    image_clip[mask_clip != 0] = np.nan

    return image_clip
