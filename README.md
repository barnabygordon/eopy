# eopy

Earth Observation for Python. A collection of helper functions and classes to search, 
download and process earth observation data.

## Examples

### Enhancement

Here's an example of some basic contrast enhancement (BCET) and decorrelation
stretching (DDS) techniques applied to a Landsat-8 false colour composite. 

![alt text](https://github.com/barnabygordon/eopy/blob/master/assets/enhance.png)


### Pansharpening

This library also includes the SFIM pansharpenning method,
here's an example using a Landsat-8 RGB image where the 30 m multispectral
bands are pansharpened using the 15 m panchromatic band.

![alt text](https://github.com/barnabygordon/eopy/blob/master/assets/pansharpening.gif)


## Access to cloud data

### Searching

Here's an example of searching for imagery in the cloud, Landsat-8 and 
Sentinel-2 are currently supported.

```python
from datetime import datetime, timedelta
from shapely.geometry import Point
from eopy.cloud import Searcher
from eopy.geometry import GeoPolygon

latitude, longitude = 51.507351, -0.127758
search_boundary = GeoPolygon(Point((longitude, latitude)).buffer(0.1), epsg=4326)

searcher = Searcher()
scenes = searcher.search(
    search_boundary, 
    start=datetime.now() - timedelta(days=7),
    end=datetime.now()
)

print(scenes[0])
>>> <Scene: S2A_39GWH_20191122_0 | Cloud: 15.57 | Date: 2019-11-22>
```

### Downloading

```python
from eopy.cloud import Downloader
from eopy.image import Loader

downloader = Downloader("data")
downloader.download(scene=scene, bands=['B8'])

loader = Loader()
image = loader.load('data/LC8202024019319.tif')

print(image.shape)
>>> (15801, 15601)
```

### Stream

It's not always convenient to have to download a whole image if we
are only interested in a specific section. Streaming a scene at a
particular boundary is much faster than downloading the whole image
and allows us to read it directly into memory.

```python
import maptlotlib.pyplot as plt

image = downloader.stream(scene, bands=['B8'], boundary=search_boundary.transform(scene.epsg))

plt.imshow(image.pixels, cmap='Greys')
```
![alt text](https://github.com/barnabygordon/eopy/blob/master/assets/stream.png)
