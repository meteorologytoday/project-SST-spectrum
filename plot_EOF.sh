#!/bin/bash

source 98_trapkill.sh
nproc=2

res_deg=0.1
label="NPAC_${res_deg}"


EOF_dir=gendata/EOF_multiple_datasets/NPAC_0.1
datasets="GHRSST,MUR_JPL,OSTIA_UKMO,DMIOI_DMI,GAMSSA_ABOM,K10SST_NAVO,GPBN_OSPO"

input_params=(
    "NPAC_ALL_2023" "$EOF_dir/EOFs_${datasets}_decentralize-T_NPAC_ALL_sst_Y2023-2023_P-6-11.nc"
    "NPAC_EAST_2023" "$EOF_dir/EOFs_${datasets}_decentralize-T_NPAC_EAST_sst_Y2023-2023_P-6-11.nc"
    "NPAC_WEST_2023" "$EOF_dir/EOFs_${datasets}_decentralize-T_NPAC_WEST_sst_Y2023-2023_P-6-11.nc"
    "NPAC_SOUTH_2023" "$EOF_dir/EOFs_${datasets}_decentralize-T_NPAC_SOUTH_sst_Y2023-2023_P-6-11.nc"
    "NPAC_NORTH_2023" "$EOF_dir/EOFs_${datasets}_decentralize-T_NPAC_NORTH_sst_Y2023-2023_P-6-11.nc"
)

input_params=(
    "NPAC_ALL"  "$EOF_dir/EOFs_${datasets}_decentralize-F_NPAC_ALL_sst_Y2020-2023_P-6-11.nc"
    "NPAC_EAST" "$EOF_dir/EOFs_${datasets}_decentralize-F_NPAC_EAST_sst_Y2020-2023_P-6-11.nc"
    "WWRF_2020-2023"      "$EOF_dir/EOFs_${datasets}_decentralize-F_WWRF_sst_Y2020-2023_P-6-11.nc"
    "WWRF_2020"      "$EOF_dir/EOFs_${datasets}_decentralize-F_WWRF_sst_Y2020-2020_P-6-11.nc"
    "WWRF_2021"      "$EOF_dir/EOFs_${datasets}_decentralize-F_WWRF_sst_Y2021-2021_P-6-11.nc"
    "WWRF_2022"      "$EOF_dir/EOFs_${datasets}_decentralize-F_WWRF_sst_Y2022-2022_P-6-11.nc"
    "WWRF_2023"      "$EOF_dir/EOFs_${datasets}_decentralize-F_WWRF_sst_Y2023-2023_P-6-11.nc"
)


plot_every_N_pts=10


nparams=2
N=$(( ${#input_params[@]} / $nparams ))

echo "We have $N file(s) to run..."
for i in $( seq 1 $(( ${#input_params[@]} / $nparams )) ) ; do

    {    
        label="${input_params[$(( (i-1) * $nparams + 0 ))]}"
        input="${input_params[$(( (i-1) * $nparams + 1 ))]}"

        output_EOF=figures/EOF/${label}_EOF.png
        output_timeseries=figures/EOF/${label}_timeseries.png

        time python3 src/plot_EOFs.py \
            --input $input \
            --output-timeseries $output_timeseries  \
            --output-EOF $output_EOF \
            --plot-every-N-pts $plot_every_N_pts \
            --title $label \
            --nEOF 4 \
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
