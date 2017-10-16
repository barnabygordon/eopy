"""
Remote Sensing!.
"""

from codecs import open
from os.path import abspath, dirname, join
from setuptools import find_packages, setup
from remotesensing import __version__

this_dir = abspath(dirname(__file__))
with open(join(this_dir, 'README.md'), encoding='utf-8') \
        as package_readme_file:
    long_description = package_readme_file.read()


setup(
    name='remote-sensing',
    version=__version__,
    description='Remote Sensing',
    long_description=long_description,
    url='https://github.com/barnabygordon/remote-sensing',
    author='Barney Gordon',
    author_email='barney@hummingbirdtech.com',
    packages=find_packages(exclude=['docs', 'tests*']),
    install_requires=[
        'folium',
        'gdal',
        'geopandas',
        'matplotlib',
        'numpy',
        'pandas',
        'pillow',
        'scipy',
        'shapely',
        'sklearn',
        'tqdm',
    ],
    namespace_packages=['remotesensing']
)
