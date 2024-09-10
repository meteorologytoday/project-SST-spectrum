#!/bin/bash



dates=(
    2017-02-01 2017-02-25
)

hycom_data_dir="hycom_data"
mitgcm_data_dir="mitgcm_data"
mitgcm_grid_dir="./set-mask/run"

params=2
N=$(( ${#dates[@]} / $params ))

set -x
for (( i=0 ; i < N ; i++ )); do

    beg_date=${dates[$(( $i * $params + 0 ))]}
    end_date=${dates[$(( $i * $params + 1 ))]}

    python3 mitgcm-preprocess_py/02_postprocess/cmd_batch_convert_hycom.py \
        --beg-date $beg_date \
        --end-date $end_date \
        --input-dir $hycom_data_dir \
        --output-dir $mitgcm_data_dir \
        --grid-dir $mitgcm_grid_dir \
        --varnames water_temp salinity water_u water_v \
        --nproc 24 \
        --iter-max 10 \
        --extend-downward


done
