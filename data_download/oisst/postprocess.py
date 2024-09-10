import numpy as np
import xarray as xr
import traceback
import os
import pathlib 
import pandas as pd

varnames = ["sst"]
input_dir = "/home/t2hsu/SO2_t2hsu/project-SST-spectrum/data/sst_raw/oisst"
input_file_fmt = "sst.day.mean.{year:04d}.nc"

output_dir = "/home/t2hsu/SO2_t2hsu/project-SST-spectrum/data/sst/oisst"
output_file_fmt = "oisst_{year:04d}.nc"

year_rng = [1982, 2023]
days_per_pentad = 5

print("Making output folder if not exists: ", output_dir)
pathlib.Path(output_dir).mkdir(parents=True, exist_ok=True)

for year in range(year_rng[0], year_rng[1]+1):
    
    print("Processing year %04d" % (year,))
    
    output_filename = output_file_fmt.format(
        year = year,
    )

    output_full_filename = os.path.join(output_dir, output_filename)

    if os.path.exists(output_full_filename):
        print("File %s already exists. Skip." % (output_full_filename,))

        continue


    input_filename = input_file_fmt.format(
        year = year,
    )

    input_full_filename = os.path.join(input_dir, input_filename)

    ds = xr.load_dataset(input_full_filename)
    
    # First, check if there are enough days
    
    t = ds.coords["time"]
    
    test_dts = pd.date_range(
        pd.Timestamp(year=year, month=1, day=1),
        pd.Timestamp(year=year+1, month=1, day=1),
        freq = "D",
        inclusive="left",
    )

    t0 = test_dts[0]

    for i, dt in enumerate(test_dts):
        
        if t[i] != dt:
            print("test t[%d] = %s, dt = %s" % (i, str(t[i]), str(dt))) 
            raise Exception("Some dates are wrong. Year = %d" % (year,)) 

    Nt = len(test_dts) // days_per_pentad
    print("There are %d days of year %d. Break into %d pentads." % (len(test_dts), year, Nt))

    res = len(test_dts) % days_per_pentad
    if res != 0:
        print("There are %d extra data that will be discarded. " % (res,))


    pentad = np.arange(Nt)
    time_bnd = [ [None, None] for _ in range(Nt) ]
    for i in range(Nt):
        time_bnd[i][0] = t0 + pd.Timedelta(days=days_per_pentad * i)
        time_bnd[i][1] = t0 + pd.Timedelta(days=days_per_pentad * (i+1))

    
    new_data = dict()
    for varname in varnames:
        d = np.zeros((Nt, ds.dims["lat"], ds.dims["lon"]))
        da = ds[varname]
        for i in range(Nt):
            d[i, :, :] = da.isel(time=slice(i*5, (i+1)*5)).mean(dim="time").to_numpy()

        new_data[varname] = d

   
    data_vars = {
        varname : ( ["pentad", "lat", "lon"], new_data[varname] )
        for varname in varnames
    }
 
    data_vars["time_bnd"] = ( ["pentad", "num_of_bnd"], time_bnd )

    new_ds = xr.Dataset(
        data_vars=data_vars,
        coords=dict(
            pentad = ( ["pentad", ] , pentad),
            lat=ds.coords["lat"],
            lon=ds.coords["lon"],
        ),
        attrs=dict(description="Weather related data."),
    )

    print("Output: ", output_full_filename)
    new_ds.to_netcdf(output_full_filename, unlimited_dims="pentad")
















