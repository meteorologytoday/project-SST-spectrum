import numpy as np
import xarray as xr
import scipy
import traceback
from pathlib import Path
import pandas as pd
import argparse



parser = argparse.ArgumentParser(
                    prog = 'plot_skill',
                    description = 'Plot prediction skill of GFS on AR.',
)

parser.add_argument('--input-file', type=str, help='Input file', required=True)
parser.add_argument('--output-SSTmap', type=str, help='Output file', default="")
parser.add_argument('--output-SSTspec', type=str, help='Output file', default="")
parser.add_argument('--lat-rng', type=float, nargs=2, help='The x axis range to be plot in km.', default=[None, None])
parser.add_argument('--lon-rng', type=float, nargs=2, help='The x axis range to be plot in km.', default=[None, None])
parser.add_argument('--cutoff-wvlen', type=float, help='The cutoff wavelength.', default=1.1)
parser.add_argument('--no-display', action="store_true")

args = parser.parse_args()
print(args)

ds = xr.open_dataset(args.input_file, decode_times=False)

SST = ds["water_temp"].isel(depth=0, time=0).sel(lat=slice(*args.lat_rng), lon=slice(*args.lon_rng))

print(SST.to_numpy().shape)
coords = { varname : SST.coords[varname].to_numpy() for varname in ds.coords}

dlat = coords["lat"][1] - coords["lat"][0]
dlon = coords["lon"][1] - coords["lon"][0]

L_lat = dlat * len(coords["lat"])
L_lon = dlon * len(coords["lon"])

SST = SST.to_numpy()
SST_nonan = SST.copy()
SST_nonan[np.isnan(SST_nonan)] = 0.0

#SST_lp = scipy.ndimage.uniform_filter(SST_nonan, size=(51, 25), mode='reflect')
SST_lp = scipy.ndimage.uniform_filter(SST_nonan, size=(25, 13), mode='reflect')
SST_hp = SST - SST_lp


# Spectral analysis
if np.any(np.isnan(SST)):
    print("Warning: SST contains NaN.")

SST_zm = np.nanmean(SST, axis=1, keepdims=True)
SST_za = SST - SST_zm
dft_coe = np.fft.fft(SST_za, axis=1)
wvlens = dlon / np.fft.fftfreq(SST_za.shape[1])


plot_wvlens  = wvlens[0:(len(wvlens) // 2)]
plot_specden = dft_coe[:, 0:(len(wvlens) // 2)]
plot_specden = np.abs(plot_specden)**2

selected_idx = plot_wvlens < args.cutoff_wvlen
plot_wvlens = plot_wvlens[selected_idx]
plot_specden = plot_specden[:, selected_idx]

plot_freqs = 1.0 / plot_wvlens




# Plot data
print("Loading Matplotlib...")
import matplotlib as mpl
if args.no_display is False:
    mpl.use('TkAgg')
else:
    mpl.use('Agg')
    mpl.rc('font', size=15)
    mpl.rc('axes', labelsize=15)

print("Done.")     
 
 
import matplotlib.pyplot as plt
from matplotlib import cm
from matplotlib.patches import Rectangle
import matplotlib.transforms as transforms
from matplotlib.dates import DateFormatter
import matplotlib.ticker as mticker
import cartopy.crs as ccrs
import tool_fig_config

print("Plotting Frequency")


ncol = 1
nrow = 1

figsize, gridspec_kw = tool_fig_config.calFigParams(
    w = 6,
    h = 6,
    wspace = 1.5,
    hspace = 0.7,
    w_left = 1.0,
    w_right = 1.5,
    h_bottom = 2.0,
    h_top = 1.0,
    ncol = ncol,
    nrow = nrow,
)


fig, ax = plt.subplots(
    nrow, ncol,
    figsize=figsize,
    subplot_kw=dict(aspect="auto"),
    gridspec_kw=gridspec_kw,
    constrained_layout=False,
    squeeze=False,
    sharex=True,
)

fig.suptitle("File: %s" % (args.input_file,))

_ax = ax.flatten()[0]
#_ax.plot(plot_wvlens, plot_specden.transpose(), color="gray", linewidth=0.5, alpha=0.5)
#_ax.plot(plot_wvlens, np.mean(plot_specden, axis=0), "k--", linewidth=2)

_ax.plot(np.log10(plot_freqs), np.log10(np.mean(plot_specden, axis=0)), "k-", linewidth=2)

#_ax.set_xlim([0, args.cutoff_wvlen])
#_ax.set_xlabel("Wavelength [deg]")
#_ax.set_ylabel("Spectral Intensity [$ \\mathrm{K}^2 $]")

xticks = np.array([-.5, 0, .5, 1])
yticks = np.array([0, 1, 2, 3])
_ax.set_xticks(ticks=xticks, labels=["$10^{%.1f}$" % (d, ) for d in xticks])
_ax.set_yticks(ticks=yticks, labels=["$10^{%d}$" % (d, ) for d in yticks])

_ax.grid(True)
_ax.set_xlabel("Wavenumber [cycle / deg]")
_ax.set_ylabel("Spectral Intensity [$ \\mathrm{K}^2 $]")


if args.output_SSTspec != "":
    print("Saving output: ", args.output_SSTspec)
    fig.savefig(args.output_SSTspec, dpi=200)



#===========================================

print("Plotting SST map")


ncol = 2
nrow = 1

figsize, gridspec_kw = tool_fig_config.calFigParams(
    w = 6,
    h = 6,
    wspace = 1.5,
    hspace = 0.7,
    w_left = 1.0,
    w_right = 1.5,
    h_bottom = 2.0,
    h_top = 1.0,
    ncol = ncol,
    nrow = nrow,
)


fig, ax = plt.subplots(
    nrow, ncol,
    figsize=figsize,
    subplot_kw=dict(aspect="auto"),
    gridspec_kw=gridspec_kw,
    constrained_layout=False,
    squeeze=False,
    sharex=True,
)

fig.suptitle("File: %s" % (args.input_file,))

SST_levs = np.linspace(5, 25, 41)
SST_lp_levs = np.linspace(5, 25, 11)
SST_hp_levs = np.linspace(-2, 2, 21)
SST_hp_cntr_levs = np.array([-1, 1]) * 0.5

_ax = ax.flatten()[0]
mappable = _ax.contourf(coords["lon"], coords["lat"], SST, SST_levs, cmap="gnuplot", extend="both")
cax = tool_fig_config.addAxesNextToAxes(fig, _ax, "bottom", thickness=0.03, spacing=0.1)
cb = plt.colorbar(mappable, cax=cax, orientation="horizontal", pad=0.00)
cb.ax.set_xlabel("SST [ K ]")


_ax = ax.flatten()[1]
mappable = _ax.contourf(coords["lon"], coords["lat"], SST_hp, SST_hp_levs, cmap="bwr", extend="both")
cax = tool_fig_config.addAxesNextToAxes(fig, _ax, "bottom", thickness=0.03, spacing=0.1)
cb = plt.colorbar(mappable, cax=cax, orientation="horizontal", pad=0.00)
cb.ax.set_xlabel("High-pass SST [ K ]")

cs = _ax.contour(coords["lon"], coords["lat"], SST_hp, SST_hp_cntr_levs, colors="black", linewidths=0.5)
#plt.clabel(cs, fmt="%.1f")

for _ax in ax.flatten():
    _ax.grid()
    _ax.set_xlabel("lon")
    _ax.set_ylabel("lat")


if args.output_SSTmap != "":
    print("Saving output: ", args.output_SSTmap) 
    fig.savefig(args.output_SSTmap, dpi=200)



if not args.no_display:
    plt.show()
