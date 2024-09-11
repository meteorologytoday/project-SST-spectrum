import numpy as np
import xarray as xr
import traceback
import os
import pathlib 
import pandas as pd


datatypes = ["mean", "anom"]

doing_varname = dict(
    mean = "sst",
    anom = "anom",
)

varname_mapping = dict(
    sst = "sst",
    anom = "ssta",
)


input_dir = "/home/t2hsu/SO2_t2hsu/project-SST-spectrum/data/physical/sst_raw/oisst"
input_file_fmt = "sst.day.{datatype:s}.{year:04d}.nc"

output_dir_fmt = "/home/t2hsu/SO2_t2hsu/project-SST-spectrum/data/physical/{varname:s}/oisst"
output_file_fmt = "oisst_physical_{varname:s}_{year:04d}.nc"

year_rng = [1982, 2023]
days_per_pentad = 5
pentads_per_year = 73


for datatype in datatypes:

    varname = doing_varname[datatype]
    new_varname = varname_mapping[varname]

    output_dir = output_dir_fmt.format(varname=new_varname)
 
    print("Making output folder if not exists: ", output_dir)
    pathlib.Path(output_dir).mkdir(parents=True, exist_ok=True)

    for year in range(year_rng[0], year_rng[1]+1):

        print("Processing year %04d" % (year,))
        
        output_filename = output_file_fmt.format(
            year = year,
            varname = new_varname,
        )

        output_full_filename = os.path.join(output_dir, output_filename)

        if os.path.exists(output_full_filename):
            print("File %s already exists. Skip." % (output_full_filename,))

            continue


        input_filename = input_file_fmt.format(
            year = year,
            datatype = datatype,
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


        time_bnd = [ [None, None] for _ in range(Nt) ]
        pentadstamp = [ None for _ in range(Nt) ]
        for i in range(Nt):
            beg_dt = t0 + pd.Timedelta(days=days_per_pentad * i)
            end_dt = t0 + pd.Timedelta(days=days_per_pentad * (i+1))
            time_bnd[i][0] = beg_dt
            time_bnd[i][1] = end_dt
            
            pentadstamp[i] = beg_dt.year * pentads_per_year + i

        
        new_data = dict()
        for _varname in [varname, ]:  # Make it into a loop for future flexibility
            d = np.zeros((Nt, ds.dims["lat"], ds.dims["lon"]))
            da = ds[_varname]
            for i in range(Nt):
                d[i, :, :] = da.isel(time=slice(i*5, (i+1)*5)).mean(dim="time").to_numpy()

            new_data[new_varname] = ( ["pentadstamp", "lat", "lon"], d )

       
        new_data["time_bnd"] = ( ["pentadstamp", "num_of_bnd"], time_bnd )

        new_ds = xr.Dataset(
            data_vars=new_data,
            coords=dict(
                pentadstamp = ( ["pentadstamp", ] , pentadstamp),
                lat=ds.coords["lat"],
                lon=ds.coords["lon"],
            ),
            attrs=dict(description="Weather related data."),
        )


        print("Output: ", output_full_filename)
        new_ds.to_netcdf(
            output_full_filename,
            unlimited_dims="pentadstamp",
            encoding={'time_bnd':{'units':'hours since 1970-01-01'}},
        )
















