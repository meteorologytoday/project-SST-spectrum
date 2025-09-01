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

def genGaussianKernel(half_Nx, half_Ny, dx, dy, sig_x, sig_y):

    Nx = 2 * half_Nx + 1
    Ny = 2 * half_Ny + 1
    
    x = np.arange(Nx) * dx
    y = np.arange(Nx) * dy

    x -= x[half_Nx]
    y -= y[half_Ny]
    
    yy, xx = np.meshgrid(y, x, indexing='ij')
    
    w = np.exp( - ( ( xx / sig_x )**2 + ( yy / sig_y )**2 / 2 ) )

    w /= np.sum(w)
    
    return w

def genBoxKernel(half_Nx, half_Ny, dx=1.0, dy=1.0):

    Nx = 2 * half_Nx + 1
    Ny = 2 * half_Ny + 1
    
    x = np.arange(Nx) * dx
    y = np.arange(Nx) * dy

    x -= x[half_Nx]
    y -= y[half_Ny]
    
    yy, xx = np.meshgrid(y, x, indexing='ij')
    
    w = xx * 0 + 1

    w /= np.sum(w)
    
    return w


def detectBoundaryForImageAndKernel(n, kn, i):
    
    half_n = n // 2
    half_kn = kn // 2
    
    if i < half_kn:
        img_rng_beg = 0
        k_rng_beg = half_kn - i
    else:
        img_rng_beg = i - half_kn
        k_rng_beg = 0


    if i > n - half_kn - 1:
        img_rng_end = n
    else:
        img_rng_end = i + half_kn + 1

    
    img_rng = slice(img_rng_beg, img_rng_end)
    k_rng = slice(k_rng_beg, k_rng_beg + (img_rng_end - img_rng_beg))

    return img_rng, k_rng
    
    

def convolve2d(image, kernel):
   
    ny, nx = image.shape
    kny, knx = kernel.shape

    half_kny = kny // 2
    half_knx = knx // 2
    
    new_image = np.zeros_like(image)
    for j in range(ny):

        y_rng, ky_rng = detectBoundaryForImageAndKernel(ny, kny, j)
        
        for i in range(nx):
            
            x_rng, kx_rng = detectBoundaryForImageAndKernel(nx, knx, i)

            slice_image = image[y_rng, x_rng]
            slice_kernel = kernel[ky_rng, kx_rng]

            valid_idx = np.isfinite(slice_image)
            
            if np.any(valid_idx):
                new_image[j, i] = sum( slice_image[valid_idx] * slice_kernel[valid_idx] ) / sum(slice_kernel[valid_idx])
            else:
                new_image[j, i] = np.nan
            

    return new_image


def doGaussianFilter(image, half_Nx, half_Ny, dx, dy, sig_x, sig_y):
    kernel = genGaussianKernel(half_Nx, half_Ny, dx, dy, sig_x, sig_y)
    return signal.convolve2d(image, kernel, mode="full", fillvalue=0)

def doBoxFilter(image, half_Nx, half_Ny):
    kernel = genBoxKernel(half_Nx, half_Ny)
    return convolve2d(image, kernel)



parser = argparse.ArgumentParser(description='Process some integers.')
parser.add_argument('--datasets', type=str, nargs="+", help='Dataset.', required=True)
parser.add_argument('--output-dir', type=str, help='Output directory.', required=True)
parser.add_argument('--varname', type=str, required=True)
parser.add_argument('--label', type=str, required=True)
parser.add_argument('--pentad-rng', type=int, nargs=2, help="Petand range of the year.", required=True)
parser.add_argument('--year-rng', type=int, nargs=2, help="Year range.", required=True)
parser.add_argument('--mask-file', type=str, help="Mask file. If not supplied, take the whole domain.", default="")
parser.add_argument('--mask-region', type=str, help="Select the region in the mask file.", default="")
parser.add_argument('--modes', type=int, help="Mask file. If not supplied, take the whole domain.", required=True)
parser.add_argument('--decentralize', action="store_true", help="If activated then will perform all possible comparison. ")
parser.add_argument('--mavg-half-window-size', type=int, help="The half size of smoothing window in x and y.", required=True)

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
    decentralize,
    datasets,
    label,
    varname,
    year_rng,
    pentad_rng,
    mavg_half_window_size,
    mask_file = "",
    mask_region = "",
):
    N_datasets = len(datasets)

    comparison_pairs = []
    
    if decentralize:
        N_diffs = int(N_datasets * (N_datasets-1) / 2)
        print("WARNING: `--decentralize` is activated. There will be %d comparison. " % ( N_diffs, ) )

        cnt = 0
        for i in range(N_datasets):
            for j in range(i+1, N_datasets):
                cnt += 1
                comparison_pairs.append((i, j))

        if cnt != N_diffs:
            raise Exception("ERROR: I am not constructing pairs correctly.")

    else:
        N_diffs = N_datasets - 1
        print("The `--decentralize` is not activated. There will be %d comparison. " % ( N_diffs, ) )
        for i in range(1, N_datasets):
            comparison_pairs.append((0, i))

    print("Comparison pairs: ", comparison_pairs)

    data = []
    da_mask = None

    if mask_file != "":    
        print("Loading mask file: ", mask_file)
        da_mask = xr.open_dataset(mask_file)["mask"].sel(region=mask_region)
        

    for dataset in datasets:
        print("Loading dataset:", dataset)
        data.append(
            loadData(dataset, label, varname, year_rng, pentad_rng)
        )

    ds_ref = data[0]
    Nt = len(ds_ref.coords["pentadstamp"])
    Nlat = len(ds_ref.coords["lat"])
    Nlon = len(ds_ref.coords["lon"])
    
    Ns = N_diffs * Nt
    fulldata = np.zeros((Ns, Nlat, Nlon))

    for cnt, (i, j) in enumerate(comparison_pairs):
        diff = data[j] - data[i]
        da_diff = diff[varname].transpose("pentadstamp", "lat", "lon")

        # Smooth data
        for p, pentadstamp in enumerate(da_diff.coords["pentadstamp"]):
            print("Doing pentadstamp: ", pentadstamp)
            anom = da_diff.isel(pentadstamp=p).to_numpy()
            filtered_anom = doBoxFilter(anom, mavg_half_window_size, mavg_half_window_size)
            
            fulldata[cnt*Nt+p, :, :] = filtered_anom
            

        #fulldata[cnt*Nt:(cnt+1)*Nt, :, :] = filtered_anom

    print("Datasets opened.")
   
    fulldata_mean = fulldata.mean(axis=0, keepdims=True)
    fulldata_std  = fulldata.std(axis=0)
    fulldata_anom = fulldata - fulldata_mean
    
    mask = np.isfinite(fulldata_mean[0, :, :]).astype(int)
    if da_mask is not None:
        print("mask: ", mask.shape)
        print("da_mask: ", da_mask.shape)
        mask *= da_mask.to_numpy()

    missing_data_idx = mask == 0
    data_reduction = len(mask) != np.sum(mask)
    d_full = fulldata_anom.reshape((Ns, -1))
    
   
    if data_reduction:
        print("Data contains NaN. Need to do reduction.")    
    
    M = matrix_helper.constructSubspaceWith(mask.flatten())
    d_reduced = np.zeros((Ns, np.sum(mask)))
 
    #print("Nt = ", Nt)
    #print("N_datasets = ", N_datasets)
    #print("Ns = ", Ns)
    #print("shape of d_full = ", d_full.shape)
    #print("shape of mask = ", mask.shape)    
    #print("shape of fulldata_mean = ", fulldata_mean.shape)
    #print("dim of M = ", M.shape)    
   
    print("Reducing the matrix") 
    for s in range(Ns):
        d_reduced[s, :] = M @ d_full[s, :]
    
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
            projected_idx = ( ["mode", "sample", ], projected_idx),
            variance = ( ["mode", ], pca.explained_variance_),
            mean = ( ["lat", "lon"], fulldata_mean[0, :, :] ), # We kept the time dimension. Now need to drop it
            std = ( ["lat", "lon"], fulldata_std ),
        ),
        coords = dict(
            lat = ds_ref.coords["lat"],
            lon = ds_ref.coords["lon"],
            sample = np.arange(Ns),
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


print("Doing EOF of datasets: ", args.datasets)

output_filename = os.path.join(
    args.output_dir,
    args.label,
    "EOFs_{datasets:s}_decentralize-{decentralize:s}_halfsize-{half_size:d}_{region:s}_{varname:s}_Y{year_beg:04d}-{year_end:04d}_P{pentad_beg:02d}-{pentad_end:02d}.nc".format(
        datasets = ",".join(args.datasets),
        decentralize = "T" if args.decentralize else "F",
        half_size=args.mavg_half_window_size,
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
        decentralize = args.decentralize,
        datasets = args.datasets,
        label = args.label,
        varname = args.varname,
        year_rng = args.year_rng,
        pentad_rng = args.pentad_rng,
        mavg_half_window_size = args.mavg_half_window_size,
        mask_file = args.mask_file, 
        mask_region = args.mask_region, 
    )








