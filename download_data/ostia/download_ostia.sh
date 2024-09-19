#!/bin/bash

output_dir=../../data/physical/sst_raw/ostia
time_str=$(date +%Y-%m-%d)

#wget -O ${output_dir}/OSTIA-UKMO-L4-GLOB-REP-v2.0.nc https://podaac.jpl.nasa.gov/dataset/OSTIA-UKMO-L4-GLOB-REP-v2.0


for year in $( seq 2012 2024 ) ; do
for month in 1 ; do

    m2=$(( $month + 1 ))
    m1=$( printf "%02d" $month )
    m2=$( printf "%02d" $m2 )


    podaac-data-downloader -c OSTIA-UKMO-L4-GLOB-REP-v2.0 -d $output_dir --start-date ${year}-${m1}-01T00:00:00Z --end-date ${year}-${m2}-01T00:00:00Z -e ""
done
done

