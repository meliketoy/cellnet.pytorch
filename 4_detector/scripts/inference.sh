#!/bin/bash

#rm -rf ./results/cropped/*

python inference_bbox.py \
    --net_type resnet \
    --depth 50 \
    --start 22 \
    --finish 27 \
