import numpy as np
import xarray as xr
import traceback
import os
import pathlib 
import pandas as pd

def findfirst(a):
    
    for i in range(len(a)):
        if a[i]:
            return i

    return -1



dataset = "ostia"

input_dir = "/home/t2hsu/SO2_t2hsu/project-SST-spectrum/data/physical/sst_raw/{dataset:s}".format(dataset=dataset)
input_file_fmt = "{datestr:s}120000-UKMO-L4_GHRSST-SSTfnd-OSTIA-GLOB_REP-v02.0-fv02.0.nc"

output_dir_fmt = "/home/t2hsu/SO2_t2hsu/project-SST-spectrum/data/physical/{varname:s}/{dataset:s}"
output_file_fmt = "{dataset:s}_physical_{varname:s}_{year:04d}.nc"

year_rng = [2018, 2018]
days_per_pentad = 5
pentads_per_year = 73


varnames = {
    "analysed_sst" : "sst",
}




for varname, new_varname in varnames.items():

    output_dir = output_dir_fmt.format(
        dataset = dataset,
        varname=new_varname,
    )
    print("Making output folder if not exists: ", output_dir)
    pathlib.Path(output_dir).mkdir(parents=True, exist_ok=True)

    for year in range(year_rng[0], year_rng[1]+1):

        print("Processing year %04d" % (year,))
        
        output_filename = output_file_fmt.format(
            year = year,
            varname = new_varname,
            dataset = dataset,
        )

        output_full_filename = os.path.join(output_dir, output_filename)

        if os.path.exists(output_full_filename):
            print("File %s already exists. Skip." % (output_full_filename,))

            continue

        required_dts = pd.date_range(
            pd.Timestamp(year=year, month=1, day=1),
            pd.Timestamp(year=year+1, month=1, day=1),
            freq = "D",
            inclusive="left",
        )
        t0 = required_dts[0]

        Nt = pentads_per_year #len(required_dts) // days_per_pentad
        print("There are %d days of year %d. Break into %d pentads." % (len(required_dts), year, Nt))

        res = len(required_dts) % days_per_pentad
        if res != 0:
            print("There are %d extra data that will be discarded. " % (res,))


        time_bnd = [ [None, None] for _ in range(Nt) ]
        pentadstamp = [ None for _ in range(Nt) ]
        
        d = None
        for i in range(Nt):
            
            print("Doing %04dP%d " % (year, i))
            
            beg_dt = t0 + pd.Timedelta(days=days_per_pentad * i)
            end_dt = t0 + pd.Timedelta(days=days_per_pentad * (i+1))
            time_bnd[i][0] = beg_dt
            time_bnd[i][1] = end_dt
            pentadstamp[i] = beg_dt.year * pentads_per_year + i

            input_full_filenames = []

            for j in range(days_per_pentad):
                
                dt = beg_dt + pd.Timedelta(days=j)
                input_filename = input_file_fmt.format(
                    datestr = dt.strftime("%Y%m%d"),
                )

                input_full_filename = os.path.join(input_dir, input_filename)
                input_full_filenames.append(input_full_filename)

            ds = xr.open_mfdataset(input_full_filenames)
            
            if d is None:
                d = np.zeros((Nt, ds.dims["lat"], ds.dims["lon"]))
                first_nonzero_lon = findfirst(ds.coords["lon"] > 0)
                print("first_nonzero_lon = ", first_nonzero_lon)

            ds = ds.roll(lon=-first_nonzero_lon, roll_coords=True)
            d[i, :, :] = ds[varname].mean(dim="time").to_numpy()
        
        new_data = dict()
        new_data[new_varname] = ( ["pentadstamp", "lat", "lon"], d )
        new_data["time_bnd"] = ( ["pentadstamp", "num_of_bnd"], time_bnd )

        new_ds = xr.Dataset(
            data_vars=new_data,
            coords=dict(
                pentadstamp = ( ["pentadstamp", ] , pentadstamp),
                lat=ds.coords["lat"],
                lon=ds.coords["lon"] % 360,
            ),
            attrs=dict(description="Weather related data."),
        )


        print("Output: ", output_full_filename)
        new_ds.to_netcdf(
            output_full_filename,
            unlimited_dims="pentadstamp",
            encoding={'time_bnd':{'units':'hours since 1970-01-01'}},
        )
















