# Remote Sensing

A collection of helper functions and classes to search, download and process earth observation data.

## Processing Techniques

### SFIM (Smoothing Filter-Based Intensity Modulation)

An image fusion method that can be used for image pansharpening. This is based entirely on the SFIM method described by Dr. Jian Liu and Dr. Philippa Mason in their book Essential Image Processing and GIS for Remote Sensing (2007), to whom all credit goes.

Landsat-8 false colour composite, 30 m (R: 6, G: 4, B: 2):
![alt text](https://github.com/barnabygordon/remote-sensing/blob/master/assets/prepansharpened.png)

Landsat-8 false colour composite, 15 m (R: 6, G: 4, B: 2):
![alt text](https://github.com/barnabygordon/remote-sensing/blob/master/assets/pansharpened.png)

### BCET (Balanced Contrast Enhancement Technique)

A useful contrast enhancement technique for improving image visualisation. Full credit for this technique goes to Dr. Jian Liu and Dr. Philippa Mason and their book Essential Image Processing and GIS for Remote Sensing (2007) in which a detailed description of BCET can be found.

BCET removes colour bias from an image by normalising each band individually to a common range and mean.

ASTER false colour composite (R: 3, G: 2, B: 1):
![alt text](https://github.com/barnabygordon/remote-sensing/blob/master/assets/orig.png)

ASTER false colour composite (R: 3, G: 2, B: 1) + BCET:
![alt text](https://github.com/barnabygordon/remote-sensing/blob/master/assets/bcet.png)

### DDS (Direct Decorrelation Stretch)

A simple saturation technique useful for image colour enhancement. This implementation is based entirely on the method described by Dr. Jian Liu and Dr. Philippa Mason in their book Essential Image Processing and GIS for Remote Sensing (2007), to whom all credit goes.

DDS is usually best applied to imagery that has undergone a BCET stretch. A value of k can be specified to control the degree of saturation.

Below is an example of an ASTER false colour composite

BCET:
![alt text](https://github.com/barnabygordon/remote-sensing/blob/master/assets/kunene_bcet.png)
BCET + DDS (k=0.6):
![alt text](https://github.com/barnabygordon/remote-sensing/blob/master/assets/kunene_dds.png)

## Image Handling

### Searching

```python
from datetime import datetime, timedelta
from shapely.geometry import Point
from remotesensing.cloud import Searcher

latitude, longitude = 51.507351, -0.127758
search_boundary = Point((longitude, latitude)).buffer(0.1)

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
from remotesensing.tools import gis

projected_boundary = gis.transform_polygon(search_boundary, in_epsg=4326, out_epsg=32630)

image = downloader.stream(scene, ['B8'], projected_boundary)

plt.imshow(image.pixels, cmap='Greys')
```
![alt text](https://github.com/barnabygordon/remote-sensing/blob/master/assets/stream.png)
