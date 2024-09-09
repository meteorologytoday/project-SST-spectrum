import numpy as np
import scipy.interpolate
from scipy.interpolate import RegularGridInterpolator
import functools
import MITgcmutils

def _filterValid(x, label):

    result = np.copy(x)
    result[label != 1] = 0
    
    return result

def _getNeighbors(data):

    data_t = np.roll(data, -1, axis=0) 
    data_b = np.roll(data,  1, axis=0) 
    data_l = np.roll(data,  1, axis=1) 
    data_r = np.roll(data, -1, axis=1) 

    return data_t, data_b, data_l, data_r


def extendData(data, axis):

    dims = len(data.shape)
    axis_N = data.shape[axis]
    swapped_data = np.swapaxes(data, axis, dims-1)
    swapped_shape = np.array(swapped_data.shape)
    reordered_data = np.reshape(swapped_data, (-1, axis_N) )

    for i in range(reordered_data.shape[0]):
        if np.isnan(reordered_data[i, 0]):
            continue

        for k in range(1, axis_N):
        
            # If find the bottom then extend it    
            if np.isnan(reordered_data[i, k]):
                reordered_data[i, k:axis_N] = reordered_data[i, k-1]
                break

     
    final_data = np.swapaxes( np.reshape(reordered_data, swapped_shape), axis, dims-1)

    return final_data




 
def horizontallyExpand(data, mask, iter_max=50):

    if len(data.shape) != 2:
        
        raise Exception("Shape of input data should be 2 dimensional. Now I have %d dimensional input." % (len(data.shape),) )


    Ny, Nx = data.shape
    data_output = np.copy(data)
        
    labels = np.zeros_like(data_output)

    ocn_idx = mask == 1
    lnd_idx = np.logical_not(ocn_idx)
    
    for k in range(iter_max+1):
   
        missing_idx = np.isnan(data_output) & ocn_idx
       
        if np.sum(missing_idx) == 0:
            break


        if k == iter_max:
            #print("Iteration maximum reached before the data is filled.")
            break


        labels[:]           =   1 # valid
        labels[missing_idx] =   0 # missing
        labels[lnd_idx]     =  -1 # land

        label_neighbors = _getNeighbors(labels)
        data_neighbors  = _getNeighbors(data_output)

        valid_label_neighbors = [ (label_neighbor == 1).astype(int) for label_neighbor in label_neighbors  ]

        valid_cnt = functools.reduce(
            ( lambda a, b : a + b ),
            valid_label_neighbors,
        )


        valid_data_neighbors = [ _filterValid(data_neighbors[i], label_neighbors[i]) for i in range(len(label_neighbors)) ]
        valid_sum = functools.reduce(
            ( lambda a, b : a + b ),
            valid_data_neighbors,
        )

        with np.errstate(divide='ignore', invalid='ignore'):
            valid_avg = valid_sum / valid_cnt
        
        filled_idx = missing_idx & ( valid_cnt > 0 )
        data_output[filled_idx] = valid_avg[filled_idx]
    
    
    return data_output, k



def convertGrid(data, grid_type, XC1, YC1, ZC1, grid2_dir=".", fill_value=0.0, iter_max=50, check_rng=[-np.inf, np.inf], extend_downward=False):
    
    if data.shape != (len(ZC1), len(YC1), len(XC1)):
        raise Exception("Input data shape does not match input XC1 YC1 ZC1.")

    if grid_type == "T":
        grid2_name = 'hFacC'
        X2 = 'XC'
        Y2 = 'YC'
        Z2 = 'RC'

    elif grid_type == "U":
        grid2_name = 'hFacW'
        X2 = 'XG'
        Y2 = 'YC'
        Z2 = 'RC'

    elif grid_type == "V":
        grid2_name = 'hFacS'
        X2 = 'XC'
        Y2 = 'YG'
        Z2 = 'RC'


    
    grid2_lnd = MITgcmutils.rdmds('%s/%s' % (grid2_dir, grid2_name)) == 0
    grid2_ocn = MITgcmutils.rdmds('%s/%s' % (grid2_dir, grid2_name)) != 0

    print("Number of ocn grid: ", np.sum(grid2_ocn))
    print("Number of lnd grid: ", np.sum(grid2_lnd))

    X2 = MITgcmutils.rdmds('%s/%s' % (grid2_dir, X2))[0, :]
    Y2 = MITgcmutils.rdmds('%s/%s' % (grid2_dir, Y2))[:, 0]
    Z2 = MITgcmutils.rdmds('%s/%s' % (grid2_dir, Z2)).flatten()





    # We do not have hycom 3D mask.
    # We only hope to expand as much as possible
    # to project onto mitgcm's grid fully    
    grid1_mask = np.ones(data.shape)
    data_xyfilled = np.zeros_like(data)
    for k in range(len(ZC1)):
        print("Filling out layer %d of %d layers...\r" % (k+1, len(ZC1)), end='')
        _data, iterations = horizontallyExpand(data[k, :, :], grid1_mask[k, :, :], iter_max=iter_max)
        data_xyfilled[k, :, :] = _data

    print()
    print("Filling complete.")

    # Sometimes the hycom data is not deep enough so
    # the bottom grid will get undesired interpolated
    # values.
    if extend_downward:
        print("Option `extend_downward` is True.")
        data_xyfilled = extendData(data_xyfilled, axis=0) 


    # Now interpolate
    data2 = np.zeros((len(Z2), len(YC1), len(XC1)))
    

    print("Vertical interpolation")
    for j in range(len(YC1)):
        for i in range(len(XC1)):
            f = scipy.interpolate.interp1d(ZC1, data_xyfilled[:, j, i])
            data2[:, j, i] = f(Z2)

    data2[np.isnan(data2)] = -9999
    
    print("Horizontal interpolation")
    data3 = np.zeros((len(Z2), len(Y2), len(X2)))
    for k in range(len(Z2)):
        interpolator = scipy.interpolate.RectBivariateSpline(YC1, XC1, data2[k, :, :], kx=1, ky=1)
        data3[k, :, :] = interpolator(Y2, X2)


    data3[grid2_lnd] = np.nan
    
    check_rng_idx = ( (data3 < check_rng[0]) | (data3 > check_rng[1]) ) & np.isfinite(data3) & grid2_ocn
    check_rng_cnt = np.sum(check_rng_idx)

    if check_rng_cnt == 0:
        print("All data with a finite value are within check_rng = [%f, %f]." % (*check_rng,))
    else:
        print("Warning: %d data with a finite value are not within check_rng = [%f, %f]." % (check_rng_cnt, *check_rng,))

 

    missing_idx = np.isnan(data3) & grid2_ocn
    missing_cnt = np.sum(missing_idx)
   
    if missing_cnt == 0:
        print("Data is successfully interpolated.")
    else:
        print("Still missing %d pts." % (missing_cnt,))    
        print("Going to replace missing pts by `fill_value` = %f." % (fill_value,))

        data3[missing_idx] = fill_value

    return data3, dict(Z=Z2, Y=Y2, X=X2)

if __name__ == "__main__":

    print("First test: ")

    Ny, Nx = (10, 5)

    lnd_value = -999
    mask = np.zeros((Ny, Nx))
    mask[1:-1, 1:-1] = 1

    x = np.floor(np.random.rand(Ny, Nx) * 100)
    x[x < 55] = np.nan
    x[mask == 0] = lnd_value

    print("x is : ")
    print(x)

    for i in range(5):
        print("Iteration %d" % (i+1,))
        x, iterations = horizontallyExpand(x, mask, iter_max=1)
        if iterations > 0:
            print(x)
        else:
            break
        


    #######################################

    print("Second test")

    Ny, Nx = (400, 800)

    lnd_value = -999
    mask = np.zeros((Ny, Nx))
    mask[1:-1, 1:-1] = 1

    x = np.floor(np.random.rand(Ny, Nx) * 100)
    x[x < 55] = np.nan
    x[mask == 0] = lnd_value

    print("x is : ")
    print(x)

    for i in range(5):
        print("Iteration %d" % (i+1,))
        x, iterations = horizontallyExpand(x, mask, iter_max=1)
        if iterations > 0:
            pass

        else:
            break
        


    #######################################

    
