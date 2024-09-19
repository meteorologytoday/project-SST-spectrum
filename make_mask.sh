#!/bin/bash

label=NPAC_0.1
python3 src/gen_mask.py \
    --test-dataset MUR \
    --test-timepentad 2018P00 \
    --label $label \
    --output gendata/mask/mask_${label}.nc
