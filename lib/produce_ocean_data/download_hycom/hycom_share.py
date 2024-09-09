import pandas as pd
from datetime import datetime
import numpy as np

incomplete_OpenDAP_URL = 'http://tds.hycom.org/thredds/dodsC'
 #GLBv0.08/expt_93.0';


hycom_beg_dt = pd.Timestamp(datetime.strptime('2000-01-01', "%Y-%m-%d"))

def hycomTime2Datetime(hycom_time: int):
    return hycom_beg_dt + pd.Timedelta(hycom_time, unit='h')
    
def datetime2hycomTime(dt):
    return int( (dt - hycom_beg_dt) / pd.Timedelta(1, unit='h') )
    
def findfirst(a):
    return np.argmax(a)

def findlast(a):
    return (len(a) - 1) - np.argmax(a[::-1])


def findArgRange(arr, lb, ub):
    if lb > ub:
        raise Exception("Lower bound should be no larger than upper bound")

    if np.any( (arr[1:] - arr[:-1]) <= 0 ):
        raise Exception("input array should be monotonically increasing")

    idx = np.logical_and((lb <= arr),  (arr <= ub))
    
    idx_low = findfirst(idx)
    idx_max = findlast(idx)

    return idx_low, idx_max



def findRegion_latlon(lat_arr, lat_rng, lon_arr, lon_rng):

    lat_beg, lat_end = findArgRange(lat_arr, lat_rng[0], lat_rng[1])
    lon_beg, lon_end = findArgRange(lon_arr, lon_rng[0], lon_rng[1])

    return (lon_beg, lon_end, lat_beg, lat_end)

