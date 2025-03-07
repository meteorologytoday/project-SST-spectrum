#!/bin/bash


output_dir=$1

if [ "$output_dir" = "" ]; then
    echo "Error: output_dir must be provided as the first argument."
fi

echo "output_dir: $output_dir"

beg_year=2005
end_year=2024


echo "##### Download OISST data year $beg_year ~ $end_year #####"
#mkdir -p $output_dir
#for datatype in anom mean ; do

for datatype in mean ; do
for y in $( seq 2005 2024 ) ; do

    year_str=$( printf "%04d" $y )
    filename=sst.day.${datatype}.${year_str}.nc
    full_filename=$output_dir/$filename
    file_url=https://downloads.psl.noaa.gov/Datasets/noaa.oisst.v2.highres/${filename}

    if [ -f "$full_filename" ] ; then
        echo "File $full_filename already exists. Skip."
    else
        echo "File $full_filename does not exist. Download."
        echo "Download SST of year $year_str"
        wget -O $full_filename $file_url
    fi
    
done
done
