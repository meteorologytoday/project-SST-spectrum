import xarray as xr
import pandas as pd
import os
import TimePentad as tp

data_archive = "data"


def getFilename(dataset, datatype, tp: TimePentad):
    
    if datatype not in ["physical", "spectral"]:
        raise Exception("Unknown datatype: %s" % (datatype,))

    full_filename = os.path.join(
        data_archive,
        datatype,
        "{dataset:s}_{year:04d}-{year:02d}.nc".format(
            year = tp.year,
            pentad = tp.pentad,
        ),
    )

    return full_filename 
 
    
def load_dataset(dataset, dt_beg, dt_end):

    if dataset in ["ERA5", "oisst", ]:
        
        data_interval = pd.Timedelta(days=1)

    else:

        raise Exception("Unknown dataset: %s" % (dataset,))
        
    

     
    if dt_end is None:
        
        

    

    return ds
    
    








