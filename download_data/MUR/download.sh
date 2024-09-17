#!/bin/bash

output_dir=/data/SO2/t2hsu/project-SST-spectrum/data/sst_raw/MUR

podaac-data-downloader -c MUR-JPL-L4-GLOB-v4.1 -d $output_dir --start-date 2018-01-01T00:00:00Z --end-date 2018-01-10T00:00:00Z -b="-180,-90,180,90"
