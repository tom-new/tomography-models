"""python3 script to convert the GLAD-M35 tomography model to a consistently formatted netCDF4 file"""

import numpy as np
import xarray as xr
from pathlib import Path
from constants import *

STW105 = xr.load_dataset(Path(__file__).parent.parent / "STW105.nc")

# load GLAD-M35 model
GLAD_M35 = xr.load_dataset(Path(__file__).parent / "GLAD_M35.nc")
for var in GLAD_M35.data_vars:
    if var == "eta":
        pass
    # convert to m/s
    GLAD_M35[var] = GLAD_M35[var] * 1e3

# standardise attributes
GLAD_M35 = GLAD_M35.rename(
    {
        "latitude": "lat",
        "longitude": "lon",
        "vsh": "Vsh",
        "vsv": "Vsv",
        "vph": "Vph",
        "vpv": "Vpv",
    }
)
GLAD_M35.attrs = {
    "id": "GLAD-M35",
    "reference": "Cui et al. (2024)",
    "doi": "https://doi.org/10.1093/gji/ggae270",
    "source": "https://doi.org/10.17611/dp/emc.2024.gladm35.1",
}
GLAD_M35["depth"].attrs = {"long_name": "depth", "units": "km", "positive": "down"}
GLAD_M35["lat"].attrs = {"long_name": "latitude", "units": "degrees"}
GLAD_M35["lon"].attrs = {
    "long_name": "longitude",
    "units": "degrees",
    "convention": "bipolar",
}
GLAD_M35["Vph"].attrs = {
    "long_name": "Horizontally polarised P-wave velocity",
    "units": "m/s",
}
GLAD_M35["Vpv"].attrs = {
    "long_name": "Vertically polarised P-wave velocity",
    "units": "m/s",
}
GLAD_M35["Vsh"].attrs = {
    "long_name": "Horizontally polarised S-wave velocity",
    "units": "m/s",
}
GLAD_M35["Vsv"].attrs = {
    "long_name": "Vertically polarised S-wave velocity",
    "units": "m/s",
}

# add isotropic Vp and Vs
# Vp is just Vpv since Vph is a derived property of Vsh
GLAD_M35["Vp"] = GLAD_M35["Vpv"]
GLAD_M35["Vp"].attrs = {
    "long_name": "Isotropic P-wave velocity",
    "units": "m/s",
}
# Vs is the Voigt average of Vsv and Vsh
GLAD_M35["Vs"] = np.sqrt(
    2 / 3 * np.square(GLAD_M35["Vsv"]) + 1 / 3 * np.square(GLAD_M35["Vsh"])
)
GLAD_M35["Vs"].attrs = {
    "long_name": "Isotropic S-wave velocity",
    "units": "m/s",
}

# add radius and make primary dim
GLAD_M35 = GLAD_M35.assign_coords(
    {"r": ("depth", earth_radius - GLAD_M35["depth"].data * 1e3)}
)
GLAD_M35["r"] = GLAD_M35["r"].assign_attrs(
    {"long_name": "radius", "units": "m", "positive": "up"}
)
GLAD_M35 = GLAD_M35.swap_dims({"depth": "r"})
GLAD_M35 = GLAD_M35.sortby("r", ascending=False)  # sort radii from cmb to surface

# remove lon=180 since we have a value at lon=-180
GLAD_M35 = GLAD_M35.isel(lon=slice(0, -1))

# calculate dlnVp and dlnVs relative to STW105
# first interpolate STW105 to GLAD_M35 radii
STW105_i = STW105.interp(r=GLAD_M35["r"].data)
# now calculate perturbations
GLAD_M35["dlnVp_percent"] = (GLAD_M35["Vp"] - STW105_i["Vp"]) / STW105_i["Vp"] * 100
GLAD_M35["dlnVs_percent"] = (GLAD_M35["Vs"] - STW105_i["Vs"]) / STW105_i["Vs"] * 100
# standardise attributes for perturbations
GLAD_M35["dlnVp_percent"].attrs = {
    "long_name": "P-wave velocity perturbation",
    "units": "percent",
}
GLAD_M35["dlnVs_percent"].attrs = {
    "long_name": "S-wave velocity perturbation",
    "units": "percent",
}

# personally I only care for the isotropic values and perturbations, so drop all the other variables
for var in GLAD_M35.data_vars:
    if var not in ["Vp", "Vs", "dlnVp_percent", "dlnVs_percent"]:
        GLAD_M35 = GLAD_M35.drop_vars(var)

# extend radius to surface and extrapolate
ri = np.concatenate(
    ([earth_radius], GLAD_M35["r"].data)
)  # create radii to extrapolate to surface and cmb
GLAD_M35 = GLAD_M35.interp(
    r=ri, method="cubic", kwargs={"fill_value": "extrapolate"}
)  # extrapolate

GLAD_M35.to_netcdf(Path(__file__).parent.parent / "GLAD_M35.nc")
