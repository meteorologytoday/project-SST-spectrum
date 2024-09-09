import xarray as xr
import numpy as np
from pathlib import Path
import os, os.path
import pandas as pd
import traceback
import argparse
import convertHycom
from multiprocessing import Pool

parser = argparse.ArgumentParser(
                    prog = 'batch_convert_hycom.py',
                    description = 'Convert hycom data to mitgcm grid in batch.',
)

parser.add_argument('--beg-date', type=str, required=True)
parser.add_argument('--end-date', type=str, required=True)
parser.add_argument('--input-dir', type=str, required=True)
parser.add_argument('--output-dir', type=str, default="output")
parser.add_argument('--varnames', type=str, nargs='+', default=['water_u', 'water_v', 'water_temp', 'salinity'], choices=['water_u', 'water_v', 'water_temp', 'salinity',])
parser.add_argument('--nproc', type=int, default=1)

args = parser.parse_args()
print(args)

beg_date = args.beg_date
end_date = args.end_date


def work(dt, input_filename, output_filename, varname, grid_type,  check_rng):
    
    status = 0


    try:        
        
        dt_str = dt.strftime("%Y-%m-%d")

        print("Processing (date, varname) = (%s, %s)" % (dt_str, varname,))

        convertHycom.convertHycomGridToMitgcm(input_filename, output_filename, varname, grid_type, args.grid_dir, args.iter_max, check_rng)
    

    except Exception as e:
        traceback.print_exc()
        status = 1

    
    return {
        'date'   : dt_str,
        'varname': varname,
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
        
        for varname, grid_type, check_rng in varname_mapping:

            if not ( varname in args.varnames ):
                continue

            input_filename = "%s/hycom_%s.nc" % (args.input_dir, dt_str,)
            output_filename = "%s/hycom_%s_%s.nc" % (args.output_dir, dt_str, varname)

            if os.path.isfile(output_filename):
                print("Skip the (date, varname) = (%s, %s) because it exists." % (dt_str, varname))
                continue

            params.append((dts[i], input_filename, output_filename, varname, grid_type, check_rng))

    for result in pool.starmap(work, params):

        if result['status'] != 0:
            print("Something is wrong with (date, varname) = (%s, %s)" % (result['date'], result['varname']))
            failed_dates.append((result['date'], result['varname']))


print("Tasks finished.")

if len(failed_dates) == 0:
    print("Success!")
else:
    print("Failed dates: ")
    for i, (failed_date, varname) in enumerate(failed_dates):
        print("%d : %s, %s" % (i+1, failed_date, varname))




 
