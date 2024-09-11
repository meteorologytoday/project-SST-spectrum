import xarray as xr
import data_loader
import numpy as np
import PentadTools as ptt
import tool_fig_config
import argparse
import pathlib
import os

parser = argparse.ArgumentParser(description='Process some integers.')
parser.add_argument('--dataset', type=str, help='Name of the dataset.', required=True)
parser.add_argument('--output-dir', type=str, help='Output directory.', required=True)
parser.add_argument('--varname', type=str, required=True)
parser.add_argument('--timepentad-rng', type=str, nargs=2, help="TimePetand range.", required=True)
parser.add_argument('--pentads-interval', type=int, help="The time interval to do the average in pentads.", default=1)
parser.add_argument('--drop-wvn', type=int, help="Number of the first few harmonics til wvn `--drop-wvn` to drop.", default=0)
parser.add_argument('--label', type=str, help='Spectral label.', required=True)

args = parser.parse_args()
print(args)

# Plot data
print("Loading Matplotlib...")
import matplotlib as mpl
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


def work(
    output_filename,
    dataset,
    varname,
    tp_rng,
    label,
):

    
    #print("Doing tp_rng = [ %s, %s ]" % (tp_rng[0], tp_rng[1], ))

    ds = data_loader.load_dataset(
        dataset = dataset,
        datatype = "spectral",
        varname = varname,
        tp_beg = tp_rng[0],
        tp_end = tp_rng[1],
        label = label,
        inclusive = "both",
    )

    wavenumber_max = np.amax(ds.coords["wavenumber"])

    ds = ds.isel(wvlen=slice(args.drop_wvn+1, None)).mean(dim="pentadstamp", keep_attrs=True)

    amp = ds["dftcoe_form2"].sel(complex_radiphas="radius")

    variance = amp**2
    total_variance = variance.sum(dim="wvlen")
    variance_frac = variance / total_variance 

    ncol = 1
    nrow = 1

    figsize, gridspec_kw = tool_fig_config.calFigParams(
        w = 6,
        h = 4,
        wspace = 1.0,
        hspace = 1.0,
        w_left = 1.0,
        w_right = 1.0,
        h_bottom = 1.0,
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
        sharex=False,
        squeeze=False,
    )
    
    labeled_wvlens = np.array([2, 5, 10, 20, 30])  # deg
    labeled_ticks = ds.attrs["Lx"] / labeled_wvlens
    labeled_wvlen_txts = [ "%d" % (wv,) for wv in labeled_wvlens ]
    
    plot_xlim_wvlens = np.array([np.inf, 1])
    plot_xlim = ds.attrs["Lx"] / plot_xlim_wvlens

    wvns = ds.coords["wavenumber"]

    _ax = ax[0, 0]
    _ax_twin = _ax.twinx()

    _ax.plot(wvns, np.log(amp), "k-")
    _ax_twin.plot(wvns, variance_frac, "r--")

    _ax.set_title("[%s] %s %s" % (label, str(tp_rng[0]), varname,) )
    _ax.grid()

    _ax.set_ylim([-8, -1])
    _ax_twin.set_ylim([0, 0.3])



    _ax.set_xticks(
        ticks=labeled_ticks,
        labels=labeled_wvlen_txts,
    )

    _ax.set_xlim(plot_xlim)

    output_dir = os.path.dirname(output_filename)
    if not os.path.exists(output_dir):
        print("Making directory: %s" % (output_dir,))
        pathlib.Path(output_dir).mkdir(parents=True, exist_ok=True) 

    print("Writing output: ", output_filename) 
    fig.savefig(output_filename, dpi=200)


    plt.close(fig)

print("Plotting dataset: ", args.dataset)
tps = list(ptt.pentad_range(args.timepentad_rng[0], args.timepentad_rng[1], inclusive="left"))
N = len(tps)
N_output = N // args.pentads_interval
res = N % args.pentads_interval
if res != 0:
    print("Length of pentads is not a integer multiple of `pentads_interval` = %d. The last %d data will be discarded." % (args.pentads_interval, res,))

for i in range(N_output):
  
    tp_beg = tps[i*args.pentads_interval] 
    tp_end = tps[(i+1)*args.pentads_interval-1] 

    output_filename = os.path.join(
        args.output_dir,
        args.label,
        args.dataset,
        "{dataset:s}_{varname:s}_{timepentad_beg:s}-{timepentad_end:s}.png".format(
            dataset = args.dataset,
            varname = args.varname,
            timepentad_beg = str(tp_beg),
            timepentad_end = str(tp_end),
        )
    )

    if os.path.exists(output_filename):
        print("File %s already exists. Skip this one." % (output_filename,))
        continue

    print("Doing output file: ", output_filename)    
    work(
        output_filename,
        args.dataset,
        args.varname,
        [tp_beg, tp_end],
        args.label,
    )








