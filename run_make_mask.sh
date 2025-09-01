#!/bin/bash

source 000_setup.sh

label=NPAC_0.1
python3 src/analysis/gen_mask.py \
    --test-dataset oisst \
    --test-timepentad 2023P00 \
    --label $label \
    --output gendata/mask/mask_${label}.nc
