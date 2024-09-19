#!/bin/bash

output_dir=../../data/physical/sst_raw/MUR


for year in $( seq 2012 2024 ) ; do
for month in 1 ; do

    m2=$(( $month + 1 ))
    m1=$( printf "%02d" $month )
    m2=$( printf "%02d" $m2 )

    podaac-data-downloader -c MUR-JPL-L4-GLOB-v4.1 -d $output_dir --start-date ${year}-${m1}-01T00:00:00Z --end-date ${year}-${m2}-01T00:00:00Z -b="-180,0,180,90"

done
done
