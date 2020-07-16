from codecs import open
from os.path import abspath, dirname, join
from setuptools import find_packages, setup
from eopy import __version__

this_dir = abspath(dirname(__file__))
with open(join(this_dir, 'README.md'), encoding='utf-8') \
        as package_readme_file:
    long_description = package_readme_file.read()


setup(
    name='eopy',
    version=__version__,
    description='Earth Observation for Python',
    long_description=long_description,
    url='https://github.com/barnabygordon/eopy',
    author='Barney Gordon',
    author_email='97gordonbe@gmail.com',
    packages=find_packages(exclude=['docs', 'tests*']),
    install_requires=[
        'folium',
        'gdal',
        'geopandas',
        'matplotlib',
        'mgrs',
        'numpy',
        'pandas',
        'pillow',
        'scipy',
        'shapely',
        'sklearn',
        'tqdm',
    ],
    namespace_packages=['eopy']
)
