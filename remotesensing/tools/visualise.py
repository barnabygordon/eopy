import folium
import matplotlib.pyplot as plt
from typing import List, Tuple
from PIL import Image as PILImage
from shapely.geometry import Polygon
import numpy as np

from remotesensing.cloud.scene import Scene
from remotesensing.classify.superpixel import Superpixels


def search_results(scene_list: List[Scene]) -> folium.Map:

    map_window = folium.Map()
    for scene in scene_list:
        folium.GeoJson(
            scene.polygon.geojson,
            style_function=lambda feature: {
                'fillOpacity': 0,
            }).add_to(map_window)

    return map_window


def save_pyplot(image: np.ndarray, filepath: str, width_in_pixels: int, height_in_pixels: int, dpi: int = 72):

    f = plt.figure(frameon=False, dpi=dpi)
    f.set_size_inches(width_in_pixels/dpi, height_in_pixels/dpi)

    ax = plt.Axes(f, [0., 0., 1., 1.])
    ax.set_axis_off()
    f.add_axes(ax)

    ax.imshow(image, aspect='normal')
    f.savefig(filepath, dpi=dpi)


def show_3d_surface(image: "Image", figsize: Tuple[int, int] = (15, 10), rstride: int = 100, cstride: int = 100, cmap: str = 'jet'):

    if image.band_count > 1:
        raise UserWarning("Image must be 2D")

    yy, xx = np.mgrid[0:image.height, 0:image.width]

    f = plt.figure(figsize=figsize)
    ax = f.gca(projection='3d')

    ax.plot_surface(xx, yy, image.pixels, rstride=rstride, cstride=cstride, cmap=cmap, linewidth=0)
    plt.show()


def show_superpixel_spectra(superpixels: Superpixels):
    """ Plot the average spectra for each superpixel cluster """
    plt.figure(figsize=(15, 10))

    for cluster in superpixels.gdf.cluster.unique():
        features = np.stack(superpixels.gdf.loc[superpixels.gdf.cluster == cluster].features.tolist())
        mean = np.nanmean(features, axis=0)
        std = np.nanmean(features, axis=0)

        plt.plot(mean, label=cluster)
        plt.fill_between([x for x in range(len(mean))], mean-std, mean=std, alpha=0.2)

    plt.legend()
    plt.show()


def show_image_and_polygon(image: "Image", polygon: Polygon):

    x, y = polygon.exterior.xy

    plt.figure(figsize=(15, 10))
    plt.imshow(image.pixels)
    plt.plot(x, y)
    plt.show()


def create_giphy(file_paths: List[str], save_path: str, duration: int = 200):

    image, *images = [PILImage.open(file_path) for file_path in file_paths]
    image.save(fp=save_path, format='GIF', append_images=images, save_all=True, duration=duration, loop=0)


def show_histogram(image: "Image", range: Tuple[float, float] = None):

    plt.figure(figsize=(10, 5))
    for i, band in enumerate(image):
        values = band.pixels.ravel()
        if range:
            plt.hist(values[~np.isnan(values)], bins=100, alpha=0.5, label=f'Band {i}', range=range)
        else:
            plt.hist(values[~np.isnan(values)], bins=100, alpha=0.5, label=f'Band {i}')
    plt.legend()
    plt.show()
