"""Program to create cross-sections of whole-mantle tomography models"""
import numpy as np
import xarray as xr
import spherical
from pathlib import Path
from scipy.spatial import geometric_slerp

# for plotting
import matplotlib.pyplot as plt
import cmcrameri as cmc
cm = 1/2.54
plt.rcParams.update({
    "text.usetex": True,
    "font.family": "sans-serif",
    "font.serif": "cm",
    "text.latex.preamble": r"""
        \usepackage[T1]{fontenc}
        \usepackage{cmbright}
        \usepackage{amsmath}
        \usepackage{siunitx}
        \sisetup{detect-all}
        """
})

def fill_great_circle(g0, g1, res=1, return_angle=False):
    """fills the great circle between g0 and g1 at the requested angular resolution"""
    gs = np.array([g0, g1]) # combine geographic coordinates into one array
    radii = np.full((gs.shape[0], 1), 1.) # create array of radii 1 for concatenation. must be 1 so getting angle is straightforward and is required by `scipy.spatial.geometric_slerp`
    gs = np.concatenate((radii, gs), axis=1) # add radii to geographical coordinate array
    ss = spherical.geo2sph(gs) # convert to spherical coordinates
    c0, c1 = spherical.sph2cart(ss) # convert to Cartesian coordinates
    angle = np.rad2deg(np.arccos(np.dot(c0, c1)))
    n_pts = int(np.ceil(angle / res))
    c_profile = geometric_slerp(c0, c1, t=np.linspace(0, 1, n_pts)) # generate a great circle between the two points
    s_profile = spherical.cart2sph(c_profile) # convert the profile points to spherical coordinates
    g_profile = spherical.sph2geo(s_profile[:,1:]) # convert the profile points to geographic coordinates (ignoring the radii)
    g_profile[:,0] = np.unwrap(g_profile[:,0], period=360)
    if return_angle: return g_profile, angle
    return g_profile



# specify cross-section coordinates and labels
g0 = [ 142.0, -26.0]
g1 = [ 189.0,  -5.5]

model_name = "TX2019slab"
tomography_path = Path.cwd().parent / Path("TX2019slab.nc")

# open netcdf
ds = xr.open_dataset(tomography_path) # open the netcdf file

# check if the cross-section profile would cross the Antimeridian and if so, convert the Dataset
if np.abs(g1[0] - g0[0]) > np.pi:
    ds = spherical.convert_lon(ds)

fig, ax = plt.subplots(1, 1, figsize=(15*cm, 12*cm), layout="constrained", subplot_kw={"projection": "polar"})


# create cross-section parameters
profile, angle = fill_great_circle(g0, g1, res=0.1, return_angle=True) # res=0.1 translates to 450 intervals for a 45 degree cross-section

lon, lat = xr.DataArray(profile[:,0], dims="theta"), xr.DataArray(profile[:,1], dims="theta")
r = xr.DataArray(np.linspace(6371e3, 3501e3, 579), dims="r")

# interpolate along the cross-section
xs = ds.interp(coords={"r": r, "lat": lat, "lon": lon}, kwargs={"bounds_error": False, "fill_value": None})
xs = xs.assign_coords(theta=np.deg2rad(np.linspace(90 + angle / 2, 90 - angle / 2, len(xs.theta))))

# plot the heatmap
pcm = ax.contourf(xs.theta, xs.r, xs.dVp_percent, cmap="cmc.vik_r", vmin=-1, vmax=1, levels=np.linspace(-1,1,18), extend="both")
ax.set_title(f'{model_name}', y=0.14)

# add the colour bar
cb = fig.colorbar(pcm, ax=ax, orientation="horizontal", shrink=0.5, pad=-0.1, extend="both", ticks=[-1, -0.5, 0, 0.5, 1])
cb.set_label(label=r"$V_p$ anomaly (\si{\percent})", labelpad=1.5)

# this actually turns the polar plot into a cross-section
ax.set_xlim(xs["theta"].max(), xs["theta"].min())
ax.set_rlim(xs["r"].min(), xs["r"].max())
ax.set_rorigin(0)

# add some nice decorations
theta = np.linspace(xs["theta"].max(), xs["theta"].min(), 200)
ax.plot(theta, np.full_like(theta, xs["r"].max() - 410e3), lw=0.5, linestyle='--', dashes=(5, 2), c='0.3', zorder=2)
ax.plot(theta, np.full_like(theta, xs["r"].max() - 660e3), lw=0.5, linestyle='--', dashes=(5, 2), c='0.3', zorder=2)
ax.plot(theta, np.full_like(theta, xs["r"].max() - 1000e3), lw=0.5, linestyle='--', dashes=(5, 2), c='0.3', zorder=2)
ax.set_xticks([], [])
ax.set_yticks([], [])
for side in ax.spines.keys():  # 'top', 'bottom', 'left', 'right'
    ax.spines[side].set_linewidth(1.5)

plt.show()
plt.close()