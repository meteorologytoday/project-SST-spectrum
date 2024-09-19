#!/bin/bash

python3 src/plot_boxes.py \
    --lat-rng 30 50 \
    --lon-rng 230 235 \
    --lat-nbox 4 \
    --lon-nbox 1 \
    --plot-lat-rng 0 65 \
    --plot-lon-rng 120 260 \
    --no-display \
    --output "ECCC_ROC_plot_boxes.svg" 

