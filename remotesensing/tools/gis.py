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

WGS84_EPSG = 4326


def world_to_pixel(x, y, geotransform):
    """ Transform a projected coordinates to image pixel indices
    :type x: float
    :type y: float
    :type geotransform: geotransform.Geotransform
    :rtype: tuple(int, int)
    """

    x = np.round((x - geotransform.upper_left_x) / geotransform.pixel_width).astype(np.int)
    y = np.round((geotransform.upper_left_y - y) / geotransform.pixel_width).astype(np.int)

    return x, y


def pixel_to_world(x, y, geotransform):
    """ Transform a pixel indices into projected coordinates
    :type x: int
    :type y: int
    :type geotransform: geotransform.Geotransform
    :rtype: tuple(float, float)
    """
    x2 = (x * geotransform.pixel_width) + geotransform.upper_left_x
    y2 = (y * geotransform.pixel_height) + geotransform.upper_left_y

    return x2, y2


def polygon_to_pixel(polygon, geotransform):
    """ Reproject polygon coordinates to image indices
    :type polygon: shapely.geometry.Polygon
    :type geotransform: geotransform.Geotransform
    :rtype: shapely.geometry.Polygon
    """
    if polygon.geom_type == 'Polygon':
        exterior = [world_to_pixel(x, y, geotransform) for x, y, in polygon.exterior.coords]
        if len(polygon.interiors) > 0:
            interior = [[world_to_pixel(x, y, geotransform) for x, y, in interior.coords]
                        for interior in polygon.interiors]

            return Polygon(exterior, interior)
        else:
            return Polygon(exterior)
    elif polygon.geom_type == 'MultiPolygon':
        return MultiPolygon([polygon_to_pixel(sub_polygon, geotransform) for sub_polygon in polygon])

    else:
        raise UserWarning("polygon has an unexpected type.")


def polygon_to_world(polygon, geotransform):
    """
    :type polygon: shapely.geometry.Polygon
    :type geotransform: geotransform.Geotransform
    :rtype: shapely.geometry.Polygon
    """

    x, y = polygon.exterior.xy
    points = [pixel_to_world(x, y, geotransform) for x, y in zip(x, y)]
    return Polygon(points)


def transform_coordinate(x, y, in_epsg, out_epsg):
    """ Tranform a coordinate to a new coordinate system
    :type x: float
    :type y: float
    :type in_epsg: int
    :type out_epsg: int
    :rtype: tuple(float, float)
    """
    in_proj = Proj(init='epsg:{}'.format(in_epsg))
    out_proj = Proj(init='epsg:{}'.format(out_epsg))

    x2, y2 = transform(in_proj, out_proj, x, y)

    return x2, y2


def transform_polygon(polygon, in_epsg, out_epsg):
    """ Transform a polygon to a new coordinate system
    :type polygon: shapely.geometry.Polygon
    :type in_epsg: int
    :type out_epsg: int
    :rtype: shapely.geometry.Polygon
    """
    projection = partial(
        transform,
        Proj(init='epsg:{}'.format(in_epsg)),
        Proj(init='epsg:{}'.format(out_epsg)))

    return shapely_transform(projection, polygon)


def wkt_to_geojson(polygon, properties=dict):
    """
    :type polygon: shapely.geometry.Polygon
    :type properties: dict
    :rtype: geojson.Feature
    """
    """ Convert a WKT polygon to GeoJSON """
    return Feature(geometry=polygon, properties=properties)


def clip_image(image, polygon, mask_value=np.nan):
    """ Clip and image using a polygon
    :type image: image.Image
    :type polygon: shapely.geometry.Polygon
    :type mask_value: float
    :rtype: image.Image
    """

    bounds = [int(value) for value in polygon.bounds]
    mask_image = PILImage.new("L", (image.height, image.width), 1)
    polygon_coords_list = _get_polygon_coords(polygon)

    [ImageDraw.Draw(mask_image).polygon(polygon_coords, 0) for polygon_coords in polygon_coords_list]
    mask = np.array(mask_image)
    mask = mask[bounds[1]:bounds[3], bounds[0]:bounds[2]]

    subset = image.subset(bounds[0], bounds[1], bounds[2] - bounds[0], bounds[3] - bounds[1])
    subset.pixels = np.copy(subset.pixels)
    subset.pixels[mask != 0] = mask_value

    return subset


def _get_polygon_coords(polygon):
    """
    :type polygon: shapely.geometry.Polygon
    :rtype: List[List[float]]
    """

    if polygon.geom_type == 'MultiPolygon':
        return [list(sub_polygon.exterior.coords) for sub_polygon in polygon]

    else:
        return [list(polygon.exterior.coords)]


def get_mgrs_info(wkt_polygon):
    """
    :type wkt_polygon: shapely.geometry.Polygon
    :rtype: tuple(str, str, str)
    """

    center = wkt_polygon.centroid
    longitude, latitude = center.x, center.y

    mgrs_converter = mgrs.MGRS()
    mgrs_code = mgrs_converter.toMGRS(latitude, longitude).decode('utf-8')

    utm_code = mgrs_code[0:2]
    latitude_band = mgrs_code[2:3]
    square = mgrs_code[3:5]

    return utm_code, latitude_band, square


def vectorise_image(image, levels):
    """ Converts a 2D array into a collection of polygon features
    :type image: numpy.ndarray
    :type levels: list[float]
    :rtype: geopandas.GeoDataFrame
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
