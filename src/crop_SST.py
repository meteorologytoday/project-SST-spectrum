import traceback
from multiprocessing import Pool
import multiprocessing
import pathlib
import os

import numpy as np
import xarray as xr
import dask
import scipy
import pandas as pd
import argparse

import PentadTools as pentt
import data_loader 
        
dask.config.set(**{'array.slicing.split_large_chunks': True}) 

parser = argparse.ArgumentParser(
                    prog = 'plot_skill',
                    description = 'Plot prediction skill of GFS on AR.',
)

parser.add_argument('--dataset', type=str, help='Input file datasets. ', required=True)

parser.add_argument('--timepentad-rng', type=str, nargs=2, help="TimePetand range.", required=True)
parser.add_argument('--lat-rng', type=float, nargs=2, help='The lat axis range to be plot in km.', default=[None, None])
parser.add_argument('--lon-rng', type=float, nargs=2, help='The lon axis range to be plot in km.', default=[None, None])
parser.add_argument('--res-deg', type=float, help='The resolution in degree.', default=[None, None])
parser.add_argument('--x-dim', type=str, help='The direction to be averaged. Can be `lat` or `lon`.', choices=['lat', 'lon'], required=True)
parser.add_argument('--label', type=str, help='Label for this.', required=True)
parser.add_argument('--nproc', type=int, help='The lon axis range to be plot in km.', default=1)

args = parser.parse_args()
print(args)

def work(
    details,
):

    lat_rng = details["lat_rng"]   
    lon_rng = details["lon_rng"]   
    dx = details["dx"]   
    phase = details["phase"]   
    dataset = details["dataset"]
    tp = details["tp"]
    varname = details["varname"] 
    x_dim = details["x_dim"] 
    label = details["label"]
    
    result = dict(
        tp = tp,
        need_work = False,
        status='UNKNOWN',
    )

    try:
        
        if x_dim not in ["lat", "lon"]:    
            raise Exception("Unknown x_dim = %s" % (str(x_dim)))

        output_full_filename = os.path.join(
            data_loader.getFilenameFromTimePentad(
                dataset = dataset,
                datatype = "cropped",
                varname = varname,
                tp = tp,
                label = label,
            )
        )

        result["output_full_filename"] = output_full_filename

        if phase == "detect":
            
            if not os.path.exists(output_full_filename):
                result["need_work"] = True
            
            return result
            
        data_vars = {}

        ds = data_loader.load_dataset(dataset, "physical", varname, tp, tp, inclusive="both")
         
        print("Subsetting data...")
        da = ds[varname].sel(lat=slice(*lat_rng), lon=slice(*lon_rng))
         
        if x_dim == "lat":
            avg_dim = "lon" 
            new_x = np.arange(lat_rng[0], lat_rng[1], dx)

        elif x_dim == "lon": 
            avg_dim = "lat" 
            new_x = np.arange(lon_rng[0], lon_rng[1], dx) 


        print("Doing avg...")
        da = da.mean(dim=avg_dim)
        
        print("Interpolation...")
        
        x_beg = da.coords[x_dim].to_numpy()[0]
        x_end = da.coords[x_dim].to_numpy()[-1]
        
        """
        # find the first and last new_x point that can be interpolated
        for i, x in enumerate(new_x):
            if x >= x_beg:
                new_x = new_x[i:]
                break
 
        for i in range(len(new_x)):

            test_idx = len(new_x) - i - 1
            if new_x[test_idx] <= x_end:
                new_x = new_x[:(test_idx+1)]
                break
        """

        da = da.interp(coords={x_dim : new_x}, method="linear")
 
        x = da.coords[x_dim].to_numpy()

        print("Converting to numpy..")
        da_numpy = da.to_numpy()

        if np.any(np.isnan(da_numpy)):
            print("Warning: Data `%s` contains NaN." % (varname,))
        
        pentadstamp = ds.coords["pentadstamp"]

        data_vars[varname] = ( ["pentadstamp", "x"], da_numpy)
        data_vars["time_bnd"] = ds["time_bnd"]
 
        new_ds = xr.Dataset(

            data_vars=data_vars,

            coords=dict(
                pentadstamp = ds.coords['pentadstamp'],
                x = (["x",], x), 
            ),

            attrs=dict(
                description="Cropped data",
                avg_dim = avg_dim,
                x_dim = x_dim,
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
tps = list(pentt.pentad_range(args.timepentad_rng[0], args.timepentad_rng[1], inclusive="left"))
for tp in tps:

    details = dict(
        lat_rng = args.lat_rng,
        lon_rng = args.lon_rng,
        dataset = args.dataset,
        tp = tp,
        varname = 'sst',
        x_dim = args.x_dim,
        label = args.label,
        dx = args.res_deg,
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
