#!/bin/bash

x_dir="lon"
label="NPAC30_${x_dir}"
datasets=( MUR oisst ostia )
for varname in sst ; do
    python3 src/plot_spectrum_snapshot_diff.py \
        --datasets "${datasets[@]}"      \
        --output-dir figures/diff_spectrum_snapshot \
        --varname $varname        \
        --label $label       \
        --timepentad-rng 2018P00 2018P00 \
        --pentads-interval 1 \
        --drop-wvn 3

done
