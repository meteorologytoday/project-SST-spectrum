#!/bin/bash


python3 src/SST_spectrum.py \
    --dataset oisst \
    --date-rng 2018P1 2018P5 \
    --lat-rng 40 45 \
    --lon-rng 150 210
