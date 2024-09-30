#!/bin/bash
source 98_trapkill.sh

nproc=1


res_deg=0.1
label="NPAC_${res_deg}"

datasets=( 
    MUR_JPL
    OSTIA_UKMO
    DMIOI_DMI
    GAMSSA_ABOM
    K10SST_NAVO
    GPBN_OSPO
    oisst
)



for varname in sst ; do
for mask_region in NPAC_SOUTH NPAC_NORTH NPAC_ALL ; do

    mask_file=gendata/mask/mask_${label}.nc


    python3 src/find_dist2.py \
        --datasets "${datasets[@]}" \
        --label $label \
        --output-dir gendata/dist2_mtx \
        --overwrite \
        --varname $varname        \
        --year-rng 2023 2023 \
        --pentad-rng -6 11 \
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
