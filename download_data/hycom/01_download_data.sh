#!/bin/bash

input_params=(
    NPAC 0 65 120 245 2018-01-01 2018-02-01
)

params=7
N=$(( ${#input_params[@]} / $params ))

set -x
for (( i=0 ; i < N ; i++ )); do

    label=${input_params[$(( $i * $params + 0 ))]}
    beg_lat=${input_params[$(( $i * $params + 1 ))]}
    end_lat=${input_params[$(( $i * $params + 2 ))]}
    beg_lon=${input_params[$(( $i * $params + 3 ))]}
    end_lon=${input_params[$(( $i * $params + 4 ))]}
    beg_date=${input_params[$(( $i * $params + 5 ))]}
    end_date=${input_params[$(( $i * $params + 6 ))]}

    python3 download_hycom/getHycomData.py \
        --dataset-info hycom_info.pickle \
        --dataset-name GLBv0.08 \
        --beg-date $beg_date \
        --end-date $end_date \
        --lat-rng $beg_lat $end_lat \
        --lon-rng $beg_lon $end_lon \
        --nproc 2 \
        --varnames sst \
        --output-dir downloaded_data/$label \
        --output-formats netcdf   &


done
    

wait
