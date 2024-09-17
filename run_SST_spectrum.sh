#!/bin/bash

spectral_dir="lon"
label="NPAC_spec-${spectral_dir}"

for dataset in oisst ostia ; do

    python3 src/SST_spectrum.py \
        --dataset $dataset \
        --label $label \
        --year-rng 2018 2018 \
        --spectral-dir $spectral_dir \
        --lat-rng 42 48  \
        --lon-rng 150 230


done
