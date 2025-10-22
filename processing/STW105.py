"""python3 script to convert the STW105 1D reference model to a usefully formatted netCDF4 file"""

import numpy as np
import xarray as xr
import pandas as pd
from pathlib import Path
from constants import *

# load 1D reference model
STW105 = pd.read_csv(Path(__file__).parent / "STW105.txt", sep=r"\s+")

# since there are non-unique radii, add a small offset to make them unique
# this allows us to use xarray as expected
radii = STW105["r"].values
# find indices of non-unique radii
_, unique_indices, counts = np.unique(radii, return_index=True, return_counts=True)
non_unique_indices = np.setdiff1d(np.arange(len(radii)), unique_indices)
# add a small offset to non-unique radii
for idx in non_unique_indices:
    radii[idx - 1] -= 0.1
    print(radii[idx - 1])
    # find next index with same radius and add offset
    radii[idx] += 0.1
    print(radii[idx])
STW105["r"] = radii

STW105["depth"] = (earth_radius - STW105["r"]) / 1e3  # add depth in km
STW105 = STW105.sort_values("depth").reset_index(drop=True)  # sort by depth
STW105["Vp"] = 2 / (1 / STW105["Vpv"] + 1 / STW105["Vph"])  # isotropic Vp
STW105["Vs"] = 2 / (1 / STW105["Vsv"] + 1 / STW105["Vsh"])  # isotropic Vs

STW105 = xr.Dataset.from_dataframe(STW105.set_index("r"))  # convert to xarray
STW105 = STW105.assign_coords(
    {"depth": ("r", STW105["depth"].data)}
)  # add depth as a coordinate

# save to netCDF4
STW105.to_netcdf(Path(__file__).parent.parent / "STW105.nc")

import matplotlib.pyplot as plt

STW105["Vp"].plot(y="depth", yincrease=False)
plt.title("STW105 P-wave velocity")
plt.xlabel("Velocity (m/s)")
plt.ylabel("Depth (km)")
plt.gca().set_ylim(2871, 0)
plt.show()
plt.close("all")
