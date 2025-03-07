import xarray as xr
import data_loader
import numpy as np
import PentadTools as ptt
import tool_fig_config
import argparse
import pathlib
import os
import matrix_helper
import dask
import sklearn.decomposition

dask.config.set(**{'array.slicing.split_large_chunks': True})


parser = argparse.ArgumentParser(description='Process some integers.')
parser.add_argument('--datasets', type=str, nargs="+", help='Datasets.', required=True)
parser.add_argument('--output-dir', type=str, help='Output directory.', required=True)
parser.add_argument('--varname', type=str, required=True)
parser.add_argument('--label', type=str, required=True)
parser.add_argument('--pentad-rng', type=int, nargs=2, help="Petand range of the year.", required=True)
parser.add_argument('--year-rng', type=int, nargs=2, help="Year range.", required=True)
parser.add_argument('--mask-file', type=str, help="Mask file. If not supplied, take the whole domain.", default="")
parser.add_argument('--mask-region', type=str, help="Select the region in the mask file.", default="")
parser.add_argument('--overwrite', action="store_true")

args = parser.parse_args()
print(args)

def loadData(dataset, label, varname, year_rng, pentad_rng):

    all_ds = []

    for y in range(year_rng[0], year_rng[1]+1):

        tp_beg = ptt.TimePentad(year=y, pentad=pentad_rng[0])
        tp_end = ptt.TimePentad(year=y, pentad=pentad_rng[1])

        all_ds.append(data_loader.load_dataset(
            dataset = dataset,
            datatype = "cropped",
            label = label,
            varname = varname,
            tp_beg = tp_beg,
            tp_end = tp_end,
            inclusive = "both",
        ))


    ds = xr.merge(all_ds)
    
    return ds




def work(
    output_filename,
    datasets,
    label,
    varname,
    year_rng,
    pentad_rng,
    mask_file = "",
    mask_region = "",
):

    data = []
    data_diff = []

    N_datasets = len(datasets)

    print("Open dataset...")
    for i, dataset in enumerate(datasets):
        print("Loading dataset:", dataset)
        data.append(loadData(dataset, label, varname, year_rng, pentad_rng))

    ref_ds = data[0]
    ref_da = ref_ds[varname]
    Nt = len(ref_ds.coords["pentadstamp"])

    da_mask = None
    if mask_file != "":    
        print("Loading mask file: ", mask_file)
        da_mask = xr.open_dataset(mask_file)["mask"].sel(region=mask_region)

    mask = np.isfinite(ref_da.isel(pentadstamp=0).to_numpy()).astype(int)
    if da_mask is not None:
        mask *= da_mask.to_numpy()

    da_mask[:, :] = mask
    da_mask_idx = da_mask == 1

    for i in range(len(data)):
        data[i] = data[i].where(da_mask_idx)

    dist2_mtx = np.zeros((Nt, N_datasets, N_datasets,))
    for i in range(N_datasets):
        for j in range(i, N_datasets):
            
            print("Computing distance between %s and %s..." % (datasets[i], datasets[j], ))    
            
            da1 = data[i][varname]
            da2 = data[j][varname]
            var = ((da1 - da2)**2.0).var(dim=["lat", "lon",])
            dist2_mtx[:, i, j] = var.to_numpy()
            dist2_mtx[:, j, i] = dist2_mtx[:, i, j]
     
    new_ds = xr.Dataset(
        data_vars = dict(
            dist2_mtx = ( ["pentadstamp", "dataset1", "dataset2"], dist2_mtx),
        ),
        coords = dict(
            pentadstamp = ref_da.coords["pentadstamp"],
            dataset1 = ( ["dataset1",], datasets ),
            dataset2 = ( ["dataset2",], datasets ),
        ),
        attrs = dict(
            varname = varname,
        )
    )
    
    output_dir = os.path.dirname(output_filename)
    if not os.path.exists(output_dir):
        print("Making directory: %s" % (output_dir,))
        pathlib.Path(output_dir).mkdir(parents=True, exist_ok=True) 

    print("Writing output: ", output_filename) 
    new_ds.to_netcdf(output_filename)


output_filename = os.path.join(
    args.output_dir,
    args.label,
    "Dist2mtx_{region:s}_{varname:s}_Y{year_beg:04d}-{year_end:04d}_P{pentad_beg:02d}-{pentad_end:02d}.nc".format(
        region = "DEFAULT" if args.mask_region == "" else args.mask_region ,
        varname = args.varname,
        year_beg = args.year_rng[0],
        year_end = args.year_rng[1],
        pentad_beg = args.pentad_rng[0],
        pentad_end = args.pentad_rng[1],
    )
)

   
if not args.overwrite and os.path.exists(output_filename):
    print("File %s already exists. Skip this one." % (output_filename,))

else:
    print("Doing output file: ", output_filename)    
    work(
        output_filename = output_filename,
        datasets = args.datasets,
        label = args.label,
        varname = args.varname,
        year_rng = args.year_rng,
        pentad_rng = args.pentad_rng,
        mask_file = args.mask_file, 
        mask_region = args.mask_region, 
    )








