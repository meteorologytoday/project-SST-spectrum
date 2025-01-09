from multiprocessing import Pool
import traceback
import xarray as xr
import data_loader
import numpy as np
import PentadTools as ptt
import tool_fig_config
import argparse
import pathlib
import os
import matrix_helper

parser = argparse.ArgumentParser(description='Process some integers.')
parser.add_argument('--input-datasets', type=str, nargs="+", help='Input datasets.', required=True)
parser.add_argument('--output-dataset', type=str, help='Output directory.', required=True)
parser.add_argument('--datatype', type=str, required=True)
parser.add_argument('--varname', type=str, required=True)
parser.add_argument('--label', type=str, required=True)
parser.add_argument('--timepentad-rng', type=str, nargs=2, help="Petand range of the year.", required=True)
parser.add_argument('--nproc', type=int, default=2)

args = parser.parse_args()
print(args)

def work(details):

    input_datasets = details['input_datasets']
    output_dataset = details['output_dataset']
    varname = details['varname']
    datatype = details['datatype']
    label = details['label']
    tp = details['tp']
    phase = details['phase']

    result=dict(
        varname = varname,
        tp = tp,
        status="UNKNOWN",
        phase = phase,
        need_work = False
    )


    try:
        output_filename = data_loader.getFilenameFromTimePentad(
            output_dataset,
            datatype,
            varname,
            tp,
            label=label,
        )

        result['output_filename'] = output_filename

        if phase == "detect":
            result['need_work'] = not os.path.exists(output_filename)
            return result
            
        N_datasets = len(input_datasets)

        da = None
        ds = None
        for dataset in input_datasets:
            print("Loading dataset:", dataset)
            ds_tmp = data_loader.load_dataset(
                dataset, datatype, varname, tp, tp, label=label, inclusive="both",
            )
            
            da_tmp = ds_tmp[varname] 
 
            if ds is None:
                ds = ds_tmp
                da = da_tmp
            else:
                da = da + da_tmp

        da /= N_datasets

        ds = ds.drop_vars(varname) 
        
        ds = xr.merge([ds, da])
        ds.attrs["datasets"] = ",".join(input_datasets)
        output_dir = os.path.dirname(output_filename)
        pathlib.Path(output_dir).mkdir(parents=True, exist_ok=True) 

        print("Writing output: ", output_filename) 
        ds.to_netcdf(output_filename)

    except Exception as e:
        
        result['status'] = 'ERROR'
        traceback.print_exc()

    return result

input_args = []
tps = list(ptt.pentad_range(args.timepentad_rng[0], args.timepentad_rng[1], inclusive="both"))

for tp in tps:

    details = dict(
        input_datasets = args.input_datasets,
        output_dataset = args.output_dataset,
        tp = tp,
        datatype = args.datatype,
        varname = args.varname,
        label = args.label,
    )

    details["phase"] = "detect"

    test = work(details)
    print(test)

    if test["need_work"]:
    
        details["phase"] = "work"
        input_args.append(
            ( details, )
        )
    
    else:

        print("Output file `%s` already exists. Skip." % (test["output_filename"],))


failed_files = []
with Pool(processes=args.nproc) as pool:

    results = pool.starmap(work, input_args)

    for i, result in enumerate(results):
        if result['status'] != 'OK':
            print('!!! Failed to generate output : %s.' % (result['output_filename'],))
            failed_files.append(result['output_filename'])


print("Tasks finished.")

print("Failed files: ")
for i, failed_file in enumerate(failed_files):
    print("%d : %s" % (i+1, failed_file,))


print("Done")
