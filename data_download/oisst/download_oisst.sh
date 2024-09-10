#!/bin/bash

output_dir=/data/SO2/t2hsu/project-SST-spectrum/data/sst_raw/oisst

for y in $( seq 1981 2024 ) ; do

    year_str=$( printf "%04d" $y )
    filename=sst.day.mean.${year_str}.nc
    full_filename=$output_dir/$filename
    file_url=https://downloads.psl.noaa.gov//Datasets/noaa.oisst.v2.highres/${filename}




    if [ -f "$full_filename" ] ; then
        echo "File $full_filename already exists. Skip."
    else
        echo "File $full_filename does not exist. Download."
        echo "Download SST of year $year_str"
        wget -O $full_filename $file_url
    fi
    

done
