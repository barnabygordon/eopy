import folium
from pyproj import Transformer
from shapely.ops import transform as shapely_transform
import geopandas as gpd
from typing import List
from shapely.geometry import Polygon, MultiPolygon

from eopy.tools import gis
from eopy.image import Geotransform


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
            polygon = self.transform(gis.WGS84_EPSG)

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

        project = Transformer.from_crs(self.epsg, epsg, always_xy=True).transform

        return GeoPolygon(shapely_transform(project, self.polygon), epsg)

    def to_pixel(self, geo_transform: "Geotransform") -> "GeoPolygon":
        """ Reproject polygon coordinates to image indices"""

        if self.polygon.geom_type == 'Polygon':
            exterior = [gis.world_to_pixel(x, y, geo_transform) for x, y, in self.polygon.exterior.coords]
            if len(self.polygon.interiors) > 0:
                interior = [[gis.world_to_pixel(x, y, geo_transform) for x, y, in interior.coords]
                            for interior in self.polygon.interiors]

                return GeoPolygon(Polygon(exterior, interior), self.epsg)
            else:
                return GeoPolygon(Polygon(exterior), self.epsg)
        elif self.polygon.geom_type == 'MultiPolygon':

            multi_polygon = MultiPolygon([GeoPolygon(sub_polygon, self.epsg).to_pixel(geo_transform).polygon for sub_polygon in self.polygon])
            return GeoPolygon(multi_polygon, self.epsg)
        else:
            raise UserWarning("polygon has an unexpected type.")

    def to_world(self, geo_transform: "Geotransform") -> "GeoPolygon":

        x, y = self.polygon.exterior.xy
        points = [gis.pixel_to_world(x, y, geo_transform) for x, y in zip(x, y)]

        return GeoPolygon(Polygon(points), self.epsg)

    @property
    def coordinates(self) -> List[List[float]]:

        if self.polygon.geom_type == 'MultiPolygon':
            return [list(sub_polygon.exterior.coords) for sub_polygon in self.polygon]
        else:
            return [list(self.polygon.exterior.coords)]

    def buffer(self, distance: int) -> "GeoPolygon":

        return GeoPolygon(self.polygon.buffer(distance), self.epsg)
