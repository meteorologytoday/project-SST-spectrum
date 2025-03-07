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

def work(
    details,
):

    phase = details["phase"]   
    label = details["label"]
    datasets = details["datasets"]
    output_dataset = details["output_dataset"]
    tp = details["tp"]
    varname = details["varname"] 
    label = details["label"]
    
    result = dict(
        tp = tp,
        need_work = False,
        status='UNKNOWN',
    )

    try:
        
        output_full_filename = os.path.join(
            data_loader.getFilenameFromTimePentad(
                dataset = output_dataset,
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

        da = None

        for dataset in datasets:
            
            _da = data_loader.getFilenameFromTimePentad(
                    dataset = output_dataset,
                    datatype = "cropped",
                    varname = varname,
                    tp = tp,
                    label = label,
            )[varname]
            
            if da is None:
                da = _da

            else:
                da += _da    
     
        da /= len(datasets)

        da.attrs["datasets"] = ", ".join(datasets)
        
        output_dir = Path(output_full_filename).parent

        print("Making output folder if not exists: ", output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)

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


if __name__ == "__main__":
    
    parser = argparse.ArgumentParser(
                        prog = 'plot_skill',
                        description = 'Plot prediction skill of GFS on AR.',
    )

    parser.add_argument('--input-root', type=str, help='Input file datasets. ', required=True)
    parser.add_argument('--datasets', type=str, nargs="+", help='Input file datasets. ', required=True)
    parser.add_argument('--label', type=str, help='Input file datasets. ', required=True)
    parser.add_argument('--timepentad-rng', type=str, nargs=2, help="TimePetand range.", required=True)
    parser.add_argument('--nproc', type=int, help='The lon axis range to be plot in km.', default=1)

    args = parser.parse_args()
    print(args)


    input_args = []
    tps = list(pentt.pentad_range(args.timepentad_rng[0], args.timepentad_rng[1], inclusive="both"))

    for tp in tps:

        details = dict(
            datasets = args.datasets,
            tp = tp,
            varname = 'sst',
            label = args.label,
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
