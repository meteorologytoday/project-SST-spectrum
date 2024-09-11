#!/bin/bash

spectral_dir="lon"
label="NPAC_spec-${spectral_dir}"
dataset=oisst

for varname in sst ssta ; do
    python3 src/plot_spectrum_snapshot.py \
        --dataset oisst      \
        --output-dir figures/spectrum_snapshot \
        --varname $varname        \
        --label $label       \
        --timepentad-rng 1982P0 1983P0 \
        --pentads-interval 1 \
        --drop-wvn 5

done
