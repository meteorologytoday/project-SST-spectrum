#!/bin/bash

x_dim="lon"
label="NPAC30_${x_dim}"

for dataset in MUR oisst ostia ; do

    python3 src/crop_SST.py \
        --dataset $dataset \
        --label $label \
        --timepentad-rng 2018P00 2018P02 \
        --x-dim $x_dim \
        --lat-rng 32 38  \
        --lon-rng 150 230 \
        --res-deg 0.01


done
