# Remote Sensing

A collection of helper functions and classes to search, download and process earth observation data.

## Examples

### Enhancement

Here's an example of some basic contrast enhancement (BCET) and decorrelation
stretching (DDS) techniques applied to a Landsat-8 false colour composite. 

![alt text](https://github.com/barnabygordon/remote-sensing/blob/master/assets/enhance.png)


### Pansharpening

This library also includes the SFIM pansharpenning method,
here's an example using a Landsat-8 RGB image where the 30 m multispectral
bands are pansharpened using the 15 m panchromatic band.

![alt text](https://github.com/barnabygordon/remote-sensing/blob/master/assets/pansharpening.gif)


## Image Handling

### Searching

```python
from datetime import datetime, timedelta
from shapely.geometry import Point
from remotesensing.cloud import Searcher
from remotesensing.geometry import GeoPolygon

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
from remotesensing.cloud import Downloader
from remotesensing.image import Loader

downloader = Downloader("data")
downloader.download(scene=scene, bands=['B8'])

loader = Loader()
image = loader.load('data/LC8202024019319.tif')

print(image.shape)
>>> (15801, 15601)
```

### Stream

```python
import maptlotlib.pyplot as plt

image = downloader.stream(scene, bands=['B8'], boundary=search_boundary.transform(scene.epsg))

plt.imshow(image.pixels, cmap='Greys')
```
![alt text](https://github.com/barnabygordon/remote-sensing/blob/master/assets/stream.png)
