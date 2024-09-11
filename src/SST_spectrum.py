import traceback
from multiprocessing import Pool
import multiprocessing
import pathlib
import os

import numpy as np
import xarray as xr
import scipy
import pandas as pd
import argparse

import PentadTools as pentt
import data_loader 

parser = argparse.ArgumentParser(
                    prog = 'plot_skill',
                    description = 'Plot prediction skill of GFS on AR.',
)

parser.add_argument('--dataset', type=str, help='Input file', required=True)
parser.add_argument('--year-rng', type=int, nargs=2, help='Time range in Pentad', required=True)
parser.add_argument('--lat-rng', type=float, nargs=2, help='The lat axis range to be plot in km.', default=[None, None])
parser.add_argument('--lon-rng', type=float, nargs=2, help='The lon axis range to be plot in km.', default=[None, None])
parser.add_argument('--spectral-dir', type=str, help='The direction to do fft. Can be `lat` or `lon`.', choices=['lat', 'lon'], required=True)
parser.add_argument('--label', type=str, help='Label for this.', required=True)
parser.add_argument('--nproc', type=int, help='The lon axis range to be plot in km.', default=1)

args = parser.parse_args()
print(args)

def fft_analysis(d, dx):

    Nt = d.shape[0]
    Nx = d.shape[1]
    necessary_N = Nx // 2

    #d_m = np.nanmean(d, axis=1, keepdims=True)
    #d_a = d - d_m

    d_a = np.zeros_like(d)
    x = np.arange(Nx)
    for t in range(Nt):
        m, b = np.polyfit(x, d[t, :], 1)
        d_a[t, :] = d[t, :] - (m * x + b) 
 
    dft_coe = np.fft.fft(d_a, axis=1) / Nx
    wvlens = dx / np.fft.fftfreq(Nx)
    
    necessary_N = Nx // 2
    dft_coe = dft_coe[:, 0:necessary_N]
    wvlens = wvlens[0:necessary_N]

    dft_coe_2d = np.zeros((dft_coe.shape[0], necessary_N, 2), dtype=float)
    dft_coe_2d[:, :, 0] = np.real(dft_coe)
    dft_coe_2d[:, :, 1] = np.imag(dft_coe)
    
    dft_coe_2d_radiphas = np.zeros((dft_coe.shape[0], necessary_N, 2), dtype=float)
    dft_coe_2d_radiphas[:, :, 0] = np.abs(dft_coe)
    dft_coe_2d_radiphas[:, :, 1] = np.angle(dft_coe)

    return dft_coe_2d, dft_coe_2d_radiphas, wvlens

def work(
    details,
):

    lat_rng = details["lat_rng"]   
    lon_rng = details["lon_rng"]   
    phase = details["phase"]   
    dataset = details["dataset"]   
    year = details["year"]
    varname = details["varname"] 
    spectral_dir = details["spectral_dir"] 
    label = details["label"]
    
    result = dict(
        year = year,
        need_work = False,
        status='UNKNOWN',
    )

    try:

        input_full_filename = os.path.join(
            data_loader.getFilenameFromYear(
                dataset = dataset,
                datatype = "physical",
                varname = varname,
                year = year,
            ) 
        )

        output_full_filename = os.path.join(
            data_loader.getFilenameFromYear(
                dataset = dataset,
                datatype = "spectral",
                varname = varname,
                year = year,
                label = label,
            )
        )

        result["output_full_filename"] = output_full_filename

        if phase == "detect":
            
            if not os.path.exists(output_full_filename):
                result["need_work"] = True
            
            return result
            


        data_vars = {}

        ds = data_loader.load_dataset(dataset, "physical", varname, "%dP0" % (year,), "%dP72" % (year,))
        coords = { 
            coord_varname : ds.coords[coord_varname].to_numpy() for coord_varname in ds.coords 
        }

        dlat = coords["lat"][1] - coords["lat"][0]
        dlon = coords["lon"][1] - coords["lon"][0]

 
        da = ds[varname].sel(lat=slice(*args.lat_rng), lon=slice(*args.lon_rng))
       
        if spectral_dir == "lat": 
            Nx = len(da.coords["lat"])
            dx = dlat
            da = da.mean(dim="lon")

        elif spectral_dir == "lon": 
            Nx = len(da.coords["lon"])
            dx = dlon
            da = da.mean(dim="lat")

        else:

            raise Exception("Unknown spectral_dir = %s" % (str(spectral_dir)))
       
        Lx = dx * Nx
        da_numpy = da.to_numpy()
        #SST_nonan = SST.copy()
        #SST_nonan[np.isnan(SST_nonan)] = 0.0

        # Spectral analysis
        if np.any(np.isnan(da_numpy)):
            print("Warning: Data `%s` contains NaN." % (varname,))

        dft_coe_form1, dft_coe_form2, wvlens = fft_analysis(da_numpy, dx)
        
        data_vars["dftcoe_form1"] = ( ["pentadstamp", "wvlen", "complex_realimag"], dft_coe_form1 )
        data_vars["dftcoe_form2"] = ( ["pentadstamp", "wvlen", "complex_radiphas"], dft_coe_form2 )
        
        data_vars["time_bnd"] = ds["time_bnd"]
        
        new_ds = xr.Dataset(
            data_vars=data_vars,
            coords=dict(
                pentadstamp = ds.coords['pentadstamp'],
                wvlen = (["wvlen",] , wvlens),
                wavenumber = (["wvlen",] , list(np.arange(len(wvlens)))),
                complex_realimag = ["real", "imag"],
                complex_radiphas = ["radius", "phase"],
            ),
            attrs=dict(
                description="Spectral data",
                Lx = Lx,
                dx = dx,
            ),
        )

        output_dir = os.path.dirname(output_full_filename)
        print("Making output folder if not exists: ", output_dir)
        pathlib.Path(output_dir).mkdir(parents=True, exist_ok=True)

        print("Output: ", output_full_filename)
        new_ds.to_netcdf(
            output_full_filename,
            unlimited_dims="pentadstamp",
        )


        result['status'] = 'OK'

    
    except Exception as e:
        
        result['status'] = 'ERROR'
        traceback.print_exc()

    return result


input_args = []
for year in range(args.year_rng[0], args.year_rng[1]+1):

    details = dict(
        lat_rng = args.lat_rng,
        lon_rng = args.lon_rng,
        dataset = args.dataset,
        year = year,
        varname = 'ssta',
        spectral_dir = args.spectral_dir,
        label = args.label,
    )

    details["phase"] = "detect"

    test = work(details)

    if test["need_work"]:
        details["phase"] = "work"
        input_args.append(
            ( details, )
        )
    else:
        print("Output file `%s` already exists. Skip." % (test["output_full_filename"],))


failed_files = []
with Pool(processes=args.nproc) as pool:

    results = pool.starmap(work, input_args)

    for i, result in enumerate(results):
        if result['status'] != 'OK':
            print('!!! Failed to generate output : %s.' % (result['output_full_filename'],))
            failed_files.append(result['output_full_filename'])


print("Tasks finished.")

print("Failed files: ")
for i, failed_file in enumerate(failed_files):
    print("%d : %s" % (i+1, failed_file,))


print("Done")
