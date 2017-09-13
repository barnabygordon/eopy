from pyproj import Proj, transform
from shapely.geometry import Polygon, MultiPolygon
from shapely.ops import transform as shapely_transform
from geojson import Feature
import mgrs
from functools import partial
import numpy as np
import geopandas as gpd
import matplotlib.pyplot as plt
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

    x = np.round((x - geotransform.upper_left_x) / geotransform.pixel_width).astype(np.int)
    y = np.round((geotransform.upper_left_y - y) / geotransform.pixel_width).astype(np.int)

    return x, y


def pixel_to_world(x: int, y: int, geotransform: Geotransform) -> (float, float):
    """ Transform a pixel indices into projected coordinates
    :param x: column
    :param y: row
    :param geotransform: the geospatial properties of the image
    :return: easting/longitude, northing/latitude
    """
    x2 = (x * geotransform.pixel_width) + geotransform.upper_left_x
    y2 = (y * geotransform.pixel_height) + geotransform.upper_left_y

    return x2, y2


def polygon_to_pixel(polygon, geotransform):
    """ Reproject polygon coordinates to image indices
    :param polygon: Shapely polygon projected in the image projection
    :param geotransform: Image geotransform
    :return: Polygon with coordinates in pixel indices
    """
    if polygon.geom_type == 'Polygon':
        return Polygon([world_to_pixel(x, y, geotransform) for x, y, in polygon.exterior.coords])
    elif polygon.geom_type == 'MultiPolygon':
        return MultiPolygon([polygon_to_pixel(sub_polygon, geotransform) for sub_polygon in polygon])

    else:
        raise UserWarning("polygon has an unexpected type.")


def polygon_to_world(polygon, geotransform):
    x, y = polygon.exterior.xy
    points = [pixel_to_world(x, y, geotransform) for x, y in zip(x, y)]
    return Polygon(points)


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


def clip_image(image, polygon: Polygon, mask_value: float=np.nan):
    """ Clip and image using a polygon
    :param image: Image object
    :param polygon: Shapely polygon object
    :param mask_value: Non-image value
    :return:
    """
    polygon_coords = list(polygon.exterior.coords)
    bounds = [int(value) for value in polygon.bounds]

    mask_image = PILImage.new("L", (image.height, image.width), 1)
    ImageDraw.Draw(mask_image).polygon(polygon_coords, 0)
    mask = np.array(mask_image)
    mask = mask[bounds[1]:bounds[3], bounds[0]:bounds[2]]

    subset = image.subset(bounds[0], bounds[1], bounds[2] - bounds[0], bounds[3] - bounds[1])
    subset.pixels = np.copy(subset.pixels)
    subset.pixels[mask != 0] = mask_value

    return subset


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


def vectorise_image(image: np.ndarray, levels: [float]) -> gpd.GeoDataFrame:
    """ Converts a 2D array into a collection of polygon features
    :param image: 2D array
    :param levels: The value intervals where polygons should be drawn (adjust for binary output)
    :return: Geopandas dataframe acting as a feature collection
    """
    contour_collection = plt.contourf(
        image,
        levels=levels)
    plt.close()

    contour_polygons = []
    for i, contour in enumerate(contour_collection.collections):
        path_polygons = []
        for path in contour.get_paths():
            path.should_simplify = False
            polygon = path.to_polygons()

            holes, exterior = [], []
            if len(polygon) > 0 and len(polygon[0]) > 3:
                exterior = polygon[0]
                if len(polygon) > 1:
                    holes = [h for h in polygon[1:] if len(h) > 3]

            if len(exterior) > 3:
                path_polygons.append(Polygon(exterior, holes))

            if len(path_polygons) > 1:
                contour_polygons.append(MultiPolygon(path_polygons))
            elif len(path_polygons) == 1:
                contour_polygons.append(path_polygons[0])

    return gpd.GeoDataFrame(contour_polygons, columns=['geom'], geometry='geom')
