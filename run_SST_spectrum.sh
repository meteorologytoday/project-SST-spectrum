#!/bin/bash

spectral_dir="lon"
label="NPAC_spec-${spectral_dir}"

python3 src/SST_spectrum.py \
    --dataset oisst \
    --label $label \
    --year-rng 1982 1982 \
    --spectral-dir $spectral_dir \
    --lat-rng 30 35  \
    --lon-rng 150 230
