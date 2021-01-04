from pyproj import Proj, transform
from shapely.geometry import Polygon, MultiPolygon
import mgrs
from typing import Tuple, List
import numpy as np
import geopandas as gpd
import matplotlib.pyplot as plt

WGS84_EPSG = 4326


def world_to_pixel(x: float, y: float, geotransform: "Geotransform") -> Tuple[int, int]:
    """ Transform a projected coordinates to image pixel indices"""

    x = np.round((x - geotransform.upper_left_x) / geotransform.pixel_width).astype(np.int)
    y = np.round((geotransform.upper_left_y - y) / geotransform.pixel_height).astype(np.int)

    return x, y


def pixel_to_world(x: int, y: int, geotransform: "Geotransform") -> Tuple[float, float]:
    """ Transform a pixel indices into projected coordinates"""
    x2 = (x * geotransform.pixel_width) + geotransform.upper_left_x
    y2 = geotransform.upper_left_y - (y * geotransform.pixel_height)

    return x2, y2


def transform_coordinate(x: float, y: float, in_epsg: int, out_epsg: int) -> Tuple[float, float]:
    """ Tranform a coordinate to a new coordinate system"""

    in_proj = Proj(f'epsg:{in_epsg}')
    out_proj = Proj(f'epsg:{out_epsg}')

    x2, y2 = transform(in_proj, out_proj, x, y, always_xy=True)

    return x2, y2


def get_mgrs_info(wkt_polygon: Polygon) -> Tuple[str, str, str]:

    center = wkt_polygon.centroid
    longitude, latitude = center.x, center.y

    mgrs_converter = mgrs.MGRS()
    mgrs_code = mgrs_converter.toMGRS(latitude, longitude).decode('utf-8')

    utm_code = mgrs_code[0:2]
    latitude_band = mgrs_code[2:3]
    square = mgrs_code[3:5]

    return utm_code, latitude_band, square


def vectorise_image(image: np.ndarray, levels: List[float]) -> gpd.GeoDataFrame:
    """ Converts a 2D array into a collection of polygon features"""
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
