"""python3 script to convert the raw text file of the OJP_P tomography model to netCDF4"""

import numpy as np
import xarray as xr
from pathlib import Path

# data parameters from README file
nlon = 288
nlat = 144
depths = np.array([40. , 64.5, 94. , 129. , 169. , 214. , 264. , 319. ,  379. , 444. , 514.5, 590. , 670.5, 756. , 846.5, 942. , 1043. , 1149. , 1260. , 1376. , 1497. , 1623.5, 1754.5, 1890.5, 2032. , 2178.5, 2330. , 2486.5, 2727.5]) # depth values are the midpoints of the depth bands in the readme in km
nlayers = len(depths)
radii = 6371e3 - depths * 1e3

# create arrays of lons and lats
offset = 180 / nlat # from the README, data are for middle of blocks, so need to calculate the offset
lons = np.linspace(-180, 180, num=nlon, endpoint=False) + offset / 2
lats = np.linspace(90, -90, num=nlat, endpoint=False) - offset / 2

# open the data
fpath = Path("processing/OJP_P")
with open(fpath, "r") as f:
    dVp = [float(value) for line in f for value in line.split()]

# reshape data to layer x lat x lon
dVp = np.array(dVp).reshape(nlayers, nlat, nlon) # the README says that the data is ordered lon x lat x depth, so we reverse this order to "unpack" the data
dVp_0_180 = dVp[:,:,:int(nlon/2)] # get a view of the vps array with longitudes between 0 and 180 degrees
dVp_180_360 = dVp[:,:,int(nlon/2):] # get a view of the vps array with longitudes between 180 and 360 degrees
dVp = np.concatenate((dVp_180_360, dVp_0_180), axis=2) # make a new array where the longitudes go from -180 to 180 degrees


# set up DataArrays for primary coordinates
r = xr.DataArray(
    radii,
    dims="r",
    attrs={
        "long_name": "radius",
        "units": "m",
        "positive": "up"
    }
)
lat = xr.DataArray(
    np.linspace(90, -90, num=nlat, endpoint=False) - offset / 2,
    dims="lat",
    attrs={
        "long_name": "latitude",
        "units": "degrees"
    }
)
lon = xr.DataArray(
    np.linspace(-180, 180, num=nlon, endpoint=False) - offset / 2,
    dims="lon",
    attrs={
        "long_name": "longitude",
        "units": "degrees",
        "convention": "bipolar"
    }
)
# create Dataset
ojp_p = xr.Dataset(
    data_vars={"dVp_percent": (["r", "lat", "lon"], dVp)},
    coords={"r": radii, "lat": lats, "lon": lon, "depth": ("r", depths)},
    attrs={
        "id": "OJP_P",
        "reference": "Obayashi et al. (2021)",
        "doi": "https://doi.org/10.1038/s41598-021-99833-5",
        "source": "personal communication"
    }
)
# assign attributes to depth
ojp_p["depth"] = ojp_p["depth"].assign_attrs({
    "long_name": "depth",
    "units": "km",
    "positive": "down"
})
ojp_p["dVp_percent"].attrs = {
    "long_name": "P-wave velocity perturbation",
    "units": "percent"
}
ojp_p = ojp_p.reindex(lat=ojp_p.lat[::-1]) # reverse latitudes so that they run from -90 to 90
ojp_p.to_netcdf(Path("OJP_P.nc"))