#!/bin/bash
source 98_trapkill.sh

nproc=2


res_deg=0.1
label="NPAC_${res_deg}"

datasets=(
    GHRSST 
    MUR_JPL
    OSTIA_UKMO
    DMIOI_DMI
    GAMSSA_ABOM
    K10SST_NAVO
    GPBN_OSPO
)




#for year in $( seq 2020 2023 ) ; do
for varname in sst ; do
#for mask_region in NPAC_ALL NPAC_EAST NPAC_WEST NPAC_SOUTH NPAC_NORTH ; do
for mask_region in WWRF ; do

    mask_file=gendata/mask/mask_${label}.nc


    python3 src/find_EOF_multiple.py \
        --datasets ${datasets[@]} \
        --label $label \
        --output-dir gendata/EOF_multiple_datasets \
        --varname $varname        \
        --year-rng 2020 2023 \
        --modes 15 \
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
#done

wait

echo "Done."
