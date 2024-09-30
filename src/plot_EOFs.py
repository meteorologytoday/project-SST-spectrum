import numpy as np
import xarray as xr
import pandas as pd
import os
import traceback
from pathlib import Path
import argparse
from datetime import (timedelta, datetime, timezone)

import cmocean

import tool_fig_config

def correlate(x1, x2):
    
    if len(x1) != len(x2):
        raise Exception("Unequal input of arrays.")


    c = np.zeros((len(x1),))

    _x1 = np.array(x1)
    _x2 = np.array(x2)

    _x1 /= np.sum(_x1**2)**0.50
    _x2 /= np.sum(_x2**2)**0.50

    for i in range(len(c)-1):
        __x1 = _x1[:len(c)-i]
        __x2 = _x2[i:]

        c[i] = np.sum(__x1 * __x2)

    return c





parser = argparse.ArgumentParser(
                    prog = 'plot_skill',
                    description = 'Plot prediction skill of GFS on AR.',
)

parser.add_argument('--input', type=str, help='Input file', required=True)
parser.add_argument('--output-timeseries', type=str, help='Input file', default="")
parser.add_argument('--output-EOF', type=str, help='Input file', default="")
parser.add_argument('--title', type=str, help='Input file', default="")
parser.add_argument('--nEOF', type=int, help='Input file', default=2)
parser.add_argument('--nEOF-variance', type=int, help='Numbmer of variance to plot', default=5)
parser.add_argument('--no-display', action="store_true")
parser.add_argument('--plot-every-N-pts', type=int, help="Skip points to speed up plotting.", default=1)
args = parser.parse_args()
print(args)



ds = xr.open_dataset(args.input)

if args.plot_every_N_pts != 1:
    ds = ds.isel(lat=slice(None, None, args.plot_every_N_pts), lon=slice(None, None, args.plot_every_N_pts))


# Decide the sign of mode
EOF_signs = np.ones((ds.dims["mode"],), dtype=int)
for i in range(ds.dims["mode"]): 
    
    EOF = ds["EOF"].isel(mode=i).to_numpy()
     
    # There are NaNs so it is easier this way
    cnt_pos_sign = np.sum(np.isfinite(EOF) & (EOF >= 0))
    cnt_neg_sign = np.sum(np.isfinite(EOF) & (EOF < 0))
    
    if cnt_neg_sign > cnt_pos_sign:
        EOF_signs[i] = -1

print("Signs: ", EOF_signs)

# Plot data
print("Loading Matplotlib...")
import matplotlib as mpl
if args.no_display is False:
    print("`--no-display` is not set.")
    mpl.use('TkAgg')
else:
    print("`--no-display` is set.")
    mpl.use('Agg')
    #mpl.rc('font', size=20)
    #mpl.rc('axes', labelsize=15)
     
 
  
import matplotlib.pyplot as plt
from matplotlib import cm
from matplotlib.patches import Rectangle
import matplotlib.transforms as transforms
from matplotlib.dates import DateFormatter
import matplotlib.ticker as mticker
import cartopy.crs as ccrs
from cartopy.mpl.gridliner import LONGITUDE_FORMATTER, LATITUDE_FORMATTER


print("done")


print("Plotting Timeseries... ")
ncol = 2
nrow = 1
print("Create figure...")
figsize, gridspec_kw = tool_fig_config.calFigParams(
    w = 5.0,
    h = 2.0,
    wspace = 1.0,
    hspace = 0.5,
    w_left = 1.0,
    w_right = 0.25,
    h_bottom = 0.5,
    h_top = 0.25,
    ncol = ncol,
    nrow = nrow,
)


fig_ts, ax = plt.subplots(
    nrow, ncol,
    figsize=figsize,
    gridspec_kw=gridspec_kw,
    constrained_layout=False,
    squeeze=False,
)

# Time series
_ax = ax[0, 0]
for i in range(args.nEOF):
    _data = ds["projected_idx"].isel(mode=i)
    _ax.plot(np.arange(len(_data)), _data * EOF_signs[i], label="EOF%d" % (i+1,))


_ax.set_xlabel("Samples")
_ax.set_ylabel("Projected Index")
_ax.set_title("(a) Series Projected Index")


_ax.legend()
_ax.grid(True)

# Variances explained
_ax = ax[0, 1]
frac_var = ds["variance"].isel(mode=slice(0, args.nEOF_variance) ) / np.sum(ds["variance"]) * 100

_ax.plot(
    1 + np.arange(len(frac_var)),
    frac_var,
    marker = "o",
    markersize = 8,
    linestyle="dashed",
    color = "black",
)

_ax.set_ylim([0, 20])
_ax.set_xlabel("Modes")
_ax.set_ylabel("Variance explained [ $ \\% $ ]")
_ax.set_title("(b) Variance explained")

_ax.grid(True)


if not args.no_display:
    plt.show()

if args.output_timeseries != "":
    output_dir = os.path.dirname(args.output_timeseries)
    if not os.path.exists(output_dir):
        print("Making directory: %s" % (output_dir,))
        Path(output_dir).mkdir(parents=True, exist_ok=True) 

    print("Saving file: ", args.output_timeseries)
    fig_ts.savefig(args.output_timeseries, dpi=200)

# First figure : EOFs

cent_lon = 180.0

plot_lon_l = 100.0
plot_lon_r = 260.0
plot_lat_b = 10.0
plot_lat_t = 60.0

proj = ccrs.PlateCarree(central_longitude=cent_lon)
proj_norm = ccrs.PlateCarree()

# Std+mean, EOFs, timeseries
ncol = 2 + args.nEOF
nrow = 1

print("Create figure...")
figsize, gridspec_kw = tool_fig_config.calFigParams(
    w = 5.0,
    h = 2.0,
    wspace = 1.0,
    hspace = 0.5,
    w_left = 1.0,
    w_right = 1.0,
    h_bottom = 1.0,
    h_top = 0.25,
    ncol = ncol,
    nrow = nrow,
)


fig_EOF, ax = plt.subplots(
    nrow, ncol,
    figsize=figsize,
    subplot_kw=dict(projection=proj, aspect="auto"),
    gridspec_kw=gridspec_kw,
    constrained_layout=False,
    squeeze=False,
)
    
coords = ds.coords

print("Plot mean and std")
_ax = ax[0, 0]

mappable = _ax.contourf(coords["lon"], coords["lat"], ds["mean"], levels=np.linspace(-1, 1, 21), cmap=cmocean.cm.balance, extend="both", transform=proj_norm)

cax = tool_fig_config.addAxesNextToAxes(fig_EOF, _ax, "right", thickness=0.02, spacing=0.02)
cb = plt.colorbar(mappable, cax=cax, orientation="vertical", pad=0.00)
cb.ax.set_ylabel("Mean [ K ]")
_ax.set_title("(a) Mean")


_ax = ax[0, 1]
mappable = _ax.contourf(coords["lon"], coords["lat"], ds["std"], levels=np.linspace(0, 0.5, 11), cmap=cmocean.cm.gray, extend="max", transform=proj_norm)

cax = tool_fig_config.addAxesNextToAxes(fig_EOF, _ax, "right", thickness=0.02, spacing=0.02)
cb = plt.colorbar(mappable, cax=cax, orientation="vertical", pad=0.00)
cb.ax.set_ylabel("Standard Deviation [ K ]")
_ax.set_title("(b) Standard Deviation")




for i in range(args.nEOF):
    
    print("Plot EOF ", i+1)
    _ax = ax[0, i+2]

    _ax.set_title("(%s) EOF%d " % ("cdefghi"[i], i+1, ))#np.floor(ds["explained_variance_ratio"].sel(EOF=i)*100)))



    EOF = ds["EOF"].isel(mode=i) * EOF_signs[i]
    EOF /= 2 * EOF.std()

    mappable = _ax.contourf(coords["lon"], coords["lat"], EOF, levels=np.linspace(-1, 1, 21), cmap=cmocean.cm.balance, extend="both", transform=proj_norm)

    cax = tool_fig_config.addAxesNextToAxes(fig_EOF, _ax, "right", thickness=0.02, spacing=0.02)
    cb = plt.colorbar(mappable, cax=cax, orientation="vertical", pad=0.00, ticks=[-1, 0, 1])


for _ax in ax.flatten():    

    _ax.set_global()
    _ax.coastlines()
    _ax.set_extent([plot_lon_l, plot_lon_r, plot_lat_b, plot_lat_t], crs=proj_norm)

    gl = _ax.gridlines(crs=ccrs.PlateCarree(), draw_labels=True,
                      linewidth=1, color='gray', alpha=0.5, linestyle='--')

    gl.xlabels_top   = False
    gl.ylabels_right = False

    #gl.xlocator = mticker.FixedLocator(np.arange(-180, 181, 30))
    gl.xlocator = mticker.FixedLocator([120, 150, 180, -150, -120])#np.arange(-180, 181, 30))
    gl.ylocator = mticker.FixedLocator([10, 20, 30, 40, 50])

    gl.xformatter = LONGITUDE_FORMATTER
    gl.yformatter = LATITUDE_FORMATTER
    gl.xlabel_style = {'size': 10, 'color': 'black'}
    gl.ylabel_style = {'size': 10, 'color': 'black'}

 


if not args.no_display:
    plt.show()

if args.output_EOF != "":
    output_dir = os.path.dirname(args.output_EOF)
    if not os.path.exists(output_dir):
        print("Making directory: %s" % (output_dir,))
        Path(output_dir).mkdir(parents=True, exist_ok=True) 

    print("Saving file: ", args.output_EOF)
    fig_EOF.savefig(args.output_EOF, dpi=200)






