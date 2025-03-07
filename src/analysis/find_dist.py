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
parser.add_argument('--dataset-compare', type=str, help='Dataset.', required=True)
parser.add_argument('--dataset-ref', type=str, help='Dataset.', required=True)
parser.add_argument('--output-dir', type=str, help='Output directory.', required=True)
parser.add_argument('--varname', type=str, required=True)
parser.add_argument('--label', type=str, required=True)
parser.add_argument('--pentad-rng', type=int, nargs=2, help="Petand range of the year.", required=True)
parser.add_argument('--year-rng', type=int, nargs=2, help="Year range.", required=True)
parser.add_argument('--mask-file', type=str, help="Mask file. If not supplied, take the whole domain.", default="")
parser.add_argument('--mask-region', type=str, help="Select the region in the mask file.", default="")
parser.add_argument('--modes', type=int, help="Mask file. If not supplied, take the whole domain.", required=True)

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
    dataset_compare,
    dataset_ref,
    label,
    varname,
    year_rng,
    pentad_rng,
    mask_file = "",
    mask_region = "",
):

    data = []
    data_diff = []
    data_dft = []

    print("Open dataset...")
    
    print("Loading dataset_compare:", dataset_compare)
    ds_compare = loadData(dataset_compare, label, varname, year_rng, pentad_rng)
    
    print("Loading dataset_ref: ", dataset_ref)
    ds_ref = loadData(dataset_ref, label, varname, year_rng, pentad_rng)

    da_mask = None
    if mask_file != "":    
        print("Loading mask file: ", mask_file)
        da_mask = xr.open_dataset(mask_file)["mask"].sel(region=mask_region)
        
    print("Datasets opened.")

    diff = ds_compare - ds_ref
    da = diff[varname].transpose(*["pentadstamp", "lat", "lon"])
   
     
    Nt = len(da.coords["pentadstamp"])
    Nlat = len(da.coords["lat"])
    Nlon = len(da.coords["lon"])
     
    da_mean = da.mean(dim="pentadstamp").rename("mean")
    da_std  = da.std(dim="pentadstamp").rename("std")
    da_anom = da - da_mean
    
    mask = np.isfinite(da.isel(pentadstamp=0).to_numpy()).astype(int)
    if da_mask is not None:
        mask *= da_mask.to_numpy()

    missing_data_idx = mask == 0

    data_reduction = len(mask) != np.sum(mask)
    
    d_full = da_anom.to_numpy().reshape((Nt, -1))
    
    if data_reduction:
        print("Data contains NaN. Need to do reduction.")    
    
    M = matrix_helper.constructSubspaceWith(mask.flatten())
    d_reduced = np.zeros((Nt, np.sum(mask)))
    

   
    print("Reducing the matrix") 
    for t in range(Nt):
        d_reduced[t, :] = M @ d_full[t, :]
    
    pca = sklearn.decomposition.PCA(n_components=args.modes)
    pca.fit(d_reduced)


    EOFs_reduced = pca.components_
    N_components = EOFs_reduced.shape[0]
    EOFs_full = np.zeros((N_components, Nlat, Nlon))
     
    for i in range(N_components):
        EOF_tmp = (M.T @ EOFs_reduced[i, :]).reshape((Nlat, Nlon))
        EOF_tmp[missing_data_idx] = np.nan
        EOFs_full[i, :, :] = EOF_tmp
        
    #                (N_com, features)  (features, Nt) => (N_com, Nt)     
    projected_idx = EOFs_reduced @ d_reduced.T 
        
        
    new_ds = xr.Dataset(
        data_vars = dict(
            EOF = ( ["mode", "lat", "lon"], EOFs_full),
            projected_idx = ( ["mode", "pentadstamp", ], projected_idx),
            variance = ( ["mode", ], pca.explained_variance_),
            mean = da_mean,
            std = da_std,
        ),
        coords = dict(
            lat = da.coords["lat"],
            lon = da.coords["lon"],
            pentadstamp = da.coords["pentadstamp"],
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


print("Doing EOF of dataset: %s against %s " % (args.dataset_compare, args.dataset_ref))

output_filename = os.path.join(
    args.output_dir,
    args.label,
    "EOFs_{dataset_compare:s}_ref{dataset_ref:s}_{region:s}_{varname:s}_Y{year_beg:04d}-{year_end:04d}_P{pentad_beg:02d}-{pentad_end:02d}.nc".format(
        dataset_compare = args.dataset_compare,
        dataset_ref = args.dataset_ref,
        varname = args.varname,
        year_beg = args.year_rng[0],
        year_end = args.year_rng[1],
        pentad_beg = args.pentad_rng[0],
        pentad_end = args.pentad_rng[1],
        region = "DEFAULT" if args.mask_region == "" else args.mask_region ,
    )
)

if os.path.exists(output_filename):
    print("File %s already exists. Skip this one." % (output_filename,))

else:
    print("Doing output file: ", output_filename)    
    work(
        output_filename = output_filename,
        dataset_compare = args.dataset_compare,
        dataset_ref = args.dataset_ref,
        label = args.label,
        varname = args.varname,
        year_rng = args.year_rng,
        pentad_rng = args.pentad_rng,
        mask_file = args.mask_file, 
        mask_region = args.mask_region, 
    )








