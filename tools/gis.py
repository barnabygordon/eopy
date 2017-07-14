from pyproj import Proj, transform
from shapely.geometry import Polygon
from shapely.ops import transform as shapely_transform
from geojson import Feature
import mgrs
from functools import partial
import numpy as np
from PIL import Image as PILImage
from PIL import ImageDraw

from image.geotransform import Geotransform

WGS84_EPSG = 4326


def world_to_pixel(x: float, y: float, geotransform: Geotransform) -> (int, int):
    """ Transform a projected coordinates to image pixel indices
    :param x: easting/longitude
    :param y: northing/latitude
    :param geotransform: the geospatial properties of the image
    :return: x, y in pixel indices
    """
    x = int((x - geotransform.upper_left_x) / geotransform.pixel_width)
    y = int((y - geotransform.upper_left_y) / geotransform.pixel_width)

    return x, -y


def pixel_to_world(x: int, y: int, geotransform: Geotransform) -> (float, float):
    """ Transform a pixel indices into projected coordinates
    :param x: column
    :param y: row
    :param geotransform: the geospatial properties of the image
    :return: easting/longitude, northing/latitude
    """
    x2 = (y * geotransform.pixel_width) + geotransform.upper_left_y
    y2 = (x * geotransform.pixel_width) + geotransform.upper_left_x

    return x2, y2


def transform_coordinate(x: float, y: float, in_epsg: int, out_epsg: int) -> (float, float):
    """ Tranform a coordinate to a new coordinate system
    :param x: easting/longitude
    :param y: northing/latitude
    :param in_epsg: input EPSG code
    :param out_epsg: output EPSG code
    :return: reprojected easting/longitude, northing/latitude
    """
    in_proj = Proj(init='epsg:{}'.format(in_epsg))
    out_proj = Proj(init='epsg:{}'.format(out_epsg))

    x2, y2 = transform(in_proj, out_proj, x, y)

    return x2, y2


def transform_polygon(polygon: Polygon, in_epsg: int, out_epsg: int) -> Polygon:
    """ Transform a polygon to a new coordinate system
    :param polygon: WKT Shapely polygon
    :param in_epsg: input EPSG code
    :param out_epsg: output EPSG code
    :return: reprojected polygon
    """
    projection = partial(
        transform,
        Proj(init='epsg:{}'.format(in_epsg)),
        Proj(init='epsg:{}'.format(out_epsg)))

    return shapely_transform(projection, polygon)


def wkt_to_geojson(polygon: Polygon, properties: dict=dict) -> Feature:
    """ Convert a WKT polygon to GeoJSON """
    return Feature(geometry=polygon, properties=properties)


def clip_image(image: np.ndarray, polygon: Polygon, mask_value: float = np.nan) -> np.ndarray:
    """ Clip an image using a polygon and masking all the output values
    :param image: a 2D array
    :param polygon: a WKT, Shapely polygon in the pixel coordinates of the image
    :param mask_value: the value to be used for non-image pixels
    :return: clipped image
    """
    coordinates = np.array([(point[0], point[1]) for point in polygon.exterior.coords])

    mask_image = PILImage.new("L", (image.shape[1], image.shape[0]), 1)
    ImageDraw.Draw(mask_image).polygon(coordinates, 0)

    mask = np.array(mask_image)
    x_min, y_min = int(min(coordinates[:, 0])), int(min(coordinates[:, 1]))
    x_max, y_max = int(max(coordinates[:, 0])), int(max(coordinates[:, 1]))

    image_clip = image[y_min:y_max, x_min:x_max]
    mask_clip = mask[y_min:y_max, x_min: x_max]
    image_clip[mask_clip != 0] = mask_value

    return image_clip


def get_mgrs_info(wkt_polygon: Polygon) -> (str, str, str):
    """ Gets MGRS info for a polygon
    :param wkt_polygon: WKT Polygon
    :return: UTM Code, Latitude Band, Square
    """
    center = wkt_polygon.centroid
    longitude, latitude = center.x, center.y

    mgrs_converter = mgrs.MGRS()
    mgrs_code = mgrs_converter.toMGRS(latitude, longitude).decode('utf-8')

    utm_code = mgrs_code[0:2]
    latitude_band = mgrs_code[2:3]
    square = mgrs_code[3:5]

    return utm_code, latitude_band, square
