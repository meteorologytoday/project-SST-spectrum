#!/bin/bash


source 98_trapkill.sh

nproc=5

res_deg=0.1
label="NPAC_${res_deg}"

#for dataset in MUR oisst ostia ; do

nproc_cnt=0
for y in $( seq 2012 2022 ) ; do
for dataset in oisst ostia MUR ; do
    
    
    python3 src/crop_SST.py \
        --dataset $dataset \
        --label $label \
        --timepentad-rng ${y}P00 ${y}P06 \
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
