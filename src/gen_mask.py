from pathlib import Path
import numpy as np
import xarray as xr
import pandas as pd
import argparse
import traceback
import os
import pretty_latlon

import data_loader
import PentadTools as ptt


pretty_latlon.default_fmt = "%d"

parser = argparse.ArgumentParser(
                    prog = 'make_ECCC_AR_objects.py',
                    description = 'Postprocess ECCO data (Mixed-Layer integrated).',
)

parser.add_argument('--test-dataset',     type=str, default="MUR")
parser.add_argument('--test-timepentad', type=str, default="2018P00")
parser.add_argument('--label', type=str, required=True)
parser.add_argument('--output', type=str, required=True)
args = parser.parse_args()
print(args)


test_tp = ptt.TimePentad(args.test_timepentad)

print("Test dataset: ", args.test_dataset)
print("Test pentadstamp: ", test_tp)
print("Used label: ", args.label)

ds = data_loader.load_dataset(
    dataset = args.test_dataset,
    datatype = "cropped",
    label = args.label,
    varname = "sst",
    tp_beg = test_tp,
    tp_end = test_tp,
    inclusive = "both",
)

test_da = ds["sst"].isel(pentadstamp=0).load()

regions = [
    "NPAC", "NPAC_SOUTH", "NPAC_NORTH", 
]


mask = xr.apply_ufunc(np.isfinite, test_da)
base_mask = mask.to_numpy().astype(int)

# Copy is necessary so that the value can be assigned later
mask = mask.expand_dims(
    dim = dict(region=regions),
    axis=0,
).rename("mask").copy()

masks = np.zeros(
    (len(regions), len(mask.coords["lat"]), len(mask.coords["lon"]),),
    dtype=int,
)

for i, region in enumerate(regions):
   
    print("Making region: ", region) 
    _mask = mask.sel(region=region).copy()
    

    if region == "NPAC":
        
        _mask = _mask.where(
            (_mask.lat > 0) &
            (_mask.lat <= 60) &
            (_mask.lon > 120) &
            (_mask.lon <= 250) 
        )

    elif region == "NPAC_SOUTH":
        
        _mask = _mask.where(
            (_mask.lat > 10) &
            (_mask.lat <= 50) &
            (_mask.lon > 150) &
            (_mask.lon <= 230) 
        )


    elif region == "NPAC_NORTH":
        
        _mask = _mask.where(
            (_mask.lat > 20) &
            (_mask.lat <= 60) &
            (_mask.lon > 150) &
            (_mask.lon <= 230) 
        )

 
    else:
        
        print("Warning: Cannot find code to define region `%s`." % (region,))
        continue 
    _mask = xr.apply_ufunc(np.isfinite, _mask)
    mask[i, :, :] = _mask.to_numpy().astype(int) * base_mask

new_ds = xr.merge([mask, ])


output_dir = os.path.dirname(args.output)
Path(output_dir).mkdir(parents=True, exist_ok=True)

new_ds.to_netcdf(args.output)
