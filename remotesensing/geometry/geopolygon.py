import folium
import geopandas as gpd
from shapely.geometry import Polygon

from remotesensing.tools import gis


class GeoPolygon:

    def __init__(self, polygon: Polygon, epsg: int):

        self.polygon = polygon
        self.epsg = epsg

    @classmethod
    def from_file(cls, filename: str, epsg: int) -> "GeoPolygon":

        df = gpd.read_file(filename)
        geometry = df.iloc[0].geometry

        return cls(geometry, epsg)

    @property
    def geojson(self) -> dict:

        return gpd.GeoSeries([self.polygon]).__geo_interface__

    @property
    def wgs84(self) -> "GeoPolygon":

        if self.epsg == gis.WGS84_EPSG:
            polygon = self.polygon
        else:
            polygon = gis.transform_polygon(self.polygon, in_epsg=self.epsg, out_epsg=gis.WGS84_EPSG)

        return GeoPolygon(polygon, epsg=gis.WGS84_EPSG)

    @property
    def show(self):

        center = self.wgs84.polygon.centroid.xy
        map_view = folium.Map(location=[center[1][0], center[0][0]])
        folium.GeoJson(self.wgs84.geojson).add_to(map_view)

        return map_view

    def transform(self, epsg: int) -> "GeoPolygon":

        if self.epsg == epsg:
            raise UserWarning(f'Polygon already in {epsg} EPSG')

        polygon = gis.transform_polygon(self.polygon, in_epsg=self.epsg, out_epsg=epsg)

        return GeoPolygon(polygon, epsg)
