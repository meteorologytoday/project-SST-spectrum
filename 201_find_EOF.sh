#!/bin/bash
source 000_setup.sh
source 98_trapkill.sh

nproc=2


res_deg=0.1
label="NPAC_${res_deg}"

datasets=(
    GHRSST-Mean 
    oisst
)

for half_window_size in 0 10 ; do
for varname in sst ; do
for mask_region in WWRF ; do

    mask_file=gendata/mask/mask_${label}.nc

    python3 src/analysis/find_EOF_multiple.py \
        --datasets ${datasets[@]} \
        --label $label \
        --output-dir gendata/EOF_multiple_datasets \
        --varname $varname        \
        --year-rng 2023 2023 \
        --modes 5 \
        --pentad-rng -6 11 \
        --mask-file $mask_file \
        --mask-region $mask_region \
        --mavg-half-window-size $half_window_size &



    nproc_cnt=$(( $nproc_cnt + 1 ))
    if (( $nproc_cnt >= $nproc )) ; then
        echo "Max batch_cnt reached: $nproc"
        wait
        nproc_cnt=0
    fi

done
done
done

wait

echo "Done."
