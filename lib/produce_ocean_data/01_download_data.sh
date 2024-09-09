#!/bin/bash

dates=(
    2017-02-01 2017-02-26
    2015-11-22 2015-12-25
)

params=2
N=$(( ${#dates[@]} / $params ))

set -x
for (( i=0 ; i < N ; i++ )); do

    beg_date=${dates[$(( $i * $params + 0 ))]}
    end_date=${dates[$(( $i * $params + 1 ))]}

    python3 "SKRIPS-case-generation/src/mitgcm-preprocess_py/01_download_hycom/getHycomData.py" \
        --dataset-info hycom_info.pickle \
        --dataset-name GLBv0.08 \
        --beg-date $beg_date \
        --end-date $end_date \
        --lat-rng 18 65 \
        --lon-rng 175 245 \
        --nproc 2 \
        --output-dir hycom_data \
        --output-formats netcdf   &


done
    

wait
