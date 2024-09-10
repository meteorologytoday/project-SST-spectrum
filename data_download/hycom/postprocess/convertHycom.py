import xarray as xr
import numpy as np
import pandas as pd
import argparse
import convert_grid

def convertHycomGridToMitgcm(input, output, varname, updated_varname, grid_type, grid_dir, iter_max, check_rng, extend_downward):

    ds_hycom = xr.open_dataset(input)

    ZC1 = - ds_hycom.coords["depth"].to_numpy()
    YC1 =   ds_hycom.coords["lat"].to_numpy()
    XC1 =   ds_hycom.coords["lon"].to_numpy()

    interpolated_data, grid2 = convert_grid.convertGrid(ds_hycom[varname][0, :, :, :].to_numpy(), grid_type, XC1, YC1, ZC1, grid2_dir=grid_dir, fill_value=-999, iter_max=iter_max, check_rng = check_rng, extend_downward = extend_downward)

    da_output = xr.DataArray(
        data = np.expand_dims(interpolated_data, 0),
        dims = ["time", "z", "lat", "lon"],
        coords = dict(
            lon=(["lon"], grid2['X']),
            lat=(["lat"], grid2['Y']),
            z=(["z"], grid2['Z']),
            time=ds_hycom.coords["time"],
            reference_time=pd.Timestamp('2000-01-01'),
        ),
    ).rename(updated_varname) 

    print("Output file: ", output)
    da_output.to_netcdf(output, unlimited_dims="time")



if __name__ == "__main__":
    
    parser = argparse.ArgumentParser(description='This program interpolate')
    parser.add_argument('--input', type=str, required=True, help='Input hycom data file')
    parser.add_argument('--output', type=str, required=True, help='Output filename.')
    parser.add_argument('--varname', type=str, required=True, help='Output filename.')
    parser.add_argument('--grid-type', type=str, required=True, help='Output filename.')
    parser.add_argument('--grid-dir', type=str, required=True, help='MITgcm grid folder.')
    parser.add_argument('--iter-max', type=int, default=50, help='Max iteration when doing data filling.')
    parser.add_argument('--check-rng', type=float, nargs=2, default=[-np.inf, np.inf], help='Check range.')
    args = parser.parse_args()

    print(args)



    updated_varname = {
        'water_u'    : 'U',
        'water_v'    : 'V',
        'water_temp' : 'T',
        'salinity'   : 'S',
    }[args.varname]

    convertHycomGridToMitgcm(args.input, args.output, args.varname, updated_varname, args.grid_type, args.grid_dir, args.iter_max, args.check_rng)

