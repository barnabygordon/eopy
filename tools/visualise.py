from tools import gis
from image import Image
import geojson
import folium


class Visualise:
    @staticmethod
    def image_bounds(image: Image):
        unprojected_bounds = gis.transform_polygon(image.bounds,
                                                   in_epsg=image.epsg,
                                                   out_epsg=gis.WGS84_EPSG)
        geojson_bounds = geojson.Feature(geometry=unprojected_bounds)
        center = unprojected_bounds.centroid.xy
        map_window = folium.Map(location=[center[1][0], center[0][0]])
        folium.GeoJson(geojson_bounds).add_to(map_window)

        return map_window
