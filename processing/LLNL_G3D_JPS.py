"""python3 script to convert the raw text files of the LLNL-G3D-JPS tomography model to a consistently formatted netCDF4 file"""

import numpy as np
import xarray as xr
import pandas as pd
from pathlib import Path
from constants import *

txt_dir = Path("processing/LLNL_G3D_JPS")

# load coordinates
coord_names = ["geodetic_lat", "lon", "lat", "slr"]
coords = pd.read_csv(txt_dir / Path("LLNL_G3D_JPS.Interpolated.Coordinates.txt"), header=None, names=coord_names, sep="\s+")
coords.drop(columns=["geodetic_lat", "slr"], inplace=True) # drop unneeded columns

# prepare to load the model
data_names = ["r", "depth", "Vp", "dVp_percent", "Vs", "dVs_percent"]
pattern = "LLNL_G3D_JPS.Interpolated.Surface*.txt"
txt_paths = list(Path(txt_dir).glob(pattern))
txt_paths.sort(key=lambda filename: int(str(filename).split(".")[3]))

# loop through the depth layers
llnl_g3g_jps = []
previous_r = None
for txt_path in txt_paths:
    layer = pd.read_csv(txt_path, header=None, names=data_names, sep="\s+")
    layer.drop(columns="depth", inplace=True) # drop depth (depth is offset from radius by about 3.6 km for some godforsaken reason)
    layer = coords.join(layer) # add coords
    r = layer["r"].mean() # get the mean radius because I really don't give a shit about the Earth being a spheroid
    # the model has some duplicate depths with different data---presumably some of these are phase transitions
    # preserve them by checking for duplicate depths and adding 100 meters to the duplicate depth so it sits just below the other one
    if r == previous_r:
        layer["r"] = (r + 0.1) * 1e3
    else:
        layer["r"] = r * 1e3
    previous_r = r
    llnl_g3g_jps.append(layer)

# join the depth layers together, reshape, and convert to `xarray.Dataset`
llnl_g3g_jps = pd.concat(llnl_g3g_jps)
llnl_g3g_jps.set_index(["r", "lat", "lon"], inplace=True)
llnl_g3g_jps = llnl_g3g_jps.to_xarray()

# add attributes
llnl_g3g_jps.attrs = {
    "id": "LLNL-G3D-JPS",
    "reference": "Simmons et al. (2015)",
    "doi": "https://doi.org/10.1002/2015GL066237",
    "source": "https://gs.llnl.gov/nuclear-threat-reduction/nuclear-explosion-monitoring/global-3d-seismic-tomography"
}
llnl_g3g_jps["r"].attrs = {
    "long_name": "radius",
    "units": "m",
    "positive": "m"
}
llnl_g3g_jps["lat"].attrs = {
    "long_name": "latitude",
    "units": "degrees"
}
llnl_g3g_jps["lon"].attrs = {
    "long_name": "longitude",
    "units": "degrees",
    "convention": "bipolar"
}
llnl_g3g_jps["Vs"].attrs = {
    "long_name": "S-wave velocity",
    "units": "km/s"
}
llnl_g3g_jps["Vp"].attrs = {
    "long_name": "P-wave velocity",
    "units": "km/s"
}
llnl_g3g_jps["dVs_percent"].attrs = {
    "long_name": "S-wave velocity perturbation",
    "units": "percent"
}
llnl_g3g_jps["dVp_percent"].attrs = {
    "long_name": "P-wave velocity perturbation",
    "units": "percent"
}

# calculate depth and add to Dataset
llnl_g3g_jps = llnl_g3g_jps.assign_coords({"depth": ("r", (earth_radius - llnl_g3g_jps["r"].data) / 1e3)})
llnl_g3g_jps["depth"] = llnl_g3g_jps["depth"].assign_attrs({
        "long_name": "depth",
        "units": "km",
        "positive": "down"
})


llnl_g3g_jps =llnl_g3g_jps.isel(lon=slice(0, -1)) # remove lon=180 since we have a value at lon=-180

ri = np.concatenate((llnl_g3g_jps["r"].data, [earth_radius])) # create radii to extrapolate to surface and cmb
llnl_g3g_jps =llnl_g3g_jps.interp(r=ri, kwargs={"fill_value": "extrapolate"}) # extrapolate

llnl_g3g_jps.to_netcdf(Path("LLNL_G3D_JPS.nc"))