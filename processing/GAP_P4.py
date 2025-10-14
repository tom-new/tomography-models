"""python3 script to convert the raw text file of the GAP_P4 tomography model to a consistently formatted netCDF4 file"""

import numpy as np
import xarray as xr
from pathlib import Path
from constants import *

# data parameters from README file
nlon = 576
nlat = 288
depths = np.array(
    [
        40.0,
        64.5,
        94.0,
        129.0,
        169.0,
        214.0,
        264.0,
        319.0,
        379.0,
        444.0,
        514.5,
        590.0,
        670.5,
        756.0,
        846.5,
        942.0,
        1043.0,
        1149.0,
        1260.0,
        1376.0,
        1497.0,
        1623.5,
        1754.5,
        1890.5,
        2032.0,
        2178.5,
        2330.0,
        2486.5,
        2727.5,
    ]
)  # depth values are the midpoints of the depth bands in the readme in km
nlayers = len(depths)
radii = earth_radius - depths * 1e3

# create arrays of lons and lats
offset = (
    180 / nlat
)  # from the README, data are for middle of blocks, so need to calculate the offset
lons = np.linspace(-180, 180, num=nlon, endpoint=False) + offset / 2
lats = np.linspace(90, -90, num=nlat, endpoint=False) - offset / 2

# open the data
fpath = Path("processing/GAP_P4")
with open(fpath, "r") as f:
    dlnVp = [float(value) for line in f for value in line.split()]

# reshape data to layer x lat x lon
dlnVp = np.array(dlnVp).reshape(
    nlayers, nlat, nlon
)  # the README says that the data is ordered lon x lat x depth, so we reverse this order to "unpack" the data
dlnVp_0_180 = dlnVp[
    :, :, : int(nlon / 2)
]  # get a view of the vps array with longitudes between 0 and 180 degrees
dlnVp_180_360 = dlnVp[
    :, :, int(nlon / 2) :
]  # get a view of the vps array with longitudes between 180 and 360 degrees
dlnVp = np.concatenate(
    (dlnVp_180_360, dlnVp_0_180), axis=2
)  # make a new array where the longitudes go from -180 to 180 degrees

# set up DataArrays for primary coordinates
r = xr.DataArray(
    radii, dims="r", attrs={"long_name": "radius", "units": "m", "positive": "up"}
)
lat = xr.DataArray(
    np.linspace(90, -90, num=nlat, endpoint=False) - offset / 2,
    dims="lat",
    attrs={"long_name": "latitude", "units": "degrees"},
)
lon = xr.DataArray(
    np.linspace(-180, 180, num=nlon, endpoint=False) - offset / 2,
    dims="lon",
    attrs={"long_name": "longitude", "units": "degrees", "convention": "bipolar"},
)
# create Dataset
gap_p4 = xr.Dataset(
    data_vars={"dlnVp_percent": (["r", "lat", "lon"], dlnVp)},
    coords={"r": radii, "lat": lats, "lon": lon, "depth": ("r", depths)},
    attrs={
        "id": "GAP_P4",
        "reference": "Obayashi et al. (2013); Fukao and Obayashi (2013)",
        "doi": "https://doi.org/10.1002/2013GL057401; https://doi.org/10.1002/2013JB010466",
        "source": "http://www.godac.jamstec.go.jp/catalog/data_catalog/metadataDisp/GAP_P4?lang=en",
    },
)
# assign attributes to depth
gap_p4["depth"] = gap_p4["depth"].assign_attrs(
    {"long_name": "depth", "units": "km", "positive": "down"}
)
gap_p4["dlnVp_percent"].attrs = {
    "long_name": "P-wave velocity perturbation",
    "units": "percent",
}
gap_p4 = gap_p4.reindex(
    lat=gap_p4["lat"][::-1]
)  # reverse latitudes so that they run from -90 to 90
gap_p4 = gap_p4.reindex(
    r=gap_p4["r"][::-1]
)  # reverse radii so that they run from cmb to surface
ri = np.concatenate(
    ([cmb_radius], gap_p4["r"].data, [earth_radius])
)  # create radii to extrapolate to surface and cmb
gap_p4 = gap_p4.interp(r=ri, kwargs={"fill_value": "extrapolate"})  # extrapolate
gap_p4.to_netcdf(Path("GAP_P4.nc"))  # save to netcdf4
