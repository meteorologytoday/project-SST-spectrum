#!/bin/bash

source 98_trapkill.sh
nproc=5

res_deg=0.1
label="NPAC_${res_deg}"

input_params=(
    "NPAC_SOUTH" "gendata/EOFs/NPAC_0.1/EOFs_oisst_refMUR_NPAC_SOUTH_sst_Y2012-2021_P00-05.nc"    
    "NPAC_NORTH" "gendata/EOFs/NPAC_0.1/EOFs_oisst_refMUR_NPAC_NORTH_sst_Y2012-2021_P00-05.nc"
    "NPAC" "gendata/EOFs/NPAC_0.1/EOFs_oisst_refMUR_NPAC_sst_Y2012-2021_P00-05.nc"
)



nparams=2
N=$(( ${#input_params[@]} / $nparams ))

echo "We have $N file(s) to run..."
for i in $( seq 1 $(( ${#input_params[@]} / $nparams )) ) ; do

    {    
        label="${input_params[$(( (i-1) * $nparams + 0 ))]}"
        input="${input_params[$(( (i-1) * $nparams + 1 ))]}"

        output_EOF=figures/EOF/${label}_EOF.png
        output_timeseries=figures/EOF/${label}_timeseries.png

        python3 src/plot_EOFs.py \
            --input $input \
            --output-timeseries $output_timeseries  \
            --output-EOF $output_EOF \
            --title $label \
            --nEOF 2 \
            --no-display
    } &
        
    nproc_cnt=$(( $nproc_cnt + 1 ))
    if (( $nproc_cnt >= $nproc )) ; then
        echo "Max batch_cnt reached: $nproc"
        wait
        nproc_cnt=0
    fi


done

wait

echo "DONE!"
