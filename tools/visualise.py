from tools import gis
from image import Image
from image.scene import SatelliteScene
import geojson
import folium


class Visualise:
    """ Class for visualising geospatial data"""
    @staticmethod
    def image_bounds(image_list: [Image]):
        """ Display image boundary on a slippy Leaflet map
        :param image_list: A list of image objects
        :return: A Folium map instance (will display automatically in Jupyter)
        """
        unprojected_bounds = [gis.transform_polygon(image.bounds,
                                                   in_epsg=image.epsg,
                                                   out_epsg=gis.WGS84_EPSG) for image in image_list]
        geojson_bounds = [geojson.Feature(geometry=bounds) for bounds in unprojected_bounds]
        center = unprojected_bounds[0].centroid.xy
        map_window = folium.Map(location=[center[1][0], center[0][0]])
        for boundary in geojson_bounds:
            folium.GeoJson(boundary).add_to(map_window)

        return map_window

    @staticmethod
    def search_results(scene_list: [SatelliteScene]):
        """ Display a list of satellite scenes on a slippy Leaflet map
        :param scene_list: A list of satellite scene objects
        :return: A Folium map instance (will display automatically in Jupyter)
        """
        map_window = folium.Map()
        for scene in scene_list:
            scene_geojson = geojson.Feature(geometry=scene.bounds)
            folium.GeoJson(
                scene_geojson,
                style_function=lambda feature: {
                    'fillOpacity': 0,
                }).add_to(map_window)

        return map_window
