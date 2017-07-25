from tools import gis
from image import Image
from image.scene import LandsatScene
import geojson
import folium


class Visualise:
    """ Class for visualising geospatial data"""
    @staticmethod
    def image_bounds(image: Image):
        """ Display image boundary on a slippy Leaflet map
        :param image: An image object
        :return: A Folium map instance (will display automatically in Jupyter)
        """
        unprojected_bounds = gis.transform_polygon(image.bounds,
                                                   in_epsg=image.epsg,
                                                   out_epsg=gis.WGS84_EPSG)
        geojson_bounds = geojson.Feature(geometry=unprojected_bounds)
        center = unprojected_bounds.centroid.xy
        map_window = folium.Map(location=[center[1][0], center[0][0]])
        folium.GeoJson(geojson_bounds).add_to(map_window)

        return map_window

    @staticmethod
    def search_results(scene_list: [LandsatScene]):
        map_window = folium.Map()
        for scene in scene_list:
            scene_geojson = geojson.Feature(geometry=scene.bounds)
            folium.GeoJson(scene_geojson).add_to(map_window)

        return map_window
