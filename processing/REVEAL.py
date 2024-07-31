"""python3 script to convert the REVEAL tomography model to a consistently formatted netCDF4 file"""

import numpy as np
import xarray as xr
from pathlib import Path
from constants import *

reveal = xr.load_dataset(Path("processing/REVEAL.nc"))

# standardise attributes
reveal = reveal.rename({
        "latitude": "lat",
        "longitude": "lon",
        "vsv": "Vsv",
        "vsh": "Vsh",
        "vpv": "Vp"
})
reveal.attrs = {
    "id": "REVEAL",
    "reference": "Thrastarson et al. (2024)",
    "doi": "https://doi.org/10.1785/0120230273",
    "source": "https://doi.org/10.17611/dp/emc.2024.reveal.1"
}
reveal["depth"].attrs = {
    "long_name": "depth",
    "units": "km",
    "positive": "down"
}
reveal["lat"].attrs = {
    "long_name": "latitude",
    "units": "degrees"
}
reveal["lon"].attrs = {
    "long_name": "longitude",
    "units": "degrees",
    "convention": "bipolar"
}
reveal["Vsv"].attrs = {
    "long_name": "SV-wave velocity",
    "units": "km/s"
}
reveal["Vsh"].attrs = {
    "long_name": "SH-wave velocity",
    "units": "km/s"
}
reveal["Vp"].attrs = {
    "long_name": "P-wave velocity",
    "units": "km/s"
}
reveal["rho"].attrs = {
    "long_name": "density",
    "units": "kg/m^3"
}

# add radius and make primary dim
reveal = reveal.assign_coords({"r": ("depth", earth_radius - reveal["depth"].data * 1e3)})
reveal["r"] = reveal["r"].assign_attrs({
        "long_name": "radius",
        "units": "m",
        "positive": "up"
})
reveal = reveal.swap_dims({"depth": "r"})
reveal = reveal.reindex(r=reveal["r"][::-1]) # reverse radii so that they run from cmb to surface

# calculate S- and P-wave perturbations
mean = reveal.mean(dim=["lat", "lon"])
dVsv_percent = xr.DataArray(
    100 * (reveal["Vsv"] - mean["Vsv"]) / mean["Vsv"],
    attrs={
        "long_name": "SV-wave velocity perturbation",
        "units": "percent"
    }
)
dVsh_percent = xr.DataArray(
    100 * (reveal["Vsh"] - mean["Vsh"]) / mean["Vsh"],
    attrs={
        "long_name": "SH-wave velocity perturbation",
        "units": "percent"
    }
)
dVp_percent = xr.DataArray(
    100 * (reveal["Vp"] - mean["Vp"]) / mean["Vp"],
    attrs={
        "long_name": "P-wave velocity perturbation",
        "units": "percent"
    }
)
# add to Dataset
reveal = reveal.assign({
    "dVsh_percent": dVsh_percent,
    "dVsv_percent": dVsv_percent,
    "dVp_percent": dVp_percent,
})


reveal = reveal.isel(lon=slice(0, -1)) # remove lon=180 since we have a value at lon=-180

reveal.to_netcdf(Path("reveal.nc"))