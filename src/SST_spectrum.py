import traceback
from multiprocessing import Pool
import multiprocessing
from pathlib import Path
import os

import numpy as np
import xarray as xr
import scipy
import pandas as pd
import argparse

import TimePentad as tp
import data_loader 

parser = argparse.ArgumentParser(
                    prog = 'plot_skill',
                    description = 'Plot prediction skill of GFS on AR.',
)

parser.add_argument('--dataset', type=str, help='Input file', required=True)
parser.add_argument('--input-dir', type=str, help='Input file', required=True)
parser.add_argument('--output-dir', type=str, help='Input file', required=True)
parser.add_argument('--date-rng', type=str, nargs=2, help='Time range in Pentad', required=True)
parser.add_argument('--lat-rng', type=float, nargs=2, help='The lat axis range to be plot in km.', default=[None, None])
parser.add_argument('--lon-rng', type=float, nargs=2, help='The lon axis range to be plot in km.', default=[None, None])
parser.add_argument('--spectral-dir', type=str, help='The direction to do fft. Can be `lat` or `lon`.', choice=['lat', 'lon'])

args = parser.parse_args()
print(args)

def fft_analysis(d, dx):

    Nx = d.shape[1]
    necessary_N = Nx // 2

    d_m = np.nanmean(SST, axis=1, keepdims=True)
    d_a = d - d_m

    dft_coe = np.fft.fft(d_a, axis=1)
    wvlens = dx / np.fft.fftfreq(Nx)

    necessary_N = Nx // 2
    dft_coe = dft_coe[0:necessary_N]
    wvlens = wvlens[0:necessary_N]

    dft_coe = np.array((necessary_N, 2), dtype=float)
    dft_coe[:, 0] = np.real(dft_coe)
    dft_coe[:, 1] = np.imag(dft_coe)

    return dft_coe, wvlens

def work(
    details,
):
   
    for v in [
        "lat_rng",
        "lon_rng",
        "dataset",
        "year",
        "pentad",
        "phase",
        "tp",
        "spectral_dir",
    ]:
        locals()[v] = details[v]

 
    result = dict(
        tp = tp,
        need_work = False,
        output_filename=output_filename,
        status='UNKNOWN',
    )

    try:

        input_full_filename = os.path.join(
            data_loader.getFilename(dataset, "physical", tp) 
        )

        output_full_filename = os.path.join(
            data_loader.getFilename(dataset, "spectral", tp) 
        )


        if phase == "detect":
            
            result["need_work"] = True
            return result
            
         
        ds = data_loader.load_dataset(input_filename)

            
        Nt = ds.dims["time"]
        coords = { 
            varname : SST.coords[varname].to_numpy() for varname in ds.coords 
        }

        dlat = coords["lat"][1] - coords["lat"][0]
        dlon = coords["lon"][1] - coords["lon"][0]
        data_vars = {}
        for varname in ["sst", ]:
 
            da = ds[varname].sel(lat=slice(*args.lat_rng), lon=slice(*args.lon_rng))
           
            if spectral_dir == "lat": 
                Nx = ds.dims["lat"]
                dx = dlat
                da = da.mean(dim="lon")

            elif spectral_dir == "lon": 
                Nx = ds.dims["lon"]
                dx = dlon
                da = da.mean(dim="lat")

            da_numpy = da.to_numpy()
            #SST_nonan = SST.copy()
            #SST_nonan[np.isnan(SST_nonan)] = 0.0

            # Spectral analysis
            if np.any(np.isnan(da_numpy)):
                print("Warning: Data `%s` contains NaN." % (varname,))

            dft_coe, wvlens = fft_analysis(da_numpy, dx)
            
            data_vars["%s_dftcoe" % (varname,)] = ( ["time", "wavenumber", "complex"], dft_coe )
            
        
        data_vars["time_bnd"] = ds["time_bnd"]
        
        new_ds = xr.Dataset(
            data_vars=data_vars,
            coords=dict(
                time = ds.coords['time'],
                wavenumber = (["wavenumber",] , )
                comoplex = ["real", "imag"],
            ),
            attrs=dict(description="Spectral data"),
        )

        print("Output: ", output_full_filename)
        new_ds.to_netcdf(
            output_full_filename,
            unlimited_dims="time",
            encoding={'time':{'units':'hours since 1970-01-01'}}
        )


        result['status'] = 'OK'

    
    except Exception as e:
        result['status'] = 'ERROR'
        traceback.print_exc()

    return result





for i in range(number_of_output_files):

    reltime_rngs = []
        
    reltime_beg_of_file = reltime_beg + i * time_interval_per_file
    time_beg_of_file = exp_beg_time + reltime_beg_of_file

    for j in range(args.output_count):
        
        reltime_rngs.append(
            [ 
                reltime_beg_of_file + j     * time_avg_interval,
                reltime_beg_of_file + (j+1) * time_avg_interval,
            ]
        )

    filename = os.path.join(
        args.output_dir,
        "analysis_{timestr:s}.nc".format(
            timestr = time_beg_of_file.strftime("%Y-%m-%d_%H:%M:%S"),
        )
    )

    if os.path.exists(filename):
        print("File %s already exists. Skip it." % (filename,))
        continue

   
    input_args.append(
        (
            args.input_dir,
            args.input_dir_base,
            filename,
            args.exp_beg_time,
            args.wrfout_data_interval,
            args.frames_per_wrfout_file,
            reltime_rngs,
            avg_before_analysis,
            args.analysis_style,
        )
    )



failed_files = []
with Pool(processes=args.nproc) as pool:

    results = pool.starmap(genAnalysis, input_args)

    for i, result in enumerate(results):
        if result['status'] != 'OK':
            print('!!! Failed to generate output : %s.' % (result['output_filename'],))
            failed_files.append(result['output_filename'])


print("Tasks finished.")

print("Failed files: ")
for i, failed_file in enumerate(failed_files):
    print("%d : %s" % (i+1, failed_file,))


print("Done")
