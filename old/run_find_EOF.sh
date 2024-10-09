#!/bin/bash
source 98_trapkill.sh

nproc=5


res_deg=0.1
label="NPAC_${res_deg}"

dataset_ref=MUR
dataset_compare=( 
    oisst
    ostia 
)



for dataset_compare in "${dataset_compare[@]}" ; do
for varname in sst ; do
for mask_region in NPAC_NORTH NPAC_SOUTH NPAC ; do

    mask_file=gendata/mask/mask_${label}.nc


    python3 src/find_EOF.py \
        --dataset-compare $dataset_compare \
        --dataset-ref $dataset_ref \
        --label $label \
        --output-dir gendata/EOFs \
        --varname $varname        \
        --year-rng 2012 2021 \
        --modes 20 \
        --pentad-rng 0 5 \
        --mask-file $mask_file \
        --mask-region $mask_region &


    nproc_cnt=$(( $nproc_cnt + 1 ))
    if (( $nproc_cnt >= $nproc )) ; then
        echo "Max batch_cnt reached: $nproc"
        wait
        nproc_cnt=0
    fi

done
done
done
