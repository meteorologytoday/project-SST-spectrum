#!/bin/bash

spatial_selector="-180,0,180,90"


dataset_details=(
    MUR_JPL        MUR-JPL-L4-GLOB-v4.1
    OSTIA_UKMO     OSTIA-UKMO-L4-GLOB-v2.0
#    GPBN_OSPO      Geo_Polar_Blended_Night-OSPO-L4-GLOB-v1.0
#    K10SST_NAVO    K10_SST-NAVO-L4-GLOB-v01
#    GAMSSA_ABOM    GAMSSA_28km-ABOM-L4-GLOB-v01
#    DMIOI_DMI      DMI_OI-DMI-L4-GLOB-v1.0

)


nparams=2
N=$(( ${#dataset_details[@]} / $nparams ))
echo "We have $N entries..."
for i in $( seq 1 $N ) ; do

    dataset="${dataset_details[$(( (i-1) * $nparams + 0 ))]}"
    dataset_label="${dataset_details[$(( (i-1) * $nparams + 1 ))]}"

    echo "Downloading dataset: $dataset => $dataset_label"

    output_dir=../../data/physical/sst_raw/$dataset

    for year1 in $( seq 2018 2022 ) ; do

        year2=$(( $year1 + 1  ))

        podaac-data-downloader \
            -c $dataset_label \
            -d $output_dir \
            --start-date ${year1}-12-20T00:00:00Z \
            --end-date ${year2}-01-01T00:00:00Z \
            -b="$spatial_selector"

    done

done
