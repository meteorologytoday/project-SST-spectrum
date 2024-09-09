import argparse
from scipy.io import savemat
import numpy as np
import xarray as xr
import pandas as pd
from datetime import datetime
import traceback
import pickle
from pathlib import Path
import os, os.path

from multiprocessing import Pool

import hycom_share
parser = argparse.ArgumentParser(
                    prog = 'postprocess_ECCO.py',
                    description = 'Postprocess ECCO data (Mixed-Layer integrated).',
)

parser.add_argument('--dataset-info', type=str, required=True)
parser.add_argument('--dataset-name', type=str, required=True)
parser.add_argument('--beg-date', type=str, required=True)
parser.add_argument('--end-date', type=str, required=True)
parser.add_argument('--lat-rng', type=float, nargs=2, default=[-90, 90])
parser.add_argument('--lon-rng', type=float, nargs=2, default=[0, 360])
parser.add_argument('--output-dir', type=str, default="downloaded_hycom_data")
parser.add_argument('--output-formats', type=str, nargs='+', default=["netcdf"], choices=["netcdf", "mat"])
parser.add_argument('--varnames', type=str, nargs='+', default=['water_u', 'water_v', 'water_temp', 'salinity', 'surf_el'], choices=['water_u', 'water_v', 'water_temp', 'salinity', 'surf_el'])
parser.add_argument('--nproc', type=int, default=1)

args = parser.parse_args()
print(args)

beg_date = args.beg_date
end_date = args.end_date

with open(args.dataset_info, 'rb') as handle:
    dataset_info = pickle.load(handle)

print("Available dataset names: ")
for i, dataset_name in enumerate(dataset_info.keys()):
    print("(%d) %s" % (i, dataset_name,))

print("Use: ", args.dataset_name)

if not ( args.dataset_name in dataset_info ):
    raise Exception("The dataset_name %s does not exist." % (args.dataset_name,))

dataset_info = dataset_info[args.dataset_name]
saved_varnames = args.varnames

def lookupSubsetByDate(dataset_info, dt):

    found_subset_names = []    
    for subset_name, subset_info in dataset_info.items():

        beg_dt = pd.Timestamp(subset_info['time_rng'][0])
        end_dt = pd.Timestamp(subset_info['time_rng'][1])

        if dt >= beg_dt and dt <= end_dt:
            found_subset_names.append(subset_name)

    return found_subset_names
        



    
def work(dt, fmt_and_output_filename):
    
    status = 0

    try:
         
        found_subset_names = lookupSubsetByDate(dataset_info, dt)
        dt_str = dt.strftime("%Y-%m-%d")

        if len(found_subset_names) == 0:
            raise Exception("Cannot find data of the date %s." % (dt.strftime("%Y-%m-%d"),))

        elif len(found_subset_names) >= 2:
            print("Warning: the data of date %s is found in more than one subsets: %s ." % (dt_str, ", ".join(found_subset_names)))
            print("Warning: I will use the first one.")

        subset_name = found_subset_names[0]
        subset_info = dataset_info[subset_name]

        url = "%s/%s/%s" % (hycom_share.incomplete_OpenDAP_URL, subset_info['dataset'], subset_name)

        lon_beg = subset_info['lon_beg']
        depth = subset_info['depth']
        lat = subset_info['lat']
        raw_lon = subset_info['lon']
        hycom_time = subset_info['time']

        rotated_lon = np.roll(raw_lon, - lon_beg, axis=0) % 360.0

        lon1, lon2, lat1, lat2 = hycom_share.findRegion_latlon(lat, args.lat_rng, rotated_lon, args.lon_rng)

        #lon1 = 2244
        #lon2 = 3056

        #lat1 = 1720
        #lat2 = 2506

        #xl = [2244:1:3056];
        #yl = [1720:1:2506];
 
        print("Found range: (%d, %d) x (%d, %d)" % (lon1, lon2, lat1, lat2))

        # construct the mapping between lon and nonrotated lon
        raw_nlon = len(raw_lon)
        new_nlon = lon2 - lon1 + 1
        lon_idx = np.zeros((new_nlon,), dtype=int)
        for i in range(new_nlon):
            lon_idx[i] = (lon_beg + lon1 + i) % (raw_nlon)
        
        time_idx = [ hycom_share.findfirst(hycom_time == hycom_share.datetime2hycomTime(dt)) ,]
        print("Opening OpenDAP url: ", url)
        with xr.open_dataset(url, decode_times=False) as ds:
            
            if not np.all(ds.coords['time'] == hycom_time):
                raise Exception("Time coordinate does not match with the dataset_info file. Please check.")

            if not np.all(ds.coords['lat'] == lat):
                raise Exception("Lat coordinate does not match with the dataset_info file. Please check.")

            if not np.all(ds.coords['lon'] == raw_lon):
                raise Exception("Lon coordinate does not match with the dataset_info file. Please check.")

            if not np.all(ds.coords['depth'] == depth):
                raise Exception("Depth coordinate does not match with the dataset_info file. Please check.")


                

            indexer = {
                'lat'  : slice(lat1, lat2+1),
                'lon'  : lon_idx,
                'time' : time_idx,
            }

            
            new_time_arr = [hycom_share.hycomTime2Datetime(hycom_time[time_idx[0]]), ]
            new_time = xr.DataArray(
                data = new_time_arr,
                dims=["new_time"],
                coords=dict(
                    new_time=new_time_arr,
                    reference_time = pd.Timestamp('2000-01-01 00:00:00'),
                ),
            ).rename('new_time')

            new_ds = []
            for varname in saved_varnames:

                    
                pulling_varname = varname
                if varname == "sst":
                    indexer["depth"] = 0
                    pulling_varname = 

                print("Pulling variable data %s from hycom %s " % (varname, pulling_varname))

                pulled_data = ds[pulling_varname][indexer]

                coords = {
                    k : v for k, v in pulled_data.coords.items() 
                }

                coords['time'] = new_time_arr
                coords['lon']  = coords['lon'] % 360.0
                coords['reference_time'] = pd.Timestamp('2000-01-01 00:00:00')

                new_ds.append(xr.DataArray(
                    data = pulled_data.to_numpy().astype('float64'),
                    dims = pulled_data.dims,
                    coords = coords,
                ).rename(varname))

            new_ds = xr.merge(new_ds)
            for output_fmt, output_filename in fmt_and_output_filename.items():
            
                if output_fmt == 'netcdf':
                    print("Output filename: ", output_filename)
                    new_ds.to_netcdf(
                        output_filename,
                        unlimited_dims = ["time",],
                    )

                elif output_fmt == 'mat':

                    # This section is to produce output compatible for matlab version
                    # that keep generating the boundary and initial condition files.

                    D = {
                        'Longitude' : new_ds.coords['lon'].to_numpy(),
                        'Latitude'  : new_ds.coords['lat'].to_numpy(),
                        'Date'      : [ hycom_time[time_idx[0]], ],
                    }
                        

                    if 'depth' in new_ds.coords:
                        z = - new_ds.coords['depth'].to_numpy()
                        z = np.concatenate((z, [-6500.0]))
                        D['Depth'] = z

                    for k in ['Longitude', 'Latitude']:
                        D[k] = D[k][np.newaxis, :]
 
                    for k in ['Depth']:
                        D[k] = D[k][:, np.newaxis]
                        
                    for varname in saved_varnames:

                        tmp = new_ds[varname].to_numpy()
                        tmp[np.isnan(tmp)] = 0.0

                        if varname in ['water_u', 'water_v', 'water_temp', 'salinity']:

                            tmp = np.concatenate(
                                (tmp, tmp[:, -1:, :, :]),
                                axis=1
                            )

                            D[varname] = np.transpose(
                                tmp,
                                axes=(0, 3, 2, 1),
                            )[0, :, :, :]

                        elif varname in ['surf_el']:
                            D[varname] = np.transpose(
                                tmp,
                                axes=(0, 2, 1)
                            )[0, :, :]

                    print("Output filename: ", output_filename)
                    savemat(output_filename, {'D' : D})
               


    except Exception as e:
        traceback.print_exc()
        status = 1

    
    return {
        'date'   : dt_str,
        'status' : status,
    }



print("Create dir: %s" % (args.output_dir,))
Path(args.output_dir).mkdir(parents=True, exist_ok=True)

failed_dates = []   
with Pool(processes=args.nproc) as pool:

    dts = list(pd.date_range(beg_date, end_date, inclusive="both"))


    params = []
    for i, dt in enumerate(dts):
     
        dt_str = dt.strftime("%Y-%m-%d_%H")
        fmt_and_output_filename = {}
 
        for fmt in args.output_formats:

            ext = {'netcdf':'nc', 'mat': 'mat'}[fmt]
            fmt_and_output_filename[fmt] = "%s/hycom_%s.%s" % (args.output_dir, dt_str, ext)


        all_exists = True
        for fmt, output_filename in fmt_and_output_filename.items():
            all_exists = all_exists and os.path.isfile(output_filename)

        if all_exists:
            print("Skip the date %s because files all exist." % (dt_str,))
            continue

        params.append((dts[i], fmt_and_output_filename))
        


    for result in pool.starmap(work, params):

        if result['status'] != 0:
            print("Something is wrong with date: %s" % (result['date'],))
            failed_dates.append(result['date'])


print("Tasks finished.")

if len(failed_dates) == 0:
    print("Success!")
else:
    print("Failed dates: ")
    for i, failed_date in enumerate(failed_dates):
        print("%d : %s" % (i+1, failed_date,))




 
