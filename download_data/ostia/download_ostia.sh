#!/bin/bash

output_dir=/data/SO2/t2hsu/project-SST-spectrum/data/sst_raw/ostia
time_str=$(date +%Y-%m-%d)

#wget -O ${output_dir}/OSTIA-UKMO-L4-GLOB-REP-v2.0.nc https://podaac.jpl.nasa.gov/dataset/OSTIA-UKMO-L4-GLOB-REP-v2.0

podaac-data-downloader -c OSTIA-UKMO-L4-GLOB-REP-v2.0 -d $output_dir --start-date 1982-01-01T00:00:00Z --end-date 1983-01-01T00:00:00Z -e ""

