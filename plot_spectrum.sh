#!/bin/bash

spectral_dir="lon"
label="NPAC_spec-${spectral_dir}"
dataset=oisst

for dataset in oisst ostia ; do
for varname in sst ; do
    python3 src/plot_spectrum_snapshot.py \
        --dataset $dataset      \
        --output-dir figures/spectrum_snapshot \
        --varname $varname        \
        --label $label       \
        --timepentad-rng 2018P0 2018P5 \
        --pentads-interval 1 \
        --drop-wvn 3

done
done
