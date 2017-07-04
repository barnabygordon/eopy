# Remote Sensing

A collection of helper functions and classes to read, process and save geospatial data.

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
