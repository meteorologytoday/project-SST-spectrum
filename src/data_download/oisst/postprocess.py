import numpy as np
import xarray as xr
import traceback
import os
from pathlib import Path 
import pandas as pd
import argparse

parser = argparse.ArgumentParser(
                    prog = 'plot_skill',
                    description = 'Plot prediction skill of GFS on AR.',
)

parser.add_argument('--input-root', type=str, help='Input file datasets. ', required=True)
parser.add_argument('--output-root', type=str, help='Input file datasets. ', required=True)
parser.add_argument('--year-rng', type=int, nargs=2, help='Year range.', required=True)
args = parser.parse_args()
print(args)


datatypes = ["mean", "anom"]

doing_varname = dict(
    mean = "sst",
    anom = "anom",
)

varname_mapping = dict(
    sst = "sst",
    anom = "ssta",
)


input_root = Path(args.input_root)
input_file_fmt = "sst.day.{datatype:s}.{year:04d}.nc"

output_file_fmt = "oisst_physical_{varname:s}_{year:04d}P{pentad:02d}.nc"

year_rng = args.year_rng
days_per_pentad = 5
pentads_per_year = 73


for datatype in datatypes:

    varname = doing_varname[datatype]
    new_varname = varname_mapping[varname]


    output_dir = Path(args.output_root) / "physical" / new_varname / "oisst"
 
    print("Making output folder if not exists: ", output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    for year in range(year_rng[0], year_rng[1]+1):
        
        input_filename = input_file_fmt.format(
            year = year,
            datatype = datatype,
        )

        input_full_filename = input_root / input_filename

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

        for pentad in range(pentads_per_year):

            print("Processing year %04dP%02d" % (year, pentad))
            
            output_filename = output_file_fmt.format(
                year = year,
                pentad = pentad,
                varname = new_varname,
            )

            output_full_filename = output_dir / output_filename

            if os.path.exists(output_full_filename):
                print("File %s already exists. Skip." % (output_full_filename,))
                continue

            

            beg_dt = t0 + pd.Timedelta(days=days_per_pentad * pentad)
            end_dt = t0 + pd.Timedelta(days=days_per_pentad * (pentad+1))

            time_bnd = [ [beg_dt, end_dt] , ]
            pentadstamp = [ year * pentads_per_year + pentad , ]

            new_data = dict()
            for _varname in [varname, ]:  # Make it into a loop for future flexibility
                d = np.zeros((1, ds.dims["lat"], ds.dims["lon"]))
                d[0, :, :] = ds[_varname].isel(time=slice(pentad*days_per_pentad, (pentad+1)*days_per_pentad)).mean(dim="time").to_numpy()

                if varname == "sst":
                    d += 273.15

                new_data[new_varname] = ( ["pentadstamp", "lat", "lon"], d )

           
            new_data["time_bnd"] = ( ["pentadstamp", "num_of_bnd"], time_bnd )

            new_ds = xr.Dataset(
                data_vars=new_data,
                coords=dict(
                    pentadstamp = ( ["pentadstamp", ] , pentadstamp),
                    lat=ds.coords["lat"],
                    lon=ds.coords["lon"],
                ),
                attrs=dict(description="Postprocessed OISST data."),
            )


            print("Output: ", output_full_filename)
            new_ds.to_netcdf(
                output_full_filename,
                unlimited_dims="pentadstamp",
                encoding={'time_bnd':{'units':'hours since 1970-01-01'}},
            )
















