"""python3 script to convert the TX2019slab tomography model to a consistently formatted netCDF4 file"""

import numpy as np
import xarray as xr
from pathlib import Path
from constants import *

TX2019slab = xr.load_dataset(Path("processing/TX2019slab.nc"))

# standardise attributes
TX2019slab = TX2019slab.rename(
    {
        "latitude": "lat",
        "longitude": "lon",
        "dvs": "dlnVs_percent",
        "dvp": "dlnVp_percent",
    }
)
TX2019slab.attrs = {
    "id": "TX2019slab",
    "reference": "Lu et al. (2019)",
    "doi": "https://doi.org/10.1029/2019JB017448",
    "source": "https://doi.org/10.17611/dp/emctx2019slab",
}
TX2019slab["depth"].attrs = {"long_name": "depth", "units": "km", "positive": "down"}
TX2019slab["lat"].attrs = {"long_name": "latitude", "units": "degrees"}
TX2019slab["lon"].attrs = {
    "long_name": "longitude",
    "units": "degrees",
    "convention": "bipolar",
}
TX2019slab["dlnVs_percent"].attrs = {
    "long_name": "S-wave velocity perturbation",
    "units": "percent",
}
TX2019slab["dlnVp_percent"].attrs = {
    "long_name": "P-wave velocity perturbation",
    "units": "percent",
}

# add radius and make primary dim
TX2019slab = TX2019slab.assign_coords(
    {"r": ("depth", earth_radius - TX2019slab["depth"].data * 1e3)}
)
TX2019slab["r"] = TX2019slab["r"].assign_attrs(
    {"long_name": "radius", "units": "m", "positive": "up"}
)
TX2019slab = TX2019slab.swap_dims({"depth": "r"})
TX2019slab = TX2019slab.reindex(
    r=TX2019slab["r"][::-1]
)  # reverse radii so that they run from cmb to surface
TX2019slab = TX2019slab.isel(
    lon=slice(0, -1)
)  # remove lon=180 since we have a value at lon=-180
ri = np.concatenate(
    ([cmb_radius], TX2019slab["r"].data, [earth_radius])
)  # create radii to extrapolate to surface and cmb
TX2019slab = TX2019slab.interp(
    r=ri, kwargs={"fill_value": "extrapolate"}
)  # extrapolate
TX2019slab.to_netcdf(Path("TX2019slab.nc"))
