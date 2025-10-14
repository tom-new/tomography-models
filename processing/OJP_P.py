"""python3 script to convert the raw text file of the OJP_P tomography model to netCDF4"""

import numpy as np
import xarray as xr
from pathlib import Path
from constants import *

# data parameters from README file
nlon = 288
nlat = 144
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
fpath = Path("processing/OJP_P")
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
ojp_p = xr.Dataset(
    data_vars={"dlnVp_percent": (["r", "lat", "lon"], dlnVp)},
    coords={"r": radii, "lat": lats, "lon": lon, "depth": ("r", depths)},
    attrs={
        "id": "OJP_P",
        "reference": "Obayashi et al. (2021)",
        "doi": "https://doi.org/10.1038/s41598-021-99833-5",
        "source": "personal communication",
    },
)
# assign attributes to depth
ojp_p["depth"] = ojp_p["depth"].assign_attrs(
    {"long_name": "depth", "units": "km", "positive": "down"}
)
ojp_p["dlnVp_percent"].attrs = {
    "long_name": "P-wave velocity perturbation",
    "units": "percent",
}
ojp_p = ojp_p.reindex(
    lat=ojp_p["lat"][::-1]
)  # reverse latitudes so that they run from -90 to 90
ojp_p = ojp_p.reindex(
    r=ojp_p["r"][::-1]
)  # reverse radii so that they run from cmb to surface
ri = np.concatenate(
    ([cmb_radius], ojp_p["r"].data, [earth_radius])
)  # create radii to extrapolate to surface and cmb
ojp_p = ojp_p.interp(r=ri, kwargs={"fill_value": "extrapolate"})  # extrapolate
ojp_p.to_netcdf(Path("ojp_p.nc"))  # save to netcdf4
