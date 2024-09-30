#!/bin/bash


for mask_region in NPAC_SOUTH NPAC_NORTH NPAC_ALL ; do

    python3 src/dist2_stat.py \
        --input gendata/dist2_mtx/NPAC_0.1/Dist2mtx_${mask_region}_sst_Y2023-2023_P-6-11.nc \
        --output figures/dist2_mtx/dist-${mask_region}.svg


done
