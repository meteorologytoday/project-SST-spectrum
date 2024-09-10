from multiprocessing import Pool
import multiprocessing
import datetime
from pathlib import Path
import os.path
import os
import netCDF4

def pleaseRun(cmd):
    print(">> %s" % cmd)
    os.system(cmd)


def ifSkip(dt):

    skip = False

    #if dt.month in [5,6,7,8]:
    #    skip = True

    #if dt.month == 4 and dt.day > 15:
    #    skip = True

    #if dt.month == 9 and dt.day < 15:
    #    skip = True

    return skip

# This is for AR
beg_time = datetime.datetime(2018,    1, 1)
end_time = datetime.datetime(2019,    1, 1)

# This is for ECCC s2s project
#beg_time = datetime.datetime(1997,    1,  1)
#end_time = datetime.datetime(2018,    2, 1)


archive_root = "/data/SO2/t2hsu/project-SST-spectrum/data/sst/ERA5"


g0 = 9.81
