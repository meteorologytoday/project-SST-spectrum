import xarray as xr
import data_loader
import numpy as np
import PentadTools as ptt
import tool_fig_config
import argparse
import pathlib
import os

parser = argparse.ArgumentParser(description='Process some integers.')
parser.add_argument('--datasets', type=str, nargs="+", help='Name of the dataset.', required=True)
parser.add_argument('--output-dir', type=str, help='Output directory.', required=True)
parser.add_argument('--varname', type=str, required=True)
parser.add_argument('--timepentad-rng', type=str, nargs=2, help="TimePetand range.", required=True)
parser.add_argument('--pentads-interval', type=int, help="The time interval to do the average in pentads.", default=1)
parser.add_argument('--drop-wvn', type=int, help="Number of the first few harmonics til wvn `--drop-wvn` to drop.", default=0)
parser.add_argument('--x-rng', type=float, nargs=2, help="X rng.", default=[None, None])
parser.add_argument('--label', type=str, help='Spectral label.', required=True)

args = parser.parse_args()
print(args)

print("Loading Matplotlib...")
import matplotlib as mpl
mpl.use('Agg')
mpl.rc('font', size=15)
mpl.rc('axes', labelsize=15)


 
import matplotlib.pyplot as plt
from matplotlib import cm
import matplotlib.transforms as transforms
import matplotlib.ticker as mticker
import tool_fig_config

print("Done.")     

def findfirst(a):
    return np.argmax(a)

def findlast(a):
    a_rev = a[::-1]
    i = findfirst(a_rev)
    
    return len(a_rev) - 1 - i



def faketail(d):
    
    dd = d.copy()
    
    first_finite = findfirst(np.isfinite(d))
    last_finite = findlast(np.isfinite(d))
    dd[:first_finite] = d[first_finite]
    dd[last_finite+1:] = d[last_finite]

    #print(dd[:10])
    #print(dd[-10:])

    return dd

def fft_analysis(d, dx):

    if len(d.shape) == 1:
        d = d[np.newaxis, :]

    Nt = d.shape[0]
    Nx = d.shape[1]
    necessary_N = Nx // 2

    #d_m = np.nanmean(d, axis=1, keepdims=True)
    #d_a = d - d_m

    d_a = np.zeros_like(d)
    x = np.arange(Nx)
    for t in range(Nt):
        d_a[t, :] = detrend(x, d[t, :])
 
    dft_coe = np.fft.fft(d_a, axis=1) / Nx
    wvlens = dx / np.fft.fftfreq(Nx)
    
    necessary_N = Nx // 2
    dft_coes = dft_coe[:, 0:necessary_N]
    wvlens = wvlens[0:necessary_N]

    """
    dft_coe_2d = np.zeros((dft_coe.shape[0], necessary_N, 2), dtype=float)
    dft_coe_2d[:, :, 0] = np.real(dft_coe)
    dft_coe_2d[:, :, 1] = np.imag(dft_coe)
    
    dft_coe_2d_radiphas = np.zeros((dft_coe.shape[0], necessary_N, 2), dtype=float)
    dft_coe_2d_radiphas[:, :, 0] = np.abs(dft_coe)
    dft_coe_2d_radiphas[:, :, 1] = np.angle(dft_coe)
    """
    return dft_coes, wvlens

def detrend(x, f):

    print("x: ", x)
    print("f: ", f)

    m, b = np.polyfit(x, f, 1)
    f_removed_mean = f - b
    f_detrended = f - (m * x + b) 

    return f_detrended



def work(
    output_filename,
    datasets,
    label,
    varname,
    tp_rng,
):

    data = []
    data_diff = []
    data_dft = []

    #print("Doing tp_rng = [ %s, %s ]" % (tp_rng[0], tp_rng[1], ))
    print("Open dataset...")
    

    for dataset in datasets:

        ds = data_loader.load_dataset(
            dataset = dataset,
            datatype = "cropped",
            label = label,
            varname = varname,
            tp_beg = tp_rng[0],
            tp_end = tp_rng[1],
            inclusive = "both",
        ).mean(dim="pentadstamp", keep_attrs=True, skipna=True)

        data.append(ds)

    print("Datasets opened.")

    ref_ds = data[0]
    x_T = ref_ds.coords["x"].to_numpy()
    x_U = (x_T[1:] + x_T[:-1])/2
    dx = ref_ds.attrs["dx"]
    Lx = dx * len(x_T)

    for i, ds in enumerate(data):
        
        diff = ds - ref_ds
        
        d = diff[varname].to_numpy()
        d = faketail(d)
        d = detrend(np.arange(len(d)), d)
                
        data_physical_raw = detrend(np.arange(len(d)), faketail(ds[varname].to_numpy()))

        # dft
        dft_coes, wvlens = fft_analysis(d, dx)

        # derivative
        dvardx = ( d[1:] - d[:-1] ) / dx 
        
        data_diff.append(
            dict(
                dataset = args.datasets[i],
                wvlens = wvlens,
                dft_coes = dft_coes,
                data_physical = d,
                data_physical_raw = data_physical_raw,
                dvardx = dvardx,
            )
        )
        

    ncol = 2
    nrow = 2

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

    print("Creating fig and ax...")

    fig, ax = plt.subplots(
        nrow, ncol,
        figsize=figsize,
        subplot_kw=dict(aspect="auto"),
        gridspec_kw=gridspec_kw,
        constrained_layout=False,
        sharex=False,
        squeeze=False,
    )

    # Plot reference SST 
    _ax = ax[0, 0]

    # Plot SST and Spectrum
    _ax_physical = ax[1, 0]
    _ax_spectral = ax[1, 1]
    _ax_spectral_twin = _ax_spectral.twinx()
    
    _ax_dvardx = ax[0, 1]
    
    for d in data_diff:
        _ax.plot( x_T, d["data_physical_raw"], label=d["dataset"])
       
        _ax_dvardx.plot( x_U, d["dvardx"], label=d["dataset"])
        _ax_physical.plot( x_T, d["data_physical"], label=d["dataset"])
        
        dft_coes = d["dft_coes"].mean(axis=0)
        amps = np.abs(dft_coes)

        wvns = np.arange(len(dft_coes))
 
        variances = amps**2
        total_variance = variances.sum()
        variance_fracs = variances / total_variance 

        _ax_spectral.plot(wvns, np.log(amps), linestyle="solid")
        _ax_spectral_twin.plot(wvns, variance_fracs, linestyle="dashed")



    data_physical_detrended = detrend(x_T, faketail(ref_ds[varname].to_numpy()))
    #print(data_physical_detrended)

    #_ax.plot( x_T, data_physical_detrended, label)
    
    _ax.set_xlabel("x [ deg ]")
    _ax.set_ylabel("$ \\mathrm{SST}' $ [ K ]")
    _ax.set_ylim([-5, 5])
    _ax.set_xlim(args.x_rng)
    _ax.legend()
    _ax.grid()

    _ax_physical.set_xlabel("x [ deg ]")
    _ax_physical.set_ylabel("$ \\mathrm{SST}' $ [ K ]")
    _ax_physical.set_ylim([-1, 1])
    _ax_physical.grid()
    _ax_physical.legend()
    _ax_physical.set_xlim(args.x_rng)

    _ax_dvardx.grid()
    _ax_dvardx.set_xlabel("x [ deg ]")
    _ax_dvardx.set_ylabel("Gradient [ $\\mathrm{K} / \\mathrm{deg} $ ]")
    _ax_dvardx.set_xlim(args.x_rng)
 
    _ax_spectral.set_xlabel("Wavelength [ deg ]")
    _ax_spectral.set_ylabel("Magnitude [ $  \\mathrm{K} $ ]")
    _ax_spectral_twin.set_ylabel("Variance Fraction [ $ \\% $ ]")
 
    _ax_spectral_twin.spines["right"].set_color('red')
    _ax_spectral_twin.spines["right"].set_color('red')
    _ax_spectral_twin.tick_params(color='red', labelcolor='red')

    labeled_wvlens = np.array([2, 5, 10, 20, 30])  # deg
    labeled_ticks = Lx / labeled_wvlens
    labeled_wvlen_txts = [ "%d" % (wv,) for wv in labeled_wvlens ]
    
    plot_xlim_wvlens = np.array([np.inf, 1])
    plot_xlim = Lx / plot_xlim_wvlens

    _ax_spectral.grid()

    _ax_spectral.set_ylim([-8, -1])
    _ax_spectral_twin.set_ylim([0, 0.3])
    
    _ax_spectral.set_xlim(plot_xlim)
    _ax_spectral.set_xticks(
        ticks=labeled_ticks,
        labels=labeled_wvlen_txts,
    )
    
    
    
    fig.suptitle("[%s] %s %s" % (label, str(tp_rng[0]), varname,) )

    output_dir = os.path.dirname(output_filename)
    if not os.path.exists(output_dir):
        print("Making directory: %s" % (output_dir,))
        pathlib.Path(output_dir).mkdir(parents=True, exist_ok=True) 

    print("Writing output: ", output_filename) 
    fig.savefig(output_filename, dpi=200)

    ds.close()
    plt.close(fig)

print("Plotting datasets: ", args.datasets)
tps = list(ptt.pentad_range(args.timepentad_rng[0], args.timepentad_rng[1], inclusive="both"))
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
        "{varname:s}_{timepentad_beg:s}-{timepentad_end:s}.png".format(
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
        args.datasets,
        args.label,
        args.varname,
        [tp_beg, tp_end],
    )








