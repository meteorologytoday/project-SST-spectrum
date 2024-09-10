import xarray as xr
import pandas as pd

def loadraw(dataset, dt_beg, dt_end):

    if dataset in ["ERA5", "oisst", ]:
        
        data_interval = pd.Timedelta(days=1)

    else:

        raise Exception("Unknown dataset: %s" % (dataset,))
        
    

     
    if dt_end is None:
        
        

    

    return ds
    
    








