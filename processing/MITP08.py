"""python3 script to convert the MITP08 tomography model to a consistently formatted netCDF4 file"""

import numpy as np
import xarray as xr
import pandas as pd
from pathlib import Path
from constants import *

df = pd.read_csv(Path(__file__).parent / "MITP08.txt", sep=r"\s+")

lats = pd.unique(df["Lat"])
lons = pd.unique(df["Long"])
depths = pd.unique(df["Depth"])

nlat, nlon, ndepth = len(lats), len(lons), len(depths)

# sanity check
assert nlat * nlon * ndepth == len(df)

# reshape
dlnVp = df["dVp"].to_numpy().reshape((nlat, nlon, ndepth), order="F")

da = xr.DataArray(
    dlnVp,
    coords={"lat": lats, "lon": lons, "depth": depths},
    dims=["lat", "lon", "depth"],
    name="dlnVp_percent",
)

ds = xr.Dataset(
    data_vars={"dlnVp_percent": da},
)

# make lon bipolar
ds = ds.assign_coords({"lon": (((ds.lon + 180) % 360) - 180)}).sortby("lon")

# extend depth range to surface and cmb
depths_ext = np.concatenate(([0], ds["depth"].data, [2891]))
ds = ds.interp(depth=depths_ext, kwargs={"fill_value": "extrapolate"})

# add attributes
ds.attrs = {
    "id": "MITP08",
    "reference": "Li et al. (2008)",
    "doi": "https://doi.org/10.1029/2007GC001806",
    "source": r"https://agupubs.onlinelibrary.wiley.com/action/downloadSupplement?doi=10.1029%2F2007GC001806&file=ggge1202-sup-0002-ds01.txt.gz",
}

ds["depth"] = ds["depth"].assign_attrs(
    {"long_name": "depth", "units": "km", "positive": "down"}
)
ds["lat"] = ds["lat"].assign_attrs({"long_name": "latitude", "units": "degrees"})
ds["lon"] = ds["lon"].assign_attrs(
    {"long_name": "longitude", "units": "degrees", "convention": "bipolar"}
)
ds["dlnVp_percent"].attrs = {
    "long_name": "P-wave velocity perturbation",
    "units": "percent",
}

# radius and make primary dim
ds = ds.assign_coords({"r": ("depth", earth_radius - ds["depth"].data * 1e3)})
ds["r"] = ds["r"].assign_attrs({"long_name": "radius", "units": "m", "positive": "up"})
ds = ds.swap_dims({"depth": "r"})

ds.to_netcdf(Path(__file__).parent.parent / "MITP08.nc")
