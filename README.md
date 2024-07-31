# Seismic Tomography Models

This repository contains several seismic tomography models as netCDF4 files, saved in a consistent _and useful_ radius-lat-lon format for plotting cross-sections and basemaps with Matplotlib.

## Format

The format used in this repository is loosely based on the format used by the [Seismological Facility for the Advancement of Geoscience](https://www.iris.edu/hq/) (SAGE):

* Dimensions of the netCDF file are radial, latitude, longitude.
* The geographic coordinates have units of degrees North and East respectively.
* The longitudinal coordinates use a bipolar convention (with a twist, see below).

However, there are also some key differences:

* The radial dimension is actually the radius (in meters), and depth in kilometers is an additional dimension.
* Where it is reasonable[^1], tomography models have been radially extrapolated to the surface and core-mantle boundary.
* Longitude ranges from $-180$ _up to but not including_ $+180$ degrees, primarily because this resolves many issues when converting from bipolar to positive (from $0$ _up to but not including_ $360$ degrees).
* The longitude dimension contains a `'convention'` attribute, which tracks whether the longitude is in bipolar or positive format[^2].
* Data variables have more meaningful names (e.g. if P-wave velocity perturbation is in %, it's called `dVp_percent`)
* Significantly less information is stored in the top level attributes of the netCDF4 files&mdash;some have been dropped entirely (e.g. full author lists) while others have been moved to the appropriate secondary level (e.g. units for dimensions are now attributes of those dimensions).

## Processing

The _`processing`_ folder contains the Python scripts that convert the source files into the format used in this repository. These scripts may require some combination of the following libraries: `numpy`, `xarray`, and `pandas`.

## Plotting

The _`plotting`_ folder contains an example script[^3] for plotting a radial cross-section, given two arbitrary geographic coordinate pairs. This depends on the `spherical.py` file, containing functions which are useful for computing things in spherical coordinate systems.

Obviously you can use any language/libraries you wish, but the example plotting script in this repository is for Python 3 and requires the `numpy`, `scipy`, `xarray`, `cmcrameri`, `cartopy`, and, of course, `matplotlib` libraries, as well as a $\LaTeX$ installation with the `amsmath` and `siunitx` packages. (If you don't already use $\LaTeX$ for typesetting your plots, you should!)

A big motivation for me to develop this workflow was my stubbornness to avoid using GMT or PyGMT. Since I was already very familiar with Matplotlib and using it for ordinary scientific plots, once I started working with geoscientific data I would either have to transition _all_ my plotting to GMT, or learn how to do geoscientific plots with Matplotlib if I wanted my plots to look consistent (which I did). Unfortunately, a lot of things that are easy to do with GMT require a bit more effort to achieve in practice with Matplotlib, most notably, cross-sections. Matplotlib was just never designed with plotting heatmaps on circular sectors in mind, and it's not something many people are doing (they're mostly doing it with GMT).

## Data sources

Every tomography model has its respective journal article(s) and download link saved as an attribute in its netCDF4 file, which in Python may be accessed using `xarray` (`SciPy` does not support netCDF4).

[^1]: I.e., in the cases where the the shallowest depth is a few tens of kilometers from the surface or the deepest depth is a couple of hundred kilometers from the core-mantle boundary.
[^2]: In a future version, which will be Soon&trade;, this will change from `'convention'` to `'antimeridian'`, which will track the location of the antimeridian such that a global basemap can be plot centred on any meridian.
[^3]: Soon&trade; it will also have one for a [spherical quadrilateral](https://en.wikipedia.org/wiki/Spherical_trigonometry#Spherical_polygons) (or basemap), given four geographic coordinate pairs which are joined by great circles.
