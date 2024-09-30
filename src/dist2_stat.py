import xarray as xr
import data_loader
import numpy as np
import PentadTools as ptt
import tool_fig_config
import argparse
import pathlib
import os
import matrix_helper
import dask
import sklearn.decomposition

dask.config.set(**{'array.slicing.split_large_chunks': True})


parser = argparse.ArgumentParser(description='Process some integers.')
parser.add_argument('--input', type=str, help='Datasets.', required=True)
parser.add_argument('--output', type=str, help='Datasets.', default="")
parser.add_argument('--no-display', action="store_true")
args = parser.parse_args()
print(args)

print("Loading file: ", args.input)
ds = xr.load_dataset(args.input)

print(ds)

dist2_mtx = ds["dist2_mtx"]

print(dist2_mtx)

dist_mtx = dist2_mtx**0.5

dist_mtx_mean = dist_mtx.mean(dim="pentadstamp")
dist_mtx_std  = dist_mtx.std(dim="pentadstamp")

datasets = ds.coords["dataset1"]
N_datasets = len(datasets)


# Plot data
print("Loading Matplotlib...")
import matplotlib as mpl
mpl.use('Agg')
  
import matplotlib.pyplot as plt
from matplotlib import cm
from matplotlib.patches import Rectangle
import matplotlib.transforms as transforms
from matplotlib.dates import DateFormatter
import matplotlib.ticker as mticker
import cartopy.crs as ccrs
from cartopy.mpl.gridliner import LONGITUDE_FORMATTER, LATITUDE_FORMATTER
import tool_fig_config
import cmocean
print("done")

box_size=1.0
w = box_size * N_datasets
h = box_size * N_datasets


ncol = 1
nrow = 1
print("Create figure...")
figsize, gridspec_kw = tool_fig_config.calFigParams(
    w = w,
    h = h,
    wspace = 1.0,
    hspace = 0.5,
    w_left = 0.5,
    w_right = 1.0,
    h_bottom = 0.5,
    h_top = 0.5,
    ncol = ncol,
    nrow = nrow,
)


fig, ax = plt.subplots(
    nrow, ncol,
    figsize=figsize,
    gridspec_kw=gridspec_kw,
    constrained_layout=False,
    squeeze=False,
)


x = np.arange(N_datasets + 1 )
y = x.copy()

x_ticks = (x[:-1] + x[1:]) / 2

_ax = ax[0, 0]
_ax.invert_yaxis()
mappable = _ax.pcolormesh(x, y, dist_mtx_mean.to_numpy(), cmap=cmocean.cm.amp, shading='flat', vmin=0, vmax=1)

cax = tool_fig_config.addAxesNextToAxes(fig, _ax, "right", thickness=0.02, spacing=0.02)
cb = plt.colorbar(mappable, cax=cax, orientation="vertical", pad=0.00)
cb.ax.set_ylabel("Mean $d$ [ $ \\mathrm{K}$ ]")

_ax.set_xticks(x_ticks, datasets.to_numpy())
_ax.xaxis.set_ticks_position("top")
_ax.tick_params(
    axis='x',          # changes apply to the x-axis
    which='both',      # both major and minor ticks are affected
    bottom=False,      # ticks along the bottom edge are off
    top=False,         # ticks along the top edge are off
    labelsize=8,
)

_ax.set_yticks(x_ticks, datasets.to_numpy(), va="center")
_ax.tick_params(
    axis='y',          # changes apply to the x-axis
    which='both',      # both major and minor ticks are affected
    labelsize=8,
    labelrotation=90,
)

_ax.set_title(args.input)

for i in range(N_datasets):
    for j in range(N_datasets):
        
        x_cent = x_ticks[i]
        y_cent = x_ticks[j]
        
        _ax.text(
            x_cent,
            y_cent,
            "$ {dist:.02f} \\pm {diststd:.02f} $".format(
                dist = dist_mtx_mean.isel(
                    dataset1=j,
                    dataset2=i,
                ).to_numpy(),
                diststd = dist_mtx_std.isel(
                    dataset1=j,
                    dataset2=i,
                ).to_numpy(),
            ),
            ha="center",
            va="center",
        )





if not args.no_display:
    plt.show()

    output_dir = os.path.dirname(args.output)
    if not os.path.exists(output_dir):
        print("Making directory: %s" % (output_dir,))
        pathlib.Path(output_dir).mkdir(parents=True, exist_ok=True) 

    print("Saving file: ", args.output)
    fig.savefig(args.output, dpi=200)

