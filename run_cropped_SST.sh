#!/bin/bash


source 98_trapkill.sh

nproc=5

res_deg=0.1
label="NPAC_${res_deg}"

datasets=(
    oisst
    MUR_JPL
    K10SST_NAVO
    OSTIA_UKMO
    DMIOI_DMI
    GAMSSA_ABOM
    GPBN_OSPO
)


#for dataset in MUR oisst ostia ; do

nproc_cnt=0
for y in $( seq 2022 2023 ) ; do
for dataset in "${datasets[@]}"; do
    
    
    python3 src/crop_SST.py \
        --dataset $dataset \
        --label $label \
        --timepentad-rng ${y}P00 ${y}P72 \
        --lat-rng 0 65    \
        --lon-rng 120 250 \
        --res-deg $res_deg &

    nproc_cnt=$(( $nproc_cnt + 1 ))
    if (( $nproc_cnt >= $nproc )) ; then
        echo "Max batch_cnt reached: $nproc"
        wait
        nproc_cnt=0
    fi

done
done

wait
